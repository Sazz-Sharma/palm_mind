from __future__ import annotations
from datetime import date, time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr

class ChatQuery(BaseModel):
    session_id: str = Field(..., min_length=3)
    question: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)
    namespace: Optional[str] = None

class ChatAnswer(BaseModel):
    session_id: str
    answer: str
    sources: List[Dict[str, Any]]

class BookingCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    date: date
    time: time

class BookingResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    date: date
    time: time