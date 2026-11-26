# Decisions

Active decisions only, grouped by theme, newest first within each theme. Each entry gives the date, the decision and the reason. Other files cite an entry by its date, so every entry keeps its date in its heading, and a merged entry keeps all of its dates. Superseded or no longer relevant entries, and the full text of merged or condensed ones, move to [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). Where the chat-era record gives no exact day, the entry says so.

**Budget changes are not recorded here** (the user's choice of 2026-11-20, unlike HOW-TO-GET-ORGANIZED.md): each one, with its date and reason, goes to "Budget history" in [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md); current values are in [MARKDOWN-MAP.md](MARKDOWN-MAP.md). *Reason:* a budget's history is not an active decision, and its rules are in [AGENTS.md](../AGENTS.md).

**Themes:** [Principles and working rules](#principles-and-working-rules) · [Talking to the person](#talking-to-the-person) · [Fonts](#fonts) · [Glyphs](#glyphs) · [Kerning](#kerning) · [Repository and documents](#repository-and-documents)

## Principles and working rules

### 2026-11-26: every request for a user action says when

A restart or GUI request says whether to act now or after which step or check, and what not to touch until the next step ([AGENTS.md](../AGENTS.md), the restart rule). *Reason:* the AG3 request named what to restart and what to leave running, but not when, while its first reading depended on Antigravity making no call before the cache was read; the user chose one rule for every user action over one for restarts only.

### 2026-11-25: questions in FontLab during live tests

- **Each test glyph is named after the button the person clicks:** `_yes` or `_yesall` for Yes, `_no` for No, `_nodlg` where no question may appear (if one does: No, and say so), `_noanswer` where the person clicks nothing and lets the question close by itself (added 2026-11-25, the user's choice, for RX4); any other name: No. The person reports the glyph names seen and the buttons clicked, never test numbers. The agent states the plan, stops, and starts the questions only after the person's "go"; one "go" covers the run. First used in RX2 1738–1752 ([LIVE-TESTS.md](LIVE-TESTS.md)).
- *Reason:* the user's words: it is extremely difficult for people to match test numbers with the dialogs that appear (RX 1728–1737, where a Yes could not be tied to a step).

### 2026-11-20: FontLab's Python documentation may be read, never as proof

- **An agent may read FontLab's Python documentation as a source of names and descriptions (step 1 of the proving steps), never as proof** ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10). Facts recorded before this date all come from probes. *Reason:* the earlier ban was a limit of the chat-era sandbox; the site loads in the built-in browser (checked 2026-11-20) and documents `flGlyph.advanceWidth`; but its examples use container access that crashed FontLab, and its FontLab version is not stated, so FontLab stays the oracle.

### 2026-11-18: every AI app is treated equally

The docs name AI apps side by side, never one "instead of" another. Shared steps are written for "your AI app", and each app gets a section of the same rank ([README.md](../README.md)). Apps may be listed in an order, but none is presented as the default. Reason: the user's choice, after ChatGPT Desktop joined Claude Desktop as a tested client.

### 2026-11-14: editing existing glyphs

- **AI agents must be able to edit an existing glyph through Glyphbridge: move nodes, add a contour to an existing shape, redraw an outline in place; in the end, every kind of glyph manipulation.** Every edit is verified by a re-read, and the layer guard's refusal is lifted only by a tool built for that edit. *Reason:* the user's requirement; today an agent must delete a glyph and draw it again.

### 2026-11-11: research on a PC where FontLab cannot save

- **While FontLab runs in Demo mode, the agent tells the user before any live research starts whether it strictly needs a File > Save stage. When it does not, the agent says so, and that the research should then be completable on this PC. Research that needs a save waits for the user's choice** (for example, a PC with a fully functional FontLab). *Reason:* the user's rule. FontLab's Demo mode does everything except save files, and the project may later continue on a PC where FontLab is fully functional. This narrows "save tests are a preference, not a rule" (2026-11-04) on such a PC, it does not replace it.

### 2026-11-09 to 2026-11-10: tool writes, FontLab's save question and the KERNING panel (S1; listener 0.132–0.136 / server 0.51–0.57)

Condensed on 2026-11-11 from six entries and again on 2026-11-13; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). How the calls work: [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §2.
- **FontLab offers its save question for every tool change, and a tool-written kerning pair shows in the KERNING panel at once** ([PROJECT.md](PROJECT.md), goals 7 and 8). After a verified write the listener makes one FontLab notification; nothing is ever saved. *Reason:* closing lost tool work silently (S1).
- **Replies say what was done, never what FontLab shows.** *Reason:* no reading follows FontLab's icon or panel (659, 668).
- **Switches** `_MARK_CHANGED`, `_REFRESH_KERNING_PANEL`, `_ICON_MAY_LAG_KERNING` (false since server 0.57). Where the icon may lag after another kind of write, the agent tells the person once per package; the kerning check is repeated on each new FontLab version ([RUNBOOK.md](RUNBOOK.md) §13, 3g).

### 2026-11-04: save tests are a preference, not a rule

- **File > Save tests are avoided by preference, not forbidden.** One runs when it answers a question better than other means, and only after the user agrees to that test. The person saves through FontLab's GUI, to a disposable file outside the repository; no tool saves (save policy below). First case: KW 557–560, save and reopen after an API kerning write ([topics/kerning.md](topics/kerning.md) §13). *Supersedes* "File > Save tests are deferred" (2026-10-24) and that day's one-case exception (both archived). *Reason:* the user's choice, after that test showed the KERNING panel was only stale.

### 2026-11-04: the modern API first

- **Prefer FontLab's modern API. A legacy call is used only where the modern one is missing or proven worse, and the reason and test number are recorded** in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10. Legacy calls in use before this decision stay until each is reviewed; until then their record says "not yet reviewed". **Goal:** every legacy call that might safely be replaced is replaced ([PROJECT.md](PROJECT.md), goal 6). *Reason:* the user's choice, after reviewing where both APIs can do a task: the legacy view can be stale or disagree with what FontLab shows (sidebearings, `font.info`, kerning), and touching it caused F1.

### 2026-11-04: macOS compatibility

- **Glyphbridge is kept macOS-compatible, although for now it can be tested only on Windows.** Where the code depends on the operating system (file locations, shortcuts, process calls), it handles macOS with the standard library as well. Such a macOS path is stub-tested where possible and recorded in [CHANGELOG.md](CHANGELOG.md) as never run on a Mac; nothing is called working on macOS before a live run there. Earlier cases: the launcher name (server 0.35 / 0.36) and the save shortcut (server 0.40). *Reason:* the user's choice: running tests on macOS may become possible only in the future.

### 2026-11-03: names read at the moment, not fixed strings

- **Text shown to the person or the agent names things from facts read at that moment** (the client's own name, the font's name and file, the system's save shortcut), never from fixed strings. A name the sender gives is shown as given, ambiguous ones such as `local-agent-mode` included; a missing one stays missing. *Reason:* the user's rule after test 290, where the delete dialog said "Claude" whoever sent the request. Built in listener 0.114 / server 0.40.
- **PostScript names come from the font package** (design C, listener 0.118 / server 0.41): the values FontLab's Font Info shows; no name is reported as "not set", since whether FontLab derived it or a person typed it cannot be read. *Reason:* tests 291–300 found no such marker, and showed the legacy `font.info` disagreeing with Font Info (298).

### 2026-11-03: several open fonts

- **`get_kerning` with several fonts open** (listener 0.112 / server 0.37, tests 265–268): it uses the current package only when its `path` is not empty and equals the current font's path, and otherwise refuses with the reason. *Supersedes* "kerning reads need exactly one open font" (2026-11-01, archived). *Reason:* the user approved it after T5 (262–264) showed that both views follow the font window in front and that `path` tells the fonts apart.
- **Goal: every operation works with 2, 3 or more fonts open, without confusion.** Closing the other fonts is the last resort, only where it is the only way to a goal. Then the tool tells the person to close them, and why: a limitation of how FontLab is built, shown by research, which Glyphbridge cannot work around. Until research has shown that, the message says the case is not supported yet. *Reason:* the user's choice, within the design rule of honest messages ([PROJECT.md](PROJECT.md)).

### 2026-10-27: kerning (v11 session)

- **Read only the pairs a task needs, never the whole kerning table or font.** *Reason:* token cost.
- **There are no hard limits, but there is a threshold at 250 pairs.** Above it the agent must warn the person, say how many pairs and why, and ask. Only after a yes may it repeat the call with `confirmed_large_read=true`. *Reason:* the user's words: "Let there be no hard limits and let there be a threshold at 250."

### October 2026: v8 session (exact day not recorded)

- **Tests with glyphs above about 150 nodes go to the very end** (the LAST block). *Reason:* they are costly in tokens and time.

### October 2026: server v0.18 (exact day not recorded)

- **Save policy.** No Glyphbridge tool ever saves the font, and none may be built that does; saving is the person's duty. After a package of changes the agent shows **one** bold reminder in chat, through `finish_changes`: never one per step, and never as a FontLab dialog. *Reason:* the user wants full control over what is kept.

### Standing design choices (from the start; exact dates not recorded)

- **The project builds its own bridge** instead of a third-party FontLab MCP server. *Reason:* that server reported false successes. This leads to the design rule in [PROJECT.md](PROJECT.md).
- **Width and Unicode writes are not confirmation-gated; delete is** (a Yes/No dialog in FontLab), as are removing a kerning group and removing contours (2026-11-20, 2026-11-25). *Reason:* the first two are reversible.

## Talking to the person

### 2026-11-21 and 2026-11-24: speak only about real issues; the `.notdef` notice (built, listener 0.203 / server 0.83–0.84)

Merged on 2026-11-24; each entry in full: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md) ("Merged and condensed on 2026-11-24").
- **Glyphbridge raises only what stands in the way of the person's progress, at the moment it matters; chores are never pushed.** *Reason:* the user's goal of 2026-11-24: guidance only when issues show up, no chores unless needed to make progress.
- **No read tool shows a `.notdef` dialog** (`get_current_font`, `get_glyph_outline(".notdef")`, `check_notdef`). *Reason:* the user's choice (2026-11-21): the dialog blocked FontLab and the call, repeated the chat, and made agents avoid `get_current_font`.
- **What is raised depends on the font's state, not the person's skill:** a missing `.notdef` always, clearly; an empty one only in a mature font, as a likely oversight. Each reaches the person once per font, through the chat (the agent's instruction) and one line in FontLab's OUTPUT panel, the place for Glyphbridge warnings (2026-11-13). An empty `.notdef` in a font still in progress (not mature, or maturity unknown) is not raised: the automatic checks tell the agent to say nothing, nothing is noted in FontLab, and `create_font` does not mention it. **Mature:** the font has all 26 uppercase and 26 lowercase English letters (by Unicode, U+0041–005A and U+0061–007A) and at least one of them is drawn (a node or a component on its modern layer). *Reason:* the user's choices; maturity over kerning (a monospaced font may be finished without it) and a glyph count (placeholders); the drawn check stops at the first drawn letter and runs only when `.notdef` is empty.
- **`check_notdef` answers about an empty `.notdef` only when the person asked;** an agent that calls it on its own says nothing about one in a font in progress. *Reason:* a question deserves an answer; an unasked check is still a chore.
- **The agent adapts the explanation:** by default one sentence and an offer to say more; none for a person who shows font-production experience; an empty `.notdef` is never presented as an error. *Reason:* the user's choice; no skill profile is stored.
- **The one `.notdef` dialog kept: deleting it.** `delete_glyph(".notdef")` gets its own confirmation text (every font needs it as glyph 0), default No. *Reason:* the person is at a decision point in FontLab already.
- **"Already noted" is remembered per font by its package `fgId`, not its file path.** *Reason:* all unsaved fonts shared one slot, and the agent was then told a notice had been shown for a font that never had one (found 2026-11-21).
- **`GLYPHBRIDGE_NOTDEF_WARN=0` switches the automatic checks off; it is a setting for scripts and automation,** documented in [topics/server-and-endpoints.md](topics/server-and-endpoints.md) only; `check_notdef` still answers on request. *Reason:* the user's choice (a line in the root README was too insignificant); with fonts in progress left alone, designers have nothing to switch off.
- Open: whether a missing `.notdef` is a real issue depends on what FontLab's export does without one (not seen live; an export is probably blocked in Demo mode).

### 2026-11-24: both counts, through a change log

- **The change count is kept on both sides; the listener's record decides.** Supersedes nothing: it refines option (i) of 2026-11-21. *Reason:* the user's choice after the discussion of 2026-11-24. The listener knows what FontLab executed, per font and client; only the server knows which replies never came back.
- **The mechanism: a change log with an ID per write.** The server sends a unique ID with each write, and a server-run ID made once per server process. The listener logs what it executed (ID, font `fgId`, client, kind, one sequence number per listener run, a run ID). The server keeps the IDs that got no reply and a bookmark per font. *Reason:* one mechanism resolves every disagreement, saving development time (the user's aim).
- **Five general rules:**
  1. The listener decides whether a change happened; an unanswered ID is asked about.
  2. When in doubt, remind; changes are matched by ID, never added together.
  3. Unknown is said, never zero.
  4. Bookmarks, no reset.
  5. Another client's changes are named, not hidden.
- **The user's choices (2026-11-24), one question at a time:** the log keeps the last **1,000 entries** per listener run (about 1 MB, estimated, to be measured), each font's running total always kept, older entries reported as dropped; **one sequence number per listener run**, so the server keeps one bookmark; a server process without a bookmark **reminds once about earlier changes still in the log**, saying they may already be saved. *Reason:* a new session and a replaced server process look the same to the server, and staying silent would bring back TO 1582.

### 2026-11-21: dialogs and AI apps' time limits (research TO, TO2, SC, CD 1577–1598; built, listener 0.203 / server 0.83)

Merged on 2026-11-24; each entry in full: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md) ("Merged and condensed on 2026-11-24").
- **No tool call may outlast a fixed time budget below the shortest limit of any AI app: a dialog the listener shows closes by itself within that budget and counts as no answer (option C).** *Reason:* the user's choice over handing the answer to a second call (options A, B): one call, one honest outcome, and a late Yes can no longer act unseen. The limits differ by app and version (Code tab 60 s, Desktop chat about 80 s, ChatGPT Desktop documented 60 s) and are out of Glyphbridge's control, so no app-specific tests are needed.
- **Every Glyphbridge dialog (the Yes/No of `delete_glyph` and `remove_kerning_group`) closes by itself after 45 s, counted as no answer.** *Reason:* the user's choice over 40 s; with the server's margin the whole call stays under the shortest AI-app limit (60 s), and the slowest answer seen took 34 s (GT 1568).
- **The default button counts down ("No (44)"), and the text says what happens without an answer.** *Reason:* the user's choice over a fixed sentence, so a dialog never vanishes by surprise. A label changed once a second while the dialog waits was seen live (CD 1596–1598). The closing itself uses the pure Qt connection (SC 1590–1592), so it never depends on the countdown.
- **No answer in time: the reply says so and that nothing changed (`not_answered_in_time`); the agent tells the person and asks before trying again, saying they will have 45 s.** *Reason:* the user's choice over one automatic retry.
- **The server waits 55 s (was 120 s); the 45 s is set in the server and sent with each request; the dialog tools refuse a listener without self-closing dialogs.** *Reason:* the user's choice; the listener answers right after its dialog closes, so past 55 s FontLab is busy or frozen, reported as an unknown outcome while the AI app still listens.
- **The change count behind the save reminder moves from the server into the listener, per font (option i); its design follows.** *Reason:* the user's choice: an AI app can replace the server process at any time, losing the count and the reminder (TO 1582), and one server can serve two apps (TO2 1587); the reminder concerns the font, whichever app changed it. Reading FontLab's own unsaved state (option ii) stays a later refinement; its reset on save cannot be proven in Demo mode.

### 2026-11-13: notes for the person (listener 0.147 / server 0.61)

- **No GUI-repaint chores for the person.** Where FontLab's display lags behind an API write, the person gets one plain sentence (what they see, that it is only a display delay, where the real value shows), never a sequence of dialog steps to force a repaint. *Reason:* the user's UX rule; 921 and 922 found no single step.
- **The agent points the person to FontLab's OUTPUT panel once per conversation.** *Reason:* the user's choice; a person who never opens it misses its warnings.

## Fonts

### 2026-11-13: a package is told apart by its fgId (listener 0.150 / server 0.62)

- **The first glyph of a new font takes its layer name from the glyph's own package (`flGlyph.package`), with any number of fonts open, only when that package's `fgId` equals the current package's. No product code uses `flPackage.isEqual`; `create_font` compares `fgId` as well.** *Reason:* `w.package` named the glyph's own font, and `isEqual` called two different packages equal (930, 931); the user approved the design as proposed.

### 2026-11-12: the create-font tool (listener 0.146 / server 0.60)

Condensed on 2026-11-24; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md) ("Merged and condensed on 2026-11-24").
- **`create_font` works with or without other fonts open, and may make more than one font per listener run;** the once-per-run limit stays on the probe.
- **A named font also gets the legacy `font.info.familyName`, written only when the font in front reads the new font's own family; a family name is refused when its PostScript name would exceed 63 characters or it holds any of `[](){}<>/%`.**
- **What can be improved goes to [ROADMAP.md](ROADMAP.md); what cannot is told to the person, in the agent's reply and in FontLab's OUTPUT panel.**
- *Reason for all:* the user's choices and approvals (834, 835, 872, 885).

### 2026-11-11: new fonts made by an agent

Condensed on 2026-11-13; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md).
- **An agent-made font matches one made with File > New Font as closely as FontLab allows, also with other fonts open; a difference is recorded and the person is told.** Carried out by `create_font` (0.146–0.150). *Reason:* the user's requirement (goal 5, [PROJECT.md](PROJECT.md)).
- **The Font window's encoding of a GUI-made font: won't-fix for now** (agent-made fonts open with None). *Reason:* only FontLab's Qt widget can set it, fragile across versions ([topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k, E1).
- **Names: with no name given, FontLab's own (`Unnamed`, `Unnamed1`, …); a name asked for is set as Font Info would set it. Whenever font names come up, the agent offers to explain the fields of Font Info's Names page.** *Reason:* the user's requirements; that page confuses new users.

## Glyphs

### 2026-11-25 and 2026-11-26: several shapes in the three edit tools (research listener 0.213–0.214, ED8–ED10 1807–1856; built listener 0.215 / server 0.94)

- **Contours keep `get_glyph_outline`'s glyph-wide numbers; a contour drawn by a component is refused.** *Reason:* the agent edits with the numbers it reads; a component's contours are its source glyph's own (ED8 1815, 1825), so editing one would change every glyph that uses the source.
- **`add_contours` adds into the only plain shape; with two or more plain shapes it needs `shape`, the element index.** *Reason:* one numbering for the agent, and an explicit choice only where the glyph leaves one to make.
- **Two or more plain shapes are included** (after ED9 1833–1839). *Reason:* the user's choice once the probe had edited either of two plain shapes.
- **Beside the edited shape only components moved by an offset and plain shapes without a transform; anything else refuses the whole call.** *Reason:* only those were seen live; lifting the rest needs a probe run of its own.
- **`remove_contours` may empty one plain shape among several; verified only if that shape is gone after the sync and every other shape and source is unchanged.** *Reason:* the one-shape rule (choice C, 2026-11-25) applied to several shapes; an emptied shape beside others was not seen before the build.
- **A glyph of components only gets ONE new plain shape after them for `add_contours`** (research first: ED10 1849, 1850). *Reason:* the user's choice after the probe added such a shape without touching the components or their sources.
- **Every edit also checks the other shapes (kind, source, offset, contour count) and every component's source glyph; a change there makes the call unverified, nothing restored.** *Reason:* the edit tools' rule of no automatic restore (2026-11-15), extended to the shapes a call must not touch.
- *Reason for all:* the user's answers, one question at a time.
- **After MS (listener 0.216 / server 0.95): a component's contour is refused before any other check, naming the source glyph to edit instead; `add_contours` always reports in `shape` the shape that received the contours** (MS 1870, 1871). *Reason:* the stale-request advice sent the agent into a loop of reading and retrying, and the agent should never have to work out where its contours went; the user's choice A, 2026-11-26.

### 2026-11-25: `remove_contours`, the third edit tool (research listener 0.207–0.209, ED5–ED7 1694–1719; built listener 0.210 / server 0.91)

- **A call that removes every contour is allowed and leaves the glyph empty, with no shape (choice C).** *Reason:* every tool then treats the glyph as a new empty one; ED7 (1715, 1717) showed that FontLab's sync removes the shape left with no contour, so no `removeShape` call is needed.
- **Each contour to remove is named by `index`, `node_count` and its first node `start`, with `expected_contours` for the glyph; any mismatch refuses the whole call (choice B).** *Reason:* removing cannot be undone (Edit > Undo offered nothing, 1703), and a count alone does not catch a contour reordered or redrawn since the read.
- **FontLab asks Yes/No on every call, as `delete_glyph` does (choice B).** *Reason:* one general rule: a tool that destroys drawn work asks in FontLab.
- **The same cases as `add_contours` (`_EDIT_ACCEPTS`); the glyph is checked again after the Yes; contours go highest index first; verified as `add_contours` is, plus 0 shapes after the sync when all go; the removed contours are returned.** *Reason:* one reply shape for the edit tools; the person may edit the glyph while the question is open.
- *Reason for all:* the user's answers, one question at a time.

### 2026-11-24: `add_contours`, the second edit tool (research listener 0.206, ED4 1657–1664; built listener 0.207 / server 0.89)

- **A tool of its own, not a mode of `draw_path`.** *Reason:* `draw_path`'s refusal of a glyph that is not empty stays a safety net; adding is a different FontLab call (`shape.shapeData.addContour` on the existing shape) with a different check.
- **Curved and open contours were researched by probe before the build** (choice B). *Reason:* each half was proven apart, their combination was not.
- **A shape with its own transform, several shapes, a component and a Power Brush shape are refused**, as by `move_nodes` ([topics/refusals.md](topics/refusals.md)). *Reason:* only one plain shape without a transform was seen; Power Brush risks the person's work (F1). Several shapes and components: lifted by the entry of 2026-11-25 and 2026-11-26 above.
- **Verified as `move_nodes` is:** the re-read nodes; sidebearings computed from them, FontLab's lagging values shown apart; `undo_note`; marked whenever the outline changed. *Reason:* the same lag (ED2–ED4); one reply shape for both edit tools.
- **`expected_contours` is required.** *Reason:* a contour placed against a stale read lands wrongly yet reads `verified`; a count needs nothing from FontLab that lags.
- **`draw_path`'s input; new contours last, in order; 2,000 nodes counted over the whole glyph.** *Reason:* the cap protects the request time.
- *Reason for all:* the user's answers, one question at a time.

### 2026-11-20: `get_glyph_width` reads `advanceWidth`, cross-checked with the legacy width (design B; listener 0.198 / server 0.81)

- **The width is FontLab's modern `advanceWidth`; the legacy `glyph.width` is still read, and shown only when the two differ by 0.01 or more, with a note and an instruction to tell the person both and not choose one.** *Reason:* the user's choice (B over A, modern only): which value FontLab saves is open (AW 1449, [WATCH-POINTS.md](WATCH-POINTS.md)), so hiding a disagreement would break the design rule ([PROJECT.md](PROJECT.md)); the extra read is F1-safe (486–496) and AW4 (1470–1489) found both reads equal on the glyph kinds tried. The cross-check may be dropped once a save test settles the stored value, as a decision of its own.
- **When the modern side cannot be reached (no wrapper, no active modern layer, no number), the legacy width is the answer, and the reply says so.** *Reason:* goal 6 replaces a legacy call only where the modern one works; a glyph with no layer was not reached in AW4; the path ran live on `.notdef` in AW5 (1494).

### 2026-11-20: whole-unit widths in `set_glyph_width` (listener 0.197 / server 0.80)

- **A requested width is rounded to the nearest whole unit, a half rounding up (rule B), and the reply says so** (`width_rounded`). *Reason:* the user's choice (B) over refusing a fraction as `set_kerning` does: FontLab's own width field rounds a typed 437.5 to 438 (AW2 1456), while `advanceWidth = 437.5` through the API left FontLab's two views apart (AW 1449).
- **A width that moved, but not to the request, is reported as changed, counted and marked; "NOT changed" only when the width did not move.** *Reason:* the design rule ([PROJECT.md](PROJECT.md)); the reply of 1449 was false.
- **FontLab's OUTPUT line does not show the rounding; only the chat reply (`width_rounded`) does.** *Reason:* the user's choice (2026-11-20, after AW3 1462): the server rounds before the listener sees the value, and showing it there would need a server change, which was not wanted.

### 2026-11-15: `move_nodes`, the first edit tool (listener 0.153–0.154 / server 0.63–0.65)

Condensed on 2026-11-17 from three entries; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md).
- **Each move gives `from` and `to`; a `from` that differs from the node refuses the whole call.** *Reason:* a stale read becomes a refusal, not a wrong edit.
- **No automatic restore when the re-read differs;** the font is marked whenever its outline changed. *Reason:* a restore is an untested second write; the person decides.
- **One plain shape only, for now.** *Reason:* only that was probed; each shape may carry its own transform.
- **`verified` means the re-read nodes match; the sidebearings are computed from them and FontLab's advance width; FontLab's own values are shown apart, with one plain note for the person when they lag. No refresh call** (0.154 / 0.64). *Reason:* FontLab's sidebearings and ink box lag after an API node move and nothing tried refreshes them (MN 1001–1015).
- **No `display_note`; `undo_note` wherever the outline changed, told once per conversation** (server 0.65). *Reason:* `display_note` gave repaint steps, against the decision of 2026-11-13; Edit > Undo lists a tool move but left the nodes moved (1023).
- *Reason for all:* the user's answers and approvals.

### 2026-11-09 to 2026-11-18: components (P2.7; listener 0.130–0.187 / server 0.50–0.74)

Merged on 2026-11-20 from four entries: placing components (2026-11-17), a target that is not empty and `remove_component` (both 2026-11-18), components against their source (2026-11-09). Each in full, with its reasons and evidence: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md). Facts: [topics/reading.md](topics/reading.md); limits: [WHAT-WORKS.md](WHAT-WORKS.md).
- **Placing (`add_component`):** FontLab's recipe build at whole-unit offsets; one component or a `components` list; soft limit 30, with the person's approval above it; the width read before, written back and confirmed; underscore names refused in a list; the font in front is used.
- **A target with content:** the same tool, through a temporary layer (`placement`); the target needs exactly one layer, the active one, or the call is refused before any change; a failure partway restores the glyph fully. A Power Brush shape flattened in later use reopens this (F1).
- **Removing (`remove_component`):** by index, with the source and offset expected there; any mismatch refuses the whole call; the call is `layer.removeShape(component, False)`; a list runs from the highest index down, with no size limit; an auto layer that is on, or a Power Brush shape, is refused.
- **A composite read behind its source is `unverified`,** with both boxes and an instruction to tell the person; the in-step checks cover plain offsets only.
- *Reason for all:* the user's answers, one question at a time.

