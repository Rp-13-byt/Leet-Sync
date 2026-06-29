from __future__ import annotations

from datetime import date, timedelta

from leetcode_portfolio_sync.stats import build_stats, current_streak, longest_streak


def test_streaks() -> None:
    today = date.today()
    days = [today - timedelta(days=2), today - timedelta(days=1), today]

    assert current_streak(days) == 3
    assert longest_streak(days) == 3


def test_build_stats_counts_distributions() -> None:
    stats = build_stats(
        [
            {
                "id": 1,
                "title": "Two Sum",
                "difficulty": "Easy",
                "language": "Python",
                "submission_date": date.today().isoformat(),
                "tags": ["Array", "Hash Table"],
            },
            {
                "id": 2,
                "title": "Add Two Numbers",
                "difficulty": "Medium",
                "language": "Java",
                "submission_date": date.today().isoformat(),
                "tags": ["Linked List"],
            },
        ]
    )

    assert stats["total_solved"] == 2
    assert stats["easy"] == 1
    assert stats["medium"] == 1
    assert stats["language_distribution"] == {"Python": 1, "Java": 1}
    assert stats["topic_distribution"]["Array"] == 1
