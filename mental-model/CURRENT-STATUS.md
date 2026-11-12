Last verified: 2026-11-12 against commit 19e08da plus the uncommitted build of listener v0.146 / server v0.60 (`create_font`; tests PASS, deployed listener identical, not yet run live); listener v0.137–v0.145 research probes only; server 0.59 live (829, 830); new-font names NF 831–835 and the Font window's encoding EN 836–840 run live on 2026-11-11, no code change; font names NM 841–880 run live on 2026-11-11 with listeners 0.136–0.143, and 881–914 on 2026-11-12; `fontlab_status` 0.136 / 0.58 (800), the new `draw_path` reply live (801); brush fractions and FontLab's panel rounding (PB2 802–828) run live on 2026-11-10 and 2026-11-11, no code change; open contours on export 779–791 and brush fractions at load 792–799, open contours through a save and reopen 755–764, component rotation 765–771 and T9 on a font made by `flPackage()` 772–778 run live on 2026-11-10; S1 657–706 and components 606–656 run live on 2026-11-09, save and reopen 707–712, kerning research 713–717, the kerning mark 718–728 and the KERNING panel 729–754 on 2026-11-10; live checks 584–603 done on 2026-11-04, not re-run)

# Current status

## Versions and identity

| Part | Version | md5 |
|---|---|---|
| listener `glyphbridge_fontlab_mcp_listener.py` | `VERSION = "0.146"` | `bd4fc6bd397b427f684a5b8cb167c225` (533,813 bytes) |
| server `glyphbridge_mcp_server.py` | `SERVER_VERSION = "0.60"`, `MIN_LISTENER_VERSION` (0, 82) | `aadd052542f8321de90d2b84c5891e2b` (219,492 bytes) |
| tests | 4 harnesses | PASS at **3206 + 58 + 90 + 1266** lines |

Which version each feature needs: [WHAT-WORKS.md](WHAT-WORKS.md). What each release changed: [CHANGELOG.md](CHANGELOG.md).

## Environment (verified 2026-11-01)

The founding developer has moved the project to a new Windows 11 PC and to this repository on November 1st 2026. This change has set the project environment as:
- Python **3.15.2**, with `mcp` **2.2.0** in the repository `venv`.
- FontLab **8.9.5** (the earlier work was on 8.4.2).
- The MCP connection works from **Claude Code** and from the **Claude Desktop chat**.
- FontLab runs in **Demo mode** on this PC (the user, 2026-11-11): it does everything a fully functional FontLab does except save files. Research with a File > Save stage cannot be completed here, and the user is told before each research ([AGENTS.md](../AGENTS.md)). Whether FontLab still asks to save when a changed font closes (S1) is untested in Demo mode. The project may move to a PC where FontLab is fully functional; that PC's entry here then replaces this one.

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

- Not built: multi-master fonts, several shapes per glyph, editing an existing outline. Built, not yet run live: `create_font` (listener 0.146 / server 0.60). Components: one or two in a glyph are read and labelled ("Resume here" below); placing them by tool and the rest are open. See [ROADMAP.md](ROADMAP.md).
- Open scenarios: [CHECKLIST.md](CHECKLIST.md).
- **F1** is fixed in 0.120 / 0.42 (V120 in [LIVE-TESTS.md](LIVE-TESTS.md)), **but still open** for paths not run live: `delete_glyph` after a read or write of a Power Brush glyph (`set_glyph_unicode` left it intact in 695, one run), several elements, and the debug probes, which still touch the legacy layer ([topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l).
- **Add Component crash on a glyph with no layer (612–619):** fixed for one master in 0.127 / 0.48 (620, one run). Not fixed for multi-master fonts or a `create_glyph` reply with `layer_note`: avoid Add Component on such a glyph in a font with unsaved work ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §9).
- **No save question (S1, 460–472):** FontLab closes a font changed only through the tools without asking about saving (it asks after a change made in its GUI), so closing loses that work silently; the chat reminder is the only warning ([topics/server-and-endpoints.md](topics/server-and-endpoints.md) §2). Since 0.132 / 0.51 glyph writes, and since 0.133 / 0.53 deletes, bring the question back, and since 0.134 / 0.54 kerning writes that changed an entry ("Resume here").

