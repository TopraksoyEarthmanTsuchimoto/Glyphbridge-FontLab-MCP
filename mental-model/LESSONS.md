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

## Method lessons

- **FontLab is the oracle; stubs are not FontLab.** Several theories that looked right in stubs were wrong live ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md), §9).
- **Predict before you measure.** For curve tests, compute the exact extents independently and write them down before drawing. Agreement only means something then.
- **Mutation testing finds missing tests.** A surviving mutation showed, for example, that a shipped default was tested only after the harness had already changed it.
- **A GUI that did not change does not prove a write failed.** FontLab caches editor numbers per tab ([topics/fonts-and-sync.md](topics/fonts-and-sync.md), §8f).
- **Stale tool descriptions:** after a server update Claude may show old tool texts until Claude Desktop has been fully restarted a second time.
- **Test the oracle's own method.** The KERNING panel filter was assumed to ignore group members, and conclusions about zeros rested on that for a whole session; two filters (tests 166–167) showed it does match members ([topics/kerning.md](topics/kerning.md), §8). Check what a GUI filter matches before reading anything into a missing row.
- **A name can mean a glyph or a class.** FontLab names a class after its first member, and `get` then reads that name as the class (defect B, [topics/kerning.md](topics/kerning.md) §9). Test with class names that cannot collide with glyph names, and change only the name to check.
- **An error message can document the API.** `get` refused a documented pair object, and its `TypeError` named the form it does accept (test 183); one more probe then settled it.
- **Big payloads** (for example 990-node drawings) are generated and checked by a script before sending, because `nodes_match` only compares against what was sent.

## Migration day (2026-11-01)

- **Copied virtual environments do not travel.** `pyvenv.cfg` points at the old machine's Python. Create a fresh venv.
- **The Store (MSIX) Claude Desktop reads its config from its own data folder, not from `%APPDATA%\Claude`.** A config written to the documented path was silently ignored. The location was found in Claude Desktop's own `main.log`. Use Settings > Developer > Edit Config ([RUNBOOK.md](RUNBOOK.md)).
- **Claude Code and the Desktop chat are configured separately.** The Code tab worked through `.mcp.json` while the chat still had no server.
