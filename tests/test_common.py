import tempfile
import fitz
from pathlib import Path

from utils.common import extract_pdf_content


def test_extract_pdf_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Hello world from PyMuPDF")
        doc.save(str(pdf_path))
        doc.close()

        # Test extract_pdf_content
        text = extract_pdf_content(pdf_path)
        assert text is not None
        assert "Hello world from PyMuPDF" in text
