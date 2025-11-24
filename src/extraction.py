"""LLM-based metric extraction utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from src.metric_registry import Metric


@dataclass
class ExtractionResult:
    """Numeric value extracted from context."""

    value: Optional[float]
    confidence: float
    source_page: int
    explanation: str


class MetricExtractor:
    """Extracts metric values from text chunks via an LLM (placeholder implementation)."""

    def __init__(self, model_name: str = "gpt-4o-mini") -> None:
        self.model_name = model_name

    def _mock_llm_extract(self, prompt: str) -> Optional[float]:
        """Placeholder extraction using regex to avoid network calls."""

        match = re.search(r"([0-9][0-9.,]*)", prompt)
        if match:
            raw = match.group(1).replace(",", "").replace(".", "")
            try:
                return float(raw)
            except ValueError:
                return None
        return None

    def extract(self, metric: Metric, chunk_text: str, page: int) -> ExtractionResult:
        """Extract a numeric value for the given metric from chunk text."""

        prompt = f"Metric: {metric.metric_id}\nInstruction: {metric.extraction_prompt}\nText: {chunk_text}"
        value = self._mock_llm_extract(prompt)
        confidence = 0.6 if value is not None else 0.0
        explanation = (
            "Placeholder regex extraction executed. Replace MetricExtractor._mock_llm_extract with real LLM call for production."
        )
        return ExtractionResult(value=value, confidence=confidence, source_page=page, explanation=explanation)


__all__ = ["MetricExtractor", "ExtractionResult"]
