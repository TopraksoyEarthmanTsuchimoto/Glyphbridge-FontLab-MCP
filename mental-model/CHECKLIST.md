# Scenario checklist (open rows)

Goal: an agent reads *any* glyph accurately and writes only what it can verify. A scenario counts as supported only when the tool's answer matches FontLab's own numbers. Until then the tool must say `unverified`, never guess.

This list holds the **open** scenarios only. Row numbers are those of the v11 matrix: the full matrix, including every DONE row and its evidence, is [archive/scenarios-checklist-v11.md](archive/scenarios-checklist-v11.md). When a row is proven, record the evidence in the topic file, delete the row here, and log the date in [archive/CHECKLIST-closed-rows.md](archive/CHECKLIST-closed-rows.md).

Status words: TODO, not started; PARTLY, some cases proven live and the rest named; stub-only, tested without FontLab only; optional and POSTPONED, by the user's decision. New rows since v11 are numbered from 81.

## How to test a scenario

1. Build a small reference glyph in a disposable font (Font > New Glyph… > Create Blank).
2. In FontLab, note 2–3 node readouts, the transform bar values and LSB/RSB.
3. Run `.\venv\Scripts\python.exe glyphbridge_mcp_server.py --check --outline NAME` and compare.
4. Add the captured case to `tests/` and record the result. Do not save after a live write test unless that save test was agreed ([DECISIONS.md](DECISIONS.md)); otherwise quit FontLab without saving.

## Kerning

Reading: none open, the K-series is done ([LIVE-TESTS.md](LIVE-TESTS.md)).

| # | Scenario | Status |
|---|---|---|
| 81 | Write a kerning pair (KW) | PARTLY: glyph : glyph pairs set, re-read and saved (544–577); marked, so FontLab asks on close, since 0.134 / 0.54 (718–721); shown in the KERNING panel at once since 0.136 / 0.56 (738–748); Edit > Undo does not cover it (563). Open: the panel refresh on a font with thousands of pairs (untimed), an exception over a class on a real font, writes with several saved fonts, multi-master ([topics/kerning.md](topics/kerning.md) §13, §14) |
| 86 | Remove glyph : glyph kerning pairs (`remove_kerning`) | PARTLY: the research probe removed a pair in both forms and an exception over a class (KD 1381–1390, KDC 1391–1397); the product tool (listener 0.192 / server 0.76) live RK 1398–1402: an exception over a class with its class value again, two no-entry cases, the panel at once. Open: the save question for a removal alone, Edit > Undo, other masters and several fonts ([topics/kerning.md](topics/kerning.md) §16) |
| 87 | Write and remove class kerning entries | PARTLY: by probe (listener 0.193), each kind set, applied on screen, and removed (CW 1409–1417); the product tools (0.194 / 0.78) live CK 1420–1432a. Open: the mark for a class write alone, Edit > Undo, other masters, several fonts ([topics/kerning.md](topics/kerning.md) §17) |
| 88 | Rename and remove kerning groups (`rename_kerning_group`, `remove_kerning_group`) | PARTLY: by probe (listener 0.199, GE–GK 1505–1545); the product tools (0.200 / 0.82) live GT 1546–1576: renames, removals with `keep` and `delete`, a No, the refusals, the panels at once. Open: the save question for a group edit alone (Demo mode), Edit > Undo, a Kerning both group, other masters, a saved font beside others, a removal answered after the client's 60 s limit ([topics/kerning.md](topics/kerning.md) §19) |

## Sync, fonts and agent level

| # | Scenario | Status |
|---|---|---|
| 53 | Auto sync not yet proven for: multi-layer (11), quadratic (43), big glyphs (42) | PARTLY |
| 57 | No font open: every route answers `open: false` (`CountFonts()`, listener 0.105) | PARTLY: every read route proven, after closing the only font (227) and in a freshly started FontLab (244); writes with no font open: one create refused (227), the rest stub-only (T12) |
| 63 | Several fonts open: which one the tools address | PARTLY: with two fonts every tool but `move_nodes` follows the font in front, and every reply names it; a new font's first glyph gets its layer beside another font since 0.150 (evidence and the list: [topics/fonts-and-sync.md](topics/fonts-and-sync.md)). Open: two unsaved fonts with the same name (322–324, 832–835); with three fonts, `draw_path`, the later tools but `create_font`, `get_kerning` and the reads other than `list_glyphs` and `get_glyph_width` (317–331); a switch during one call; `construct_named&mark=yes` beside two fonts marked only the new font (914) |
| 62 | Modern glyph creation without `font.update()` | TODO, low priority (T6) |
| 22 | Layer-name derivation when glyphs disagree, or when none has a layer | stub-only |

## Reading gaps

