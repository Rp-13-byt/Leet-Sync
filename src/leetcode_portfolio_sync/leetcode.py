from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Any, cast

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import AppConfig
from .models import Difficulty, Example, ProblemMetadata, Submission

QUESTION_QUERY = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionFrontendId
    title
    titleSlug
    difficulty
    content
    exampleTestcases
    hints
    topicTags { name }
  }
}
"""

RECENT_SUBMISSIONS_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id
    title
    titleSlug
    timestamp
  }
}
"""

SUBMISSION_DETAILS_QUERY = """
query submissionDetails($submissionId: Int!) {
  submissionDetails(submissionId: $submissionId) {
    code
    runtime
    memory
    lang { verboseName }
    timestamp
    statusDisplay
    question { titleSlug }
  }
}
"""


class LeetCodeClient:
    def __init__(
        self,
        config: AppConfig,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config
        self.session = session or requests.Session()
        if session is None:
            retry = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=("POST", "GET"),
            )
            self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def _headers(self) -> dict[str, str]:
        csrf = self._env(self.config.leetcode.csrf_env)
        headers = {
            "Content-Type": "application/json",
            "Referer": self.config.leetcode.base_url,
            "User-Agent": "leetcode-portfolio-sync/1.0",
        }
        if csrf:
            headers["x-csrftoken"] = csrf
        return headers

    def _env(self, name: str) -> str:
        import os

        return os.getenv(name, "")

    def _cookies(self) -> dict[str, str]:
        session_cookie = self._env(self.config.leetcode.session_env)
        csrf = self._env(self.config.leetcode.csrf_env)
        cookies: dict[str, str] = {}
        if session_cookie:
            cookies["LEETCODE_SESSION"] = session_cookie
        if csrf:
            cookies["csrftoken"] = csrf
        return cookies

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(
            self.config.leetcode.graphql_url,
            json={"query": query, "variables": variables},
            headers=self._headers(),
            cookies=self._cookies(),
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            messages = "; ".join(
                error.get("message", "Unknown error") for error in payload["errors"]
            )
            raise RuntimeError(f"LeetCode GraphQL error: {messages}")
        return cast(dict[str, Any], payload["data"])

    def accepted_submissions(
        self, username: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        data = self.graphql(
            RECENT_SUBMISSIONS_QUERY, {"username": username, "limit": limit}
        )
        return list(data.get("recentAcSubmissionList") or [])

    def submission(self, submission_id: str) -> Submission:
        data = self.graphql(
            SUBMISSION_DETAILS_QUERY, {"submissionId": int(submission_id)}
        )
        details = data["submissionDetails"]
        timestamp = int(details.get("timestamp") or 0)
        submitted_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return Submission(
            submission_id=submission_id,
            language=details.get("lang", {}).get("verboseName") or "Not Available",
            code=details.get("code") or "",
            runtime=details.get("runtime") or "Not Available",
            memory=details.get("memory") or "Not Available",
            submitted_at=submitted_at,
            status=details.get("statusDisplay") or "Accepted",
        )

    def problem(self, title_slug: str) -> ProblemMetadata:
        data = self.graphql(QUESTION_QUERY, {"titleSlug": title_slug})
        question = data["question"]
        statement = html_to_markdown(question.get("content") or "Not Available")
        return ProblemMetadata(
            id=int(question["questionFrontendId"]),
            title=question["title"],
            title_slug=question["titleSlug"],
            difficulty=Difficulty(question["difficulty"]),
            tags=[tag["name"] for tag in question.get("topicTags") or []],
            url=f"{self.config.leetcode.base_url}/problems/{title_slug}/",
            statement=statement,
            examples=parse_examples(statement),
            constraints=parse_constraints(statement),
            hints=question.get("hints") or [],
        )


def html_to_markdown(content: str) -> str:
    text = html.unescape(content)
    replacements = [
        (r"<pre>", "\n```text\n"),
        (r"</pre>", "\n```\n"),
        (r"<code>", "`"),
        (r"</code>", "`"),
        (r"</p>", "\n\n"),
        (r"<li>", "- "),
        (r"</li>", "\n"),
        (r"<[^>]+>", ""),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", text).strip() or "Not Available"


def parse_examples(statement: str) -> list[Example]:
    blocks = re.findall(r"```text\n(.*?)\n```", statement, flags=re.DOTALL)
    examples: list[Example] = []
    for block in blocks:
        input_match = re.search(r"Input:\s*(.*)", block)
        output_match = re.search(r"Output:\s*(.*)", block)
        explanation_match = re.search(r"Explanation:\s*(.*)", block, flags=re.DOTALL)
        examples.append(
            Example(
                input=input_match.group(1).strip() if input_match else "Not Available",
                output=(
                    output_match.group(1).strip() if output_match else "Not Available"
                ),
                explanation=(
                    explanation_match.group(1).strip()
                    if explanation_match
                    else "Not Available"
                ),
            )
        )
    return examples


def parse_constraints(statement: str) -> list[str]:
    match = re.search(
        r"Constraints:\s*(.*)", statement, flags=re.DOTALL | re.IGNORECASE
    )
    if not match:
        return []
    return [
        line.strip("- ").strip() for line in match.group(1).splitlines() if line.strip()
    ]
