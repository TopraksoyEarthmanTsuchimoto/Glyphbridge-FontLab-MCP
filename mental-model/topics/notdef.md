# .notdef check and notice

> Moved from milestone summary v11 (§7) on 2026-11-01, edited only where the chat-era workflow or a personal path no longer applies. The original section numbers are kept, so older cross-references such as "section 8p" still resolve: [MARKDOWN-MAP.md](../MARKDOWN-MAP.md) lists which file holds each section. Snapshot: [archive/milestone-summary-v11.md](../archive/milestone-summary-v11.md).

## 7. `.notdef` check and notice (v0.46 / v0.10; no dialog since v0.203 / v0.83)

**Why:** every font must have `.notdef` as glyph 0; the OpenType spec recommends a visible outline (rectangle, with or without a
question mark or X). A new FontLab font starts with an EMPTY `.notdef`: empty is valid, a normal state for a font in progress,
but not recommended. Agents must expect `.notdef` in every font and must never treat an unreadable one as empty.

**Detector** (`check_notdef()` in the listener, read-only; status on **positive evidence only**):

| status | rule |
|---|---|
| `missing` | no glyph named `.notdef` (evidence names glyph 0) |
| `empty` | exactly 0 layers and 0 components; or exactly 1 readable body layer with 0 nodes, contours, shapes and 0 components |
| `has_outline` | any node, shape or component |
| `unknown` | no verdict: `len(glyph.layers)` unreadable, 2+ layers, layer unreachable although it exists, any count not a plain number. **Never triggers a notice** |

`.notdef` not at index 0 only adds a note. Fonts without a glyph named `.notdef` are reported `missing` even if glyph 0 is differently named.

**Notice (since listener 0.203 / server 0.83, 2026-11-24; run live SD 1599–1616, [LIVE-TESTS.md](../LIVE-TESTS.md); the design: [DECISIONS.md](../DECISIONS.md), 2026-11-21):** `POST /font/notdef/warn` re-checks inside the listener and shows NO dialog: a missing or empty `.notdef` is noted once per font as one OUTPUT line, remembered by the package `fgId` (`_NOTDEF_NOTED`; an unreadable `fgId` is not remembered, so the note may repeat but is never wrongly held back); `force: true` repeats it. For an empty `.notdef` the reply carries the font's maturity (`_font_maturity`: all 52 letters A–Z a–z by Unicode, and one of them drawn, checked from n o H O on). The server's instruction: missing, said clearly; empty in a mature font, a likely oversight. **Since server 0.84 (2026-11-24, [DECISIONS.md](../DECISIONS.md)), an empty `.notdef` in a font still in progress (not mature, or unknown) is left alone:** the server does not ask the listener to note it, the automatic checks tell the agent to say nothing, and `check_notdef` answers only if the person asked (0.83 gave one light sentence). A listener older than 0.203 is not asked to note anything. Deleting `.notdef` through `delete_glyph` gets its own warning in the self-closing Yes/No dialog.

