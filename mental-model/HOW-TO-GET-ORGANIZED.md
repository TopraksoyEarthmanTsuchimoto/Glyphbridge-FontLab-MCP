# How to Get Organized

## Purpose and role of this document

This document describes a repository-based workflow for preserving project knowledge across AI conversations. It is the workflow guide itself. When adopted in a project repository, keep HOW-TO-GET-ORGANIZED.md with the other project documentation in the dedicated documentation folder, such as mental-model/, and link to it from MARKDOWN-MAP.md. It is not automatically one of the startup core files below; if the team adds it to that core set, propose a word budget for it and record the approved budget in MARKDOWN-MAP.md.

## The problem and goal

**Problem:** Plain chat conversations with AI agents can quickly become too large, forcing the team to start a new conversation. A new conversation does not have the full history, so people must reconstruct the necessary context from milestone summaries that tend to grow over time.

**Idea:** Use Code mode so an AI agent can scan the project folder and read or propose updates to individual files without rewriting the entire report.

**Solution:** Make the repository, rather than any particular chat window, the durable source of truth for project knowledge.

**Goal:** The AI agent should read relevant Markdown files and propose updates to the appropriate project documents, including the Markdown files themselves. In a new conversation, the agent should read the map, follow relevant links, identify documents that may need updates, and prepare replacement files when the user approves the plan.

**Method:** Move from creating and uploading milestone summaries to a modular, well-organized repository workflow.

**Success test:** Can someone start a fresh AI conversation, point the agent to a small set of repository documents, and resume development without manually reconstructing the project's history?

**Optional discovery:** Interview the user so the workflow is less generic and better aligned with their preferences.

## Part 1 — The workflow

### Startup core files

The following eight files are candidates for the core set that an AI agent reads at the beginning of a new conversation. Extend the set when the project needs it.

1. mental-model/README.md
2. mental-model/PROJECT.md
3. mental-model/ARCHITECTURE.md
4. mental-model/CURRENT-STATUS.md
5. mental-model/DECISIONS.md
6. mental-model/MARKDOWN-MAP.md
7. mental-model/CHECKLIST.md
8. AGENTS.md

### Session-start procedure

At the start of a new conversation, the AI agent should:

1. Read the startup core files and the applicable AGENTS.md instructions.
2. Use MARKDOWN-MAP.md to find and follow links to other documents needed for the current task.
3. Check whether the information needed for the task is available and current. The agent must not assume the documents are automatically up to date. If it needs additional documents or code to verify the project's state, it should ask the user for those materials.
4. Summarize its understanding of the project, the verified current state, and the next task.
5. Identify other documents or code files that should be provided next, and list contradictions found between the documents or between the documents and any code provided.
6. Propose a plan for any document updates. The agent must not produce replacement files until the user approves the plan.

The startup response should make it easy to review the agent's understanding: project and current-state summary; next task; documents or code still needed; contradictions found; and proposed update plan, if any.

### Session-close procedure

When a conversation is getting too long or is being closed, the user may say:

> We are ending this session. Propose updates to every document that needs one, and report each file's word count against its budget.

Before proposing updates, the AI agent should:

1. Check whether the session made a new decision, reached a milestone or similar significant point, or is being closed. For these update triggers, check whether CURRENT-STATUS.md and DECISIONS.md need updates and propose them when needed.
2. Verify any proposed CURRENT-STATUS.md update against the code. Update its first line to show the verification date and commit, when applicable. If the needed code is unavailable, request it before proposing a replacement.
3. Identify other documents that need updates, including completed status items or superseded decisions that should move to the archive.
4. Report each affected file's word count against its budget. Do not produce replacement files until the user approves the plan.
5. Keep live filenames stable. If a snapshot is worth keeping, advise saving it in the archive with a descriptive suffix.

The closing response should list the proposed changes by file, note what was verified for CURRENT-STATUS.md, identify anything needed from the user, and report word counts against budgets.

Keeping project context in files also makes it possible to version-control that context.

## Part 2 — Rules

Everything in this part is binding, not optional.

### File layout and links

- The repository-root README.md is the file shown by default when someone views a repository on GitHub.
- The root README.md is for end users. Its primary purpose is to give step-by-step installation instructions for Windows, Linux, and macOS. Keep it brief and aimed at people who want to use the software, not contribute to or develop it. It is not part of the startup core set because installation and usage instructions are not expected to change frequently.
- AGENTS.md lives in the repository root. All other Markdown files live together in a dedicated folder, such as mental-model/ or another, more distinctive folder.
- mental-model/README.md introduces the project to human developers. It explains what the project is, how to use it, its goals, and where to find important information. It is for outsiders; PROJECT.md and MARKDOWN-MAP.md are for the working team.
- Use ordinary Markdown links with relative paths, not [[Wikilinks]], for compatibility.
- Keep live filenames stable so links do not break. When a snapshot is worth keeping, advise saving it in mental-model/archive/ with a descriptive suffix.

### Map, links, and archive upkeep

- MARKDOWN-MAP.md must list mental-model/archive/.
- When a Markdown file is added, moved, or archived, update MARKDOWN-MAP.md so it points to the file's current location and describes its role.
- Before completing that change, check the affected relative Markdown links and update links that would otherwise point to a moved or archived file incorrectly.
- Keep links to active information pointed at the stable live file. Use a descriptive suffix for archived snapshots so readers can tell them apart from the live document.
- Keep HOW-TO-GET-ORGANIZED.md listed in MARKDOWN-MAP.md when it is adopted into the project documentation folder.

### Rules that AGENTS.md must include

In addition to anything else it contains, AGENTS.md must specify:

