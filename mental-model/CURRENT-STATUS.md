Last verified: 2026-11-03 against the working tree after 40bfd0d (listener v0.110, server v0.36; tests PASS, deployed copy identical)

# Current status

## Versions and identity

| Part | Version | md5 (as committed) |
|---|---|---|
| listener `glyphbridge_fontlab_mcp_listener.py` | `VERSION = "0.110"` | `6f432f56af289d9a54b0e4c21a340648` (373,526 bytes) |
| server `glyphbridge_mcp_server.py` | `SERVER_VERSION = "0.36"`, `MIN_LISTENER_VERSION` (0, 82) | `ce2c67321b49f6f3798bf51a9a4b90d9` (155,383 bytes) |
| tests | 4 harnesses | PASS at **2186 + 58 + 90 + 768** lines |

`get_kerning` needs listener 0.104 (server 0.33). v0.105 / 0.106 (server 0.34) answer "no font open" on every product route (P0.2) and name the client in the activity log; v0.107 / 0.108 add the K11 probe `/debug/features`; v0.109 / 0.35 drop the guessed `unknown agent` and name the program that started the server (live 237–239); v0.110 / 0.36 show it briefly (`local-agent-mode | CLAUDE`; live 240–242) ([CHANGELOG.md](CHANGELOG.md)).

## Environment (verified 2026-11-01)

The founding developer has moved the project to a new Windows 11 PC and to this repository on November 1st 2026. This change has set the project environment as:
- Python **3.15.2**, with `mcp` **2.2.0** in the repository `venv`.
- FontLab **8.9.5** (the earlier work was on 8.4.2).
- The MCP connection works from **Claude Code** and from the **Claude Desktop chat**.

On 2026-11-01 `--check` gave four `[OK]` lines, and the tests passed on this machine with the deployed listener copy identical; re-checked at the end of that day with listener 0.104 / server 0.33 (Arial open).

Setup steps: [RUNBOOK.md](RUNBOOK.md).

## What works (live-proven in FontLab)

