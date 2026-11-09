# Decisions

Active decisions only, newest first. Each entry gives the date, the decision and the reason. Superseded or no longer relevant entries move to [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). Where the chat-era record gives no exact day, the entry says so.

## 2026-11-09: a new glyph gets its layer (listener 0.127 / server 0.48)

- **`create_glyph` creates the glyph's layer at once in a font with one master. When it cannot, the glyph is still created and the reply says why, with a warning about Add Component.** *Reason:* Add Component crashes FontLab on a glyph with no layer (612–619); refusing the create would remove what works today in order to protect a later GUI step. The user approved the design as proposed.

## 2026-11-04: open contours in `draw_path` (listener 0.126 / server 0.47)

- **A contour given as `{"points": [...], "closed": false}` is drawn open; a plain list stays closed**, so existing calls are unchanged. An open contour may not carry `c1` / `c2` on its first point or be smooth at an end. Every reply with an open contour tells the agent to say that open contours have no fill and that what FontLab does with them on export is untested. *Reason:* the user approved the design as proposed; the facts are 586–603.

## 2026-11-04: whole kerning units (server 0.45)

- **`set_kerning` refuses a value that is not a whole number, before anything is sent**, instead of rounding it. *Reason:* FontLab stores kerning in whole units, rounded to the nearest with halves away from zero (567–569); the tool must never write a value nobody asked for. The user approved it as proposed.

## 2026-11-04: the kerning write tool (listener 0.124 / server 0.44)

- **`set_kerning` writes glyph : glyph pairs only, in the current master, with the `flags` key `((left, False), (right, False))`**; class names are not accepted. *Reason:* the `flags` form names both sides as glyphs, so a glyph named like a class never means the class (defect B); `set` accepts it (564).
- **All checks run before the first write; the first pair not confirmed by the re-read stops the request**, and the reply names the pairs that were set. *Reason:* the user's choice (2026-11-04); more predictable for the designer than continuing.
- **Not gated, like other reversible value writes; more than 250 pairs need the person's approval**, as for reads. Every reply tells the agent to say that the KERNING panel lists the pairs only after save and reopen (since server 0.45 also after a switch to another font and back; 573, 574), that closing asks no save question, and that Undo cannot take them back. *Reason:* the user approved the design as proposed; the facts are KW 557–563.

## 2026-11-04: save tests are a preference, not a rule

- **File > Save tests are avoided by preference, not forbidden.** One runs when it answers a question better than other means, and only after the user agrees to that test. The person saves through FontLab's GUI, to a disposable file outside the repository; no tool saves (save policy below). First case: KW 557–560, save and reopen after an API kerning write ([topics/kerning.md](topics/kerning.md) §13). *Supersedes* "File > Save tests are deferred" (2026-10-24) and that day's one-case exception (both archived). *Reason:* the user's choice, after that test showed the KERNING panel was only stale.

## 2026-11-04: the vertical check and quadratic extents (listener 0.121 / server 0.43)

- **`verified` on the modern route needs the vertical extent too, checked against FontLab's own `inkBox()`**; without a usable box the reply says `y_extent_checked: false` and why. *Supersedes* the horizontal-only check of the F1 fix (archived). *Reason:* `inkBox()` equalled the exact extents on five glyphs with no F1 (519–533); FontLab displays no vertical ink number to compare with (533).
- **Quadratic outlines are checked from their exact extents, computed by the server.** *Reason:* the user's choice; `inkBox()` agreed with them (522, 526).

## 2026-11-04: the modern API first

- **Prefer FontLab's modern API. A legacy call is used only where the modern one is missing or proven worse, and the reason and test number are recorded** in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10. Legacy calls in use before this decision stay until each is reviewed; until then their record says "not yet reviewed". **Goal:** every legacy call that might safely be replaced is replaced ([PROJECT.md](PROJECT.md), goal 6). *Reason:* the user's choice, after reviewing where both APIs can do a task: the legacy view can be stale or disagree with what FontLab shows (sidebearings, `font.info`, kerning), and touching it caused F1.

## 2026-11-04: macOS compatibility

- **Glyphbridge is kept macOS-compatible, although for now it can be tested only on Windows.** Where the code depends on the operating system (file locations, shortcuts, process calls), it handles macOS with the standard library as well. Such a macOS path is stub-tested where possible and recorded in [CHANGELOG.md](CHANGELOG.md) as never run on a Mac; nothing is called working on macOS before a live run there. Earlier cases: the launcher name (server 0.35 / 0.36) and the save shortcut (server 0.40). *Reason:* the user's choice: running tests on macOS may become possible only in the future.

## 2026-11-04: the F1 fix (listener 0.120 / server 0.42)

- **A glyph with modern nodes is read from the modern layer only**; when that read fails the reply is an error, never a legacy fallback. *Reason:* touching `glyph.layer` or reading `glyph.layers` of a Power Brush glyph lets the next `font.update()` flatten it (332–496).
- **After a width or sidebearing write the sync check compares only the legacy width**; drawings and new layers keep the full check. *Reason:* the same facts; `glyph.width` is safe (486–488).

## 2026-11-03: names read at the moment, not fixed strings

