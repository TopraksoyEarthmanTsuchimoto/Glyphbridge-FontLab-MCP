# Architecture

## Two processes, one local link

```
AI app (Claude Desktop / Claude Code)
   │ MCP over stdio
glyphbridge_mcp_server.py      own venv, normal Python, MCP SDK v2 (mcp 2.2.0)
   │ HTTP + JSON, 127.0.0.1:8765 only
glyphbridge_fontlab_mcp_listener.py   inside FontLab 8 (embedded Python 3.11)
   │ FontLab Python API (legacy fgFont/fgGlyph + modern flGlyph/flLayer)
FontLab 8
```

1. **Listener** (`glyphbridge_fontlab_mcp_listener.py`, `VERSION` in the file). It is started by hand from FontLab's Scripting panel each session. It reports **raw FontLab facts only** and does not speak MCP.
   - FontLab gives background threads no CPU while it idles, so a `QTimer` polls a non-blocking socket every 25 ms on the main thread. Every `fontlab` call therefore runs on FontLab's main thread, and a long request keeps FontLab busy.
   - It imports `QMessageBox` from `PythonQt.QtGui`, falling back to `PythonQt.QtWidgets`.
   - While a FontLab dialog it opened is waiting for a click, nothing else is served, and other calls time out (live-verified).
   - It prints one short line per change, and a summary of reads, in FontLab's OUTPUT panel, built only from each request and its reply (v0.102), naming the client that sent it (v0.105) and, once per new client, the program that started the server (v0.109, `| CLAUDE` since v0.110): [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §4.
2. **Server** (`glyphbridge_mcp_server.py`, `SERVER_VERSION` in the file). A normal MCP server, launched over stdio by the AI app. It **never imports `fontlab`**. All interpretation lives here: curve rebuild, transform maths, verification, name rules, Unicode instructions, save-policy bookkeeping, and the `agent_instruction` texts.
   - `MIN_LISTENER_VERSION` is `(0, 82)`. Newer tools check the listener version they need before sending anything.
   - Request timeout: 5 s by default, longer for kerning reads and for dialogs that wait for a click.
   - Every request carries the app's own name and, read once at startup from the operating system, the file name of the program that started the server (`X-Glyphbridge-Client`, `X-Glyphbridge-Launcher`; v0.34, v0.35 / v0.36).
   - Every listener reply that used a font names it in three headers: family and style, a short hash of its path, and the number of open fonts (`X-Glyphbridge-Font`, `-Font-Key`, `-Fonts-Open`; v0.113 / v0.38). The server adds `font` and `fonts_open` to each tool reply, and `font_note` when several fonts are open or the font in front changed. These headers never carry the path; `fontlab_status` and `get_current_font` do report it (test 273).

Effect of the split: the AI app starts the server in its own Python with its own libraries. FontLab access stays in one small HTTP surface, so every FontLab call is easy to audit and can be tested with stubs.

## FontLab's two APIs and how Glyphbridge uses them

- **Legacy** objects (`fgFont`, `fgGlyph`, `fgLayer`) list glyphs, names, Unicode values and margins. They also provide `font.update()`.
- **Modern** objects (`flGlyph`, `flLayer`, `flShape`, `flPackage`) give the real element transforms, the drawing calls (`addContour`/`addShape`), `setSB` and `advanceWidth`, and the sync call `fontlab.Update(flGlyph)`.
- The bridge `fontlab.flGlyph(fgGlyph, fgFont)` leaks one native reference per construction. The listener therefore caches one wrapper per glyph and validates it before reuse: [topics/reading.md](topics/reading.md) §6.
- **Writes** go through the modern API. Right after each one the listener calls `Update(<flGlyph>)` (auto sync), so the legacy view catches up, and since 0.132 / 0.51 a verified, synced glyph write also tells FontLab it changed (`notifyChangesApplied`), so FontLab asks to save on close; since 0.133 / 0.53 a verified delete does the same through one surviving glyph, and since 0.134 / 0.54 a kerning write that changed an entry through a glyph of a changed pair; since 0.136 / 0.56 such a write also asks FontLab to refresh its KERNING panel (`notifyPackageContentUpdated`). A guard skips the legacy `font.update()` while any changed glyph might still be unsynced, because that call can throw unsynced work away: [topics/fonts-and-sync.md](topics/fonts-and-sync.md).
- **Reads** of a glyph with modern nodes use the modern layer only (listener 0.120): touching the legacy layer of a Power Brush glyph lets the next `font.update()` flatten it (F1, [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l). Glyphs without modern nodes are read from the legacy layer, cross-checked with the modern margins: [topics/reading.md](topics/reading.md). The PostScript names come from the font package, where FontLab keeps what Font Info shows; the legacy `font.info` can disagree (listener 0.118, [topics/fonts-and-sync.md](topics/fonts-and-sync.md)).
- **Modern first** (2026-11-04, [DECISIONS.md](DECISIONS.md)): a legacy call is used only where the modern one is missing or proven worse. The legacy calls still in use, and why, are listed in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10; replacing them is goal 6 in [PROJECT.md](PROJECT.md).
- Some FontLab objects crash FontLab natively when used the wrong way, for example indexing a native object. Those rules are in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md).

