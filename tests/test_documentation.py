from __future__ import annotations

from datetime import datetime, timezone

from leetcode_portfolio_sync.analysis import CodeAnalyzer
from leetcode_portfolio_sync.documentation import DeterministicDocumentationProvider
from leetcode_portfolio_sync.models import (
    Difficulty,
    ProblemMetadata,
    SolvedProblem,
    Submission,
)
from leetcode_portfolio_sync.recommendations import RecommendationEngine
from leetcode_portfolio_sync.review import CodeReviewService


def test_documentation_uses_code_analysis() -> None:
    submission = Submission(
        submission_id="1",
        language="Python",
        code="def solve(nums):\n    seen = set()\n    for n in nums:\n        seen.add(n)\n    return len(seen)\n",
        runtime="10 ms",
        memory="12 MB",
        submitted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    problem = ProblemMetadata(
        id=1,
        title="Two Sum",
        title_slug="two-sum",
        difficulty=Difficulty.EASY,
        tags=["Array", "Hash Table"],
        url="https://leetcode.com/problems/two-sum/",
    )
    analysis = CodeAnalyzer().analyze(submission.code, submission.language)
    solved = SolvedProblem(problem=problem, submission=submission, analysis=analysis)
    solved.review = CodeReviewService().review(solved, analysis)
    solved.recommendations = RecommendationEngine().recommend(
        problem, analysis.patterns
    )

    docs = DeterministicDocumentationProvider().generate(solved)

    assert "AI Code Review" in docs.readme
    assert "Flow Diagram" in docs.readme
    assert analysis.time_complexity in docs.readme
