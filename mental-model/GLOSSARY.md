# Glossary

The project's short codes and terms, one line each, with a link to where each is defined. This file only points: a fact is added or changed in its home file, never here. Add a line when a new code is introduced.

## Versions and numbers

- **0.x** (`0.196`, `v0.79`): a release of the listener or the server; which is which is said beside it or in [CHANGELOG.md](CHANGELOG.md).
- **vN without a dot** (`v8`, `v10`, `v11`): milestone summary N of the chat era (the hand-offs before 2026-11-01), not a script version. The last one: [archive/milestone-summary-v11.md](archive/milestone-summary-v11.md).
- **section 8p, §8k, §9.9:** a section number from milestone summary v11, kept as a heading in its new file; [MARKDOWN-MAP.md](MARKDOWN-MAP.md) says which file.
- **A plain number** (`1437`, `612–619`): a live test; the numbers in use are in [LIVE-TESTS.md](LIVE-TESTS.md), the next free one in [CURRENT-STATUS.md](CURRENT-STATUS.md).
- **Letters before a number** (`CK 1420`, `NB2`, `RK`): a named series of live tests, under its own heading in [LIVE-TESTS.md](LIVE-TESTS.md).
- **goal N:** a goal in [PROJECT.md](PROJECT.md). **row N:** a row of [CHECKLIST.md](CHECKLIST.md).

## Work items and test series

- **P0 to P5, LAST** (`P0.9`, `P2.7`): work items in [ROADMAP.md](ROADMAP.md); LAST holds the large-glyph tests, postponed to the end.
- **K-series** (`K1` to `K16`): the kerning live tests; **T-series** (`T1` to `T13`): the earlier live tests. Both in [LIVE-TESTS.md](LIVE-TESTS.md).

## Findings

- **F1:** reading or touching the legacy layer of a Power Brush glyph can make a later write flatten it: [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l.
- **S1:** FontLab does not ask to save a font changed only through the tools: [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §2.
- **Defect A, defect B:** the legacy kerning table can be empty while FontLab applies kerning (A); a glyph name that is also a class name is read as the class (B): [topics/kerning.md](topics/kerning.md) §9.

## Terms

- **Legacy and modern API:** FontLab's older objects (`fgFont`, `fgGlyph`, `fl.CurrentFont()`) and its newer ones (`flPackage`, `flGlyph`, `flLayer`): [ARCHITECTURE.md](ARCHITECTURE.md) ("FontLab's two APIs and how Glyphbridge uses them"); the legacy calls in use: [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10.
- **Names only, gated probe, `go=yes`:** the steps that prove a FontLab call: [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10.
- **Name gate** (`tri`, `edp`, `ocp`, `cpp`): a prefix a probe demands of its test glyph: [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §3.
- **Changed mark:** the call that turns the font's changed icon blue so FontLab asks to save (S1): [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §2.
- **Demo mode:** FontLab without saving, on the current PC: [CURRENT-STATUS.md](CURRENT-STATUS.md) (Environment).
- **Watch point:** something seen but not yet explained: [WATCH-POINTS.md](WATCH-POINTS.md).
- **AGY, `antigravity-client`:** how FontLab's OUTPUT panel names Antigravity's agent program (`agy.exe`) and its MCP client; AGY is also the label of the 2026-11-26 Antigravity test font: [RUNBOOK.md](RUNBOOK.md) step 4c.
