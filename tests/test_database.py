from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from leetcode_portfolio_sync.database import DatabaseManager
from leetcode_portfolio_sync.models import (
    Difficulty,
    ProblemMetadata,
    SolvedProblem,
    Submission,
)


def solved_problem() -> SolvedProblem:
    return SolvedProblem(
        problem=ProblemMetadata(
            id=1,
            title="Two Sum",
            title_slug="two-sum",
            difficulty=Difficulty.EASY,
            tags=["Array", "Hash Table"],
            url="https://leetcode.com/problems/two-sum/",
            statement="Find two numbers.",
        ),
        submission=Submission(
            submission_id="123",
            language="Python",
            code="class Solution:\n    def twoSum(self, nums, target):\n        return []\n",
            runtime="32 ms",
            memory="17.9 MB",
            submitted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
    )


def test_database_manager_operations(tmp_path: Path) -> None:
    db_path = tmp_path / "test.sqlite"
    db = DatabaseManager(db_path)

    # 1. Test cache get/set
    db.set("test_namespace", "my_key", {"data": 42})
    cached = db.get("test_namespace", "my_key")
    assert cached == {"data": 42}

    # 2. Test event/events logging
    db.event("test_event", {"info": "success"})
    events = db.events(limit=5)
    assert len(events) == 1
    assert events[0]["event"] == "test_event"
    assert events[0]["payload"] == {"info": "success"}

    # 3. Test saving solved problem
    solved = solved_problem()
    db.save_solved_problem(solved)

    # 4. Test retrieving solved problem
    problems = db.get_solved_problems()
    assert len(problems) == 1
    p = problems[0]
    assert p["id"] == 1
    assert p["title"] == "Two Sum"
    assert p["difficulty"] == "Easy"
    assert p["language"] == "Python"
    assert p["submission_id"] == "123"
    assert p["tags"] == ["Array", "Hash Table"]

    # 5. Test documentation saving
    db.save_documentation(1, "# Readme content", "# Notes content")
    with db.connect() as conn:
        row = conn.execute(
            "SELECT readme, notes FROM documentation_versions WHERE problem_id = 1"
        ).fetchone()
    assert row is not None
    assert row[0] == "# Readme content"
    assert row[1] == "# Notes content"
