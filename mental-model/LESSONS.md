# Lessons learned

Incidents and method lessons from the chat-era sessions up to v11, plus the migration day. The rules they produced live in [AGENTS.md](../AGENTS.md) and [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md). This file keeps the *why*.

## Incidents

- **A patch script emptied a harness.** An invalid argument to `open(path, "w", ...)` raised its error *after* the file had been truncated. That emptied a harness and its expected-output file, and `run_all.py` then reported a vacuous "PASS (0 lines)".
  *Lesson:* compute the complete new content first, validate every argument, keep a backup, and check file sizes afterwards. `run_all.py` now refuses to PASS, or to `--update`, on empty, crashing or Traceback output.
- **Files changed between turns (v8 provenance incident).** The working server and one harness changed without any edit in that conversation.
  *What worked:*
  - rebuild the backup from the untouched originals (a backup made after the change is worthless)
  - read the whole diff
  - verify every helper name and listener reply key the new code relies on
  - run the harnesses, and fix test fakes instead of accepting changed expectations
  - mutation-test, then adopt it and tell the user plainly

  In the repository, `git diff` against the last commit does this job.
- **Context resets (v9, v11).** Twice a session lost its scratchpad or context.
  *What worked:* rebuild from the last test set plus the recorded added blocks, then verify line counts, case numbers and md5 before continuing. Nothing was lost. The repository now makes this unnecessary.
- **The "uniXXXX names are not mapped" mistake.** An early test concluded FontLab ignores `uniXXXX` names, but another glyph already held the codepoint. FontLab *skips* automatic codepoints that are already taken.
  *Lesson:* change one variable at a time and rule out the obvious alternative before recording a fact. Details: [topics/names-unicode.md](topics/names-unicode.md).
- **A console encoding showed a correct run as FAIL.** A non-UTF-8 Windows code page turned a printed `é` into `�`.
  *Lesson:* `run_all.py` forces UTF-8. Never `--update` over such a diff.
- **A follow-up message slipped (v11).** The deploy steps for a build were sent only after the user asked.
  *Lesson:* every build turn ends with what changed, the deploy steps and the next live checks.
- **The Add Component crash (2026-11-09).** FontLab crashed five times when a component was added to a glyph made by `create_glyph`. The first suspect, `font.update()`, looked convincing and was wrong: a run without it crashed the same way (617). The cause was the glyph having no layer, and the fix was built only after a run with a layer did not crash (619, 620).
  *Lesson:* a good suspect is still a guess. Add back one factor at a time until the result changes. Details: [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §9, [LIVE-TESTS.md](LIVE-TESTS.md).

## Method lessons

- **FontLab is the oracle; stubs are not FontLab.** Several theories that looked right in stubs were wrong live ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md), §9).
- **For a crash that might be ours, first repeat the steps with no tools and no listener.** That shows which side to look at before any theory is built (613–615).
- **Windows' Application log gives a crash's address.** The same address across runs shows it is the same fault, even when the steps look different (Event ID 1000).
- **Predict before you measure.** For curve tests, compute the exact extents independently and write them down before drawing. Agreement only means something then.
- **Predictions must include how FontLab stores numbers.** The T4 prediction for sidebearings 50 / 60 shifted the nodes by the exact −52.1548; FontLab moved them by a whole −52 (test 145c). Ask whether a target can be reached in whole units before predicting it.
- **A write can land in the element transform, not in the nodes.** In 145f the node list of `A` was unchanged while its margins had moved: `setSB` had set the Power Brush element's dx to −142. Read the element matrix before concluding anything from node lists.
- **Mutation testing finds missing tests.** A surviving mutation showed, for example, that a shipped default was tested only after the harness had already changed it.
- **A GUI that did not change does not prove a write failed.** FontLab caches editor numbers per tab ([topics/fonts-and-sync.md](topics/fonts-and-sync.md), §8f).
- **Stale tool descriptions:** after a server update Claude may show old tool texts until Claude Desktop has been fully restarted a second time.
- **Test the oracle's own method.** The KERNING panel filter was assumed to ignore group members, and conclusions about zeros rested on that for a whole session; two filters (tests 166–167) showed it does match members ([topics/kerning.md](topics/kerning.md), §8). Check what a GUI filter matches before reading anything into a missing row.
- **A name can mean a glyph or a class.** FontLab names a class after its first member, and `get` then reads that name as the class (defect B, [topics/kerning.md](topics/kerning.md) §9). Test with class names that cannot collide with glyph names, and change only the name to check.
- **An error message can document the API.** `get` refused a documented pair object, and its `TypeError` named the form it does accept (test 183); one more probe then settled it.
- **Big payloads** (for example 990-node drawings) are generated and checked by a script before sending, because `nodes_match` only compares against what was sent.

