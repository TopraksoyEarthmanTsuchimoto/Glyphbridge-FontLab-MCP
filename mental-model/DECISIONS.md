# Decisions

Active decisions only, newest first. Each entry gives the date, the decision and the reason. Superseded or no longer relevant entries move to [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). Where the chat-era record gives no exact day, the entry says so.

## 2026-11-01: repository workflow (migration day)

- **No test may depend on the local file `savedtestfont.vfc` in the end.** Live tests build their reference glyphs in a fresh disposable font. `savedtestfont.vfc` may be used until it is no longer useful. Font files (`*.vfc`, `*.vfj`) are ignored by git. *Reason:* people who fork the repository must find everything they need in it ([ROADMAP.md](ROADMAP.md) §11).
- **The code comments get tidied in the next build (listener 0.96, server 0.32).** Each module docstring's version history moves to `archive/` (with a short live changelog from then on), and the listener's endpoint list is corrected and completed. The MCP tool docstrings stay as they are: they are the agents' tool descriptions. The `#` comments stay next to the code they protect, and only references to session and test numbers shrink to the fact. *Reason:* about 11,000 words of history sit at the top of the two scripts. The build still needs "Yes. Build v0.96 / v0.32 as described."
- **`.gitignore` lists only what this project produces.** *Reason:* the generic Python template made the repository look less maintained.

- **The repository is the source of truth.** The project follows [HOW-TO-GET-ORGANIZED.md](HOW-TO-GET-ORGANIZED.md), with all documentation in `mental-model/`. *Reason:* milestone summaries had grown to about 28,000 words, and every new chat had to rebuild the context. *Supersedes* "the milestone summary is the single source of truth".
- **CLAUDE.md joins the core set with a 200-word budget.** The reference total becomes 8,700 words including the root README, and 8,200 for the startup core files. *Reason:* Claude Code reads CLAUDE.md automatically, so it costs context in every session.
- **The CHECKLIST.md budget goes from 1,000 to 1,300 words.** The reference totals become 9,000 including the root README, and 8,500 for the startup core files. *Reason:* the first version used 994 of 1,000 words, which left no room for new scenarios.
- **`tests/README.md` stays in `tests/`**, an exception to the "all Markdown in `mental-model/`" rule. *Reason:* the user's choice, so it stays next to the harnesses it describes.
- **The repository is public.** Live files contain no personal paths, names, time zones or locales. *Reason:* the user's choice. The v11 summary snapshot was trimmed of those details before the first push.
- **The project folder is the cloned repository.** The scripts stay at the root, and the server uses its own `venv` there (Python 3.15.2, `mcp==2.2.0`, ignored by git). *Reason:* `run_all.py` reads the scripts from the parent of `tests/`, and the MCP configs point at the root.
- **Claude Code uses a committed `.mcp.json` with relative paths.** *Reason:* it works without user-specific paths in a public repository (verified).
- **The old `Notes\` folder stays out of the repository.** *Reason:* the user's choice.
- **The user commits and pushes with GitHub Desktop.** Agents do not commit unless asked.

## 2026-10-27: kerning (v11 session)

- **Read only the pairs a task needs, never the whole kerning table or font.** *Reason:* token cost.
- **There are no hard limits, but there is a threshold at 250 pairs.** Above it the agent must warn the person, say how many pairs and why, and ask. Only after a yes may it repeat the call with `confirmed_large_read=true`. *Reason:* the user's words: "Let there be no hard limits and let there be a threshold at 250."
- **Priority: the K-series of kerning live tests comes before the T-series.**

## 2026-10-24: v10 session

- The user may restart FontLab without saving at any moment, so live tests must be re-runnable and must state their stage.
- **File > Save tests (T9 and similar) are deferred** until the user says otherwise.

## October 2026: v8 session (exact day not recorded)

- **Tests with glyphs above about 150 nodes go to the very end** (the LAST block). *Reason:* they are costly in tokens and time.
- **The approval phrase for builds is "Yes. Build vX as described."** Nothing is built before it.

## October 2026: server v0.18 (exact day not recorded)

- **Save policy.** No Glyphbridge tool ever saves the font, and none may be built that does; saving is the person's duty. After a package of changes the agent shows **one** bold reminder in chat, through `finish_changes`: never one per step, and never as a FontLab dialog. *Reason:* the user wants full control over what is kept.

## Standing design choices (from the start; exact dates not recorded)

- **The project builds its own bridge** instead of a third-party FontLab MCP server. *Reason:* that server reported false successes. This leads to the design rule in [PROJECT.md](PROJECT.md).
- **TypeRig is not adopted.** The project uses FontLab's own API, learned through staged probes.
- **Width and Unicode writes are not confirmation-gated; delete is** (a Yes/No dialog in FontLab). *Reason:* the first two are reversible.
- **The config entry name `glyphbridge-fontlab` and the server name "Glyphbridge FontLab" were kept** when the scripts were renamed (listener v0.47, server v0.11).
