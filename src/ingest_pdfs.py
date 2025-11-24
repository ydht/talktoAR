"""Utilities for ingesting IDX annual report PDFs into chunked text storage."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import pandas as pd
import pdfplumber


@dataclass
class TextChunk:
    """Represents a chunk of text extracted from a PDF page."""

    ticker: str
    year: int
    page: int
    chunk_id: str
    text: str


def discover_pdfs(raw_dir: Path) -> List[Path]:
    """Find PDF files within the raw directory.

    Expected layout: ``raw_dir/<TICKER>/<YEAR>/*.pdf``.
    """

    return sorted(raw_dir.glob("**/*.pdf"))


def detect_metadata(pdf_path: Path) -> tuple[str, int]:
    """Infer ticker and fiscal year from the path segments."""

    parts = pdf_path.parts
    if len(parts) < 3:
        raise ValueError(f"Unable to parse ticker/year from path: {pdf_path}")
    ticker = parts[-3].upper()
    year = int(parts[-2])
    return ticker, year


def chunk_text(text: str, max_chars: int = 500) -> List[str]:
    """Break text into roughly even character-sized chunks."""

    words = text.split()
    chunks: List[str] = []
    buffer: List[str] = []
    total = 0
    for word in words:
        buffer.append(word)
        total += len(word) + 1
        if total >= max_chars:
            chunks.append(" ".join(buffer))
            buffer = []
            total = 0
    if buffer:
        chunks.append(" ".join(buffer))
    return chunks


def extract_chunks(pdf_path: Path) -> Iterable[TextChunk]:
    """Extract text chunks from a PDF file."""

    ticker, year = detect_metadata(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for idx, chunk in enumerate(chunk_text(text), start=1):
                yield TextChunk(
                    ticker=ticker,
                    year=year,
                    page=page_number,
                    chunk_id=f"{pdf_path.stem}-p{page_number}-c{idx}",
                    text=chunk,
                )


def ingest_pdfs(raw_dir: Path, output: Path) -> Path:
    """Ingest PDFs under ``raw_dir`` and write them to a Parquet file."""

    pdf_files = discover_pdfs(raw_dir)
    rows: List[TextChunk] = []
    for pdf_path in pdf_files:
        rows.extend(list(extract_chunks(pdf_path)))
    df = pd.DataFrame([chunk.__dict__ for chunk in rows])
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest IDX annual report PDFs.")
    parser.add_argument("--raw-dir", type=Path, required=True, help="Directory containing raw PDFs")
    parser.add_argument("--output", type=Path, default=Path("data/processed/chunks.parquet"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ingest_pdfs(args.raw_dir, args.output)
    print(f"Wrote chunks to {args.output}")


if __name__ == "__main__":
    main()
