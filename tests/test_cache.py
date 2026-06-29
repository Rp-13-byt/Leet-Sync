from __future__ import annotations

from leetcode_portfolio_sync.cache import SQLiteCache


def test_sqlite_cache_round_trips_values_and_events(tmp_path) -> None:
    cache = SQLiteCache(tmp_path / "cache.sqlite3")

    cache.set("problem", "two-sum", {"id": 1})
    cache.event("sync_completed", {"submission_id": "123"})

    assert cache.get("problem", "two-sum") == {"id": 1}
    assert cache.events()[0]["event"] == "sync_completed"
