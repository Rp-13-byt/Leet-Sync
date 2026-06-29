from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import AppConfig
from .cache import SQLiteCache
from .queue import RetryQueue
from .stats import build_stats, load_metadata
from .sync import SyncEngine


class SyncRecentRequest(BaseModel):
    username: str
    limit: int = 20


class SyncSubmissionRequest(BaseModel):
    title_slug: str
    submission_id: str


def create_app(config: AppConfig | None = None) -> FastAPI:
    settings = config or AppConfig()
    api = FastAPI(title="LeetCode Portfolio Sync", version="1.0.0")
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.get("/stats")
    def stats() -> dict[str, Any]:
        cache = SQLiteCache(settings.cache.sqlite_path)
        items = cache.get_solved_problems()
        if not items:
            items = load_metadata(settings.repository.local_path)
        return build_stats(items)

    @api.get("/problems")
    def problems() -> list[dict[str, Any]]:
        cache = SQLiteCache(settings.cache.sqlite_path)
        items = cache.get_solved_problems()
        if not items:
            items = load_metadata(settings.repository.local_path)
        return items

    @api.get("/sync/status")
    def sync_status() -> dict[str, Any]:
        cache = SQLiteCache(settings.cache.sqlite_path)
        queue = RetryQueue(settings.repository.local_path / ".retry-queue.json")
        return {
            "events": cache.events(),
            "queued_retries": queue.items(),
            "queue_depth": len(queue.items()),
        }

    @api.get("/analytics")
    def analytics() -> dict[str, Any]:
        cache = SQLiteCache(settings.cache.sqlite_path)
        items = cache.get_solved_problems()
        if not items:
            items = load_metadata(settings.repository.local_path)
        return build_stats(items)

    @api.post("/sync/recent")
    def sync_recent(request: SyncRecentRequest) -> list[dict[str, Any]]:
        try:
            return [
                result.model_dump(mode="json")
                for result in SyncEngine(settings).sync_recent(
                    request.username, request.limit
                )
            ]
        except Exception as exc:  # noqa: BLE001 - API should return structured failure.
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @api.post("/sync/submission")
    def sync_submission(request: SyncSubmissionRequest) -> dict[str, Any]:
        try:
            return (
                SyncEngine(settings)
                .sync_submission(
                    request.title_slug,
                    request.submission_id,
                )
                .model_dump(mode="json")
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return api
