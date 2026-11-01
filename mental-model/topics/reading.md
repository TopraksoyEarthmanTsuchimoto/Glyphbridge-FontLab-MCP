# Reading glyphs

> Moved from milestone summary v11 (§4, §5, §6, §8e, §8i, §8n) on 2026-11-01, edited only where the chat-era workflow or a personal path no longer applies. The original section numbers are kept, so older cross-references such as "section 8p" still resolve: [MARKDOWN-MAP.md](../MARKDOWN-MAP.md) lists which file holds each section. Snapshot: [archive/milestone-summary-v11.md](../archive/milestone-summary-v11.md).

## 4. How a glyph is read

| `kind` | meaning |
|---|---|
| `Move` | first on-curve node of a contour (this separates contours) |
| `On` | on-curve; an `On` right after an `On` is a straight line |
| `Curve` | cubic handle: exactly two between on-curve nodes |
| `Off` | quadratic off-curve point: runs of any length, implied on-curve at midpoints |

`smooth` matters only on on-curve nodes. One "To TT Curves" turns a cubic contour into the quadratic pattern (<= 0.63 unit deviation).

**Element transforms.** A FontLab *element* (shape) carries its own transform. `layer.findNode(i).x/.y` returns element-LOCAL
coordinates; FontLab's bbox, margins and drawing include the transform. The true transform is a Qt matrix per shape:
`x' = m11*x + m21*y + dx`, `y' = m12*x + m22*y + dy` (a 10 degree slant arrives as `m21 = 0.176327`).

**Verification statuses** (`get_glyph_outline` tries the direct route first):
- **`verified`** (`transform_source` "FontLab's own element transform, read directly"): real matrices applied; the result reproduces
  FontLab's control-point bounding box and left/right margins (tolerance 0.05 each).
- **`calibrated`** (fallback): matrices unavailable; transform estimated per axis from FontLab's bbox (scale + shift), confirmed by
  the horizontal margin. Assumes one element, no rotation/slant.
- **`unverified`**: something could not be confirmed; `x`/`y` are then RAW element-local values, the failed attempt is stored as
  `attempted_calibration_NOT_applied`, and `coordinate_space` says which space the numbers are in.
- With a transform applied, nodes carry `raw_x`/`raw_y` beside `x`/`y`. A mirrored glyph cannot pass the fallback as "verified".
- **Stale-view cross-check (server v0.25):** on the LEGACY route (the glyph has been opened in an editor, so the legacy view sees its nodes) a `verified` / `calibrated` result adds `verification.modern_margins_check` = `{status: agrees}`, or `{status: mismatch, differs, legacy, modern}` together with `status: unverified`, `stale_legacy_view: true` and a note; `{status: not_checked, reason}` when the extra read failed (the old verdict is kept and a note says so). Section 8i.

Verified live earlier, all `verified`: identity, scale + offset, 10 degree slant, cubic, quadratic, a Power Brush outline.

## 5. Layers

- `bodyLayer`/`activeLayer` (after the warm-up) hold the nodes; `glyph.layer` and `glyph.bodyLayerStrict` return a **placeholder
  layer named `Body` with 0 nodes for every glyph seen**, so a 0 from the `strict`/`glayer` routes proves nothing. Modern
  `flGlyph.bodyLayer` is `None` (use `activeLayer`).
- `layer.countContours()`, `countNodes()`, `countShapes()`, `len(layer)` match FontLab's GUI tooltip counts. `len(glyph.layers)`
  works (`fgLayers`): 1 for ordinary glyphs, **0 for a glyph with no outline data at all** (section 7).
- Multi-master / multi-layer glyphs are untested.

## 6. The legacy-to-modern bridge and its leak

`fontlab.flGlyph(fgGlyph, fgFont)` returns the real modern glyph for any glyph by name. Path used: `flGlyph.activeLayer.shapes` (a
REAL Python list, indexable) -> each shape's `.transform` (`QTransform`: `m11 m12 m21 m22 dx dy`). `flGlyph.fgGlyphId` equals the
legacy `fgGlyph.id`. `flWorkspace`/`flGlyphInfo` reach only the glyph open in the editor.

**Leak (measured):** each construction leaves one native reference behind (cause not isolated). Mitigation: ONE cached wrapper per
legacy glyph id, validated before reuse (name, `fgGlyphId`, `isValid()`), rebuilt if stale, cache cleared when the font path
changes (`elements.wrapper` reports `cached`). `release()` was deliberately NOT tried (crash risk).

## 8e. Reading an outline back from the modern layer; direction; curves (what is known)

