# Refusal register

Every case a tool refuses, or that no tool supports yet, in one table: which tools refuse it, which handle it, and what would lift it. The rule that uses this file is in [AGENTS.md](../../AGENTS.md); the decision behind it is in [DECISIONS.md](../DECISIONS.md) (2026-11-24, refusals tracked in one register).

**How a row changes.** When a tool comes to handle a case, move the tool from "Refused by" to "Handled by" with its test numbers, and check the other tools in "Refused by" in the same proposal. A row that no tool refuses any more moves to a file in [archive/](../archive/README.md), with the date. The evidence stays in the file the last column links to; this table holds only the state.

`add_contours` (listener 0.207 / server 0.89) is stub-tested only, not yet run in FontLab. Since 0.207 the edit tools' cases are also a table in the listener code, `_EDIT_ACCEPTS`; a stub test runs every tool in it against every case and fails when a tool departs from the table. A change here and a change there go together.

| Case | Refused by | Handled by | What would lift it | Evidence |
|---|---|---|---|---|
| The glyph already holds an outline | `draw_path`, `draw_polygon` (layer guard) | `move_nodes`, `add_contours`; `add_component` (temporary layer, 0.186) | only a tool built for that edit ([DECISIONS.md](../DECISIONS.md), 2026-11-14) | [geometry.md](geometry.md) |
| Several shapes in the glyph | `move_nodes` (stub only, [CHECKLIST.md](../CHECKLIST.md) row 30), `add_contours` | none | a probe that edits the second shape, and a way to name a shape | [geometry.md](geometry.md) |
| A shape with its own transform | `move_nodes` (identity required), `add_contours` | the reading tools | a probe that adds to, or moves nodes in, a moved or scaled shape | [reading.md](reading.md), [geometry.md](geometry.md) |
| Components beside the edited shape | `move_nodes` (1021), `add_contours` | `add_component`, `remove_component` | a probe that edits a plain shape beside a component | [reading.md](reading.md) |
| A Power Brush or other composite shape | `move_nodes`, `add_contours`, `remove_component` | the reading tools (modern route); `add_component` beside one (PB 1328–1345) | a gated series like PB, per tool (F1) | [fonts-and-sync.md](fonts-and-sync.md) §8l |
| A component source that is not one plain shape | `add_component` | none | not chosen | [reading.md](reading.md) |
| A target with several layers, or another layer active | `add_component` (NB 1353) | none | not chosen | [reading.md](reading.md) |
| An auto layer switched on | `remove_component` | none | not chosen | [reading.md](reading.md) |
| An underscore name in a `components` list | `add_component` (0.175) | the single form | none known: FontLab's build reads it as a ligature (AC2u 1216–1235) | [reading.md](reading.md) |
| Other masters | every tool (not built) | none | a design decision first | [ROADMAP.md](../ROADMAP.md) |
| Several fonts, kerning | `get_kerning` unless the font's path is not empty and matches | the other tools follow the font in front | [ROADMAP.md](../ROADMAP.md) P0.5 | [fonts-and-sync.md](fonts-and-sync.md) |
