from __future__ import annotations

from sqlmodel import SQLModel
from app.db.session import engine
from app.models.db_models import Document, Chunk, ChatSession, ChatMessage, InterviewBooking  # noqa: F401


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print("Database tables created.")