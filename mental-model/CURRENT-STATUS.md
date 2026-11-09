Last verified: 2026-11-10 against commit 20bbda1 plus uncommitted listener v0.134, server v0.55, tests and documents (tests PASS, deployed listener identical, `fontlab_status` 0.134 / 0.55; S1 657–706 and components 606–656 run live on 2026-11-09, save and reopen 707–712, kerning research 713–717 and the kerning mark 718–728 on 2026-11-10; live checks 584–603 done on 2026-11-04, not re-run)

# Current status

## Versions and identity

| Part | Version | md5 |
|---|---|---|
| listener `glyphbridge_fontlab_mcp_listener.py` | `VERSION = "0.134"` | `0912dd07fc6bca6c0fe7c01c511382ab` (484,559 bytes) |
| server `glyphbridge_mcp_server.py` | `SERVER_VERSION = "0.55"`, `MIN_LISTENER_VERSION` (0, 82) | `6537ba8b79fa3185e06a4a6fb196c7b2` (208,901 bytes) |
| tests | 4 harnesses | PASS at **2885 + 58 + 90 + 1204** lines |

Which version each feature needs: [WHAT-WORKS.md](WHAT-WORKS.md). What each release changed: [CHANGELOG.md](CHANGELOG.md).

## Environment (verified 2026-11-01)

The founding developer has moved the project to a new Windows 11 PC and to this repository on November 1st 2026. This change has set the project environment as:
- Python **3.15.2**, with `mcp` **2.2.0** in the repository `venv`.
- FontLab **8.9.5** (the earlier work was on 8.4.2).
- The MCP connection works from **Claude Code** and from the **Claude Desktop chat**.

On 2026-11-01 `--check` gave four `[OK]` lines, and the tests passed on this machine with the deployed listener copy identical; re-checked at the end of that day with listener 0.104 / server 0.33 (Arial open).

Setup steps: [RUNBOOK.md](RUNBOOK.md).

## What works (summary by area)

Proven live. The evidence and the limits of each are in [WHAT-WORKS.md](WHAT-WORKS.md), and [AGENTS.md](../AGENTS.md) says when to read it.

| Area | Proven live | Detail |
|---|---|---|
| Reading | Outlines, transforms, open contours; components partly | [reading](topics/reading.md) |
| Writing | Glyphs, Unicode, width, sidebearings, contours into an empty glyph | [geometry](topics/geometry.md), [names-unicode](topics/names-unicode.md) |
| Save question | Glyph writes, deletes and kerning writes yes | [server-and-endpoints](topics/server-and-endpoints.md) §2 |
| Kerning | Read from the current master; write glyph : glyph only | [kerning](topics/kerning.md) |
| Fonts | No font open; several fonts follow the one in front | [fonts-and-sync](topics/fonts-and-sync.md) |
| Other | `.notdef`, font names, activity log, save reminder | [WHAT-WORKS.md](WHAT-WORKS.md) |

## Not proven or not built

- Not built: multi-master fonts, several shapes per glyph, editing an existing outline, a create-font tool. Components: one or two in a glyph are read and labelled ("Resume here" below); placing them by tool and the rest are open. See [ROADMAP.md](ROADMAP.md).
- Open scenarios: [CHECKLIST.md](CHECKLIST.md).
- **F1** is fixed in 0.120 / 0.42 (V120 in [LIVE-TESTS.md](LIVE-TESTS.md)), **but still open** for paths not run live: `delete_glyph` after a read or write of a Power Brush glyph (`set_glyph_unicode` left it intact in 695, one run), several elements, and the debug probes, which still touch the legacy layer ([topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l).
- **Add Component crash on a glyph with no layer (612–619):** fixed for one master in 0.127 / 0.48 (620, one run). Not fixed for multi-master fonts or a `create_glyph` reply with `layer_note`: avoid Add Component on such a glyph in a font with unsaved work ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §9).
- **No save question (S1, 460–472):** FontLab closes a font changed only through the tools without asking about saving (it asks after a change made in its GUI), so closing loses that work silently; the chat reminder is the only warning ([topics/server-and-endpoints.md](topics/server-and-endpoints.md) §2). Since 0.132 / 0.51 glyph writes, and since 0.133 / 0.53 deletes, bring the question back, and since 0.134 / 0.54 kerning writes that changed an entry ("Resume here").

## Resume here (sessions of 2026-11-09 and 2026-11-10)

