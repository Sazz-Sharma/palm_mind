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
from app.services.booking_llm import extract_booking_info
from datetime import datetime
from app.models.schemas import BookingCreate
from app.api.booking import create_booking
import json
import re


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

def _normalize_hms_if_needed(t: str) -> str:
    t = (t or "").strip()
    try:
        # accept "HH:MM:SS"
        datetime.strptime(t, "%H:%M:%S")
        return t
    except Exception:
        pass
    try:
        # accept "HH:MM" -> add seconds
        return datetime.strptime(t, "%H:%M").strftime("%H:%M:00")
    except Exception:
        return t  # let Pydantic validation catch invalid formats


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
    booking_result = extract_booking_info(payload.question)
    print("Booking extraction result:", booking_result)
    if "BOOKING_READY" in booking_result:
        try:
            match = re.search(r'BOOKING_READY:\s*(\{.*?\})', booking_result)
            if match:
                booking_data = json.loads(match.group(1))
                print("Parsed booking data:", booking_data)
            else:
                raise ValueError("No JSON object found after BOOKING_READY")
        except Exception:
            answer = "I couldn’t parse the booking details. Please provide name, email, date (YYYY-MM-DD), and time (HH:MM:SS)."
            user_msg = ChatMessageDB(session_id=cs.id, sender="user", message=payload.question)
            asst_msg = ChatMessageDB(session_id=cs.id, sender="assistant", message=answer)
            session.add_all([user_msg, asst_msg]); session.commit()
            add_message(payload.session_id, "user", payload.question)
            add_message(payload.session_id, "assistant", answer)
            return ChatAnswer(session_id=payload.session_id, answer=answer, sources=[])

        name = (booking_data.get("name") or "").strip()
        email = (booking_data.get("email") or "").strip()
        date_str = (booking_data.get("date") or "").strip()
        time_str = (booking_data.get("time") or "").strip()

        if not name or not email or not date_str or not time_str:
            missing = [k for k,v in {"name":name,"email":email,"date":date_str,"time":time_str}.items() if not v]
            answer = f"To confirm your booking, please provide: {', '.join(missing)}. Time must be HH:MM:SS."
            user_msg = ChatMessageDB(session_id=cs.id, sender="user", message=payload.question)
            asst_msg = ChatMessageDB(session_id=cs.id, sender="assistant", message=answer)
            session.add_all([user_msg, asst_msg]); session.commit()
            add_message(payload.session_id, "user", payload.question)
            add_message(payload.session_id, "assistant", answer)
            return ChatAnswer(session_id=payload.session_id, answer=answer, sources=[])

        # 2) Build BookingCreate. Only normalize if validation fails.
        try:
            booking_payload = BookingCreate(name=name, email=email, date=date_str, time=time_str)
        except Exception:
            time_norm = _normalize_hms_if_needed(time_str)
            try:
                booking_payload = BookingCreate(name=name, email=email, date=date_str, time=time_norm)
            except Exception:
                answer = "Please provide the time in HH:MM:SS format (e.g., 15:00:00 for 3pm)."
                user_msg = ChatMessageDB(session_id=cs.id, sender="user", message=payload.question)
                asst_msg = ChatMessageDB(session_id=cs.id, sender="assistant", message=answer)
                session.add_all([user_msg, asst_msg]); session.commit()
                add_message(payload.session_id, "user", payload.question)
                add_message(payload.session_id, "assistant", answer)
                return ChatAnswer(session_id=payload.session_id, answer=answer, sources=[])

        # 3) Create booking BEFORE responding
        booking_resp = create_booking(payload=booking_payload, session=session)

        answer = f"Booking confirmed for {booking_resp.name} on {booking_resp.date} at {booking_resp.time}."
        user_msg = ChatMessageDB(session_id=cs.id, sender="user", message=payload.question)
        asst_msg = ChatMessageDB(session_id=cs.id, sender="assistant", message=answer)
        session.add_all([user_msg, asst_msg]); session.commit()
        add_message(payload.session_id, "user", payload.question)
        add_message(payload.session_id, "assistant", answer)
        return ChatAnswer(session_id=payload.session_id, answer=answer, sources=[])

    elif booking_result.startswith("NO_BOOKING"):

        ns = payload.namespace or "__default__"
        docs = retrieve(payload.question, top_k=payload.top_k, namespace=ns)
        messages = build_prompt(history, docs)
        messages.append({"role": "user", "content": payload.question})
        answer = chat_completion(messages)
        user_msg = ChatMessageDB(session_id=cs.id, sender="user", message=payload.question)
        asst_msg = ChatMessageDB(session_id=cs.id, sender="assistant", message=answer)
        session.add_all([user_msg, asst_msg]); session.commit()
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

    else:
        # LLM is asking for missing booking info (multi-turn slot filling)
        answer = booking_result
        user_msg = ChatMessageDB(session_id=cs.id, sender="user", message=payload.question)
        asst_msg = ChatMessageDB(session_id=cs.id, sender="assistant", message=answer)
        session.add_all([user_msg, asst_msg]); session.commit()
        add_message(payload.session_id, "user", payload.question)
        add_message(payload.session_id, "assistant", answer)
        return ChatAnswer(session_id=payload.session_id, answer=answer, sources=[])    