## Kerning

### 2026-11-20: renaming and removing kerning groups (research listener 0.199, GE0–GK 1499–1545; built listener 0.200 / server 0.82)

Condensed on 2026-11-24; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md) ("Merged and condensed on 2026-11-24").
- **Two tools, `rename_kerning_group` and `remove_kerning_group`, one group per call. A removal requires `pairs`, `"keep"` or `"delete"`, with no default, and asks Yes/No in FontLab (default No); a rename asks nothing.** *Reason:* removing differs from renaming; keep and delete change kerning a lot in opposite directions (GE 1518, 1520); a removed group cannot be brought back, a rename is undone by renaming back.
- **A new name that is also a glyph's name is allowed, with a note (`same_name_glyph`); one that is any group's or class's name is refused.** *Reason:* FontLab names classes after a member, and the kerning tools mark a class side with `@`.
- **After a change: the mark, one panel refresh (`notifyPackageContentUpdated`) and a check that FontLab caught up (`fontlab_caught_up`).** *Reason:* without the refresh FontLab's panels and the glyphs' group ids lag until a font switch (GE 1512–1516).
- *Reason for the rest:* the user's choices, one question at a time.

### 2026-11-20: class kerning in `set_kerning` and `remove_kerning` (research listener 0.193, CW 1409–1417; built listener 0.194 / server 0.78)

