# Changelog

One entry per release of the two scripts, newest first. The listener's `VERSION` and the server's `SERVER_VERSION` are bumped together with the header line of each file.

Earlier history, in full: [archive/listener-history-to-v0.95.md](archive/listener-history-to-v0.95.md) and [archive/server-history-to-v0.31.md](archive/server-history-to-v0.31.md). What was proven live, and when, is recorded in the topic files and [CHECKLIST.md](CHECKLIST.md).

## Server v0.84 (2026-11-24, listener unchanged at v0.203): an empty `.notdef` in a font in progress is left alone

**Built as proposed and approved** ([DECISIONS.md](DECISIONS.md), 2026-11-24: speak only about real issues, when they matter).

- Server: `check_notdef_glyph` asks the listener to note `.notdef` (`POST /font/notdef/warn`) only for an issue: missing, or empty with the first read's `maturity.mature` true. An empty `.notdef` in a font still in progress (not mature, or unknown) gets `noted_in_output_panel: false`, no request, no version check, and the instruction "Say nothing about .notdef" from the automatic checks, or "If the person asked about .notdef, …" from `check_notdef` and `--check --notdef-warn` (`asked=True`). `create_font` no longer returns `notdef_note` or asks the agent to mention it. `get_glyph_outline(".notdef")`'s note now says an empty `.notdef` is normal while a font is in progress; `check_notdef`'s description says what is noted and when the agent speaks.
- Tests: four stub harnesses PASS at 5536 + 58 + 121 + 1756 lines. `notdef_tests.py` parts 4 and 5 revised (4b2, 4d3, 4w, 5e2 new: an early font left alone is raised once it becomes mature); section 36 of `create_unicode_tests.py` loses `notdef_note`. Mutation run: 15 of 15 caught, the no-change control not. **Not yet run in FontLab.**

## Listener v0.203 / server v0.83 (2026-11-24): self-closing dialogs, and the `.notdef` notice without a dialog

**Built as proposed and approved** (the two designs of 2026-11-21, [DECISIONS.md](DECISIONS.md)); research SC 1588–1593, CD 1594–1598. Started 2026-11-21, finished 2026-11-24 in a new session.

- Listener: the Yes/No dialogs of `/glyph/delete` and `/kerning/group/remove` close by themselves after `dialog_seconds` (10–50, default 45), counted as no answer (`not_answered`), through a single-shot `QTimer` owned by the dialog and connected to its `reject()` slot; the No button counts down ("No (44)"); the text says what happens without an answer. If the closing timer cannot be set up, no dialog is shown (`dialog_error`). An unreadable click counts as declined. Deleting `.notdef` gets its own warning text. `POST /font/notdef/warn` shows no dialog: it notes a missing or empty `.notdef` once per font as one OUTPUT line, remembered by the package `fgId`; for an empty `.notdef` the reply adds the font's maturity (all 52 letters A–Z a–z by Unicode, one of them drawn). The OUTPUT panel also logs a dialog that was not answered or not shown.
- Server: sends `dialog_seconds` 45 and waits 55 s (was 120 s); `delete_glyph` and `remove_kerning_group` need listener 0.203 (the general `MIN_LISTENER_VERSION` stays 0.82); a dialog that closed unanswered gives `not_answered_in_time`, nothing changed, and the agent asks the person before trying again. The `.notdef` instruction depends on the font's state: missing, clearly; empty in a mature font, a likely oversight; otherwise one light sentence. Nothing is noted through a listener older than 0.203. `create_font` mentions the new font's empty `.notdef` once (`notdef_note`). Every tool description and the timeout message were corrected, including `remove_kerning_group`'s "Needs listener v0.200" (now v0.203).
- Tests: four stub harnesses PASS at 5536 + 58 + 113 + 1756 lines; the deployed listener copy is identical. New cases 2882–2907 (with 2884b, 2884c, 2898b), `notdef_tests.py` rewritten (4d2 added), `create_unicode_tests.py` 50o–50zg. Mutation run: 41 of 42 caught, the no-change control not; the one left (the maturity read for a missing `.notdef`) is equivalent, since a missing `.notdef` returns before that line. **Not yet run in FontLab.**

## Listener v0.202 (2026-11-21, server unchanged at v0.82): a countdown in the self-closing test dialog

**Built as proposed and approved.** Research for the countdown of the self-closing dialog design ([DECISIONS.md](DECISIONS.md), 2026-11-21); names only 1594, 1595.

- Listener: `GET /debug/trydialogtimeout` takes `countdown=yes`: a second `QTimer` owned by the dialog, repeating each second, calls a Python function that relabels the No button "No (N)" through `button(QMessageBox.No).setText`. The first label is set only once that timer is connected; no "No (0)" is shown; the closing is unchanged. A countdown that fails is reported (`countdown_error`, the first error) and the dialog still closes on time. The reply adds `countdown_ticks`, `countdown_last_label`, `countdown_label_after`. The clicked button's label is now read as the property `text` (SC 1591, 1592).
- Tests: four stub harnesses PASS at 5498 + 58 + 90 + 1740 lines; the deployed listener copy is identical. New cases 2865–2881; the fake button now has `text` as a property, as PythonQt does. Mutation run: 36 of 36 caught (two needed the new cases 2880 and 2881), the no-change control not. Run live CD 1596–1598 ([LIVE-TESTS.md](LIVE-TESTS.md)): the No button counted down visibly once a second, the dialog closed on time, and Yes and No in time counted as usual; the clicked button's label reads correctly.

## Listener v0.201 (2026-11-21, server unchanged at v0.82): gated probe for a dialog that closes itself

**Built as proposed and approved.** Research for the user's choice of 2026-11-21 (option C): a dialog that closes itself before an AI app's time limit ends the call (TO, TO2, [LIVE-TESTS.md](LIVE-TESTS.md)); names only 1588, 1589.

- Listener: `GET /debug/trydialogtimeout?how=slot|python&seconds=3..50&go=yes` ([topics/server-and-endpoints.md](topics/server-and-endpoints.md) §3): UI only, no font call. ONE test Yes/No dialog (default No) with a single-shot `QTimer` owned by the dialog; `slot` connects its `timeout()` to the dialog's `reject()`, `python` to a Python function that calls it. The reply gives the elapsed time, the dialog's result, the clicked button (or none) and, for `python`, whether the timer fired. 10 requests per listener run, counted before the dialog; a failed `connect` shows no dialog.
- Tests: four stub harnesses PASS at 5479 + 58 + 90 + 1740 lines; the deployed listener copy is identical. New cases 2853–2864 (a recording dialog and timer; a spy and a static scan for any font call). Mutation run: 20 of 20 caught, the no-change control not. Run live SC 1590–1593 ([LIVE-TESTS.md](LIVE-TESTS.md)): both forms close a waiting dialog on time; reading the clicked button's label fails (`text` is a property in PythonQt), which the product does not need.

## Listener v0.200 / server v0.82 (2026-11-20): `rename_kerning_group` and `remove_kerning_group`

**Built as proposed and approved** (the design of 2026-11-20, [DECISIONS.md](DECISIONS.md)). Research: GE0–GK 1499–1545 ([topics/kerning.md](topics/kerning.md) §18).

