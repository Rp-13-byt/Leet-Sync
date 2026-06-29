# Installation Guide

1. Install Python 3.10 or newer.
2. Install the package with `python -m pip install -e ".[dev]"`.
3. Copy `.env.example` to `.env` and add `LEETCODE_SESSION`, `LEETCODE_CSRF_TOKEN`, and `GITHUB_TOKEN`.
4. Copy `config.example.yaml` to `config.yaml`.
5. Run `leetcode-portfolio-sync sync-recent your-leetcode-username`.

For one-command startup, use `docker compose up --build`.
