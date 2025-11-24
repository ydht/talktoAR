"""Builds metric tables across companies and years."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import duckdb
import pandas as pd

from src.extraction import ExtractionResult, MetricExtractor
from src.metric_registry import Metric
from src.retrieval import RetrievalClient

CACHE_PATH = Path("data/processed/metrics_cache.duckdb")


@dataclass
class MetricRequest:
    """Represents a structured request for a metric across tickers and years."""

    metric: Metric
    tickers: List[str]
    years: List[int]


class MetricsCache:
    """Simple DuckDB-backed cache to avoid repeated extractions."""

    def __init__(self, path: Path = CACHE_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        con = duckdb.connect(str(self.path))
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics_cache (
                metric TEXT,
                ticker TEXT,
                year INTEGER,
                value DOUBLE,
                confidence DOUBLE,
                source_page INTEGER,
                explanation TEXT
            )
            """
        )
        con.close()

    def get(self, metric: str, ticker: str, year: int) -> Optional[ExtractionResult]:
        con = duckdb.connect(str(self.path), read_only=True)
        res = con.execute(
            "SELECT value, confidence, source_page, explanation FROM metrics_cache WHERE metric=? AND ticker=? AND year=?",
            [metric, ticker, year],
        ).fetchone()
        con.close()
        if res:
            value, confidence, source_page, explanation = res
            return ExtractionResult(value=value, confidence=confidence, source_page=source_page, explanation=explanation)
        return None

    def put(self, metric: str, ticker: str, year: int, result: ExtractionResult) -> None:
        con = duckdb.connect(str(self.path))
        con.execute(
            "INSERT INTO metrics_cache VALUES (?, ?, ?, ?, ?, ?, ?)",
            [metric, ticker, year, result.value, result.confidence, result.source_page, result.explanation],
        )
        con.close()


class TableBuilder:
    """Coordinates retrieval, extraction, and caching to build DataFrames."""

    def __init__(self, retrieval_client: RetrievalClient, extractor: MetricExtractor, cache: Optional[MetricsCache] = None) -> None:
        self.retrieval_client = retrieval_client
        self.extractor = extractor
        self.cache = cache or MetricsCache()

    def build(self, request: MetricRequest, top_k: int = 5) -> pd.DataFrame:
        rows = []
        for ticker in request.tickers:
            for year in request.years:
                cached = self.cache.get(request.metric.metric_id, ticker, year)
                if cached and cached.value is not None:
                    rows.append({"ticker": ticker, "year": year, "value": cached.value, "source_page": cached.source_page, "confidence": cached.confidence})
                    continue

                chunks = self.retrieval_client.query(text=request.metric.description, top_k=top_k, ticker=ticker, year=year)
                best = max(chunks, key=lambda c: c.score) if chunks else None
                if best:
                    result = self.extractor.extract(request.metric, best.document, best.page)
                    self.cache.put(request.metric.metric_id, ticker, year, result)
                    rows.append({"ticker": ticker, "year": year, "value": result.value, "source_page": result.source_page, "confidence": result.confidence})
                else:
                    rows.append({"ticker": ticker, "year": year, "value": None, "source_page": None, "confidence": 0.0})
        df = pd.DataFrame(rows)
        return df

    @staticmethod
    def export(df: pd.DataFrame, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".csv":
            df.to_csv(path, index=False)
        else:
            df.to_excel(path, index=False)
        return path


__all__ = ["TableBuilder", "MetricRequest", "MetricsCache"]
