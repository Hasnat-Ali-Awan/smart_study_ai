import os
from pypdf import PdfReader
from docx import Document
from database import db

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file):
    """Save uploaded file to disk"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = uploaded_file.name.replace(" ", "_")
    filename = f"{timestamp}_{safe_name}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    file_content = uploaded_file.getbuffer()
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return {
        'filename': filename,
        'original_name': uploaded_file.name,
        'file_path': file_path,
        'file_size': len(file_content),
        'file_type': uploaded_file.type or uploaded_file.name.split('.')[-1].lower()
    }

def extract_text_from_file(file_path, file_type):
    """Extract text from supported file types"""
    try:
        if 'pdf' in file_type.lower() or file_path.endswith('.pdf'):
            return extract_pdf(file_path)
        elif 'text' in file_type.lower() or file_path.endswith('.txt'):
            return extract_txt(file_path)
        elif 'word' in file_type.lower() or file_path.endswith('.docx'):
            return extract_docx(file_path)
        else:
            if file_path.endswith('.pdf'):
                return extract_pdf(file_path)
            elif file_path.endswith('.txt'):
                return extract_txt(file_path)
            elif file_path.endswith('.docx'):
                return extract_docx(file_path)
            else:
                return f"Unsupported file format: {file_type}"
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_pdf(file_path):
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        return f"Error reading PDF: {e}"
    return clean_text(text)

def extract_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return clean_text(f.read())
    except Exception as e:
        return f"Error reading TXT: {e}"

def extract_docx(file_path):
    try:
        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)
        return clean_text(text)
    except Exception as e:
        return f"Error reading DOCX: {e}"

def clean_text(text):
    """Normalize extracted text"""
    if not text:
        return ""
    
    text = text.replace("\x00", "")
    import re
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    
    return text.strip()

def process_file_upload(uploaded_file):
    """Process file upload"""
    # Get active session
    active_session = db.get_active_session()
    if not active_session:
        session_id = db.create_session()
    else:
        session_id = active_session['id']
    
    # Save file
    file_info = save_uploaded_file(uploaded_file)
    
    # Extract text
    extracted_text = extract_text_from_file(file_info['file_path'], file_info['file_type'])
    
    # Store in database
    file_id = db.add_file(
        session_id=session_id,
        filename=file_info['original_name'],
        filepath=file_info['file_path'],
        filesize=file_info['file_size'],
        content_text=extracted_text,
        file_type=file_info['file_type']
    )
    
    return {
        'file_id': file_id,
        'session_id': session_id,
        'filename': file_info['original_name'],
        'content': extracted_text
    }