Condensed on 2026-11-24; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md) ("Merged and condensed on 2026-11-24").
- **The two tools are extended; no new tools. A side written `@name` is a kerning group,** confirmed by both of FontLab's sources and standing on a side that fits, else the request is refused before any write. *Reason:* a class entry is the same call with a different key (CW); `@` cannot occur in a glyph name.
- **The 250 approval counts entries; a class pair is verified by its exact entry and one sample glyph pair; a glyph side named like a group is written as the glyph, with a note; class values are whole units, as glyph values are.**
- *Reason for the rest:* the user's answers, one question at a time.

### 2026-11-19: removing kerning pairs, `remove_kerning` (research listener 0.191, KD 1380–1390, KDC 1391–1397; built listener 0.192 / server 0.76)

Condensed on 2026-11-24; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md) ("Merged and condensed on 2026-11-24").
- **A tool of its own; `set_kerning` stays unchanged.** *Reason:* removing is a different act from setting a value; a separate name keeps an agent from removing a pair by passing 0.
- **It follows `set_kerning`'s rules:** approval above 250 pairs (`confirmed_large_write`), a stop at the first removal that cannot be confirmed, and the mark and panel refresh after a change. **A pair with no entry gets a note, not an error; removing an exception over a class reports the class value that applies again** (`class_value_applies`, KDC 1395–1397).
- **Only the re-read counts, never the return value of FontLab's call.** *Reason:* defect B; the return value follows the form, not the outcome (1387, 1390).
- *Reason for the rest:* the user's answers, one question at a time.