**Dialog (until listener 0.202):** `POST /font/notdef/warn` re-checked inside the listener (never on the caller's say-so) and showed a modal
`QMessageBox.Information` with an OK button (title "Glyphbridge: .notdef glyph"; wording in `_NOTDEF_DIALOG_TEXT`, one text for
`empty`, one for `missing`; since 0.109 without the closing line that said it is shown once and that "an AI agent" read the font). At most once per font **path** per listener
run (`_NOTDEF_WARNED`); `force: true` repeats it. Fonts with an empty or shared path share one memory slot. While the dialog is
open the listener answers nothing else: live-verified (a plain `/health` request timed out after 5 s while the dialog was open), so a second
request cannot stack a second dialog. Live-verified through Claude Desktop: the host tool call simply waits for the click, even for 90 s.

**Triggers (server):** `get_current_font` (automatic, adds a `notdef` entry), `get_glyph_outline(".notdef")` when it comes back
empty (adds `notdef_check`), and the explicit `check_notdef` tool. NOT `list_glyphs`, NOT other glyphs. Automatic checks are
best-effort: a failure becomes `{"status":"check_failed"}` and never fails the host tool. Results carry an `agent_instruction`
(tell the user in chat too; "unknown" -> say nothing about missing/empty).

**Error wording:** an outline whose layer cannot be reached says "this does NOT mean the glyph is empty"; for `.notdef` it also
points to `check_notdef`.

**Real-FontLab evidence (read-only probes, then live runs):**
- An empty `.notdef` (GUI shows it blank): `len(glyph.layers)` 0, `bodyLayer`/`activeLayer` `None` on every attempt, on every outline call (body
  and active routes) and on 3 of 3 later `layerstats` calls; one earlier layerstats success was never explained or reproduced. `hasBody` is a callable (never called).
- A drawn `.notdef` (checked on Arial opened from the system, 4548 glyphs): 1 layer, 2 contours, 8 nodes, 1 shape, 0 components,
  reads normally, status `has_outline`.
- `len(glyph.components)` is readable on the layerless `.notdef`; `GET /font/notdef` -> `empty`; `POST /font/notdef/warn` -> the
  dialog appeared (reported by the user) with `dialog_shown: true`; a second call -> `already_warned: true`, no dialog;
  `--check --notdef-warn` and `--check --outline .notdef` behaved as designed (`empty: true`, "no layer at all" note, `notdef_check`).
- **Through Claude Desktop** (v0.46 / v0.10): asking for the open font ran `get_current_font`, which ran the automatic check; the dialog appeared;
  after OK Claude answered and mentioned the empty `.notdef`; a second request showed no second dialog (the once-per-font memory holds across real requests).
- **Long wait:** with the dialog left open for 90 s the tool call stayed pending and Claude answered only after the click. So
  Claude Desktop's own tool-call limit is at least 90 s (its exact value is unknown); the server gives up at 120 s by design (the
  automatic check then reports `check_failed`; that path has not been seen live). Superseded: since listener 0.203 / server 0.83 the
  `.notdef` notice shows no dialog, and the server waits 55 s for the dialogs that remain ([server-and-endpoints.md](server-and-endpoints.md) §2).
- **An empty glyph is not always layerless** (1405–1408, 2026-11-19, one run; SP 1726–1727, 2026-11-25, one run): Arial's `space` has one empty layer (`Regular`, 0 nodes),
  while the empty `.notdef` of a File > New Font font has none; the legacy outline read (`modern=no`) and the Layers panel agree. Times New Roman's `space` likewise had 0 contours and nodes by `get_glyph_outline`, and the Layers & Masters panel showed one empty `Regular` layer. Selecting the glyph did not add a layer.
- **Blocking:** with the dialog open, `GET /health` timed out after 5 s: the listener serves nothing during a dialog (no re-entrancy, so no stacked dialogs).

**Not yet verified on real FontLab:** the explicit `check_notdef` tool and `get_glyph_outline(".notdef")` through Claude Desktop
(restart the listener first, which resets the once-per-font memory); (no longer applies since 0.203 / 0.83, the notice has no dialog:) a wait between 90 and 120 s and one beyond 120 s (the server
then gives up); a font with a drawn `.notdef` through Claude Desktop (no dialog expected; follows from the GET result); a missing `.notdef` (it needs a Yes to delete it; not run; do not delete `.notdef` from a font that matters); whether empty glyphs
made by FontLab other than `.notdef` have 0 layers (Arial's `space` has one, above; the outline route answers `node_count` 0 for any zero-layer glyph); multi-layer
`.notdef`; `hasBody()`; whether a WRITE that timed out while a dialog was open is still executed after the click (the request waits in the
listener's socket queue; untested, which is why the timeout message says to check the state before repeating a change). One related observation from the v0.51 session:
after a Claude Desktop restart, a `create_glyph` call and then a read-only `list_glyphs` call each got no answer for 4 minutes (an unanswered Allow prompt was the likely cause); the font was
unchanged afterwards, i.e. the timed-out create had NOT been applied.
