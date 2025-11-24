from pathlib import Path

from src.metric_registry import MetricRegistry


def test_resolve_metric():
    registry = MetricRegistry(path=Path("config/metrics.yaml"))
    metric = registry.resolve("Please provide total assets for 2024")
    assert metric is not None
    assert metric.metric_id == "total_assets"