- **Text shown to the person or the agent names things from facts read at that moment** (the client's own name, the font's name and file, the system's save shortcut), never from fixed strings. A name the sender gives is shown as given, ambiguous ones such as `local-agent-mode` included; a missing one stays missing. *Reason:* the user's rule after test 290, where the delete dialog said "Claude" whoever sent the request. Built in listener 0.114 / server 0.40.
- **Not pursued** (the user's choice): the fixed "all 132 groups of Arial" in a debug note, and "FontLab 8" in tool descriptions and the unreachable message (the project's scope; no fact can be read there).
- **PostScript names come from the font package** (design C, listener 0.118 / server 0.41): the values FontLab's Font Info shows; no name is reported as "not set", since whether FontLab derived it or a person typed it cannot be read. *Reason:* tests 291–300 found no such marker, and showed the legacy `font.info` disagreeing with Font Info (298).

## 2026-11-03: several open fonts

- **`get_kerning` with several fonts open** (listener 0.112 / server 0.37, tests 265–268): it uses the current package only when its `path` is not empty and equals the current font's path, and otherwise refuses with the reason. *Supersedes* "kerning reads need exactly one open font" (2026-11-01, archived). *Reason:* the user approved it after T5 (262–264) showed that both views follow the font window in front and that `path` tells the fonts apart.
- **Goal: every operation works with 2, 3 or more fonts open, without confusion.** Closing the other fonts is the last resort, only where it is the only way to a goal. Then the tool tells the person to close them, and why: a limitation of how FontLab is built, shown by research, which Glyphbridge cannot work around. Until research has shown that, the message says the case is not supported yet. *Reason:* the user's choice, within the design rule of honest messages ([PROJECT.md](PROJECT.md)).

## 2026-11-03: proven container calls on native objects

- **Container access (`[]`, `get`, `keys`, `values`, `items`, `has_key`, iteration) on a native FontLab object is forbidden until proven, per object and call form.** The proven calls form one table in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10, with their test numbers. This replaces the blanket ban and its two one-off exceptions (the kerning `get`, the K11 `keys()`). *Reason:* the user's choice, the tidiest option. The ban rests on one crash (`font.shapes`), the `keys()` exception was noticed only after the live runs, and one proof path keeps the rules and the reports consistent.

## 2026-11-02: the client's name in the activity log

- **The log shows the name the app sends by itself** (MCP `clientInfo`), without the config entry name `glyphbridge-fontlab`. No label is set in the MCP configs. *Reason:* the user's choice: an ambiguous automatic name such as `local-agent-mode` is enough, and the configs stay untouched.

## 2026-11-01: code comments and tool docstrings

- **MCP tool docstrings are the agents' tool descriptions, so a tidy-up leaves them as they are. `#` comments stay next to the code they protect**; only references to session and test numbers shrink to the fact. *Reason:* about 11,000 words of history sat at the top of the two scripts; that tidy-up is archived.

## 2026-11-01: kerning groups

- **AI agents must be able to see which groups have which members** ([ROADMAP.md](ROADMAP.md) P1.6; proposed first and built only after approval). *Supersedes* "group membership is deliberately not read". *Reason:* K9 and the KERNING panel method depended on membership, which only FontLab's Classes panel could show; the members of one group are a small read.

## 2026-11-01: repository workflow (migration day)

- **No test may depend on the local file `savedtestfont.vfc` in the end.** Live tests build their reference glyphs in a fresh disposable font. `savedtestfont.vfc` may be used until it is no longer useful. Font files (`*.vfc`, `*.vfj`) are ignored by git. *Reason:* people who fork the repository must find everything they need in it ([ROADMAP.md](ROADMAP.md) §11).
- **`.gitignore` lists only what this project produces.** *Reason:* the generic Python template made the repository look less maintained.
- The other choices of that day (`tests/README.md`, the project folder, `.mcp.json`, `Notes\`) are in force and archived.

## 2026-10-27: kerning (v11 session)

- **Read only the pairs a task needs, never the whole kerning table or font.** *Reason:* token cost.
- **There are no hard limits, but there is a threshold at 250 pairs.** Above it the agent must warn the person, say how many pairs and why, and ask. Only after a yes may it repeat the call with `confirmed_large_read=true`. *Reason:* the user's words: "Let there be no hard limits and let there be a threshold at 250."

## October 2026: v8 session (exact day not recorded)

- **Tests with glyphs above about 150 nodes go to the very end** (the LAST block). *Reason:* they are costly in tokens and time.

## October 2026: server v0.18 (exact day not recorded)

- **Save policy.** No Glyphbridge tool ever saves the font, and none may be built that does; saving is the person's duty. After a package of changes the agent shows **one** bold reminder in chat, through `finish_changes`: never one per step, and never as a FontLab dialog. *Reason:* the user wants full control over what is kept.

## Standing design choices (from the start; exact dates not recorded)

- **The project builds its own bridge** instead of a third-party FontLab MCP server. *Reason:* that server reported false successes. This leads to the design rule in [PROJECT.md](PROJECT.md).
- **Width and Unicode writes are not confirmation-gated; delete is** (a Yes/No dialog in FontLab). *Reason:* the first two are reversible.
