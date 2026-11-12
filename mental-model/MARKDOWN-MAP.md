# Markdown map

Every Markdown file in the repository, its role and, for core files, its word budget. When a file is added, moved or archived, update this map and the links that point to the file ([AGENTS.md](../AGENTS.md)).

## Startup core files (read at the start of every session)

| File | Role | Word budget |
|---|---:|---:|
| [AGENTS.md](../AGENTS.md) | rules and working agreements for every agent | 950 |
| [CLAUDE.md](../CLAUDE.md) | imports AGENTS.md, plus Claude-only notes | 200 |
| [README.md](README.md) | introduction for outside developers | 700 |
| [PROJECT.md](PROJECT.md) | goals, scope, non-goals, design rule | 850 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | processes, APIs, verification model, tools, layout | 1,600 |
| [CURRENT-STATUS.md](CURRENT-STATUS.md) | where the project stands and what comes next | 2,200 |
| [DECISIONS.md](DECISIONS.md) | active decisions with dates and reasons | 2,200 (active part) |
| [MARKDOWN-MAP.md](MARKDOWN-MAP.md) | this map | 900 |
| [CHECKLIST.md](CHECKLIST.md) | open scenarios | 1,400 |

Not core, but budgeted: the root [README.md](../README.md), the end-user install guide, has a budget of 500, and [WATCH-POINTS.md](WATCH-POINTS.md) a budget of 2,200 (2026-11-03, raised from 750 to 950 and then to 1,250 the same day, [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md); 2026-11-04, raised to 1,500, the same archive; 2026-11-09, raised to 1,800, the same archive, and then to 2,200, [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md)). [WHAT-WORKS.md](WHAT-WORKS.md) has a budget of 1,700 (2026-11-09, 1,500, [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md); 2026-11-10, raised to 1,700, the same archive).

**Reference totals:** 11,500 words including the root README, and 11,000 for the startup core files. These are reference figures, not caps. The guide's starting budgets totalled 8,500 and 8,000. On 2026-11-01, CLAUDE.md (200) was added, CHECKLIST.md was raised from 1,000 to 1,300 and CURRENT-STATUS.md from 800 to 1,250. On 2026-11-03, CURRENT-STATUS.md was raised to 1,350 and DECISIONS.md from 1,200 to 1,350, then to 1,450 and 1,700 (those entries are in [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md)). On 2026-11-04, CURRENT-STATUS.md was raised to 1,600 and then 1,800, DECISIONS.md to 1,900 and then 2,000, and CHECKLIST.md to 1,400 ([archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md)). On 2026-11-09, CURRENT-STATUS.md was raised to 2,000 and DECISIONS.md to 2,200 ([archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md)). On 2026-11-12, CURRENT-STATUS.md was raised to 2,200 ([DECISIONS.md](DECISIONS.md)).

## Linked files (read when the task needs them; no budget unless noted)

| File | Role |
|---|---|
| [WHAT-WORKS.md](WHAT-WORKS.md) | what is live-proven and which version each feature needs; read on the trigger in AGENTS.md (budget 1,700) |
| [HOW-TO-GET-ORGANIZED.md](HOW-TO-GET-ORGANIZED.md) | the workflow guide this repository follows |
| [WATCH-POINTS.md](WATCH-POINTS.md) | what was seen but is not yet explained or settled, and how an entry is settled or dropped (budget 2,200) |
| [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) | hard rules for FontLab API calls, the proven calls and the legacy calls in use, and dead ends not to retry |
| [RUNBOOK.md](RUNBOOK.md) | machine setup, restart rules, PowerShell conventions, re-verify steps, ready commands |
| [LIVE-TESTS.md](LIVE-TESTS.md) | the K-series and T-series live tests in full |
| [ROADMAP.md](ROADMAP.md) | work items P0–P5 and LAST; known limits |
| [CHANGELOG.md](CHANGELOG.md) | one entry per release of the two scripts |
| [LESSONS.md](LESSONS.md) | incidents and method lessons |
| [topics/server-and-endpoints.md](topics/server-and-endpoints.md) | every server tool and listener route, switches, save policy mechanics |
| [topics/reading.md](topics/reading.md) | how a glyph is read: kinds, transforms, layers, bridge, stale view, modern-first route, the component API by name |
| [topics/notdef.md](topics/notdef.md) | the `.notdef` check and dialog |
| [topics/names-unicode.md](topics/names-unicode.md) | glyph creation, names, Unicode |
| [topics/geometry.md](topics/geometry.md) | width, sidebearings, polygons, curves, layer guard, v8 live record |
| [topics/fonts-and-sync.md](topics/fonts-and-sync.md) | new fonts, unsynced layers, guard, auto sync, GUI refresh |
| [topics/kerning.md](topics/kerning.md) | how kerning is read and written, and its tests |
| [tests/README.md](../tests/README.md) | the test harnesses (kept in `tests/` by decision) |

## Archive

[archive/](archive/README.md) holds snapshots and retired material:
- [archive/milestone-summary-v11.md](archive/milestone-summary-v11.md): the last chat-era hand-off, personal details removed.
- [archive/scenarios-checklist-v11.md](archive/scenarios-checklist-v11.md): the full scenario matrix with its DONE rows, verbatim.
- [archive/CHECKLIST-closed-rows.md](archive/CHECKLIST-closed-rows.md): rows closed since v11, with dates and tests.
- [archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md): superseded decisions.
- [archive/WATCH-POINTS-settled.md](archive/WATCH-POINTS-settled.md): watch points settled or dropped, one line each.
- [archive/CURRENT-STATUS-resume-2026-11-10.md](archive/CURRENT-STATUS-resume-2026-11-10.md): the finished items of CURRENT-STATUS's "Resume here", as of 2026-11-10.
- [archive/listener-history-to-v0.95.md](archive/listener-history-to-v0.95.md) and [archive/server-history-to-v0.31.md](archive/server-history-to-v0.31.md): the old module docstrings with the full version history.

## Where the sections of milestone summary v11 went

Older notes refer to sections by number ("section 8p"). The linked files keep those numbers as headings.

| v11 section | Live file |
|---|---|
| header (status, what changed v8–v11) | CURRENT-STATUS, DECISIONS, WATCH-POINTS; history only in the archive |
| §0 design rule | PROJECT |
| §1 architecture | ARCHITECTURE; operational part in RUNBOOK |
| §2, §3 | topics/server-and-endpoints |
| §4, §5, §6, §8e, §8i, §8n | topics/reading |
| §7 | topics/notdef |
| §8 | topics/names-unicode |
| §8b, §8c, §8d, §8g, §8h, §8j | topics/geometry |
| §8k, §8l, §8m, §8o, §8f | topics/fonts-and-sync |
| §8p | topics/kerning |
| §9, §10 | FONTLAB-API-RULES |
| §11, §14 work items | ROADMAP |
| §12 | AGENTS (agreements), LESSONS (incidents), DECISIONS |
| §13, Appendix A | RUNBOOK |
| §14 K- and T-series | LIVE-TESTS |
| §15 hand-off | replaced by the session procedure in AGENTS; archive only |
