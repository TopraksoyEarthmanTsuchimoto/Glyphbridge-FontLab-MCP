Last verified: 2026-11-03 against the working tree after commit 2f78fb0 (listener v0.118, server v0.41; tests PASS, deployed copy identical; not yet committed)

# Current status

## Versions and identity

| Part | Version | md5 (as committed) |
|---|---|---|
| listener `glyphbridge_fontlab_mcp_listener.py` | `VERSION = "0.118"` | `1d89cde4903b98846fc16c42281f32c7` (391,429 bytes) |
| server `glyphbridge_mcp_server.py` | `SERVER_VERSION = "0.41"`, `MIN_LISTENER_VERSION` (0, 82) | `859ec496012e917a31d78e618754eb43` (164,288 bytes) |
| tests | 4 harnesses | PASS at **2328 + 58 + 90 + 825** lines |

`get_kerning` needs listener 0.104 (server 0.33); with several fonts open, 0.112 / 0.37. The PostScript names from the font package need 0.118 / 0.41. What each release changed: [CHANGELOG.md](CHANGELOG.md).

## Environment (verified 2026-11-01)

The founding developer has moved the project to a new Windows 11 PC and to this repository on November 1st 2026. This change has set the project environment as:
- Python **3.15.2**, with `mcp` **2.2.0** in the repository `venv`.
- FontLab **8.9.5** (the earlier work was on 8.4.2).
- The MCP connection works from **Claude Code** and from the **Claude Desktop chat**.

On 2026-11-01 `--check` gave four `[OK]` lines, and the tests passed on this machine with the deployed listener copy identical; re-checked at the end of that day with listener 0.104 / server 0.33 (Arial open).

Setup steps: [RUNBOOK.md](RUNBOOK.md).

## What works (live-proven in FontLab)

- **Reading:** outlines with element transforms (scale, offset, slant), cubic and quadratic outlines, Power Brush output, widths, sidebearings, the stale-view fallback. → [topics/reading.md](topics/reading.md)
- **Writing:** create and delete glyphs (name safety rules), Unicode set and clear, width, sidebearings, closed straight and cubic contours into an empty glyph, auto sync after every modern write, also with the glyph's editor tab open (T3, 257) and on an existing glyph with a legacy layer, in a font opened from a file (T4, 145a–g, 259, 260: a plain contour and a Power Brush shape). → [topics/geometry.md](topics/geometry.md), [topics/names-unicode.md](topics/names-unicode.md), [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **Save reminder:** `finish_changes` through the Desktop chat (T2, 253–255): one request with three verified writes ended with one bold reminder, a read-only request with none; FontLab showed LSB 50, width 400, RSB 50 as reported.
- **`.notdef`** check and one-time dialog. → [topics/notdef.md](topics/notdef.md)
- **Activity log** in FontLab's OUTPUT panel: one line per change and one summary of reads, naming the client (`local-agent-mode`) and, once, the program that started the server (`| CLAUDE`); live tests 190, 191, 225–229, 236–242. Stub-tested only: REFUSED / FAILED lines, unsynced or warned results, the `writes` / `off` modes, the flush at `/shutdown`. → [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §4
- **No font open** (P0.2): with the only font closed in a running FontLab, `fontlab_status` gave `font_open: false`, and a width read and a create were refused; Arial reopened read as before (227, 228). In a freshly started FontLab (K13, 244) all 8 read routes answered `open: false`, the placeholder glyph `Paper` included, with no dialog. Not seen live: the other write tools (stub only). → [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **Several fonts open** (T5, 262–284): `CurrentFont()` and the current package follow the font window in front; `get_kerning` reads that font with 2 and 3 fonts open, matched by path, and refuses an unsaved one. Since 0.113 / 0.38 every reply names its font and reports a switched font window (269–272). Create, draw, width, sidebearings and Unicode writes change only the font in front, across window switches, with two saved fonts of the same name (273–281); since server 0.39 an error reply names a switch as well (277, fixed and live-checked in 282–284). With two new unsaved fonts (285–290; FontLab names the second "Unnamed1"), `draw_path` and `delete_glyph` changed only the font in front; drawing into a brand-new font's first glyph is refused while several fonts are open (288); the goal is that every operation works with several fonts ([PROJECT.md](PROJECT.md)). → [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **Kerning** (K1–K14 and K16, 2026-11-01 to 2026-11-03, each test in [LIVE-TESTS.md](LIVE-TESTS.md)): **since 0.104 / 0.33** `get_kerning` reads the current master's table and reports each value's `source` (live 219–223); with several fonts open it reads the font in front, matched by path, and names it (0.112 / 0.37, 265–268). Proven: GET and POST, the agent reading only the pairs it needs and asking above 250, `text` mode equal to the KERNING panel with its special characters, errors never read as zero, an exception winning over its class, a FontLab text line and Arial's `kern` feature agreeing with the table, an empty table, timings up to 2,000 pairs. → [topics/kerning.md](topics/kerning.md) §10, §11

- **Font names** (291–302): FontLab keeps the names Font Info shows in the font package (`psn`, `ffn`, `tfn`, `tsn`, `sgn`); the legacy `font.info` the tools read before can disagree (298). Since listener 0.118 `/font/current` reads the package when it is matched to the font (302), and says why when it is not (301). → [topics/fonts-and-sync.md](topics/fonts-and-sync.md)

## Fixed defects

- **P0.2**, tools answering for a placeholder font when no font is open, is fixed in listener 0.105 (227).
- **Kerning defects A and B** (GUI-made kerning read as 0; a class named like a glyph read instead of the exception; found 2026-11-01, tests 169–176) are fixed in listener 0.104 / server 0.33 and live-checked (219–223). Details: [topics/kerning.md](topics/kerning.md) §9–§10.

## Not proven or not built

- Not built: components, open contours, multi-master fonts, several shapes per glyph, editing an existing outline, a create-font tool, saving workflows. See [ROADMAP.md](ROADMAP.md).
- Built and stub-tested, not yet seen live: the delete dialog naming the client and the font (listener 0.114), the save shortcut read from the system (server 0.40), the PostScript names from the package in `get_current_font` (server 0.41). They need a full Claude Desktop restart.
- Open scenarios: [CHECKLIST.md](CHECKLIST.md).

## Next steps (the user's priority of 2026-11-01)

1. **The K-series is done** ([LIVE-TESTS.md](LIVE-TESTS.md)); K15 was dropped ([DECISIONS.md](DECISIONS.md)); P0.8 is done.
2. The **T-series**: T2, T3 and T4 are done; T5 is done for `get_kerning` (0.112 / 0.37), for replies naming their font (0.113 / 0.38), for five write tools (273–281), and for `draw_path` and `delete_glyph` (288, 290). First, after the restart: the live checks of 0.114 / 0.40 / 0.41. Candidates for several open fonts, none approved: whether `fontlab_status` should keep sending the font's full path, an `expected_font` check on writes, per-font memory ([ROADMAP.md](ROADMAP.md) P0.5).
3. Candidates after that (none approved): P0.3 / P0.4, a create-font tool; P1.1, components. Required by the user, not yet designed: P1.6, kerning group membership.

The next free test number is **303**; the numbers in use: [LIVE-TESTS.md](LIVE-TESTS.md). Large-glyph and very-large-read tests stay in the LAST block.

## Contradictions and watch points

- Between the documents and the code: none known (checked 2026-11-03; ARCHITECTURE's "the path never leaves the listener" corrected after test 273).
- Open watch points (seen, not yet explained or settled): **13**, in [WATCH-POINTS.md](WATCH-POINTS.md).
