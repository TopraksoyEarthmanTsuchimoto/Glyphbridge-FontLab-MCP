# Decisions

Active decisions only, newest first. Each entry gives the date, the decision and the reason. Superseded or no longer relevant entries move to [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). Where the chat-era record gives no exact day, the entry says so.

**Budget changes are not recorded here** (the user's choice of 2026-11-20, unlike HOW-TO-GET-ORGANIZED.md): each one, with its date and reason, goes to "Budget history" in [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md); current values are in [MARKDOWN-MAP.md](MARKDOWN-MAP.md). *Reason:* a budget's history is not an active decision, and its rules are in [AGENTS.md](../AGENTS.md).

## 2026-11-20: CODEX.md, notes for Codex only

A root file beside CLAUDE.md, named in AGENTS.md's startup line. *Reason:* Codex loads only one instruction file per folder (AGENTS.md here) and has no import syntax, per its documentation; named CODEX.md after the agent, not the app. Rules for every agent stay in AGENTS.md.

## 2026-11-19: removing kerning pairs, `remove_kerning` (research listener 0.191, KD 1380–1390, KDC 1391–1397; built listener 0.192 / server 0.76)

- **A tool of its own; `set_kerning` stays unchanged.** *Reason:* removing is a different act from setting a value; a separate name keeps an agent from removing a pair by passing 0; `set_kerning` is live-proven.
- **A pair with no glyph : glyph entry gets a note, not an error; the other pairs go on.** When a class gives the pair its value, the note names the class and the value that still applies.
- **A glyph : glyph exception over a class may be removed; the reply reports the class value that applies again** (`class_value_applies`). *Reason:* KDC 1395–1397 ([topics/kerning.md](topics/kerning.md) §16): only the exception went, the class value applied again, the panel showed the class row.
- **More than 250 pairs need the person's approval** (`confirmed_large_write`), as `set_kerning`.
- **The first removal that cannot be confirmed stops the request;** the pairs before it are reported removed, the rest `not attempted`, as `set_kerning`.
- **The call is `remove(((left, False), (right, False)))`; its return value is ignored, only the re-read counts** (the entry `None` after, `len()` one lower). *Reason:* defect B; the return value follows the form, not the outcome (1387, 1390).
- **After a removal that changed the table: the mark (`notifyChangesApplied`) and the panel refresh (`notifyPackageContentUpdated`), as `set_kerning`;** no change, no calls. The mark for a removal alone is untested (Demo mode).
- *Reason for the rest:* the user's answers, one question at a time.

## 2026-11-19: Glyphbridge Community Source-Available License

- **Glyphbridge uses custom source-available terms, not an OSI open-source license.** Eligible users are individuals acting on their own behalf, schools and non-profits of any size, and organizations with fewer than 10 people (owners, employees, and regular freelancers; not customers or one-time suppliers). Larger organizations other than schools and non-profits need a separate license. Eligible commercial use is free; Glyphbridge itself cannot be sold, while users may sell work made using it.
- **Free copies and modified forks may be shared under the unchanged license,** with the copyright notice retained, changes identified, and no claim that a fork is official. Modified forks may be public, but use rights remain limited to eligible users. Unmodified copies may not be re-hosted as separate downloads; direct people to the official installation page.
- **The effect of an eligible organization's later growth is intentionally unspecified.** The four URL placeholders remain for now, and the values section is non-binding. License text: [LICENSE](../LICENSE). *Reason:* the user's stated access and sharing goals.

## 2026-11-19: the author's name in LICENSE

The rule against personal data in live files ([AGENTS.md](../AGENTS.md)) gets one exception: the author's name as the copyright holder in the LICENSE file. Nothing else personal goes there or anywhere else (no e-mail address, user name or path). Reason: a license needs a named copyright holder; the user's choice before adding LICENSE.

## 2026-11-19: kerning group membership, `get_kerning_groups` (P1.6; research listener 0.188–0.189; built listener 0.190 / server 0.75)

- **The side comes from the modern `items()` of the master's kerning groups (route C), not from the legacy `kerningLeft` / `kerningRight` nor from `values()` matched by members.** *Reason:* the user's choice; one modern call gives name, members and side (KG 1373–1375, [topics/kerning.md](topics/kerning.md) §9.10).
- **A read tool of its own; `get_kerning` stays unchanged.** *Reason:* separate reply shapes and limits; `get_kerning` is live-proven.
- **Every kerning group may be listed; above 250 groups only after the person's approval** (`confirmed_large_read`, the rule of 2026-10-27). **The full list includes members.**
- **Kerning groups only.** OpenType classes and Glyph tags are not read by this tool. **Glyphbridge must eventually work with OpenType classes too, through a tool of their own** ([ROADMAP.md](ROADMAP.md) P1.7).
- **Every read is cross-checked with `getAllGroups()`;** a group whose sources disagree is reported with both versions, never settled by the tool.
- **An unknown name is an error for that name only;** the other names are read, and a glyph in no kerning group gets a plain note.
- *Reason for the rest:* the user's answers, one question at a time; the font and master matching follow `get_kerning`.

## 2026-11-18: every AI app is treated equally

The docs name AI apps side by side, never one "instead of" another. Shared steps are written for "your AI app", and each app gets a section of the same rank ([README.md](../README.md)). Apps may be listed in an order, but none is presented as the default. Reason: the user's choice, after ChatGPT Desktop joined Claude Desktop as a tested client.

## 2026-11-18: `add_component` for a glyph that is not empty (research listener 0.180–0.185; built listener 0.186–0.187 / server 0.73–0.74)

Merged on 2026-11-18 from three entries; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md).
- **Researched in the user's route order: a temporary layer in the target glyph; then setting the shapes aside and putting them back; then a component shape made directly; a scratch glyph only if all three fail.** *Reason:* FontLab's recipe build on that glyph replaced its contents (NE 1268, [topics/reading.md](topics/reading.md)); a scratch glyph would need a hidden delete in every call (the F1 risk of `delete_glyph`) and could be left behind by a failure. The first route worked (TL 1294–1300).
- **`add_component` is extended, not joined by a new tool:** an empty target keeps its route, a target with content gets the temporary-layer route inside the same request (`placement`). *Reason:* one tool for agents; run C showed the route is safe only when nothing falls between its steps.
- **A failure partway restores the glyph fully:** the components the call added are removed with `removeShape`, the temporary layer removed, the width written back, and a re-read confirms (`restore.restored`). *Reason:* `removeShape` is proven exact (RM, RC); a half-built glyph is left to nobody.
- **A target may hold contours, components and Power Brush shapes; Power Brush was researched first** (listener 0.185, PB 1328–1345). No `inkBox()` is called on a brush shape.
- **The full sync check for every target, brush targets included.** *Reason:* PB-F kept its brush through two updates; one rule for all writes. F1 is not isolated: a brush flattened in later use reopens this.
- **Both forms on a target with content,** with the list form's rules (soft limit 30, no underscore names); the list form there live since NB 1350.
- **Every target, both routes, both forms, needs exactly one layer, the active one; anything else is refused before any change** (0.187 / 0.74). *Reason:* in NB 1353 an empty active layer beside a full one took the empty route, and the component named that layer as its source's. The user chose this rule (A) over requiring only the master layer active (B): it is the rule proven in 1351.
- *Reason for all:* the user's answers, one question at a time; each build approved as proposed. In the build, the reply field is `placement` (`route` already existed), and each new component names its source's own layer.

