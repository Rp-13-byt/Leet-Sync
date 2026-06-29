# User Guide

Use `sync-recent` to import recent accepted submissions, `sync-submission` for a known accepted submission id, and `watch` to poll LeetCode continuously.

The generated portfolio is written to `repository.local_path`. Existing problem folders are updated in place, so the same problem is never duplicated when a newer accepted solution arrives.

Every accepted solution is analyzed before documentation is generated. The generated docs
include detected algorithms, data structures, Mermaid diagrams, complexity estimates,
code review notes, and recommended follow-up problems.

Documentation providers:

- `openai`: rich AI documentation through the OpenAI API.
- `gemini`: rich AI documentation through Gemini.
- `deterministic`: factual documentation from available metadata only.

Reliability features:

- local SQLite cache for sync events and fetched data
- retry queue for failed sync operations
- structured JSON logs for automation-friendly observability
