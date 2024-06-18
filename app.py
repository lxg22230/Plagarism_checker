from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from models import Tag, db, User, UploadedFile
from forms import RegistrationForm, LoginForm
from plagiarism_checker import check_plagiarism, get_existing_files
from functools import wraps


from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        files = UploadedFile.query.filter_by(user_id=current_user.id).order_by(desc(UploadedFile.upload_date)).all()
        if current_user.is_admin:
            users = User.query.all()
        else:
            users = []
    else:
        files = []
        users = []
    return render_template('index.html', files=files, users=users)





@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Congratulations, you are now a registered user!', 'success')
            return redirect(url_for('login'))
        except IntegrityError as e:
            db.session.rollback()
            if 'username' in str(e.orig):
                form.username.errors.append('Username already exists. Please choose a different username.')
            elif 'email' in str(e.orig):
                form.email.errors.append('Email already exists. Please choose a different email.')
            else:
                form.username.errors.append('An error occurred while creating your account. Please try again.')
    return render_template('signup.html', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    print("in upload", request.form)
    tags = Tag.query.all()
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        week_tag = request.form.get('tag')
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        print("in upload1")
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                file_extension = filename.rsplit('.', 1)[1].lower()
                # Create the subdirectory based on the week_tag
                subdirectory = os.path.join(app.config['UPLOAD_FOLDER'], week_tag)
                if not os.path.exists(subdirectory):
                    os.makedirs(subdirectory)
                    
                
                filepath = os.path.join(subdirectory, filename)
                file.save(filepath)

                # Save file info to the database with status 'Processing' and associate it with the current user
                new_file = UploadedFile(filename=filename, filepath=filepath, upload_date=datetime.now(), week_tag=week_tag, match=None, user=current_user)
                db.session.add(new_file)
                db.session.commit()

                # Perform plagiarism check
                existing_files = get_existing_files(app.config['UPLOAD_FOLDER'], week_tag, file_extension, current_user.id)
                max_similarity, max_similarity_file = check_plagiarism(filepath, existing_files)
                new_file.match = max_similarity
                new_file.status = 'Processed'
                new_file.matched_file = max_similarity_file  # Store only the file name
                db.session.commit()

                flash('File uploaded successfully. Plagiarism check completed.', 'success')
            except Exception as e:
                flash(f'An error occurred while saving the file: {e}', 'danger')
            return redirect(url_for('index'))
        else:
            flash('File type not allowed', 'danger')
            return redirect(request.url)
    return render_template('upload.html', tags=tags)

@app.route('/uploads/<week_tag>/<filename>')
@login_required
def uploaded_file(week_tag, filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], week_tag, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    
    if filename.endswith('.pdf'):
        response = make_response(send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], week_tag), filename))
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename={filename}'
        return response
    elif filename.endswith('.txt'):
        response = make_response(send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], week_tag), filename))
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'inline; filename={filename}'
        return response
    elif filename.endswith('.docx') or filename.endswith('.doc'):
        # Serve DOCX and DOC files for download
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], week_tag), filename, as_attachment=True)
    else:
        return "Unsupported file type", 400
    
def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_view
    
@app.route('/admin')
@login_required
@admin_required
def admin():
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file = UploadedFile.query.get_or_404(file_id)
    try:
        if os.path.exists(file.filepath):
            os.remove(file.filepath)
        db.session.delete(file)
        db.session.commit()
        flash('File deleted successfully', 'success')
    except Exception as e:
        flash(f'An error occurred while deleting the file: {e}', 'danger')
    return redirect(url_for('index'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User added successfully.', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('add_user.html', form=form)

@app.route('/admin/panel')
@login_required
@admin_required
def admin_panel():
    users = User.query.all()
    return render_template('admin_panel.html', users=users)

@app.route('/tags', methods=['GET', 'POST'])
@login_required
def manage_tags():
    if request.method == 'POST':
        tag_name = request.form['tag_name']
        if tag_name:
            new_tag = Tag(name=tag_name)
            db.session.add(new_tag)
            db.session.commit()
            flash('Tag added successfully.', 'success')
        else:
            flash('Please enter a tag name.', 'danger')
    tags = Tag.query.all()
    return render_template('manage_tags.html', tags=tags)
@app.route('/tags/edit/<int:tag_id>', methods=['GET', 'POST'])
@login_required
def edit_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    if request.method == 'POST':
        tag_name = request.form['tag_name']
        if tag_name:
            tag.name = tag_name
            db.session.commit()
            flash('Tag updated successfully.', 'success')
            return redirect(url_for('manage_tags'))
        else:
            flash('Please enter a tag name.', 'danger')
    return render_template('edit_tag.html', tag=tag)

@app.route('/tags/delete/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash('Tag deleted successfully.', 'success')
    return redirect(url_for('manage_tags'))



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
