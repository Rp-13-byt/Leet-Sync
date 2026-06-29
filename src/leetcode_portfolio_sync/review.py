from __future__ import annotations

import json
import logging
import re
from textwrap import dedent

from .config import AppConfig
from .models import CodeAnalysis, CodeReview, CodeReviewFinding, SolvedProblem

LOGGER = logging.getLogger(__name__)


class CodeReviewService:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config

    def review(self, solved: SolvedProblem, analysis: CodeAnalysis) -> CodeReview:
        if self.config and self.config.documentation.provider in {"openai", "gemini"}:
            try:
                return self._ai_review(solved, analysis)
            except (
                Exception
            ) as exc:  # noqa: BLE001 - static review is the safe fallback.
                LOGGER.warning("AI code review failed; using static review: %s", exc)
        return self._static_review(solved, analysis)

    def _static_review(
        self, solved: SolvedProblem, analysis: CodeAnalysis
    ) -> CodeReview:
        findings: list[CodeReviewFinding] = []
        code = solved.submission.code
        if "eval(" in code or "exec(" in code:
            findings.append(
                CodeReviewFinding(
                    severity="high",
                    title="Avoid dynamic code execution",
                    detail="The accepted solution uses eval/exec, which is unsafe in reusable portfolio code.",
                )
            )
        if analysis.max_loop_depth >= 3:
            findings.append(
                CodeReviewFinding(
                    severity="medium",
                    title="Deeply nested loops",
                    detail="The implementation may have cubic or worse behavior; confirm this is intended.",
                )
            )
        if re.search(r"\bprint\s*\(", code):
            findings.append(
                CodeReviewFinding(
                    severity="low",
                    title="Debug output",
                    detail="Remove debug prints before presenting the solution in interviews.",
                )
            )
        summary = (
            "Static review found no blocking concerns."
            if not findings
            else f"Static review found {len(findings)} item(s) to inspect."
        )
        return CodeReview(
            summary=summary,
            findings=findings,
            security_notes=["No credential access detected."],
            maintainability_notes=[
                f"Detected patterns: {', '.join(analysis.patterns)}.",
                f"Estimated complexity: {analysis.time_complexity} time, {analysis.space_complexity} space.",
            ],
        )

    def _ai_review(self, solved: SolvedProblem, analysis: CodeAnalysis) -> CodeReview:
        prompt = dedent(f"""
            Review this accepted LeetCode solution as JSON with keys summary,
            findings, security_notes, and maintainability_notes. Findings must use
            severity, title, detail, and optional line. Do not invent facts.

            Problem: {solved.problem.title}
            Language: {solved.submission.language}
            Static analysis: {analysis.model_dump_json()}
            Code:
            {solved.submission.code}
            """).strip()
        if self.config and self.config.documentation.provider == "openai":
            from openai import OpenAI

            openai_response = OpenAI().responses.create(
                model=self.config.documentation.model,
                temperature=0,
                input=prompt,
            )
            return parse_review(openai_response.output_text)
        if self.config and self.config.documentation.provider == "gemini":
            import google.generativeai as genai

            gemini_response = genai.GenerativeModel(
                self.config.documentation.model,
            ).generate_content(prompt)
            return parse_review(str(gemini_response.text or "{}"))
        return self._static_review(solved, analysis)


def parse_review(text: str) -> CodeReview:
    payload = json.loads(text)
    return CodeReview(
        summary=str(payload.get("summary") or "AI review completed."),
        findings=[
            CodeReviewFinding(
                severity=str(item.get("severity", "info")),
                title=str(item.get("title", "Review finding")),
                detail=str(item.get("detail", "Not Available")),
                line=item.get("line"),
            )
            for item in payload.get("findings", [])
        ],
        security_notes=[str(item) for item in payload.get("security_notes", [])],
        maintainability_notes=[
            str(item) for item in payload.get("maintainability_notes", [])
        ],
    )
