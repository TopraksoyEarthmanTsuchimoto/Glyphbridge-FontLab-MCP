# Project: goals, scope, non-goals

## Purpose

Give AI agents reliable access to the font open in FontLab 8. With it they can inspect a glyph, answer spacing and kerning questions, and make basic geometry and metadata changes for the person who designs the font.

## Design rule (binding since the start)

As of October 2026 there was only one MCP project for FontLab on GitHub which at the time was observed to be far from being useful and it reported false successes. This project has been initiated to fill that void of functionality. Therefore:
- Every failure gets a specific, honest message.
- No write is reported successful unless the listener re-read the state afterwards.
- Coordinates are called `verified` only when FontLab's own numbers agree.
- **A failed read is never reported as "empty", "missing" or "none".**
- A reply that could not check something says so (`unknown`, `unreadable`, "could not check whether another glyph holds it") instead of staying silent.

## Goals, in priority order

1. **Read any glyph accurately.** This covers outlines, element transforms, layers, widths, sidebearings and Unicode, checked against FontLab's bounding box and margins. The biggest remaining gaps are components and multi-master fonts ([ROADMAP.md](ROADMAP.md), P1).
2. **Write geometry a designer needs.** Today: width, sidebearings, and closed and open straight and cubic contours into an empty glyph. Next: several shapes, editing existing outlines (P2).
3. **Read kerning cheaply.** Only the pairs the task needs, using FontLab's own effective values, class kerning included ([topics/kerning.md](topics/kerning.md)).
4. **Make new fonts usable by agents**: a create-font tool and a correct "is a font open" check (P0).
5. **Work the same with several fonts open.** The most desirable result: any operation runs without confusion when 2, 3 or more fonts are open. Where closing the other fonts is the only way to a goal, the tool says so, and that research has shown it to be a limitation of FontLab ([DECISIONS.md](DECISIONS.md), [topics/fonts-and-sync.md](topics/fonts-and-sync.md)).
6. **Replace legacy calls with modern ones.** Any legacy method that might have a chance to be safely replaced with a modern one should be replaced with a modern one. Each replacement is proven by the probe steps in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10, where the legacy calls in use are listed with their review state.

## Scope

- FontLab 8 on Windows. macOS should work in principle but is untested; the code is kept macOS-compatible ([DECISIONS.md](DECISIONS.md)). Linux would need Wine and is not supported.
- Claude Desktop and Claude Code as MCP clients. Any stdio MCP client should work.
- The current font: the one whose window is in front. With two fonts open every tool is proven to use the font in front, and every reply names its font (T5 in [LIVE-TESTS.md](LIVE-TESTS.md)); with three fonts, three read tools (`list_glyphs`, `get_glyph_width`, `get_kerning`) and every write tool but `draw_path` are proven, and two unsaved fonts with the same name are untested (goal 5).

## Non-goals and hard limits

- **No saving, exporting or generating fonts.** The human font designer saves the font, if and when they want to (save policy, [DECISIONS.md](DECISIONS.md)).
- **Prefer small piece-by-piece of reads instead of whole-table or whole-font reads** where a few items is enough to answer the bigger question. Large reads need the person's approval.
- No direct FontLab access from the MCP server, and no network exposure of the listener.
- No TypeRig or other FontLab wrapper libraries. The project uses the FontLab API only, through probes ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md)).
- No feature-based (GPOS), contextual or multi-master kerning in the current kerning tool.

## Success criteria

- A reply is either confirmed by FontLab's numbers or clearly marked as unconfirmed.
- Every write is verified by a re-read, and no work in the font is lost by a tool.
- All test harnesses pass, and each live-proven scenario is recorded in [CHECKLIST.md](CHECKLIST.md).
- Workflow success test: a fresh agent session can resume from the repository's documents alone ([HOW-TO-GET-ORGANIZED.md](HOW-TO-GET-ORGANIZED.md)).

## People and roles

- **The user** (font designer and project owner) decides, approves builds, performs FontLab GUI steps, and reports FontLab's numbers.
- **AI agents** propose, build after approval, test, and keep the documents current ([AGENTS.md](../AGENTS.md)).
