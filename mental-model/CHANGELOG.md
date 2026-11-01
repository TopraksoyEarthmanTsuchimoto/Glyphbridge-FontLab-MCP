# Changelog

One entry per release of the two scripts, newest first. The listener's `VERSION` and the server's `SERVER_VERSION` are bumped together with the header line of each file.

Earlier history, in full: [archive/listener-history-to-v0.95.md](archive/listener-history-to-v0.95.md) and [archive/server-history-to-v0.31.md](archive/server-history-to-v0.31.md). What was proven live, and when, is recorded in the topic files and [CHECKLIST.md](CHECKLIST.md).

## Listener v0.96 / server v0.32 (2026-11-01)

Housekeeping. **No behaviour change**: a comparison of the parsed code with v0.95 / v0.31 shows it identical apart from the version constants.
- The version history moved out of both module docstrings and into the archive (about 11,000 words).
- The listener's route list is now complete and correct. It covers all 51 registered routes and adds the kerning routes and the `/debug/fontdir`, `/debug/trykern` and `/debug/trygroups` probes. It also fixes a `/version` example that said 0.67.
- One listener comment that pointed at the old history now points at [topics/reading.md](topics/reading.md) §6.
- The test expectations changed in version lines only (30 lines).

## Listener v0.95 / server v0.31 (2026-10-27)

`get_kerning`: no pair cap, an approval threshold at 250 pairs (`confirmed_large_read`), and `POST /kerning/pairs` for large reads. Details: [topics/kerning.md](topics/kerning.md).
