import os
import fitz  # PyMuPDF
import docx
from concurrent.futures import ThreadPoolExecutor

from models import UploadedFile


import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer


def preprocess_text(text):
    # Remove punctuation, special characters, and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Convert to lowercase
    text = text.lower()
    # Tokenize the text into words
    words = word_tokenize(text)
    # Remove stop words
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words]
    # Perform stemming
    stemmer = PorterStemmer()
    words = [stemmer.stem(word) for word in words]
    return words

def calculate_similarity(text1, text2):
    # Preprocess the texts
    words1 = preprocess_text(text1)
    words2 = preprocess_text(text2)

    # Calculate the Jaccard similarity
    set1 = set(words1)
    set2 = set(words2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    similarity = intersection / union

    return similarity * 100


def read_doc(file_path):
    doc = docx.Document(file_path)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return '\n'.join(text)

def read_file(file_path):
    try:
        if file_path.endswith('.pdf'):
            return read_pdf(file_path)
        elif file_path.endswith('.doc') or file_path.endswith('.docx'):
            return read_doc(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as file:
            return file.read()

def read_pdf(file_path):
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error reading PDF file {file_path}: {e}")
    return text
# def calculate_similarity(text1, text2):
#     return SequenceMatcher(None, text1, text2).ratio() * 100

def compare_files(new_file_path, file_path):
    if file_path == new_file_path:
        return 0, None
    new_file_text = read_file(new_file_path)
    existing_file_text = read_file(file_path)
    print(f"Comparing {new_file_path} and {file_path}")
    similarity = calculate_similarity(new_file_text, existing_file_text)
    print(f"Similarity: {similarity}")
    return similarity, file_path


def check_plagiarism(new_file_path, existing_files):
    max_similarity = 0
    max_similarity_file = None
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda file_path: compare_files(new_file_path, file_path), existing_files))
    for similarity, file_path in results:
        if similarity > max_similarity:
            max_similarity = similarity
            max_similarity_file = os.path.basename(file_path)  # Extract the file name
    return max_similarity, max_similarity_file


def get_existing_files(basepath, week_tag, file_extension, user_id):
    subdirectory = os.path.join(basepath, week_tag)
    if not os.path.exists(subdirectory):
        return []
    return [os.path.join(subdirectory, f) for f in os.listdir(subdirectory) if os.path.isfile(os.path.join(subdirectory, f)) and f.endswith(file_extension) and UploadedFile.query.filter_by(filepath=os.path.join(subdirectory, f), user_id=user_id).first()]