- **Components (P1.1), live 606–656:** one component, identity, offset and horizontal scale read `verified` ([topics/reading.md](topics/reading.md)); since 0.128 / 0.49 `get_glyph_outline` labels a component and names its source (624–626). The crash fix is live-checked (620–623). Two components in a glyph and one source shared by two glyphs read correctly (627–636). Since 0.130 / 0.50 an accent inside its base reads `verified` element by element (652), and a component behind its source reads `unverified` (`source_in_step`, 651, 653; plain offsets only). **A tool edit of a source reached the glyphs using it once in five; GUI edits did all four times** (638–655). No tool places a component yet.
- **S1 (657–669):** since 0.132 / 0.51 a verified, synced glyph write makes one `flItems.notifyChangesApplied` call, reported in `fontlab_changed_mark`. `create_glyph` alone turned FontLab's changed icon blue and brought the save question back, twice (668, 669); the research rounds and a control without the call are 657–667. It gives no Undo ([WATCH-POINTS.md](WATCH-POINTS.md)).
- **The goal of S1 ([PROJECT.md](PROJECT.md), goal 7): every tool change gets FontLab's save question.** Since server 0.52 `save_question_note` comes only when the mark call was not made or failed; `glyph_has_changes` is information only, since it read false while the mark worked (668; again in the setup of 688, with no note, so the fix is proven live). Proven live: `create_glyph` with its layer (668, 669); width, sidebearings, `draw_polygon`, `draw_path` and Unicode each turned a dark icon blue alone (677–681), and FontLab asked after the Unicode write (682). Before 0.133 a delete stayed dark and closing lost it silently (683). Since 0.133 / 0.53 a verified delete is marked through one surviving glyph (`via_glyph`): blue at once, and FontLab asked (688); a Power Brush survivor stayed intact (690); with two fonts open only the front one turned blue (691c). Since 0.134 / 0.54 a `set_kerning` that changed an entry is marked through a glyph of a changed pair (718–721). Not marked, with the note: a delete that leaves only `.notdef` (689), `create_glyph` with no layer, which includes the first glyphs of a new font while another font is open (691a), the legacy width route, an unconfirmed sync.
- **S1 glyph-write checks done (692–706, one master, one run each):** on a Power Brush glyph width, sidebearings and Unicode each kept the brush and its fractions and turned a dark icon blue (693–695), and the drawing tools were refused, leaving it dark (696, 697). FontLab asked on close after width, sidebearings, `draw_polygon` and `draw_path`, each alone (698–701). Five writes with two fonts open landed in the front font, which turned blue, and left the font behind dark (702–706).
- **Save and reopen (707–712, 2026-11-10):** plain tool-made glyphs came back exactly. A Power Brush glyph kept its advance, offset, Unicode, node count and brush element, but nearly all its nodes gained fractions at load, also on a glyph no tool wrote to (712): [topics/reading.md](topics/reading.md) §8p.
- **S1, marking kerning writes (713–717, 2026-11-10; one run, one master, a glyph : glyph pair, one font open):** `set_kerning` alone left the icon dark (714); one gated `notifyChangesApplied` on the pair's left glyph turned it blue at once and FontLab asked (715, 716); saved at the question and reopened, the pair was there (717). **Built in 0.134 / 0.54 and live-checked:** `set_kerning` alone turned the icon blue (after a hover) and FontLab asked (718, 719); the same value made no call and stayed dark (720); both pairs survived a reopen (721). The fallback to other glyphs is stub-tested only. **Server 0.55 (live-checked, 727, 728):** a request that changed nothing now says so (the flaw of 720), and a marked kerning write tells the person that the icon may need a hover. The icon usually did (719, 722, 723, 725, 726; 724 did not): the policy is in [DECISIONS.md](DECISIONS.md). A write is isolated without a gated probe by saving first: Ctrl+S turns the icon dark (677–681).
- **The next task (the user's choice of 2026-11-10): the KERNING panel, goal 8 in [PROJECT.md](PROJECT.md).** What was tried and what is untried: [topics/kerning.md](topics/kerning.md) §14. Each gated probe needs the user's `go=yes`.
- **FontLab:** no test font is kept; every test needs a new disposable font.
- **Next:** first the KERNING panel; then (1) rotation and the other component transforms; (2) open questions of open contours, each only with the user's OK: what FontLab does with them on export (a save test), quadratic; (3) **final polish for kerning** (the user's decision of 2026-11-04, for later): an exception over a class on a disposable copy of a real font; writes with two saved fonts open; multi-master, a design decision before any test.

## Next steps (the user's priorities of 2026-11-01 and 2026-11-09)

1. **The KERNING panel comes first** ("Resume here"). **Components are under way** (the user's choice of 2026-11-06); open contours and kerning polish wait: see "Resume here" above. Other candidates (none approved): a tool that places a component (P2.7, research first), finding why tool edits of a source miss its composites ([WATCH-POINTS.md](WATCH-POINTS.md)); `delete_glyph` after a Power Brush write; the review of legacy calls (goal 6 in [PROJECT.md](PROJECT.md); the table in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10), starting with `get_glyph_width` (legacy `glyph.width`, while the writes use `advanceWidth`) and `font.info` (it disagreed with Font Info, 298).
2. The **T-series**: T2, T3 and T4 are done. What is open in T5 is in [CHECKLIST.md](CHECKLIST.md) row 63; the candidates for several open fonts, none approved, are in [ROADMAP.md](ROADMAP.md) P0.5.
3. **S1, stage 2** (none approved): the writes still unmarked: the first glyphs of a new font while another font is open, a delete that leaves only `.notdef`, the legacy width route.
4. Candidates after that (none approved): P0.3 / P0.4, a create-font tool. Required by the user, not yet designed: P1.6, kerning group membership.

The next free test number is **729**; the numbers in use: [LIVE-TESTS.md](LIVE-TESTS.md). Large-glyph and very-large-read tests stay in the LAST block.

## Contradictions and watch points

- Between the documents and the code: none known (versions, md5 and tests checked 2026-11-10 against listener 0.134 / server 0.55; tools and the main routes checked 2026-11-06, none added since; ARCHITECTURE's "the path never leaves the listener" corrected after test 273).
- Open watch points (seen, not yet explained or settled): **24**, in [WATCH-POINTS.md](WATCH-POINTS.md).
