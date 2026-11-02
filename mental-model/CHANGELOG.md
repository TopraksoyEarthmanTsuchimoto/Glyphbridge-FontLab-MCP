# Changelog

One entry per release of the two scripts, newest first. The listener's `VERSION` and the server's `SERVER_VERSION` are bumped together with the header line of each file.

Earlier history, in full: [archive/listener-history-to-v0.95.md](archive/listener-history-to-v0.95.md) and [archive/server-history-to-v0.31.md](archive/server-history-to-v0.31.md). What was proven live, and when, is recorded in the topic files and [CHECKLIST.md](CHECKLIST.md).

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
