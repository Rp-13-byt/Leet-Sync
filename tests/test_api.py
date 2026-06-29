from __future__ import annotations

from fastapi.testclient import TestClient

from leetcode_portfolio_sync.api import create_app
from leetcode_portfolio_sync.config import AppConfig, CacheSettings, RepositorySettings


def test_api_exposes_analytics_and_sync_status(tmp_path) -> None:
    config = AppConfig(
        repository=RepositorySettings(local_path=tmp_path / "portfolio"),
        cache=CacheSettings(sqlite_path=tmp_path / "cache.sqlite3"),
    )
    client = TestClient(create_app(config))

    analytics = client.get("/analytics")
    status = client.get("/sync/status")

    assert analytics.status_code == 200
    assert status.status_code == 200
    assert analytics.json()["total_solved"] == 0
    assert status.json()["queue_depth"] == 0
