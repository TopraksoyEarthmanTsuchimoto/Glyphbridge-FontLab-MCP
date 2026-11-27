# Expanding element transforms, and FontLab's Undo

What FontLab does when an element transform is expanded, through its GUI and through the API, and how its Edit > Undo relates to edits made through the API. Everything here comes from research probes (listener 0.218–0.220) and FontLab's GUI, one run each, on plain straight shapes in a font with one master, FontLab 8.9.5 in Demo mode. The tool built on it, `expand_transformation` (listener 0.221 / server 0.98), is in §4. The runs: XT, XT2, XT3 and XT4, 1952–1981 in [LIVE-TESTS.md](../LIVE-TESTS.md); the probes: [server-and-endpoints.md](server-and-endpoints.md) §3; the calls' review state: [FONTLAB-API-RULES.md](../FONTLAB-API-RULES.md); what is still open: [WATCH-POINTS.md](../WATCH-POINTS.md).

## 1. Expanding a transform

- **FontLab's Element > Expand Transformation** moves the element's transform into its nodes and leaves the identity: the stored nodes take the drawn positions, and the outline, the sidebearings and the ink box stay (1956). The command is greyed out on a shape without a transform (1967, 1981). Edit > Undo reverses it (1957).
- **Through the API, `shape.applyTransform()` with no argument does the same** (1959, 1968, 1969, 1972, 1976), offsets included (1972, 1976). It returns `None`. Bottom nodes may read −0.0.
- **Both round the expanded nodes to whole units.** A square scaled, slanted 5° and rotated 15° came out at (136, 54), (387, 121), (338, 398), (87, 330) through the API (1975) and, node for node, through the GUI (1981), where the exact positions were (135.570, 53.646), (386.711, 120.939), (337.904, 397.739), (86.763, 330.446): the outline moved by up to 0.446 units. The rounding happens in the call itself, before the sync (1975). With whole-number results nothing moves (1956, 1959, 1972, 1976).
- **After an API expansion FontLab's transform panel can stay stale** (it showed 150 % after 1959) until a later event; the data is current.
- `shape.applyTransform(<its own transform>)` was built into the probe as a control (`how=own`) but not run live.

## 2. FontLab's history

- **Glyphs, layers, shapes, contours and nodes each list history members** (names only, 1952): `hasHistoryStates`, `currentHistoryState()`, `initialHistoryState()`, `historyStates(bool)`, `restoreHistoryState(uint)` and others. The reads run without a crash and return plain numbers and real lists of numbers (1966). The numbers look like positions in one shared counter.
- **`historyStates(True)` holds the states up to the current one; `historyStates(False)` holds the undone ones too** (1970). The lists are not in a fixed order (1966, 1969).
- **A GUI edit records a state on the shape** (1967). The glyph holds its own states; the layer held states only once (1972).
- **An API edit records no state** (1968), also between `flItems.notifyEditActionStarted()` and `notifyEditActionFinished()` (1969, both returned `None`).

## 3. The change mark and Edit > Undo

Glyphbridge's change mark, `flItems.notifyChangesApplied(title, …)`, is what makes FontLab ask to save after a tool write ([server-and-endpoints.md](server-and-endpoints.md) §2). Its title also becomes an Edit menu entry, title-cased ("Undo Glyphbridge Expand", 1961; "Glyphbridge Move Nodes", 1023).

| Mark | Where FontLab records a state | Edit > Undo after an API expansion |
|---|---|---|
| standard: `(title, <glyph>, False)` | the glyph only (1968, 1969) | the glyph's history steps back, the outline stays expanded: nothing visible is reversed (1962, 1970) |
| `(title, <glyph>, True)`, recursive | the glyph, the layer and the shape (1972) | **reversed**: transform and nodes restored; Redo restores the expansion (1973, 1974) |
| `(title, <shape>, False)` | the shape only (1976) | **damaging**: the transform is restored but the nodes are not, so the old transform applies to the expanded nodes (1977). Never used in a tool ([FONTLAB-API-RULES.md](../FONTLAB-API-RULES.md) §9) |

- **Undo restores values in single precision:** m11 1.4700000286 for 1.47, x 170.0000029 for 170 (1973), the same after an accidental GUI Undo (1979). The panel then showed a right sidebearing of −465 for 464.0000086.
- **Why the recursive mark works,** as read from the history values: before the API edit, the shape's current state is the one its last GUI edit recorded (1968, 1969); the recursive mark records the state after the edit on top of it, so Undo has the earlier state to return to. Whether this holds after other writes (widths, drawing, node moves, components, kerning) is untested.

## 4. The tool, `expand_transformation`, live (XT5 1982–2024)

One run each, one master, Demo mode; the design: [DECISIONS.md](../DECISIONS.md) (2026-11-26 and 2026-11-27); every step: [LIVE-TESTS.md](../LIVE-TESTS.md).
- **The preview predicts FontLab's rounding exactly:** the tool maps each node by the transform and rounds it to the nearest whole unit; FontLab stored the same numbers on a rotated and slanted square (1994) and on a cubic curve.
- **Control points are rounded too** (1999): (618.69, 101.79) became (619, 102). Research had seen only on-curve nodes rounded.
- **Edit > Undo takes the tool's expansion back, and Redo brings it again** (1990, 1991): the Edit menu names it "Glyphbridge Expand Transformation", the mark's title. After a list of three glyphs, what one Undo reverses was not tried.
- **What it leaves alone:** a component beside the expanded shape and its source glyph stay unchanged (2004, 2005).