- **Reading:** outlines with element transforms (scale, offset, slant), cubic and quadratic outlines, Power Brush output, widths, sidebearings, the stale-view fallback. → [topics/reading.md](topics/reading.md)
- **Writing:** create and delete glyphs (name safety rules), Unicode set and clear, width, sidebearings, closed straight and cubic contours into an empty glyph, auto sync after every modern write. → [topics/geometry.md](topics/geometry.md), [topics/names-unicode.md](topics/names-unicode.md), [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **`.notdef`** check and one-time dialog. → [topics/notdef.md](topics/notdef.md)
- **Activity log** in FontLab's OUTPUT panel (test 190, a new font): 11 changes and their reads gave 14 lines exactly as predicted, including the run summaries, the 10 s idle flush, a declined delete and a refused width. Probe lines live in test 191 (13 lines for 13 gated requests). Since 0.105 each line names the client as the app sends it: Claude Code and the Desktop chat both send `local-agent-mode-glyphbridge-fontlab`, shown as `local-agent-mode` since 0.106 (tests 225, 226, 229); reads answered "no font open" are listed apart (227). Test 236: a request without a client name (`curl`) was shown as `unknown agent`, and a summary carries the time it is printed. Tests 237–239 (0.109): the chat and the Code tab both go through servers the Desktop app starts; 240–242 (0.110): `| CLAUDE` as predicted. Stub-tested only: REFUSED / FAILED lines, unsynced or warned results, the `writes` / `off` modes, the flush at `/shutdown`. → [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §4
- **No font open** (P0.2, test 227): with the only font closed in a running FontLab, `fontlab_status` gave `font_open: false`, and a width read and a create were refused; Arial reopened read as before (228). Not seen live: a freshly started FontLab, the other write tools (stub only). → [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **Kerning:** the FontLab call `font.kerning.get` was proven on Arial by probes. The listener route `/kerning/pairs` was run live on 2026-11-01: GET (K2) gave all 13 values as predicted, and POST (K3) gave identical answers. The `get_kerning` tool ran live through the Claude Desktop chat (K4): one call, three pairs, correct values. In `text` mode all 10 pairs of K5 equal FontLab's KERNING panel; the zeros are conclusive for the kerning table (166–167); a FontLab text line applies the same kerning as the tool for AV, ÁV, To and Type (K10, 224). Bad requests are refused live with specific messages, and an unknown glyph is reported as unreadable, never as zero (K7). Special characters in `text` (K6): a space and `é` map to the right glyphs, and a missing character gives an error, never a zero. The 250-pair approval flow works at agent level (K8): the agent asked before reading 324 and 251 pairs and read 250 without asking. An exception wins over its class value (K9). **Since 0.104 / 0.33** it reads the current master's table, reports each value's `source`, and needs exactly one open font; live tests 219–223 (the GUI-kerned test font, a class edit, two fonts refused, Arial's 13 pairs unchanged, the Desktop agent reporting sources without guessing). **K11** (158, 230–235): Arial's `kern` feature is FontLab's decompiled GPOS, and all 20 pairs compared equal the table. → [topics/kerning.md](topics/kerning.md) §10, §11

## Fixed defects

- **P0.2**, tools answering for a placeholder font when no font is open, is fixed in listener 0.105 (227).
- **Kerning defects A and B** (GUI-made kerning read as 0; a class named like a glyph read instead of the exception; found 2026-11-01, tests 169–176) are fixed in listener 0.104 / server 0.33 and live-checked (219–223). Details: [topics/kerning.md](topics/kerning.md) §9–§10.

## Not proven or not built

- Not built: components, open contours, multi-master fonts, several shapes per glyph, editing an existing outline, a create-font tool, saving workflows. See [ROADMAP.md](ROADMAP.md).
- `finish_changes` ran live once through Claude Code (9 changes counted correctly); the agent-level check through the Desktop chat (T2) is open.
- Open scenarios: [CHECKLIST.md](CHECKLIST.md).

## Next steps (the user's priority of 2026-11-01)

1. **The rest of the K-series** ([LIVE-TESTS.md](LIVE-TESTS.md)). K1 to K11 and P0.8 are done. Suggested order: K12, K13, K14, K16. K15 goes in the last block.
2. Then the **T-series**: T2 (`finish_changes` live), T3 (an open editor tab during a write, highest value), T4.
3. Candidates after that (none approved): P0.3 / P0.4, a create-font tool; P1.1, components. Required by the user, not yet designed: P1.6, kerning group membership.

Tests 155 to 242 are used (K-series, P0.8 research and checks, 189–190 the v0.101 check and the activity log, 225–229 the checks of 0.105 / 0.106, 158 and 230–235 K11, 236–242 the sender tests; details in [LIVE-TESTS.md](LIVE-TESTS.md) and [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §4); the next free test number is **243**. Large-glyph and very-large-read tests stay in the LAST block.

## Contradictions and watch points

- **Arial differs on this PC.** It has **4651** glyphs; the old PC had 4548. It may be a different Arial version, but its kerning is unchanged: K2 read `table_size` 1370 and the same 13 pair values as the old probes.
- Agents guessed whether a kerning value comes from a direct pair or a class (K5; K8: missing pairs "may sit in GPOS lookups"). Since 0.104 / 0.33 the reply names the `source`, and in test 223 the Desktop agent reported it without guessing. Watch it in later agent-level tests.
- Arial's `kern` feature has 1,417 `pos` lines, its kerning table 1,370 entries: the difference is unexplained (K11).
- **New, stricter:** `get_kerning` needs exactly one open font (test 221) until T5 shows which package belongs to the current font.
- **The client name is the app's own claim** and names the app, not the model; both Claude apps send the same name. The launcher does not tell them apart on this PC either: the Desktop app starts the servers for both (237–238); a file name is not proof. A name with non-ASCII characters would print as such in the OUTPUT panel: not seen, not tested in FontLab.
- The change counter showed 9 in a Claude Code session that made no changes, also after a full FontLab restart, and 20 at the start of a later one: the server process outlived the earlier sessions (inferred). After a full Claude Desktop restart `fontlab_status` showed no counter (a fresh server; consistent with that).
- FontLab 8.9.5 versus 8.4.2: no difference seen. Writes on 8.9.5: only `create_glyph`, `draw_polygon` and `set_glyph_width` on new glyphs of a new font (K9 setup, test 190), all verified and synced, and a declined `delete_glyph` (190).
