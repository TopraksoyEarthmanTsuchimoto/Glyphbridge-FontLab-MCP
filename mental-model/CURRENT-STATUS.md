Last verified: 2026-11-03 against the working tree after c39459b (listener v0.110, server v0.36; tests PASS, deployed copy identical)

# Current status

## Versions and identity

| Part | Version | md5 (as committed) |
|---|---|---|
| listener `glyphbridge_fontlab_mcp_listener.py` | `VERSION = "0.110"` | `6f432f56af289d9a54b0e4c21a340648` (373,526 bytes) |
| server `glyphbridge_mcp_server.py` | `SERVER_VERSION = "0.36"`, `MIN_LISTENER_VERSION` (0, 82) | `ce2c67321b49f6f3798bf51a9a4b90d9` (155,383 bytes) |
| tests | 4 harnesses | PASS at **2186 + 58 + 90 + 768** lines |

`get_kerning` needs listener 0.104 (server 0.33). What each release changed: [CHANGELOG.md](CHANGELOG.md).

## Environment (verified 2026-11-01)

The founding developer has moved the project to a new Windows 11 PC and to this repository on November 1st 2026. This change has set the project environment as:
- Python **3.15.2**, with `mcp` **2.2.0** in the repository `venv`.
- FontLab **8.9.5** (the earlier work was on 8.4.2).
- The MCP connection works from **Claude Code** and from the **Claude Desktop chat**.

On 2026-11-01 `--check` gave four `[OK]` lines, and the tests passed on this machine with the deployed listener copy identical; re-checked at the end of that day with listener 0.104 / server 0.33 (Arial open).

Setup steps: [RUNBOOK.md](RUNBOOK.md).

## What works (live-proven in FontLab)

- **Reading:** outlines with element transforms (scale, offset, slant), cubic and quadratic outlines, Power Brush output, widths, sidebearings, the stale-view fallback. → [topics/reading.md](topics/reading.md)
- **Writing:** create and delete glyphs (name safety rules), Unicode set and clear, width, sidebearings, closed straight and cubic contours into an empty glyph, auto sync after every modern write, also with the glyph's editor tab open (T3, 257). → [topics/geometry.md](topics/geometry.md), [topics/names-unicode.md](topics/names-unicode.md), [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **`.notdef`** check and one-time dialog. → [topics/notdef.md](topics/notdef.md)
- **Activity log** in FontLab's OUTPUT panel: one line per change and one summary of reads, naming the client (`local-agent-mode`) and, once, the program that started the server (`| CLAUDE`); live tests 190, 191, 225–229, 236–242. Stub-tested only: REFUSED / FAILED lines, unsynced or warned results, the `writes` / `off` modes, the flush at `/shutdown`. → [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §4
- **No font open** (P0.2): with the only font closed in a running FontLab, `fontlab_status` gave `font_open: false`, and a width read and a create were refused; Arial reopened read as before (227, 228). In a freshly started FontLab (K13, 244) all 8 read routes answered `open: false`, the placeholder glyph `Paper` included, with no dialog. Not seen live: the other write tools (stub only). → [topics/fonts-and-sync.md](topics/fonts-and-sync.md)
- **Kerning** (K1–K14 and K16, 2026-11-01 to 2026-11-03; each test in [LIVE-TESTS.md](LIVE-TESTS.md)): **since 0.104 / 0.33** `get_kerning` reads the current master's table, reports each value's `source`, and needs exactly one open font (live 219–223). Proven: the listener route by GET and POST (K2, K3); the agent reading only the pairs asked for (K4) and asking before more than 250 (K8); `text` mode equal to the KERNING panel (K5) and its special characters (K6); errors never read as zero (K7); an exception winning over its class value (K9); a FontLab text line applying the same kerning (K10); Arial's `kern` feature (decompiled GPOS) equal to the table in 20 pairs (K11); a `.vfc` opened from a file, with an empty table and panel (K12); 250 and 2,000 pairs read in under 0.1 s each on Arial, FontLab responsive (K14); `+`, `&`, `%`, a space and `é` arrive intact by every route (K16). → [topics/kerning.md](topics/kerning.md) §10, §11

