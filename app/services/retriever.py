from __future__ import annotations
from typing import List, Dict, Any
from app.services.pinecone_service import PineconeService

pc = PineconeService()

def retrieve(query: str, top_k: int = 5, namespace: str | None = None) -> List[Dict[str, Any]]:
    emb = pc.embed_texts([query], input_type="query")[0]
    res = pc.index.query(
        vector=emb,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace,
    )
    # normalize result items
    matches = getattr(res, "matches", None) or res.get("matches", [])
    docs: List[Dict[str, Any]] = []
    for m in matches:
        docs.append({
            "id": getattr(m, "id", None) or m.get("id"),
            "score": getattr(m, "score", None) or m.get("score"),
            "metadata": getattr(m, "metadata", None) or m.get("metadata", {}),
        })
    return docs