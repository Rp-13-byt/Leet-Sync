from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .config import AppConfig
from .leetcode import LeetCodeClient
from .models import ProblemMetadata, Submission


class CodingPlatform(ABC):
    name: str

    @abstractmethod
    def accepted_submissions(self, username: str, limit: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def problem(self, title_slug: str) -> ProblemMetadata:
        raise NotImplementedError

    @abstractmethod
    def submission(self, submission_id: str) -> Submission:
        raise NotImplementedError


class LeetCodePlatform(CodingPlatform):
    name = "leetcode"

    def __init__(self, config: AppConfig) -> None:
        self.client = LeetCodeClient(config)

    def accepted_submissions(self, username: str, limit: int) -> list[dict[str, Any]]:
        return self.client.accepted_submissions(username, limit)

    def problem(self, title_slug: str) -> ProblemMetadata:
        return self.client.problem(title_slug)

    def submission(self, submission_id: str) -> Submission:
        return self.client.submission(submission_id)


class PlatformRegistry:
    def __init__(self, config: AppConfig) -> None:
        self.platforms: dict[str, CodingPlatform] = {
            "leetcode": LeetCodePlatform(config)
        }

    def register(self, platform: CodingPlatform) -> None:
        self.platforms[platform.name] = platform

    def get(self, name: str) -> CodingPlatform:
        return self.platforms[name]
