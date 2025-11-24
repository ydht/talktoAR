"""FastAPI entrypoint for the IDX Annual Report AI Terminal."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from src.conversation import ConversationManager
from src.extraction import MetricExtractor
from src.metric_registry import MetricRegistry
from src.retrieval import RetrievalClient
from src.table_builder import TableBuilder

app = FastAPI(title="IDX Annual Report AI Terminal")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    table: Optional[list]


index_dir = Path("data/processed/index")
retrieval_client = RetrievalClient(index_dir=index_dir)
extractor = MetricExtractor()
metric_registry = MetricRegistry()
table_builder = TableBuilder(retrieval_client=retrieval_client, extractor=extractor)
conversation_manager = ConversationManager(table_builder=table_builder, metric_registry=metric_registry)


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    result = conversation_manager.handle_message(payload.message)
    return ChatResponse(reply=result["reply"], table=result["table"])


@app.get("/download")
def download_latest(format: str = "xlsx"):
    df = conversation_manager.current_table()
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No table available yet")
    exports_dir = Path("data/exports")
    exports_dir.mkdir(parents=True, exist_ok=True)
    filename = exports_dir / f"latest.{format}"
    if format == "csv":
        df.to_csv(filename, index=False)
    else:
        df.to_excel(filename, index=False)
    return FileResponse(filename)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the FastAPI server")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    import uvicorn

    uvicorn.run("src.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