1. Where to find MARKDOWN-MAP.md.
2. Core files have word budgets listed in MARKDOWN-MAP.md. When an AI agent proposes a new Markdown file, it must report the file's word count against its budget. If the file would exceed the budget, the agent proposes what to move to a linked document or archive instead.
3. Each fact lives in one file; other files link to it instead of repeating it.
4. If the AI agent cannot run a word-count tool, it must say that the word counts are approximate.

### Update triggers

When a new decision is made, when a milestone or similar significant point is reached, and when a session is being closed, the AI agent must check whether CURRENT-STATUS.md and DECISIONS.md need updates and propose them if so.

### CURRENT-STATUS.md

- CURRENT-STATUS.md contains where the project stands and what comes next. Completed items move to the archive.
- Its first line states when the status was last verified. If the project uses git, use this form: Last verified: YYYY-MM-DD against commit short-id. If it does not use git, use this form: Last verified: YYYY-MM-DD.
- The agent may propose a replacement only after checking the current status against the code. It must update the first line to reflect that verification. If the code is unavailable, it must request the code needed to verify the status before proposing a replacement.

### DECISIONS.md

- Each entry has a date, the decision, the reason, and a “superseded by” note when the decision is replaced.
- Superseded decisions move to the archive.
- Older decisions that are no longer relevant to current work move to the archive, so only relevant decisions remain in the active part and within its word budget.

### MARKDOWN-MAP.md and word budgets

When MARKDOWN-MAP.md is first created, it must contain the following starting word budgets. Measure word counts with a tool such as wc -w. Budgets may be adjusted later only with the user's approval, and the change must be recorded in DECISIONS.md. If budgets are adjusted, recalculate and display the total budget; it is a reference figure, not a hard limit.

| File | Word budget |
| --- | ---: |
| /README.md | 500 |
| mental-model/README.md | 700 |
| mental-model/PROJECT.md | 850 |
| mental-model/ARCHITECTURE.md | 1,600 |
| mental-model/CURRENT-STATUS.md | 800 |
| mental-model/DECISIONS.md | 1,200 for the active part; older entries move to the archive |
| mental-model/MARKDOWN-MAP.md | 900 |
| mental-model/CHECKLIST.md | 1,000 |
| AGENTS.md | 950 |

These listed budgets total 8,500 words, including the root README.md. The eight startup core files total 8,000 words. These totals are reference figures, not a cap; there is no total budget cap.

When any other file is added to the core set, the agent must propose a budget for it.

## Part 3 — Possible roles for other files

This part is optional. It is a generic, theoretical list of possibilities for splitting a large milestone into manageable, modular pieces, not a build plan. The rules in Part 2 apply to any of these files that are created.

- **AGENTS.md** — Explains how agents should work. It can contain commands, conventions, constraints, working agreements, testing instructions, and security considerations. It is an increasingly cross-agent convention, supported by multiple coding tools.
- **CLAUDE.md** — For concerns specific to Claude Code that exclude other AI agents such as ChatGPT, Gemini, Grok, or Cline. It can provide Claude-specific project context, background, workflow, or conventions. If a concern applies beyond Claude, use AGENTS.md. Other agents may not automatically recognize CLAUDE.md and may have their own dedicated files, such as GEMINI.md, GROK.md, or CHATGPT.md.
- **mental-model/PROJECT.md** — Goals, scope, and non-goals for the working team.
- **mental-model/ARCHITECTURE.md** — Project architecture.
- **mental-model/MARKDOWN-MAP.md** — A link tracker that can support an “Obsidian vault style” of management.
- **mental-model/CURRENT-STATUS.md and mental-model/DECISIONS.md** — Track project status and decisions, following the rules in Part 2.
- **mental-model/SKILL.md** — A playbook or training manual.
- **mental-model/LESSONS.md** — Lessons learned from experiments.
- **mental-model/EXTENDED-MEMORY.md** — Persistent information that does not fit another file's scope.
- **mental-model/GOALS.md, PLAN.md, CHECKLIST.md, DESIGN.md, COMPARISONS.md, and TESTS.md** — Organize ongoing work. These are illustrative naming conventions rather than universal standards. They help distinguish the immediate plan, design rationale, and decisions already made.
- **mental-model/STRATEGY.md** — Project strategy.
- **mental-model/RESEARCH.md** — The research question, scope, and methodology.
- **mental-model/SOURCES.md** — References and sources.
- **mental-model/FINDINGS.md** — Research findings.
- **mental-model/REPORT.md** — A place to develop conclusions.
- **mental-model/CONTRIBUTING.md** — Human contributor setup, contribution steps, and pull request expectations. Keep tool-specific agent instructions in AGENTS.md.
- **mental-model/GLOSSARY.md** — Project-specific terms, abbreviations, and domain concepts that are easy to misread across sessions.
- **mental-model/REQUIREMENTS.md** — Agreed functional and non-functional requirements, with links to their sources or acceptance criteria.
- **mental-model/ROADMAP.md** — Longer-term milestones and priorities. Keep immediate next steps in CURRENT-STATUS.md.
- **mental-model/OPERATIONS.md or RUNBOOK.md** — Deployment, maintenance, recovery, and other operational procedures.
- **mental-model/TROUBLESHOOTING.md** — Common failures, symptoms, and verified remedies.
- **mental-model/SECURITY.md** — Security policy, reporting route, and project-specific security practices, if applicable.
- **mental-model/API.md or INTERFACES.md** — Stable contracts between components or external systems when they are not clear from code and architecture.
- **mental-model/TESTING.md** — How to run checks and how test coverage is organized, when those instructions would otherwise make AGENTS.md too large.
- **mental-model/CHANGELOG.md** — User-facing release history, distinct from the active decision log.
- **mental-model/archive/README.md** — What belongs in the archive, how snapshots are named, and how active material moves there.
