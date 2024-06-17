from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, make_response
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from models import db, UploadedFile
from plagiarism_checker import check_plagiarism, get_existing_files

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)

@app.route('/')
def index():
    files = UploadedFile.query.all()
    return render_template('index.html', files=files)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        week_tag = request.form.get('week_tag')
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
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

                # Check plagiarism
                existing_files = get_existing_files(app.config['UPLOAD_FOLDER'], week_tag, file_extension)
                match_percentage = check_plagiarism(filepath, existing_files)

                new_file = UploadedFile(filename=filename, filepath=filepath, upload_date=datetime.now(), week_tag=week_tag, match=match_percentage)
                db.session.add(new_file)
                db.session.commit()
                flash('File uploaded successfully', 'success')
            except Exception as e:
                flash(f'An error occurred while saving the file: {e}', 'danger')
            return redirect(url_for('index'))
        else:
            flash('File type not allowed', 'danger')
            return redirect(request.url)
    return render_template('upload.html')

@app.route('/uploads/<week_tag>/<filename>')
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

@app.route('/delete/<int:file_id>', methods=['POST'])
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
