from __future__ import annotations

import json
from abc import ABC, abstractmethod
from textwrap import dedent

from .config import AppConfig
from .models import GeneratedDocumentation, SolvedProblem


class DocumentationProvider(ABC):
    @abstractmethod
    def generate(self, solved: SolvedProblem) -> GeneratedDocumentation:
        raise NotImplementedError


class DocumentationService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.provider = self._provider()

    def _provider(self) -> DocumentationProvider:
        if self.config.documentation.provider == "openai":
            return OpenAIDocumentationProvider(self.config)
        if self.config.documentation.provider == "gemini":
            return GeminiDocumentationProvider(self.config)
        return DeterministicDocumentationProvider()

    def generate(self, solved: SolvedProblem) -> GeneratedDocumentation:
        return self.provider.generate(solved)


class OpenAIDocumentationProvider(DocumentationProvider):
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def generate(self, solved: SolvedProblem) -> GeneratedDocumentation:
        from openai import OpenAI

        client = OpenAI()
        response = client.responses.create(
            model=self.config.documentation.model,
            temperature=self.config.documentation.temperature,
            input=build_llm_prompt(solved),
        )
        return parse_llm_json(response.output_text)


class GeminiDocumentationProvider(DocumentationProvider):
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def generate(self, solved: SolvedProblem) -> GeneratedDocumentation:
        import google.generativeai as genai

        model = genai.GenerativeModel(self.config.documentation.model)
        response = model.generate_content(build_llm_prompt(solved))
        return parse_llm_json(response.text or "")


class DeterministicDocumentationProvider(DocumentationProvider):
    def generate(self, solved: SolvedProblem) -> GeneratedDocumentation:
        problem = solved.problem
        submission = solved.submission
        analysis = solved.analysis
        review = solved.review
        examples = (
            "\n\n".join(
                f"### Example {index}\n\nInput: `{example.input}`\n\nOutput: `{example.output}`\n\n"
                f"Explanation: {example.explanation}"
                for index, example in enumerate(problem.examples, start=1)
            )
            or "Not Available"
        )
        constraints = (
            "\n".join(f"- {item}" for item in problem.constraints) or "Not Available"
        )
        tags = ", ".join(problem.tags) or "Not Available"
        hints = "\n".join(f"- {hint}" for hint in problem.hints) or "Not Available"
        algorithms = ", ".join(analysis.algorithms) if analysis else "Not Available"
        structures = (
            ", ".join(analysis.data_structures) if analysis else "Not Available"
        )
        patterns = ", ".join(analysis.patterns) if analysis else "Not Available"
        mermaid = analysis.mermaid if analysis else "Not Available"
        review_summary = review.summary if review else "Not Available"
        findings = (
            "\n".join(
                f"- **{finding.severity}:** {finding.title}. {finding.detail}"
                for finding in (review.findings if review else [])
            )
            or "No issues detected by static review."
        )
        recommendations = (
            "\n".join(
                f"- [{item.title}]({item.url}) ({item.difficulty}): {item.reason}"
                for item in solved.recommendations
            )
            or "Not Available"
        )
        time_complexity = analysis.time_complexity if analysis else "Not Available"
        space_complexity = analysis.space_complexity if analysis else "Not Available"
        implementation_explanation = (
            analysis.explanation if analysis else "Not Available"
        )
        readme = dedent(f"""
            # Problem

            **Problem Number:** {problem.id}

            **Problem Name:** {problem.title}

            **Difficulty:** ![Difficulty](https://img.shields.io/badge/{problem.difficulty.value}-blue)

            **Tags:** {tags}

            **Language:** {submission.language}

            **LeetCode Link:** [{problem.title}]({problem.url})

            **Submission Date:** {submission.submitted_at.date().isoformat()}

            --------------------------------------------------

            ## Problem Statement

            {problem.statement}

            --------------------------------------------------

            ## Examples

            {examples}

            --------------------------------------------------

            ## Constraints

            {constraints}

            --------------------------------------------------

            ## Objective

            Solve `{problem.title}` according to the official statement and constraints.

            --------------------------------------------------

            ## Observations

            - Official tags: {tags}
            - Detected algorithms: {algorithms}
            - Detected data structures: {structures}
            - Hints:
            {hints}

            --------------------------------------------------

            ## Intuition

            The implementation suggests a `{patterns}` approach. It keeps state with
            `{structures}` and applies `{algorithms}` to move from the input toward
            the final answer.

            --------------------------------------------------

            ## Algorithm

            1. Read the input and initialize the state used by the accepted solution.
            2. Iterate or recurse according to the detected implementation structure.
            3. Update `{structures}` as each candidate state is processed.
            4. Return the value produced by the accepted solution.

            {implementation_explanation}

            ## Flow Diagram

            {mermaid}

            --------------------------------------------------

            ## Dry Run

            Not Available

            --------------------------------------------------

            ## Correctness Proof

            The implementation maintains the state described by `{structures}` while
            processing the input according to `{patterns}`. At each step, the state is
            updated only from values already inspected or from valid recursive/iterative
            transitions. When processing completes, every candidate required by the
            detected algorithm has been considered, so the returned value matches the
            objective defined by the problem.

            --------------------------------------------------

            ## Complexity Analysis

            **Time Complexity:** {time_complexity}

            **Space Complexity:** {space_complexity}

            Justification: Derived from the submitted code structure, including
            {analysis.loop_count if analysis else "Not Available"} loop(s),
            maximum loop depth {analysis.max_loop_depth if analysis else "Not Available"},
            and detected state containers `{structures}`.

            --------------------------------------------------

            ## Edge Cases

            - Minimum values: validate base cases and empty state initialization.
            - Maximum values: confirm the estimated {time_complexity} runtime is acceptable.
            - Duplicates: confirm `{structures}` handles repeated values correctly.
            - Empty input: confirm loops and return paths are still valid.
            - Overflow: verify numeric operations are safe for the submitted language.
            - Corner cases: review branch count {analysis.branch_count if analysis else "Not Available"}.

            --------------------------------------------------

            ## Alternative Solutions

            - Brute Force: Not Available
            - Better Solution: Not Available
            - Optimal Solution: Not Available
            - Trade-offs: Not Available

            --------------------------------------------------

            ## Pattern Recognition

            **Pattern Name:** {patterns}

            **Data Structures:** {structures}

            **Algorithms:** {algorithms}

            **Category:** {problem.difficulty.value}

            --------------------------------------------------

            ## Common Mistakes

            - Misidentifying the required state transition.
            - Updating pointers or memoized state in the wrong order.
            - Forgetting edge cases listed above.
            - Review findings:
            {findings}

            --------------------------------------------------

            ## Interview Perspective

            Interviewers can use this solution to discuss why `{patterns}` is suitable,
            how the detected data structures affect complexity, and whether the same
            objective can be solved with a simpler or more memory-efficient approach.

            --------------------------------------------------

            ## Learning Summary

            Key takeaways: {implementation_explanation}

            Related problems:
            {recommendations}

            Recommended next problems:
            {recommendations}

            --------------------------------------------------

            ## AI Code Review

            {review_summary}

            {findings}
            """).strip() + "\n"
        notes = dedent(f"""
            # Interview Revision Notes

            **Pattern:** {patterns}

            **Difficulty:** {problem.difficulty.value}

            **Important Concepts:** {algorithms}; {structures}

            **Core Trick:** {implementation_explanation}

            **Common Mistakes:** Review pointer/state updates, base cases, and detected findings.

            **Interview Tips:** Explain why the implementation has {time_complexity} time and {space_complexity} space.

            **Follow-up Questions:** Can memory be reduced? Can the same pattern handle larger constraints?

            **Revision Summary:** The submitted solution uses {patterns}. Review the diagram, complexity,
            and edge cases before interview practice.
            """).strip() + "\n"
        return GeneratedDocumentation(readme=readme, notes=notes)