| # | Scenario | Status |
|---|---|---|
| 8, 49 | Component (composite) glyphs | PARTLY (P1.1), one master: one or two components and a shared source read correctly (606–636), labelled with the source since 0.128 / 0.49; an accent inside its base `verified` element by element and one behind its source `unverified` since 0.130 / 0.50 (651–653). Open: other masters ([topics/reading.md](topics/reading.md)) |
| 9 | Element reference | TODO |
| 10 | Component with its own transform | PARTLY: offset (608) and horizontal scale with offset (611, 656); rotation 90° and 30°, a rectangle and a curve (768–771); slant, mirroring, vertical scale TODO |
| 11 | Multiple layers or masters | TODO (T7) |
| 12c, 12d, 12e | Rotation, mirroring, combined transform on real data | PARTLY: rotation of components `verified` (768–771); mirroring and a combined transform TODO (T11), simulated only |
| 13 | Two elements with different transforms | PARTLY: two components, one with an offset and one without (631, 633, 636), one rotated and one not (771); two different non-identity transforms TODO |
| 14 | Power Brush glyph with an element transform | PARTLY: an offset (dx −142, set by `setSB`) read `verified`, FontLab's Elements panel Δ=(-142,0) (T4, 145g, 260), and on the modern route (515); scale and rotation not tested |
| 6, 50 | Open contours, read | PARTLY: server 0.46 reads them from the modern layer, live `verified` for a straight and a cubic open contour drawn in FontLab's GUI (584, 585; [topics/reading.md](topics/reading.md) §8e); open: a quadratic open contour (stub only), the legacy route |
| 15, 40, 51 | A real designed letter (Arial `O`, `S`, `g`, `eacute`), read-only | TODO (P1.5), under about 150 nodes each |
| 4 | Back To PS Curves round trip | TODO |
| 5 | The "To Line" route itself (straight polygons already read back) | PARTLY |
| 16 | Other empty glyphs (e.g. `space`): zero layers like `.notdef`? | PARTLY: Arial's `space` has one empty layer (`Regular`, 0 nodes), unlike the layerless `.notdef` of a File > New Font font; API and Layers panel agree (1405–1408, one run). A glyph made with Font > New Glyph… > Create Blank has a modern layer, width 500 (1471–1473, one run). Open: other imported fonts |
| 18 | `.notdef` remainders: explicit `check_notdef` through Claude, a drawn `.notdef`, a missing `.notdef` | PARTLY: a drawn `.notdef`: `draw_path`, 3 contours, layer created, verified (926, one run); `check_notdef` through Claude Code (SD 1602). Open: a missing `.notdef`, not run |

## Writing gaps

| # | Scenario | Status |
|---|---|---|
| 28 | Draw an open contour | PARTLY: `draw_path` with `"closed": false` (listener 0.126 / server 0.47) draws open straight and cubic contours, alone or with closed ones, `verified` (586–603); unchanged after a save and reopen (755–764); FontLab's export drops them silently (779–791). Open: quadratic, other export settings ([topics/geometry.md](topics/geometry.md) §8g) |
| 82 | `create_glyph` in a font with components, then Add Component on the new glyph | PARTLY: FontLab crashes on a glyph with no layer (612–618); fixed for one master in 0.127 / 0.48 (620, 767: two runs); `layer_note` seen live (691a); open: multi-master ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §9) |
| 83 | Edit a component's source: do the glyphs using it follow? | PARTLY: GUI edits yes (639, 643, 652, 655); `set_glyph_sidebearings` one of five (638, 638b, 640, 648, 653); a missed glyph reads `unverified` since 0.130 / 0.50 (651, 653; [topics/reading.md](topics/reading.md)). Open: whether the other tool edits of the source reach it (`move_nodes`, drawing) |
| 85 | Place and remove components by tool (P2.7) | PARTLY, one master: `add_component` into an empty and a non-empty target, single and list forms, and `remove_component` are live-proven (AC, AC2, RC, TL, NB–NB3; [WHAT-WORKS.md](WHAT-WORKS.md)). Open: its auto-layer refusal live, its restore after a failure, other transforms, other masters; two recipe-built components became contours unexplained (1059) ([topics/reading.md](topics/reading.md)) |
| 30 | Several separate shapes in one glyph | TODO (P2.2); `move_nodes` refuses them (stub only); FontLab's Rectangle tool made a second contour, not a shape (1022a) |
| 31 | Draw into, or edit, an existing outline | PARTLY: `move_nodes` (0.154 / 0.64) moves nodes and control points `verified`, refuses a lone smooth node and a component (1016–1022); Edit > Undo does not revert it (1023). Open: adding, removing and redrawing contours, Power Brush glyphs, several shapes ([topics/geometry.md](topics/geometry.md)) |
| 43 | `draw_path` in a quadratic font | TODO, low (T8) |
| 44 | `set_glyph_width` with an existing but inactive layer | TODO (T10), stub-tested |
| 39 | Smooth gate leftovers: very short handles, zero-length handle on a non-smooth node | optional (P2.5) |

## Last block (by the user's decision)

| # | Scenario | Status |
|---|---|---|
| 17, 42, 64 | Large glyphs: 1980-node request, 2001-node refusal, read 1000+ nodes, time of `Update` against the 5 s timeout | POSTPONED |

Rows closed since v11: [archive/CHECKLIST-closed-rows.md](archive/CHECKLIST-closed-rows.md).
