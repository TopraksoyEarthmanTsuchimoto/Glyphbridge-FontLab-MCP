Last verified: 2026-11-09 against commit 9bda0a6 plus uncommitted code and document updates, listener v0.128 / server v0.49 (tests PASS, deployed listener identical, `fontlab_status` 0.128 / 0.49; components 606–626 run live that day; live checks 584–603 done on 2026-11-04, not re-run)

# Current status

## Versions and identity

| Part | Version | md5 |
|---|---|---|
| listener `glyphbridge_fontlab_mcp_listener.py` | `VERSION = "0.128"` | `4934e0abec08d6d446fe5cd5379d7bdc` (455,751 bytes) |
| server `glyphbridge_mcp_server.py` | `SERVER_VERSION = "0.49"`, `MIN_LISTENER_VERSION` (0, 82) | `344496c4f37cc4cab26bb597132fa91e` (197,037 bytes) |
| tests | 4 harnesses | PASS at **2714 + 58 + 90 + 1109** lines |

`get_kerning` needs listener 0.104 (server 0.33); with several fonts open, 0.112 / 0.37. The PostScript names from the font package need 0.118 / 0.41; the F1 fix, 0.120 / 0.42; the vertical check against `inkBox()` and exact quadratic extents, 0.121 / 0.43. Listeners 0.122 and 0.123 add only gated research probes for kerning writes; `set_kerning` needs 0.124 / 0.44, its whole-unit check and panel wording 0.45; open contours are read by server 0.46; listener 0.125 adds only the gated probe `/debug/tryopen`; `draw_path` draws open contours with 0.126 / 0.47; `create_glyph` makes the layer with 0.127 / 0.48; `get_glyph_outline` labels components with 0.128 / 0.49. What each release changed: [CHANGELOG.md](CHANGELOG.md).

## Environment (verified 2026-11-01)

The founding developer has moved the project to a new Windows 11 PC and to this repository on November 1st 2026. This change has set the project environment as:
- Python **3.15.2**, with `mcp` **2.2.0** in the repository `venv`.
- FontLab **8.9.5** (the earlier work was on 8.4.2).
- The MCP connection works from **Claude Code** and from the **Claude Desktop chat**.

On 2026-11-01 `--check` gave four `[OK]` lines, and the tests passed on this machine with the deployed listener copy identical; re-checked at the end of that day with listener 0.104 / server 0.33 (Arial open).

Setup steps: [RUNBOOK.md](RUNBOOK.md).

## What works (live-proven in FontLab)

