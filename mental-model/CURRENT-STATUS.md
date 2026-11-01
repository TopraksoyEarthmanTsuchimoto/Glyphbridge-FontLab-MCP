Last verified: 2026-11-01 against commit 8d464b0

# Current status

## Versions and identity

| Part | Version | md5 (as committed) |
|---|---|---|
| listener `glyphbridge_fontlab_mcp_listener.py` | `VERSION = "0.95"` | `873913621428a2c4e3d1f8a43c02be27` |
| server `glyphbridge_mcp_server.py` | `SERVER_VERSION = "0.31"`, `MIN_LISTENER_VERSION` (0, 82) | `dedcc8366021f9fdfd20cd2aaa16d48f` |
| tests | 4 harnesses | PASS at **1489 + 58 + 90 + 668** lines |

Both md5s equal the identity recorded at the v11 hand-off. No code has changed since then.

## Environment (verified 2026-11-01)

The project moved to a new Windows 11 PC and to this repository:
- Python **3.15.2**, with `mcp` **2.2.0** in the repository `venv`.
- FontLab **8.9.5** (the earlier work was on 8.4.2).
- The MCP connection works from **Claude Code** and from the **Claude Desktop chat**.

Live checks done today:
- `/version` answered 0.95.
- `--check` gave four `[OK]` lines.
- `fontlab_status` gave server 0.31, listener 0.95, no `compatibility_note`, and `get_kerning` was listed.
- The tests ran on the new machine for the first time and passed: 1489 + 58 + 90 + 668 lines, the deployed listener copy identical.

Setup steps: [RUNBOOK.md](RUNBOOK.md).

## What works (live-proven in FontLab)

- **Reading:** outlines with element transforms (scale, offset, slant), cubic and quadratic outlines, Power Brush output, widths, sidebearings, the stale-view fallback. → [topics/reading.md](topics/reading.md)
- **Writing:** create and delete glyphs (name safety rules), Unicode set and clear, width, sidebearings, closed straight and cubic contours into an empty glyph, auto sync after every modern write. → [topics/geometry.md](topics/geometry.md), [topics/names-unicode.md](topics/names-unicode.md), [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **`.notdef`** check and one-time dialog. → [topics/notdef.md](topics/notdef.md)
- **Kerning:** the FontLab call `font.kerning.get` was proven on Arial by probes. **The `get_kerning` tool itself has not yet been run live**, only stub- and mutation-tested. → [topics/kerning.md](topics/kerning.md)

## Not proven or not built

- Not built: components, open contours, multi-master fonts, several shapes per glyph, editing an existing outline, a create-font tool, saving workflows. See [ROADMAP.md](ROADMAP.md).
- Not run live: the save-reminder flow (`finish_changes`).
- Open scenarios: [CHECKLIST.md](CHECKLIST.md).

## Next steps (the user's priority of 2026-10-27, still in force)

0. **Housekeeping build first** (listener 0.96, server 0.32): move the docstring version history out of both scripts ([DECISIONS.md](DECISIONS.md)). To be proposed in detail and built only after the approval phrase.
1. **K-series of kerning live tests** ([LIVE-TESTS.md](LIVE-TESTS.md)). K1 is done. Suggested order: K2, K3, K4, K5, K7, K6, K8, K9, K10, K11, K12, K13, K14, K16. K15 goes in the last block.
2. Then the **T-series**: T2 (`finish_changes` live), T3 (an open editor tab during a write, highest value), T4.
3. Candidates after that (none approved): P0.2, a `CountFonts()`-based "font open" check for every route; P0.3 / P0.4, a create-font tool; P1.1, components.

The next free test number is **155**. Large-glyph and very-large-read tests stay in the LAST block.

## Contradictions and watch points

- **Arial differs on this PC.** It has **4651** glyphs; the old PC had 4548. It may be a different Arial version, so the K2 expectations (`table_size` 1370, the pair values) must be re-checked rather than assumed.
- FontLab 8.9.5 versus 8.4.2: no difference seen in today's read-only checks. Write behaviour has not been re-tested on 8.9.5.
- Two listener comments still point to "the milestone summary" (code text only; [ROADMAP.md](ROADMAP.md) P5).
