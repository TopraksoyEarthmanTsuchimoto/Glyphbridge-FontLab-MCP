# .notdef check and warning dialog

> Moved from milestone summary v11 (§7) on 2026-11-01, edited only where the chat-era workflow or a personal path no longer applies. The original section numbers are kept, so older cross-references such as "section 8p" still resolve: [MARKDOWN-MAP.md](../MARKDOWN-MAP.md) lists which file holds each section. Snapshot: [archive/milestone-summary-v11.md](../archive/milestone-summary-v11.md).

## 7. `.notdef` check and warning dialog (v0.46 / v0.10)

**Why:** every font must have `.notdef` as glyph 0; the OpenType spec recommends a visible outline (rectangle, with or without a
question mark or X). A new FontLab font starts with an EMPTY `.notdef`: empty is valid, a normal state for a font in progress,
but not recommended. Agents must expect `.notdef` in every font and must never treat an unreadable one as empty.

**Detector** (`check_notdef()` in the listener, read-only; status on **positive evidence only**):

| status | rule |
|---|---|
| `missing` | no glyph named `.notdef` (evidence names glyph 0) |
| `empty` | exactly 0 layers and 0 components; or exactly 1 readable body layer with 0 nodes, contours, shapes and 0 components |
| `has_outline` | any node, shape or component |
| `unknown` | no verdict: `len(glyph.layers)` unreadable, 2+ layers, layer unreachable although it exists, any count not a plain number. **Never triggers a dialog** |

`.notdef` not at index 0 only adds a note. Fonts without a glyph named `.notdef` are reported `missing` even if glyph 0 is differently named.

**Dialog:** `POST /font/notdef/warn` re-checks inside the listener (never on the caller's say-so) and shows a modal
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
  automatic check then reports `check_failed`; that path has not been seen live).
- **Blocking:** with the dialog open, `GET /health` timed out after 5 s: the listener serves nothing during a dialog (no re-entrancy, so no stacked dialogs).

**Not yet verified on real FontLab:** the explicit `check_notdef` tool and `get_glyph_outline(".notdef")` through Claude Desktop
(restart the listener first, which resets the once-per-font memory); a wait between 90 and 120 s and one beyond 120 s (the server
then gives up); a font with a drawn `.notdef` through Claude Desktop (no dialog expected; follows from the GET result); the `missing` dialog (stub-tested only; do not delete `.notdef` from a font that matters); whether other glyphs with
no outline (e.g. `space`) also have 0 layers (the outline route now answers `node_count` 0 for any zero-layer glyph); multi-layer
`.notdef`; `hasBody()`; whether a WRITE that timed out while a dialog was open is still executed after the click (the request waits in the
listener's socket queue; untested, which is why the timeout message says to check the state before repeating a change). One related observation from the v0.51 session:
after a Claude Desktop restart, a `create_glyph` call and then a read-only `list_glyphs` call each got no answer for 4 minutes (an unanswered Allow prompt was the likely cause); the font was
unchanged afterwards, i.e. the timed-out create had NOT been applied.
