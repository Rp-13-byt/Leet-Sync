from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from cryptography.fernet import Fernet
from pydantic import BaseModel, Field


class GitHubSettings(BaseModel):
    owner: str = ""
    repository: str = "LeetCode-Portfolio"
    default_branch: str = "main"
    token_env: str = "GITHUB_TOKEN"
    oauth_client_id_env: str = "GITHUB_OAUTH_CLIENT_ID"
    auto_create: bool = True


class LeetCodeSettings(BaseModel):
    session_env: str = "LEETCODE_SESSION"
    csrf_env: str = "LEETCODE_CSRF_TOKEN"
    graphql_url: str = "https://leetcode.com/graphql"
    base_url: str = "https://leetcode.com"
    poll_seconds: int = 300


class DocumentationSettings(BaseModel):
    provider: Literal["openai", "gemini", "deterministic"] = "deterministic"
    model: str = "gpt-4.1-mini"
    temperature: float = 0.1
    require_llm: bool = False


class RepositorySettings(BaseModel):
    local_path: Path = Path("LeetCode-Portfolio")
    commit_style: str = "feat(leetcode): solve #{id:04d} {title} ({language})"
    auto_push: bool = True
    theme: Literal["light", "dark", "system"] = "system"


class CacheSettings(BaseModel):
    sqlite_path: Path = Path(".leetcode-portfolio-sync/cache.sqlite3")


class LoggingSettings(BaseModel):
    level: str = "INFO"
    json_logs: bool = True


class PlatformSettings(BaseModel):
    enabled: list[str] = Field(default_factory=lambda: ["leetcode"])


class AppConfig(BaseModel):
    github: GitHubSettings = Field(default_factory=GitHubSettings)
    leetcode: LeetCodeSettings = Field(default_factory=LeetCodeSettings)
    documentation: DocumentationSettings = Field(default_factory=DocumentationSettings)
    repository: RepositorySettings = Field(default_factory=RepositorySettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    platforms: PlatformSettings = Field(default_factory=PlatformSettings)
    dashboard_enabled: bool = True


def load_config(path: Path | str = "config.yaml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        return AppConfig()
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return AppConfig.model_validate(data)


def write_default_config(path: Path | str = "config.yaml") -> Path:
    config = AppConfig()
    config_path = Path(path)
    config_path.write_text(
        yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    return config_path


class SecretStore:
    """Small encrypted local store for optional desktop/server deployments."""

    def __init__(self, key_path: Path, secrets_path: Path) -> None:
        self.key_path = key_path
        self.secrets_path = secrets_path

    def _fernet(self) -> Fernet:
        if self.key_path.exists():
            key = self.key_path.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            self.key_path.write_bytes(key)
        return Fernet(key)

    def set(self, name: str, value: str) -> None:
        data = self.all()
        data[name] = value
        encrypted = self._fernet().encrypt(yaml.safe_dump(data).encode("utf-8"))
        self.secrets_path.parent.mkdir(parents=True, exist_ok=True)
        self.secrets_path.write_bytes(encrypted)

    def get(self, name: str) -> str | None:
        return self.all().get(name) or os.getenv(name)

    def all(self) -> dict[str, str]:
        if not self.secrets_path.exists():
            return {}
        decrypted = self._fernet().decrypt(self.secrets_path.read_bytes())
        return yaml.safe_load(decrypted.decode("utf-8")) or {}
