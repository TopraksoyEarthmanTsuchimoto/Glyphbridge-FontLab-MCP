# Decisions

Active decisions only, newest first. Each entry gives the date, the decision and the reason. Superseded or no longer relevant entries move to [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). Where the chat-era record gives no exact day, the entry says so.

## 2026-11-04: the F1 fix (listener 0.120 / server 0.42)

- **A glyph with modern nodes is read from the modern layer only**; when that read fails the reply is an error, never a legacy fallback. *Reason:* touching `glyph.layer` or reading `glyph.layers` of a Power Brush glyph lets the next `font.update()` flatten it (332–496).
- **After a width or sidebearing write the sync check compares only the legacy width**; drawings and new layers keep the full check. *Reason:* the same facts; `glyph.width` is safe (486–488).
- **`verified` on the modern route checks the horizontal extent only**, and the reply says `y_extent_checked: false`, until a vertical check is built. *Reason:* approved with the build, when no FontLab box was proven; 519 later found `inkBox()`.

## 2026-11-03: names read at the moment, not fixed strings

- **Text shown to the person or the agent names things from facts read at that moment** (the client's own name, the font's name and file, the system's save shortcut), never from fixed strings. A name the sender gives is shown as given, ambiguous ones such as `local-agent-mode` included; a missing one stays missing. *Reason:* the user's rule after test 290, where the delete dialog said "Claude" whoever sent the request. Built in listener 0.114 / server 0.40.
- **Not pursued** (the user's choice): the fixed "all 132 groups of Arial" in a debug note, and "FontLab 8" in tool descriptions and the unreachable message (the project's scope; no fact can be read there).
- **PostScript names come from the font package** (design C, listener 0.118 / server 0.41): the values FontLab's Font Info shows; no name is reported as "not set", since whether FontLab derived it or a person typed it cannot be read. *Reason:* tests 291–300 found no such marker, and showed the legacy `font.info` disagreeing with Font Info (298).

## 2026-11-03: several open fonts

- **`get_kerning` with several fonts open** (listener 0.112 / server 0.37, tests 265–268): it uses the current package only when its `path` is not empty and equals the current font's path, and otherwise refuses with the reason. *Supersedes* "kerning reads need exactly one open font" (2026-11-01, archived). *Reason:* the user approved it after T5 (262–264) showed that both views follow the font window in front and that `path` tells the fonts apart.
- **Goal: every operation works with 2, 3 or more fonts open, without confusion.** Closing the other fonts is the last resort, only where it is the only way to a goal. Then the tool tells the person to close them, and why: a limitation of how FontLab is built, shown by research, which Glyphbridge cannot work around. Until research has shown that, the message says the case is not supported yet. *Reason:* the user's choice, within the design rule of honest messages ([PROJECT.md](PROJECT.md)).

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

## 2026-10-27: kerning (v11 session)

- **Read only the pairs a task needs, never the whole kerning table or font.** *Reason:* token cost.
- **There are no hard limits, but there is a threshold at 250 pairs.** Above it the agent must warn the person, say how many pairs and why, and ask. Only after a yes may it repeat the call with `confirmed_large_read=true`. *Reason:* the user's words: "Let there be no hard limits and let there be a threshold at 250."

## 2026-10-24: v10 session

- **File > Save tests (T9 and similar) are deferred** until the user says otherwise.

## October 2026: v8 session (exact day not recorded)

- **Tests with glyphs above about 150 nodes go to the very end** (the LAST block). *Reason:* they are costly in tokens and time.

## October 2026: server v0.18 (exact day not recorded)

- **Save policy.** No Glyphbridge tool ever saves the font, and none may be built that does; saving is the person's duty. After a package of changes the agent shows **one** bold reminder in chat, through `finish_changes`: never one per step, and never as a FontLab dialog. *Reason:* the user wants full control over what is kept.

## Standing design choices (from the start; exact dates not recorded)

- **The project builds its own bridge** instead of a third-party FontLab MCP server. *Reason:* that server reported false successes. This leads to the design rule in [PROJECT.md](PROJECT.md).
- **TypeRig is not adopted.** The project uses FontLab's own API, learned through staged probes.
- **Width and Unicode writes are not confirmation-gated; delete is** (a Yes/No dialog in FontLab). *Reason:* the first two are reversible.
- **The config entry name `glyphbridge-fontlab` and the server name "Glyphbridge FontLab" were kept** when the scripts were renamed (listener v0.47, server v0.11).