## Verification model

Each outline reply carries a status:
- `verified`: real transforms applied, and FontLab's bounding box and margins are reproduced within 0.05. On the modern route the vertical extent is checked against FontLab's own ink box, `inkBox()` (`y_extent_checked`, listener 0.121 / server 0.43).
- `calibrated`: transforms estimated from the bounding box.
- `unverified`: the coordinates are raw, and the reply says which coordinate space they are in.

On a glyph with components (server 0.50, plain offsets only), an outer box that fits with and without the transforms is settled element by element (`element_boxes_checked`), and a component found behind its source makes the read `unverified` (`source_in_step`): [topics/reading.md](topics/reading.md).

Every write is reported as successful only after a re-read agrees. Drawings are compared node by node (`nodes_match`). Details: [topics/reading.md](topics/reading.md) §4 and [topics/geometry.md](topics/geometry.md).

## Tools (server) and routes (listener)

| Area | Tools | Listener routes | Details |
|---|---|---|---|
| status, font | `fontlab_status`, `get_current_font`, `list_glyphs` | `/health`, `/version`, `/font/current`, `/font/glyphs` | [server-and-endpoints](topics/server-and-endpoints.md) |
| new font | `create_font` (server 0.60) | POST `/font/create` (listener 0.146) | [server-and-endpoints](topics/server-and-endpoints.md), [fonts-and-sync](topics/fonts-and-sync.md) §8k |
| reading | `get_glyph_outline`, `get_glyph_width`, `get_glyph_sidebearings` | `/glyph/outline`, `/glyph/width`, `/glyph/sidebearings` | [reading](topics/reading.md) |
| `.notdef` | `check_notdef` (+ automatic checks) | `/font/notdef`, `/font/notdef/warn` | [notdef](topics/notdef.md) |
| names, Unicode | `create_glyph`, `delete_glyph`, `check_glyph_unicode`, `set_glyph_unicode` | `/glyph/create`, `/glyph/delete`, `/glyph/unicode` | [names-unicode](topics/names-unicode.md) |
| geometry | `set_glyph_width`, `set_glyph_sidebearings`, `draw_polygon`, `draw_path` | `/glyph/width`, `/glyph/sidebearings`, `/glyph/polygon`, `/glyph/path` | [geometry](topics/geometry.md) |
| kerning | `get_kerning`, `set_kerning` | GET/POST `/kerning/pairs`, POST `/kerning/set` (the current master's table of the font in front; with several fonts open, matched by path) | [kerning](topics/kerning.md) |
| save policy | `finish_changes` | none (server bookkeeping) | [server-and-endpoints](topics/server-and-endpoints.md) §2 |
| research | none | `/debug/...` probes, gated by `go=yes` where they change anything | [server-and-endpoints](topics/server-and-endpoints.md) §3 |

**Confirmation and gating:**
- `delete_glyph` asks a Yes/No question in FontLab (default No).
- Reversible value writes are not gated, nor is `create_font`, which changes nothing that exists.
- Probes that construct objects or change UI state need `go=yes`.
- Environment switches: `GLYPHBRIDGE_PORT`, `GLYPHBRIDGE_MODERN`, `GLYPHBRIDGE_NOTDEF_WARN`.

## Repository layout

```
README.md, AGENTS.md, CLAUDE.md, .mcp.json
glyphbridge_mcp_server.py, glyphbridge_fontlab_mcp_listener.py   (root: tests read them from here)
tests/          run_all.py, four stub harnesses, expected_*.txt, README.md
mental-model/   all other documentation (map: MARKDOWN-MAP.md)
venv/           local only, ignored by git
```

The FontLab-side copy of the listener lives in `~/Documents/FontLab/FontLab 8/Scripts/`. `run_all.py` warns when it differs from the repository copy.

## Tests

- **The harnesses are print-based.** Each one runs the real scripts against stub `fontlab` / MCP modules and compares its output line by line with `expected_*.txt`. A change shows up as a diff, which is reviewed before `--update`.
- **Spy fakes and a static scan** guard the forbidden calls: no save, no whole-table kerning reads, no native subscripting.
- **Mutation testing:** new guard paths are mutation-tested. One asserted mutation at a time is applied to a throwaway copy, and the suite must fail. The runners are not committed.
- **Live tests** in FontLab are separate and recorded in [LIVE-TESTS.md](LIVE-TESTS.md) and [CHECKLIST.md](CHECKLIST.md).
