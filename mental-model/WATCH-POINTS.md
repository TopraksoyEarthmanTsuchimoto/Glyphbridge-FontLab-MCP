# Watch points

What was seen in FontLab, in the tools or in agent behaviour and is **not yet explained or settled**. A proven fact belongs in its topic file, an open scenario in [CHECKLIST.md](CHECKLIST.md), a known limit in [ROADMAP.md](ROADMAP.md). Word budget: 750 ([MARKDOWN-MAP.md](MARKDOWN-MAP.md)).

## How an entry lives

- **Record:** the date first seen, the test numbers, what was seen, what is still open, and what would settle it.
- **Settle:** after a run that rules out the obvious alternative, move the fact to its topic file and delete the entry.
- **Drop:** when an experiment contradicts it or it no longer matters, delete it and add one line to the record at the end.
- [CURRENT-STATUS.md](CURRENT-STATUS.md) shows only the number of open entries.

## FontLab and fonts

- **Whole-unit sidebearing shift** (2026-11-03, T4: 145c, 145f, 259, 260). `setSB` moved `testglyph2` by −52, not −52.1548 (its nodes moved), and the Power Brush glyph `A` by −142, not −142.466 (its element transform, fractions kept); the reply said `set: false` with its reason. Open: does the advance round to the nearest unit or up (382.534 → 383)? What does a plain contour with fractional nodes do? Settles: a target whose advance ends in .1 to .4. Details: [topics/geometry.md](topics/geometry.md) §8c; candidate P2.8 in [ROADMAP.md](ROADMAP.md).
- **`updated_fg_glyphs` after a write** (2026-11-03, T4: 145b, 145e). The probe's list went from 0 to 4 ids after the width write on `testglyph2`, and held 1 id after the width write on `A`. Not predicted; no tool depends on it.
- **Arial on this PC** (2026-11-01, K2). 4651 glyphs here, 4548 on the old PC; the kerning is unchanged (`table_size` 1370, the same 13 pair values). Perhaps another Arial version: not checked.
- **Arial's `kern` feature against its table** (2026-11-03, K11). 1,417 `pos` lines against 1,370 table entries, although the 20 pairs compared agree.
- **FontLab 8.9.5 against 8.4.2** (since 2026-11-01). No difference seen. Writes seen on 8.9.5: `create_glyph`, `draw_polygon`, `set_glyph_width` and `set_glyph_sidebearings` on new glyphs (K9 setup, 190, 253) and on two existing glyphs (T4), and a declined `delete_glyph` (190). The other writes: not yet.

## Agents and clients

- **Answering from an earlier reply** (2026-11-03, T2: 254). Asked for a width, the agent answered from the sidebearings reply and said so; asked to read it "now", it read (254b). Watch in later agent-level tests.
- **Guessing where a kerning value comes from** (2026-11-01, K5, K8). Agents guessed between a direct pair and a class ("may sit in GPOS lookups"). Since 0.104 / 0.33 the reply names the `source`, and in 223 the Desktop agent reported it without guessing. Watch in later agent-level tests.
- **The client name is the app's own claim** (2026-11-03, 236–242). It names the app, not the model, and both Claude apps send the same name. The launcher does not tell them apart on this PC either: the Desktop app starts the servers for both (237–238). A name with non-ASCII characters: not seen in FontLab.
- **The change counter outlives sessions.** `fontlab_status` showed 9, and later 20, changes at the start of Claude Code sessions that had made none (also after a full FontLab restart), and 6 at the start of the session of 2026-11-03; after a full Claude Desktop restart, no counter. Inferred: the server process outlives the sessions. Not checked in the process list.

## Settled or dropped

- 2026-11-03: "`get_kerning` needs exactly one open font" moved out: it is a known limit ([ROADMAP.md](ROADMAP.md) P0.5, [topics/kerning.md](topics/kerning.md)), not an open observation; lifted for saved fonts in listener 0.112 / server 0.37 (265–268).
