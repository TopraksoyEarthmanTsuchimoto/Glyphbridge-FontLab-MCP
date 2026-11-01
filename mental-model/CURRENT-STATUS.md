Last verified: 2026-11-01 against the working tree after 80ad76e (listener v0.104 and server v0.33 not committed yet)

# Current status

## Versions and identity

| Part | Version | md5 (as committed) |
|---|---|---|
| listener `glyphbridge_fontlab_mcp_listener.py` | `VERSION = "0.104"` | `6154a82b3eb421e341261250a11b20e9` (356,250 bytes) |
| server `glyphbridge_mcp_server.py` | `SERVER_VERSION = "0.33"`, `MIN_LISTENER_VERSION` (0, 82) | `9b7c56bf5ed01e97ae3f952a8852ded0` (146,560 bytes) |
| tests | 4 harnesses | PASS at **1928 + 58 + 90 + 701** lines |

v0.97 to v0.100 only add research probes (`/debug/trypkgkern`, gated; `/debug/moddir`, names only); no product route changed. v0.101 fixes the traceback after `/shutdown` and two OUTPUT lines; live-checked as test 189. v0.102 adds the activity log; v0.103 adds the research probe `/debug/trykerngroups`; v0.104 / server v0.33 fix `get_kerning` ([CHANGELOG.md](CHANGELOG.md)); `get_kerning` needs listener 0.104. `fontlab_status` reads 0.102 as newer than 0.95 (no `compatibility_note`).

## Environment (verified 2026-11-01)

The project moved to a new Windows 11 PC and to this repository:
- Python **3.15.2**, with `mcp` **2.2.0** in the repository `venv`.
- FontLab **8.9.5** (the earlier work was on 8.4.2).
- The MCP connection works from **Claude Code** and from the **Claude Desktop chat**.

On 2026-11-01 `--check` gave four `[OK]` lines, and the tests passed on this machine with the deployed listener copy identical; re-checked at the end of that day with listener 0.104 / server 0.33 (Arial open).

Setup steps: [RUNBOOK.md](RUNBOOK.md).

## What works (live-proven in FontLab)

- **Reading:** outlines with element transforms (scale, offset, slant), cubic and quadratic outlines, Power Brush output, widths, sidebearings, the stale-view fallback. → [topics/reading.md](topics/reading.md)
- **Writing:** create and delete glyphs (name safety rules), Unicode set and clear, width, sidebearings, closed straight and cubic contours into an empty glyph, auto sync after every modern write. → [topics/geometry.md](topics/geometry.md), [topics/names-unicode.md](topics/names-unicode.md), [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **`.notdef`** check and one-time dialog. → [topics/notdef.md](topics/notdef.md)
- **Activity log** in FontLab's OUTPUT panel (test 190, a new font): 11 changes and their reads gave 14 lines exactly as predicted, including the run summaries, the 10 s idle flush, a declined delete and a refused width. Probe lines live in test 191 (13 lines for 13 gated requests). Stub-tested only: REFUSED / FAILED lines, unsynced or warned results, the `writes` / `off` modes, the flush at `/shutdown`. → [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §4
- **Kerning:** the FontLab call `font.kerning.get` was proven on Arial by probes. The listener route `/kerning/pairs` was run live on 2026-11-01: GET (K2) gave all 13 values as predicted, and POST (K3) gave identical answers. The `get_kerning` tool ran live through the Claude Desktop chat (K4): one call, three pairs, correct values. In `text` mode all 10 pairs of K5 equal FontLab's KERNING panel; the zeros are conclusive for the kerning table (166–167); K10 checks text rendering. Bad requests are refused live with specific messages, and an unknown glyph is reported as unreadable, never as zero (K7). Special characters in `text` (K6): a space and `é` map to the right glyphs, and a missing character gives an error, never a zero. The 250-pair approval flow works at agent level (K8): the agent asked before reading 324 and 251 pairs and read 250 without asking. An exception wins over its class value (K9). **Since 0.104 / 0.33** it reads the current master's table, reports each value's `source`, and needs exactly one open font; live tests 219–223 (the GUI-kerned test font, a class edit, two fonts refused, Arial's 13 pairs unchanged, the Desktop agent reporting sources without guessing). → [topics/kerning.md](topics/kerning.md) §10

## Fixed defects

- **Kerning defects A and B** (GUI-made kerning read as 0; a class named like a glyph read instead of the exception; found 2026-11-01, tests 169–176) are fixed in listener 0.104 / server 0.33 and live-checked (219–223). Details: [topics/kerning.md](topics/kerning.md) §9–§10.

## Not proven or not built

- Not built: components, open contours, multi-master fonts, several shapes per glyph, editing an existing outline, a create-font tool, saving workflows. See [ROADMAP.md](ROADMAP.md).
- `finish_changes` ran live once through Claude Code (9 changes counted correctly); the agent-level check through the Desktop chat (T2) is open.
- Open scenarios: [CHECKLIST.md](CHECKLIST.md).

## Next steps (the user's priority of 2026-11-01)

1. **The rest of the K-series** ([LIVE-TESTS.md](LIVE-TESTS.md)). K1 to K9 and P0.8 are done. Suggested order: K10, K11, K12, K13, K14, K16. K15 goes in the last block.
2. Then the **T-series**: T2 (`finish_changes` live), T3 (an open editor tab during a write, highest value), T4.
3. Candidates after that (none approved): P0.2, a `CountFonts()`-based "font open" check for every route; P0.3 / P0.4, a create-font tool; P1.1, components. Required by the user, not yet designed: P1.6, kerning group membership.

Tests 155 to 157 and 159 to 223 are used (K2, K3, K7 with 157b, K6, K8, the panel filter, K9, P0.8 probes, 189 the v0.101 check, 190 the activity log, 191–218 P0.8 research, 219–223 the P0.8 live checks); 158 is reserved for A7, so the next free test number is **224**. Large-glyph and very-large-read tests stay in the LAST block.

## Contradictions and watch points

- **Arial differs on this PC.** It has **4651** glyphs; the old PC had 4548. It may be a different Arial version, but its kerning is unchanged: K2 read `table_size` 1370 and the same 13 pair values as the old probes.
- Agents guessed whether a kerning value comes from a direct pair or a class (K5; K8: missing pairs "may sit in GPOS lookups"). Since 0.104 / 0.33 the reply names the `source`, and in test 223 the Desktop agent reported it without guessing. Watch it in later agent-level tests.
- **New, stricter:** `get_kerning` needs exactly one open font (test 221) until T5 shows which package belongs to the current font.
- **P0.2 seen live on 8.9.5** (2026-11-01): with no font open, `fontlab_status` gave `font_open: true`, empty names and `path: null`. After closing the only font in a running FontLab (later that day) it correctly gave `font_open: false`; the conditions of the wrong answer are not known.
- The change counter showed 9 in a Claude Code session that made no changes, also after a full FontLab restart, and 20 at the start of a later one: the server process outlived the earlier sessions (inferred). After a full Claude Desktop restart `fontlab_status` showed no counter (a fresh server; consistent with that).
- FontLab 8.9.5 versus 8.4.2: no difference seen. Writes on 8.9.5: only `create_glyph`, `draw_polygon` and `set_glyph_width` on new glyphs of a new font (K9 setup, test 190), all verified and synced, and a declined `delete_glyph` (190).
