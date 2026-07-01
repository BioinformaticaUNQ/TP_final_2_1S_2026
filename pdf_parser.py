from __future__ import annotations

from pathlib import Path
from typing import List

from PyPDF2 import PdfReader

try:
    import tabula
except ImportError: 
    tabula = None


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    path = Path(pdf_path)
    reader = PdfReader(str(path))

    pages_text: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages_text.append(text)

    return "\n".join(pages_text)


def extract_tables_from_pdf(pdf_path: str | Path, pages: str = "all"):
    if tabula is None:
        raise ImportError("tabula-py is not installed or could not be imported")

    path = Path(pdf_path)
    return tabula.read_pdf(str(path), pages=pages, multiple_tables=True)
