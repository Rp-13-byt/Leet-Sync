from __future__ import annotations

import json
from datetime import datetime, timezone

from leetcode_portfolio_sync.config import AppConfig, RepositorySettings
from leetcode_portfolio_sync.models import (
    Difficulty,
    GeneratedDocumentation,
    ProblemMetadata,
    SolvedProblem,
    Submission,
)
from leetcode_portfolio_sync.portfolio import PortfolioRepository


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


def test_upsert_problem_writes_required_files(tmp_path) -> None:
    config = AppConfig(repository=RepositorySettings(local_path=tmp_path))
    repository = PortfolioRepository(config)

    changed = repository.upsert_problem(
        solved_problem(),
        GeneratedDocumentation(readme="# Problem\n", notes="# Notes\n"),
    )

    folder = tmp_path / "solutions" / "Easy" / "0001-two-sum"
    assert changed
    assert (folder / "README.md").exists()
    assert (folder / "solution.py").exists()
    assert (folder / "notes.md").exists()
    assert (folder / "metadata.json").exists()
    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "stats.json").exists()
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["id"] == 1
    assert metadata["language"] == "Python"