## Resume here (sessions of 2026-11-09 to 2026-11-12)

- **Components (P1.1), live 606–656:** one component, identity, offset and horizontal scale read `verified` ([topics/reading.md](topics/reading.md)); since 0.128 / 0.49 `get_glyph_outline` labels a component and names its source (624–626). The crash fix is live-checked (620–623). Two components in a glyph and one source shared by two glyphs read correctly (627–636). Since 0.130 / 0.50 an accent inside its base reads `verified` element by element (652), and a component behind its source reads `unverified` (`source_in_step`, 651, 653; plain offsets only). **A tool edit of a source reached the glyphs using it once in five; GUI edits did all four times** (638–655). **Rotation (765–771, 2026-11-10):** components rotated 90° and 30° in FontLab's Transform panel read `verified`, a rotated curve with its exact extent; `source_in_step` says `"unknown"` for them ([topics/reading.md](topics/reading.md)). A rotated component inside another, the case that must read `unverified`, was not built (771). No tool places a component yet.
- **Save question (S1, goal 7 in [PROJECT.md](PROJECT.md); 657–728):** since 0.132–0.134 / 0.51–0.54 every verified glyph write, delete and kerning write that changed an entry is marked, and FontLab asks on close. Not marked, with `save_question_note`: a delete that leaves only `.notdef`, `create_glyph` with no layer, the legacy width route, an unconfirmed sync. [WHAT-WORKS.md](WHAT-WORKS.md), [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §2.
- **The KERNING panel (goal 8; 729–754):** a kerning write that changed an entry refreshes it at once, since 0.136 / 0.56. Open: classes, other masters, timing on large fonts; the Desktop chat's copy of the 0.57 description was not checked. [topics/kerning.md](topics/kerning.md) §14.
- **Save and reopen (T9):** tool-made glyphs, open contours included, came back exactly, in a font made with File > New Font (707–712, 755–764) and in one made by `flPackage()` (772–778); a Power Brush glyph's nodes gained fractions at load. [topics/reading.md](topics/reading.md) §8p, [topics/geometry.md](topics/geometry.md) §8g, [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k.
- **Brush fractions at load (PB, 792–799):** FontLab rebuilds a Power Brush outline from its stroke when it opens a `.vfj`, and a `.vfc` the same way, node for node (PB2 809–812); the stored outline is not used. The brush size changes the fractions (820), and FontLab's panels round sidebearings down, −38.25 to −39 (827). Open: why a GUI rebuild gave whole-unit extremes ([WATCH-POINTS.md](WATCH-POINTS.md)). [topics/reading.md](topics/reading.md) §8p.
- **Open contours on export (EX, 779–791):** FontLab's export, TrueType and OpenType PS with default settings, drops open contours silently; the font keeps them. Since server 0.58 the `draw_path` reply and description say so (reply live 801; the description was still stale after one restart). [topics/geometry.md](topics/geometry.md) §8g.
- **New fonts (NF 831–835, EN 836–840, 2026-11-11):** FontLab names each further new font `Unnamed1`, `Unnamed2`, …, and `flPackage()` follows the same rule by itself and brings the new font to the front, also with two and three fonts open, so a create-font tool (P0.3) needs no renaming step. Its Font window opens with Encoding None, while File > New Font opens with Latin Simple and ignores the preference; setting the box of a GUI font through the API is won't-fix for now. [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k.
- **Font names (NM 841–914, 2026-11-11 and 2026-11-12, P0.4; listener 0.137–0.145, probes only):** Font Info's Build Names gives Full name = family + " " + style, PostScript = family without spaces + "-" + style, Style group = family. Through the API the package names read back, Font Info shows them and `title_name` returns the live Full name, but two displays lag. **The tab title** is a copy refreshed only when the Full name is changed to a different value in Font Info (902, 907b, 910: typing any other name, then the wanted one, works); no API write, `title_name` call, empty OK, identical retype, add or tab switch does it (896–909). **The FONTS panel** follows a family changed in Font Info (903) and usually a close (901), not an add; a font named in its creation request kept its creation name after two closes (896, 914). A new font takes the lowest free `tfn` (894–901). **Save question:** an API name write leaves the font unmarked (911); the package-level mark `notifyChangesApplied(title, <flPackage>, False)` brings it back on a GUI font (912), on a `flPackage()` font (913) and on the right font among three (914, `construct_named&mark=yes`). Both routes of `create_font` are built in listener 0.146 / server 0.60 (2026-11-12): `flPackage()`, the four names and the legacy family, the mark, and notes on what FontLab will not show, in the reply and the OUTPUT panel ([DECISIONS.md](DECISIONS.md)). Open: [WATCH-POINTS.md](WATCH-POINTS.md). Evidence: [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k.
- The full text of these items as of 2026-11-10: [archive/CURRENT-STATUS-resume-2026-11-10.md](archive/CURRENT-STATUS-resume-2026-11-10.md).
- **FontLab:** no test font is kept; every test needs a new disposable font.
- **Next (the user's choice, not yet made):** (1) the other component transforms (mirroring, slant, vertical scale) and a rotated component inside another (rotation itself: 765–771); (2) open questions of open contours, each only with the user's OK: quadratic (a save and reopen is proven, 755–764; export 779–791); (3) **final polish for kerning** (the user's decision of 2026-11-04, for later): an exception over a class on a disposable copy of a real font; writes with two saved fonts open; multi-master, a design decision before any test.

## Next steps (the user's priorities of 2026-11-01 and 2026-11-09)

1. **Components are under way** (the user's choice of 2026-11-06); kerning polish waits, and of open contours only quadratic is left (export and the brush fractions were taken up on 2026-11-10 by the user's choice, the brush fractions finished on 2026-11-11 (PB2 802–828)): see "Resume here" above. Other candidates (none approved): a tool that places a component (P2.7, research first), finding why tool edits of a source miss its composites ([WATCH-POINTS.md](WATCH-POINTS.md)); `delete_glyph` after a Power Brush write; the review of legacy calls (goal 6 in [PROJECT.md](PROJECT.md); the table in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10), starting with `get_glyph_width` (legacy `glyph.width`, while the writes use `advanceWidth`) and `font.info` (it disagreed with Font Info, 298).
2. The **T-series**: T2, T3 and T4 are done. What is open in T5 is in [CHECKLIST.md](CHECKLIST.md) row 63; the candidates for several open fonts, none approved, are in [ROADMAP.md](ROADMAP.md) P0.5.
3. **S1, stage 2** (none approved): the writes still unmarked: the first glyphs of a new font while another font is open, a delete that leaves only `.notdef`, the legacy width route.
4. **Under way (the user's choice of 2026-11-11):** P0.3 / P0.4, a create-font tool, research first (NF, EN, NM in "Resume here"); built in listener 0.146 / server 0.60 on 2026-11-12; next, its live checks from 915 (unnamed with one font; a second font in the same listener run; named beside two other fonts; closing each, answering No), none needing a save; then P0.9, the first glyph with other fonts open. Required by the user, not yet designed: P1.6, kerning group membership.

The next free test number is **915**; the numbers in use: [LIVE-TESTS.md](LIVE-TESTS.md). Large-glyph and very-large-read tests stay in the LAST block.

## Contradictions and watch points

- Between the documents and the code: none known (versions, md5 and tests checked 2026-11-12 against listener 0.146 / server 0.60; the 19 tools and the main routes, `/font/create` included, checked 2026-11-12; ARCHITECTURE's "the path never leaves the listener" corrected after test 273).
- Open watch points (seen, not yet explained or settled): **28**, in [WATCH-POINTS.md](WATCH-POINTS.md).
