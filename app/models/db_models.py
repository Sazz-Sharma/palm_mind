from datetime import datetime, date as date_type, time as time_type
from typing import Optional, Any

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Relationship


# --- define Chunk FIRST ---
class Chunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    chunk_index: int = Field(index=True)
    text: str
    embedding: Optional[list[float]] = Field(default=None, sa_type=JSONB)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # forward ref is fine here
    document: Optional["Document"] = Relationship(back_populates="chunks")


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True)
    filetype: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    source: Optional[str] = Field(default=None)
    meta: Optional[dict[str, Any]] = Field(default=None, sa_type=JSONB)

    # now that Chunk is defined above, we can use list[Chunk] (NOT quoted)
    chunks: list[Chunk] = Relationship(
        back_populates="document",
        sa_relationship_kwargs=dict(
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    )


class ChatSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    messages: list["ChatMessage"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs=dict(
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    )


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id", index=True)
    sender: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    session: Optional["ChatSession"] = Relationship(back_populates="messages")


class InterviewBooking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True)
    date: date_type
    time: time_type
    created_at: datetime = Field(default_factory=datetime.utcnow)
