# Settled and dropped watch points

Watch points that were settled or dropped, one line each, in the order they were recorded. Moved from [WATCH-POINTS.md](../WATCH-POINTS.md) on 2026-11-10 and still added to. A settled fact lives in the file its line names.

- 2026-11-12: "The client name is the app's own claim" moved to [topics/server-and-endpoints.md](../topics/server-and-endpoints.md) §4: a recorded fact (236–242), not an open question.

- 2026-11-12: "`updated_fg_glyphs` after a write" dropped: no tool depends on it. The probe's list went from 0 to 4 ids after the width write on `testglyph2` and held 1 id after the width write on `A` (T4: 145b, 145e, [LIVE-TESTS.md](../LIVE-TESTS.md)); not predicted, not explained.

- 2026-11-12: "Two GUI events" (2026-11-09) dropped: neither repeated. Editing X, Y and width of a component together changed nothing and left its source glyph in front, while each field alone worked; and one Font > New Glyph added no glyph.

- 2026-11-12: the evidence of six entries moved to their topic files under the rule "an entry holds what is open and what would settle it" ([DECISIONS.md](../DECISIONS.md)); the entries stay open.

- 2026-11-11: "Brush fractions at load" settled and moved to [topics/reading.md](../topics/reading.md) §8p: a `.vfc` is rebuilt like a `.vfj` (809–812), the brush size changes the fractions (820), and FontLab's panels round sidebearings down (820, 827).

- 2026-11-10: "Tool descriptions after two restarts" settled: at the start of a new Claude Code session the `set_kerning` description was the 0.57 text, with no icon note, so a new session shows it; a session reopened from the sidebar had kept the old text. The Desktop chat's copy was not checked.

- 2026-11-10: "The hover after a kerning mark" settled for use: the icon needed one in 719, 722, 723, 725 and 726 and not in 724; with the panel refresh after the mark it was blue at once in 748–753 ([DECISIONS.md](../DECISIONS.md)). No control with the refresh off, so the cause is inferred.

- 2026-11-03: "A Power Brush glyph flattened by `create_glyph`" (F1, 332–416) settled and moved to [topics/fonts-and-sync.md](../topics/fonts-and-sync.md) §8l: a `get_glyph_outline` read followed by `create_glyph` flattens it, with one font open.

- 2026-11-09: "The package's change flags stay false" settled: `isChanged` and `hasChanges` of the package do not follow the icon that goes with the save question (657–659, 553–556), [topics/server-and-endpoints.md](../topics/server-and-endpoints.md) §2.

- 2026-11-03: "Arial on this PC" (4651 glyphs, kerning unchanged) moved to [topics/kerning.md](../topics/kerning.md): a recorded difference, not an open question.

- 2026-11-03: "`get_kerning` needs exactly one open font" moved out: it is a known limit ([ROADMAP.md](../ROADMAP.md) P0.5, [topics/kerning.md](../topics/kerning.md)), not an open observation; lifted for saved fonts in listener 0.112 / server 0.37 (265–268).
