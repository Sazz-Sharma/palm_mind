# app/services/pinecone_service.py
from __future__ import annotations
from typing import List, Dict, Any, Iterable
from loguru import logger
from pinecone import Pinecone
from app.core.config import get_settings

settings = get_settings()

def _batched(seq: List[str], n: int) -> Iterable[List[str]]:
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

class PineconeService:
    def __init__(self) -> None:
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index = self.pc.Index(settings.pinecone_index_name)
        self.model = getattr(settings, "pinecone_embedding_model", None)
        if not self.model:
            logger.warning("PINECONE_EMBEDDING_MODEL not set; set it in .env")

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 96,
        input_type: str = "passage",   # <- REQUIRED for llama-text-embed-v2
        truncate: str = "END",         # optional, prevents token-length rejections
    ) -> List[List[float]]:
        if not self.model:
            raise RuntimeError("PINECONE_EMBEDDING_MODEL is required for inference embedding.")

        all_vectors: List[List[float]] = []
        for batch in _batched(texts, batch_size):
            res = self.pc.inference.embed(
                model=self.model,
                inputs=batch,
                parameters={
                    "input_type": input_type,   # "passage" for docs, "query" for queries
                    "truncate": truncate,
                },
            )

            # normalize response shape
            if hasattr(res, "data"):
                data = res.data
            elif isinstance(res, dict) and "data" in res:
                data = res["data"]
            else:
                data = res

            for item in data:
                if isinstance(item, dict) and "values" in item:
                    all_vectors.append(item["values"])
                elif hasattr(item, "values"):
                    all_vectors.append(item.values)
                else:
                    all_vectors.append(item)

        if len(all_vectors) != len(texts):
            raise RuntimeError(f"Embedding count mismatch: got {len(all_vectors)} for {len(texts)} inputs")
        return all_vectors

    def embed_query(self, query: str) -> List[float]:
        # convenience helper for queries
        return self.embed_texts([query], input_type="query")[0]

    def upsert(self, items: List[Dict[str, Any]], namespace: str | None = None) -> None:
        self.index.upsert(vectors=items, namespace=namespace)
