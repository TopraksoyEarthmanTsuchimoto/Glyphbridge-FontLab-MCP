# Changelog

One entry per release of the two scripts, newest first. The listener's `VERSION` and the server's `SERVER_VERSION` are bumped together with the header line of each file.

Earlier history, in full: [archive/listener-history-to-v0.95.md](archive/listener-history-to-v0.95.md) and [archive/server-history-to-v0.31.md](archive/server-history-to-v0.31.md). What was proven live, and when, is recorded in the topic files and [CHECKLIST.md](CHECKLIST.md).

## Server v0.45 (2026-11-04; listener unchanged at 0.124)

**`set_kerning` polished from the live checks 565–574** ([topics/kerning.md](topics/kerning.md) §14).
- **Whole units:** a value that is not a whole number is refused before anything is sent (FontLab stores kerning in whole units, 567–569); `-12.0` counts as whole.
- **Panel wording** (reply and tool description): FontLab applies the value at once, but the KERNING panel misses a new pair and keeps a listed pair's old value until the person switches to another open font and back (with one font open: File > New Font, then back) or saves and reopens the font (566, 573, 574).
- **A failed pair that changed** names what its entry holds now ("the entry now holds -13").
- **`matched_by`** in the reply, as in `get_kerning`.
- **Messages:** a listener refusal that already says "nothing was set" no longer gets "Nothing was changed." added; `get_kerning`'s refusal ends with a full stop before the font note.
- Tests: server 27za–27zs; 27f and 27p use whole numbers now (2636 + 58 + 90 + 973 lines). Other output changed only in the version lines, 19an / 19ao / 19x28 (the full stop) and `matched_by` in the 27 replies. Mutation run: 9 of 9 killed.
- Live-checked 2026-11-04 (575, 576).

## Listener v0.124 / server v0.44 (2026-11-04)

**`set_kerning`: the first kerning write tool** (glyph : glyph pairs, current master; research KW 542–564, [topics/kerning.md](topics/kerning.md) §13, §14).
- **Listener `POST /kerning/set`** `{"pairs": [[left, right, value], ...]}`: the font and table are matched as `/kerning/pairs` matches them (shared helper `_kern_table_target`; the read itself is unchanged). Refused with nothing set: bad input (HTTP 400; a pair twice, a value that is not a finite number), no font, an unmatched font, a name that is not a glyph, |value| > the package's `upm`, an unreachable `set`. Per pair: the effective value before (shared `_kern_effective`, as the read gives it) and the exact entry, ONE `set(((left, False), (right, False)), float(value))`, then the exact entry and the effective value again. `set` only when the exact entry equals the value and FontLab applies it from the glyph : glyph entry; the first pair that is not stops the request, the rest are `not attempted`. Reply: `before`, `after`, `changed`, `exception_over_class` per pair, `table_size_before` / `_after` / `_as_expected`. Activity log: `kerning A:V: 0 -> -50 (verified)`. No `Update()`, `font.update()` or save.
- **Server tool `set_kerning(pairs, confirmed_large_write)`**: checks names and values before sending; more than 250 pairs need the person's approval; needs listener 0.124. A failed pair raises an error that says which pairs were set and counts the change (or an uncertain one). The `agent_instruction` and the tool description tell the agent to say that the KERNING panel lists such pairs only after save and reopen, that closing asks no save question and loses them, and that Undo cannot take them back.
- Tests: listener 2000–2047 (2018b/c, 2025b/c, 2013b–o); server 27a–27zz (2636 + 58 + 90 + 953 lines). Existing output changed only in the version lines, the read scan 1180 (`target`, a dict) and the tool counts (17 → 18). Mutation run: 28 of 28 killed (a first run left three survivors; cases 2018c, 2025b and 2025c were added).
- Live-checked 2026-11-04 (565–573, [topics/kerning.md](topics/kerning.md) §14).

## Listener v0.123 (2026-11-04; server unchanged)

