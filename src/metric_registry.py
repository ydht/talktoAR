"""Metric registry for mapping natural language queries to structured metrics."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class Metric:
    """Structured definition of a metric."""

    metric_id: str
    description: str
    synonyms: List[str]
    extraction_prompt: str
    unit: str


class MetricRegistry:
    """Registry encapsulating metric lookup and synonym matching."""

    def __init__(self, path: Path = Path("config/metrics.yaml")) -> None:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.metrics: Dict[str, Metric] = {}
        for metric_id, payload in data.get("metrics", {}).items():
            metric = Metric(
                metric_id=metric_id,
                description=payload.get("description", ""),
                synonyms=[metric_id.replace("_", " ")] + payload.get("synonyms", []),
                extraction_prompt=payload.get("extraction_prompt", ""),
                unit=payload.get("unit", ""),
            )
            self.metrics[metric_id] = metric

    def resolve(self, query: str) -> Optional[Metric]:
        """Return the best matching metric given a natural language query."""

        query_lower = query.lower()
        for metric in self.metrics.values():
            for synonym in metric.synonyms:
                if re.search(rf"\b{re.escape(synonym.lower())}\b", query_lower):
                    return metric
        return None

    def get(self, metric_id: str) -> Metric:
        """Retrieve a metric by id or raise."""

        if metric_id not in self.metrics:
            raise KeyError(f"Unknown metric {metric_id}")
        return self.metrics[metric_id]


__all__ = ["Metric", "MetricRegistry"]
