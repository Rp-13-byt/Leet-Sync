from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import SolvedProblem


class DatabaseManager:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init(self) -> None:
        with self.connect() as db:
            # Core cache table
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    namespace TEXT,
                    key TEXT,
                    value TEXT,
                    updated_at REAL,
                    PRIMARY KEY (namespace, key)
                )
                """
            )
            # Sync events table (for compatibility)
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT,
                    payload TEXT,
                    created_at REAL
                )
                """
            )
            # Problems table
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS problems (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    title_slug TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    tags TEXT NOT NULL, -- JSON list of tags
                    url TEXT NOT NULL,
                    statement TEXT,
                    constraints TEXT, -- JSON list of constraints
                    hints TEXT -- JSON list of hints
                )
                """
            )
            # Submissions table
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS submissions (
                    submission_id TEXT PRIMARY KEY,
                    problem_id INTEGER NOT NULL,
                    language TEXT NOT NULL,
                    code TEXT NOT NULL,
                    runtime TEXT,
                    memory TEXT,
                    submitted_at TEXT NOT NULL, -- ISO timestamp
                    status TEXT NOT NULL,
                    analysis TEXT, -- JSON CodeAnalysis
                    review TEXT, -- JSON CodeReview
                    recommendations TEXT, -- JSON list of Recommendations
                    FOREIGN KEY (problem_id) REFERENCES problems (id)
                )
                """
            )
            # Documentation versions table
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS documentation_versions (
                    problem_id INTEGER PRIMARY KEY,
                    readme TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    FOREIGN KEY (problem_id) REFERENCES problems (id)
                )
                """
            )
            # Sync history table
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT NOT NULL,
                    payload TEXT NOT NULL, -- JSON payload
                    created_at REAL NOT NULL
                )
                """
            )

    # Cache Compatibility API
    def get(self, namespace: str, key: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT value FROM cache WHERE namespace = ? AND key = ?",
                (namespace, key),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def set(self, namespace: str, key: str, value: dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO cache (namespace, key, value, updated_at) VALUES (?, ?, ?, ?)",
                (namespace, key, json.dumps(value), time.time()),
            )

    def event(self, name: str, payload: dict[str, Any]) -> None:
        now = time.time()
        with self.connect() as db:
            db.execute(
                "INSERT INTO sync_events (event, payload, created_at) VALUES (?, ?, ?)",
                (name, json.dumps(payload), now),
            )
            db.execute(
                "INSERT INTO sync_history (event, payload, created_at) VALUES (?, ?, ?)",
                (name, json.dumps(payload), now),
            )

    def events(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT event, payload, created_at FROM sync_history ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {"event": event, "payload": json.loads(payload), "created_at": created_at}
            for event, payload, created_at in rows
        ]

    # Portfolio API
    def save_solved_problem(self, solved: SolvedProblem) -> None:
        problem = solved.problem
        submission = solved.submission
        analysis = solved.analysis
        review = solved.review
        recommendations = solved.recommendations

        with self.connect() as db:
            db.execute(
                """
                INSERT OR REPLACE INTO problems (id, title, title_slug, difficulty, tags, url, statement, constraints, hints)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    problem.id,
                    problem.title,
                    problem.title_slug,
                    problem.difficulty.value,
                    json.dumps(problem.tags),
                    str(problem.url),
                    problem.statement,
                    json.dumps(problem.constraints),
                    json.dumps(problem.hints),
                ),
            )
            db.execute(
                """
                INSERT OR REPLACE INTO submissions (submission_id, problem_id, language, code, runtime, memory, submitted_at, status, analysis, review, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    submission.submission_id,
                    problem.id,
                    submission.language,
                    submission.code,
                    submission.runtime,
                    submission.memory,
                    submission.submitted_at.isoformat(),
                    submission.status,
                    json.dumps(analysis.model_dump(mode="json")) if analysis else None,
                    json.dumps(review.model_dump(mode="json")) if review else None,
                    json.dumps([r.model_dump(mode="json") for r in recommendations]),
                ),
            )

    def save_documentation(self, problem_id: int, readme: str, notes: str) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT OR REPLACE INTO documentation_versions (problem_id, readme, notes, generated_at)
                VALUES (?, ?, ?, ?)
                """,
                (problem_id, readme, notes, datetime.now(timezone.utc).isoformat()),
            )

    def get_solved_problems(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                """
                SELECT p.id, p.title, p.title_slug, p.difficulty, p.tags, p.url, p.statement, p.constraints, p.hints,
                       s.submission_id, s.language, s.code, s.runtime, s.memory, s.submitted_at, s.status, s.analysis, s.review, s.recommendations
                FROM problems p
                JOIN submissions s ON p.id = s.problem_id
                ORDER BY p.id ASC
                """
            ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            (
                p_id, p_title, p_slug, p_diff, p_tags, p_url, p_stmt, p_const, p_hints,
                s_id, s_lang, s_code, s_runtime, s_memory, s_sub_at, s_status, s_anal, s_rev, s_recs
            ) = row

            submitted_at = datetime.fromisoformat(s_sub_at)
            analysis = json.loads(s_anal) if s_anal else None
            review = json.loads(s_rev) if s_rev else None
            recs = json.loads(s_recs) if s_recs else []

            results.append({
                "id": p_id,
                "title": p_title,
                "title_slug": p_slug,
                "difficulty": p_diff,
                "language": s_lang,
                "runtime": s_runtime,
                "memory": s_memory,
                "submission_time": submitted_at.strftime("%H:%M:%S"),
                "submission_date": submitted_at.date().isoformat(),
                "submission_id": s_id,
                "url": p_url,
                "tags": json.loads(p_tags),
                "hints": json.loads(p_hints),
                "analysis": analysis,
                "review": review,
                "recommendations": recs,
            })
        return results
