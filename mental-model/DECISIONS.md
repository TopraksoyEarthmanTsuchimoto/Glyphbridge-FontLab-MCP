# Decisions

Active decisions only, newest first. Each entry gives the date, the decision and the reason. Superseded or no longer relevant entries move to [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). Where the chat-era record gives no exact day, the entry says so.

## 2026-11-17: placing components, `add_component` (listener 0.169–0.175 / server 0.66–0.69)

Condensed on 2026-11-17 from three entries, all built; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md).
- **The modern route: FontLab's recipe build (`recipe`, `autoLayer = True`, `buildAuto()`, `autoLayer = False`); the legacy `fgComponent` route is not probed.** *Reason:* the user asked whether legacy was the only way; the modern route worked (1041b–1042b, [topics/reading.md](topics/reading.md)) and the modern-API-first decision applies. Revisit only if it cannot do what a tool needs.
- **Into an existing, empty glyph layer, at whole-unit offsets set after the build; one form per call: a single component (`component`, `x`, `y`) or a `components` list; repeated sources allowed.** *Reason:* only that was proven with the width unchanged (1049); one recipe build placed them all (1110–1177); repeats are separate components, each movable alone (1172–1177).
- **Soft limit 30** (tested at 2–5, 15 and 30, the sizes between assumed safe): above it the first call changes nothing; the agent tells the person that only up to 30 was tested, asks, and repeats with a confirmation flag after a yes. **No hard ceiling** but the listener's request-body size. *Reason:* the user's rule, with Chinese characters in mind; the ask-first precedent of kerning reads.
- **The width is read before, written back after, and confirmed.** *Reason:* FontLab set 500 every time (1110–1172).
- **A failure partway: placing stops, then the auto layer is switched off, the recipe cleared and the width put back, each component and step reported; nothing else is restored.** *Reason:* `autoLayer = False` leaves the glyph editable, not a locked auto layer (1055a); `recipe = ""` clears the leftover recipe (1058); no proven way to remove a component (1090).
- **With several fonts open, the tool follows the font in front.** *Reason:* the rule of the other write tools ([PROJECT.md](PROJECT.md), goal 5); live with two fonts (1091–1095).
- **The element reader has no element limit and reports its timing,** replacing both 20-element caps, none with a recorded reason (`_COMPONENT_BOX_MAX`, v0.130; `_TRYSHAPEBOX_MAX_SHAPES`, v0.129). *Reason:* above 20 `source_in_step` was "unknown" (1168); 30 boxes took under 10 ms.
- **In the list form a source name with an underscore is refused before anything changes; after a failed build each entry's state is matched by source name, and the reply lists what the glyph holds** (0.175 / 0.69). *Reason:* FontLab's recipe reads `a_b` as a ligature of its parts (1234); a placed component was called "not reached" (1200–1208).
- *Reason for all but the first:* the user's answers, one question at a time.

## 2026-11-15: `move_nodes`, the first edit tool (listener 0.153–0.154 / server 0.63–0.65)

Condensed on 2026-11-17 from three entries; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md).
- **Each move gives `from` and `to`; a `from` that differs from the node refuses the whole call.** *Reason:* a stale read becomes a refusal, not a wrong edit.
- **No automatic restore when the re-read differs;** the font is marked whenever its outline changed. *Reason:* a restore is an untested second write; the person decides.
- **One plain shape only, for now.** *Reason:* only that was probed; each shape may carry its own transform.
- **`verified` means the re-read nodes match; the sidebearings are computed from them and FontLab's advance width; FontLab's own values are shown apart, with one plain note for the person when they lag. No refresh call** (0.154 / 0.64). *Reason:* FontLab's sidebearings and ink box lag after an API node move and nothing tried refreshes them (MN 1001–1015).
- **No `display_note`; `undo_note` wherever the outline changed, told once per conversation** (server 0.65). *Reason:* `display_note` gave repaint steps, against the decision of 2026-11-13; Edit > Undo lists a tool move but left the nodes moved (1023).
- *Reason for all:* the user's answers and approvals.

## 2026-11-14: editing existing glyphs

- **AI agents must be able to edit an existing glyph through Glyphbridge: move nodes, add a contour to an existing shape, redraw an outline in place; in the end, every kind of glyph manipulation.** Every edit is verified by a re-read, and the layer guard's refusal is lifted only by a tool built for that edit. *Reason:* the user's requirement; today an agent must delete a glyph and draw it again.

## 2026-11-13 to 2026-11-17: word budgets raised by the user's choice

Condensed on 2026-11-17 from nine entries; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). Current budgets and their history: [MARKDOWN-MAP.md](MARKDOWN-MAP.md).
- **CURRENT-STATUS.md 2,500, then 2,750, then 3,000; DECISIONS.md 2,500, then 2,800; PROJECT.md 1,000; MARKDOWN-MAP.md 1,000; WATCH-POINTS.md 2,500; WHAT-WORKS.md 2,250, then 2,500.** Nothing was trimmed or moved for any of them. *Reason:* the user's choice each time.

## 2026-11-13: a package is told apart by its fgId (listener 0.150 / server 0.62)

- **The first glyph of a new font takes its layer name from the glyph's own package (`flGlyph.package`), with any number of fonts open, only when that package's `fgId` equals the current package's. No product code uses `flPackage.isEqual`; `create_font` compares `fgId` as well.** *Reason:* `w.package` named the glyph's own font, and `isEqual` called two different packages equal (930, 931); the user approved the design as proposed.

