# Changelog

One entry per release of the two scripts, newest first. The listener's `VERSION` and the server's `SERVER_VERSION` are bumped together with the header line of each file.

Earlier history, in full: [archive/listener-history-to-v0.95.md](archive/listener-history-to-v0.95.md) and [archive/server-history-to-v0.31.md](archive/server-history-to-v0.31.md). What was proven live, and when, is recorded in the topic files and [CHECKLIST.md](CHECKLIST.md).

## Listener v0.110 / server v0.36 (2026-11-03)

**One launcher, shown briefly and alike on Windows and macOS.**
- **Server:** reads one level only (`LAUNCHER_LEVELS = 1`): the second name only said how the app itself was opened (Explorer, launchd, a terminal), and Explorer's own names follow the system language. The file name is sent unchanged.
- **Listener:** shows the launcher without one final `.exe` (any case) and in capitals (`claude.exe` -> `CLAUDE`; a macOS name has no extension), at most 40 characters; from an older server's `a < b` only the first name. Lines: `Connected at … - first request (GET /health) from "local-agent-mode" | CLAUDE.` and, for a later new pair, `[glyphbridge] local-agent-mode | CLAUDE` (without a name: `[glyphbridge] CLAUDE`). The Connected line no longer says "(the name the client gave, shortened as in the log)", "started by" or "to this FontLab session".
- Tests: cases 1490 (display rule: `.exe` case, `x.exe.exe`, `é`, `ß`, an older two-name value) and 1491–1497 updated; server part 21 walks give one name. Existing output changed otherwise only in the Connected lines and the version lines. Mutation run: 41 of 42 killed (26 listener, 16 server); the first run's survivor S3 (an unreadable start time on the first launcher accepted) led to the walk case "level 1 start unreadable"; S5 (the venv skip after a name) is equivalent with one level.
- Live 2026-11-03 (tests 240–242, Arial), every line as predicted: the Code tab's `fontlab_status` gave `Connected at 03:16:41 - first request (GET /health) from "local-agent-mode" | CLAUDE.`; `curl` gave `[Glyphbridge] 03:16:55 reads: font info 1`; the Desktop chat (241) gave only `[local-agent-mode > Glyphbridge] 03:17:33 reads: font info 1` (same pair, no second line). Not live: macOS, a second pair in one listener run.

## Listener v0.109 / server v0.35 (2026-11-03)

**Facts only about who sent a request:** no guessed client name, and the programs that started the server.
- **Listener, no guesses:** a line without a client name starts with `[Glyphbridge]` (was `[unknown agent > Glyphbridge]`; test 236 showed the sender was `curl`). The `.notdef` dialog no longer ends with "(Shown once per font per session by Glyphbridge, because an AI agent read this font.)"; it still appears at most once per font and listener run.
- **Listener, launcher:** reads the `X-Glyphbridge-Launcher` header (percent-decoded, control characters removed, at most 90 characters). The first time a client name comes with a new launcher value in a listener run, it prints `[glyphbridge] New client: <name>, started by <launcher>` (without a name: `New client, started by …`), after the pending summaries and in every log mode. The first pair is named in the "Connected" line instead. No header, no line. Summaries still split by client name only.
- **Server:** reads once at startup (never on import) the file names of the two programs above its process, and sends them as `X-Glyphbridge-Launcher: claude.exe < claude.exe`. File names only: no path, argument, environment variable or user name. Windows: one Toolhelp process snapshot plus each process's start time; in a venv, one parent with the server's own file name (the venv launcher) is skipped. A parent that started after its child (a reused process id), or whose start time is unreadable, ends the walk. macOS: libproc `proc_pidinfo`, written and stub-tested, never run on a Mac. Other systems, or any failure: no header. Tool schemas unchanged.
- Tests: listener cases 1490–1499, server part 21 (21a–21f, with a privacy scan of the launcher code). Existing output changed only in the version lines, the 86 `unknown agent` prefixes and the two `.notdef` texts. Mutation run: 33 of 33 killed (17 listener, 16 server; two first survivors led to cases 1491b and the walk "a python further up"). The real Windows calls (`_windows_process_info`) and the macOS calls are not reachable by stubs.
- Before the build, outside FontLab: a research script read `claude.exe < explorer.exe` above the Desktop chat's servers and `claude.exe < claude.exe` above the Code sessions' servers; the built reader gave `powershell.exe < cmd.exe` and `bash.exe < bash.exe` from two shells.
- Live 2026-11-03 (tests 237–239, Arial): the Code tab's `fontlab_status` gave the Connected line with `started by claude.exe < explorer.exe`. The prediction `claude.exe < claude.exe` was **wrong**: the call came through a server the Desktop app started, not the one the Code session started from `.mcp.json` (process list). The Desktop chat (238) gave no new line, as revised: same launcher. `curl` (239) gave `[Glyphbridge] 02:13:19 reads: font info 1`.

