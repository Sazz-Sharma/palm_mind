# palm_mind_rag

A modular, production-grade FastAPI backend for Document Ingestion, Conversational RAG, and Interview Booking with LLM, Pinecone, Redis, and Postgres.

## Features
- **Document Ingestion API**: Upload .pdf/.txt, extract text, chunk (recursive/sliding), embed, store in Pinecone, metadata in Postgres.
- **Conversational RAG API**: Multi-turn chat with context retrieval, Redis chat memory, Groq LLM, custom prompt, no RetrievalQAChain.
- **Smart Interview Booking**: Detect booking intent, extract info with LLM, auto-book via API, ask for missing info, confirm booking.
- **Session-aware Chat**: Remembers bookings and chat history per session, answers status queries robustly.
- **Industry-standard typing & modularity**: Clean code, type annotations, easy to extend.

## Quickstart

### 1. Clone & Create Environment
```bash
git clone https://github.com/Sazz-Sharma/palm_mind.git
cd palm_mind
conda env create -f environment.yaml
conda activate palm_mind_py311
```

### 2. Setup .env
Create a `.env` file in the project root:
```ini
APP_ENV=dev
APP_NAME=palm_mind_rag
API_PREFIX=/api/v1
LOG_LEVEL=INFO
PORT=8000
HOST=0.0.0.0
GROQ_API_KEY=dummy_groq_key
GROQ_MODEL=llama-3.1-70b-versatile
PINECONE_API_KEY=dummy_pinecone_key
PINECONE_INDEX_NAME=dummy_index
PINECONE_HOST=https://dummy-host.pinecone.io
PINECONE_EMBEDDING_MODEL=multilingual-e5-large
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/palm_mind
```

### 4. Run the Redis Server

```bash
redis-server
```
To confirm you can check with: 

```bash
redis-cli ping
```

### 5. Initialize Database
```bash
python -m app.db.init_db
```

### 6. Run the API
```bash
uvicorn app.main:app --reload
```

### 7. Explore Endpoints
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: `/api/v1/health`
- Ingest: `/api/v1/ingest/upload` (upload .pdf/.txt)
- Chat: `/api/v1/chat/query` (multi-turn RAG, booking intent)
- Booking: `/api/v1/booking` (manual booking)


## Features
- **Upload & Search**: Ingest documents, ask questions, get context-aware answers.
- **Smart Booking**: Book interviews via chat, LLM extracts info, asks for missing fields, confirms booking.
- **Session Memory**: Chat remembers your previous bookings and answers status queries.
- **Custom Chunking**: Choose between recursive or sliding window chunking for ingestion.
- **Extensible**: Add new APIs, chunkers, LLMs, or vector DBs easily.

## Requirements
- Python 3.11 (via conda)
- Postgres, Redis, Pinecone account, Groq API key

## Troubleshooting
- If you see import errors, ensure your conda env is activated and all dependencies are installed.
- For Pinecone and Groq, use real API keys. 

