# Contributing

## Development

```powershell
python -m pip install -e ".[dev]"
pre-commit install
pytest
```

Keep changes typed, tested, and scoped. For LeetCode and GitHub integrations, prefer mocked tests unless an integration test is explicitly marked and documented.

## Pull Requests

- Explain the user-facing change.
- Include tests for behavior changes.
- Run linting, typing, and tests before submitting.
- Do not commit credentials or personal LeetCode session values.