## Listener v0.108 / server v0.34 (2026-11-03)

**Two more stages for `/debug/features` (K11)**; the server is unchanged.
- `stage=shape&tag=T&go=yes`: the size, the number of lines that start with `pos`, `enum pos`, a `pos` with a class on the left, `lookup`, `lookupflag`, `script`, `language`, `subtable`, a class definition (`@name =`) or `#`, and the first 300 characters.
- `stage=lines&tag=T&contains=a,b,c&go=yes`: the size, and only the lines that name 1–3 glyph or class names (`A-Z a-z 0-9 . _ - @`, 1–63 characters) as whole words: at most 20 per name, each cut at 200 characters. Only `stage=lines` takes `contains`.
- The same calls, gate, one-font rule and cap (10 requests per listener run, all stages together) as v0.107.
- Tests: cases 1470–1485; existing output changed in the version lines, the reworded go and stage messages (1440–1443) and the scan of 1466 (the helper's local names). Mutation run: 25 of 25 killed (13 of v0.107, 12 new), each by a case, not only by a scan.
- Live 2026-11-03 on Arial: tests 233 (`shape`) and 234 (`lines`), [topics/kerning.md](topics/kerning.md) §11.

## Listener v0.107 / server v0.34 (2026-11-03)

**A gated research probe of the font's OpenType feature code (K11)**; the server is unchanged.
- New route `/debug/features`, from the names-only tests 158 and 230 on Arial (`font.features` is an `fgOTLayout`, `len` 29). `stage=tags&go=yes` calls `keys()` once and returns the tags and their count. `stage=size&tag=T&go=yes` calls `keys()`, then `has_key(T)` only when T is one of the tags, then `get_feature(T)` only when that answers `True`, and returns the size of that feature's code only (characters, lines, lines with the word `pos`), never the text. Tag: 1–4 characters from `A-Z a-z 0-9`. Exactly one font must be open; 10 requests per listener run, counted before the first call; `len(features)` before and after (`side_effect_detected`). Never called: `clear`, `remove`, `set_feature`, `set_prefix`, `get_prefix`.
- Tests: cases 1440–1468; existing output changed only in the version lines. The scan slice of case 1409 now ends before the new probe. Mutation run: 13 of 13 killed.
- Live 2026-11-03 on Arial (FontLab 8.9.5): test 231 gave 29 tags, `kern` among them; test 232 gave `kern` 52,450 characters, 1,558 lines, 1,417 with `pos`; `side_effect_detected` false both times.

## Listener v0.106 / server v0.34 (2026-11-02)

The shown client name leaves out the config entry name; the server is unchanged.
- Claude Code and the Claude Desktop chat both send `local-agent-mode-glyphbridge-fontlab` (tests 225–226), so lines read `[local-agent-mode-glyphbridge-fontlab > Glyphbridge]`. `_act_client` now leaves out `glyphbridge-fontlab` (`ENTRY_NAME`, any capitalization, whole word only, with the separators next to it); a name that is only that is kept. The "Connected" line uses the same short name and says so.
- The startup "Try:" line names the file: "All routes are listed at the top of glyphbridge_fontlab_mcp_listener.py."
- Tests: cases 1434–1436; existing output changed in the version, startup and "Connected" lines. Mutation run: 5 of 5 killed.
- Live check 2026-11-02 (test 229): both lines read `local-agent-mode`, as predicted.

## Listener v0.105 / server v0.34 (2026-11-02)

**"No font open" on every product route (P0.2), and the client's name in the activity log.**
- **Listener, P0.2:** `_open_font()` answers "no font" when `CountFonts()` is the int 0; otherwise `CurrentFont()` decides, as before. The 13 product code paths that called `CurrentFont()` use it, so every product route answers `{"open": false}` without touching FontLab's placeholder font. The kerning route keeps its own check; the debug probes are unchanged.
- **Listener, activity log:** every line starts with `[<client> > Glyphbridge]`, the name from the `X-Glyphbridge-Client` header (percent-decoded, control characters removed, at most 40 characters; `unknown agent` without one). The summaries are printed when the client changes. A read answered `open: false` (replies up to 4096 bytes are checked) is listed under "no font open", not as a read, and adds no kerning pairs. The "Connected" line names the client.
- **Server:** every tool takes the MCP context (`ctx: Context | None = None`, filled in by the SDK; the tool schemas and descriptions are byte-identical to 0.33) and records the app's `title`, else its `name`; every listener request sends it, percent-encoded. `--check` sends `glyphbridge --check`. The name is the app's claim, not checked, and names the app, not the model.
- Tests: listener cases 1420–1433, server part 20 (20a–20f), and an in-memory run with the real MCP SDK. Existing output changed in version lines, printed signatures, the activity prefix and case 761 (now refused as "no font open"). Mutation run: 10 of 10 killed.
- Live checks 2026-11-02 (tests 225–228, FontLab 8.9.5): both Claude apps send `local-agent-mode-glyphbridge-fontlab`; with the only font closed, `fontlab_status` gave `font_open: false`, a width read and a create were refused, and the log read `reads: no font open: font info 1, width 1` and `REFUSED create kn6A: no font is open`; Arial reopened gave the K2 values unchanged.

## Listener v0.104 / server v0.33 (2026-11-01)

**The fix of kerning defects A and B** ([ROADMAP.md](ROADMAP.md) P0.8; the facts it rests on: [topics/kerning.md](topics/kerning.md) §9.7–§9.9).
- **Listener `/kerning/pairs`** reads `flPackage.kerning(current master)` and never the legacy `font.kerning` (defect A). A glyph's classes come from its `kerningLeft` / `kerningRight` group ids, named by ONE `getAllGroups()` per request, only when an id is not 0. Each pair is asked with explicit keys in FontLab's order, glyph : glyph, glyph : class, class : glyph, class : class; the first entry that exists answers (defect B: a plain name tuple is never sent). New fields: `master`, `master_count`, and per result `source` plus `left_class` / `right_class` when a class answered. No entry: value 0, `source` "none"; an entry that holds 0 keeps its source. An unreadable, unlisted or twice-listed class id is an error for that pair. **Exactly one font must be open** (stricter than before, until T5).
- **Server `get_kerning`** needs listener 0.104 (older ones are refused: they can give false zeros and class values). It checks `source` and the class names (anything else is an error entry), passes `master` / `master_count`, says "this master has no kerning at all" only for an empty master's table, and notes when a font has several masters. Timeout `5 + pairs/50` s (was `/100`). The tool docstring and agent instruction tell the agent to report the source and never guess.
- Tests: the `/kerning/pairs` section was rewritten around the master's table (same cases 1140–1225, values unchanged, new fields), plus cases 1430–1459 (order of entries, defect B, explicit 0, Both class, bad ids, class list failures, one font, masters); server part 19 gained 19x01–19x29. Spies abort on the legacy table, a plain key, or any package member outside the allow-list. Mutation run: 39 of 39 killed (29 listener, 10 server).
- Live checks 2026-11-01 (tests 219–223, FontLab 8.9.5): the GUI-kerned test font read every source kind as predicted, a class edit showed at once, two open fonts were refused, Arial's 13 K2 pairs kept their values, and the Desktop agent reported sources without guessing ([topics/kerning.md](topics/kerning.md) §10).

## Listener v0.103 / server v0.32 (2026-11-01)

Research probes for P0.8 step (d) ([ROADMAP.md](ROADMAP.md)); no product route changed; the server is unchanged.
- **New gated probe `/debug/trykerngroups`** (R1): where FontLab keeps a kerning group's members and side. `stage=all&contains=…`: one `flPackage.getAllGroups()`, only the entries whose group or member names equal a token (at most 20; members cut at 50). `stage=modes&contains=…`: the master's `kerning.groups`, one `values()`, and the seven `fgGroup` members of the first and the matching entries, read as attributes; a callable is reported, never called. `stage=glyph&name=N`: the legacy glyph's `kerningLeft` / `kerningRight` (are they group ids?). Only a real Python list or tuple is ever looked into. One-font gate, 10 requests per listener run counted before the first native call, `len` of the master's table and of its groups before and after. Never called: `keys`, `items`, `asDict`, `has_key`, `clear`, `remove`, `rename`, `findGroup`, `deleteGroups`, `autoKern`, any subscript of a native object.
- **`/debug/trypkgkern`** (R2): in `mode=flags`, a side flagged T may name a class. Only the name rule is checked for it, and the reply lists it under `class_names_not_checked`. Tuple mode and F sides still require glyph names.
- Tests: cases 1370–1410 with allow-list spies (any other member, a subscript or an iteration of a fake native object aborts the run) and a static scan, plus R2 cases 1411–1419 (81 lines in all). Existing output changed only in version lines. Mutation run: 40 of 40 killed (the first run left the 20-entry cut of `stage=modes` alive; case 1380b now covers it).
- Live check 2026-11-01 (tests 198–204, FontLab 8.9.5, the step (c) test font): all three stages and the class-name keys answered without a side effect; `getAllGroups()` and `values()` returned real lists, the latter of tuples, not `fgGroup` objects ([topics/kerning.md](topics/kerning.md) §9.9).

## Listener v0.102 / server v0.32 (2026-11-01)

The **activity log** in FontLab's OUTPUT panel ([ROADMAP.md](ROADMAP.md) P6.1). No route and no reply changed; the server is unchanged.
- `_handle` passes every served request and its reply to `_activity_note` before sending. One timestamped line per change: create, delete, Unicode, width, sidebearings, polygon and path drawing, a shown `.notdef` dialog, and every `/debug/...` request with `go=yes`. Lines say "verified" only where the reply's own re-read says so; refusals (400), failures (500), "no font is open", NOT DONE results, declined deletes, unsynced or warned results and probes are always printed.
- Against flooding: a run of verified changes of one kind shows 3 lines, then one "N more like this, all verified" line. Deletes never collapse. Reads (`/health`, `/version` and `/shutdown` excepted) are counted by kind and printed as one "reads:" line, kerning with its pair count. Both summaries are printed before a different change, after 10 s without a request (checked by the poll timer), and at `/shutdown`. *10 s, not the proposed 2 s:* an agent's tool calls arrive seconds apart, so 2 s would break most runs.
- Built only from the request and the reply, never a `fontlab` call; both entry points swallow their own errors. ASCII only. Switch `_ACTIVITY_LOG = "normal" | "writes" | "off"`.
- Tests: cases 1336–1360 (126 lines) with a fixed clock: every route's reply shapes, runs, idle flushes, modes, broken input, a raising print (the reply is still sent), the end-to-end path through `_handle` and `_poll`, a check that every reply field the log reads exists in the listener, and a static scan (no `fontlab` call in the log block). Existing output changed only in version lines. Mutation run: 31 of 32 killed; the survivor (the tick ignoring `pending`) is equivalent.
- Live check 2026-11-01 (test 190, FontLab 8.9.5, a new font): 5 creates, a drawing, 5 widths, an outline read, a declined delete and a refused width gave 14 OUTPUT lines exactly as predicted; the width summary came 10 s after the last request.

## Listener v0.101 / server v0.32 (2026-11-01)

No route changed; the server is unchanged.
- `_poll` stops as soon as `_sock` is `None`. Before, a `GET /shutdown` handled inside the poll loop was followed by `_sock.accept()` on `None`, and FontLab's OUTPUT panel showed an `AttributeError` traceback after "Listener stopped." (seen live). It was harmless: the timer was already stopped and the reply sent.
- The first-request line no longer says "an AI agent (Claude)": any local client can send the first `GET /health`. It now reads "Connected at HH:MM:SS - first request (GET /health) from a local client to this FontLab session."
- The startup "Try:" line listed 7 old routes, the delete route among them. It now names `GET /health` and `GET /version` and points to the route list at the top of the file.
- Tests: cases 1328–1335 (16 lines) drive `_poll` with fake sockets (a `/shutdown` among later requests, a `/shutdown` as the 8th request, a call after `stop()`) and check `start()` and the first-request line. The old code fails case 1328 with the live traceback. Mutation run: 5 of 5 killed.
- Live check 2026-11-01 (test 189, FontLab 8.9.5, after a full FontLab restart): the three OUTPUT lines as predicted, `fontlab_status` read 0.101, and no traceback after `/shutdown`.

## Listener v0.100 / server v0.32 (2026-11-01)

Versions are compared part by part: **0.100 follows 0.99** (the server reads `(0, 100)`).
- The gated `/debug/trypkgkern` replaces `mode=glyph` with `&mode=flags&flags=FF|FT|TF|TT`. It asks `get(((a, flag), (b, flag)))` with F = False and T = True. That's the form `fgKerning.get` named when it refused the `fgKerningObjectPair` of v0.99 (test 183). No `fontgate` object is built any more.
- Tests: the v0.99 section (cases 1311–1329, 24 lines) is replaced by the flags cases 1311–1327 (28 lines); the static scan of case 1273 accepts the probe's own flag table. Mutation run: 9 of 9 killed.

## Listener v0.99 / server v0.32 (2026-11-01)

The gated `/debug/trypkgkern` gets `&mode=glyph` (default `tuple`, unchanged); no product route and no server change.
- `mode=glyph` asks both tables with ONE `fontgate.fgKerningObjectPair(a, b, 'glyphMode', 'glyphMode')`, the documented way to say that a name is a glyph (test 181; defect B, [topics/kerning.md](topics/kerning.md) §9). The constructor comes from the already loaded `fontgate` module (never imported) and is called once, after the request counter; a constructor error or a `None` result means no `get` is called.
- Every reply now carries `mode`. Tests: 25 new lines (cases 1311–1329) and one changed line (case 1232 shows `mode`). Mutation run: 13 of 13 killed.

## Listener v0.98 / server v0.32 (2026-11-01)

One new **names-only probe**; no product route and no server change.
- `GET /debug/moddir` lists names in modules FontLab has **already** loaded: matching module names, matching names inside one module, or the docstrings of one entry (as `/debug/classdir`). `?stage=kerntype` gives the type and module of `font.kerning`. *Why:* test 177 found that `fgKerningObjectPair` is not a name of the `fontlab` module (defect B, [topics/kerning.md](topics/kerning.md) §9).
- It never imports, constructs or calls anything; it needs 1 to 3 filter tokens and never returns a whole module or the whole module list (at most 100 modules, 200 names).
- `debug_class_probe` takes an optional module; `/debug/classdir` is unchanged.
- Tests: 42 new lines (cases 1280–1310). Mutation run: 21 of 21 killed.

## Listener v0.97 / server v0.32 (2026-11-01)

One new **gated research probe**; no product route and no server change.
- `GET /debug/trypkgkern?a=NAME&b=NAME[&master=NAME]&go=yes` reads one pair from `flPackage.kerning(master)` next to the legacy `font.kerning`. *Why:* in live tests 169 and 170, a class pair made in FontLab's GUI was invisible to `font.kerning`.
- Same one-font gate as `/debug/trysync`. At most 20 requests per listener run, counted before the call. The only calls are `pkg.masters`, `pkg.master`, `pkg.kerning(master)`, `len()` and `get((a, b))`.
- Tests: 56 new lines in the listener harness (cases 1230–1274). Mutation run: 31 of 32 killed; the survivor (`len()` returning a bool) is equivalent.

## Listener v0.96 / server v0.32 (2026-11-01)

Housekeeping. **No behaviour change**: a comparison of the parsed code with v0.95 / v0.31 shows it identical apart from the version constants.
- The version history moved out of both module docstrings and into the archive (about 11,000 words).
- The listener's route list is now complete and correct. It covers all 51 registered routes and adds the kerning routes and the `/debug/fontdir`, `/debug/trykern` and `/debug/trygroups` probes. It also fixes a `/version` example that said 0.67.
- One listener comment that pointed at the old history now points at [topics/reading.md](topics/reading.md) §6.
- The test expectations changed in version lines only (30 lines).

## Listener v0.95 / server v0.31 (2026-10-27)

`get_kerning`: no pair cap, an approval threshold at 250 pairs (`confirmed_large_read`), and `POST /kerning/pairs` for large reads. Details: [topics/kerning.md](topics/kerning.md).
