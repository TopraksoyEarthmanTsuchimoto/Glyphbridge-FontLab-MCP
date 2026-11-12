# Decisions

Active decisions only, newest first. Each entry gives the date, the decision and the reason. Superseded or no longer relevant entries move to [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). Where the chat-era record gives no exact day, the entry says so.

## 2026-11-12: the create-font tool (listener 0.146 / server 0.60)

- **`create_font` works whether or not other fonts are open, and may make more than one font per listener run;** the once-per-run limit stays on the probe. *Reason:* the user's choice; 834 and 835 made two fonts in one FontLab session, and the native reference belongs to FontLab, not to the listener.
- **A named font also gets the legacy `font.info.familyName`,** written only when the font in front reads the new font's own family. *Reason:* the user's choice (option A): the server names a font from it, and the FONTS panel gave the font its own line only with it (885). Risk: it reverted once (872).
- **A family name gives a PostScript name of at most 63 characters and holds none of `[](){}<>/%`; one check serves `create_font` and the `/debug/tryfont` probe.** *Reason:* the user's approval; the approved "58 characters" let the PostScript name reach 66, and PostScript names may not hold those characters.
- **What can be improved goes to [ROADMAP.md](ROADMAP.md) (P0.5c, P0.9, P0.10); what cannot is told to the person, in the agent's reply and in FontLab's OUTPUT panel.** *Reason:* the user's rule.

## 2026-11-12: CURRENT-STATUS budget raised to 2,200

- **The word budget of [CURRENT-STATUS.md](CURRENT-STATUS.md) is 2,200 (was 2,000); the reference totals in [MARKDOWN-MAP.md](MARKDOWN-MAP.md) are now 11,500 and 11,000.** *Reason:* the user's choice; the file stood at 1,918 words with live research under way. Finished items still move to the archive.

## 2026-11-12: watch points hold the open question only

- **An entry in [WATCH-POINTS.md](WATCH-POINTS.md) holds what is open and what would settle it; the evidence lives in the topic file it links to. The budget stays 2,200.** *Reason:* the user's choice over a seventh raise: the file had grown by collecting the story of each run. Nothing is cut; evidence moves, word for word where the topic file lacks it.

## 2026-11-11: new fonts made by an agent

- **A font made through Glyphbridge should match one made with File > New Font as closely as FontLab allows, and making one while other fonts are open must become reliable** (the create-font tool, [ROADMAP.md](ROADMAP.md) P0.3). Where the API result differs from the GUI's, the difference is recorded and the person is told. *Reason:* the user's requirement, so that what an agent does resembles what the person would do by hand; part of goal 5 in [PROJECT.md](PROJECT.md). The names already match (NF 831–835).
- **The Font window's encoding: agent-made fonts need no step (they open with None); setting the box of a GUI-made font through the API is won't-fix for now.** The only route found is the Font window's Qt widget, kept as a candidate in P0.3. *Reason:* File > New Font ignores the "Default: Encoding" preference (840), and driving FontLab's widgets is fragile across versions, for the gain of a few clicks ([topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k, E1).
- **Names: when the person has given no name, the new font gets FontLab's own (`Unnamed`, `Unnamed1`, …, as with File > New Font); when the person asks for a name, the tool sets it as Font Info would. Whenever font names come up, the agent asks whether the person wants the fields of Font Info's Names page explained, and explains them on request.** *Reason:* the user's requirements (2026-11-11); Font Info opens on that page, which confuses new users. Setting names through the API is researched in NM 841–914 and built in listener 0.146 / server 0.60 ([ROADMAP.md](ROADMAP.md) P0.4).
- **The unnamed and the named route ship together, in one build after the naming research ([ROADMAP.md](ROADMAP.md) P0.4).** *Reason:* the user's choice (2026-11-11).

## 2026-11-11: research on a PC where FontLab cannot save

- **While FontLab runs in Demo mode, the agent tells the user before any live research starts whether it strictly needs a File > Save stage. When it does not, the agent says so, and that the research should then be completable on this PC. Research that needs a save waits for the user's choice** (for example, a PC with a fully functional FontLab). *Reason:* the user's rule. FontLab's Demo mode does everything except save files, and the project may later continue on a PC where FontLab is fully functional. This narrows "save tests are a preference, not a rule" (2026-11-04) on such a PC, it does not replace it.

## 2026-11-09 to 2026-11-10: tool writes, FontLab's save question and the KERNING panel (S1; listener 0.132–0.136 / server 0.51–0.57)

Condensed on 2026-11-11 from six entries; their full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md).
- **Goals: FontLab offers its save question for every tool change, as for a GUI change, and a kerning pair written by a tool shows in the KERNING panel at once** ([PROJECT.md](PROJECT.md), goals 7 and 8). *Reason:* closing lost tool work silently (S1); a designer could take a valid pair for missing, or kern it again.
- **After a verified write the listener makes one `flItems.notifyChangesApplied` call:** for a synced glyph write on that glyph (0.132); for a delete on the first surviving glyph that is not `.notdef` and has a modern layer (0.133); for a kerning write that changed an entry on a glyph of a changed pair, left side first (0.134). At most 20 glyphs are tried and `via_glyph` names the one used; a request that changed nothing makes no call. After such a kerning write it also makes one `notifyPackageContentUpdated(<package fgId>)` (0.136). Nothing is ever saved. *Reason:* each call brought FontLab's question or panel back where a control did not (657–667, 684–688, 713–721, 738–743). The user approved each design as proposed.
- **Replies say what was done (`fontlab_changed_mark`, `fontlab_panel_refresh`), never what FontLab shows; `save_question_note` depends only on whether the mark call was made without an error.** *Reason:* no reading follows FontLab's icon or panel (659, 668).
- **Switches** `_MARK_CHANGED` and `_REFRESH_KERNING_PANEL`; `_ICON_MAY_LAG_KERNING = False` since server 0.57, after five runs in a row blue at once (748–753). Where the icon is not reliably immediate after another kind of tool write, the agent tells the person, once per package; the kerning check is repeated on each new FontLab version ([RUNBOOK.md](RUNBOOK.md) §13, 3g).

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
