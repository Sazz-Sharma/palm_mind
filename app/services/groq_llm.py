from __future__ import annotations
from typing import List, Dict
from groq import Groq
from app.core.config import get_settings

settings = get_settings()
client = Groq(api_key=settings.groq_api_key)

def chat_completion(messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
    resp = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""