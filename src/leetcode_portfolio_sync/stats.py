from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
import re


def load_metadata(repository_path: Path) -> list[dict[str, Any]]:
    return [
        __import__("json").loads(path.read_text(encoding="utf-8"))
        for path in repository_path.glob("solutions/*/*/metadata.json")
    ]


def build_stats(items: list[dict[str, Any]]) -> dict[str, Any]:
    difficulty = Counter(str(item.get("difficulty", "Not Available")) for item in items)
    languages = Counter(str(item.get("language", "Not Available")) for item in items)
    topics: Counter[str] = Counter()
    patterns: Counter[str] = Counter()
    runtimes: list[float] = []
    heatmap: Counter[str] = Counter()
    solved_dates: list[date] = []
    for item in items:
        for tag in item.get("tags", []):
            topics[str(tag)] += 1
        analysis = item.get("analysis") or {}
        for pattern in analysis.get("patterns", []):
            patterns[str(pattern)] += 1
        runtime = parse_runtime_ms(str(item.get("runtime", "")))
        if runtime is not None:
            runtimes.append(runtime)
        value = item.get("submission_date")
        if value:
            solved_date = datetime.fromisoformat(value).date()
            solved_dates.append(solved_date)
            heatmap[solved_date.isoformat()] += 1
    solved_dates = sorted(set(solved_dates))
    return {
        "total_solved": len(items),
        "easy": difficulty.get("Easy", 0),
        "medium": difficulty.get("Medium", 0),
        "hard": difficulty.get("Hard", 0),
        "current_streak": current_streak(solved_dates),
        "longest_streak": longest_streak(solved_dates),
        "language_distribution": dict(languages),
        "topic_distribution": dict(topics),
        "pattern_distribution": dict(patterns),
        "runtime_distribution": runtime_distribution(runtimes),
        "submission_heatmap": dict(heatmap),
        "recently_solved": sorted(
            items,
            key=lambda item: str(item.get("submission_date", "")),
            reverse=True,
        )[:10],
    }


def parse_runtime_ms(value: str) -> float | None:
    match = re.search(r"([\d.]+)\s*ms", value)
    return float(match.group(1)) if match else None


def runtime_distribution(values: list[float]) -> dict[str, int]:
    buckets = {"0-50ms": 0, "51-100ms": 0, "101-250ms": 0, "251ms+": 0}
    for value in values:
        if value <= 50:
            buckets["0-50ms"] += 1
        elif value <= 100:
            buckets["51-100ms"] += 1
        elif value <= 250:
            buckets["101-250ms"] += 1
        else:
            buckets["251ms+"] += 1
    return buckets


def current_streak(days: list[date]) -> int:
    if not days:
        return 0
    day_set = set(days)
    cursor = date.today()
    if cursor not in day_set:
        cursor -= timedelta(days=1)
    count = 0
    while cursor in day_set:
        count += 1
        cursor -= timedelta(days=1)
    return count


def longest_streak(days: list[date]) -> int:
    if not days:
        return 0
    longest = current = 1
    for previous, current_day in zip(days, days[1:]):
        if current_day == previous + timedelta(days=1):
            current += 1
        else:
            longest = max(longest, current)
            current = 1
    return max(longest, current)