## 2026-11-13: notes for the person (listener 0.147 / server 0.61)

- **No GUI-repaint chores for the person.** Where FontLab's display lags behind an API write, the person gets one plain sentence (what they see, that it is only a display delay, where the real value shows), never a sequence of dialog steps to force a repaint. *Reason:* the user's UX rule; 921 and 922 found no single step.
- **The agent points the person to FontLab's OUTPUT panel once per conversation.** *Reason:* the user's choice; a person who never opens it misses its warnings.

## 2026-11-12: the create-font tool (listener 0.146 / server 0.60)

- **`create_font` works whether or not other fonts are open, and may make more than one font per listener run;** the once-per-run limit stays on the probe. *Reason:* the user's choice; 834 and 835 made two fonts in one FontLab session, and the native reference belongs to FontLab, not to the listener.
- **A named font also gets the legacy `font.info.familyName`,** written only when the font in front reads the new font's own family. *Reason:* the user's choice (option A): the server names a font from it, and the FONTS panel gave the font its own line only with it (885). Risk: it reverted once (872).
- **A family name gives a PostScript name of at most 63 characters and holds none of `[](){}<>/%`; one check serves `create_font` and the `/debug/tryfont` probe.** *Reason:* the user's approval; the approved "58 characters" let the PostScript name reach 66, and PostScript names may not hold those characters.
- **What can be improved goes to [ROADMAP.md](ROADMAP.md) (P0.5c, P0.9, P0.10); what cannot is told to the person, in the agent's reply and in FontLab's OUTPUT panel.** *Reason:* the user's rule.

## 2026-11-12: watch points hold the open question only

- **An entry in [WATCH-POINTS.md](WATCH-POINTS.md) holds what is open and what would settle it; the evidence lives in the topic file it links to.** *Reason:* the user's choice over a seventh raise: the file had grown by collecting the story of each run. Nothing is cut; evidence moves, word for word where the topic file lacks it.

## 2026-11-11: new fonts made by an agent

Condensed on 2026-11-13; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md).
- **An agent-made font matches one made with File > New Font as closely as FontLab allows, also with other fonts open; a difference is recorded and the person is told.** Carried out by `create_font` (0.146–0.150). *Reason:* the user's requirement (goal 5, [PROJECT.md](PROJECT.md)).
- **The Font window's encoding of a GUI-made font: won't-fix for now** (agent-made fonts open with None). *Reason:* only FontLab's Qt widget can set it, fragile across versions ([topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k, E1).
- **Names: with no name given, FontLab's own (`Unnamed`, `Unnamed1`, …); a name asked for is set as Font Info would set it. Whenever font names come up, the agent offers to explain the fields of Font Info's Names page.** *Reason:* the user's requirements; that page confuses new users.

## 2026-11-11: research on a PC where FontLab cannot save

- **While FontLab runs in Demo mode, the agent tells the user before any live research starts whether it strictly needs a File > Save stage. When it does not, the agent says so, and that the research should then be completable on this PC. Research that needs a save waits for the user's choice** (for example, a PC with a fully functional FontLab). *Reason:* the user's rule. FontLab's Demo mode does everything except save files, and the project may later continue on a PC where FontLab is fully functional. This narrows "save tests are a preference, not a rule" (2026-11-04) on such a PC, it does not replace it.

## 2026-11-09 to 2026-11-10: tool writes, FontLab's save question and the KERNING panel (S1; listener 0.132–0.136 / server 0.51–0.57)

Condensed on 2026-11-11 from six entries and again on 2026-11-13; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). How the calls work: [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §2.
- **FontLab offers its save question for every tool change, and a tool-written kerning pair shows in the KERNING panel at once** ([PROJECT.md](PROJECT.md), goals 7 and 8). After a verified write the listener makes one FontLab notification; nothing is ever saved. *Reason:* closing lost tool work silently (S1).
- **Replies say what was done, never what FontLab shows.** *Reason:* no reading follows FontLab's icon or panel (659, 668).
- **Switches** `_MARK_CHANGED`, `_REFRESH_KERNING_PANEL`, `_ICON_MAY_LAG_KERNING` (false since server 0.57). Where the icon may lag after another kind of write, the agent tells the person once per package; the kerning check is repeated on each new FontLab version ([RUNBOOK.md](RUNBOOK.md) §13, 3g).

## 2026-11-09: components against their source (listener 0.130 / server 0.50)

- **A composite found behind its source reads `unverified`, with both boxes and an instruction to tell the person.** *Reason:* its numbers match what FontLab holds, but can change at the next GUI edit (638–653). The user approved the design as proposed.
- **The per-element and in-step checks cover plain offsets only;** anything else stays as before and says `"unknown"`. *Reason:* only offsets were tested.

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

## 2026-11-01: code comments and tool docstrings

- **MCP tool docstrings are the agents' tool descriptions, so a tidy-up leaves them as they are. `#` comments stay next to the code they protect**; only references to session and test numbers shrink to the fact. *Reason:* about 11,000 words of history sat at the top of the two scripts; that tidy-up is archived.

## 2026-11-01: kerning groups

- **AI agents must be able to see which groups have which members** ([ROADMAP.md](ROADMAP.md) P1.6; proposed first and built only after approval). *Supersedes* "group membership is deliberately not read". *Reason:* K9 and the KERNING panel method depended on membership, which only FontLab's Classes panel could show; the members of one group are a small read.

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
