import os
from difflib import SequenceMatcher
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor

def read_file(file_path):
    try:
        if file_path.endswith('.pdf'):
            return read_pdf(file_path)
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

def calculate_similarity(text1, text2):
    return SequenceMatcher(None, text1, text2).ratio() * 100

def compare_files(new_file_path, file_path):
    if file_path == new_file_path:
        return 0
    new_file_text = read_file(new_file_path)
    existing_file_text = read_file(file_path)
    print(f"Comparing {new_file_path} and {file_path}")
    similarity = calculate_similarity(new_file_text, existing_file_text)
    print(f"Similarity: {similarity}")
    return similarity

def check_plagiarism(new_file_path, existing_files):
    max_similarity = 0
    with ThreadPoolExecutor() as executor:
        similarities = list(executor.map(lambda file_path: compare_files(new_file_path, file_path), existing_files))
    max_similarity = max(similarities)
    return max_similarity

def get_existing_files(basepath, week_tag, file_extension):
    subdirectory = os.path.join(basepath, week_tag)
    if not os.path.exists(subdirectory):
        return []
    return [os.path.join(subdirectory, f) for f in os.listdir(subdirectory) if os.path.isfile(os.path.join(subdirectory, f)) and f.endswith(file_extension)]
