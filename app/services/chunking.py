from __future__ import annotations
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_recursive(
    text: str, chunk_size: int = 800, chunk_overlap: int = 100
) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)

def chunk_sliding_window(
    text: str, chunk_size: int = 800, chunk_overlap: int = 100
) -> List[str]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be < chunk_size")
    tokens = list(text)
    chunks: List[str] = []
    start = 0
    n = len(tokens)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append("".join(tokens[start:end]))
        if end == n:
            break
        start = end - chunk_overlap
    return chunks