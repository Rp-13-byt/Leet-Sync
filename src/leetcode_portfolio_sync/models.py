from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class Difficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class Language(str, Enum):
    PYTHON = "Python"
    JAVA = "Java"
    CPP = "C++"
    C = "C"
    JAVASCRIPT = "JavaScript"
    TYPESCRIPT = "TypeScript"
    GO = "Go"
    RUST = "Rust"
    KOTLIN = "Kotlin"
    SWIFT = "Swift"
    PHP = "PHP"
    RUBY = "Ruby"
    CSHARP = "C#"
    SCALA = "Scala"


LANGUAGE_EXTENSIONS: dict[str, str] = {
    "Python": "py",
    "Python3": "py",
    "Java": "java",
    "C++": "cpp",
    "C": "c",
    "JavaScript": "js",
    "TypeScript": "ts",
    "Go": "go",
    "Rust": "rs",
    "Kotlin": "kt",
    "Swift": "swift",
    "PHP": "php",
    "Ruby": "rb",
    "C#": "cs",
    "Scala": "scala",
}


class Example(BaseModel):
    input: str = "Not Available"
    output: str = "Not Available"
    explanation: str = "Not Available"


class ProblemMetadata(BaseModel):
    id: int
    title: str
    title_slug: str
    difficulty: Difficulty
    tags: list[str] = Field(default_factory=list)
    url: HttpUrl | str
    statement: str = "Not Available"
    examples: list[Example] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)


class Submission(BaseModel):
    submission_id: str
    language: str
    code: str
    runtime: str = "Not Available"
    memory: str = "Not Available"
    submitted_at: datetime
    status: str = "Accepted"


class CodeAnalysis(BaseModel):
    language: str
    algorithms: list[str] = Field(default_factory=list)
    data_structures: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    uses_recursion: bool = False
    uses_graph_traversal: bool = False
    uses_dynamic_programming: bool = False
    uses_greedy: bool = False
    uses_sliding_window: bool = False
    loop_count: int = 0
    branch_count: int = 0
    function_count: int = 0
    max_loop_depth: int = 0
    time_complexity: str = "Not Available"
    space_complexity: str = "Not Available"
    explanation: str = "Not Available"
    mermaid: str = "Not Available"


class CodeReviewFinding(BaseModel):
    severity: str
    title: str
    detail: str
    line: int | None = None


class CodeReview(BaseModel):
    summary: str = "No issues detected by static review."
    findings: list[CodeReviewFinding] = Field(default_factory=list)
    security_notes: list[str] = Field(default_factory=list)
    maintainability_notes: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    id: int | None = None
    title: str
    difficulty: str = "Not Available"
    reason: str
    url: str = "Not Available"


class SolvedProblem(BaseModel):
    problem: ProblemMetadata
    submission: Submission
    analysis: CodeAnalysis | None = None
    review: CodeReview | None = None
    recommendations: list[Recommendation] = Field(default_factory=list)

    @property
    def folder_name(self) -> str:
        return f"{self.problem.id:04d}-{self.problem.title_slug}"

    @property
    def solution_filename(self) -> str:
        extension = LANGUAGE_EXTENSIONS.get(self.submission.language, "txt")
        return f"solution.{extension}"

    def metadata_json(self) -> dict[str, Any]:
        submitted_at = self.submission.submitted_at
        return {
            "id": self.problem.id,
            "title": self.problem.title,
            "title_slug": self.problem.title_slug,
            "difficulty": self.problem.difficulty.value,
            "language": self.submission.language,
            "runtime": self.submission.runtime,
            "memory": self.submission.memory,
            "submission_time": submitted_at.strftime("%H:%M:%S"),
            "submission_date": submitted_at.date().isoformat(),
            "submission_id": self.submission.submission_id,
            "url": str(self.problem.url),
            "tags": self.problem.tags,
            "hints": self.problem.hints,
            "analysis": (
                self.analysis.model_dump(mode="json") if self.analysis else None
            ),
            "review": self.review.model_dump(mode="json") if self.review else None,
            "recommendations": [
                recommendation.model_dump(mode="json")
                for recommendation in self.recommendations
            ],
        }


class GeneratedDocumentation(BaseModel):
    readme: str
    notes: str


class SyncResult(BaseModel):
    changed: bool
    committed: bool
    pushed: bool
    commit_message: str | None = None
    paths: list[Path] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
