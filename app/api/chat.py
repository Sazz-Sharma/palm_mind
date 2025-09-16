from __future__ import annotations
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.schemas import ChatQuery, ChatAnswer
from app.models.db_models import ChatSession as ChatSessionDB, ChatMessage as ChatMessageDB
from app.services.redis_memory import add_message, get_messages
from app.services.retriever import retrieve
from app.services.groq_llm import chat_completion

router = APIRouter(prefix="/chat", tags=["chat"])

SYSTEM_PROMPT = (
    "You are a helpful assistant. Use the provided context to answer the user. "
    "If the answer is not in the context, say you are not sure."
)

def build_prompt(history: List[Dict[str, str]], context_docs: List[Dict]) -> List[Dict[str, str]]:
    context_strs = []
    for i, d in enumerate(context_docs):
        meta = d.get("metadata", {})
        chunk_index = meta.get("chunk_index")
        filename = meta.get("filename")
        text = meta.get("text") or ""
        context_strs.append(f"[{i}] file={filename} chunk={chunk_index}\n{text}".strip())
    context_block = "\n\n".join(context_strs).strip()

    messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    if context_block:
        messages.append({"role": "system", "content": f"Context:\n{context_block}"})
    return messages

@router.post("/query", response_model=ChatAnswer)
def chat_query(payload: ChatQuery, session: Session = Depends(get_session)) -> ChatAnswer:
    # Ensure chat session row exists
    cs = session.exec(
        select(ChatSessionDB).where(ChatSessionDB.session_id == payload.session_id)
    ).first()
    if not cs:
        cs = ChatSessionDB(session_id=payload.session_id)
        session.add(cs)
        session.commit()
        session.refresh(cs)

    # Get history from Redis
    history = get_messages(payload.session_id, limit=20)

    # Retrieve docs
    ns = payload.namespace or "__default__"
    docs = retrieve(payload.question, top_k=payload.top_k, namespace=payload.namespace)

    # Build and call LLM
    messages = build_prompt(history, docs)
    messages.append({"role": "user", "content": payload.question})
    answer = chat_completion(messages)

    # Persist messages (DB + Redis)
    user_msg = ChatMessageDB(session_id=cs.id, sender="user", message=payload.question)
    asst_msg = ChatMessageDB(session_id=cs.id, sender="assistant", message=answer)
    session.add_all([user_msg, asst_msg])
    session.commit()

    add_message(payload.session_id, "user", payload.question)
    add_message(payload.session_id, "assistant", answer)

    sources = []
    for d in docs:
        md = d.get("metadata", {})
        sources.append({
            "id": d.get("id"),
            "score": d.get("score"),
            "filename": md.get("filename"),
            "chunk_index": md.get("chunk_index"),
        })

    return ChatAnswer(session_id=payload.session_id, answer=answer, sources=sources)