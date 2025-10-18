import os
import pdfplumber
from docx import Document
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
UPLOAD_FOLDER = 'uploads'

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath, filename):
    """Extract text content from uploaded files based on their extension."""
    try:
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        if file_extension == 'txt':
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()
                
        elif file_extension == 'pdf':
            text = ""
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
            
        elif file_extension == 'docx':
            doc = Document(filepath)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
            
        else:
            return "Unsupported file format"
            
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def save_uploaded_file(file, upload_folder):
    """Save uploaded file and return the filepath."""
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    
    # Handle duplicate filenames by adding a number
    counter = 1
    base_filename = filename
    while os.path.exists(filepath):
        name, ext = os.path.splitext(base_filename)
        filename = f"{name}_{counter}{ext}"
        filepath = os.path.join(upload_folder, filename)
        counter += 1
    
    file.save(filepath)
    return filepath, filename