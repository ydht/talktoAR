"""Vector retrieval utilities backed by ChromaDB."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from chromadb import PersistentClient
from chromadb.api.types import Documents, EmbeddingFunction, QueryResult
from chromadb.utils import embedding_functions

DEFAULT_COLLECTION = "idx_chunks"


@dataclass
class RetrievedChunk:
    """Represents a retrieved chunk with metadata and score."""

    document: str
    score: float
    ticker: str
    year: int
    page: int


class RetrievalClient:
    """Wraps Chroma collection operations for filtered retrieval."""

    def __init__(self, index_dir: Path, collection_name: str = DEFAULT_COLLECTION, embedding_function: Optional[EmbeddingFunction] = None) -> None:
        self.client = PersistentClient(path=str(index_dir))
        self.embedding_function = embedding_function or embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
        )

    def query(self, text: str, top_k: int = 5, ticker: Optional[str] = None, year: Optional[int] = None) -> List[RetrievedChunk]:
        """Query the vector index with optional filters."""

        where = {}
        if ticker:
            where["ticker"] = ticker
        if year:
            where["year"] = year

        result: QueryResult = self.collection.query(query_texts=[text], n_results=top_k, where=where)
        documents: Documents = result.get("documents", [[]])[0]
        distances = result.get("distances", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]

        chunks: List[RetrievedChunk] = []
        for doc, distance, metadata in zip(documents, distances, metadatas):
            chunks.append(
                RetrievedChunk(
                    document=doc,
                    score=float(distance),
                    ticker=str(metadata.get("ticker")),
                    year=int(metadata.get("year")),
                    page=int(metadata.get("page")),
                )
            )
        return chunks


__all__ = ["RetrievalClient", "RetrievedChunk"]