### 2026-11-19: kerning group membership, `get_kerning_groups` (P1.6; research listener 0.188–0.189; built listener 0.190 / server 0.75)

Condensed on 2026-11-24; full text: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md) ("Merged and condensed on 2026-11-24").
- **A read tool of its own; the side comes from the modern `items()` (route C); every read is cross-checked with `getAllGroups()`, and a group whose sources disagree is reported with both versions, never settled by the tool.** *Reason:* one modern call gives name, members and side (KG 1373–1375); `get_kerning` stays as it is.
- **Every group may be listed, above 250 groups only after the person's approval; the list includes members; an unknown name is an error for that name only.**
- **Kerning groups only. Glyphbridge must eventually work with OpenType classes too, through a tool of their own** ([ROADMAP.md](ROADMAP.md) P1.7).
- *Reason for the rest:* the user's answers, one question at a time.

### 2026-11-01: kerning groups

- **AI agents must be able to see which groups have which members** ([ROADMAP.md](ROADMAP.md) P1.6; proposed first and built only after approval). *Supersedes* "group membership is deliberately not read". *Reason:* K9 and the KERNING panel method depended on membership, which only FontLab's Classes panel could show; the members of one group are a small read.

## Repository and documents

### 2026-11-26: GEMINI.md, notes for Gemini in Antigravity only

