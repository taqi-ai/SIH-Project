"""Document text layer extraction with a graceful OCR-fallback message.

For the prototype, uploaded PDFs are read via their embedded text layer (pypdf).
If no text layer is present (e.g. a scanned image-only PDF), we surface a clear
'OCR engine unavailable in prototype' status instead of silently failing —
this is the seam where PaddleOCR/Tesseract would plug in for production.
"""
from pypdf import PdfReader


def extract_text_per_page(file_path: str) -> list[str]:
    try:
        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
        return pages
    except Exception:
        return []


def ocr_document(file_path: str) -> dict:
    pages = extract_text_per_page(file_path)
    if not pages or not any(p.strip() for p in pages):
        return {
            "success": False,
            "pages": [],
            "full_text": "",
            "message": "No extractable text layer found. OCR engine (PaddleOCR/Tesseract) "
                       "would run here in production; prototype requires a text-layer PDF.",
        }
    return {
        "success": True,
        "pages": pages,
        "full_text": "\n".join(pages),
        "message": "Text layer extracted successfully.",
    }
