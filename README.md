# Plagiarism Checker

A plagiarism checker application that compares new files with existing files to detect potential plagiarism. It supports various file formats, including PDF, DOC, and DOCX.

## Features

- Upload and compare files to detect plagiarism
- Supports PDF, DOC, and DOCX file formats
- Calculates similarity percentage between files
- Provides a user-friendly web interface for easy interaction

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/lxg22230/Plagarism_checker.git
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up the database:
   - Create a PostgreSQL database for the application
   - Update the database configuration in `config.py`

4. Run the application:
   ```
   python app.py
   ```

## Usage

1. Access the application through the provided URL (e.g., `http://localhost:5000`).

2. Register a new account or log in with an existing account.

3. Upload a file for plagiarism checking:
   - Select the desired file format (PDF, DOC, or DOCX)
   - Choose the file from your local machine
   - Specify the week tag for categorization
   - Click the "Upload" button

4. The application will process the file and compare it with existing files in the database.

5. The similarity percentage and the file with the highest similarity will be displayed.

6. Review the results and take appropriate action based on the plagiarism detection.

## Algorithm and Methodology

The plagiarism checker uses the following algorithm and methodology:

1. Text Preprocessing:
   - Remove punctuation, special characters, and digits
   - Convert text to lowercase
   - Tokenize the text into words
   - Remove stop words
   - Perform stemming using the Porter stemmer

2. Similarity Calculation:
   - Calculate the Jaccard similarity between the preprocessed texts
   - Jaccard similarity = (intersection of words) / (union of words)

3. Plagiarism Detection:
   - Compare the uploaded file with existing files in the database
   - Find the file with the highest similarity percentage
   - Display the similarity percentage and the matched file

## File Structure

- `app.py`: The main Flask application file
- `config.py`: Configuration settings for the application
- `models.py`: Database models and relationships
- `plagiarism_checker.py`: Plagiarism detection functions and utilities
- `templates/`: HTML templates for the web interface
- `static/`: Static files (CSS, JavaScript, images)
- `uploads/`: Directory for storing uploaded files

## Database

The application uses a PostgreSQL database to store user information, uploaded files, and plagiarism detection results. The database configuration can be found in `config.py`.

## Contributing

Contributions to the plagiarism checker project are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request. Make sure to follow the existing code style and guidelines.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For any questions or inquiries, please contact [your email address].

---

Feel free to customize and expand upon this README template based on your specific project details and requirements.
