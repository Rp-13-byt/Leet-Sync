from __future__ import annotations

import json
import os
import subprocess
import time

import requests

from .config import AppConfig


class GitService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.root = config.repository.local_path
        self.queue_file = self.root / ".sync-queue.json"

    def ensure_repository(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if not (self.root / ".git").exists():
            self._run(["git", "init", "-b", self.config.github.default_branch])
        if not self._run(["git", "config", "user.name"], allow_failure=True).strip():
            self._run(["git", "config", "user.name", "LeetCode Portfolio Sync"])
        if not self._run(["git", "config", "user.email"], allow_failure=True).strip():
            self._run(
                [
                    "git",
                    "config",
                    "user.email",
                    "leetcode-portfolio-sync@users.noreply.github.com",
                ]
            )

    def ensure_remote(self) -> None:
        if not self.config.github.owner:
            return
        remote_url = f"https://github.com/{self.config.github.owner}/{self.config.github.repository}.git"
        current = self._run(["git", "remote", "get-url", "origin"], allow_failure=True)
        if not current.strip():
            self._run(["git", "remote", "add", "origin", remote_url])

    def create_github_repository(self, token: str) -> None:
        if not self.config.github.auto_create or not self.config.github.owner:
            return
        response = requests.get(
            f"https://api.github.com/repos/{self.config.github.owner}/{self.config.github.repository}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=30,
        )
        if response.status_code == 200:
            return
        if response.status_code != 404:
            response.raise_for_status()
        create = requests.post(
            "https://api.github.com/user/repos",
            json={
                "name": self.config.github.repository,
                "private": False,
                "auto_init": False,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=30,
        )
        create.raise_for_status()

    def commit_and_push(self, message: str, auto_push: bool) -> tuple[bool, bool]:
        self.ensure_repository()
        self.ensure_remote()
        self._run(["git", "add", "."])
        if not self._run(["git", "status", "--porcelain"]).strip():
            return False, False
        self._run(["git", "commit", "-m", message])
        if not auto_push:
            return True, False
        try:
            self._push_with_retry()
            self.replay_queue()
            return True, True
        except RuntimeError as exc:
            self.enqueue(message, str(exc))
            return True, False

    def enqueue(self, message: str, error: str) -> None:
        queue = []
        if self.queue_file.exists():
            queue = json.loads(self.queue_file.read_text(encoding="utf-8"))
        queue.append({"message": message, "error": error})
        self.queue_file.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")

    def replay_queue(self) -> None:
        if self.queue_file.exists():
            self.queue_file.unlink()

    def _push_with_retry(self) -> None:
        last_error: RuntimeError | None = None
        for attempt in range(3):
            try:
                token = os.getenv(self.config.github.token_env)
                remote = "origin"
                if token and self.config.github.owner:
                    remote = (
                        "https://x-access-token:"
                        f"{token}@github.com/{self.config.github.owner}/"
                        f"{self.config.github.repository}.git"
                    )
                self._run(
                    ["git", "push", "-u", remote, self.config.github.default_branch]
                )
                return
            except RuntimeError as exc:
                last_error = exc
                time.sleep(2**attempt)
        if last_error:
            raise last_error

    def _run(self, args: list[str], allow_failure: bool = False) -> str:
        result = subprocess.run(
            args,
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode and not allow_failure:
            message = result.stderr.strip() or result.stdout.strip()
            token = os.getenv(self.config.github.token_env)
            if token:
                message = message.replace(token, "***")
            raise RuntimeError(message)
        return result.stdout
