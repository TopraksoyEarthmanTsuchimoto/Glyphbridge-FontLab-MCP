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
**Result fields (server):** contours (`closed`, `clockwise_reported`, `direction_computed`, `flag_follows_known_inversion`, `node_list` with x/y/kind/curve/smooth, `curve_type`, `svg_path` for straight and cubic closed contours; v0.24), `ink_bbox`, `ink_bbox_exact`, margins, `verification`. Status is `verified` only for straight-segment outlines whose node box equals the modern lsb and ink width; since server v0.24 cubic outlines are `verified` too (section 8g), and since server v0.43 quadratic ones (§8p); contours that mix both kinds, or are malformed, stay `unverified` with a reason.
**DIRECTION (live, three glyphs):** FontLab's `contour.clockwise` flag is the OPPOSITE of the y-up geometry: a counterclockwise contour reports `clockwise: true`, a clockwise one `false` (confirmed with a house, a square, and both ring contours). The outer contour of the real glyph `A` (cubic test font, Power Brush shape) is COUNTERCLOCKWISE in y-up. So: outer contours counterclockwise, counters (holes) clockwise. One real sample: a strong hint, not a law. The server warns only when a flag does NOT show the known inversion.
**Curve building blocks (from `/debug/classdir`; the working recipe is in section 8g):**
- `flNode` constructors: `flNode()`, `flNode(Node)` (clone), `flNode(QPointF position[, string nodeType="on"[, int nodeKind=None]])`, `flNode(double x, double y[, string nodeType="on"[, int nodeKind=None]])`. `flNode.NodeType` is a real Python dict (`On` 1, `Off` 2, `Curve` 4, `AnyNodeMask` 7); `flNode.NodeKind` and `flContour.FigureType` are dicts too (their contents were printed by a `names` probe; re-run it). Members worth a names-only look: `convertToCurve`, `convertToCurves`, `convertToLine`, `smooth`, `nextNode`, `prevNode`, `type`, `isCurve`.
- `flContour` constructors (docstring): `flContour()`, `flContour(list(Node)[, bool closed=false])`, `flContour(list(QPointF)[, NodeType=On[, bool closed=false]])`, `flContour(QRectF)`, `flContour(QLineF)`. **Live:** only forms with at most 2 arguments exist; `flContour(points, On, True)` is refused ("Incorrect # of args"); `flContour([flNode, ...], True)` is refused ("QPointF expected"); NONE of the constructor forms closes the contour (set `contour.closed = True` afterwards); `flContour(QRectF)` gives a closed 4-node contour. Members of interest: `insert`, `insertNodeTo`, `insertSafeNodeTo`, `add`, `nodes` (method), `takeNodes`, `clearNodes`, `getNodeAt`, `setPoint`, `convertTTtoCurve`, `segments`, `segment`, `getSegment`, `closed`, `closedT1`.
- Reading already shows `Off` / `curve` nodes; cubic = exactly two handles between on-curve nodes (section 4).

**Open contours (OC, tests 579–585, 2026-11-04, FontLab 8.9.5, server 0.45 → 0.46).** Glyphs `oc1_a` and `oc1_b` were created with `create_glyph` (580, 582) in a new unsaved font and drawn by the person with the Pen tool; each path was ended without clicking its first node again.
- **FontLab's facts:** a contour drawn that way reads `closed: false` on the modern layer. The open "V" (581) has 3 `On` nodes (24, 482), (132, 69), (228, 462), LSB 24, RSB −228, advance 0. The open arch (583) has the order On (105, 104), Curve (105, 280), Curve (398, 255), On (398, 104): both ends on-curve, no handle stored after the last node; its last node reads `smooth: true` (not explained). FontLab's `inkBox()` of the arch has the top **226.804**, the exact extent of the cubic segment (585). The names-only probe of `flContour` (579): 176 public names, among them `closed` ("closed attribute"), `closedT1`, `breakContour(flNode | int)`, `getFirstPoint`, `getLastPoint`, `extrapolateFirst`, `extrapolateLast`, `boundingBox`, `inkBox`; none was called.
- **Server 0.45** (581, 583): the open V was `verified` (straight segments: the node box is the real box) but had no `svg_path` and a meaningless direction; the open arch was `unverified` (its curve was not parsed), with the box of its end nodes (top 104).
- **Server 0.46** (584, 585): an open contour runs from its first node to its last, without a closing segment; `svg_path` without Z; `direction_computed` "not applicable (open contour)"; a note names the open contours. Both glyphs read `verified`, the arch with box 105 / 398 / 104 / 226.804, equal to FontLab's ink box. Stub only: a quadratic open contour, an open contour whose end is a handle (refused with its reason). The legacy route still assumes closed contours.

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
**Power Brush with an offset (T4, 145g, 260, 2026-11-03):** after `setSB` put dx −142 into the transform of `A`'s Power Brush shape, the reader answered `verified`: FontLab's own transform applied, the transformed box equal to FontLab's (50.466..322.534), margins 50.466 / 60.466 / 383 in agreement; FontLab's Elements panel showed Δ=(-142,0). Scale and rotation on a Power Brush shape are still untested (checklist 14).

## 8p. Modern-first reading (listener 0.120, server 0.42; live 497–520; vertical check 0.121 / 0.43)