def build_llm_prompt(solved: SolvedProblem) -> str:
    return dedent(f"""
        Generate professional LeetCode solution documentation as strict JSON with keys
        "readme" and "notes". Do not invent facts. If a detail cannot be inferred from
        the provided official metadata or accepted solution, write "Not Available".

        README must include all mandatory sections from the project specification.
        notes must include concise interview revision notes.

        CRITICAL DOCUMENTATION INSTRUCTIONS:
        1. Base your "Intuition" and "Algorithm" explanation on the user's actual accepted solution code.
        2. Use the provided AST signals ("Static code analysis" below) such as loop_count, branch_count, function_count, and max_loop_depth to describe the flow.
        3. Explain the "Complexity Analysis" (Time and Space Complexity) in direct relation to these AST signals. For example, explain how the loop depth or recursion structures justify the complexity.
        4. Detail "Edge Cases" specifically checked or handled in the branching structure (branch_count) of the code.

        Official metadata:
        {json.dumps(solved.problem.model_dump(mode="json"), indent=2)}

        Submission:
        {json.dumps(solved.submission.model_dump(mode="json"), indent=2)}

        Static code analysis (AST signals):
        {json.dumps(solved.analysis.model_dump(mode="json") if solved.analysis else None, indent=2)}

        Static code review:
        {json.dumps(solved.review.model_dump(mode="json") if solved.review else None, indent=2)}

        Recommended related problems:
        {json.dumps([item.model_dump(mode="json") for item in solved.recommendations], indent=2)}
        """).strip()


def parse_llm_json(text: str) -> GeneratedDocumentation:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Documentation provider returned invalid JSON") from exc
    return GeneratedDocumentation(
        readme=str(payload.get("readme") or "Not Available\n"),
        notes=str(payload.get("notes") or "Not Available\n"),
    )
