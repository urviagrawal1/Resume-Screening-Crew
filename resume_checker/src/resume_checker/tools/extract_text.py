import os
import re
import fitz  # PyMuPDF
from concurrent.futures import ProcessPoolExecutor, as_completed

# For Parallel Extraction of Resume PDFs

def clean_text(text: str) -> str:
    """Clean and normalize resume text."""
    text = text.replace('\u200b', '').replace('\xa0', ' ').replace('\u00ad', '')

    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Signature\s*[:\-]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Date\s*[:\-]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Place\s*[:\-]*', '', text, flags=re.IGNORECASE)

    text = re.sub(r'[■◆•→●]', ' ', text)

    lines = text.splitlines()
    line_counts = {}
    for line in lines:
        line_clean = line.strip()
        if line_clean:
            line_counts[line_clean] = line_counts.get(line_clean, 0) + 1

    cleaned_lines = [line for line in lines if line_counts.get(line.strip(), 0) < 2]
    cleaned_text = "\n".join(cleaned_lines)

    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

    return cleaned_text.strip()


def process_file(file_path):
    """Extract and clean text from a single PDF file."""
    filename = os.path.basename(file_path)
    try:
        with fitz.open(file_path) as doc:
            if doc.page_count == 0:
                warning = f"❌ {filename} has ZERO pages (invalid or corrupted PDF)."
                return (filename, "", warning)

            raw_text = ''.join(page.get_text() for page in doc)

            if not raw_text.strip():
                warning = f"⚠ {filename} has NO extractable text (possibly scanned or empty)."
                return (filename, "", warning)

            cleaned = clean_text(raw_text)
            return (filename, cleaned, None)

    except Exception as e:
        warning = f"❌ Error reading {filename}: {e}"
        return (filename, "", warning)


def extract_text_from_pdf_parallel(folder_path: str):
    pdf_files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith('.pdf')
    ]

    extracted = {}
    warnings_list = []

    for f in pdf_files:
        filename, content, warning = process_file(f)
        extracted[filename] = content
        if warning:
            warnings_list.append(warning)

    return extracted, warnings_list