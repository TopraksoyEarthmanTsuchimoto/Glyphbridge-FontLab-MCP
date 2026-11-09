# Scenario checklist (open rows)

Goal: an agent reads *any* glyph accurately and writes only what it can verify. A scenario counts as supported only when the tool's answer matches FontLab's own numbers. Until then the tool must say `unverified`, never guess.

This list holds the **open** scenarios only. Row numbers are those of the v11 matrix: the full matrix, including every DONE row and its evidence, is [archive/scenarios-checklist-v11.md](archive/scenarios-checklist-v11.md). When a row is proven, record the evidence in the topic file, delete the row here, and log the date in [archive/CHECKLIST-closed-rows.md](archive/CHECKLIST-closed-rows.md).

## How to test a scenario

1. Build a small reference glyph in a disposable font (Font > New Glyph… > Create Blank).
2. In FontLab, note 2–3 node readouts, the transform bar values and LSB/RSB.
3. Run `.\venv\Scripts\python.exe glyphbridge_mcp_server.py --check --outline NAME` and compare.
4. Add the captured case to `tests/` and record the result. Do not save after a live write test unless that save test was agreed ([DECISIONS.md](DECISIONS.md)); otherwise quit FontLab without saving.

## Kerning

Reading: none open, the K-series is done ([LIVE-TESTS.md](LIVE-TESTS.md)).

| # | Scenario | Status |
|---|---|---|
| 81 | Write a kerning pair (KW) | PARTLY: a glyph : glyph pair set, re-read, applied and saved (544–560); the KERNING panel lists it only after save and reopen (545–560); before 0.134 closing asked nothing and lost the pair (561, 562), since 0.134 / 0.54 the write is marked and FontLab asks (718–721); Edit > Undo does not cover it (563); `set` accepts the tuple and the `flags` form (564); `set_kerning` live-checked (565–574): glyph : glyph pairs, whole units, refusals, the panel after a font switch; server 0.45 live-checked (575, 576); saved and reopened (577); open: the pair in the panel at once (goal 8), an exception over a class on a real font, writes with several saved fonts, multi-master ([topics/kerning.md](topics/kerning.md) §13) |

## Sync, fonts and agent level

| # | Scenario | Status |
|---|---|---|
| 53 | Auto sync not yet proven for: multi-layer (11), quadratic (43), big glyphs (42) | PARTLY |
| 57 | No font open: every route answers `open: false` (`CountFonts()`, listener 0.105) | PARTLY: every read route proven, after closing the only font (227) and in a freshly started FontLab (244); writes with no font open: one create refused (227), the rest stub-only (T12) |
| 63 | Several fonts open: which one the tools address | PARTLY: with two fonts every tool follows the font in front and every reply names it (262–316); evidence in [topics/fonts-and-sync.md](topics/fonts-and-sync.md). Open: two unsaved fonts with the same name (a Font Info rename does not produce it, 322–324), three fonts (`list_glyphs`, `get_glyph_width` and every write but `draw_path` proven, 317–331; `get_kerning` only its refusal of an unsaved font in front, 268; the other reads untested), a switch during one call |
| 84 | FontLab's changed icon after a kerning write | Not reliably immediate (719, 722–726); retest on each new FontLab version and when the marking code changes; five runs in a row blue at once retire the note ([DECISIONS.md](DECISIONS.md)) |
| 62 | Modern glyph creation without `font.update()` | TODO, low priority (T6) |
| 22 | Layer-name derivation when glyphs disagree, or when none has a layer | stub-tested only |

## Reading gaps

