# Developer Guide

Run the Python checks:

```powershell
ruff check src tests
black --check src tests
mypy src
pytest
```

Run the dashboard:

```powershell
cd dashboard
npm install
npm run dev
```

Add a language by extending `LANGUAGE_EXTENSIONS` in `src/leetcode_portfolio_sync/models.py`.

Add a platform by implementing `CodingPlatform` in `src/leetcode_portfolio_sync/platforms.py`.
Keep platform-specific authentication and fetching inside the plugin. The sync engine
should continue to receive normalized `ProblemMetadata` and `Submission` objects.

Add analyzer support by extending `CodeAnalyzer`. Prefer AST parsers where available and
fall back to conservative heuristics when a language parser is not part of the runtime.