## P0.8 sessions (2026-11-01)

- **Check how the GUI recorded an entry before building on it.** Alt + Left arrow on a pair whose entry was glyph : class made a glyph : glyph entry, not the class : glyph exception the test needed. The panel showed it (plain names, no class count) and one explicit-key read confirmed it before any conclusion was drawn ([topics/kerning.md](topics/kerning.md) §9.9).
- **Rule out the age of an entry.** "The glyph : class exception wins" also fitted "the older entry wins"; removing it and making it again, newer, settled it (tests 211–213).
- **A GUI instruction must be checked for its side effects before it is given.** The Text tool was suggested for a screen check but hides the text bar; the Element tool shows it but moves the selected outline with arrow keys; Ctrl+Z was suggested as cleanup although it can undo a kerning edit. Name the tool that shows what is needed, and what not to press with it.
- **Incident: test edits through shell heredocs.** One heredoc did not parse at all; another turned an escaped `\n` in a test value into a real line break, and the harness crashed with a SyntaxError (caught by its exit code before any `--update`). Write test code with a file tool, or compute it in a script that asserts every anchor.

## Migration day (2026-11-01)

- **Copied virtual environments do not travel.** `pyvenv.cfg` points at the old machine's Python. Create a fresh venv.
- **The Store (MSIX) Claude Desktop reads its config from its own data folder, not from `%APPDATA%\Claude`.** A config written to the documented path was silently ignored. The location was found in Claude Desktop's own `main.log`. Use Settings > Developer > Edit Config ([RUNBOOK.md](RUNBOOK.md)).
- **Claude Code and the Desktop chat are configured separately.** The Code tab worked through `.mcp.json` while the chat still had no server.

## Components session (2026-11-09)

- **A GUI instruction must name something that tells the two states apart.** "Check that the panel says `mx1dieresis`" passed on the source glyph as well as on the component, so a scale meant for the component went onto the source (655). "It is already selected" had also stopped being true by the time it was acted on (631). The tab title would have told them apart.
- **A mutation that survives may have changed a comment.** One target string first occurred in a header comment, so the code was never mutated. Aim mutations at the code, and read a survivor before trusting or dismissing it.
- **After repeated wrong predictions about a cause, stop proposing causes and run a control.** Three explanations of why tool edits missed the composites failed in turn (638b, 640, 642); keeping Ü untouched as a control in 642 showed more than any of them. A later read that compares two numbers FontLab gives (650) found a way to detect the miss without explaining it.
- **Read a reply's code before saying what it lacks.** "`delete_glyph` has no warning at all" was said because `save_question_note` was missing; the reply does carry the general save instruction, and whether FontLab asks had never been tested (683). Name the exact warning that is missing, and say what was checked.
- **A save gives a clean start for one write.** The person's Ctrl+S turned FontLab's changed icon dark, so each write could be seen alone, which had been thought to need gated probes (677–681).
- **Record the mouse and the focus in icon tests.** The conditions of 668–688 came from the user's memory only, and a delete turned out to differ from the glyph writes: its click on Yes is a FontLab event.
- **Do not build a cause on one result.** The focus idea rested on 724 and was dropped at 725; the prediction that followed from it was wrong.
- **A control separates a tool's effect from FontLab's own.** A brush glyph no tool wrote to (712) showed that the fractions at load do not need a tool write.
- **`run_all.py` shows at most 60 lines of a diff.** The lines that mattered (33d, 33e, 33j) came after version lines and were cut off. Compare the whole output with the expected file before `--update`.

## KERNING panel session (2026-11-10)

- **A call that failed has not tested the idea behind it.** `notifyPackageContentUpdated` raised `SystemError` with the object id (732) and could have been written off with the others that showed no row. The docstring asked for a `uint`, and the id was a 13-digit object id. With `fgId` the same call was the one that worked (738). Compare what a call received with what its docstring asks for before recording "no effect".
