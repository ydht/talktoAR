"""Build a FAISS-backed Chroma index from chunked Parquet data."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd
from chromadb import PersistentClient
from chromadb.utils import embedding_functions


DEFAULT_COLLECTION = "idx_chunks"


def load_chunks(parquet_path: Path) -> pd.DataFrame:
    """Load chunked text data from Parquet."""

    return pd.read_parquet(parquet_path)


def get_client(index_dir: Path) -> PersistentClient:
    """Create a persistent Chroma client with FAISS backend."""

    index_dir.mkdir(parents=True, exist_ok=True)
    return PersistentClient(path=str(index_dir))


def build_index(chunks: pd.DataFrame, index_dir: Path, collection_name: str = DEFAULT_COLLECTION) -> None:
    """Create or refresh a vector index from chunked text."""

    client = get_client(index_dir)
    embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")
    collection = client.get_or_create_collection(name=collection_name, embedding_function=embeddings, metadata={"backend": "faiss"})

    if len(chunks) == 0:
        raise ValueError("No chunks found; ensure ingestion has run.")

    # Remove previous contents to avoid duplicates when rebuilding.
    try:
        collection.delete(where={})
    except Exception:
        # Collection may be empty; safe to ignore.
        pass

    ids = chunks["chunk_id"].astype(str).tolist()
    documents = chunks["text"].tolist()
    metadatas = chunks[["ticker", "year", "page"]].to_dict("records")
    collection.add(ids=ids, documents=documents, metadatas=metadatas)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build vector index for IDX chunks.")
    parser.add_argument("--chunks", type=Path, required=True, help="Path to chunks.parquet")
    parser.add_argument("--index-dir", type=Path, default=Path("data/processed/index"))
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chunks = load_chunks(args.chunks)
    build_index(chunks, args.index_dir, args.collection)
    print(f"Built index at {args.index_dir} in collection {args.collection}")


if __name__ == "__main__":
    main()