**Why:** the legacy reader (`/glyph/outline`) lags and is BLIND to shapes drawn through the API; `modern_check` compares the modern node count with the legacy count, and `modern_outline` (v0.74) is added whenever the modern layer has nodes and the two disagree. The server then answers with `source: "modern layer"`.
**Proven live calls:** `layer.getContours()` returns a plain Python list (indexed only when it is a real list/tuple); `contour.getNodeAt(i)` after a range check against `nodesCount`; node reads `x, y, isOn(), isOff(), isCurve(), smooth, index`; contour reads `closed, clockwise, nodesCount`. `layer.shapes` is a list. `layer.getShapes()` raises IndexError. `contour.nodes` is a METHOD (calling it is untested). Limit `_MODERN_OUTLINE_MAX_NODES = 5000`; no partial outlines (any failed read gives `{available: false, error}`).
**Result fields (server):** contours (`closed`, `clockwise_reported`, `direction_computed`, `flag_follows_known_inversion`, `node_list` with x/y/kind/curve/smooth, `curve_type`, `svg_path` for straight and cubic closed contours; v0.24), `ink_bbox`, `ink_bbox_exact`, margins, `verification`. Status is `verified` only for straight-segment outlines whose node box equals the modern lsb and ink width; since server v0.24 cubic outlines are `verified` too (section 8g); quadratic or malformed curves stay `unverified` with a reason.
**DIRECTION (live, three glyphs):** FontLab's `contour.clockwise` flag is the OPPOSITE of the y-up geometry: a counterclockwise contour reports `clockwise: true`, a clockwise one `false` (confirmed with a house, a square, and both ring contours). The outer contour of the real glyph `A` (cubic test font, Power Brush shape) is COUNTERCLOCKWISE in y-up. So: outer contours counterclockwise, counters (holes) clockwise. One real sample: a strong hint, not a law. The server warns only when a flag does NOT show the known inversion.
**Curve building blocks (from `/debug/classdir`; the working recipe is in section 8g):**
- `flNode` constructors: `flNode()`, `flNode(Node)` (clone), `flNode(QPointF position[, string nodeType="on"[, int nodeKind=None]])`, `flNode(double x, double y[, string nodeType="on"[, int nodeKind=None]])`. `flNode.NodeType` is a real Python dict (`On` 1, `Off` 2, `Curve` 4, `AnyNodeMask` 7); `flNode.NodeKind` and `flContour.FigureType` are dicts too (their contents were printed by a `names` probe; re-run it). Members worth a names-only look: `convertToCurve`, `convertToCurves`, `convertToLine`, `smooth`, `nextNode`, `prevNode`, `type`, `isCurve`.
- `flContour` constructors (docstring): `flContour()`, `flContour(list(Node)[, bool closed=false])`, `flContour(list(QPointF)[, NodeType=On[, bool closed=false]])`, `flContour(QRectF)`, `flContour(QLineF)`. **Live:** only forms with at most 2 arguments exist; `flContour(points, On, True)` is refused ("Incorrect # of args"); `flContour([flNode, ...], True)` is refused ("QPointF expected"); NONE of the constructor forms closes the contour (set `contour.closed = True` afterwards); `flContour(QRectF)` gives a closed 4-node contour. Members of interest: `insert`, `insertNodeTo`, `insertSafeNodeTo`, `add`, `nodes` (method), `takeNodes`, `clearNodes`, `getNodeAt`, `setPoint`, `convertTTtoCurve`, `segments`, `segment`, `getSegment`, `closed`, `closedT1`.
- Reading already shows `Off` / `curve` nodes; cubic = exactly two handles between on-curve nodes (section 4).

## 8i. Stale legacy view after API writes (live finding on v0.24; detection in server v0.25, wording v0.26)

**What happens.** FontLab keeps two views of a glyph: the MODERN layer (`flGlyph.activeLayer`, what every write tool changes and what `get_glyph_sidebearings` reads) and the LEGACY view (`fgGlyph`, what the old reader `GET /glyph/outline` walks). A glyph that was never opened in an editor has an empty legacy view (`legacy reader sees 0 nodes`), so the server takes the modern route (`source: "modern layer"`, current). A glyph that HAS been opened in an editor tab has a populated legacy view, the server takes the legacy route (no `source` key, no `modern_check`) and that view does NOT follow later modern writes: after `set_glyph_sidebearings(40, 60)` (and again after `(20, 30)`) the legacy nodes still showed the old x range, the legacy margins the old values (0 / 100, 0 / 50), and only the advance width was new. The v0.24 reader compared the legacy nodes with the legacy margins (equally stale) and said `verified`. FontLab's own X/Y readouts and the modern reads had the new geometry.