**`/debug/trykernrefresh`, a gated probe: can the KERNING panel be made to list a pair written through the API?** ([topics/kerning.md](topics/kerning.md) §13).
- `stage=container|update|changed&go=yes`: ONE `flPackage.kerningContainer()`; `update` then calls `fontlab.Update(container)` once, `changed` calls `container.changed()` once. A container that is `None`, null or of unknown null state gets no call. Before and after: the `isChanged` / `hasChanges` flags of the package and the container, and `len()` of the current master's table. The one-font gate of `/debug/trysync`; 6 requests per listener run, counted before the first call. Never `Update()` without an argument, `UpdateAll`, `Update` with the font or package, `container.update`, `remove`, `release`, `setFlag`, the history calls, a kerning setter or `font.update()` (spies and a static scan). No product route changed.
- Tests: listener 1712–1736 and 1718b (2526 + 58 + 90 + 888 lines). Existing output changed only in the version lines. Mutation run: 15 of 15 killed (a first run left one survivor, the uncallable `changed`; case 1718b was added).
- Live 2026-11-04 (553–556): every call harmless; no call made the panel list the pair.

## Listener v0.122 (2026-11-04; server unchanged)

**`/debug/trysetkern`, a gated probe that writes one kerning pair** ([topics/kerning.md](topics/kerning.md) §13).
- `a=A&b=B&value=N&form=tuple|flags&go=yes`: ONE `flPackage.kerning(current master).set(key, value)`, with `form=tuple` the key `(a, b)` and with `form=flags` the key `((a, False), (b, False))`. Before and after: `get(((a, False), (b, False)))` and `len()` of the table; the reply carries `set_returned`, `read_back_matches` and `table_size_changed`. Refused: without `go=yes`; other than exactly one font open; a name that is not a glyph of the font; a name that any group of ONE `getAllGroups()` also carries, or a group list of unknown shape (defect B); a value that is not a finite decimal number or exceeds the package's `upm` either way. When the read before fails, `set` is not called. 10 requests per listener run, counted before the first kerning call. Never `remove`, `clear`, `setPlainPairs` or another setter, `font.update()`, `Update()`.
- Tests: listener 1677–1711 (2496 + 58 + 90 + 888 lines). Existing output changed only in the version lines; the trypkgkern scans 1273 and 1327 now end where the new section starts. Mutation run: 20 of 21 killed; the survivor (`isfinite` removed) is equivalent, since the character rule already refuses `nan` and `inf`.
- Live 2026-11-04 (544–551, 557–560): the `tuple` form works; `set` returns `None`; the pair is saved, and the KERNING panel lists it after save and reopen.

## Listener v0.121 / server v0.43 (2026-11-04)

