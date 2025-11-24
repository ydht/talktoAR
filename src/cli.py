"""Command-line interface for common pipeline actions."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.build_index import build_index, load_chunks
from src.ingest_pdfs import ingest_pdfs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IDX Annual Report AI Terminal CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest PDFs into chunk parquet")
    ingest_parser.add_argument("--raw-dir", type=Path, required=True)
    ingest_parser.add_argument("--output", type=Path, default=Path("data/processed/chunks.parquet"))

    index_parser = subparsers.add_parser("index", help="Build vector index")
    index_parser.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.parquet"))
    index_parser.add_argument("--index-dir", type=Path, default=Path("data/processed/index"))
    index_parser.add_argument("--collection", type=str, default="idx_chunks")

    api_parser = subparsers.add_parser("api", help="Run API server")
    api_parser.add_argument("--host", type=str, default="0.0.0.0")
    api_parser.add_argument("--port", type=int, default=8000)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "ingest":
        ingest_pdfs(args.raw_dir, args.output)
        print(f"Wrote chunks to {args.output}")
    elif args.command == "index":
        chunks = load_chunks(args.chunks)
        build_index(chunks, args.index_dir, args.collection)
        print(f"Index built at {args.index_dir}")
    elif args.command == "api":
        from src.api import main as api_main

        api_main()


if __name__ == "__main__":
    main()
