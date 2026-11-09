# Decisions

Active decisions only, newest first. Each entry gives the date, the decision and the reason. Superseded or no longer relevant entries move to [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). Where the chat-era record gives no exact day, the entry says so.

## 2026-11-10: tool-written kerning pairs in the KERNING panel

- **Goal: a kerning pair written by a tool shows in FontLab's KERNING panel at once, without a save and reopen** ([PROJECT.md](PROJECT.md), goal 8). *Reason:* the user's goal; until then a designer can take a valid pair for missing, or kern it again.

## 2026-11-10: the changed icon can lag behind a tool write (server 0.55)

- **Where FontLab's changed icon is not reliably immediate after a kind of tool write, the agent tells the person, once per package of changes: the icon may stay dark until the mouse moves near the font's title, which can make FontLab redraw it, and a dark icon does not mean the change failed.** *Reason:* the user's policy; a verified write with a dark icon looks like nothing happened. Today this covers `set_kerning` (719, 722, 723, 725, 726 needed a hover; 724 did not).
- **A kind of write observed as immediate gets no such note.** Glyph writes: blue with the mouse on Claude Desktop and FontLab unfocused (668, 669, 677–681, conditions by the user's recollection). Deletes: blue at once (688), but always after the person's click on Yes in FontLab's dialog, so the lag would not be seen in use.
- **The note is retired by evidence, not by a reading:** no reading follows the icon (659). `_ICON_MAY_LAG_KERNING = False`, with its own entry here, after five live runs in a row blue at once, mixing new and changed pairs, with the mouse outside FontLab. The test is repeated on each new FontLab version and when the marking code changes ([CHECKLIST.md](CHECKLIST.md) row 84).

## 2026-11-10: a kerning write is marked through a glyph of a changed pair (listener 0.134 / server 0.54)

- **A kerning write that changed an entry makes one `notifyChangesApplied` call, on the left glyph of the first changed pair, then its right glyph, then the sides of later changed pairs, never `.notdef`, at most 20 tried; `via_glyph` names it. A request that changed nothing makes no call. The reply says what was done and never claims FontLab's icon or question.** *Reason:* a kerning write has no glyph of its own to report; the call brought the save question back (713–717, 718–721). The user approved the design as proposed.

## 2026-11-09: a delete is marked through a surviving glyph (listener 0.133 / server 0.53)

- **After a verified delete the listener makes one `notifyChangesApplied` call on the first surviving glyph that is not `.notdef` and has a modern layer, at most 20 tried; `via_glyph` names it. When none can be notified, the reply gets `save_question_note`.** *Reason:* a deleted glyph cannot be reported, and this brought the save question back (684–688). The user approved the design as proposed.

## 2026-11-09: the save question for every tool change (server 0.52)

- **Goal: FontLab offers its save question for every tool change, as it does for a GUI change** ([PROJECT.md](PROJECT.md), goal 7). *Reason:* the user's goal; FontLab does not treat API writes like GUI writes, so closing can lose tool work silently (S1).
- **`save_question_note` depends only on whether the mark call was made without an error; `glyph_has_changes` stays in the reply as information.** *Reason:* it read false while the mark worked (668), and no reading follows FontLab's icon (659). The user approved the fix as proposed.

## 2026-11-09: the live-proven record gets its own file

- **The live-proven record and the version needs move unchanged to [WHAT-WORKS.md](WHAT-WORKS.md) (budget 1,500), which is not a core file. CURRENT-STATUS.md keeps a summary by area, and [AGENTS.md](../AGENTS.md) says when to read the file.** *Reason:* the user's choice; the record grows with every milestone, and most sessions need only one area of it.

## 2026-11-09: tool writes mark the font as changed (listener 0.132 / server 0.51)

- **After a verified, synced glyph write, the listener makes one `flItems.notifyChangesApplied` call, so that FontLab asks to save on close; nothing is ever saved. The reply says what was done (`fontlab_changed_mark`) and never claims FontLab's icon or question; a write it could not mark gets `save_question_note`.** Kerning writes are not marked yet (stage 2, research first). `_MARK_CHANGED = False` switches it off. *Reason:* closing lost tool work silently (S1); the call brought the question back and a control without it did not (657–667). The user approved the design as proposed.

## 2026-11-09: components against their source (listener 0.130 / server 0.50)

- **A composite found behind its source reads `unverified`, with both boxes and an instruction to tell the person.** *Reason:* its numbers match what FontLab holds, but can change at the next GUI edit (638–653). The user approved the design as proposed.
- **The per-element and in-step checks cover plain offsets only;** anything else stays as before and says `"unknown"`. *Reason:* only offsets were tested.

## 2026-11-09: a new glyph gets its layer (listener 0.127 / server 0.48)

- **`create_glyph` creates the glyph's layer at once in a font with one master. When it cannot, the glyph is still created and the reply says why, with a warning about Add Component.** *Reason:* Add Component crashes FontLab on a glyph with no layer (612–619); refusing the create would remove what works today in order to protect a later GUI step. The user approved the design as proposed.

## 2026-11-04: save tests are a preference, not a rule

- **File > Save tests are avoided by preference, not forbidden.** One runs when it answers a question better than other means, and only after the user agrees to that test. The person saves through FontLab's GUI, to a disposable file outside the repository; no tool saves (save policy below). First case: KW 557–560, save and reopen after an API kerning write ([topics/kerning.md](topics/kerning.md) §13). *Supersedes* "File > Save tests are deferred" (2026-10-24) and that day's one-case exception (both archived). *Reason:* the user's choice, after that test showed the KERNING panel was only stale.

## 2026-11-04: the modern API first

- **Prefer FontLab's modern API. A legacy call is used only where the modern one is missing or proven worse, and the reason and test number are recorded** in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10. Legacy calls in use before this decision stay until each is reviewed; until then their record says "not yet reviewed". **Goal:** every legacy call that might safely be replaced is replaced ([PROJECT.md](PROJECT.md), goal 6). *Reason:* the user's choice, after reviewing where both APIs can do a task: the legacy view can be stale or disagree with what FontLab shows (sidebearings, `font.info`, kerning), and touching it caused F1.

## 2026-11-04: macOS compatibility

- **Glyphbridge is kept macOS-compatible, although for now it can be tested only on Windows.** Where the code depends on the operating system (file locations, shortcuts, process calls), it handles macOS with the standard library as well. Such a macOS path is stub-tested where possible and recorded in [CHANGELOG.md](CHANGELOG.md) as never run on a Mac; nothing is called working on macOS before a live run there. Earlier cases: the launcher name (server 0.35 / 0.36) and the save shortcut (server 0.40). *Reason:* the user's choice: running tests on macOS may become possible only in the future.

## 2026-11-03: names read at the moment, not fixed strings

- **Text shown to the person or the agent names things from facts read at that moment** (the client's own name, the font's name and file, the system's save shortcut), never from fixed strings. A name the sender gives is shown as given, ambiguous ones such as `local-agent-mode` included; a missing one stays missing. *Reason:* the user's rule after test 290, where the delete dialog said "Claude" whoever sent the request. Built in listener 0.114 / server 0.40.
- **PostScript names come from the font package** (design C, listener 0.118 / server 0.41): the values FontLab's Font Info shows; no name is reported as "not set", since whether FontLab derived it or a person typed it cannot be read. *Reason:* tests 291–300 found no such marker, and showed the legacy `font.info` disagreeing with Font Info (298).

## 2026-11-03: several open fonts

- **`get_kerning` with several fonts open** (listener 0.112 / server 0.37, tests 265–268): it uses the current package only when its `path` is not empty and equals the current font's path, and otherwise refuses with the reason. *Supersedes* "kerning reads need exactly one open font" (2026-11-01, archived). *Reason:* the user approved it after T5 (262–264) showed that both views follow the font window in front and that `path` tells the fonts apart.
- **Goal: every operation works with 2, 3 or more fonts open, without confusion.** Closing the other fonts is the last resort, only where it is the only way to a goal. Then the tool tells the person to close them, and why: a limitation of how FontLab is built, shown by research, which Glyphbridge cannot work around. Until research has shown that, the message says the case is not supported yet. *Reason:* the user's choice, within the design rule of honest messages ([PROJECT.md](PROJECT.md)).

## 2026-11-03: proven container calls on native objects

- **Container access (`[]`, `get`, `keys`, `values`, `items`, `has_key`, iteration) on a native FontLab object is forbidden until proven, per object and call form.** The proven calls form one table in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10, with their test numbers. This replaces the blanket ban and its two one-off exceptions (the kerning `get`, the K11 `keys()`). *Reason:* the user's choice, the tidiest option. The ban rests on one crash (`font.shapes`), the `keys()` exception was noticed only after the live runs, and one proof path keeps the rules and the reports consistent.

## 2026-11-01: code comments and tool docstrings

- **MCP tool docstrings are the agents' tool descriptions, so a tidy-up leaves them as they are. `#` comments stay next to the code they protect**; only references to session and test numbers shrink to the fact. *Reason:* about 11,000 words of history sat at the top of the two scripts; that tidy-up is archived.

## 2026-11-01: kerning groups

- **AI agents must be able to see which groups have which members** ([ROADMAP.md](ROADMAP.md) P1.6; proposed first and built only after approval). *Supersedes* "group membership is deliberately not read". *Reason:* K9 and the KERNING panel method depended on membership, which only FontLab's Classes panel could show; the members of one group are a small read.

## 2026-11-01: repository workflow (migration day)

- **No test may depend on the local file `savedtestfont.vfc` in the end.** Live tests build their reference glyphs in a fresh disposable font. `savedtestfont.vfc` may be used until it is no longer useful. Font files (`*.vfc`, `*.vfj`) are ignored by git. *Reason:* people who fork the repository must find everything they need in it ([ROADMAP.md](ROADMAP.md) §11).

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
