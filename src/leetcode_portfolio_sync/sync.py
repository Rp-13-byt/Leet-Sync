from __future__ import annotations

import os
import time
import logging

from .analysis import CodeAnalyzer
from .cache import SQLiteCache
from .config import AppConfig
from .documentation import DocumentationService
from .git_service import GitService
from .models import SolvedProblem, SyncResult
from .metrics import PerformanceMetrics
from .platforms import CodingPlatform, LeetCodePlatform
from .portfolio import PortfolioRepository
from .queue import RetryQueue
from .recommendations import RecommendationEngine
from .review import CodeReviewService

LOGGER = logging.getLogger(__name__)


class SyncEngine:
    def __init__(
        self,
        config: AppConfig,
        leetcode: CodingPlatform | None = None,
        portfolio: PortfolioRepository | None = None,
        docs: DocumentationService | None = None,
        git: GitService | None = None,
        analyzer: CodeAnalyzer | None = None,
        reviewer: CodeReviewService | None = None,
        recommender: RecommendationEngine | None = None,
        cache: SQLiteCache | None = None,
        queue: RetryQueue | None = None,
        metrics: PerformanceMetrics | None = None,
    ) -> None:
        self.config = config
        self.leetcode = leetcode or LeetCodePlatform(config)
        self.portfolio = portfolio or PortfolioRepository(config)
        self.docs = docs or DocumentationService(config)
        self.git = git or GitService(config)
        self.analyzer = analyzer or CodeAnalyzer()
        self.reviewer = reviewer or CodeReviewService(config)
        self.recommender = recommender or RecommendationEngine()
        self.cache = cache or SQLiteCache(config.cache.sqlite_path)
        self.queue = queue or RetryQueue(
            config.repository.local_path / ".retry-queue.json"
        )
        self.metrics = metrics or PerformanceMetrics()

    def sync_submission(self, title_slug: str, submission_id: str) -> SyncResult:
        try:
            with self.metrics.timer("sync_submission"):
                with self.metrics.timer("fetch_problem"):
                    problem = self.leetcode.problem(title_slug)
                with self.metrics.timer("fetch_submission"):
                    submission = self.leetcode.submission(submission_id)
                with self.metrics.timer("analyze_code"):
                    analysis = self.analyzer.analyze(
                        submission.code, submission.language
                    )
                    solved = SolvedProblem(
                        problem=problem,
                        submission=submission,
                        analysis=analysis,
                    )
                    solved.review = self.reviewer.review(solved, analysis)
                    solved.recommendations = self.recommender.recommend(
                        problem,
                        analysis.patterns,
                    )
                self.cache.set(
                    "submission",
                    submission_id,
                    solved.model_dump(mode="json"),
                )
                with self.metrics.timer("generate_documentation"):
                    documentation = self.docs.generate(solved)
                self.cache.save_solved_problem(solved)
                self.cache.save_documentation(problem.id, documentation.readme, documentation.notes)
                changed_paths = self.portfolio.upsert_problem(solved, documentation)
                if not changed_paths:
                    self.cache.event("sync_unchanged", {"submission_id": submission_id})
                    return SyncResult(changed=False, committed=False, pushed=False)
                token = os.getenv(self.config.github.token_env)
                if token:
                    self.git.create_github_repository(token)
                message = self.config.repository.commit_style.format(
                    id=problem.id,
                    title=problem.title,
                    language=submission.language,
                )
                with self.metrics.timer("git_sync"):
                    committed, pushed = self.git.commit_and_push(
                        message,
                        self.config.repository.auto_push,
                    )
                self.metrics.increment("submissions_synced")
                self.cache.event(
                    "sync_completed",
                    {
                        "submission_id": submission_id,
                        "changed": True,
                        "committed": committed,
                        "pushed": pushed,
                    },
                )
                LOGGER.info("Synced accepted submission %s", submission_id)
                return SyncResult(
                    changed=True,
                    committed=committed,
                    pushed=pushed,
                    commit_message=message,
                    paths=changed_paths,
                )
        except Exception as exc:  # noqa: BLE001 - failed syncs are queued for retry.
            self.queue.enqueue(
                "sync_submission",
                {"title_slug": title_slug, "submission_id": submission_id},
                str(exc),
            )
            self.cache.event(
                "sync_failed",
                {"submission_id": submission_id, "error": str(exc)},
            )
            LOGGER.exception("Failed to sync accepted submission %s", submission_id)
            return SyncResult(
                changed=False,
                committed=False,
                pushed=False,
                errors=[str(exc)],
            )

    def sync_recent(self, username: str, limit: int = 20) -> list[SyncResult]:
        results: list[SyncResult] = []
        for item in self.leetcode.accepted_submissions(username, limit):
            results.append(self.sync_submission(item["titleSlug"], str(item["id"])))
        return results

    def watch(self, username: str, limit: int = 20) -> None:
        seen: set[str] = set()
        while True:
            for item in self.leetcode.accepted_submissions(username, limit):
                submission_id = str(item["id"])
                if submission_id not in seen:
                    self.sync_submission(item["titleSlug"], submission_id)
                    seen.add(submission_id)
            time.sleep(self.config.leetcode.poll_seconds)
