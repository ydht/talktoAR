# IDX Annual Report AI Terminal

This repository provides a modular pipeline for ingesting IDX annual report PDFs, building a vector search index, and serving a chat-based interface for financial metric extraction. The system is designed for rapid experimentation and small-team operations, with sensible defaults for offline evaluation.

## Features
- **PDF ingestion** using `pdfplumber`, with chunked storage in Parquet.
- **Vector indexing** via SentenceTransformers embeddings and FAISS-backed ChromaDB.
- **Metric registry** loaded from YAML for configurable metric detection and prompts.
- **Retrieval-augmented extraction** pipeline that caches metric results in DuckDB.
- **Conversation-aware chat API** powered by FastAPI with Excel/CSV export support.
- **CLI tools** for ingestion, index building, and running the API server.

## Quickstart
1. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Ingest PDFs placed under `data/raw/<TICKER>/<YEAR>/*.pdf`:
   ```bash
   python -m src.ingest_pdfs --raw-dir data/raw --output data/processed/chunks.parquet
   ```
3. Build the vector index:
   ```bash
   python -m src.build_index --chunks data/processed/chunks.parquet --index-dir data/processed/index
   ```
4. Run the API server:
   ```bash
   python -m src.api --host 0.0.0.0 --port 8000
   ```

## Directory Layout
See inline comments in `config/` and `src/` for module responsibilities and extensibility guidance.

## Notes
- The code is written for Python 3.10+.
- Replace the placeholder LLM call in `src/extraction.py` with your provider of choice (OpenAI, Azure, etc.).
- The pipeline prefers lightweight, local dependencies for ease of deployment.
