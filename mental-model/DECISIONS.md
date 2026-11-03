# Decisions

Active decisions only, newest first. Each entry gives the date, the decision and the reason. Superseded or no longer relevant entries move to [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). Where the chat-era record gives no exact day, the entry says so.

## 2026-11-03: WATCH-POINTS.md budget 950

- **The WATCH-POINTS.md budget goes from 750 to 950 words.** *Supersedes* the 750 of the watch-points entry below. *Reason:* the user's choice, after tests 273–281 brought the file to 656 words with 10 open entries.

## 2026-11-03: several open fonts

- **`get_kerning` with several fonts open** (listener 0.112 / server 0.37, tests 265–268): it uses the current package only when its `path` is not empty and equals the current font's path, and otherwise refuses with the reason. *Supersedes* "kerning reads need exactly one open font" (2026-11-01, archived). *Reason:* the user approved it after T5 (262–264) showed that both views follow the font window in front and that `path` tells the fonts apart.
- **Goal: every operation works with 2, 3 or more fonts open, without confusion.** Closing the other fonts is the last resort, only where it is the only way to a goal. Then the tool tells the person to close them, and why: a limitation of how FontLab is built, shown by research, which Glyphbridge cannot work around. Until research has shown that, the message says the case is not supported yet. *Reason:* the user's choice, within the design rule of honest messages ([PROJECT.md](PROJECT.md)).

## 2026-11-03: DECISIONS.md budget 1,700

- **The DECISIONS.md budget (active part) goes from 1,350 to 1,450 words, then on the same day to 1,700**; the reference totals become 10,050 including the root README, and 9,550 for the startup core files. Three entries move to [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md): the CLAUDE.md and CHECKLIST.md budgets of 2026-11-01 (the budgets are in [MARKDOWN-MAP.md](MARKDOWN-MAP.md), their totals were out of date) and the K-series priority of 2026-10-27 (the K-series is done). *Reason:* the user's choice; after the watch-points decision the file used 1,313 of 1,350 words, with the decision on `get_kerning` and several fonts still to come; that decision left 36 words, hence 1,700.

## 2026-11-03: watch points get their own file

- **The watch points move from CURRENT-STATUS.md to a new [WATCH-POINTS.md](WATCH-POINTS.md)**, with a budget of 750 words; it is not a startup core file. CURRENT-STATUS keeps the number of open entries and a link; the list of test numbers in use moves to [LIVE-TESTS.md](LIVE-TESTS.md). The CURRENT-STATUS budget stays at 1,350. *Reason:* the user's idea: CURRENT-STATUS had reached 1,338 of 1,350 words, a third of it watch points, and observations that are not yet explained are one kind of fact with their own life: recorded, then settled into a topic file or dropped.

## 2026-11-03: K15 dropped

- **K15 (a kerning POST body near and above the 1,000,000-byte limit, about 30,000 pairs) will not be run.** The limit stays stub-tested only. *Reason:* the user's choice: it adds no significant value, since agents read only the pairs a task needs and more than 250 needs the person's approval (K8), and 2,000 pairs already read in under 0.1 s (K14).

## 2026-11-03: who sent a request, facts only

- **A missing client name stays missing:** the log line starts with `[Glyphbridge]`; the `.notdef` dialog drops its closing line about "an AI agent". *Reason:* the user's choice; the listener cannot know an agent sent a request (test 236: `curl`).
- **The server sends the file name of the program that started it (option C)**, read once at startup with the standard library on Windows and macOS; the listener shows it without `.exe`, in capitals, once per new pair. Only file names: no path, argument, environment variable, user name or other app's file; a failure shows nothing. *Reason:* the user's choice: a system fact, no new dependency. Rejected: command lines, app configs, self-naming, `psutil`.
- **`local-agent-mode` stays as sent** for now.

## 2026-11-03: proven container calls on native objects

- **Container access (`[]`, `get`, `keys`, `values`, `items`, `has_key`, iteration) on a native FontLab object is forbidden until proven, per object and call form.** The proven calls form one table in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10, with their test numbers. This replaces the blanket ban and its two one-off exceptions (the kerning `get`, the K11 `keys()`). *Reason:* the user's choice, the tidiest option. The ban rests on one crash (`font.shapes`), the `keys()` exception was noticed only after the live runs, and one proof path keeps the rules and the reports consistent.

## 2026-11-02: the client's name in the activity log

- **The log shows the name the app sends by itself** (MCP `clientInfo`), without the config entry name `glyphbridge-fontlab`. No label is set in the MCP configs. *Reason:* the user's choice: an ambiguous automatic name such as `local-agent-mode` is enough, and the configs stay untouched.

## 2026-11-01: kerning groups

- **AI agents must be able to see which groups have which members** ([ROADMAP.md](ROADMAP.md) P1.6; proposed first and built only after approval). *Supersedes* "group membership is deliberately not read". *Reason:* K9 and the KERNING panel method depended on membership, which only FontLab's Classes panel could show; the members of one group are a small read.

## 2026-11-01: repository workflow (migration day)

- **No test may depend on the local file `savedtestfont.vfc` in the end.** Live tests build their reference glyphs in a fresh disposable font. `savedtestfont.vfc` may be used until it is no longer useful. Font files (`*.vfc`, `*.vfj`) are ignored by git. *Reason:* people who fork the repository must find everything they need in it ([ROADMAP.md](ROADMAP.md) §11).
- **`.gitignore` lists only what this project produces.** *Reason:* the generic Python template made the repository look less maintained.

- **The repository is the source of truth.** The project follows [HOW-TO-GET-ORGANIZED.md](HOW-TO-GET-ORGANIZED.md), with all documentation in `mental-model/`. *Reason:* milestone summaries had grown to about 28,000 words, and every new chat had to rebuild the context. *Supersedes* "the milestone summary is the single source of truth".
- **`tests/README.md` stays in `tests/`**, an exception to the "all Markdown in `mental-model/`" rule. *Reason:* the user's choice, so it stays next to the harnesses it describes.
- **The repository is public.** Live files contain no personal paths, names, time zones or locales. *Reason:* the user's choice. The v11 summary snapshot was trimmed of those details before the first push.
- **The project folder is the cloned repository.** The scripts stay at the root, and the server uses its own `venv` there (Python 3.15.2, `mcp==2.2.0`, ignored by git). *Reason:* `run_all.py` reads the scripts from the parent of `tests/`, and the MCP configs point at the root.
- **Claude Code uses a committed `.mcp.json` with relative paths.** *Reason:* it works without user-specific paths in a public repository (verified).
- **The old `Notes\` folder stays out of the repository.** *Reason:* the user's choice.
- **The user commits and pushes with GitHub Desktop.** Agents do not commit unless asked.

## 2026-10-27: kerning (v11 session)

- **Read only the pairs a task needs, never the whole kerning table or font.** *Reason:* token cost.
- **There are no hard limits, but there is a threshold at 250 pairs.** Above it the agent must warn the person, say how many pairs and why, and ask. Only after a yes may it repeat the call with `confirmed_large_read=true`. *Reason:* the user's words: "Let there be no hard limits and let there be a threshold at 250."

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