A root file beside CLAUDE.md and CODEX.md, named in AGENTS.md's startup line. *Reason:* Antigravity loads AGENTS.md and GEMINI.md by itself and ignores other names such as ANTIGRAVITY.md (its documentation; checked 2026-11-26), so the file needs no import, and one would load AGENTS.md twice; named after the model family, as Gemini CLI's own file is. Rules for every agent stay in AGENTS.md.

### 2026-11-24: refusals tracked in one register

- **Every case a tool refuses, or no tool supports yet, is listed in [topics/refusals.md](topics/refusals.md), with what would lift it. When a case becomes possible in one tool, the agent proposes lifting it in every other tool that refuses it, or says why not ([AGENTS.md](../AGENTS.md)). A shared table in the code of what each edit tool accepts, with a stub test of every tool against every case, was built with the add-contour tool (`_EDIT_ACCEPTS`, listener 0.207).** *Reason:* the user's choice; the add-contour tool is the third edit tool to refuse the same cases, and a lifted case was remembered nowhere.

### 2026-11-20: version history lives in WHAT-WORKS.md and CHANGELOG.md

- **Goals, scope, architecture and the map describe the current state; which version brought what is recorded in [WHAT-WORKS.md](WHAT-WORKS.md)'s version table and [CHANGELOG.md](CHANGELOG.md), and moves into the archive are recorded in the archive files themselves.** *Reason:* release-by-release text in PROJECT.md, ARCHITECTURE.md and MARKDOWN-MAP.md grew with every build and pushed them toward their budgets; the user approved removing it from each (2026-11-20).

