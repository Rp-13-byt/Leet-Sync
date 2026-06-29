from __future__ import annotations

from pathlib import Path
import os

import typer
from dotenv import load_dotenv

from .api import create_app
from .config import SecretStore, load_config, write_default_config
from .github_oauth import GitHubOAuthDeviceFlow
from .logging import configure_logging
from .sync import SyncEngine

app = typer.Typer(help="Automatically sync accepted LeetCode submissions to GitHub.")


@app.callback()
def main() -> None:
    load_dotenv()
    settings = load_config()
    configure_logging(settings.logging.level, settings.logging.json_logs)
    secrets_dir = Path(".leetcode-portfolio-sync")
    if (secrets_dir / "key.bin").exists() and (secrets_dir / "secrets.enc").exists():
        for name, value in (
            SecretStore(
                secrets_dir / "key.bin",
                secrets_dir / "secrets.enc",
            )
            .all()
            .items()
        ):
            os.environ.setdefault(name, value)


@app.command()
def init(
    path: Path = typer.Option(Path("config.yaml"), help="Configuration path.")
) -> None:
    written = write_default_config(path)
    typer.echo(f"Created {written}")


@app.command()
def github_login(
    config: Path = typer.Option(Path("config.yaml")),
    secrets_dir: Path = typer.Option(Path(".leetcode-portfolio-sync")),
) -> None:
    settings = load_config(config)
    flow = GitHubOAuthDeviceFlow(settings.github.oauth_client_id_env)
    code = flow.start()
    typer.echo(f"Open {code.verification_uri} and enter code {code.user_code}.")
    token = flow.poll(code.device_code, code.interval)
    store = SecretStore(secrets_dir / "key.bin", secrets_dir / "secrets.enc")
    store.set(settings.github.token_env, token)
    typer.echo("GitHub token saved in the encrypted local secret store.")


@app.command()
def sync_recent(
    username: str = typer.Argument(..., help="LeetCode username."),
    limit: int = typer.Option(20, min=1, max=100),
    config: Path = typer.Option(Path("config.yaml")),
) -> None:
    engine = SyncEngine(load_config(config))
    results = engine.sync_recent(username=username, limit=limit)
    changed = sum(1 for result in results if result.changed)
    pushed = sum(1 for result in results if result.pushed)
    typer.echo(
        f"Processed {len(results)} accepted submissions; changed {changed}; pushed {pushed}."
    )


@app.command()
def sync_submission(
    title_slug: str = typer.Argument(
        ..., help="LeetCode title slug, for example two-sum."
    ),
    submission_id: str = typer.Argument(..., help="Accepted submission id."),
    config: Path = typer.Option(Path("config.yaml")),
) -> None:
    result = SyncEngine(load_config(config)).sync_submission(title_slug, submission_id)
    typer.echo(result.model_dump_json(indent=2))


@app.command()
def watch(
    username: str = typer.Argument(..., help="LeetCode username."),
    limit: int = typer.Option(20, min=1, max=100),
    config: Path = typer.Option(Path("config.yaml")),
) -> None:
    SyncEngine(load_config(config)).watch(username=username, limit=limit)


@app.command()
def serve(
    config: Path = typer.Option(Path("config.yaml")),
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8000),
) -> None:
    import uvicorn

    uvicorn.run(create_app(load_config(config)), host=host, port=port)


if __name__ == "__main__":
    app()
