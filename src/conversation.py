"""Conversation manager that tracks history and the active result table."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from src.metric_registry import MetricRegistry
from src.table_builder import MetricRequest, TableBuilder


@dataclass
class ConversationState:
    history: List[Dict[str, str]] = field(default_factory=list)
    active_table: Optional[pd.DataFrame] = None


class ConversationManager:
    """High-level stateful handler for chat interactions."""

    def __init__(self, table_builder: TableBuilder, metric_registry: Optional[MetricRegistry] = None) -> None:
        self.table_builder = table_builder
        self.metric_registry = metric_registry or MetricRegistry()
        self.state = ConversationState()

    def parse_years(self, text: str) -> List[int]:
        years = [int(y) for y in re.findall(r"20[0-9]{2}", text)]
        return years or [2024]

    def parse_tickers(self, text: str) -> List[str]:
        # Simple heuristic: uppercase words of length 3-5 are treated as tickers
        tickers = re.findall(r"\b[A-Z]{3,5}\b", text)
        return tickers or ["BBCA", "BMRI"]

    def handle_message(self, message: str) -> Dict[str, object]:
        self.state.history.append({"role": "user", "content": message})
        metric = self.metric_registry.resolve(message)
        if not metric:
            reply = "I could not identify a metric from your request. Try mentioning revenue, total assets, or number of employees."
            self.state.history.append({"role": "assistant", "content": reply})
            return {"reply": reply, "table": None}

        tickers = self.parse_tickers(message)
        years = self.parse_years(message)
        request = MetricRequest(metric=metric, tickers=tickers, years=years)
        df = self.table_builder.build(request)
        self.state.active_table = df
        reply = f"Compiled {metric.metric_id} for {', '.join(tickers)} across years {', '.join(map(str, years))}."
        self.state.history.append({"role": "assistant", "content": reply})
        return {"reply": reply, "table": df.to_dict(orient="records")}

    def current_table(self) -> Optional[pd.DataFrame]:
        return self.state.active_table


__all__ = ["ConversationManager", "ConversationState"]
