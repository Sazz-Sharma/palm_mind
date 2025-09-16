from __future__ import annotations
from typing import List, Dict, Any
import json
import redis
from app.core.config import get_settings

settings = get_settings()
r = redis.from_url(settings.redis_url, decode_responses=True)

def _key(session_id: str) -> str:
    return f"chat:{session_id}:messages"

def _booking_key(session_id: str) -> str:
    return f"chat:{session_id}:booking:last"

def set_last_booking(session_id: str, data: dict) -> None:
    r.set(_booking_key(session_id), json.dumps(data))

def get_last_booking(session_id: str) -> dict | None:
    raw = r.get(_booking_key(session_id))
    return json.loads(raw) if raw else None

def add_message(session_id: str, role: str, content: str, max_messages: int = 20) -> None:
    record = json.dumps({"role": role, "content": content})
    r.rpush(_key(session_id), record)
    r.ltrim(_key(session_id), -max_messages, -1)

def get_messages(session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    items = r.lrange(_key(session_id), -limit, -1)
    return [json.loads(i) for i in items]

def clear_session(session_id: str) -> None:
    r.delete(_key(session_id))