| # | Scenario | Status |
|---|---|---|
| 8, 49 | Component (composite) glyphs | PARTLY (P1.1): one component, one master, read `verified`, labelled with its source since 0.128 / 0.49 (606–611, 624–626, [topics/reading.md](topics/reading.md)); two components in a glyph and one source shared by two glyphs (630, 635, 636), an accent inside its base `verified` element by element since 0.130 / 0.50 (652), one behind its source `unverified` (651, 653); open: other masters |
| 9 | Element reference | TODO |
| 10 | Component with its own transform | PARTLY: offset (608) and horizontal scale with offset (611, 656); rotation, slant, mirroring, vertical scale TODO |
| 11 | Multiple layers or masters | TODO (T7) |
| 12c, 12d, 12e | Rotation, mirroring, combined transform on real data | TODO (T11), simulated only |
| 13 | Two elements with different transforms | PARTLY: two components, one with an offset and one without (631, 633, 636); two different non-identity transforms TODO |
| 14 | Power Brush glyph with an element transform | PARTLY: an offset (dx −142, set by `setSB`) read `verified`, FontLab's Elements panel Δ=(-142,0) (T4, 145g, 260), and on the modern route (515); scale and rotation not tested |
| 6, 50 | Open contours, read | PARTLY: server 0.46 reads them from the modern layer, live `verified` for a straight and a cubic open contour drawn in FontLab's GUI (584, 585; [topics/reading.md](topics/reading.md) §8e); open: a quadratic open contour (stub only), the legacy route |
| 15, 40, 51 | A real designed letter (Arial `O`, `S`, `g`, `eacute`), read-only | TODO (P1.5), under about 150 nodes each |
| 4 | Back To PS Curves round trip | TODO |
| 5 | The "To Line" route itself (straight polygons already read back) | PARTLY |
| 16 | Other empty glyphs (e.g. `space`): zero layers like `.notdef`? | OPEN |
| 18 | `.notdef` remainders: explicit `check_notdef` through Claude, a drawn `.notdef`, the `missing` dialog, waits of 90–120 s and over 120 s | PARTLY |
| 20 | `create_glyph('uni00e8')` shows the lowercase-hex warning in its v0.17 wording | TODO (T10) |

## Writing gaps

| # | Scenario | Status |
|---|---|---|
| 28 | Draw an open contour | PARTLY: `draw_path` with `"closed": false` (listener 0.126 / server 0.47): open straight and cubic contours, and an open one with a closed one, drawn and read `verified`; refusals change nothing (595–603; research 586–594; [topics/geometry.md](topics/geometry.md) §8g); open: quadratic, what FontLab does with them on export |
| 82 | `create_glyph` in a font with components, then Add Component on the new glyph | PARTLY: FontLab crashes on a glyph with no layer (612–618); fixed for one master in 0.127 / 0.48 (620, one run); `layer_note` seen live (691a); open: multi-master ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §9) |
| 83 | Edit a component's source: do the glyphs using it follow? | PARTLY: GUI edits yes (639, 643, 652, 655); `set_glyph_sidebearings` one of five (638, 638b, 640, 648, 653); a missed glyph reads `unverified` since 0.130 / 0.50 (651, 653; [topics/reading.md](topics/reading.md)); placing a component by tool: not built |
| 30 | Several separate shapes in one glyph | TODO (P2.2) |
| 31 | Draw into, or edit, an existing outline | not supported; decide the behaviour first (P2.2) |
| 43 | `draw_path` in a quadratic font | TODO, low (T8) |
| 44 | `set_glyph_width` with an existing but inactive layer | TODO (T10), stub-tested |
| 19 | A write that times out while a dialog is open: applied after OK? | TODO (T10) |
| 38 | `draw_polygon` rounding report, live | TODO |
| 39 | Smooth gate leftovers: very short handles, zero-length handle on a non-smooth node | optional (P2.5) |
| 36 | The layer guard's own refusal path | stub-only. Accepted: not worth more live effort |

## Last block (by the user's decision)

| # | Scenario | Status |
|---|---|---|
| 17, 42, 64 | Large glyphs: 1980-node request, 2001-node refusal, read 1000+ nodes, time of `Update` against the 5 s timeout | POSTPONED |

Rows closed since v11: [archive/CHECKLIST-closed-rows.md](archive/CHECKLIST-closed-rows.md).
