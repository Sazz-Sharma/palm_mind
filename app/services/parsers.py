from __future__ import annotations

from typing import BinaryIO
from pypdf import PdfReader

def read_txt(file_obj: BinaryIO) -> str:
    file_obj.seek(0)
    return file_obj.read().decode("utf-8", errors="ignore")

def read_pdf(file_obj: BinaryIO) -> str:
    file_obj.seek(0)
    reader = PdfReader(file_obj)
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(texts).strip()