# Glyphbridge for developers

Glyphbridge connects AI agents to **FontLab 8**, the font editor. An agent such as Claude can then inspect and change the font that is open: outlines, metrics, Unicode values and kerning. Its central promise is honesty: **a reply says only what FontLab itself confirms.** Anything that could not be checked is labelled `unverified` or `unknown`, never guessed.

## How it works, in one paragraph

FontLab's Python runs a small **listener** script inside FontLab. It answers HTTP requests on `127.0.0.1:8765` with raw FontLab facts. Separately, a normal **MCP server** process (`glyphbridge_mcp_server.py`) is started by the AI app. It turns those facts into tools, checks them, and adds instructions for the agent. The server never touches FontLab directly. Details: [ARCHITECTURE.md](ARCHITECTURE.md).

## Using it

End-user installation is in the repository's [README](../README.md). Developer setup, deployment and smoke tests are in [RUNBOOK.md](RUNBOOK.md). The tests run with the Python standard library only, because FontLab and the MCP SDK are stubbed: [tests/README.md](../tests/README.md).

## Goals

- An agent can **read any glyph accurately**: coordinates match FontLab's own numbers, or the reply says why not.
- An agent can **write the geometry a designer needs**, and every write is verified by reading it back.
- An agent can answer **spacing and kerning** questions from FontLab's own values, reading only the pairs it needs.
- The **person stays in control**: nothing is saved by a tool, destructive steps ask in FontLab, and large reads ask for approval.

Scope and non-goals: [PROJECT.md](PROJECT.md).

## Where to find things

| You want to know… | Read |
|---|---|
| where the project stands and what is next | [CURRENT-STATUS.md](CURRENT-STATUS.md) |
| what is already proven in FontLab | [WHAT-WORKS.md](WHAT-WORKS.md) |
| why something is the way it is | [DECISIONS.md](DECISIONS.md) |
| which scenarios are still unproven | [CHECKLIST.md](CHECKLIST.md) |
| what was seen but is not yet explained | [WATCH-POINTS.md](WATCH-POINTS.md) |
| the FontLab API traps that crash FontLab | [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) |
| how a subsystem works (reading, geometry, kerning, …) | `topics/`, listed in [MARKDOWN-MAP.md](MARKDOWN-MAP.md) |
| how AI agents are expected to work here | [AGENTS.md](../AGENTS.md) |
| the full history up to 2026-10-27 | [archive/](archive/README.md) |

## Status in one line

Listener 0.179 and server 0.72 are the current releases, on Windows 11 with FontLab 8.9.5 (0.179 / 0.72 add the tool `remove_component`, live-proven in RC 1257–1264b; 0.178 / 0.71 give `add_component`'s single form the width write-back the list form had, live CC 1254–1255; 0.177 / 0.70 count components by `isComponent`, live 1249–1252; 0.176 adds research stages for removing a component, run live in RM 1240–1247; 0.175 / 0.69 refuse underscore names in `add_component`'s list, live-proven in AC3 1236–1239, and report what a failed build left, stub-tested only; 0.155–0.168 add the research probe for placing components; 0.169 / 0.66 add the tool `add_component`, live-proven in AC 1079–1101; 0.170 a research switch for the save mark; server 0.67 corrects its Undo sentence; 0.171 extends the probe to several components, run live in PC2 1102–1128, 0.172 to five and 0.173 to 30, run live 1129–1177; 0.174 / 0.68 give `add_component` a `components` list, proven live in AC2 1178–1215); `move_nodes`, the first edit of an existing outline, moves nodes and curve control points `verified` live (1016–1022), though Edit > Undo does not revert it; `create_font` is live-proven (915–925), and a new font's first glyph gets its layer with other fonts open (932–936). Reading, writing basic geometry (open contours included) and reading kerning (from the current master's table, with its source) work; writing kerning between two glyphs is live-checked and shows in FontLab's KERNING panel at once; classes and other masters are not covered. Components are partly proven; multi-master fonts are open. See [CURRENT-STATUS.md](CURRENT-STATUS.md).