### 2026-11-20: CODEX.md, notes for Codex only

A root file beside CLAUDE.md, named in AGENTS.md's startup line. *Reason:* Codex loads only one instruction file per folder (AGENTS.md here) and has no import syntax, per its documentation; named CODEX.md after the agent, not the app. Rules for every agent stay in AGENTS.md.

### 2026-11-19 and 2026-11-20: exceptions to the rule against personal data

Merged on 2026-11-24; each entry in full: [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md) ("Merged and condensed on 2026-11-24").
The rule against personal data in live files ([AGENTS.md](../AGENTS.md)) has two exceptions: **the author's name as the copyright holder in the LICENSE file** (2026-11-19), and **the repository's own GitHub address**, which contains the owner's account name, where install instructions or links need it, today the root README (2026-11-20). Nothing else personal goes there or anywhere else (no e-mail address, user name or path). *Reason:* a license needs a named copyright holder (the user's choice before adding LICENSE); a public repository cannot be installed or linked without its address.

### 2026-11-19: Glyphbridge Community Source-Available License

- **Glyphbridge uses custom source-available terms, not an OSI open-source license.** Eligible users are individuals acting on their own behalf, schools and non-profits of any size, and organizations with fewer than 10 people (owners, employees, and regular freelancers; not customers or one-time suppliers). Larger organizations other than schools and non-profits need a separate license. Eligible commercial use is free; Glyphbridge itself cannot be sold, while users may sell work made using it.
- **Free copies and modified forks may be shared under the unchanged license,** with the copyright notice retained, changes identified, and no claim that a fork is official. Modified forks may be public, but use rights remain limited to eligible users. Unmodified copies may not be re-hosted as separate downloads; direct people to the official installation page.
- **The effect of an eligible organization's later growth is intentionally unspecified.** The four URL placeholders remain for now, and the values section is non-binding. License text: [LICENSE](../LICENSE). *Reason:* the user's stated access and sharing goals.

### 2026-11-12: watch points hold the open question only

- **An entry in [WATCH-POINTS.md](WATCH-POINTS.md) holds what is open and what would settle it; the evidence lives in the topic file it links to.** *Reason:* the user's choice over a seventh raise: the file had grown by collecting the story of each run. Nothing is cut; evidence moves, word for word where the topic file lacks it.

### 2026-11-01: code comments and tool docstrings

- **MCP tool docstrings are the agents' tool descriptions, so a tidy-up leaves them as they are. `#` comments stay next to the code they protect**; only references to session and test numbers shrink to the fact. *Reason:* about 11,000 words of history sat at the top of the two scripts; that tidy-up is archived.
