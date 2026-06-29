from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from .config import AppConfig
from .models import GeneratedDocumentation, SolvedProblem
from .stats import build_stats, load_metadata


class PortfolioRepository:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.root = config.repository.local_path

    def ensure(self) -> None:
        for path in [
            self.root,
            self.root / "solutions" / "Easy",
            self.root / "solutions" / "Medium",
            self.root / "solutions" / "Hard",
            self.root / "topics",
            self.root / "difficulty",
            self.root / "assets",
        ]:
            path.mkdir(parents=True, exist_ok=True)
        config_file = self.root / "config.yaml"
        if not config_file.exists():
            config_file.write_text(
                yaml.safe_dump(self.config.model_dump(mode="json"), sort_keys=False),
                encoding="utf-8",
            )

    def upsert_problem(
        self,
        solved: SolvedProblem,
        docs: GeneratedDocumentation,
    ) -> list[Path]:
        self.ensure()
        folder = self.problem_folder(solved)
        folder.mkdir(parents=True, exist_ok=True)
        solution_path = folder / solved.solution_filename
        for existing in folder.glob("solution.*"):
            if existing != solution_path:
                existing.unlink()
        files = {
            folder / "README.md": docs.readme,
            folder / "notes.md": docs.notes,
            solution_path: solved.submission.code,
            folder
            / "metadata.json": json.dumps(
                solved.metadata_json(),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
        }
        changed: list[Path] = []
        for path, content in files.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                path.write_text(content, encoding="utf-8")
                changed.append(path)
        changed.extend(self.regenerate_indexes())
        return changed

    def problem_folder(self, solved: SolvedProblem) -> Path:
        return (
            self.root
            / "solutions"
            / solved.problem.difficulty.value
            / solved.folder_name
        )

    def regenerate_indexes(self) -> list[Path]:
        from .cache import SQLiteCache

        db = SQLiteCache(self.config.cache.sqlite_path)
        items = db.get_solved_problems()
        if not items:
            items = load_metadata(self.root)
        stats = build_stats(items)
        outputs = {
            self.root / "stats.json": json.dumps(stats, indent=2, ensure_ascii=False)
            + "\n",
            self.root / "README.md": render_root_readme(items, stats),
        }
        outputs.update(render_difficulty_indexes(self.root, items))
        outputs.update(render_topic_indexes(self.root, items))
        changed: list[Path] = []
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                path.write_text(content, encoding="utf-8")
                changed.append(path)
        return changed


def render_root_readme(items: list[dict[str, Any]], stats: dict[str, Any]) -> str:
    table = "\n".join(
        problem_row(item) for item in sorted(items, key=lambda item: int(item["id"]))
    )
    languages = (
        ", ".join(
            f"{language}: {count}"
            for language, count in stats["language_distribution"].items()
        )
        or "Not Available"
    )
    topics = (
        ", ".join(
            f"{topic}: {count}" for topic, count in stats["topic_distribution"].items()
        )
        or "Not Available"
    )
    recent = (
        "\n".join(
            f"- #{item['id']:04d} {item['title']} ({item['language']})"
            for item in stats["recently_solved"]
        )
        or "Not Available"
    )
    return f"""# LeetCode Portfolio

![Solved](https://img.shields.io/badge/Solved-{stats['total_solved']}-brightgreen)
![Current Streak](https://img.shields.io/badge/Current%20Streak-{stats['current_streak']}-orange)
![Longest Streak](https://img.shields.io/badge/Longest%20Streak-{stats['longest_streak']}-blue)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Repository Dashboard

- Total Solved: {stats['total_solved']}
- Easy Count: {stats['easy']}
- Medium Count: {stats['medium']}
- Hard Count: {stats['hard']}
- Current Streak: {stats['current_streak']}
- Longest Streak: {stats['longest_streak']}
- Language Distribution: {languages}
- Topic Distribution: {topics}

## Progress Bars

Easy: {progress(stats['easy'], stats['total_solved'])}

Medium: {progress(stats['medium'], stats['total_solved'])}

Hard: {progress(stats['hard'], stats['total_solved'])}

## Recently Solved

{recent}

## Searchable Table

| Problem | Difficulty | Language | Tags | Solution Link | Documentation Link |
| --- | --- | --- | --- | --- | --- |
{table}

## Latest Commits

Generated by LeetCode Portfolio Sync. Run `git log --oneline -10` for the latest commit list.
"""


def progress(value: int, total: int) -> str:
    if total == 0:
        return "`[----------] 0%`"
    filled = round((value / total) * 10)
    return f"`[{'#' * filled}{'-' * (10 - filled)}] {round((value / total) * 100)}%`"


def problem_row(item: dict[str, Any]) -> str:
    title_slug = item.get("title_slug") or slugify(str(item["title"]))
    folder = f"solutions/{item['difficulty']}/{int(item['id']):04d}-{title_slug}"
    solution = next_solution_name(item.get("language", ""))
    return (
        f"| #{int(item['id']):04d} {item['title']} | {item['difficulty']} | "
        f"{item['language']} | {', '.join(item.get('tags', [])) or 'Not Available'} | "
        f"[Solution]({folder}/{solution}) | [Docs]({folder}/README.md) |"
    )


def next_solution_name(language: str) -> str:
    from .models import LANGUAGE_EXTENSIONS

    return f"solution.{LANGUAGE_EXTENSIONS.get(language, 'txt')}"


def render_difficulty_indexes(
    root: Path, items: list[dict[str, Any]]
) -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    for difficulty in ["Easy", "Medium", "Hard"]:
        rows = "\n".join(
            problem_row(item) for item in items if item["difficulty"] == difficulty
        )
        outputs[root / "difficulty" / f"{difficulty}.md"] = (
            f"# {difficulty}\n\n| Problem | Difficulty | Language | Tags | Solution Link | Documentation Link |\n"
            f"| --- | --- | --- | --- | --- | --- |\n{rows}\n"
        )
    return outputs


def render_topic_indexes(root: Path, items: list[dict[str, Any]]) -> dict[Path, str]:
    by_topic: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        for tag in item.get("tags", []) or ["Uncategorized"]:
            by_topic.setdefault(str(tag), []).append(item)
    return {
        root
        / "topics"
        / f"{slugify(topic).replace('-', '')}.md": (
            f"# {topic}\n\n| Problem | Difficulty | Language | Tags | Solution Link | Documentation Link |\n"
            f"| --- | --- | --- | --- | --- | --- |\n"
            + "\n".join(problem_row(item) for item in topic_items)
            + "\n"
        )
        for topic, topic_items in by_topic.items()
    }


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