## 2026-11-18: removing components, `remove_component` (listener 0.179 / server 0.72)

- **A component is named by its index in `get_glyph_outline`'s element list, with the source and offset expected there; any mismatch refuses the whole call before anything changes.** *Reason:* a stale read becomes a refusal, as with `move_nodes`' `from`; two copies of one source at one place stay apart.
- **One form per call: `component` or a `components` list. In a list every index refers to the glyph as read before the call, every entry is checked first, and removal runs from the highest index down. No size limit.**
- **Any glyph holding a component is accepted, also one with contours; every other element is confirmed unchanged.** A Power Brush shape is refused (F1; added in the build).
- **A target whose auto layer is on is refused; a leftover recipe is kept and reported.** *Reason:* an auto layer is FontLab's to rebuild; RM tested only glyphs with it off.
- **The call is `layer.removeShape(component, False)`.** *Reason:* it removed exactly the component asked for (RM 1241–1245), `recursive` made no difference, and `clearComponents()` changed nothing (1246).
- **The font is marked whenever the outline changed; a width FontLab changed is written back once and reported.** *Reason:* the precedents of `move_nodes` and `add_component`.
- *Reason for the rest:* the user's answers, one question at a time.

## 2026-11-17: placing components, `add_component` (listener 0.169–0.175 / server 0.66–0.69)

Moved to [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md) on 2026-11-19 (budget), still in force: FontLab's recipe build (`recipe`, `autoLayer`, `buildAuto()`) at whole-unit offsets; one component or a `components` list; soft limit 30 with the person's approval above it; the width read before, written back and confirmed; underscore names refused in a list.

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