- **Reading:** outlines with element transforms (scale, offset, slant), cubic and quadratic outlines, Power Brush output, widths, sidebearings, the stale-view fallback; since 0.120 / 0.42 a glyph with modern nodes from the modern layer only, its transforms applied, checked horizontally (497–520); since 0.121 / 0.43 checked vertically too, against FontLab's `inkBox()`, and quadratic outlines from their exact extents (INK 521–533, V121 534–541); since server 0.46 open contours, straight and cubic, `verified` with an `svg_path` without Z and no direction (OC 579–585). → [topics/reading.md](topics/reading.md)
- **Writing:** create and delete glyphs (name safety rules), Unicode set and clear, width, sidebearings, closed straight and cubic contours into an empty glyph, since 0.126 / 0.47 open ones too, alone or with closed ones (OT 595–603), auto sync after every modern write, also with the glyph's editor tab open (T3, 257) and on an existing glyph with a legacy layer, in a font opened from a file (T4, 145a–g, 259, 260: a plain contour and a Power Brush shape). → [topics/geometry.md](topics/geometry.md), [topics/names-unicode.md](topics/names-unicode.md), [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **Save reminder:** `finish_changes` through the Desktop chat (T2, 253–255): one request with three verified writes ended with one bold reminder, a read-only request with none; FontLab showed LSB 50, width 400, RSB 50 as reported.
- **`.notdef`** check and one-time dialog. → [topics/notdef.md](topics/notdef.md)
- **Activity log** in FontLab's OUTPUT panel: one line per change and one summary of reads, naming the client (`local-agent-mode`) and, once, the program that started the server (`| CLAUDE`); live tests 190, 191, 225–229, 236–242. Stub-tested only: REFUSED / FAILED lines, unsynced or warned results, the `writes` / `off` modes, the flush at `/shutdown`. → [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §4
- **No font open** (P0.2): with the only font closed in a running FontLab, `fontlab_status` gave `font_open: false`, and a width read and a create were refused; Arial reopened read as before (227, 228). In a freshly started FontLab (K13, 244) all 8 read routes answered `open: false`, the placeholder glyph `Paper` included, with no dialog. Not seen live: the other write tools (stub only). → [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **Several fonts open** (T5, 262–331): every tool follows the font window in front, every reply names its font, and a switch is reported in the next reply, also after an error; `get_kerning` refuses an unsaved font in front. With three fonts, `draw_path` and the reads other than `list_glyphs`, `get_glyph_width` and `get_kerning` are untested. → [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **Kerning** (K1–K14 and K16, 2026-11-01 to 2026-11-03, each test in [LIVE-TESTS.md](LIVE-TESTS.md)): **since 0.104 / 0.33** `get_kerning` reads the current master's table and reports each value's `source` (live 219–223); with several fonts open it reads the font in front, matched by path, and names it (0.112 / 0.37, 265–268). Proven: GET and POST, the agent reading only the pairs it needs and asking above 250, `text` mode equal to the KERNING panel with its special characters, errors never read as zero, an exception winning over its class, a FontLab text line and Arial's `kern` feature agreeing with the table, an empty table, timings up to 2,000 pairs. → [topics/kerning.md](topics/kerning.md) §10, §11

- **Kerning writes:** `set_kerning` writes glyph : glyph pairs of the current master, in whole units, verified by a re-read and saved like GUI pairs (research 542–564, live 565–577). FontLab's KERNING panel shows them only after a switch to another font and back, or a save and reopen; closing asks no save question and loses them; Undo cannot take them back. → [topics/kerning.md](topics/kerning.md) §13, §14

- **Font names** (291–302): FontLab keeps the names Font Info shows in the font package (`psn`, `ffn`, `tfn`, `tsn`, `sgn`); the legacy `font.info` the tools read before can disagree (298). Since listener 0.118 `/font/current` reads the package when it is matched to the font (302), and says why when it is not (301); `get_current_font` reports them since server 0.41 (303). The delete dialog names the client as sent and the font, and the save reminder uses the system's shortcut (0.114 / 0.40, 304–308, [CHANGELOG.md](CHANGELOG.md)). → [topics/fonts-and-sync.md](topics/fonts-and-sync.md)

## Not proven or not built

- Not built: components, multi-master fonts, several shapes per glyph, editing an existing outline, a create-font tool, save-and-reopen checks (T9). See [ROADMAP.md](ROADMAP.md).
- Open scenarios: [CHECKLIST.md](CHECKLIST.md).
- **F1** is fixed in 0.120 / 0.42 (V120 in [LIVE-TESTS.md](LIVE-TESTS.md)), **but still open** for paths not run live: `delete_glyph` and `set_glyph_unicode` after a read or write of a Power Brush glyph, several elements, and the debug probes, which still touch the legacy layer ([topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l).
- **Add Component crash on a glyph with no layer (612–619):** fixed for one master in 0.127 / 0.48 (620, one run). Not fixed for multi-master fonts or a `create_glyph` reply with `layer_note`: avoid Add Component on such a glyph in a font with unsaved work ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §9).
- **No save question (S1, 460–472):** FontLab closes a font changed only through the tools without asking about saving (it asks after a change made in its GUI), so closing loses that work silently; the chat reminder is the only warning ([topics/server-and-endpoints.md](topics/server-and-endpoints.md) §2).

## Resume here (session of 2026-11-09)

- **Components (P1.1), live 606–626:** one component, identity, offset and horizontal scale read `verified` ([topics/reading.md](topics/reading.md)); since 0.128 / 0.49 `get_glyph_outline` labels a component and names its source (624–626). The crash fix is live-checked (620–623). The code and these documents are uncommitted.
- **FontLab:** the test fonts are gone; every test needs a new disposable font.
- **Next:** (1) rotation and the other component transforms; (2) several components in one glyph; (3) open questions of open contours, each only with the user's OK: what FontLab does with them on export (a save test), quadratic; (4) **final polish for kerning** (the user's decision of 2026-11-04, for later): an exception over a class on a disposable copy of a real font; writes with two saved fonts open; multi-master, a design decision before any test.

## Next steps (the user's priority of 2026-11-01)

1. **Components are under way** (the user's choice of 2026-11-06); open contours and kerning polish wait: see "Resume here" above. Other candidates (none approved): `delete_glyph` and `set_glyph_unicode` after a Power Brush write; the review of legacy calls (goal 6 in [PROJECT.md](PROJECT.md); the table in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10), starting with `get_glyph_width` (legacy `glyph.width`, while the writes use `advanceWidth`) and `font.info` (it disagreed with Font Info, 298).
2. The **T-series**: T2, T3 and T4 are done. What is open in T5 is in [CHECKLIST.md](CHECKLIST.md) row 63; the candidates for several open fonts, none approved, are in [ROADMAP.md](ROADMAP.md) P0.5.
3. **S1** (proposed, none approved): say so in the reminder and the tool descriptions, or find out whether the API can mark a font as changed without saving it.
4. Candidates after that (none approved): P0.3 / P0.4, a create-font tool. Required by the user, not yet designed: P1.6, kerning group membership.

The next free test number is **627**; the numbers in use: [LIVE-TESTS.md](LIVE-TESTS.md). Large-glyph and very-large-read tests stay in the LAST block.

## Contradictions and watch points

- Between the documents and the code: none known (versions, md5 and tests checked 2026-11-09 against listener 0.128 / server 0.49; tools and the main routes checked 2026-11-06, none added since; ARCHITECTURE's "the path never leaves the listener" corrected after test 273).
- Open watch points (seen, not yet explained or settled): **19**, in [WATCH-POINTS.md](WATCH-POINTS.md).
