Last verified: 2026-11-11 against commit 567b06e plus uncommitted server v0.58 and v0.59 (listener v0.136, server v0.59; tests PASS, deployed listener identical; server 0.59 live (829, 830); `fontlab_status` 0.136 / 0.58 (800), the new `draw_path` reply live (801); brush fractions and FontLab's panel rounding (PB2 802–828) run live on 2026-11-10 and 2026-11-11, no code change; open contours on export 779–791 and brush fractions at load 792–799, open contours through a save and reopen 755–764, component rotation 765–771 and T9 on a font made by `flPackage()` 772–778 run live on 2026-11-10; S1 657–706 and components 606–656 run live on 2026-11-09, save and reopen 707–712, kerning research 713–717, the kerning mark 718–728 and the KERNING panel 729–754 on 2026-11-10; live checks 584–603 done on 2026-11-04, not re-run)

# Current status

## Versions and identity

| Part | Version | md5 |
|---|---|---|
| listener `glyphbridge_fontlab_mcp_listener.py` | `VERSION = "0.136"` | `373d42d8ff60dee92766b5d3875c0bdd` (491,688 bytes) |
| server `glyphbridge_mcp_server.py` | `SERVER_VERSION = "0.59"`, `MIN_LISTENER_VERSION` (0, 82) | `f100046d2a7f4e972ec41a990b6ed79d` (211,635 bytes) |
| tests | 4 harnesses | PASS at **2951 + 58 + 90 + 1222** lines |

Which version each feature needs: [WHAT-WORKS.md](WHAT-WORKS.md). What each release changed: [CHANGELOG.md](CHANGELOG.md).

## Environment (verified 2026-11-01)

The founding developer has moved the project to a new Windows 11 PC and to this repository on November 1st 2026. This change has set the project environment as:
- Python **3.15.2**, with `mcp` **2.2.0** in the repository `venv`.
- FontLab **8.9.5** (the earlier work was on 8.4.2).
- The MCP connection works from **Claude Code** and from the **Claude Desktop chat**.

On 2026-11-01 `--check` gave four `[OK]` lines, and the tests passed on this machine with the deployed listener copy identical; re-checked at the end of that day with listener 0.104 / server 0.33 (Arial open).

Setup steps: [RUNBOOK.md](RUNBOOK.md).

## What works (summary by area)

Proven live. The evidence and the limits of each are in [WHAT-WORKS.md](WHAT-WORKS.md), and [AGENTS.md](../AGENTS.md) says when to read it.

| Area | Proven live | Detail |
|---|---|---|
| Reading | Outlines, transforms, open contours; components partly | [reading](topics/reading.md) |
| Writing | Glyphs, Unicode, width, sidebearings, contours into an empty glyph | [geometry](topics/geometry.md), [names-unicode](topics/names-unicode.md) |
| Save question | Glyph writes, deletes and kerning writes yes | [server-and-endpoints](topics/server-and-endpoints.md) §2 |
| Kerning | Read from the current master; write glyph : glyph only; the KERNING panel updates at once | [kerning](topics/kerning.md) |
| Fonts | No font open; several fonts follow the one in front | [fonts-and-sync](topics/fonts-and-sync.md) |
| Other | `.notdef`, font names, activity log, save reminder | [WHAT-WORKS.md](WHAT-WORKS.md) |

## Not proven or not built

- Not built: multi-master fonts, several shapes per glyph, editing an existing outline, a create-font tool. Components: one or two in a glyph are read and labelled ("Resume here" below); placing them by tool and the rest are open. See [ROADMAP.md](ROADMAP.md).
- Open scenarios: [CHECKLIST.md](CHECKLIST.md).
- **F1** is fixed in 0.120 / 0.42 (V120 in [LIVE-TESTS.md](LIVE-TESTS.md)), **but still open** for paths not run live: `delete_glyph` after a read or write of a Power Brush glyph (`set_glyph_unicode` left it intact in 695, one run), several elements, and the debug probes, which still touch the legacy layer ([topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l).
- **Add Component crash on a glyph with no layer (612–619):** fixed for one master in 0.127 / 0.48 (620, one run). Not fixed for multi-master fonts or a `create_glyph` reply with `layer_note`: avoid Add Component on such a glyph in a font with unsaved work ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §9).
- **No save question (S1, 460–472):** FontLab closes a font changed only through the tools without asking about saving (it asks after a change made in its GUI), so closing loses that work silently; the chat reminder is the only warning ([topics/server-and-endpoints.md](topics/server-and-endpoints.md) §2). Since 0.132 / 0.51 glyph writes, and since 0.133 / 0.53 deletes, bring the question back, and since 0.134 / 0.54 kerning writes that changed an entry ("Resume here").

## Resume here (sessions of 2026-11-09 to 2026-11-11)

- **Components (P1.1), live 606–656:** one component, identity, offset and horizontal scale read `verified` ([topics/reading.md](topics/reading.md)); since 0.128 / 0.49 `get_glyph_outline` labels a component and names its source (624–626). The crash fix is live-checked (620–623). Two components in a glyph and one source shared by two glyphs read correctly (627–636). Since 0.130 / 0.50 an accent inside its base reads `verified` element by element (652), and a component behind its source reads `unverified` (`source_in_step`, 651, 653; plain offsets only). **A tool edit of a source reached the glyphs using it once in five; GUI edits did all four times** (638–655). **Rotation (765–771, 2026-11-10):** components rotated 90° and 30° in FontLab's Transform panel read `verified`, a rotated curve with its exact extent; `source_in_step` says `"unknown"` for them ([topics/reading.md](topics/reading.md)). A rotated component inside another, the case that must read `unverified`, was not built (771). No tool places a component yet.
- **Save question (S1, goal 7 in [PROJECT.md](PROJECT.md); 657–728):** since 0.132–0.134 / 0.51–0.54 every verified glyph write, delete and kerning write that changed an entry is marked, and FontLab asks on close. Not marked, with `save_question_note`: a delete that leaves only `.notdef`, `create_glyph` with no layer, the legacy width route, an unconfirmed sync. [WHAT-WORKS.md](WHAT-WORKS.md), [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §2.
- **The KERNING panel (goal 8; 729–754):** a kerning write that changed an entry refreshes it at once, since 0.136 / 0.56. Open: classes, other masters, timing on large fonts; the Desktop chat's copy of the 0.57 description was not checked. [topics/kerning.md](topics/kerning.md) §14.
- **Save and reopen (T9):** tool-made glyphs, open contours included, came back exactly, in a font made with File > New Font (707–712, 755–764) and in one made by `flPackage()` (772–778); a Power Brush glyph's nodes gained fractions at load. [topics/reading.md](topics/reading.md) §8p, [topics/geometry.md](topics/geometry.md) §8g, [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k.
- **Brush fractions at load (PB, 792–799):** FontLab rebuilds a Power Brush outline from its stroke when it opens a `.vfj`, and a `.vfc` the same way, node for node (PB2 809–812); the stored outline is not used. The brush size changes the fractions (820), and FontLab's panels round sidebearings down, −38.25 to −39 (827). Open: why a GUI rebuild gave whole-unit extremes ([WATCH-POINTS.md](WATCH-POINTS.md)). [topics/reading.md](topics/reading.md) §8p.
- **Open contours on export (EX, 779–791):** FontLab's export, TrueType and OpenType PS with default settings, drops open contours silently; the font keeps them. Since server 0.58 the `draw_path` reply and description say so (reply live 801; the description was still stale after one restart). [topics/geometry.md](topics/geometry.md) §8g.
- The full text of these items as of 2026-11-10: [archive/CURRENT-STATUS-resume-2026-11-10.md](archive/CURRENT-STATUS-resume-2026-11-10.md).
- **FontLab:** no test font is kept; every test needs a new disposable font.
- **Next (the user's choice, not yet made):** (1) the other component transforms (mirroring, slant, vertical scale) and a rotated component inside another (rotation itself: 765–771); (2) open questions of open contours, each only with the user's OK: quadratic (a save and reopen is proven, 755–764; export 779–791); (3) **final polish for kerning** (the user's decision of 2026-11-04, for later): an exception over a class on a disposable copy of a real font; writes with two saved fonts open; multi-master, a design decision before any test.

## Next steps (the user's priorities of 2026-11-01 and 2026-11-09)

1. **Components are under way** (the user's choice of 2026-11-06); kerning polish waits, and of open contours only quadratic is left (export and the brush fractions were taken up on 2026-11-10 by the user's choice, the brush fractions finished on 2026-11-11 (PB2 802–828)): see "Resume here" above. Other candidates (none approved): a tool that places a component (P2.7, research first), finding why tool edits of a source miss its composites ([WATCH-POINTS.md](WATCH-POINTS.md)); `delete_glyph` after a Power Brush write; the review of legacy calls (goal 6 in [PROJECT.md](PROJECT.md); the table in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10), starting with `get_glyph_width` (legacy `glyph.width`, while the writes use `advanceWidth`) and `font.info` (it disagreed with Font Info, 298).
2. The **T-series**: T2, T3 and T4 are done. What is open in T5 is in [CHECKLIST.md](CHECKLIST.md) row 63; the candidates for several open fonts, none approved, are in [ROADMAP.md](ROADMAP.md) P0.5.
3. **S1, stage 2** (none approved): the writes still unmarked: the first glyphs of a new font while another font is open, a delete that leaves only `.notdef`, the legacy width route.
4. Candidates after that (none approved): P0.3 / P0.4, a create-font tool. Required by the user, not yet designed: P1.6, kerning group membership.

The next free test number is **831**; the numbers in use: [LIVE-TESTS.md](LIVE-TESTS.md). Large-glyph and very-large-read tests stay in the LAST block.

## Contradictions and watch points

- Between the documents and the code: none known (versions, md5 and tests checked 2026-11-11 against listener 0.136 / server 0.59, uncommitted; the 18 tools and the main routes checked 2026-11-10; ARCHITECTURE's "the path never leaves the listener" corrected after test 273).
- Open watch points (seen, not yet explained or settled): **26**, in [WATCH-POINTS.md](WATCH-POINTS.md).