## Fixed defects

- **P0.2**, tools answering for a placeholder font when no font is open, is fixed in listener 0.105 (227).
- **Kerning defects A and B** (GUI-made kerning read as 0; a class named like a glyph read instead of the exception; found 2026-11-01, tests 169–176) are fixed in listener 0.104 / server 0.33 and live-checked (219–223). Details: [topics/kerning.md](topics/kerning.md) §9–§10.

## Not proven or not built

- Not built: components, open contours, multi-master fonts, several shapes per glyph, editing an existing outline, a create-font tool, saving workflows. See [ROADMAP.md](ROADMAP.md).
- `finish_changes` through the Desktop chat (T2, 253–255): one request with three verified writes ended with one bold reminder, a read-only request with none; FontLab showed LSB 50, width 400, RSB 50 as reported.
- Open scenarios: [CHECKLIST.md](CHECKLIST.md).

## Next steps (the user's priority of 2026-11-01)

1. **The K-series is done** ([LIVE-TESTS.md](LIVE-TESTS.md)); K15 was dropped ([DECISIONS.md](DECISIONS.md)); P0.8 is done.
2. Next, the **T-series**: T4 (an existing glyph with legacy layers); T2 and T3 are done.
3. Candidates after that (none approved): P0.3 / P0.4, a create-font tool; P1.1, components. Required by the user, not yet designed: P1.6, kerning group membership.

Tests 155 to 258 are used (K-series, P0.8 research and checks, 189–190 the v0.101 check and the activity log, 225–229 the checks of 0.105 / 0.106, 158 and 230–235 K11, 236–242 the sender tests, 243 K12(b), 244 K13, 245–246 K14, 247–252 K16, 253–255 T2, 256–258 T3; details in [LIVE-TESTS.md](LIVE-TESTS.md) and [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §4); the next free test number is **259**. Large-glyph and very-large-read tests stay in the LAST block.

## Contradictions and watch points

- **Arial differs on this PC.** It has **4651** glyphs; the old PC had 4548. It may be a different Arial version, but its kerning is unchanged: K2 read `table_size` 1370 and the same 13 pair values as the old probes.
- An agent may answer a read from an earlier reply instead of reading (T2, 254: the width, and it said so); asked to read "now", it read.
- Agents guessed whether a kerning value comes from a direct pair or a class (K5; K8: missing pairs "may sit in GPOS lookups"). Since 0.104 / 0.33 the reply names the `source`, and in test 223 the Desktop agent reported it without guessing. Watch it in later agent-level tests.
- Arial's `kern` feature has 1,417 `pos` lines, its kerning table 1,370 entries: the difference is unexplained (K11).
- **New, stricter:** `get_kerning` needs exactly one open font (test 221) until T5 shows which package belongs to the current font.
- **The client name is the app's own claim** and names the app, not the model; both Claude apps send the same name. The launcher does not tell them apart on this PC either: the Desktop app starts the servers for both (237–238); a file name is not proof. A name with non-ASCII characters would print as such in the OUTPUT panel: not seen, not tested in FontLab.
- The change counter showed 9 in a Claude Code session that made no changes, also after a full FontLab restart, and 20 at the start of a later one: the server process outlived the earlier sessions (inferred). After a full Claude Desktop restart `fontlab_status` showed no counter (a fresh server; consistent with that).
- FontLab 8.9.5 versus 8.4.2: no difference seen. Writes on 8.9.5: only `create_glyph`, `draw_polygon`, `set_glyph_width` and `set_glyph_sidebearings` on new glyphs of new fonts (K9 setup, tests 190, 253), all verified, and a declined `delete_glyph` (190).