**The vertical extent checked against FontLab's own ink box; exact quadratic extents** (facts 519–533, [topics/reading.md](topics/reading.md) §8p).
- **Listener `/glyph/outline`** (the modern-only route): `fontlab_ink_box`, from `layer.inkBox()` called once with no argument on the same modern layer, as raw rectangle getters (`left`, `right`, `top`, `bottom`, `width`, `height`), or `{error}`. The outline is answered all the same when the call fails. No legacy member is touched.
- **Server, quadratic extents:** `_cubic_contour_pieces` became `_contour_pieces`, which also parses quadratic contours (implied on-curve points halfway between two off-curve points), and `_quad_extremes` adds each segment's extreme. Quadratic contours get `ink_bbox_exact: true`, an `svg_path` with `Q` pieces, and the horizontal check; contours that mix cubic and quadratic points stay `unverified`. This applies to every modern-layer answer, the stale-view fallback included.
- **Server, vertical check** (`source: "modern"`): the computed box is compared with FontLab's ink box at 0.05, its lower and upper y taken by `min` / `max` (Qt names the sides y-down). `verified` needs both checks (`y_extent_checked: true`, `ink_box_vs_fontlab`); a vertical mismatch is `unverified` with both numbers. The vertical check also decides between the raw and the transformed reading. Without a usable box (an older listener, a failed call, a box that is not the exact extents) the check stays horizontal and `y_extent_note` says why. The `get_glyph_outline` description says so.
- Tests: listener 1668–1676; server 26a–26zz (2443 + 58 + 90 + 888 lines). Existing output changed only in the version lines and 14j (a quadratic contour is now parsed: its true extent no longer matches the fake's margins). Mutation run: 11 of 11 killed.
- Live-checked 2026-11-04 (V121, 534–541): all five test glyphs `verified` with the vertical extent checked, `A` intact after a create.

## Listener v0.120 / server v0.42 (2026-11-04)

**F1: a glyph with modern nodes is read and sync-checked without the legacy layer** (facts 332–496, [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l: touching `glyph.layer` or reading `glyph.layers` of a Power Brush glyph, then any `font.update()`, flattens it; `glyph.width`, `glyph.components` and the name are safe).
- **Listener `/glyph/outline`** (`layer=body|active`): when the glyph's modern active layer holds nodes, the reply comes from the modern layer only: `source: "modern"`, `modern_outline`, `elements` (from `_describe_modern_glyph`, without the legacy comparison), `component_count` and `shape_count` from the modern counts. No `glyph.layer`, `glyph.layers`, `bodyLayer`, `findNode` or legacy margins. An unreadable modern node count or outline gives an error, never a legacy fallback. The legacy reader runs only when the modern side cannot be reached, when the modern layer is missing or empty, for `layer=strict|glayer`, and for `modern=no`. Module switch `_MODERN_FIRST` (shipped `True`; the stub tests turn it off for the older legacy-reader cases).
- **Listener `/font/notdef`:** a `.notdef` whose modern layer holds nodes or components is judged from the modern counts (`source: "modern"`); otherwise the legacy check runs as before.
- **Listener sync check** (`_guard_classify`, used by the auto sync after every modern write and by the guard before `font.update()`): after a width or sidebearing write only the legacy `glyph.width` is compared with the modern advance width. Drawings and new layers keep the full check; a glyph registered by one stays "full" while it is remembered (`_guard_register`).
- **Listener `/debug/readmodern?stage=box&go=yes`** (gated): `layer.boundingBox()` and `layer.inkBox()` on the modern layer, as plain rectangles.
- **Server `get_glyph_outline`:** a `source: "modern"` reply gets the element transforms applied by contour counts and is checked against the modern left sidebearing and ink width. Raw and transformed coordinates are both checked; only an unambiguous match is `verified`. `verification.y_extent_checked` is `false` on this route. With `GLYPHBRIDGE_MODERN=0` the legacy reply carries a note that a Power Brush glyph may now be flattened. Older listeners are answered as before.
- Tests: listener 1630–1667; server 25a–25w (2432 + 58 + 90 + 850 lines). Existing output changed only in the version lines and the `/debug/readmodern` stage message. Mutation run: 20 of 20 killed.
- Not yet live-tested.

## Listener v0.119 (2026-11-03; server unchanged)

**`/debug/tryrefresh`, a gated experiment for F1** ([topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l): can a refresh of only the changed glyph replace the whole-font `font.update()` of the legacy writes?
- `stage=create&name=N&how=Update_flGlyph|none&go=yes`: `font.createGlyph(N)`, then with `Update_flGlyph` one `fontlab.Update` on the new glyph's modern object. `stage=unicode&name=N&value=V&go=yes`: `glyph.unicode = V` (1 to 1114111), then one `fontlab.Update` on that glyph's modern object; nothing is set when the modern object cannot be reached, and no `Update` follows a failed set. The one-font gate of `/debug/trysync`; each mode once per listener run, counted before the first change. Never `font.update()`, `glyph.update()`, `UpdateAll()`, the assign family, delete, save or export (spies and a static scan). No product route changed.
- Tests: listener 1590–1624 (2386 + 58 + 90 + 825 lines). Existing output changed only in the version lines. Mutation run: 13 of 13 killed.
- Live 2026-11-03 (FontLab 8.9.5, 436–453): the probe worked as specified; what it showed is in [LIVE-TESTS.md](LIVE-TESTS.md), F1.

## Listener v0.118 / server v0.41 (2026-11-03)

**PostScript names as FontLab's Font Info shows them (design C, research 291–300).** Test 298 set the PostScript field to `W6aTest-Regular` in Font Info; the legacy `font.info.postscriptFontName` still read `Unnamed1-Regular`, while the font package's `psn` read `W6aTest-Regular` (300).
- **Listener `/font/current`:** adds `package_names` (`psn`, `ffn`, `tfn`, `tsn`, `sgn`) and `package_matched_by`, read from the workspace's current package only when it is proven to be this font: the only font open (`_trysync_target`), or with several fonts the same non-empty path (`_kern_package_by_path`). Otherwise `package_names_unavailable` with the reason (two unsaved fonts, a count that is not a positive number, a null package). Each name is read once; a callable is never called; a value that is not text becomes null and is listed in `package_name_errors`.
- **Server `_clean_font`:** the fixed check that turned any PostScript name starting with "Unnamed" into null is removed. `postscript_font_name` and `postscript_full_name` come from `psn` / `ffn` when available; `postscript_names_source` names the view; `legacy_postscript_*` and a note appear when the legacy view differs. Without the package the legacy values are kept, with a note that this view can lag behind Font Info and why. The `get_current_font` description tells the agent not to call a name "unset" or "a placeholder".
- Tests: listener 1579–1589 and 1585b; server 24a–24h and 24b2 (2328 + 58 + 90 + 825 lines). Existing output changed otherwise only in the version lines and the first `/font/current` line (the old stub has no `CountFonts`). Mutation run: 16 of 16 killed; the first run's two survivors (a count of −1; a differing full name) led to 1585b and 24b2.
- Live 2026-11-03, listener only (FontLab 8.9.5): 301 two unsaved fonts gave `package_names_unavailable` with the path reason; 302 with one font left, `psn` `W6aTest-Regular`, matched as the only font. Server v0.41, live 2026-11-03 (303, through Claude Code, a new unsaved font alone): `get_current_font` gave `Unnamed-Regular` / `Unnamed Regular` with `postscript_names_source` "font package (as FontLab's Font Info shows them)" and no `legacy_*` fields, as predicted.

## Listener v0.117 (2026-11-03)

**One gated `keys()` call for the font-info research.** `/debug/fontdir?stage=keys&attr=NAME&members=PATH&go=yes`: the `memberdir` path rules; the object at the end must have a public, callable `keys`, called once without arguments and only with exactly `go=yes` (otherwise the reply says what it would call). A plain list or tuple of text is returned (at most 200 entries, with the count); anything else by its type only, never iterated. `has_key`, `value`, `asDict` and `del` are never called. Tests 1563–1578; guard check 1033 now reads "read-only but for the gated keys stage". Mutation run: 15 of 15 killed. Live: 297, 298 (`fgStringDict.keys()`, [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10).

## Listener v0.116 (2026-11-03)

**`stage=memberdir` takes a dotted path of up to 3 steps** (`members=dict.flags`). Each step is a public plain identifier in `dir()` of the step before, read once; a plain value or a callable (never called) ends the walk; `path_types` lists the earlier steps' types. Written with tuples so the older guard scans (1032, 1053) still flag nothing. Tests 1547–1562. Mutation run: 12 of 12 killed. Live: 295, 296.

## Listener v0.115 (2026-11-03)

**`/debug/fontdir?stage=memberdir`:** one member of an attribute's sub-object, names only (type, docstring, public names; no value, no call, no `len`, no container access). Tests 1534–1546. Mutation run: 10 of 10 killed. Live: 294 (`font.info.dict`).

## Listener v0.114 / server v0.40 (2026-11-03)

**No fixed names (decision of 2026-11-03).**
- **Listener:** the delete dialog no longer says "Claude (via Glyphbridge)" and "the current font". `_deletion_text` names the client the request named (the activity log's cleaned `X-Glyphbridge-Client`), or says "A request through Glyphbridge asks …"; the font as family and style (or "a font without a name"), its file name, "not saved to a file yet", or "its file could not be read"; and "1 of N open fonts, the one whose window is in front" when several are open. `_REQUEST_FONT` keeps `saved` and `file` for this; the headers never carry the file name.
- **Server:** `SAVE_SHORTCUT` is read from the operating system at startup (Cmd+S on macOS, Ctrl+S otherwise) and used in `SAVE_REMINDER`, the `save_note` and the 8 tool descriptions that name it; all 17 tools register through `_tool()`, which fills the placeholder.
- Tests: listener 1520–1533 (with 1526b, 1528b); server part 23. Mutation run: 13 of 13 killed. Real MCP SDK: 17 tools, 8 naming Ctrl+S, no placeholder left.
- Live 2026-11-03 (listener 0.118 / server 0.41, FontLab 8.9.5, through Claude Code, a new unsaved font alone, prefixes `w7a_`, `w7b_`): 304 / 307 `create_glyph`, 305 / 308 `delete_glyph` with Yes (2 → 1 glyphs each). The 308 dialog, from the user's screenshot, title "Glyphbridge: Confirm Deletion", default No: "local-agent-mode (via Glyphbridge) is requesting to delete the glyph 'w7b_one' from the font "Unnamed Regular" (not saved to a file yet).", as predicted. 306: `finish_changes` counted 2 changes, reminder with Ctrl+S; the loaded tool descriptions named Ctrl+S. 331 (three fonts, testfont in front): the dialog ended "(file savedtestfont.vfc; 1 of 3 open fonts, the one whose window is in front)", the file name without its path, as predicted ([LIVE-TESTS.md](LIVE-TESTS.md), T5). Not seen live: Cmd+S, a missing client name.

## Server v0.39 (2026-11-03)

**An error reply names its font too (test 277).** The first call after a font window switch failed ("No glyph named …") and carried no font fields, while the server had already recorded the new font, so the switch was reported nowhere.
- **Server:** `_with_font` appends the `font_note` to the message of a `ToolError` raised by the tool, by changing the same exception object (an `OutcomeUnknown` keeps its class and still counts as an uncertain change). Unchanged: errors raised before any listener call, errors without a note (one font, no switch), errors with no font open or from an older listener, and all successful replies. The listener stays at 0.113.
- Tests: server part 22: 22o now prints the message; new 22w–22z, 22w2, 22w3, 22x2 (805 lines). Existing output changed otherwise only in the version lines. Mutation run: 4 of 4 killed (no note appended; a new exception losing the class; the note appended without a `font_note`, killed only by a crash; only `OutcomeUnknown` caught).
- Live 2026-11-03 (tests 282–284, FontLab 8.9.5, two copies of the test font): after one click on the other tab, a read of a missing glyph ended with the switch note ("another font with the same name … from a different file"); the next read showed no `font_changed`.
- Correction to v0.38 below: the font headers never carry the path, but `fontlab_status` and `get_current_font` do report it (test 273).

## Listener v0.113 / server v0.38 (2026-11-03)

**Every reply names its font (goal 5, ROADMAP P0.5 (a)).**
- **Listener:** `_open_font()` and the kerning route remember the font a request used (`_note_request_font`: `font.info.familyName` / `styleName` without control characters, at most 100 characters each; the first 12 hex digits of the SHA-1 of `font.path`, or `none` for an empty or unreadable path; `CountFonts()`). `_build_response()` sends them as `X-Glyphbridge-Font` (family and style, percent-encoded, joined by `/`), `X-Glyphbridge-Font-Key` and `X-Glyphbridge-Fonts-Open` (only when the count is a plain number). `_route()` and `_handle()` forget the font at each request, so `/health`, `/version`, the probes and a request that used no font get no headers. JSON replies are unchanged; the path never leaves the listener.
- **Server:** `_do_request` records the headers of each listener reply; every tool returns through `_with_font`, which adds `font` and `fonts_open`, and `font_note` when several fonts are open, the font has no path, or the font changed. `font_changed` (from / to) compares with the previous tool call in this server process: the path hashes decide when both exist, otherwise the names (two unsaved fonts of the same name cannot be told apart, and the note says so; the same name from another file is named as such). A change inside one call adds `font_changed_during_call`, and on a write `change_target_uncertain`. A refusal still updates the remembered font; an older listener adds nothing.
- Tests: listener cases 1510–1519c, and 1424 now shows `font.info` read with one font open. Server part 22 (22a–22v). Existing output changed otherwise only in the version lines. Mutation run: 23 of 23 killed (10 listener, 13 server); the first run's two survivors (no reset per tool call; names deciding over path hashes) led to cases 22t–22v.
- Live 2026-11-03 (tests 269–272, FontLab 8.9.5): no font open gave no font fields; one font was named without a note; a switch between Arial and the test font was reported in both directions with the note.

## Listener v0.112 / server v0.37 (2026-11-03)

**`get_kerning` with several fonts open (T5).**
- **Listener `/kerning/pairs`:** with one font open nothing changes (`_trysync_target`, the package path is not read). With two or more, the new `_kern_package_by_path` takes the workspace's current package only when the current font's `path` is a non-empty string, the package is not null, and its `path` is the same non-empty string; otherwise it refuses, naming the check that failed, and suggests bringing a saved font to the front or closing the other fonts. `CountFonts()` below 1 is refused. `packages()` is not used on this route. The reply adds `fonts_open`, `matched_by` (`"only font"` or `"path"`) and `family_name` (`font.info.familyName`, or null).
- **Server:** passes `fonts_open`, `matched_by` and `family_name` on (odd values become null). With more than one font open, the instruction says which font was read (the one whose window is in front, matched by its file path) and asks the agent to name it. The tool description no longer says "Exactly one font must be open"; it says the tool reads the font in front and may refuse with several fonts open.
- Tests: listener cases 1447 and 1447b now read (matching paths), new 1447c–1447p (one font never reads the package path; two fonts read it once; differing, empty, `None`, unreadable or non-text paths; a null or unknown package; `CountFonts()` −1; `packages()` unused); every kerning reply line gained the three fields; the static scan lists `path` among the font members read. Server cases 19dn–19ds, and 19x29 checks the new sentence. Existing output changed otherwise only in the version lines. Mutation run: 12 of 12 killed (8 listener, 4 server).
- Live 2026-11-03 (tests 265–268, FontLab 8.9.5): Arial in front read with `matched_by` `path` and its known values; the test font in front read after one click; a new unsaved font in front (3 fonts) refused with the path reason.

## Listener v0.111 / server v0.36 (2026-11-03)

**`/debug/tryfont?stage=state` tells packages apart (T5)**; the server is unchanged.
- The current package is also reported with its `path` and `fileName` (the same `_tryfont_read` as the `construct` stage), because its `name` is empty even for a saved font (test 261). The type name of what `flWorkspace.packages()` returns is reported as `packages_type`; it is never iterated or indexed (an unproven container call, [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10). The `construct` and `attach` stages show the same fields in their workspace snapshots.
- Tests: cases 732b (a new package: empty path, a failing `fileName` reported as text) and 732c (a saved package: its path and file name, no forbidden call). Existing output changed only in the version lines. Mutation run: 3 of 3 killed (no `path` read, no `packages_type`, `fileName` read from `name`).
- Live 2026-11-03 (T5, tests 262–264, Arial and `savedtestfont.vfc` open): `path` matched `CurrentFont()`'s path in each state, `fileName` ends in `.xfo`, `packages_type` is `list`.

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
