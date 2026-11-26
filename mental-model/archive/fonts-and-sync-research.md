# New fonts, unsynced layers, sync and GUI refresh: the research record

Moved from [topics/fonts-and-sync.md](../topics/fonts-and-sync.md) on 2026-11-26 (the user's choice: topic files get a word budget), word for word except for the link paths. Each passage stands under the heading of the section it came from, in its original order; the current facts and descriptions stayed in the topic file.

## 8k. Creating a new font (live-verified, listener 0.83 / 0.84)

- **An error names the switch too** (fixed in server 0.39, live 282–284): in server 0.38 a failed first call after a switch carried no font fields while the server had already recorded the new font, so the switch was reported nowhere (277). Since 0.39 the error message ends with the `font_note`.

**v10 additions to 8k:** re-confirmed in 139a: with no font open `CurrentFont()` is a placeholder `fgFont` (empty path and family, one glyph) while `CountFonts()` is 0; after `construct` the legacy family reads "Unnamed"; the first glyph's layer is `Regular` (`layer_name_source: "package master"`); drawing, sidebearings, width and the AUTO SYNC (8m) all work on such a font. Still no create-font tool.

## 8m. Automatic sync after modern writes (live-proven in the v10 session; listener 0.89, server 0.29)

**Evidence (one variable per run; new unsaved "Unnamed Regular" font unless stated; each run started from a restarted listener because the probe allows one call per `how` per run):**

- **140a, `fillFgData(False, False)`** on the unsynced glyph: returned an object, changed NOTHING (verdict stayed `at_risk`, legacy layers 0, outline `agree: false`), no harm (`layer_lost` false). Useless.
- **140b, `Update(<flGlyph>)`:** verdict `at_risk` -> `synced` in one call; legacy layers 0 -> 1 (1 contour, 4 nodes); `layer_lost` false; the next `/glyph/outline` read the legacy side directly (`agree: true`, `margins_agree: true`). No editor tab, no GUI action. Return value `None`.
- **141, sidebearings:** polygon, then `set_glyph_sidebearings(20, 30)` (advance 450), THEN `Update`: legacy outline x 20..420, margins 20 / 30 / 450, `margins_agree: true`, no `modern_outline` needed. Then `create_glyph` (its legacy `font.update()` ran, nothing was at risk): the synced glyph kept outline, margins and advance. The grid tile of the glyph appeared after that later `font.update()` (the tile stayed BLANK right after `Update` alone in 140b: FontLab repaints its own screen at its own events).
- **142, v0.89 on a font OPENED FROM A FILE** (the local test font `savedtestfont.vfc`, 6 glyphs, layer `test_font`, layer name taken from the other glyphs): `create` stl88, `draw_polygon`, `set_glyph_sidebearings(20, 30)`, `set_glyph_width(520)` on the same glyph (second and third sync of the same glyph), `create` stl89, `draw_polygon` stl89, `create` stl90: EVERY write reply carried `synced_with_fontlab: true` and `fontlab_sync: {attempted: true, verdict: synced, synced: true}`; the later creates ran their legacy refresh (nothing skipped); stl88 kept outline x 20..420 and margins 20 / 100 / 520, stl89 its outline. Screenshot: grid with 9 glyphs, thumbnails of the two drawn glyphs repainted.
- **143 (read-only):** see 8o.

**Tests (stubs):** listener cases 990-1008 (fakes for `Update`: syncs / no effect / raises / wipes / missing; `_AUTO_SYNC` off; polygon, path, sidebearings, modern width; legacy width route not synced; second edit of a synced glyph; create after a successful and after a failed sync; `_auto_sync` raising; two glyphs; no `UpdateAll`, no forbidden call, exactly one `upd(w)`, shipped default `True`; version) and server part 18 (18a to 18k). `m88_setup` (the `/debug/trymodern` tests) now sets `_AUTO_SYNC = False`, because those tests need a glyph that stays unsynced.

## 8o. Probe record of the v10 session (tests 137 to 143) and the new probe `/debug/trymodern`

| Test | What | Result |
|---|---|---|
| 137 | names only: `flPackage`, `flGlyph`, `flLayer`, `flWorkspace`, `fldir` (module names filtered by glyph / package / font / sync / update) | `fontlab` module names: `AllFonts`, `CountFonts`, `CurrentFont`, `CurrentGlyph`, `FontLayer`, `FontMetrics`, `GlyphComponent`, `GlyphInfoState`, `SetCurrentFont`, `SetCurrentGlyph`, `Update`, `UpdateActiveCanvas`, `UpdateAll`, `UpdateGlyphRect`, `flGlyph`, `flGlyphInfo`, `flPackage` (there is NO `flFont`). `flPackage` has `addGlyph`, `findName`, `glyphsCount`, `prepareFontGateData`; `flGlyph` has `fillFgData`, `updatedFgGlyphs`, `clearUpdateFgGlyphs`, `updateFgGlyph`, `ensureFgData`, `assignFontGateData` (never called) |
| 138 | docstrings of `Update`, `UpdateAll`, `UpdateGlyphRect`, `UpdateActiveCanvas` | the `Update` text quoted in 8m |
| 139a / 139b | v0.88 with NO font open at the start | `/debug/trymodern state` refused with "CountFonts() is 0" before a font existed; after `/debug/tryfont?stage=construct&go=yes` a font "Unnamed Regular" with one master `Regular`; first glyph layer from the package master (`layer_name_source: "package master"`); unsynced polygon: `at_risk`, legacy layers 0, `agree: false` with `modern_outline` attached; after ONE GUI action (open the glyph in an editor, back to the grid) and the next request: `synced`; then the stale-margins case of 8n |
| 140a / 140b | `fillFgData` / `Update(flGlyph)` | 8m |
| 141 | sidebearings, then `Update`, then a create | 8m |
| 142 | v0.89 on a font opened from a file | 8m |
| 143 | read-only reads of every glyph of that font | 8n; glyphs without a layer (`.notdef`, a created empty glyph) answer `modern_layer: false`; the probe's verdict for them is `lost`, which only means "no modern layer yet" |

**`/debug/trymodern?stage=state|call|create&name=N[&how=...][&go=yes]` (listener 0.88, gated like `/debug/trysync`: runs only when `CountFonts()` is exactly 1 and the workspace holds exactly one non-null package).**

- `stage=state` (read-only; default stage): legacy and modern state of the glyph, `updatedFgGlyphs()` ids (count + up to 50 ints), legacy / modern width, the guard verdict, the guard registry, the counters.
- `stage=call&how=Update_fgGlyph|Update_flGlyph|Update_all|fillFgData|prepareFontGateData&go=yes`: ONE call per `how` per listener run, counter raised BEFORE the call, only on a glyph in the guard registry (drawn / changed through the tools in this run; with v0.89 that is now only a glyph whose auto sync did not reach `synced`, or any glyph while `_AUTO_SYNC` is false). Reply: return value (type name), `call_error`, `before` / `after` snapshots, `layer_lost`, `synced_after`. Used live for `fillFgData` and `Update_flGlyph` only.
- `stage=create&name=N&go=yes`: `flGlyph()`, set `name`, `flPackage.addGlyph(glyph)`, read the name back with `findName`, NO update call; refuses if the name does not read back or already exists. **Never run live yet.**
- Never called by the probe: the assign family (`assignFgLayer`, `assignFontGateData`), `replaceGlyph`, `deleteGlyph`, `removeGlyph`, save, close, export, release, remove, `blockUpdate`, `unblockUpdate`. A static scan test checks the probe source.

## 8f. GUI refresh facts (CLOSED; do not re-research)

**Live end-to-end check (v0.75 / v0.22, last session):** a never-opened glyph went through `create_glyph` -> automatic layer creation -> `draw_polygon` -> `set_glyph_sidebearings` -> `get_glyph_outline`, and every step read back correctly; `ringtest` (square with a hole, sidebearings 40/60, advance 400) read back with 2 contours, 8 nodes, `verified`, outer counterclockwise, hole clockwise.
