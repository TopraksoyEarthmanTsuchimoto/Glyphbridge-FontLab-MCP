# Settled and dropped watch points

Watch points that were settled or dropped, one line each, in the order they were recorded. Moved from [WATCH-POINTS.md](../WATCH-POINTS.md) on 2026-11-10 and still added to. A settled fact lives in the file its line names.

- 2026-11-26: "`fonts_changed` names a shared font name once" (1942, 1944) settled by design: server 0.97 lists each changed font as an object, same-named fonts apart with `same_name`, times and `in_front` (the user's choice of Option 2), run live FC 1945–1951 ([topics/server-and-endpoints.md](../topics/server-and-endpoints.md) §2, [LIVE-TESTS.md](../LIVE-TESTS.md)); in that run the agent named both fonts with their times.

- 2026-11-24: "The client gives up while a FontLab dialog waits" (GT 1566–1576, TO 1577–1582, TO2 1583–1587) settled: both parts of the chosen fix are built and run live, self-closing dialogs (listener 0.203 / server 0.83, SD 1599–1617) and the change count in the listener (listener 0.204 / server 0.85, CL 1618–1634) ([topics/server-and-endpoints.md](../topics/server-and-endpoints.md) §2, [DECISIONS.md](../DECISIONS.md) 2026-11-21 and 2026-11-24); the user's choice.

- 2026-11-24: "`changes_by_font` absent: empty log or unreadable?" (CL 1618) settled by design: server 0.86 answers `[]` for an empty record and `"unknown"` when the record cannot be read ([topics/server-and-endpoints.md](../topics/server-and-endpoints.md) §2, [CHANGELOG.md](../CHANGELOG.md)); the user's choice B. Not yet run live.

- 2026-11-20: "What `flPackage.isEqual` compares" (PK 930, 931) dropped: the product no longer uses it ([FONTLAB-API-RULES.md](../FONTLAB-API-RULES.md), [LESSONS.md](../LESSONS.md)); the user's choice.

- 2026-11-20: "Answering from an earlier reply" (T2 254, 254b) dropped: an agent-behaviour note with no way to settle it; the user's choice.

- 2026-11-20: "A fractional width written through the API" (AW 1449, AW2 1451–1455) merged into the open entry "Fractional widths and FontLab's two reads": since listener 0.197 / server 0.80 `set_glyph_width` writes whole units only; the user's choice.

- 2026-11-20: "`remove_kerning`'s instruction on `no entry` predates class sides" (CK 1430; also the revert and restore sentences for a class pair, 1421, 1429, and the OUTPUT line) settled by listener 0.195 / server 0.79: run live CK2 1434–1436a, a glyph-only control unchanged (1435) ([LIVE-TESTS.md](../LIVE-TESTS.md), [CHANGELOG.md](../CHANGELOG.md)).

- 2026-11-18: "`add_component` judges 'empty' by the active layer only" (NB 1353) settled in part: since listener 0.187 / server 0.74 every target needs exactly one layer, the active one, and `cpqt5` was refused with either layer active, nothing changed (1355, 1356, [LIVE-TESTS.md](../LIVE-TESTS.md)). Its open question, the `verified` read of such a glyph, stays in [WATCH-POINTS.md](../WATCH-POINTS.md).

- 2026-11-17: "A source name with an underscore dropped from a recipe" settled by the approved plan: the likely cause, a recipe of several glyphs reading `a_b` as a ligature of its parts (one run, 1234), is guarded since listener 0.175 / server 0.69, which refuse such a list; run live AC3 1237–1239. What is left open (a second run of 1234; why the single form places such a glyph) is in [topics/reading.md](../topics/reading.md).

- 2026-11-17: "FontLab 8.9.5 against 8.4.2" dropped: 8.4.2 is no longer used ([CURRENT-STATUS.md](../CURRENT-STATUS.md), Environment). No difference was seen in the writes run on 8.9.5 from 2026-11-01 to 2026-11-09 (190–683, [LIVE-TESTS.md](../LIVE-TESTS.md)).

- 2026-11-17: "Arial's `kern` feature against its table" (K11) dropped: GPOS kerning is a non-goal ([PROJECT.md](../PROJECT.md)). 1,417 `pos` lines against 1,370 table entries, while the 20 pairs compared agreed ([topics/kerning.md](../topics/kerning.md) §11).

- 2026-11-17: "Two 'no font' states" (852) dropped: the tools decide by `CountFonts()` ([topics/fonts-and-sync.md](../topics/fonts-and-sync.md) §8k), so neither state affects them. `CurrentFont()` returned FontLab's placeholder font at the start of a FontLab run and nothing later in the same run.

- 2026-11-17: "Guessing where a kerning value comes from" (K5, K8) dropped: since 0.104 / 0.33 the reply names the `source`, and the Desktop agent in 223 reported it without guessing ([topics/kerning.md](../topics/kerning.md)).

- 2026-11-17: "The component `buildAuto()` placed" (1041b, 1041c) settled in [topics/reading.md](../topics/reading.md) "Components: placing one through the API": after `autoLayer = False` FontLab showed a normal component (1042–1042b); of the differences seen, the flat fill and the icon before the name are how any unselected component looks.

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
