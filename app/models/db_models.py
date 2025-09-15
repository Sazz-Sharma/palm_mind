from __future__ import annotations

from datetime import datetime, date as date_type, time as time_type
from typing import Optional, List, Dict

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True)
    filetype: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    source: Optional[str] = None  # e.g., "upload"
    # Rename attribute to avoid reserved name; keep DB column name as "metadata"
    meta: Optional[Dict[str, Any]] = Field(
    default=None,
    sa_column=Column("metadata", JSONB, nullable=True),
)

    chunks: List["Chunk"] = Relationship(back_populates="document")


class Chunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    chunk_index: int = Field(index=True)
    text: str
    # Store embedding optionally (primary source is Pinecone)
    embedding: Optional[list[float]] = Field(
        default=None,
        sa_column=Column(JSONB),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    document: Optional[Document] = Relationship(back_populates="chunks")


class ChatSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    messages: List["ChatMessage"] = Relationship(back_populates="session")


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id", index=True)
    sender: str  # "user" | "assistant" | "system"
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    session: Optional[ChatSession] = Relationship(back_populates="messages")


class InterviewBooking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True)
    date: date_type
    time: time_type
    created_at: datetime = Field(default_factory=datetime.utcnow)