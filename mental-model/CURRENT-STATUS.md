Last verified: 2026-11-01 against commit f271d27

# Current status

## Versions and identity

| Part | Version | md5 (as committed) |
|---|---|---|
| listener `glyphbridge_fontlab_mcp_listener.py` | `VERSION = "0.100"` | `398eee2d807a25c466de6d30f056e372` (325,673 bytes; not yet committed) |
| server `glyphbridge_mcp_server.py` | `SERVER_VERSION = "0.32"`, `MIN_LISTENER_VERSION` (0, 82) | `7d8c99950725ddbd795ff9b26fd39e31` (144,054 bytes) |
| tests | 4 harnesses | PASS at **1616 + 58 + 90 + 668** lines |

v0.97 to v0.100 only add research probes (`/debug/trypkgkern`, gated; `/debug/moddir`, names only); no product route changed ([CHANGELOG.md](CHANGELOG.md)). v0.100 runs live; `fontlab_status` reads it as newer than 0.95 (no `compatibility_note`).

## Environment (verified 2026-11-01)

The project moved to a new Windows 11 PC and to this repository:
- Python **3.15.2**, with `mcp` **2.2.0** in the repository `venv`.
- FontLab **8.9.5** (the earlier work was on 8.4.2).
- The MCP connection works from **Claude Code** and from the **Claude Desktop chat**.

On 2026-11-01 `--check` gave four `[OK]` lines, and the tests passed on this machine with the deployed listener copy identical.

Setup steps: [RUNBOOK.md](RUNBOOK.md).

## What works (live-proven in FontLab)

- **Reading:** outlines with element transforms (scale, offset, slant), cubic and quadratic outlines, Power Brush output, widths, sidebearings, the stale-view fallback. → [topics/reading.md](topics/reading.md)
- **Writing:** create and delete glyphs (name safety rules), Unicode set and clear, width, sidebearings, closed straight and cubic contours into an empty glyph, auto sync after every modern write. → [topics/geometry.md](topics/geometry.md), [topics/names-unicode.md](topics/names-unicode.md), [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **`.notdef`** check and one-time dialog. → [topics/notdef.md](topics/notdef.md)
- **Kerning:** the FontLab call `font.kerning.get` was proven on Arial by probes. The listener route `/kerning/pairs` was run live on 2026-11-01: GET (K2) gave all 13 values as predicted, and POST (K3) gave identical answers. The `get_kerning` tool ran live through the Claude Desktop chat (K4): one call, three pairs, correct values. In `text` mode all 10 pairs of K5 equal FontLab's KERNING panel; the zeros are conclusive for the kerning table (166–167); K10 checks text rendering. Bad requests are refused live with specific messages, and an unknown glyph is reported as unreadable, never as zero (K7). Special characters in `text` (K6): a space and `é` map to the right glyphs, and a missing character gives an error, never a zero. The 250-pair approval flow works at agent level (K8): the agent asked before reading 324 and 251 pairs and read 250 without asking. An exception wins over its class value (K9). → [topics/kerning.md](topics/kerning.md)

## Known defects (live-proven 2026-11-01, not fixed)

- **A:** `get_kerning` reads the legacy `font.kerning`. Kerning made in FontLab's GUI lives in `flPackage.kerning(master)`, so a new font's kerning reads 0 and "no kerning at all" (tests 169–170).
- **B:** an exception on a glyph whose name is also a class name reads as the class value (174–176). Fix path found: `get(((a, False), (b, False)))` reads the exact glyph pair (−50, test 186), but does not resolve classes (188).

Both break the design rule. Details: [topics/kerning.md](topics/kerning.md) §9; fix: [ROADMAP.md](ROADMAP.md) P0.8.

## Not proven or not built

- Not built: components, open contours, multi-master fonts, several shapes per glyph, editing an existing outline, a create-font tool, saving workflows. See [ROADMAP.md](ROADMAP.md).
- `finish_changes` ran live once through Claude Code (9 changes counted correctly); the agent-level check through the Desktop chat (T2) is open.
- Open scenarios: [CHECKLIST.md](CHECKLIST.md).

## Next steps (the user's priority of 2026-11-01)

1. **P0.8, the fix of kerning defects A and B** ([ROADMAP.md](ROADMAP.md)). The probes are done (tests 168–188); next is a design proposal.
2. **The rest of the K-series** ([LIVE-TESTS.md](LIVE-TESTS.md)). K1 to K9 are done. Suggested order: K10, K11, K12, K13, K14, K16. K15 goes in the last block.
3. Then the **T-series**: T2 (`finish_changes` live), T3 (an open editor tab during a write, highest value), T4.
4. Candidates after that (none approved): P0.2, a `CountFonts()`-based "font open" check for every route; P0.3 / P0.4, a create-font tool; P1.1, components. Required by the user, not yet designed: P1.6, kerning group membership.

Tests 155 to 157 and 159 to 188 are used (K2, K3, K7 with 157b, K6, K8, the panel filter, K9, P0.8 probes); 158 is reserved for A7, so the next free test number is **189**. Large-glyph and very-large-read tests stay in the LAST block.

## Contradictions and watch points

- **Arial differs on this PC.** It has **4651** glyphs; the old PC had 4548. It may be a different Arial version, but its kerning is unchanged: K2 read `table_size` 1370 and the same 13 pair values as the old probes.
- Agents may guess whether a kerning value comes from a direct pair or a class: in K5 the agent said four direct pairs "suggests they come from the same class kerning". The reply does not say which. The same in K8 (163, 164): missing pairs "may sit in GPOS lookups". A line in the `get_kerning` agent instruction is a candidate (not approved).
- FontLab 8.9.5 versus 8.4.2: no difference seen. Writes on 8.9.5: only `create_glyph`, `draw_polygon` and `set_glyph_width` on new glyphs of a new font (K9 setup), all verified and synced.
