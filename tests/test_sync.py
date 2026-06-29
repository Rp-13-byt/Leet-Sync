from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from leetcode_portfolio_sync.config import AppConfig, CacheSettings, RepositorySettings
from leetcode_portfolio_sync.documentation import DeterministicDocumentationProvider
from leetcode_portfolio_sync.models import Difficulty, ProblemMetadata, Submission
from leetcode_portfolio_sync.portfolio import PortfolioRepository
from leetcode_portfolio_sync.sync import SyncEngine


class FakeLeetCode:
    def problem(self, title_slug: str) -> ProblemMetadata:
        return ProblemMetadata(
            id=238,
            title="Product of Array Except Self",
            title_slug=title_slug,
            difficulty=Difficulty.MEDIUM,
            tags=["Array", "Prefix Sum"],
            url=f"https://leetcode.com/problems/{title_slug}/",
            statement="Return products.",
        )

    def submission(self, submission_id: str) -> Submission:
        return Submission(
            submission_id=submission_id,
            language="Python",
            code="class Solution:\n    def productExceptSelf(self, nums):\n        return nums\n",
            runtime="42 ms",
            memory="20 MB",
            submitted_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )


class FakeDocs:
    def __init__(self) -> None:
        self.provider = DeterministicDocumentationProvider()

    def generate(self, solved):
        return self.provider.generate(solved)


class FakeGit:
    def __init__(self) -> None:
        self.message = ""

    def create_github_repository(self, token: str) -> None:
        return None

    def commit_and_push(self, message: str, auto_push: bool) -> tuple[bool, bool]:
        self.message = message
        return True, auto_push


def test_sync_submission_generates_and_commits(tmp_path: Path) -> None:
    config = AppConfig(
        repository=RepositorySettings(local_path=tmp_path, auto_push=True),
        cache=CacheSettings(sqlite_path=tmp_path / "cache.sqlite3"),
    )
    fake_git = FakeGit()
    engine = SyncEngine(
        config,
        leetcode=FakeLeetCode(),  # type: ignore[arg-type]
        portfolio=PortfolioRepository(config),
        docs=FakeDocs(),  # type: ignore[arg-type]
        git=fake_git,  # type: ignore[arg-type]
    )

    result = engine.sync_submission("product-of-array-except-self", "999")

    assert result.changed is True
    assert result.committed is True
    assert result.pushed is True
    assert (
        fake_git.message
        == "feat(leetcode): solve #0238 Product of Array Except Self (Python)"
    )