- Listener: `POST /kerning/group/rename` `{"group", "new_name"}` and `POST /kerning/group/remove` `{"group", "pairs"}` ([topics/server-and-endpoints.md](topics/server-and-endpoints.md)). Both match the font and master as `/kerning/pairs` and need a kerning group confirmed by `items()` and `getAllGroups()`. Rename: a new name of any group or class refused, a glyph's name allowed (`same_name_glyph`); ONE `groups.rename`; `renamed` only when the re-read shows the old name gone and the same members and side under the new name, both sizes unchanged; `id_before` / `id_after`. Remove: a Yes/No dialog in FontLab (default No) naming the group, its side, members (8 shown) and what happens to its kerning; ONE `groups.remove(group)` or `remove(group, True)`; `removed` when the group left both sources and the container shrank by one; the table's size before and after. After a change: the mark through a member glyph (`Glyphbridge kerning group`), ONE `notifyPackageContentUpdated(<package fgId>)`, and `fontlab_caught_up` (one member's `kerningLeft` / `kerningRight` against the new id or 0). `getAllGroups()` returning None counts as no group. One OUTPUT line per request.
- Server: tools `rename_kerning_group(group, new_name)` and `remove_kerning_group(group, pairs)` (26 tools); a leading `@` is stripped; `pairs` required (`keep` or `delete`); both need listener 0.200; the removal waits up to 120 s for the dialog; a No is reported as expected behaviour; replies forward the mark, the refresh and `fontlab_caught_up`, and the instructions say what `keep` makes of each kind of entry (GK), that a rename gives a new id, and that FontLab may lag until a font switch when `caught_up` is not true. `MIN_LISTENER_VERSION` unchanged.
- Tests: four stub harnesses PASS at 5465 + 58 + 90 + 1740 lines; the deployed listener copy is identical. New cases: listener 2831–2852 (a spy on the container, the table and the package; a static scan), server section 50. Mutation run: 34 of 34 caught, the two no-change controls not. Not yet run live.

## Listener v0.199 (2026-11-20, server unchanged at v0.81): gated probe that renames or removes one kerning group

**Built as proposed and approved.** Research for editing kerning groups; names only GE0 1499–1504 ([LIVE-TESTS.md](LIVE-TESTS.md)).

- Listener: `GET /debug/trykerngroupedit` ([topics/server-and-endpoints.md](topics/server-and-endpoints.md) §3): `op=rename&name=OLD&new=NEW` makes ONE `rename(OLD, NEW)`, `op=remove&name=N&pairs=keep|delete` ONE `remove(N)` or `remove(N, True)`, on the current master's kerning groups. Gated (`go=yes`), exactly one font open, 10 requests per listener run counted before the first kerning call. Refused before any kerning call: bad names, NEW equal to OLD, to a glyph name or to any group's name, an unknown `glyph`; refused before the edit: a group not confirmed by `items()` and `getAllGroups()`. Read before and after: both group sources, `len()` of the table and of the groups, and with `&glyph=G` the group's own class entry (under both names after a rename). `renamed`, `removed`, `entry_followed` and `entry_gone` come from the re-read only. No subscript, no `del`, no legacy group call, no `deleteGroups`, no mark, no panel refresh, no save.
- Tests: four stub harnesses PASS at 5389 + 58 + 90 + 1691 lines; the deployed listener copy is identical. New cases 2807–2830 (a spy that aborts on any other member, subscript or iteration of the group container; a static scan); the KERNING-panel probe's scan now ends at the new section. Mutation run: 25 of 25 caught, the no-change control not. Not yet run live.

## Listener v0.198 / server v0.81 (2026-11-20): `get_glyph_width` reads the modern advance width, cross-checked with the legacy width

**Built as proposed and approved** (design B, [DECISIONS.md](DECISIONS.md)). Research: AW–AW4 ([LIVE-TESTS.md](LIVE-TESTS.md)).

- Listener: GET `/glyph/width` reads the modern wrapper's `activeLayer` and then `advanceWidth` once (`source: "modern"`, `advance_width`), and the legacy `glyph.width` as `legacy_width`. With no wrapper, no active modern layer, or an `advanceWidth` that raises or is not a number, the answer is the legacy width (`source: "legacy"`, `modern_reason`). A failed legacy read gives `legacy_error`; when both fail, `width` and `source` are null, `readable: false` and `reason` names both causes. The legacy layer is never touched (F1). `width` stays the chosen value, so an older server keeps working.
- Server: `get_glyph_width` adds `width_source`. When both widths are numbers 0.01 or more apart: `legacy_width`, `widths_disagree: true`, `width_note` and an `agent_instruction` to tell the person both values and not choose one. A legacy answer, a failed cross-check, and a listener older than 0.198 each get a `width_note`. An unreadable width is an error that says it is not a width of 0. The tool description says all this. `MIN_LISTENER_VERSION` unchanged.
- Tests: four stub harnesses PASS at 5322 + 58 + 90 + 1691 lines; the deployed listener copy is identical. New cases: 2600–2609 (listener; a spy confirms no legacy layer read), 49a–49m (server). Mutation tests, one at a time on a throwaway copy, all killed: the 0.01 threshold, the old-listener branch, the legacy note, the modern-first choice, a legacy layer read, an `advanceWidth` read without a layer. Not yet run live.

## Listener v0.197 / server v0.80 (2026-11-20): whole-unit widths, and a changed width is never reported as unchanged

**Built as proposed and approved.** Cause: AW 1449 ([LIVE-TESTS.md](LIVE-TESTS.md)): `set_glyph_width tri1a 437.5` changed the width (`advanceWidth` 438.0, legacy 437.5) but replied "NOT changed", and the change was not counted; FontLab's width field rounds a typed 437.5 to 438 (AW2 1456).

- Listener: `set_glyph_width` rounds the requested width to a whole unit before any write (rule B, a half rounds up), on the modern and the legacy route; the re-read is checked against the rounded value; `width_rounded {requested, written}` when the number changed. A width that moved, but not to the request, gives `changed: true` and the reason "the width changed to X, not to the requested Y"; on the modern route the glyph is synced and the font marked. OUTPUT: "(rounded from 437.5, verified)" when the listener itself receives a fraction (a direct POST; through server 0.80 the server rounds first, so the line shows only the whole width, AW3 1462), and "CHANGED, NOT AS ASKED" in place of "NOT DONE" for such a write.
- Server: rounds before sending (so an older listener is covered too); a successful reply carries `width_rounded` and `rounding_note`; a width that moved but not to the request raises "Width of glyph 'X' was changed to A (was B), but not to the requested C: …", counted as a change, also from a listener that sends no `changed`; "NOT changed" only when the re-read equals the old width. The `set_glyph_width` description says the width is rounded.
- Tests: four stub harnesses PASS at 5310 + 58 + 90 + 1676 lines; the deployed listener copy is identical. New cases: 341a–341i (listener), 9zg–9zn (server). Not stub-tested: the legacy route's `changed` case (the fake legacy glyph keeps any width). No mutation run. Not yet run live.

## Listener v0.196 (2026-11-20, server unchanged at v0.79): gated `flGlyph.advanceWidth` read

**Built as proposed and approved (in a Codex session).**

- Listener: `/debug/tryadvancewidth` lists member names at `stage=names`; `stage=read&go=yes` reads `flGlyph.advanceWidth` once, with one-font and `tri`-name gates and a 10-call listener-run cap.
- Tests: four stub harnesses PASS at 5301 + 58 + 90 + 1668 lines; the deployed listener copy is identical. The stub tests cover the names stage, a read without `go=yes` and one gated read; the refusals (a second font, another name, the cap reached) are not stub-tested. Live FontLab status: [LIVE-TESTS.md](LIVE-TESTS.md).

## Listener v0.195 / server v0.79 (2026-11-20): the general kerning instructions and the OUTPUT line name a class pair's own rules

**Built as proposed and approved, after CK 1421, 1429 and 1430 ([LIVE-TESTS.md](LIVE-TESTS.md)).** Run live CK2 1433–1436a, every prediction held.
- Server: in a reply with a class side (the variant already chosen when a pair has 'kind'), `remove_kerning`'s instruction says a `no entry` pair "had no entry of its kind" (it said "no glyph : glyph entry", 1430) and "to restore a glyph pair, call set_kerning with its 'before' value; a class pair: see below"; `set_kerning`'s point (3) reads "to revert a glyph pair, if 'before' was …; a class pair: see below". For a class pair 'before' is the sample's, so the glyph-pair rule gave a wrong revert (1421, 1429). Glyph-only replies are unchanged, word for word.
- Listener: the OUTPUT line of a single pair with no entry names its kind ("no class : class entry, nothing removed"); a glyph pair, or an unknown kind, keeps "no glyph : glyph entry".
- Tests: `stub_listener_tests.py` 5290 → 5296 lines (2747b–2747d); `create_unicode_tests.py` 1661 → 1668 (48z1–48z6, two of them glyph-only controls; 48c and 48s2 follow the new wording). Mutation run: 7 of 7 caught (5 server, 2 listener).

## Listener v0.194 / server v0.78 (2026-11-20): class kerning in `set_kerning` and `remove_kerning`

**The design of the user's answers of 2026-11-20 ([DECISIONS.md](DECISIONS.md)), built as approved.** Run live CK 1420–1432a, every predicted value held ([topics/kerning.md](topics/kerning.md) §17). Research: CW 1409–1417 ([topics/kerning.md](topics/kerning.md) §17).
- Listener: `/kerning/set` and `/kerning/remove` accept a side `@name`. A request with a class side reads ONE `getAllGroups()` and ONE `items()` before the first write; each class must be confirmed by both and fit its side, else nothing is changed. Key `((name, isClass), (name, isClass))`. Per class pair: `kind`, `classes` (side, member count), `sample` (the first member of each class side that is a glyph of the font) with its effective value before and after, `sample_verdict` (`applied`, `covered`, `no sample`) and `entry_before`; a pair is `set` only when its exact entry reads the value and the verdict holds. The mark goes through the sample glyphs, never a class name. `same_name_group` on a glyph side named like a kerning group, from the class list the request already read (no extra call). Glyph-only requests take the same path, calls and replies, apart from that note.
- Server: both tools accept `@name` sides, check them before sending, need listener 0.194 for a class side (0.124 / 0.192 for glyphs only), check each class pair's fields and verdict against its sample themselves, report a failed class pair through its sample pair, pass the `note` on, and extend the instructions and tool descriptions; "class (group) names cannot be used" is removed from the refusals and descriptions.
- Tests: `stub_listener_tests.py` 5206 → 5290 lines (2780–2806b; 2033 and 2034, 2736 follow the new key and the `groups` read; two glyph-only replies gain `same_name_group`); `create_unicode_tests.py` 1612 → 1661 (section 48; the refusal texts of 27g and 47h and the phrase lists of 27y and 47x follow the corrected wording). Mutation run: 30 of 30 caught (17 listener, 13 server), after two server cases were added for the first run's survivors (48h2, 48j2).

## Listener v0.193 (2026-11-20, server unchanged at v0.77): class sides in the research probes `/debug/trysetkern` and `/debug/trydelkern`

**Research build for class writes (CW 1409–1419), approved as proposed.** Run live CW 1409–1417, every prediction held ([topics/kerning.md](topics/kerning.md) §17); 1418, 1419 not run (Demo mode).
- Listener: both probes take `&left=glyph|class&right=glyph|class` (default `glyph`, so earlier calls are unchanged). A class side needs `form=flags` and is sent as `(name, True)`: ONE `set(((a, isClass), (b, isClass)), value)` or `remove(...)`, with `get()` of that same key before and after. Before the first kerning call a class side must name a kerning group of the ONE `getAllGroups()` (an OpenType class or an unknown name is refused); after it, the master's kerning groups get `len()` and ONE `items()` (the reader of `/kerning/groups`), and the group must be confirmed by both sources and on a side that fits (left or both on the left, right or both on the right). Anything else refuses with nothing set or removed. A class side's reply adds `left`, `right`, `classes` and the groups' `len()` before and after. A glyph side is checked as before. No mark and no panel refresh.
- Tests: `stub_listener_tests.py` 5172 → 5206 lines (2748–2778, 2766b; the stub table now keeps a class entry apart from a glyph entry of the same names; 1692 and 2644 name the new key form; 1710 lists the `groups` read); `create_unicode_tests.py` version lines only. Mutation run: 16 of 16 caught.

## Server v0.77 (2026-11-19): corrected `set_kerning` revert guidance

- Server: the `set_kerning` agent guidance now explains when to use `set_kerning` versus `remove_kerning` to restore the prior glyph : glyph state, including an underlying class value; the `set_kerning` tool description gives the same advice. The server only reports the state the listener confirms.
- No listener or FontLab API behavior changed. This guidance correction was not tested in real FontLab.

## Listener v0.192 / server v0.76 (2026-11-19): `remove_kerning`, removing glyph : glyph kerning pairs

**The design of the user's six answers of 2026-11-19 ([DECISIONS.md](DECISIONS.md)), built as approved.** Not yet run live. Research: KD 1380–1390, KDC 1391–1397 ([topics/kerning.md](topics/kerning.md) §16).
- Listener: POST `/kerning/remove` (`{"pairs": [[left, right], ...]}`): every check before the first removal; per pair the effective value and the exact glyph : glyph entry; a pair with no such entry is `no entry`, nothing called, and the request goes on; otherwise ONE `remove(((left, False), (right, False)))`, its return value ignored; `removed` only when the entry reads `None` and `len()` dropped by exactly one; `class_value_applies`; the first pair not confirmed stops the request (the rest `not attempted`); then the mark and the panel refresh of `/kerning/set`; in the activity log as "kerning remove". The probe `/debug/trydelkern` stays.
- Server: the 24th tool `remove_kerning(pairs, confirmed_large_write)`, needs listener 0.192; pairs checked before sending; more than 250 pairs refused until the person approves; `no entry` becomes a note naming any class that still kerns the pair; a removal is verified only when 'after' no longer comes from a glyph : glyph entry; `agent_instruction` on the class value that applies again (not 0), the panel, the mark, Edit > Undo and how to restore a pair with `set_kerning`.
- Tests: `stub_listener_tests.py` 5077 → 5172 lines (2700–2747, 2723b; 2290 and 2291v now count two kerning routes); `create_unicode_tests.py` 1555 → 1612 (section 47; 27x's scan ends where the new code starts; the tool count 23 → 24). Mutation run: 31 of 31 caught (17 listener, 14 server), after one case was added for the first run's survivor (another entry removed in place of the asked one, 2723b).

## Listener v0.191 (2026-11-19, server unchanged at v0.75): research probe `/debug/trydelkern`, removing one kerning pair

**The research build approved on 2026-11-19, after the names-only test 1380** (`fgKerning.remove` has no docstring). Run live KD 1381–1390 ([LIVE-TESTS.md](LIVE-TESTS.md)). Facts: [topics/kerning.md](topics/kerning.md) §16.
- Listener: `/debug/trydelkern?a=A&b=B&form=tuple|flags&go=yes`: the gates of `/debug/trysetkern` (exactly one font open, glyph names that no group carries, the current master; 10 requests per listener run, counted before the first kerning call); `flPackage.kerning(master)` once; the exact entry and `len()` before; ONE `remove((a, b))` or `remove(((a, False), (b, False)))`, not called when the read before failed; the entry and `len()` after. `removed` is true only when `remove` raised nothing, the entry was a number before, reads `None` after, and `len()` dropped by exactly 1. No mark, no panel refresh, no save.
- Tests: `stub_listener_tests.py` 5039 → 5077 lines (2633–2662, 2638b, 2638c; 1710's scan now ends where the new probe starts); `create_unicode_tests.py` only its version line. Mutation run: 12 of 12 caught, after two cases were added for the first run's survivors (`remove` raising after it removed; the read after it failing).

## Listener v0.190 / server v0.75 (2026-11-19): `get_kerning_groups`, the kerning groups of the current master (P1.6)

**The design of the user's six answers of 2026-11-19 ([DECISIONS.md](DECISIONS.md)), built as approved.** Not yet run live. Facts: [topics/kerning.md](topics/kerning.md) §15; routes and fields: [topics/server-and-endpoints.md](topics/server-and-endpoints.md).
- Listener: GET and POST `/kerning/groups` (`get_kerning_groups`): named groups and / or glyphs, or every group; the font and master as `/kerning/pairs`; ONE `items()` on the master's kerning groups and ONE `getAllGroups()`, cross-checked (`confirmed`, `mismatch`, `class_list_members`); a name listed twice by either source is never confirmed; more than 250 groups in an all-groups read answer only the count without `confirmed`; an unknown name is an error for that name; the sizes before and after; in the activity log as "kerning groups". Found in the build and fixed before any run: a truth test of the `groups` argument would have called `len()` on a native object (2629c).
- Server: the 23rd tool `get_kerning_groups(groups, glyphs, all_groups, confirmed_large_read)`, needs listener 0.190; names checked and folded before sending; more than 250 names refused until approved; the all-groups confirmation turned into the ask-the-person refusal; every entry type-checked (an `unknown` side never confirmed); `agent_instruction` on sides, unconfirmed groups, OpenType classes, other masters. A pure read.
- Tests: `stub_listener_tests.py` 4977 → 5039 lines (2610–2632; 1180's scan now ends where the groups code starts); `create_unicode_tests.py` 1478 → 1555 (section 46; 19ci's scan ends where the groups code starts; the tool count 22 → 23). Mutation run: 54 of 54 caught (38 listener, 16 server), after three boundary cases were added for the first run's survivors (a native or subclassed pair in `items()`, class-list entries of 4 and 6 fields, exactly 250 names).

## Listener v0.189 (2026-11-19, server unchanged at v0.74): research stage `items` for kerning groups (P1.6)

**The research build approved on 2026-11-19, after the names-only test 1373.** Run live KG 1374–1375 (one run, [LIVE-TESTS.md](LIVE-TESTS.md); facts: [topics/kerning.md](topics/kerning.md) §9.10).
- Listener: `/debug/trykerngroups` gets `stage=items&contains=a,b,c&go=yes`: as `stage=tuples`, but ONE `groups.items()` instead of `values()` (reply keys `items_type`, `note_items`); a token also matches one level deeper, a member inside (name, (members, side)); `stage=tuples` keeps its depth. Beyond the proposal, found in the build: a real list or tuple inside a field showed only 10 elements, where the members of a name pair sit, so it now shows up to 50 (`_TRYKERNGROUPS_ITEMS`) with its own `cut`, for both stages. The static scan forbids `items` everywhere but the one read `container.items`.
- Tests: `stub_listener_tests.py` 4955 → 4977 lines (2600–2609b; the nested `cut` in 2585–2592; 1370–1372, 2597c the new texts; 1409's scan); `create_unicode_tests.py` only its version lines. Mutation run: 38 of 38 caught (the guards of 0.188 on the new code, and 14 new ones).

## Listener v0.188 (2026-11-19, server unchanged at v0.74): research stage `tuples` for kerning groups (P1.6)

**The research build approved on 2026-11-19.** Run live KG 1364–1372 (one run, [LIVE-TESTS.md](LIVE-TESTS.md); facts: [topics/kerning.md](topics/kerning.md) §9.10).
- Listener: `/debug/trykerngroups` gets `stage=tuples&contains=a,b,c&go=yes`: the reads of `stage=modes` (`kerning(current master)` once, its `groups`, ONE `values()`, the sizes before and after), but the entries are read as plain data: only a real list or tuple (the exact type) is looked into; the shapes of all entries, the first entry and the entries holding a token as a text field or a text element of a list field (at most 20); each field plain, a real list or tuple by its length and up to 50 elements (`_TRYKERNGROUPS_ITEMS`), at most 8 fields (`_TRYKERNGROUPS_FIELDS`), any other object by its type name only; nothing in an entry is called. Same gate, one-font check and 10 requests per listener run as the other stages.
- Tests: `stub_listener_tests.py` 4926 → 4955 lines (2585–2599b, 2590c, 2591c, 2592b; 1372's stage list; 1409's scan sees the new helpers' own lists); `create_unicode_tests.py` unchanged at 1478 but for its version lines. Mutation run: 24 of 24 caught, after four boundary cases were added for the first run's survivors (exactly 50 elements, 8 fields, 20 matches; a token one level too deep).

## Listener v0.187 / server v0.74 (2026-11-18): one layer, the active one, for every `add_component` target

**The design approved after NB 1353 (rule A, [DECISIONS.md](DECISIONS.md)).** Run live 1354–1363a (one run, [LIVE-TESTS.md](LIVE-TESTS.md)): refused with either layer active; one-layer targets, empty and not, still placed, by both forms.
- Listener: `_comp_one_layer_problem`, asked by both forms before the route is chosen: the glyph must have exactly one layer, its name the active layer's, not `gb_temp_component`; otherwise "add_component needs a glyph with exactly one layer, the active one (it has [...], active '...')", nothing changed. Before, only the non-empty route checked it, so in 1353 an empty active layer beside a full one took the empty route. The single form's `one_component` no longer holds the source-layer test: `source_layer` is its own check.
- Server: `add_component`'s description states the rule for every target, the case seen in 1353, and listener 0.187; `source_layer` is shown and required when the listener sends it (an older listener's `one_component` holds it); `_comp_refusal` says "nothing was changed" once in add_component's three refusals (twice in 1351). `remove_component`'s refusal still says it twice (not in this build).
- Tests: `stub_listener_tests.py` 4906 → 4926 lines (2584a–i; every single-form `checks` gains `source_layer`; 2581a refused before the route; the early fake `P72Mod` gets `layers`, with 2423d/e and 2464 kept on their unreadable-layers case); `create_unicode_tests.py` 1469 → 1478 (section 45; refusals say it once). Mutation run: 12 of 12 caught, after one equivalent condition (`lay[3] != working_name`, the same read as `working_name`) was dropped.

## Listener v0.186 / server v0.73 (2026-11-18): `add_component` for a glyph that is not empty

**The design of 2026-11-18 ([DECISIONS.md](DECISIONS.md)), approved as proposed.** Not yet run live.
- Listener: `POST /glyph/component`, both forms. A target that is not empty (contours, components, Power Brush shapes) goes to `_add_beside`: checks first (one layer, the active one; `autoLayer` off; every element readable as a contour shape, a component or a brush shape, the kinds checked before any `inkBox()`; the sources as in the list form); then, in the one request, `addLayer(flLayer("gb_temp_component"))`, `setActive()` of the working layer if needed, the recipe build on the temporary layer, each offset and `shapeData.componentLayer` (the source's own layer) there, `recipe = ""`, `addShape` of each into the working layer, `removeLayer`, the width written back. `placed` needs the old elements unchanged and first, the new components after them in order (source, source layer, offset, ink box), one layer, active, contours held, `autoLayer` / recipe as before, sources, width and glyph count unchanged; then the full sync check and the mark. A failure partway runs `_beside_restore` (`removeShape` of the added components, `setActive`, `removeLayer`, width) and reports `restore.restored` from a re-read. An empty target keeps its route and now says `placement: "empty layer"`.
- Server: `add_component`'s description covers both routes and the restore; `_comp_beside_reply` gives `placement`, `existing_kept`, `restore`, `layers_after`, `component_states`, `components_after`; a confirmed restore is `font_modified: false` with its own instruction. `remove_component`'s description points to it.
- Tests: `stub_listener_tests.py` 4861 → 4906 lines (2580–2583; 2423d/e and 2464 now reach the new route; 2465's scan ends where the new section begins); `create_unicode_tests.py` 1452 → 1469 (section 44; 38w checks the new description). Mutation run: 23 of 23 caught.

## Listener v0.185 (2026-11-18; server unchanged at v0.72): `templayer` with `brush=yes` and `sync=light|full`

**Research for Power Brush targets before the tool is built** (the user's choice and approval of 2026-11-18). Research only; run live PB 1328–1345 ([LIVE-TESTS.md](LIVE-TESTS.md)).
- Listener: `stage=templayer` takes `brush=yes`: the working layer may also hold shapes reading `isComponent` False and `isComposite` True (a Power Brush or other composite shape). No `inkBox()` is called on such a shape (untested, F1): its row says `not_read`, it is compared by kind and matrix, and the layer's contours in full. `sync=light` registers the glyph as the new light guard kind `trycomponent_light`, so the sync check after a step and the guard before a later `font.update()` read only `glyph.width` and the modern layer, never `glyph.layer` / `glyph.layers`; `sync=full`, the default, keeps the full check. `brush` and `sync` are refused on other stages. The probe's own limit is 20 calls per listener run (10 before).
- Also: a target's kinds are checked before any `inkBox()` call, in every step and in `droptemp`; before, a refused brush target had already had `inkBox()` called on its brush shape (stub-found, 2571a; never run live on a brush target).
- Tests: `stub_listener_tests.py` 4768 → 4861 lines (2570–2578; 2542 now counts to 21; 2530i/j, 2544c, 2560d show the sync mode; 2531b/c and 2564e refuse without an `inkBox()` call). Mutation run: 16 of 16 caught.

## Listener v0.184 (2026-11-18; server unchanged at v0.72): `templayer` steps `setlayer` and `droptemp`

**The source-layer fix of 1285a in the order a tool would use, and a clean-up for a temporary layer left behind** (the user's approval of 2026-11-18). Research only.
- Listener: `step=setlayer`, between `build` and `move`, with a baseline, the working layer as recorded, and the temporary layer holding exactly one component of a `cpp` glyph whose source layer is not the working layer's name: ONE `shapeData.componentLayer = <working layer name>` on that component, after checking it still names the source read before. `temp_layer_set` needs the read-back name, the component's source, matrix and ink box unchanged, the working layer, width, source glyph and glyph count unchanged. Not marked. `step=droptemp` needs no baseline: on a glyph of exactly two layers, `gb_temp_component` known to be empty and one other layer of plain contours and `cpp` components, ONE `working_layer.setActive()` when the temporary layer is active (read back; it stops if the other layer did not become active), then ONE `w.removeLayer(<gb_temp_component>)`. `temp_dropped` needs only the other layer left, active, its elements and outline, the width and glyph count unchanged. Not marked. A temporary layer that is not known to be empty is refused.
- Tests: `stub_listener_tests.py` 4659 → 4768 lines (2560–2565; 2530a and 2530b list the new steps; 2543 and 2549 count the clean-up's `removeLayer` and `setActive`). Mutation run: 15 of 15 caught.

## Listener v0.183 (2026-11-18; server unchanged at v0.72): `stage=fixlayer`; `templayer` checks the source layer

**A component built on the temporary layer names that layer as its source layer** (live 1283a, 1283b: `gb_temp_component`, a layer its source glyph does not have; FontLab draws it all the same, 1284). Research only.
- Listener: `stage=fixlayer&target=cpp…&element=I`, `go=yes`, exactly one font open, one master, its own 6 calls per listener run; other parameters are refused. On a target with exactly one layer (the active one), `autoLayer` off, holding only plain contour shapes and components of `cpp` glyphs, whose element I is a component of a `cpp` glyph naming a source layer other than the target's layer name: ONE `shape.shapeData.componentLayer = <the target's layer name>`, after checking that the shape still names the source read before. `layer_set` needs element I to name the target's layer and nothing else changed (`component_kept`: source, matrix and ink box; `others_kept`; `outline_kept`; width, source glyph, glyph count, `autoLayer` / recipe). Marked only then.
- `stage=templayer`: `move` and `removelayer` report `component_layer_matches` (the new component names the working layer); `placed_beside` needs it, so the route of TL 1272–1283 now reads `placed_beside` false and is not marked.
- Tests: `stub_listener_tests.py` 4609 → 4659 lines (2550–2556; 2340c and 2470n list the new stage). Mutation run: 13 of 13 caught.

## Listener v0.182 (2026-11-18; server unchanged at v0.72): `stage=templayer&step=activate`

**The working layer can be made the active one again** (live TL 1272: `addLayer` made `gb_temp_component` the active layer; the user chose to fix this before going on). Research only.
- Listener: `step=activate`, with the same preconditions as the steps after `addlayer` (a baseline in this listener run, exactly the working layer and `gb_temp_component`): ONE `working_layer.setActive()`. It reads back the active layer, `isActive()` of both layers (`is_active`), the layer names and both layers' elements, outlines and `autoLayer` / recipe. `working_active` needs the working layer active by name and by `isActive()`, the temporary layer's `isActive()` False, both layers and the layer list unchanged (`layers_unchanged`), and the width, source and glyph count unchanged; the active-layer change is not counted as a side effect for this step. Not marked. `flGlyph.updateActiveLayer(bool)` is kept in reserve, not called.
- Tests: `stub_listener_tests.py` 4557 → 4609 lines (2544–2549; 2530a and 2530b list the new step). Mutation run: 8 of 8 caught, after case 2548e was added for the one that first survived (the name check).

## Listener v0.181 (2026-11-18; server unchanged at v0.72): a temporary layer in the target glyph, research

**`/debug/trycomponent` gets `stage=templayer`** (the user's route order of 2026-11-18, after NE 1268 showed the recipe build replaces a layer's contents: a temporary layer first, [DECISIONS.md](DECISIONS.md)). Research only: no tool, no server change.
- Listener: `stage=templayer&target=cpp…&step=addlayer|build|move|removelayer[&recipe=cpp…]`, one step per request, `go=yes`, exactly one font open, one master, its own 10 calls per listener run; other parameters are refused. `addlayer`: on a target with exactly one layer (the active one), `autoLayer` off, holding one or more plain contour shapes and / or components of `cpp` glyphs, ONE `w.addLayer(flLayer("gb_temp_component"))`; it records the baseline (working layer name, elements with ink boxes, contours). `build` (`recipe=` one `cpp` glyph of plain contours): on the temporary layer only, empty with `autoLayer` off and recipe `""`, the proven sequence `recipe`, `autoLayer = True`, `buildAuto()`, `autoLayer = False`, `recipe = ""`, each read back (`substeps`), stopping at the first failure. `move`: ONE `working_layer.addShape(<the temporary layer's only component>)`. `removelayer`: ONE `w.removeLayer(<the layer named gb_temp_component>)`. Every step needs the working layer (found by name, never by being active) as recorded, reads back the layer names, the active layer, both layers' elements, contours, `autoLayer` / recipe and widths, the glyph width, the source and the glyph count, and reports `layer_added`, `built`, `moved` (with `same_as_temp_component`, `temp_still_holds_it`) or `layer_removed` (with `component_survived`, `placed_beside`). Only `removelayer` can mark the font, when the temporary layer is gone and the working layer holds the baseline plus exactly one new component; every other change is synced unmarked.
- Tests: `stub_listener_tests.py` 4412 → 4557 lines (2530–2543). Mutation run: 20 of 20 caught.

## Listener v0.180 (2026-11-18; server unchanged at v0.72): the recipe build on a glyph that is not empty, research

**`/debug/trycomponent` `stage=auto` takes `nonempty=yes`** (the user's choices of 2026-11-18: placing components into a glyph that already holds contours, components or both; research route "build in place" first). Research only: no tool, no server change; `add_component` still refuses a glyph that is not empty.
- Listener: with `nonempty=yes` the steps `setrecipe`, `setauto`, `build`, `unauto` and `clearrecipe` run on a target that holds at least one element, every one a plain contour shape (`isComponent` and `isComposite` both False) or a component of a `cpp` glyph; a Power Brush or unreadable shape, a component of another glyph, an empty target and an unreadable ink box are refused before anything is touched. `nonempty` with another stage or step, or with a value other than `yes`, is refused; without it every step behaves as before. `step=setrecipe` records the target's elements (kind, source, source layer, matrix, ink box) and outline for this listener run; every step then reports `existing_before`, `existing_after` and `existing_kept` (each recorded element found again, matrix and ink box within 0.001, and the recorded contours still in the outline, in order), with `existing_missing` and `new_elements`; `"unknown"` with `existing_note` when no `setrecipe` was recorded in this run. A build's width change is reported (`width_changed_by_build`), not counted as a side effect. `placed` (build): `existing_kept` and the new elements exactly components of the recipe's glyphs, in recipe order, at any matrix (reported). The font is marked only when that step is confirmed and `existing_kept` is true; any other change is synced unmarked. Still 6 probe calls per listener run.
- Tests: `stub_listener_tests.py` 4353 → 4412 lines (2520–2529). Mutation run: 12 of 12 caught.

## Listener v0.179 / server v0.72 (2026-11-18): `remove_component`

**A new tool removes components from a glyph** (P2.7; the user's design of 2026-11-18, [DECISIONS.md](DECISIONS.md)), through the call proven in RM 1241–1245, `layer.removeShape(component, False)`. Run live RC 1257–1264b ([LIVE-TESTS.md](LIVE-TESTS.md)); the auto-layer refusal stub-tested only.
- Listener: POST `/glyph/component/remove` takes `{"name", "index", "component", "x", "y"}` or `{"name", "components": [...]}`. Each entry names an element of `layer.shapes` by index, with the source and offset (dx, dy within 0.001) expected there; a mismatch, an index given twice, past the end or at a non-component refuses the whole call before anything changes. Also refused: more than one master, no modern layer, `autoLayer` on or an unreadable recipe, an unreadable ink box or `contoursCount`, contour counts that do not add up to the outline, and a Power Brush or other composite shape among the elements (F1: the guard's full check after the write reads the legacy layer; added in the build, not part of the approved design). Each shape's source is read again from the shape object just before the first removal. Removal runs from the highest index down, one call per entry, and stops at the first exception; a width FontLab changed is written back once (`width_changed_by_removal`, `cleanup`). `removed` only when the re-read shows the layer kept, exactly the other elements in order (kind, source, source layer, matrix), their ink boxes, the outline equal to the kept elements' contours (grouped by `contoursCount`), `autoLayer` and recipe, every source's outline, the width and the glyph count unchanged. The reply gives `entry_states` (removed, called but not confirmed, call failed, not reached), `components_after`, `empty_after`, `recipe_kept` and timing. Whenever the glyph changed it is synced and marked ("Glyphbridge remove component"); one OUTPUT line per call.
- Server: `remove_component(name, index, component, x, y, components)` checks the entries before sending (index 0–100,000, a non-empty name, x and y within ±20,000, fractions allowed, each index once, one form only), needs listener 0.179 and passes on only the known fields. `add_component`'s description and its list-form failure instruction name `remove_component` instead of "no Glyphbridge tool removes a component yet".
- Tests: `stub_listener_tests.py` 4260 → 4353 lines (2500–2510); `create_unicode_tests.py` 1420 → 1452 lines (section 43; 20e, 22r and 23b count 22 tools; 38w and 40h show the retired sentence gone). Mutation run: 32 of 32 caught (23 listener, 9 server); the first run missed "stop at the first failure", caught after case 2507n was added.

## Listener v0.178 / server v0.71 (2026-11-17): `add_component`'s single form writes the width back

**The single form now restores the advance width FontLab's build changes, as the list form and the tool's own description already said** (live 1250: `.notdef`, width 500, ended at 0 after placing `cpprs2`, `placed: false`; one run). The user approved the fix as proposed.
- Listener: after its steps, whether they succeeded or failed partway, the single form runs the list form's clean-up: `autoLayer = False` if still on, `recipe = ""` if the recipe was set but not cleared, and, whenever the recipe was set and the width differs from before, ONE `w.advanceWidth = width_before`. The reply gets `cleanup` (`auto_layer_set_back`, `recipe_cleared`, `width_restored`, each True or the failure; `auto_layer_set_back` moved there from the top level) and `width_set_by_build`, the width read before the write-back, only when it differed. The list form reports `width_set_by_build` too. "width unchanged" is still checked after the clean-up. A build that fails before placing anything now leaves the glyph as it was (recipe cleared), so the reply says nothing changed.
- Server: both forms pass on `width_set_by_build` (a finite number only); the single form's failure reply passes on `cleanup` (its known keys only); a listener 0.169–0.177 reply's top-level `auto_layer_set_back` still passes. The description's version line names 0.178 for the width write-back.
- Tests: `stub_listener_tests.py` 4240 → 4260 lines (2490–2492; 2424a–c now read `changed: false` with the recipe cleared, 2424e, 2424m and 2424p clear the recipe, 2424h is `placed: true`, 2425 counts two `recipe = ""` statements); `create_unicode_tests.py` 1409 → 1420 lines (section 42). Mutation run: 11 of 11 caught (6 listener, 5 server). Run live CC 1253–1256 ([LIVE-TESTS.md](LIVE-TESTS.md)): the width written back, `width_set_by_build` 0 and 300 (the source's advance).

## Listener v0.177 / server v0.70 (2026-11-17): components counted by `isComponent`

**A glyph's component count comes from its shapes' `isComponent`, not from FontLab's `componentsCount()`,** which read 0 on every glyph holding components (RM 1241–1246, [WATCH-POINTS.md](WATCH-POINTS.md)). The user approved the design as proposed after a check of every use: no tool decision rested on that count alone, but `check_notdef`'s evidence and `get_glyph_outline`'s note could mislead.
- Listener: `_tryshape_modern_state` sets `components` to the number of shapes in `layer.shapes` (a real list) whose `isComponent` reads True (`_layer_component_shapes`), 0 without reading `layer.shapes` when `shapesCount()` reads 0, and a "not readable: …" text when the list or a flag cannot be read. `componentsCount()` is still read, once, into `fontlab_components_count`, information and a guard only. Every guard that read `components != 0` (`move_nodes`, both forms of `add_component`, `_tryshape_modern_known_empty`, the probes) goes through `_state_has_components`: it refuses unless both counts read a plain 0, so the old refusals stand (a non-zero `componentsCount()` with no flagged shape still refuses); refusal texts name both counts (`_state_components_text`). `get_glyph_outline`'s modern `component_count` and `check_notdef`'s modern evidence now carry the shape count.
- Server: `_modern_outline_result` no longer says a component's outline "is not read by this tool", which was wrong on that route; for a count above 0 it says the outlines are included and where the sources are named, and for an unreadable count that it could not be read (text cleaned). The legacy routes keep their notes.
- Tests: `stub_listener_tests.py` 4225 → 4240 lines (2480–2482; 2316j, 2335g, 2346i show the new refusal texts; every printed state gains `fontlab_components_count`; the shapebox and notify fakes gained the `isComponent` / `shapes` that FontLab has); `create_unicode_tests.py` 1394 → 1409 lines (section 41; 11n and 25s show the new note). Mutation run: 13 of 13 caught (9 listener, 4 server). Run live CC 1248–1252 ([LIVE-TESTS.md](LIVE-TESTS.md)): the new note, "components 1" in `check_notdef`, the refusals unchanged.

## Listener v0.176 (2026-11-17; server unchanged at v0.69): research stages for removing a component

**Two gated stages of `/debug/trycomponent` for removing a component** (the user's choice of 2026-11-17: no tool removes a component, and Edit > Undo offered nothing after `add_component`, 1090). Research only: no tool, no server change. Names only first (1240, `/debug/classdir`): `flLayer.removeShape(flShape[, bool recursive=true])`, `clearComponents()`, `removeAllShapes([ShapeType])`, `flShape.remove([flObject])`.
- Listener: `stage=removeshape&target=cpp…&element=I&recursive=0|1&go=yes` makes ONE `layer.removeShape(<component I>, recursive)`, `recursive` always passed explicitly; `stage=clearcomponents&target=cpp…&go=yes` ONE `layer.clearComponents()`. The target must hold 1 to 30 elements, each a component of a cpp glyph, `autoLayer` off; the shape at I must still name the source read before. Every check before the call; counted in the probe's 6 per listener run before the glyph is read; one font open. The reply has elements, ink boxes, outline, state, `autoLayer` and recipe, width and glyph count before and after, every source's outline before and after, `call_returned`, `layer_kept`, `elements_as_expected`, `others_kept`, `empty_after`, `source_changed`, `side_effect_detected`, `removed` and `elapsed_seconds`; `removed` only when the elements left are exactly the expected ones, in order, with matrices and ink boxes unchanged, the layer kept and nothing else changed. A change is synced and marked (not marked when not confirmed). The new code sits in its own section, before the v0.155 probe section; the other stages are unchanged; `recursive` on another stage is refused.
- Tests: `stub_listener_tests.py` 4132 → 4225 lines (2470–2476; 2340c's stage list grows by the two stages). Mutation run: 13 of 14 caught; the one missed (dropping `layer_kept` from `removed`) is equivalent, since with no layer the element list cannot match; 2474n shows `layer_kept: false`. Run live RM 1240–1247 ([LIVE-TESTS.md](LIVE-TESTS.md)): `removeShape` removed exactly the component asked for (1241, 1243–1245); `clearComponents` changed nothing (1246).

## Listener v0.175 / server v0.69 (2026-11-17): underscore names refused in the list, honest states after a failed build

**`add_component`'s list form refuses source names with an underscore, and a failure reply says what the glyph holds** (the user's approved design of 2026-11-17, [DECISIONS.md](DECISIONS.md); evidence AC2 1200–1208, AC2u 1216–1235).
- Listener: `add_components` refuses a list with a source name holding `_` before anything is read or touched (`underscore_refused`, "nothing was changed"; FontLab's recipe of several glyphs reads `a_b` as a ligature of `a` and `b`, 1234). `component_states`: "not reached" only where `buildAuto()` was never called (the flag is `autoLayer = True` done); with the right element count as before, otherwise each entry is matched to an unused element of its source, in list order: "left by the build" or "missing after the build". The unused `reached` list and its states "placed by the build" / "offset set" are gone. Every failure reply past the first write gets `components_after` (`_comp_after`): per element its source, `x`, `y` and `plain_offset`, or "not a component" / "unreadable", or `{"error"}`.
- Server: `write_glyph_components` refuses an underscore name before anything is sent, also above 30 entries (no confirmation is asked); the single form is unchanged and still places such a glyph. `_COMP_LIST_STATES` gains the two states and drops the two never sent; `components_after` is passed on cleaned (`_comp_after_view`: names and errors through `_clean_font_text`, offsets only when finite numbers); the instruction asks the agent to tell the person which components are left and that no tool removes one. The description states the underscore rule, the states and `components_after`. Still needs listener 0.174 for the list (`components_after` from 0.175).
- Tests: `stub_listener_tests.py` 4113 → 4132 lines (2466–2468; 2463a–e and 2463g now show the new states); `create_unicode_tests.py` 1379 → 1394 lines (section 40; 39z7's text check follows the description). Mutation run: 17 of 17 caught (10 listener, 7 server). Not yet run live.

## Listener v0.174 / server v0.68 (2026-11-17): `add_component` with a `components` list

**Several components in one call, and no element cap** (the user's design, [DECISIONS.md](DECISIONS.md) 2026-11-17 "several components"; route proven with the probe, PC2 / PC3 1102–1177).
- Listener: `POST /glyph/component` also takes `{"name", "components": [{"component", "x", "y"}, …], "confirmed_untested_size"}` through a new function, `add_components`; the single form's code is unchanged. More than 30 entries without the flag are refused before any change (`untested_size`). Checks before the first write as the single form, each distinct source once; names may not contain `+`. Steps: recipe of the names joined by `+` (repeats kept), `autoLayer` on, ONE `buildAuto()` that must return True, `autoLayer` off, the built elements checked against the list in order, ONE `shape.transform = QTransform(…)` for each element not already at its offset. Clean-up always: `autoLayer` off if still on, `recipe = ""`, the advance width written back (`advanceWidth`); placing stops at the first failure. `placed` only when the re-read confirms the count, each source, layer, matrix and ink box, the recipe, `autoLayer`, the sources, the width and the glyph count; then marked. Reply: `component_states` (placed, at FontLab's position, not reached, unknown), `cleanup`, `build_seconds`, `elapsed_seconds`; OUTPUT line `component <glyph>: N components (verified)`.
- Both 20-element caps removed (no recorded reason): `_COMPONENT_BOX_MAX` (v0.130, the outline route; `get_glyph_outline` now gives every component its boxes and the reply `elements.boxes_seconds`) and `_TRYSHAPEBOX_MAX_SHAPES` (v0.129, `_tryshapebox_boxes`; v0.173's `max_shapes` gone).
- Server: `add_component(name, component=None, x=0, y=0, components=None, confirmed_untested_size=False)`, one form per call; above 30 without confirmation nothing is sent and the reply has `needs_confirmation` and an instruction to ask the person; the list form needs listener 0.174; success only with all seven checks; a failure returns `component_states`, `cleanup`, `checks`, `timing`. `get_glyph_outline` adds `verification.element_boxes_seconds`. The description names the list, the soft limit, repeats, the width written back, stop-then-clean-up and the request-size limit.
- Tests: `stub_listener_tests.py` 4059 → 4113 lines (2460–2465; 2150, 2425's scan region and 2452 follow the change); `create_unicode_tests.py` 1341 → 1379 lines (section 39, 32j now boxed, 32s2, 38w's signature). The single form's cases unchanged. Mutation run: 22 of 22 caught, after three gaps (a box off its matrix, a changed source, the outline timing) got cases. Run live 1178–1179: the versions, and `get_glyph_outline` of 30 components all `source_in_step` true; the list form not yet (the resumed session kept the old schema).

## Listener v0.173 (2026-11-17; server unchanged at v0.67)

**`/debug/trycomponent`: 30 components, with timing** (the user's choice of 2026-11-17, with Chinese characters in mind: test 30, with 15 as a middle control, before `add_component`'s list limit is set).
- `stage=auto` takes recipes of one to 30 glyphs; `stage=offset&element=I` works on a layer of 2 to 30 components (element 0 to 29).
- The probe reads up to 30 ink boxes through its own limit: `_tryshapebox_boxes` takes `max_shapes`, passed only by the probe. The shared `_TRYSHAPEBOX_MAX_SHAPES = 20` (set in v0.129 with no recorded reason) stays for `/debug/tryshapebox` and `add_component`.
- Timing: `build_seconds` for the `buildAuto()` call; `elapsed_seconds` for each `stage=auto` / `stage=offset` request as a whole (refusals included).
- Tests: `stub_listener_tests.py` 4045 → 4059 lines (2450–2452; 2440d, 2442c and 2445c now refuse element 30, 31 components and a 31-glyph recipe). Timing values are checked for type only. Mutation run: 10 of 10 caught. Run live 1152–1177: 15 and 30 glyphs and a repeated source as predicted, each request in milliseconds; `get_glyph_outline` hit the shared 20-element cap (1168).

## Listener v0.172 (2026-11-17; server unchanged at v0.67)

**`/debug/trycomponent`: four and five components** (the user's choice of 2026-11-17: test four and five glyphs before `add_component`'s list limit is set; the list itself is decided: a new `components` parameter).
- `stage=auto` takes recipes of one to five glyphs (`_TRYCOMP_AUTO_PARTS_MAX`); `stage=offset&element=I` works on a layer of 2 to 5 components (`_TRYCOMP_SEVERAL_MAX`, element 0 to 4). Nothing else changed.
- Tests: `stub_listener_tests.py` 4030 → 4045 lines (2447–2449; 2440d, 2442c and 2445c now refuse element 5, six components and a six-glyph recipe; the "2 to 3" and "one to three" wordings now say 5 and five). Mutation run: 6 of 6 caught. Run live 1129–1151: four and five glyphs as predicted; FontLab set the width to 500 each time.

## Listener v0.171 (2026-11-17; server unchanged at v0.67)

**`/debug/trycomponent`: several components in one glyph** (P2.7; the user's choice of 2026-11-17, after 1049 put the second component of a two-glyph recipe at (−200, 0) and set the width 0 → 500).
- `stage=auto` takes recipes of one to three glyphs; `generate` / `setgenerated` keep two.
- `stage=offset&how=assign&element=I&dx=DX&dy=DY`: on a layer of 2 or 3 components of `cpp` glyphs, each matrix a plain offset, `autoLayer` off, the shape at position I must still name the source read at I; then ONE `shape.transform = QTransform(1, 0, 0, 1, dx, dy)` on it (absolute, different from its offset; (0, 0) allowed). `offset_placed`: I's matrix reads the offset, its ink box moved by the difference, every other element (source, layer, matrix, ink box) unchanged, no side effect (width, sources, glyph count, recipe / `autoLayer`); only then is the font marked. Raw nodes reported only. Without `element=` the stage is unchanged. No new probe call for the width: `set_glyph_width` is used live.
- Tests: `stub_listener_tests.py` 3959 → 4030 lines (2440–2446; 2390g's refusal now says "one to three"). Mutation run: 20 of 20 caught. Run live PC2 1102–1128: every step as predicted (two and three components, one offset set at a time, the width set back with `set_glyph_width`).

## Server v0.67 (2026-11-17; listener unchanged at v0.170)

**`add_component`'s description corrected after test 1090** (the user's request of 2026-11-17; a text change only, no code path changed).
- The sentence "whether FontLab's Edit > Undo takes the component back is untested" becomes: Edit > Undo offers nothing to take the component back (seen live once: Undo was greyed out), and no Glyphbridge tool removes a component yet.
- Tests: `create_unicode_tests.py` 38w now checks the new sentences instead of the old one, 1341 lines as before; the version lines 0.66 → 0.67 in the same harness. Read live after a restart of Claude Desktop: the new description, and `fontlab_status` server 0.67 / listener 0.170.

## Listener v0.170 (2026-11-17; server unchanged at v0.66)

**`/debug/markswitch`: the changed mark off and on for one listener run** (S1 research; the user's choice of 2026-11-17, to make clear whether `add_component` alone brings FontLab's save question: in Demo mode a font never returns to "unchanged", and every tool that sets up a test glyph marks it).
- `GET /debug/markswitch` reads `_MARK_CHANGED`; `?on=0|1&go=yes` sets it for THIS listener run only (a restart sets it on again). No FontLab call, no font touched. While it is off, every write reply says so in `fontlab_changed_mark` ("switched off in the listener") and the server adds `save_question_note`; the OUTPUT panel prints one line at each real change of the switch.
- Tests: `stub_listener_tests.py` 3940 → 3959 lines (2430a–2433). Mutation run: 5 of 5 caught. Run live 1097–1101: the save-question pair for `add_component`.

## Listener v0.169 / server v0.66 (2026-11-17): `add_component`

**The first tool that places a component** (P2.7; design of the user, [DECISIONS.md](DECISIONS.md) 2026-11-17; the route proven with `/debug/trycomponent`, 1039–1058).
- Listener: `POST /glyph/component` `{"name", "component", "x", "y"}` (whole numbers, ±10,000). Refused before any write: no font, more than one master, the glyph missing, without a layer, not empty, or with `autoLayer` on or an unreadable recipe; the component glyph missing, the glyph itself, without plain contours only (a component, Power Brush or other composite shape refused) or without nodes, or its ink box unreadable. Steps: `recipe = component`, `autoLayer = True`, ONE `buildAuto()` that must return True, `autoLayer = False`, `shape.transform = QTransform(1, 0, 0, 1, x, y)` only for an offset, `recipe = ""`. `placed` (and `verified`) only when every check reads true: one component of the source on its layer, the offset, its `inkBox()` equal to the source's moved by (x, y), the recipe cleared, `autoLayer` off, the source, the advance width and the glyph count unchanged. After a failure once `autoLayer` was on, ONE `autoLayer = False` (`auto_layer_set_back`); nothing else restored, nothing marked. Mark title "Glyphbridge add component"; guard kind full; OUTPUT line `component <glyph>: <source> at (x, y) (verified)`.
- Server: tool `add_component(name, component, x=0, y=0)` (21 tools), needs listener 0.169; whole-number offsets (a whole float accepted); success only when the listener's `placed`, `verified` and all eight checks are true; a refusal that changed nothing is an error; a changed but unconfirmed glyph returns `steps_done`, `checks`, `elements_after` and counts as a change (an unknown outcome as uncertain). The description names the limits: one master, an empty glyph, plain source, Undo untested, the unexplained 1059.
- Tests: `stub_listener_tests.py` 3865 → 3940 lines (2420–2425f); the `move_nodes` static scan now ends where the new section starts, its output unchanged; new fake modes for the trycomponent fakes, earlier output unchanged. `create_unicode_tests.py` 1315 → 1341 lines (section 38; tool count 20 → 21). Mutation run: 29 of 29 caught (23 listener, 6 server). Run live AC 1079–1101: all as predicted except Edit > Undo, which offered nothing (1090).

## Listener v0.168 (2026-11-17; server unchanged at v0.65)

**`/debug/trycomponent stage=auto&step=clearrecipe`: can the recipe left after a build be cleared?** (the user's design choice of 2026-11-17 for the planned placing tool: research clearing the recipe first; 1057 had not shown it re-applied.)
- ONE `layer.recipe = ""` on a layer whose `autoLayer` reads False, that holds only components of `cpp` glyphs and whose recipe reads a non-empty text; read back. Refused, nothing touched: `autoLayer` on, an empty layer or a plain shape, an empty or unreadable recipe, a recipe in the request.
- `recipe_cleared`: the recipe reads `""`, the same components (source, layer, matrix) and outline, `autoLayer` still False, no side effect (width, glyph count, sources). Only then is the font marked; an outline change is synced unmarked.
- Tests: `stub_listener_tests.py` 3830 → 3865 lines (2411–2415; 2390a, b list the new step). The 0.165 call count now looks for the `setrecipe` form of `layer.recipe =`, its output unchanged. Mutation run: 8 of 10 caught; the two left (`step_took_effect` and `component_kept` dropped from the verdict) are equivalent, since either one false already makes `side_effect_detected` true. Run live 1058 (`recipe_cleared` true); 1059 refused, rightly: `cpp2tgt` no longer held components.

## Listener v0.167 (2026-11-17; server unchanged at v0.65)

**`/debug/trycomponent stage=offset`: can a placed component be given an offset?** (live 1042: a normal component of `cpp1src` at identity in `cpp1tgt2`; the user's approval of 2026-11-17: "first an offset after the build". Names only: `flShape.transform`, docstring "transform"; `flShape.applyTransform([QTransform transform])`; no `setTransform`, `translate` or `move`.)
- `stage=offset&target=cpp…&how=assign|apply&dx=DX&dy=DY&go=yes`, ONE call per request: `assign` sets `shape.transform = QTransform(1, 0, 0, 1, dx, dy)`, `apply` makes ONE `shape.applyTransform(<the same QTransform>)`. Only on a layer that holds exactly one element, a component of a `cpp` glyph at the identity matrix, with `autoLayer` False. (dx, dy) may not be (0, 0). `how` belongs to this stage only, and the stage takes no source and no recipe.
- The reply has, before and after: the element (source, layer, matrix), its ink box (`shape.inkBox()`, read only on components since 644–656), the raw nodes of `layer.getContours()`, the source's outline, the width, `recipe` / `autoLayer` and the glyph count. `offset_placed` is true when the matrix reads the offset, the ink box moved by exactly (dx, dy), the raw nodes are unchanged or moved by the offset (`raw_nodes` says which), and nothing else changed. Only then is the font marked; any other change is synced unmarked.
- Tests: `stub_listener_tests.py` 3762 → 3830 lines (2405–2410a; 2340c lists the new stage). Mutation run: 16 of 16 caught. Run live 1043–1044 (`how=assign`, one run): `offset_placed` true; `how=apply` not run. The steps of 0.165 / 0.166 also ran a two-glyph recipe, 1045–1050a.

## Listener v0.166 (2026-11-17; server unchanged at v0.65)

**`stage=auto&step=unauto|killauto`: can the component `buildAuto()` placed become a normal one?** (live 1041b, 1041c: it shows as an auto layer, its element greyed and locked; the user's approval of 2026-11-17).
- On a layer whose `autoLayer` reads True and that holds only components of `cpp` glyphs: `unauto` sets `layer.autoLayer = False` and reads it back; `killauto` makes ONE `layer.killAuto()` (its effect on the recipe is reported, not counted as a side effect). `component_kept`: the same components (source, layer, matrix) and the same outline after; `component_normal`: kept, `autoLayer` False and no side effect; only then is the font marked. Any other outline change is synced unmarked.
- Tests: `stub_listener_tests.py` 3731 → 3762 lines (2400–2404; 2390a, b list the new steps). The 0.165 checks were narrowed, their output unchanged: the static scan no longer forbids `killAuto(`, and the call count looks for `autoLayer = True`. Mutation run: 9 of 9 caught. Run live: `unauto` 1042, 1050; `killauto` 1055 (it changed nothing the probe reads).

## Listener v0.165 (2026-11-17; server unchanged at v0.65)

**`/debug/trycomponent stage=auto`, FontLab's own recipe build** (live 1037: `name_id` items gave "GlyphComponent expected", so every argument of the four-argument form is right and its "must be Int" most likely asks for the fifth; the user's choice of 2026-11-17: the recipe route next. Names only: `flLayer.recipe` QString, `flLayer.autoLayer` bool, `bool flLayer.buildAuto()`, `killAuto()`).
- `stage=auto&target=cpp…&step=S&go=yes`, ONE step per request on an existing target layer, empty for every step but `read`: `read` (`recipe`, `autoLayer`, nothing changed), `setrecipe&recipe=R` (`layer.recipe = R`, read back), `setauto` (`layer.autoLayer = True`, read back), `build&recipe=R` (`layer.buildAuto()` once, only when the recipe reads exactly R). R as for `generate`.
- Each reply has `auto_before` / `auto_after`, the elements, outline, width, the recipe glyphs and the glyph count before and after, `step_took_effect`, `outline_changed` and `side_effect_detected`; `build` adds `placed` and `component_placed`. Only a confirmed component from `build` is marked; any other outline change is synced unmarked. `killAuto()` is never called.
- Tests: `stub_listener_tests.py` 3674 → 3731 lines (2390–2399a; 2340c lists the new stage). Mutation run: 12 of 12 caught. Run live 1038–1041b, 1046–1049, 1052–1054.

## Listener v0.164 (2026-11-17; server unchanged at v0.65)

**`setgenerated&items=id`, the list's contents as the one variable** (live 1036: a whole-number width gave "must be Int!" too; FontLab's archived FontLab 7 reference gives `bool setGlyphComponents(QList result, double width, flPackage package, bool colorize)`; the user's choice of 2026-11-17: one more probe, then, if it fails, find out whether the legacy route is the only way).
- `items=id` passes each `GlyphComponent`'s `name_id` (a plain whole number up to a uint's maximum) in place of the object; a list that is not a real Python list, or a `name_id` that is not such a number, is refused before the call. `items_passed` and `call_made` name what was passed. Only `stage=setgenerated` takes it.
- Tests: `stub_listener_tests.py` 3657 → 3674 lines (2386–2389). The FontLab-like fake now holds two readings of the "must be Int" of 1033 / 1036: `width_must_be_int` (disproved by 1036; kept for the 2381 and 2384 cases, whose output is unchanged) and `items_must_be_int` (tested by 1037). Mutation run: 6 of 6 caught. Not yet run live.

## Listener v0.163 (2026-11-17; server unchanged at v0.65)

**`setgenerated&width=int`, the second argument as the one variable** (live 1035: `0` as the fourth gave "argument type must be Boolean!", so the fourth is a bool after all and 1033's "must be Int" came from the first two, most likely the width `0.0`; the user's approval of 2026-11-17).
- `width=int` passes the width as a whole number; a width that is not one is refused before the call. `call_made` names it. Only `stage=setgenerated` takes it.
- Tests: `stub_listener_tests.py` 3641 → 3657 lines (2383–2385). The FontLab-like fake now answers as live 1031, 1033, 1034 and 1035 (count, then third, then fourth, then second), so 2381d now fails with "must be Boolean" as 1035 did. Mutation run: 5 of 5 caught. Not yet run live.

## Listener v0.162 (2026-11-17; server unchanged at v0.65)

**`setgenerated&int=yes`, the fourth argument as the one variable** (live 1034: the fgId gave "Wrong argument type. flPackage expected.", so the package object is right and 1033's "must be Int" was the fourth argument, `False`; the user's approval of 2026-11-17).
- `int=yes` passes the whole number `0` in place of `False`; `call_made` names it. Only `stage=setgenerated` takes it.
- Tests: `stub_listener_tests.py` 3623 → 3641 lines (2380–2382; a fake that answers as FontLab did in 1031, 1033 and 1034). Mutation run: 5 of 5 caught. Not yet run live.

## Listener v0.161 (2026-11-17; server unchanged at v0.65)

**`setgenerated&pkg=id`, the third argument as the one variable** (live 1033: with `args=4`, "TypeError: argument type must be Int!" instead of the argument-count error; the user's approval of 2026-11-17).
- `pkg=id` passes the package's `fgId` as the third argument of `setGlyphComponents`, read as the KERNING panel refresh reads it; a value that is not a plain whole number from 0 to a uint's maximum is refused before the call. `package_fgid` and `call_made` name what was passed. Only `stage=setgenerated` takes it.
- Fixed while building: `call_returned` was read even when the call had not been made.
- Tests: `stub_listener_tests.py` 3605 → 3623 lines (2376–2378). Mutation run: 7 of 7 caught. Not yet run live.

## Listener v0.160 (2026-11-17; server unchanged at v0.65)

**`setgenerated&args=N`, the argument count as the one variable** (live 1031: FontLab's own list gave the same "IndexError: Unexpected SeqBase<T> length." as 1026; in this project that error meant a wrong argument count before, [topics/geometry.md](topics/geometry.md); the user's approval of 2026-11-17).
- `args=N` (2 to 5, default 5) calls `layer.setGlyphComponents` once with the first N of `(list, width, package, False, 0)`; `call_made` names the call. Only `stage=setgenerated` takes it; the message before `go=yes` names the count.
- Tests: `stub_listener_tests.py` 3587 → 3605 lines (2372–2375; 2360b's message). Mutation run: 6 of 6 caught. Not yet run live.

## Listener v0.159 (2026-11-17; server unchanged at v0.65)

**`setgenerated` takes the form `generateGlyph` really returns** (live 1032: a real list of one `GlyphComponent`, `name_id` 5113, identity, no width; the user's approval of 2026-11-17).
- `stage=setgenerated` also accepts a real list of 1–20 items that are all `GlyphComponent` (by `isinstance` only) and passes it as is to ONE `layer.setGlyphComponents(<list>, <the target's own advance width>, package, False, 0)`; `width_source` says so. A list with any other item, or an unreadable target width, is refused before the call.
- A pair now needs a number as its second item, so the list of two `GlyphComponent` of a two-glyph recipe is not taken for a pair.
- Tests: `stub_listener_tests.py` 3577 → 3587 lines (2371a–h); the refusal wording and the step label changed in 2365c, g, m and 2370a–c, and 2370a's `setgenerated` now places. Mutation run: 6 of 6 caught. Not yet run live.

## Listener v0.158 (2026-11-17; server unchanged at v0.65)

**`generateGlyph` results that are not a pair** (live 1030: a real list of one item; the user's approval of 2026-11-17).
- `stage=generate` / `setgenerated`: a real list or tuple that is not a pair is described item by item (`generate_returned_items`, at most 20); `setGlyphComponents` is still called only for a pair.
- Every description (also `layer.components` of 0.156) is by type only: a value is a transform only when it is an instance of the `QTransform` class (no member of an unknown object is read; the spies had caught 0.157 reading `m11` from one), a `GlyphComponent` gives its documented members, and a real tuple or list is described part by part, two levels deep at most. In the reply a transform part is `{"type", "matrix"}` (was `{"type", "value": {"matrix"}}`).
- Test fix: the static scan of the read stage (2355) had covered the 0.157 generate code too and listed its calls; it now covers the read stage only. That line was accepted unnoticed in the 0.157 update.
- Tests: `stub_listener_tests.py` 3567 → 3577 lines (2370a–e). Mutation run: 7 of 7 caught. Not yet run live.

## Listener v0.157 (2026-11-17; server unchanged at v0.65)

**`/debug/trycomponent stage=generate / setgenerated`** (P2.7; the user's approval of 2026-11-17, after 1029 read an empty `layer.components`). Names only first: `flPackage.generateGlyph(string recipe, string layer_name, FontMetrics metrics, bool rtl)` returns `(QList<GlyphComponent>, double width)`; `FontMetrics(flPackage p, string layer_name)`.
- `stage=generate&target=cpp…&recipe=R&go=yes`: `FontMetrics(package, <target's layer name>)`, then ONE `package.generateGlyph(R, layer_name, metrics, False)`. What it returns is described (a list only when it is a real Python list or tuple); the target, the recipe glyphs and the glyph count are compared before and after, and any change is `side_effect_detected`.
- `stage=setgenerated`: the same call, then ONE `layer.setGlyphComponents(<the returned list, as is>, <the returned width>, package, False, 0)`, read back as the 0.155 stages; the returned width is not counted as a side effect. `placed` = components naming the recipe glyphs, in order, at the identity matrix.
- R is one or two `cpp` glyph names joined by `+` (sent as `%2B`: a plain `+` arrives as a space and is refused), none of them the target; no `@` placement.
- Tests: `stub_listener_tests.py` 3520 → 3567 lines (2360–2368); `create_unicode_tests.py` 1314 → 1315: the no-save scan (8x) now leaves out the `/debug/trycomponent` block, and 8x1 lists that block's save / export / generate calls, where only `.generateGlyph(` may appear (it builds components and writes no file). Mutation run: 17 of 17 caught. Not yet run live.

## Listener v0.156 (2026-11-17; server unchanged at v0.65)

**`/debug/trycomponent stage=readcomponents`, read only** (P2.7; the user's approval of 2026-11-17, after 1026 and 1027 failed at argument conversion).
- `stage=readcomponents&target=cpp…&go=yes`: one font, the shared cap of 6, no source and no offset. ONE read of `layer.components` (called once with no argument if it is callable). Only a real Python list or tuple is indexed, at most 20 items; a tuple or list item is described part by part (text, numbers, a transform as its matrix), a `GlyphComponent` by `name_id`, `width_scale`, `use_anchors` and its matrix, anything else by its type name. Anything else at the top level is reported by type only. `side_effect_detected` compares the layer counts and the glyph count before and after.
- Every element listing of the probe also gives `shape_data_type`, the type name of `shape.shapeData`.
- Tests: `stub_listener_tests.py` 3501 → 3520 lines (2350–2355) and 7 version lines, `create_unicode_tests.py` 2 version lines. Mutation run: 9 of 9 caught. Not yet run live.

## Listener v0.155 (2026-11-17; server unchanged at v0.65)

**`/debug/trycomponent`, research for placing a component** (P2.7; the user's approval of 2026-11-17). Names only first (no font needed): `flLayer.addComponent` takes an `flComponent`, which is not a public name, so it is not tried; `flLayer.setGlyphComponents(QList<GlyphComponent>, double width, flPackage, bool colorize, uint flags)` and `GlyphComponent(string name)` (members `name_id`, `transform`, `width_scale`, `use_anchors`) are the first route; `flShape(flShapeData)` with `layer.addShape` the second.
- Gated probe, research only: `go=yes`, exactly one font open, `target` and `source` named `cpp…` and different, `dx` / `dy` whole numbers within ±1000, 6 calls per listener run counted before either glyph is read. The source needs one plain shape with nodes; the target needs an existing layer (a glyph with no layer is refused: the Add Component crash) with at most one plain shape.
- `stage=glyphcomponents`: `GlyphComponent(source)`, its transform set to `QTransform(1, 0, 0, 1, dx, dy)` and read back, then ONE `layer.setGlyphComponents([gc], <target advance width>, <current package>, False, 0)`. `stage=shapedata`: `flShape(<source shape>.shapeData)`, the same transform, then ONE `layer.addShape`.
- Reply: the target's elements (`is_component`, `component_glyph`, `component_layer`, `reference_count`, matrix), counts, outline and advance width before and after; the source's elements and outline before and after; the glyph count; `placed`, `existing_kept`, `source_contours_in_outline`, `side_effect_detected`, `component_placed`. A change goes through `_guard_mark` (mark title "Glyphbridge component"); only a confirmed placement is marked.
- Tests: `stub_listener_tests.py` 3439 → 3501 lines (2340–2349) and 7 version lines, `create_unicode_tests.py` 2 version lines. Mutation run: 19 of 19 caught. Not yet run live.

## Server v0.65 (2026-11-15; listener unchanged at v0.154)

**`move_nodes` notes after MN 1016–1024** (the user's approval of 2026-11-15).
- No `display_note` in a `move_nodes` reply: the listener's shared note gives repaint steps ([DECISIONS.md](DECISIONS.md), 2026-11-13); `person_note` covers the lag.
- `undo_note` in every reply whose outline changed (a verified move, and a re-read that differs with `changed: true`): FontLab's Edit > Undo lists the move but did not move the nodes back (1023); `agent_instruction` ends with "Tell the person undo_note once per conversation." The tool description says the same.
- Tests: `create_unicode_tests.py` 1308 → 1314 lines (37zm1–37zm6) and 13 version lines. Mutation run: 3 of 3 caught. Run live 1025.

## Listener v0.154 and server v0.64 (2026-11-15)

**`move_nodes` verification after the live run** (MN 1001–1015; the user's approval of 2026-11-15, [DECISIONS.md](DECISIONS.md)).
- Listener: no `layer.resetInkBox()` call (no proven effect: 1003–1006); `margins` are FontLab's values as read. Message coordinates print `0`, not `-0` (1002).
- Server: `verified` = the re-read nodes match; `left`, `right`, `ink_width` computed from the re-read nodes (exact curve extents) and FontLab's advance width (`sidebearings_source`); FontLab's own values in `fontlab_sidebearings` with `fontlab_sidebearings_current`; when they lag, `person_note` (one plain sentence) and an `agent_instruction` to say it once. `sidebearings_current`, `extent_check`, `verification_note` and `ink_box_refresh` are gone.
- Tests: `stub_listener_tests.py` 3439 lines (refresh cases renamed, 2334f the `-0` fix), `create_unicode_tests.py` 1306 → 1308 (part 37 rewritten, 37c2, 37k2). Mutation run: 13 of 13 caught. Not yet run live.

## Listener v0.153 and server v0.63 (2026-11-15)

**`move_nodes`, the first edit of an existing outline** (P2.2; design approved by the user on 2026-11-15, [DECISIONS.md](DECISIONS.md)).
- Listener: POST `/glyph/move` `{"name", "moves": [{"contour", "node", "from": {x, y}, "to": {x, y}}]}`, 1–200 moves, no node twice, `to` rounded by rule B (`coordinates_rounded`), `to` = `from` refused. The glyph needs ONE plain shape (`isComponent` and `isComposite` False), no components and an identity shape transform. Every check runs before the first node is touched: index, `from` within 0.001, and a smooth on-curve node newly off its line (draw_path's 2-degree rule; one already off before does not count). Then `node.x` / `node.y`, ONE `layer.resetInkBox()`, the re-read compared node by node (position, kind, smooth flag), and `_guard_mark` (kind `move_nodes`, full guard check, mark title "Glyphbridge move nodes"); the font is marked whenever the outline changed, confirmed or not; nothing is restored. The OUTPUT panel logs `move <glyph>: N nodes`.
- Server: tool `move_nodes(name, moves)` (20 tools), checks everything before sending, needs listener 0.153. Success: `moved`, `nodes_match`, `verified` only when the re-read outline's extent (exact curve extents) equals FontLab's left sidebearing and ink width (`sidebearings_current`, `extent_check`). A re-read that differs returns `moved: false` with `mismatches`, `before`, `after` and an instruction to move back only with the person's agreement; a refusal that changed nothing is a ToolError.
- Not in the approved design, added for safety: the identity-transform refusal (a stored node position must be the drawn one, 638), and the route name `/glyph/move` (GET `/glyph/nodes` is an older debug read).
- Tests: `stub_listener_tests.py` 3364 → 3439 lines (2332–2338), `create_unicode_tests.py` 1266 → 1306 (part 37, tool counts). Mutation run: 12 of 12 caught. Run live 1001–1002: the sidebearings were not current (see v0.154).

## Listener v0.152 (2026-11-14; server unchanged at v0.62)

**`/debug/tryedit&refresh=R`** (P2.2 research, step B2): after a confirmed edit, ONE member of the fixed table `_TRYEDIT_REFRESH` (`contour.update` with `movenode` only, `shape.update`, `shapedata.update`, `layer.update`, `glyph.update`, `layer.changed`, `shape.changed`, `layer.resetinkbox`), called once before `_guard_mark`; the sidebearings before and after it against those the edited nodes give (straight contours only), `refresh_changed_outline` as a side effect. Unknown values and `resetMetrics*` are refused; no refresh after a failed edit. Tests: `stub_listener_tests.py` 3318 → 3364 lines (2321–2331); `create_unicode_tests.py` version lines only. Mutation run: 6 of 6 caught. Run live 989–1000.

## Listener v0.151 (2026-11-14; server unchanged at v0.62)

**`/debug/tryedit`** (P2.2 research, step 2; the editing goal of 2026-11-14, [DECISIONS.md](DECISIONS.md)): ONE edit of a plain drawn glyph per call, `go=yes`, names starting with `edp`, exactly one font open, 8 per listener run counted before the glyph is read. Stages: `movenode` (`node.x`, `node.y`), `addcontour` (a fixed square through `shape.shapeData.addContour`), `removecontour` (`shape.shapeData.removeContour`), `replace` (a fixed triangle through `layer.replaceShape`). A plain glyph: one shape, `isComponent` and `isComposite` False, no components; contours only through `layer.getContours()`, nodes through `getNodeAt`. The reply has the outline before and after, `expected_after`, `mismatches`, `smooth_changed`, the glyph count before and after, `side_effect_detected` and `edited`; a change goes through `_guard_mark` and is marked as "Glyphbridge edit" (new in `_MARK_TITLES`). Never called: `font.update()`, save, `smartMove`, `smartSetXY`, `moveBy`, `decomposite`, `ejectTo`, `shapeBuilder`, `activateBuilder`. Tests: `stub_listener_tests.py` 3262 → 3318 lines (2311–2320: refusals, the four stages, sync and mark, the plain-glyph gate, failure modes, the call cap, spies and a static scan); `create_unicode_tests.py` version lines only. Mutation run: 6 of 6 caught. Not yet run live.

## Listener v0.150 and server v0.62 (2026-11-13)

**The first glyph of a new font with other fonts open** (ROADMAP P0.9; design approved 2026-11-13, [DECISIONS.md](DECISIONS.md)).
- Listener: `_package_layer_name(font, w)` takes the master name from the glyph's own package, `w.package`, with any number of fonts open. It refuses unless `CountFonts()` is a plain whole number of at least 1, the current package and the glyph's package are not null, both `fgId` values are plain numbers and equal, and the old checks hold (one master, `defaultMaster` = `master` = the one name in `masters`, glyph count and units per em). The number of workspace packages is no longer read. `_derive_layer_name` passes the wrapper on; without one the master name is not used.
- Listener: `create_font`'s front check compares the `fgId` of the new and the current package instead of `isEqual` (930, 931); the "double-click the first glyph" note is gone.
- Server: the `create_font` description drops the same sentence.
- Tests: `stub_listener_tests.py` 3252 → 3262 lines (gate cases 760–799b: new refusals 765–767i, accepted 760–760c, direct calls 796 and 796b, the scan 799b; 2304i–j now an unreadable and a bool `fgId`); `create_unicode_tests.py` 1266 lines (version lines and one note fewer in 36z). Mutation run: 11 of 11 caught. Run live 932–936.

## Listener v0.149 (2026-11-13; server unchanged at v0.61)

**`/debug/trypackage?stage=cached&go=yes`** (P0.9 research): the wrappers already in the listener's cache, at most 20, none built; each checked against its key (`fgGlyphId`) and `isValid` first, then ONE read of its package, that package's `isNull`, `fgId`, `glyphsCount`, and ONE `isEqual` against the current package; the run counter of the glyph stage. Tests: 3236 → 3252 lines (2310a–o). Mutation run: 12 of 12 caught. Run live 930, 931.

## Listener v0.148 (2026-11-13; server unchanged at v0.61)

**`/debug/trypackage?name=X&go=yes`** (P0.9 research, read only, any number of fonts open): ONE read of `flGlyph.package` of a glyph of the font in front, that package's reads, ONE `isEqual` against the current package, the font in front's glyph count, units per em and path for comparison, `CountFonts()` and the package count before and after; 20 per listener run. Tests: 3203 → 3236 lines (2309a–ae). Mutation run: 6 of 6 caught. Run live 928, 929.

## Listener v0.147 and server v0.61 (2026-11-13)

**Plainer `create_font` notes and a pointer to the OUTPUT panel** (the user's wording, 2026-11-13; CF 915–922, [DECISIONS.md](DECISIONS.md)).
- Listener: the unsaved note drops "Glyphbridge never saves". For a named font the tab note (with its two-edit Font Info workaround) and the FONTS-panel note ("sometimes even after that") become one: the temporary name may still show in the tab and the FONTS panel, it is only a display delay, Font Info shows the actual names, and saving and reopening should update the display. The temporary name is the creation family, else the creation Full name. "Should": not yet tested, FontLab runs in Demo mode ([ROADMAP.md](ROADMAP.md) P0.3).
- Server: the `create_font` instruction and description ask the agent to tell the person once per conversation that FontLab's OUTPUT panel lists every change with its warnings and is worth keeping open; the description drops the two-step workaround.
- Tests: `stub_listener_tests.py` 3206 → 3203 lines (one note fewer in 2302m, 2306, 2307), `create_unicode_tests.py` 1266 lines (the instruction texts, note counts 5 → 4); text-only change, no new guard path, so no mutation run. Run live 2026-11-13 (923–925): the reply, the instruction and the OUTPUT panel as intended.

## Listener v0.146 and server v0.60 (2026-11-12)

**`create_font` / `POST /font/create {"family"?}`** (ROADMAP P0.3 / P0.4; design approved 2026-11-12, [DECISIONS.md](DECISIONS.md)).
- Listener: ONE `flPackage()` per request, with or without other fonts open and with no per-run cap. Success only when `CountFonts()` went up by exactly one and the workspace's current package `isEqual` the new one; otherwise `created: false` with the reason, and nothing is named or marked. With `family`: `tfn`, `ffn`, `psn`, `sgn` as Build Names gives them, each read back; then the legacy `font.info.familyName`, written only when the font in front still reads the new package's own family; then, only when all five read back equal, ONE `flItems.notifyChangesApplied('Glyphbridge create font', <the package>, False)` (switch `_MARK_CHANGED`). Without `family` nothing is written or marked. `notes` holds what the person must be told (unsaved; the tab title and the FONTS panel lag, with the Font Info workaround of 910; with other fonts open, the first glyph (288) and keeping the window in front); the activity log prints one line and each note in the OUTPUT panel.
- Family check: printable ASCII, no edge space, none of `[](){}<>/%`, and a PostScript name (family without spaces + "-Regular") of at most 63 characters, so at most 55 characters without spaces. This corrects the approved "58 characters", which let the PostScript name reach 66. One check, `_family_name_error`, now serves both this route and the probe `/debug/tryfont?stage=construct_named`, whose own limit of 58 (since v0.142) is gone (the user's approval, the same day).
- Server: `create_font(family=None)`, needs listener 0.146; the same checks before anything is sent; `person_notes` and an instruction to relay every one; with a name, the offer to explain Font Info's Names page (2026-11-11). A font made but not confirmed is reported and counted as a change; an unknown outcome as an uncertain one.
- Tests: `stub_listener_tests.py` 3108 → 3206 lines (2302a–2308d; the probe's 2298c and 2298d now test 56 and 55 characters, 2298r and 2298s are new), `create_unicode_tests.py` 1222 → 1266 lines (36a–36z2, end to end through the real listener included); other output changed only in version lines. Mutation run: 19 of 19 caught (13 listener, 6 server). Not yet run live.

## Listener v0.145 (2026-11-12; server unchanged at v0.59)

**`/debug/tryfont?stage=construct_named&mark=yes`** (NM 912–913, [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k).
- After the four names read back equal, ONE `flItems.notifyChangesApplied('Glyphbridge test', <the package just made>, False)` on that package object, in the same request; `mark` is off by default and refused when neither empty nor `yes`. No mark when a name assignment failed, none without `flItems`; a mark error is reported in `mark.error` and the construct stays counted. Reason: 912 and 913 showed that this mark brings FontLab's save question back for a font named through the API, with one font open; with several open, which font it lands on is untested.
- Tests: 3095 → 3108 lines (2301a–m). Mutation run: 10 of 10 caught in the new switch, with a clean control run. Run live (914, one run): beside two other fonts only the new font was marked and asked to save.

## Listener v0.144 (2026-11-12; server unchanged at v0.59)

**`/debug/trynames?stage=title`** (NM 902–904, [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k).
- ONE `flPackage.title_name(True|False)` (`full=yes|no`, default yes), gated by `go=yes`, 3 per listener run, one font open; the reply holds the returned text and `elidedName` before and after. `stage=state` also reads `elidedName` (`elided_name`). Reason: a Full name typed in Font Info changed the tab's title (902) and API writes never did.
- Tests: 3078 → 3095 lines (2300a–q; `title` joins the stage lists and the counters). Mutation run: 10 of 10 caught in the new stage, with a clean control run. Run live (905, 908; three calls, one run each).

## Listener v0.143 (2026-11-11; server unchanged at v0.59)

**`/debug/trynames?stage=info_set`** (NM 879–880, [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k).
- ONE `flPackage.info.F = V` for F = `openTypeNamePreferredFamilyName` or `openTypeNamePreferredSubfamilyName`, with the value checks of `set`; 3 per listener run. Every `trynames` reply now also reads both (an `info` part, in `changed_readings` too). Refused before any call when the package has no usable `info` object.
- Tests: 3066 → 3078 lines (2299a–l; every state shows the `info` part). Mutation run: 35 of 35 caught in `trynames`, 9 of 9 in `construct_named`, each with a control run. Not yet run live.

## Listener v0.142 (2026-11-11; server unchanged at v0.59)

**`/debug/tryfont?stage=construct_named&family=F&go=yes`** (NM 878).
- ONE `flPackage()`, then in the same request the names Build Names gives: `tfn` = F, `ffn` = F + " Regular", `psn` = F without spaces + "-Regular", `sgn` = F, each read back. Shares the once-per-run limit of `construct`; the flag is set before the constructor runs. F: 1–58 printable ASCII characters, no edge space.
- Tests: 3047 → 3066 lines (2298a–q; the unknown-stage message of 726 changed). Mutation run: 9 of 9 caught, a control run matched. Live 878: all four names read back, but the tab and the FONTS panel showed the old names.

## Listener v0.141 (2026-11-11; server unchanged at v0.59)

**`trynames?stage=refresh` takes `which=applied|readed|added`** (NM 874–876): `flItems.notifyChangesApplied('Glyphbridge test', <flPackage>, False)`, `notifyPackageReaded(<flPackage>)`, `notifyPackageAdded(<flPackage>)`, 3 each per run.
- Tests: 3035 → 3047 lines (2297a–l). Mutation run: 30 of 30 caught, a control run matched. Live 874–876: `applied` turned the font's icon blue; none redrew the FONTS panel.

## Listener v0.140 (2026-11-11; server unchanged at v0.59)

**`trynames?stage=refresh` takes `which=model|properties|changed`** (NM 867–869): `flItems.notifyModelChanged()`, `flItems.notifyPropertiesChanged(<flPackage>)`, `flPackage.changed()`, 3 each per run.
- Tests: 3019 → 3035 lines (2296a–p). The static scan 2212 of `/debug/trynotify` ended at the next probe after it, which now includes `trynames` and its deliberate `changed()`: it ends where `trynames` begins. The fake package prints as `<TNPkg>`, not with a memory address. Mutation run: 27 of 27 caught, a control run matched. Live 867–869: none redrew the FONTS panel.

## Listener v0.139 (2026-11-11; server unchanged at v0.59)

**`/debug/trynames` gains two gated stages** (NM 864–866, [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k).
- `stage=store&go=yes`: ONE `flPackage.store_font_info(<the package's fgPackage>)`, refused before the call when `store_font_info` is missing or `fgPackage` is not a font object. `stage=legacy_set&field=familyName&value=V&go=yes`: ONE `font.info.familyName = V`, with the value checks of `set` and `read_back_equal` against the legacy field. 3 each per listener run; every name read before and after. An unknown stage now lists all five stages.
- Tests: `stub_listener_tests.py` 3000 → 3019 lines (2295a–s; the counter dictionary gained two keys; the static scan allows one `store_font_info` lookup and the two setters). Mutation run: 23 of 23 caught, a control run matched. Live 864–866.

## Listener v0.138 (2026-11-11; server unchanged at v0.59)

**`/debug/trynames?stage=refresh` takes `which=content|package|packages`** (NM 862, 863).
- `package`: ONE `flItems.notifyPackageUpdated(<package fgId>)`; `packages`: ONE `flItems.notifyPackagesUpdated()`, no argument; `content`, the default, as in 0.137. 3 per `which` and listener run, replacing the shared 6; an unknown `which` is refused before anything is called.
- Tests: 2984 → 3000 lines (2294a–p; the counter dictionary changed shape). Mutation run: 17 of 17 caught, a control run matched. Live 862, 863, 866.

## Listener v0.137 (2026-11-11; server unchanged at v0.59)

**New research probe `/debug/trynames`** (P0.4, a `create_font` that can be given a name; NM 851–861).
- `stage=state`, read only, no `go`: the package's `psn ffn tfn tsn sgn` and `fileName`, and the legacy `font.info` family, style, Full name and PostScript name. `stage=set&field=F&value=V&go=yes`: ONE assignment of one package name; 1–63 printable ASCII characters, no leading or trailing space, no space in `psn`; 10 per listener run. `stage=refresh&go=yes`: ONE `flItems.notifyPackageContentUpdated(<package fgId>)`, 6 per run. Exactly one font open (the gate of `/debug/trysync`); the counter is raised before the call.
- Tests: 2951 → 2984 lines (2292a–2293e). The probe's variable is named `notifier`, not `items`, because 2291v counts the product route's own call text. Mutation run: 12 of 12 caught, a control run matched (the first run without one compared unmasked output, [LESSONS.md](LESSONS.md)).

## Server v0.59 (2026-11-11; listener unchanged at v0.136)

**`get_glyph_sidebearings` no longer claims to show what FontLab's panel shows** (PB2 820, 827, [topics/reading.md](topics/reading.md) §8p).
- The description and the reply's `note` said the values are "exactly what FontLab's editor panel shows". They are FontLab's exact values; its editor panel and font grid bar show sidebearings rounded down to whole units (61.75 as 61, −38.25 as −39). Both texts now say so, and the description tells the agent to give the exact value and say that the panel shows it rounded down.
- Tests: `create_unicode_tests.py` stays at 1222 lines; 9t (the `note`) changed, the rest only in version lines. Text only, no new code path, so no mutation run. Live 829, 830: the reply carries the new note; the description in a Claude Code session after one restart was still the old one.

## Server v0.58 (2026-11-10; listener unchanged at v0.136)

**The `draw_path` texts state the export result** (EX 779–791, [topics/geometry.md](topics/geometry.md) §8g).
- `_OPEN_CONTOUR_INSTRUCTION`: no longer "has NOT been tested"; it now says that FontLab 8.9.5's export (TrueType and OpenType PS, default settings) dropped open contours without a warning, that a glyph made only of them came out empty, that they must be closed or turned into outlines first, and that other export settings were not tested.
- The `draw_path` description says the same in one sentence.
- Tests: `create_unicode_tests.py` stays at 1222 lines; 29d (the instruction) and 29zg (the description check, now "export drops them" and "old 'not been tested' gone") changed, the rest only in version lines. No new code path, so no mutation run. Live 800, 801: the reply carries the new text; the description in a Claude Code session after one restart was still the old one.

## Server v0.57 (2026-11-10; listener unchanged at v0.136)

**The icon note is retired, and a request that changed nothing no longer calls the panel stale** ([DECISIONS.md](DECISIONS.md)).
- `_ICON_MAY_LAG_KERNING = False` (749–753); the `set_kerning` description no longer mentions the icon's lag. The note's code stays and is tested with the switch on.
- Point (1) of a request that changed nothing: "The value was already set, so FontLab was not asked to refresh its KERNING panel." (746).
- Tests: `create_unicode_tests.py` 1217 → 1222 lines; other output changed only in the version lines, 34k and 35e. Mutation run: 15 of 15 caught. Live 748, 754.

## Listener v0.136 / server v0.56 (2026-11-10)

**A kerning write that changed an entry refreshes FontLab's KERNING panel** ([DECISIONS.md](DECISIONS.md), goal 8).
- **Listener:** `/kerning/set` makes one `flItems.notifyPackageContentUpdated(<package fgId>)` after the changed mark, on the package the write used, when at least one entry is known to have changed, also when the request stopped partway. An `fgId` that is not a plain number fitting a `uint` means no call and a reason. The reply gains `fontlab_panel_refresh` (`called`, `reason`, `call_error`). `_REFRESH_KERNING_PANEL = False` switches it off.
- **Server:** forwards the field, type-checked; point (1) of the instruction says FontLab was asked to refresh the panel when the call was made without error; the `set_kerning` description says so.
- Tests: `stub_listener_tests.py` 2924 → 2951 lines, `create_unicode_tests.py` 1204 → 1217; other output changed only in the version lines and the new field. Mutation run: 36 of 36 caught. Live 744–747, 749–753; the failure paths are stub-tested only.

## Listener v0.135 (2026-11-10; server unchanged at v0.55)

**`/debug/trynotify` can pass FontLab's small ids** (research for goal 8).
- `stage=ids` reads the object ids, `fgId` and `fgGlyphId`, and asks `findPackageId` and `isEqual`; `which=font_selected`; `id_from=object|fg` for the calls that take an id; a number that does not fit a `uint` is refused before any call.
- Tests: `stub_listener_tests.py` 2885 → 2924 lines; other output changed only in the version lines, the two new counters and the error wording. Mutation run: 34 of 34 caught, after one added case. Live 736–743.

## Server v0.55 (2026-11-10; listener unchanged at v0.134)

**The icon note, and a truthful reply when nothing changed** ([DECISIONS.md](DECISIONS.md)).
- When a kerning write was marked, the `set_kerning` instruction gains point (4): the changed icon may stay dark until the mouse moves near the font's title, and a dark icon does not mean the change failed; said once per package. `_ICON_MAY_LAG_KERNING = False` retires it.
- When no entry changed, point (2) says the request adds nothing that needs saving, instead of the warning about closing (720).
- Tests: `create_unicode_tests.py` 1192 → 1204 lines, part 33 extended; other output changed only in the version lines and in 33y. Mutation run: 19 of 19 caught. Live 727, 728.

## Listener v0.134 / server v0.54 (2026-11-10)

**A kerning write that changed an entry marks the font as changed** ([DECISIONS.md](DECISIONS.md), S1).
- **Listener:** `/kerning/set` makes one `flItems.notifyChangesApplied("Glyphbridge kerning", <flGlyph>, False)` when at least one entry is known to have changed, also when the request stopped partway. Target: the left glyph of the first changed pair, then its right glyph, then the sides of later changed pairs, never `.notdef`, at most 20 tried; `via_glyph` names it. The loop is shared with the delete's mark (`_mark_through_first`).
- **Server:** `set_kerning` forwards `fontlab_changed_mark`; point (2) of its instruction says FontLab was told when the mark was made, and keeps the old warning otherwise; `save_question_note` follows as for other writes.
- Tests: `stub_listener_tests.py` 2861 → 2885 lines, `create_unicode_tests.py` 1181 → 1192; other output changed only in the version lines and in the new field of the `/kerning/set` replies. Mutation run: 23 of 23 caught. Live 718–721; the fallback to other glyphs, a failed notification and the cap of 20 are stub-tested only.

## Listener v0.133 / server v0.53 (2026-11-09)

**A verified delete marks the font as changed** ([DECISIONS.md](DECISIONS.md), S1).
- **Listener:** after a delete confirmed by the re-read: one `flItems.notifyChangesApplied("Glyphbridge delete", <flGlyph>, False)` on the first surviving glyph that is not `.notdef` and has a modern active layer, at most 20 tried, reported in `fontlab_changed_mark` with `via_glyph`. With none to notify: `called` false and the reason. `_MARK_CHANGED = False` switches it off.
- **Server:** forwards `via_glyph`, type-checked; `save_question_note` follows as for other writes; the `delete_glyph` description explains it.
- Tests: `stub_listener_tests.py` 2843 → 2861 lines, part 33 in `create_unicode_tests.py` 1176 → 1181; other output changed only in the version lines. Mutation run: 14 of 14 caught. Live 688–691c; a failed notification and the cap of 20 are stub-tested only.

## Server v0.52 (2026-11-09; listener unchanged at v0.132)

**`save_question_note` no longer warns wrongly** ([DECISIONS.md](DECISIONS.md), S1).
- **Server:** the note comes only when the mark call was not made or failed. `glyph_has_changes` stays in `fontlab_changed_mark` as information; it read false while the mark worked (668).
- Tests: line counts unchanged; `create_unicode_tests.py` output changed in the version lines and in 33d, 33e, 33j, which lost the note. Mutation run: 6 of 6 caught. Live 670–682: no note on 20 marks; `glyph_has_changes` never read false there; it did in the setup of 688, with no note.

## Listener v0.132 / server v0.51 (2026-11-09)

**Tool writes mark the font as changed** ([DECISIONS.md](DECISIONS.md), S1).
- **Listener:** after a verified, synced write of `create_glyph` with its layer, width, sidebearings, `draw_polygon`, `draw_path` or Unicode: one `flItems.notifyChangesApplied(title, <flGlyph>, False)`, reported in `fontlab_changed_mark` (`called`, `reason`, `call_error`, `glyph_has_changes`). A write that changed nothing, was not confirmed, is not synced or has no layer is not marked and says why. Kerning writes and deletes are not marked. `_MARK_CHANGED = False` switches it off.
- **Server:** forwards the field, type-checked, and adds `save_question_note` to a real change that was not confirmed marked. **Known fault:** `glyph_has_changes` read false while the mark worked (668), so the note can warn wrongly.
- Tests: `stub_listener_tests.py` 2806 → 2843 lines, part 33 in `create_unicode_tests.py` (1159 → 1176); other output changed only in the version lines and the reasons on `create_glyph` without a layer. Mutation run: 33 of 33 caught, after one added case. Live: `create_glyph` only (668, 669); the other writes, the error paths and the skip paths are stub-tested only.

## Listener v0.131 (2026-11-09; server unchanged at v0.50)

**A research probe for S1** ([WATCH-POINTS.md](WATCH-POINTS.md)); no product route changed.
- **Listener:** gated `/debug/trynotify`: `stage=state` reads `isChanged`, `hasChanges`, `hasHistoryStates`, `currentHistoryState()` and `initialHistoryState()` of the package, workspace and one glyph; `stage=call&which=...` makes ONE call from a fixed list of `flItems` notifications, on the class or on `flItems.instance()`. One font open, `go=yes`, 20 state reads and 3 per call in a listener run.
- Tests: `stub_listener_tests.py` 2757 → 2806 lines; other output changed only in the version lines. Mutation run: 25 of 25 caught. Live 659b–667: only `which=changes_applied` on the class was called; the other four calls, `on=instance` and the error paths are stub-tested only.

## Listener v0.130 / server v0.50 (2026-11-09)

**A component is checked on its own and against its source** ([topics/reading.md](topics/reading.md), [DECISIONS.md](DECISIONS.md)).
- **Listener:** for a component only, each outline read adds `ink_box` (one `shape.inkBox()`) and `source_ink_box` (one `layer.inkBox()` on the source's active layer, when its name equals `component_layer`). At most 20 elements; an unreadable box is `{"error"}`.
- **Server:** an outer box that fits with and without the transforms is settled element by element (`element_boxes_checked`). Each component says `source_in_step`: true, false or `"unknown"`. False makes the read `unverified`, gives both boxes and an `agent_instruction`. Both checks cover plain offsets only. `set_glyph_sidebearings` has a `component_note`. An older listener gets the previous behaviour.
- Tests: part 32 in `create_unicode_tests.py` (1109 → 1159 lines); other output changed only in the version lines, the list of `inkBox` calls (1675) and the sidebearing reply. Mutation run: 40 of 40 caught, after three added cases. Live 651–656; the error paths and a vertical offset are stub-tested only.

## Listener v0.129 (2026-11-09; server unchanged at v0.49)

**A research route, `/debug/tryshapebox`** (read only, gated, P1.1; [topics/reading.md](topics/reading.md)).
- **`stage=shapebox`:** one `shape.inkBox()` per element of the modern active layer, used only when `layer.shapes` is a real list of at most 20. **`stage=dependencies`:** one `flGlyph.isUnbindedDependecies()`.
- Both need `go=yes` and exactly one font open, at most 12 per stage and listener run, counted before the call. Layer counts and advance width are compared before and after (`side_effect_detected`). Never called: `bindDependencies`, `update`, `changed`, `resetInkBox`, `font.update()`, save.
- Tests: cases 2130–2168 in `stub_listener_tests.py` (2714 → 2757 lines); other output changed only in the version lines and the list of `inkBox` calls (1675). Mutation run: 23 of 23 caught, after one mutation that had changed a comment was aimed at the call. Live 644–650.

## Listener v0.128 / server v0.49 (2026-11-09)

**`get_glyph_outline` says when a glyph holds a component** (gap found in 607; [topics/reading.md](topics/reading.md)).
- **Listener:** `_describe_modern_glyph` reads `shape.shapeData.componentGlyph` and `componentLayer`, for a component only; a failed read gives `component_error`, never an empty name.
- **Server, modern-first branch:** each element gains `is_component` (`"unknown"` when the flag could not be read) and, for a component, `component_glyph` and `component_layer`; one note per component names its source. When the element list cannot be used, the note says that whether the glyph holds components is unknown.
- **Wording:** the `get_glyph_outline` and `draw_polygon` descriptions are corrected; a description no longer prints `-0` for an offset.
- Tests: part 31 in `create_unicode_tests.py` (1082 → 1109 lines); other output changed only in the version lines and the two "unknown" notes. Mutation run: 23 of 23 caught, after one added case. Live 624–626 afterwards, one master; the failure paths and the `-0` fix are stub-tested only.

## Listener v0.127 / server v0.48 (2026-11-09)

**`create_glyph` gives the new glyph its layer** (the Add Component crash, [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §9; live 612–619).
- **Listener `POST /glyph/create`:** after the glyph is known to exist, in a font with exactly one master, `_create_glyph_layer` creates the layer with the existing `_modern_edit_target(name, create_layer=True)` and syncs it with `_guard_mark`. The reply adds `layer_created` and `layer_name_source`. When no layer can be made (several masters, an unreadable master count, a layer name that cannot be determined, any error), the glyph is still created and the reply adds `layer_note` with the reason.
- **Server `create_glyph`:** forwards these fields, type-checked; with `layer_note` the `agent_instruction` tells the agent to warn the person not to use Add Component on that glyph. The tool description says so. The `draw_polygon` description, which still says a new glyph has no layer, was left unchanged.
- Tests: server and listener part 30 in `create_unicode_tests.py` (1054 → 1082 lines); other output changed only in the version lines. Mutation run: 20 of 20 caught. Live 620–623 afterwards, one master; `layer_note` is stub-tested only.

## Listener v0.126 / server v0.47 (2026-11-04)

**`draw_path` draws open contours** (P2.1; research 586–594, [topics/geometry.md](topics/geometry.md) §8g).
- **The request:** a contour is a point list (closed, as before) or `{"points": [...], "closed": false}` (open, from the first point to the last); `{"points": [...]}` or `"closed": true` means closed. Open and closed contours can be mixed in one call, still one shape into an empty glyph.
- **Rules for an open contour**, checked by the server before sending and again by the listener: 2 to 500 points, at least 2 different positions after rounding; no `c1` / `c2` on the first point (no closing segment); no smooth first or last point (one neighbour). Inner smooth points use the existing check, without wrapping round.
- **Listener `POST /glyph/path`:** builds an open contour with `_path_build_contour(…, closed=False)`; its `closed` flag must read False detached and on the layer, otherwise nothing is reported as drawn; the reply lists `open_contours`; the activity log line counts them ("1 open"). Closed contours are unchanged.
- **Server `draw_path`:** needs listener 0.126 only when a contour is open (refused before sending otherwise); the reply adds `closed` per contour, `open_contours_note`, and an `agent_instruction` to tell the person that open contours have no fill and that what FontLab does with them on export is untested. The tool's input schema takes both contour forms.
- Tests: listener 2090–2122 (2676 → 2714 lines), server 29a–29zz (1018 → 1054); other output changed only in the version lines and the `draw_path` signature (13zf). Mutation run: 17 of 17 killed, both unmutated controls passed. Not yet live-checked at release; live 595–603 afterwards.

## Listener v0.125 (2026-11-04; server unchanged at 0.46)

**`/debug/tryopen`, a gated research probe for P2.1 (drawing open contours).** Does a contour that is never closed stay open once attached?
- `stage=detached|draw`, `name=ocp…`, `kind=line|curve`, `go=yes`. Fixed shapes: `line` the open V of 581, `curve` the open arch of 583. The one-font gate of `/debug/trysync`; at most 6 calls per listener run, counted before anything is created or built.
- `detached` builds the contour with `_path_build_contour(…, closed=False)` and reads it back; the glyph is not touched. `draw` builds it the same way into a glyph whose modern layer is known to be empty (a missing layer is created, as `draw_path` does), attaches it only when the detached contour reads `closed` false with the expected positions and node kinds, reads the layer back (`layer_closed`, `layer_mismatches`, `drawn`), and marks the glyph for the guard. Smooth flags are reported, not required.
- `_path_build_contour` gains `closed=True` (default); `draw_path` and `draw_polygon` are unchanged (stub 2081, 2082).
- Tests: listener 2050–2085 (2636 → 2676 lines); other output changed only in the version lines. Mutation run: 13 of 13 killed, the unmutated control passed. Never run in FontLab at release; live 586–594 afterwards.

## Server v0.46 (2026-11-04; listener unchanged at 0.124)

**Open contours, read** (P1.4; live 581: an open straight V, `verified`; 583: an open cubic arch, `unverified` in 0.45).
- **`_contour_pieces`** parses an open contour (`closed` false) from its first node to its last, with no closing segment; both ends must be on-curve, otherwise the reply says "an open contour whose first or last node is not on-curve". A `closed` flag that is not a bool is named as such. So an open curve gets its exact extents and can be `verified` against FontLab's margins and `inkBox()`.
- **`svg_path`** for open contours, straight and curved, without the closing Z (`_svg_path(…, closed=False)`).
- **Direction:** `direction_computed` is "not applicable (open contour)" and `flag_follows_known_inversion` null; FontLab's own flag stays listed.
- **A note** names the open contours; the `get_glyph_outline` description says how they are read.
- Closed contours are unchanged; the legacy route's "assumed closed" note is unchanged.
- Tests: server 28a–28z (2636 + 58 + 90 + 1018 lines); 14n (an open inner contour, margins of another shape) now reads "does not match" instead of "not computed". Mutation run: 11 of 11 killed, the unmutated control passed.
- Not yet live-checked at release; live 579–585 afterwards.

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
