# Decisions archive

Superseded decisions, and decisions no longer relevant to current work. Active decisions: [DECISIONS.md](../DECISIONS.md).

| Date | Decision | Reason | Superseded by |
|---|---|---|---|
| 2026-10-24 (v10) | Do not deliver `tests.zip` or any test files unless the user asks; the tests stay in the chat sandbox. | Keep the hand-offs small. | 2026-11-01: the tests live in the repository's `tests/`. |
| v8 era (October 2026, exact day not recorded) | Deliver only the changed scripts after a build. The whole test folder, the checklist and the summary are delivered once, at hand-off. | The file upload/download workflow of plain chat. | 2026-11-01: agents edit files in the repository; the user commits. |
| v8–v11 | The milestone summary is the single source of truth. A new chat reads it completely first. | No shared file system between chats. | 2026-11-01: the repository workflow ([HOW-TO-GET-ORGANIZED.md](../HOW-TO-GET-ORGANIZED.md)). |
| v8–v11 | Project files at a fixed path on the old PC; the Claude Desktop config at `%APPDATA%\Claude`. | The old machine's layout. | 2026-11-01: the repository folder, and the Store build's own config location ([RUNBOOK.md](../RUNBOOK.md)). |
| v8–v11 | Scripts were developed and tested in Claude's sandbox (`/bin/sh`, no process substitution). | Plain-chat tooling. | 2026-11-01: tests run locally with the repository venv (PowerShell / Git Bash). |
| v9 | Test 136a will be run in a new chat; other work may come first. | | v10: superseded by tests 139a / 139b and 142. |