- **The route:** `/glyph/outline` with `layer=body|active` reads a glyph whose modern active layer holds nodes from the modern layer only (`source: "modern"`): the contours, the element transforms (`_describe_modern_glyph`), the modern margins and counts. The legacy layer is never touched, because touching it lets the next `font.update()` flatten a Power Brush glyph (F1, [fonts-and-sync.md](fonts-and-sync.md) §8l). If the modern node count or outline cannot be read, the reply is an error, never a legacy fallback.
- **Legacy fallbacks:** the modern side cannot be reached, the modern layer is missing or holds no nodes (then there is no outline to flatten), `layer=strict|glayer`, and `modern=no` (`GLYPHBRIDGE_MODERN=0`; the server then warns about F1). The legacy reader (§4–§6) is unchanged.
- **Coordinates:** the modern node coordinates are the element's own values, before its transform (515: with the offset −142 the raw nodes did not move). The server applies the element matrices by contour counts, as on the legacy route; it checks both readings and calls only an unambiguous match `verified`.
- **The check:** the box of the transformed nodes, cubic and quadratic extremes included (server 0.43), against FontLab's modern left sidebearing and ink width (tolerance 0.05). Since listener 0.121 / server 0.43 the vertical extent is checked too, against `fontlab_ink_box` from `flLayer.inkBox()`; `verified` needs both (`y_extent_checked: true`, `ink_box_vs_fontlab`). The vertical check also decides between the raw and the transformed reading. Without a usable box the check stays horizontal and `y_extent_note` says why. Live (V121, 535–539): `testglyph1`–`4` and `A` `verified` with `y_extent_checked: true`.
- **`inkBox()` (live 519–533, FontLab 8.9.5, `savedtestfont.vfc`):** called with no argument it equalled the exact curve extents with the element transform applied on `testglyph1` (quadratic, scale and offset), `testglyph2` (cubic), `testglyph3` (quadratic), `testglyph4` (slant) and `A` (Power Brush, with and without an offset), in x and y; Qt's `top` was always the lower y. A `create_glyph` after it left `A` intact (531–532). FontLab's own selection readout shows the box of the selected points, handles included (533: `testglyph2` X 83, Y 172, 300 × 242), not the ink box, so no displayed number checks the vertical ink extent; the x extent matches the glyph panel's sidebearings.
- **`.notdef`:** `/font/notdef` judges a `.notdef` with modern nodes or components from the modern counts; otherwise the legacy check runs.

## Components: the API by name (P1.1, 2026-11-06, tests 604, 605; FontLab 8.9.5, no font open)

Names and docstrings only (`/debug/moddir`, `/debug/classdir`): nothing was called or constructed, so **nothing here is proven behaviour**. Docstrings can mislead (`flLayer.boundingBox`, test 519).

- **Modules (604):** in `fontlab`, a search for component, reference and element finds `GlyphComponent` (and, by the letters "reference", `flPreferences`); in `fontgate`, `fgComponent` and `fgComponents`. **`flComponent`, the argument type in the docstring of `flLayer.addComponent`, did not match that search**, so it is not a public name of either module.
- **`flLayer` (605):** `components` ("list(name, transform)"), `componentsCount()`, `hasComponents()`, `hasComposites()`.
- **`flShape`:** `isComponent`, `isComposite`, `hasComponents` (bool), `isShape` (doc not read), `shapeType`.
- **`flShapeData`:** `componentGlyph`, `componentLayer` (strings), `isComponent`, `isComposite` (bool), `referenceCount` (int), `shapeType()`. `flGlyph` has no member with "comp" in its name.
- **`GlyphComponent`:** `name_id` (uint), `transform` (QTransform), `width_scale` (double), `use_anchors` (bool).
- **Legacy:** `fgGlyph.components` (documented as a list of `fgComponent`); `fgComponent` has `baseGlyph`, `matrix` (`fgMatrix`), `index`, `box` (`fgRect`), and `offset`, `scale`, `hasFullMatrix` without docstrings; `fgComponents` is a native type (`asList`, `getAsList`, no docstrings), so its container rule applies ([FONTLAB-API-RULES.md](../FONTLAB-API-RULES.md) §10).
- **Already in use:** the listener reads `componentsCount()` of the modern layer and `len(glyph.components)` for its counts, and the debug shape reader reads `isComponent` and `isComposite`. `A` (Power Brush) reads `is_composite: true` with `component_count` 0 (143).
- **Not to be called in probes**, since they change or may change the font: `addComponent`, `clearComponents`, `setGlyphComponents`, `decomposite`, `mergeTopComposite`, and on the legacy objects `append`, `insert`, `del`, `clean`, `decompose`, `move`.
- **Open:** what `flLayer.components` holds on a real component glyph, whether `flShapeData.componentLayer` names a master (the fonts tested had one), and whether `referenceCount` marks element references.

## Components: what was read live (2026-11-09, tests 606–611, [LIVE-TESTS.md](../LIVE-TESTS.md); FontLab 8.9.5, one master)

- **Telling a component from a plain shape:** `flShape.isComponent` is true on a component and false on a plain shape (606, 610). `shapeType` does not tell them apart: both read `ShapeContours`. `isComposite` is not enough either: a Power Brush shape reads true too (143).
- **The source glyph:** `shape.shapeData.componentGlyph` names it and `componentLayer` gives `Regular`; on a plain shape both are empty (609, 610).
- **Nodes:** the layer counts the component's nodes (`nodesCount` 4), so the modern-first route reads the glyph like a contour glyph, from the component's own coordinates.
- **Transforms:** an offset, and horizontal scale with an offset, are read from `flShape.transform`, applied, and agree with FontLab's panels and `inkBox()`: `verified` (608, 611). Rotation, slant, mirroring, vertical scale and several components are untested.
- **What the reply says (listener 0.128 / server 0.49, live 624–626):** each element gives `is_component` (`"unknown"` when the flag could not be read) and, for a component, `component_glyph` and `component_layer`, with one note that the nodes are the source glyph's outline. Found missing in 607. The failure paths are stub-tested only; the older legacy route keeps its own note.
- **`referenceCount`** read 2 on `cp1base` and 1 on its component, unexplained ([WATCH-POINTS.md](../WATCH-POINTS.md)).
