from __future__ import annotations

import uuid
from typing import Literal, List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlmodel import Session
from loguru import logger

from app.db.session import get_session
from app.models.db_models import Document, Chunk
from app.services.parsers import read_pdf, read_txt
from app.services.chunking import chunk_recursive, chunk_sliding_window
from app.services.pinecone_service import PineconeService

router = APIRouter(prefix="/ingest", tags=["ingestion"])

ChunkerName = Literal["recursive", "sliding"]

@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    chunker: ChunkerName = Query("recursive"),
    chunk_size: int = Query(800, ge=100, le=4000),
    chunk_overlap: int = Query(100, ge=0, le=2000),
    namespace: str | None = Query(None),
    session: Session = Depends(get_session),
) -> dict:
    # 1) Parse file
    content_type = file.content_type or ""
    filename = file.filename or "uploaded"
    try:
        if filename.lower().endswith(".pdf") or "pdf" in content_type:
            text = read_pdf(file.file)
        elif filename.lower().endswith(".txt") or "text" in content_type:
            text = read_txt(file.file)
        else:
            raise HTTPException(status_code=400, detail="Only .pdf or .txt supported")
    except Exception as e:
        logger.exception("Failed to parse file")
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found")

    # 2) Chunk
    if chunker == "recursive":
        chunks = chunk_recursive(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    else:
        chunks = chunk_sliding_window(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    if not chunks:
        raise HTTPException(status_code=400, detail="Chunking produced no chunks")

    # 3) Create Document record
    doc = Document(
        filename=filename,
        filetype="pdf" if filename.lower().endswith(".pdf") else "txt",
        source="upload",
        meta={"chunker": chunker, "chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    # 4) Embed and upsert to Pinecone
    pc = PineconeService()
    embeddings = pc.embed_texts(chunks, input_type="passage")

    items = []
    chunk_rows: List[Chunk] = []
    for idx, (ch_text, emb) in enumerate(zip(chunks, embeddings)):
        vector_id = str(uuid.uuid4())
        items.append({
            "id": vector_id,
            "values": emb,
            "metadata": {
                "document_id": doc.id,
                "filename": filename,
                "chunk_index": idx,
                "text": ch_text,
            },
        })
        chunk_rows.append(Chunk(
            document_id=doc.id,
            chunk_index=idx,
            text=ch_text,
            # optional: store embedding locally; we can skip to save space
            embedding=None,
        ))

    pc.upsert(items, namespace=namespace)

    # 5) Persist chunks
    session.add_all(chunk_rows)
    session.commit()

    return {
        "document_id": doc.id,
        "filename": filename,
        "chunks": len(chunks),
        "namespace": namespace,
        "message": "Ingestion completed",
    }