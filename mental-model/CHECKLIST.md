# Scenario checklist (open rows)

Goal: an agent reads *any* glyph accurately and writes only what it can verify. A scenario counts as supported only when the tool's answer matches FontLab's own numbers. Until then the tool must say `unverified`, never guess.

This list holds the **open** scenarios only. Row numbers are those of the v11 matrix: the full matrix, including every DONE row and its evidence, is [archive/scenarios-checklist-v11.md](archive/scenarios-checklist-v11.md). When a row is proven, record the evidence in the topic file, delete the row here, and log the date in [CURRENT-STATUS.md](CURRENT-STATUS.md).

## How to test a scenario

1. Build a small reference glyph in a disposable font (Font > New Glyph… > Create Blank).
2. In FontLab, note 2–3 node readouts, the transform bar values and LSB/RSB.
3. Run `.\venv\Scripts\python.exe glyphbridge_mcp_server.py --check --outline NAME` and compare.
4. Add the captured case to `tests/` and record the result. Never save after a live write test; quit FontLab without saving.

## Kerning (priority, details in [LIVE-TESTS.md](LIVE-TESTS.md))

| # | Scenario | Status |
|---|---|---|
| 73a | Defect A: `get_kerning` misses kerning made in FontLab's GUI (reads the legacy table) | TODO (P0.8), found by K9 |
| 73b | Defect B: an exception on a glyph whose name is also a class name reads as the class value | TODO (P0.8), right side proven, left side untested; fix path found (exact glyph pair via (name, False) tuples, 186), design open |
| 74 | K10: `font.kerning` versus kerning applied to text | TODO, high value |
| 75 | K11: GPOS / contextual kerning, names-only probe | TODO |
| 76 | K12: new font, test font, two fonts | PARTLY: (a) `table_size` 0 proven (168) |
| 77 | K13: no font open | TODO |
| 78 | K14: timings at 250 and 2000 pairs | TODO |
| 80 | K16: encoding end to end | TODO |
| 79 | K15: transport limit (about 1 MB) | POSTPONED to the last block |

## Sync, fonts and agent level

| # | Scenario | Status |
|---|---|---|
| 59 | T3: write while the glyph's editor tab is open | TODO, highest value |
| 60 | T4: width and sidebearings on an existing glyph with legacy layers | TODO |
| 53 | Auto sync not yet proven for: an open editor (59), existing glyphs (60), multi-layer (11), quadratic (43), big glyphs (42), after save (32) | PARTLY |
| 21, 52, 61 | T2: one request with several writes, then ONE bold save reminder from `finish_changes`; none after a pure read | TODO |
| 57 | No font open: every route answers `open: false` (`CountFonts()`). Only the kerning route does this today | TODO (P0.2, T12) |
| 63 | Two fonts open: which one the tools address | TODO (T5) |
| 62 | Modern glyph creation without `font.update()` | TODO, low priority (T6) |
| 22 | Layer-name derivation when glyphs disagree, or when none has a layer | stub-tested only |
| 32 | Save and reopen after API-drawn geometry | DEFERRED by the user (T9) |

## Reading gaps

| # | Scenario | Status |
|---|---|---|
| 8, 49 | Component (composite) glyphs | TODO (P1.1): names-only probe first; today the reader declines them and says so |
| 9 | Element reference | TODO |
| 10 | Component with its own transform | TODO |
| 11 | Multiple layers or masters | TODO (T7) |
| 12c, 12d, 12e | Rotation, mirroring, combined transform on real data | TODO (T11), simulated only |
| 13 | Two elements with different transforms | TODO |
| 14 | Power Brush glyph with an element transform | TODO |
| 6, 50 | Open contours, read | TODO (P1.4); assumed closed today |
| 15, 40, 51 | A real designed letter (Arial `O`, `S`, `g`, `eacute`), read-only | TODO (P1.5), under about 150 nodes each |
| 4 | Back To PS Curves round trip | TODO |
| 5 | The "To Line" route itself (straight polygons already read back) | PARTLY |
| 16 | Other empty glyphs (e.g. `space`): zero layers like `.notdef`? | OPEN |
| 18 | `.notdef` remainders: explicit `check_notdef` through Claude, a drawn `.notdef`, the `missing` dialog, waits of 90–120 s and over 120 s | PARTLY |
| 20 | `create_glyph('uni00e8')` shows the lowercase-hex warning in its v0.17 wording | TODO (T10) |

## Writing gaps

| # | Scenario | Status |
|---|---|---|
| 28 | Draw an open contour | TODO (P2.1) |
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

Closed on 2026-11-01: row 33 (tests refreshed and passing on the user's machine), row 65 (K1 deployment check), row 66 (K2 listener route), row 67 (K3 POST equals GET), row 68 (K4 three pairs through the agent), row 69 (K5 `text` mode against the KERNING panel), row 70 (K6 special characters in `text`), row 71 (K7 error cases), row 72 (K8 approval flow at 250 / 251 / 324 pairs), row 73 (K9: the exception wins over the class value when names are unambiguous).
