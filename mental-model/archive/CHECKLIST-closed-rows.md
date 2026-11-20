# Closed checklist rows

Rows closed since the v11 matrix, moved from [CHECKLIST.md](../CHECKLIST.md) on 2026-11-06, newest first. Each row's scenario is in [scenarios-checklist-v11.md](scenarios-checklist-v11.md); the evidence is in the topic files and [LIVE-TESTS.md](../LIVE-TESTS.md). When a row is closed, add its date, number and tests here.

Closed on 2026-11-20: row 36 (the layer guard's own refusal path; stub-only, accepted as not worth more live effort, closed by the user's choice; no live test).

Trimmed on 2026-11-20 (still open in [CHECKLIST.md](../CHECKLIST.md), cut there to their status, open items and a link to the evidence, approved by the user): rows 63 and 85 as they stood, unchanged except for the link paths.

| # | Scenario | Status |
|---|---|---|
| 63 | Several fonts open: which one the tools address | PARTLY: with two fonts every tool but `move_nodes` follows the font in front, and every reply names it (262–316, 747, 916, 917, 1091–1095, 1264a–1264b; the list: [PROJECT.md](../PROJECT.md) Scope); a new font's first glyph gets its layer beside another font since 0.150 (933–935). Open: two unsaved fonts with the same name (a Font Info rename does not produce it, 322–324; new fonts get a numbered family, through the GUI and `flPackage()` alike, 832–835); with three fonts, `draw_path`, the later tools but `create_font`, `get_kerning` (only its refusal, 268) and the reads other than `list_glyphs` and `get_glyph_width` are untested (317–331); a switch during one call ([topics/fonts-and-sync.md](../topics/fonts-and-sync.md)); `construct_named&mark=yes` beside two fonts marked only the new font (914) |
| 85 | Place and remove components by tool (P2.7) | PARTLY, one master, an empty target: `add_component` (0.169 / 0.66) places one component, AC 1079–1101 ([WHAT-WORKS.md](../WHAT-WORKS.md)); two to five, 15 and 30 components and a repeated source by the probe of 0.171–0.173, each offset set alone (1112–1177); its `components` list (0.174 / 0.68), AC2 1178–1215 (1180–1213); its underscore refusal (0.69) live (1237); its single form's width write-back (0.178 / 0.71) live (1254, 1255). Removing one: the probe of 0.176, `layer.removeShape`, exact (1241–1245); the tool `remove_component` (0.179 / 0.72), live RC 1258–1264b (one, a list, all, 30, beside a contour, two fonts; stale requests refused). A non-empty target: the temporary-layer route passed once by probe (TL 1294–1300); `add_component` for it (0.186 / 0.73) live NB 1347–1352 (beside a contour, a component, a brush; a list; a second layer refused); since 0.187 / 0.74 a glyph with two layers refused with either active (1355, 1356; an empty active layer beside a full one took the empty route before, 1353), an empty and a non-empty one-layer glyph still placed (1357, 1358), by the list form too, its refusals there live (NB3 1360–1363). Open: its auto-layer refusal live, its restore after a failure, other transforms, other masters; two recipe-built components became contours unexplained (1059) ([topics/reading.md](../topics/reading.md)) |

Closed on 2026-11-19: row 20 (lowercase-hex warning, live 1403), row 38 (`draw_polygon` rounding report, live 1404).

Moved on 2026-11-11: row 84 (FontLab's changed icon after a kerning write) to [RUNBOOK.md](../RUNBOOK.md) §13 as the standing retest 3g; blue at once since listener 0.136 / server 0.56 (748–753).

Closed on 2026-11-10: row 32 (save and reopen after tool-drawn geometry, tests 707–712; on a font made with File > New Font, one master).

Closed on 2026-11-03: row 60 (T4, tests 145a–g, 259 and 260), rows 21, 52, 61 (T2, tests 253–255), row 59 (T3, tests 256–258), row 75 (K11 on Arial, tests 158, 230–235), row 76 (K12: (a) test 168, (b) test 243; (c) handed to T5, row 63), row 77 (K13, tests 227 and 244), row 78 (K14, tests 245 and 246), row 80 (K16, tests 247–252); row 79 (K15) dropped by the user's decision.

Closed on 2026-11-02: row 74 (K10, test 224).

Closed on 2026-11-01: rows 73a and 73b (P0.8, kerning defects A and B: listener 0.104 / server 0.33, live tests 219–223), row 33 (tests refreshed and passing on the user's machine), row 65 (K1 deployment check), row 66 (K2 listener route), row 67 (K3 POST equals GET), row 68 (K4 three pairs through the agent), row 69 (K5 `text` mode against the KERNING panel), row 70 (K6 special characters in `text`), row 71 (K7 error cases), row 72 (K8 approval flow at 250 / 251 / 324 pairs), row 73 (K9: the exception wins over the class value when names are unambiguous).
