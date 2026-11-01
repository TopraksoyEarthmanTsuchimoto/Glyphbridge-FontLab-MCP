# Changelog

One entry per release of the two scripts, newest first. The listener's `VERSION` and the server's `SERVER_VERSION` are bumped together with the header line of each file.

Earlier history, in full: [archive/listener-history-to-v0.95.md](archive/listener-history-to-v0.95.md) and [archive/server-history-to-v0.31.md](archive/server-history-to-v0.31.md). What was proven live, and when, is recorded in the topic files and [CHECKLIST.md](CHECKLIST.md).

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