**What was proven live (one variable at a time, glyph `stl85a`, opened in an editor tab):**
- Baseline before any change: `verified`, `modern_margins_check: agrees`.
- Immediately after `set_glyph_sidebearings(20, 30)`: `unverified`, `stale_legacy_view: true`, legacy margins 0 / 50 against modern 20 / 30, advance 525 on both (the reply names both).
- A plain click on the grid tab and back: legacy view STILL stale. About 7 minutes of waiting with no GUI action: STILL stale (read twice).
- Closing the glyph's editor tab (X) and double-clicking the thumbnail: legacy view refreshed (`verified`, nodes 20 to 520, handles at 520, margins 20 / 30, `modern_margins_check: agrees`).
- NOT tested: whether selecting a node in the editor also refreshes it. In the earlier `grd83a` run the stale view cleared after the user switched to the grid tab and back AND inspected nodes (screenshots with X/Y readouts); that run did not separate the factors, so only "close and reopen the tab" is recorded as confirmed.
- On the legacy route `bounding_box_check.raw_node_box` is the box of ALL nodes including control points (0 to 500 for the bulging rectangle) while the ink extents and margins use the exact curve (0 to 475); the two agree through FontLab's own `fontlab_box`, and the result is `verified`.

**What the server does now (v0.25 / v0.26):** `_stale_legacy_check` (legacy route only; skipped when the status is already `unverified`, when `modern_check.modern_layer` is not true, or when the modern layer was used) calls `GET /glyph/sidebearings?name=...` once and compares `lsb` / `rsb` / `advance` with the legacy `margins.left` / `right` / `width`, tolerance `_STALE_MARGIN_TOLERANCE = 0.05`. It never raises. It does not change the listener. Tests: part 15 of `create_unicode_tests.py` (15a live case, 15b detail, 15c agree, 15d 0.04 tolerated, 15e 0.06 flagged, 15f advance only, 15g read fails, 15h modern not readable, 15i not a number, 15j legacy margins missing, 15k no modern layer, 15l old listener, 15m modern switched off, 15n old node-count path, 15o already unverified, 15p calibrated checked too, 15q docstring, 15s v0.26 wording, 15r no write and no save); a mutation test (check disabled) turns 15a back into `verified`.

**Advice for agents and for the person:** after changing a glyph through the API, trust `get_glyph_sidebearings` and the modern reads; if `get_glyph_outline` says `stale_legacy_view`, ask the person to CLOSE the glyph's editor tab and reopen it from the grid, then read again. A glyph never opened in an editor is always read from the modern layer and is not affected.

**Possible later improvement: BUILT in v10** (listener 0.88 / server 0.28, section 8n): the listener returns the modern outline whenever the modern margins disagree with the legacy ones, and since listener 0.89 the write itself syncs the glyph (8m), so the refresh recipe above (close the editor tab) is no longer needed in normal use.

## 8n. Listener-side stale-view fallback (listener 0.88, server 0.28; live-proven in 139b)

**What it does.** `GET /glyph/outline`: when the legacy node count equals the modern count (so the old `modern_check` said `agree: true`) and the legacy margins were read, `_reader_margins_compare(w, legacy_margins)` compares modern left / right / advance with the legacy `left` / `right` / `width` (tolerance `_READER_MARGIN_TOLERANCE = 0.05`). `modern_check` gains `margins_agree`: `true`, `false` (plus `margins_differ`, `legacy_margins`, `modern_margins`) or `null` (plus `margins_note`: no QTransform, unreadable, a legacy value not a number). It is compared only when both counts agree and are above 0 (an empty layer is not compared). On `false` the listener attaches `modern_outline` (as it already did for a node-count disagreement). **Server v0.28:** `_modern_outline_result` answers from the modern layer when `margins_agree` is false (`source: "modern layer"`, `legacy_view_was_stale: true`, note "STALE LEGACY VIEW, answered from the modern layer", `verification.legacy_margins_vs_modern`); an older listener or a `null` comparison falls back to the server's own v0.25 `_stale_legacy_check`. The `get_glyph_outline` docstring says so ("Since listener 0.88 ...").
**Live (139b):** after `set_glyph_sidebearings(20, 30)` on a glyph whose legacy view had just been synced, the legacy read gave x 0..400, margins 0 / 50 / 450 against modern 20 / 30 / 450, `margins_agree: false`, `margins_differ: [left, right]`, and the attached `modern_outline` had the correct x 20..420. **With v0.89 this case should no longer occur** (the write syncs itself); the fallback is a safety net (for example after a failed sync).
**Verified read-only on transforms (143):** the modern and legacy margins use the SAME coordinate space even when a glyph has a non-identity element transform: `testglyph1` (scale 0.951 x 0.969, offset 15 / 24), `testglyph4` (skew m21 0.176) and the composite-flagged `A` all gave `margins_agree: true`. Rotation and mirroring are still untested (checklist 12c / 12d).
**Side observation (143):** `lsb` / `rsb` come from FontLab's own sidebearing calculation and can differ from the control-point bounding box (`testglyph2`: bbox left 83.0 from a control point, lsb 102.15 from the true curve; `testglyph4`: lsb 158.9 against bbox left 142.2 with the skew). Do not compare the two directly.
