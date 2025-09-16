# reset_db.py
from sqlmodel import SQLModel
from app.db.session import engine
# IMPORTANT: importing models registers the tables with SQLModel.metadata
from app.models.db_models import Document, Chunk, ChatSession, ChatMessage, InterviewBooking  # noqa: F401

def reset_db() -> None:
    SQLModel.metadata.drop_all(engine)   # 🔥 drops all tables known to this metadata
    SQLModel.metadata.create_all(engine) # 🆕 recreates them

if __name__ == "__main__":
    reset_db()
    print("Database reset (drop_all + create_all).")
