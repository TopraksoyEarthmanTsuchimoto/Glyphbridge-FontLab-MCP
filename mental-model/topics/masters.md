# Fonts with several masters

What the tools do on a font with more than one master, as seen live. Everything here comes from MM 2046–2062 and MR–MR3 2070–2088 ([LIVE-TESTS.md](../LIVE-TESTS.md)); the design built on it: [DECISIONS.md](../DECISIONS.md), 2026-11-27. Conditions: one run each unless stated, two masters made with FontLab's Add Layer dialog (All glyphs, Add font master, the new master left empty), straight contours, listener 0.221 / server 0.99, FontLab 8.9.5 in Demo mode. Open questions: [WATCH-POINTS.md](../WATCH-POINTS.md); the refusal: [refusals.md](refusals.md). Word budget: 6,000 ([MARKDOWN-MAP.md](../MARKDOWN-MAP.md)).

## 1. Masters, layers and the current master

- **A new font has one master, named `Regular` by FontLab** (2048: `master` `Regular`, `master_count` 1). Adding a master gives every glyph with a layer a layer of that name; `.notdef` of a File > New Font font, which has no layer, got only the new one (2054).
- **Clicking a master's layer in Layers & Masters switches the whole font's master:** the window title changes ("Unnamed: Regular") and every glyph shows that master (2054).
- **`flGlyph.activeLayer` follows the current master**, for every glyph (2050, 2054). Every Glyphbridge read and write uses it.
- **The legacy view does not follow: it shows `Bold`.** After the switch to `Regular` it showed 0 contours on glyphs whose `Regular` layer held an outline (2054, 2060b); with `Bold` given 4 nodes and `Regular` 8, it read 4 with `Regular` current (MR 2074), also with the glyph open in an editor and after further requests (2076, 2076a) and after `font.update()` (2079a). With one master it showed the outline (2049). Open: whether it shows the master added last or a layer by position.
- **FontLab's current master can split.** Selecting a glyph that has only a `Regular` layer, with `Bold` current, moved the window title, the KERNING panel and the kerning tools' `master` to `Regular`, while every other glyph's `activeLayer` stayed `Bold` (2085–2087); selecting a glyph with both layers ended it (2088). In that state glyph tools and kerning tools address different masters. One observation, no control yet.

## 2. Writes

- **Every tool write changed the current master only:** `set_glyph_width` (2056b), `set_glyph_sidebearings` (2057), `move_nodes` (2058), `add_contours` (2059), checked in FontLab on both masters; `set_kerning` (2060).
- **Each master has its own kerning table:** −80 written with `Bold` current left `Regular` at −50 (2060, 2060a). The kerning tools name the master and give `master_count`.
- **FontLab lets an empty master layer whose width was never set follow the width of the layer that holds the outline**, after a GUI edit (2056c) as after a tool edit (2056, 2057). A width set on that layer itself is kept (2056a, 2056b). So a width write can show on two masters while the reply names one change.

## 3. What the replies and checks get wrong

- **Reads name no master.** `get_glyph_outline` on an empty `Bold` layer answered "This glyph has no contours of its own" while `Regular` held a square (2051); the `font` field is the font's name ("Unnamed Regular"), not the master. `get_kerning` says that only the current master was read.
- **Outline edits read as not synced.** After a full-check write (drawing, `move_nodes`, `add_contours` and the like) the listener compares the legacy view's node count with the modern layer's (`_guard_classify`). On `Regular` it compared `Regular`'s nodes with `Bold`'s, so the verdict was `at_risk`, the change mark was skipped, and FontLab may ask no save question (2058, 2059). A drawing on `Bold` read as synced and was marked (2071). Width and sidebearing writes compare widths only and were marked (2056–2057).
- **The danger behind that check did not occur:** one `font.update()` (gated probe, 2077) kept `Regular`'s moved node and added contour and `Bold`'s outline (2078, 2079, 2079a), and brought FontLab's lagging sidebearings up to date. One run, straight contours.
- **A new glyph gets no layer.** `create_glyph` says so (`layer_note`) and skips the display refresh while other glyphs read as unsynced; the glyph did not appear in the grid at first (2061), later it did (2080, cause not isolated). `draw_polygon` then refuses it, because the glyphs' layer names differ (2062), although its description says a glyph without a layer in a multi-master font gets one. `draw_polygon` into an empty `Bold` layer beside `Regular`'s outline was allowed: its empty-glyph check looks at the current master's layer only (2071).

## 4. New layers

- **FontLab's Font > New Glyph made a layer for every master** (`Regular` and `Bold`), width 500, `hasBody` false (2080–2082).
- **`flGlyph.findLayerCreate("Regular")` added a first layer** to a glyph with none, with `Bold` current; it became the glyph's active layer, width 0; the legacy view still saw no layer (2083). The research probe adds only a first layer (2084); a second one was not tried.

## 5. Members for addressing a master by name (MR4)

- **Names only** (2089–2092): `flLayer` has `advanceWidth` ("double"), `inkBox()`, `isMasterLayer()`, `isActive()` and `setActive()`, but no sidebearing getter; `flGlyph` has `findLayer`, `getLayerByName`, `findLayerCreate`, `addLayers(list(flLayer))` and `updateActiveLayer(bool)`; `flPackage` has `setMaster(string name[, bool notify = false])`, `defaultMaster` and `hasMaster`; `flWorkspace` names nothing about masters. None of these was called, except `findLayer` and `findLayerCreate` (above).
- **Kerning read by master name works:** `flPackage.kerning("Regular")` and `kerning("Bold")` gave −50 and −80 with `Bold` current, the table size unchanged (2093, 2094).
- The probe built on these, `/debug/trymaster` (listener 0.222), is not yet run live.
