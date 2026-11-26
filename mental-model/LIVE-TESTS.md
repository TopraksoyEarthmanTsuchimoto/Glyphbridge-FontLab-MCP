# Live tests (K-series, T-series)

> Moved from milestone summary v11 (§14 tests) on 2026-11-01, edited only where the chat-era workflow or a personal path no longer applies. The original section numbers are kept, so older cross-references such as "section 8p" still resolve: [MARKDOWN-MAP.md](MARKDOWN-MAP.md) lists which file holds each section. Snapshot: [archive/milestone-summary-v11.md](archive/milestone-summary-v11.md).

## 14. Live tests: what is closed, and the test numbers in use (from milestone summary v11 §14)

**Rules for live tests:** [AGENTS.md](../AGENTS.md) (Working agreements) and [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10; current priorities: [CURRENT-STATUS.md](CURRENT-STATUS.md); the LAST block: [ROADMAP.md](ROADMAP.md). The v8 principles that stood here: [archive/milestone-summary-v11.md](archive/milestone-summary-v11.md) §14.

**CLOSED (do not repeat):** v8 list (sidebearings and width on a curved glyph; O with counter vs the GUI; diagonal-node circle; S-like blob; smooth gate at 0.33 / 2.73 degrees, zero-length handle on a smooth node, c1 = c2, line-to-handle smooth node, negative x; refusals create no layer; 180- and 990-node draws; `fontlab_status` version reporting). v10: the stale legacy view (fixed at the source by `Update(flGlyph)` and by the 0.88 fallback); the guard live (139a / 139b, 142: a drawing survives a create, and a synced glyph survives a later `font.update()`); first glyph of a new font (layer `Regular` from the package master); margin comparison on a scaled and on a skewed glyph (143); `fillFgData` is useless; sidebearings and width are carried by the sync (141, 142). Evidence only from stubs: the layer guard's own refusal path (8h); the failed-sync path of 0.89.

**Test numbers in use** (moved from [CURRENT-STATUS.md](CURRENT-STATUS.md) on 2026-11-03; the next free number is kept there): 155 to 520 (K-series, P0.8 research and checks, 189–190 the v0.101 check and the activity log, 225–229 the checks of 0.105 / 0.106, 158 and 230–235 K11, 236–242 the sender tests, 243 K12(b), 244 K13, 245–246 K14, 247–252 K16, 253–255 T2, 256–258 T3, 145a–g (reserved for T4), 259 and 260 T4, 261–290 T5, 291–302 N1, 303–308 the checks of 0.114 / 0.40 / 0.41 ([CHANGELOG.md](CHANGELOG.md)), 309–316 T5 (read tools), 317–321 T5 (three fonts), 322–324 T5 (a Font Info rename), 325–331 T5 (writes with three fonts), 332–496 F1, 497–520 V120 (the checks of 0.120 / 0.42), 521–533 INK (`inkBox()` research), 534–541 V121 (the checks of 0.121 / 0.43), 542–564 KW (kerning writes, below), 565–577 SK (`set_kerning` live checks, below), 578 E1 (the Font window's encoding, [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k), 579–585 OC (open contours, [topics/reading.md](topics/reading.md) §8e), 586–594 OD (drawing open contours, [topics/geometry.md](topics/geometry.md) §8g), 595–603 OT (`draw_path` with open contours, the same section), 604–605 CP (the component API by name, [topics/reading.md](topics/reading.md)), 606–626 CP (components live, the Add Component crash and its fix, the labels, below), 627–656 CP (components, continued), 657–728 S (the changed icon, the save question, save and reopen, marking kerning writes), 729–754 KP (the KERNING panel, below), 755–764 OS (open contours through a save and reopen, below), 765–771 RT (rotated components, below), 772–778 T9 (save and reopen of a font made by `flPackage()`, below), 779–791 EX (open contours on export, below), 792–799 PB (Power Brush fractions at load, below), 800–801 the server 0.58 check (after the PB series), 802–828 PB2 (`.vfc` against `.vfj`, another brush, how the panel shows fractions, below), 829–830 the server 0.59 check (below), 831–835 NF (how new fonts are named, below), 836–840 EN (the Font window's encoding through the API, below), 841–914 NM (writing a font's names, below), 915–922 CF (`create_font` live and a display-refresh step, below), 923–925 the checks of 0.147 / 0.61 (below), 926 a design run (below), 927–936 PK (a new font's first glyph with other fonts open, P0.9, below), 937–953 DL (`delete_glyph` after a read or write of a Power Brush glyph, below), 954–963 ED (the editing API by name, [topics/geometry.md](topics/geometry.md)), 964–983 ED2 (the edit probe live, below), 984–988 B1 (refresh calls by name, below), 989–1000 B2 (a refresh call after an edit, below), 1001–1025 MN (`move_nodes` live, below), 1026–1078 PC (placing a component, below), 1079–1101 AC (`add_component` live, below), 1102–1128 PC2 (several components in one glyph, below), 1129–1177 PC3 (four to 30 components and a repeated source, below), 1178–1215 AC2 (`add_component`'s list, live, below), 1216–1235 AC2u (underscore names in a recipe, below), 1236–1239 AC3, 1240–1247 RM, 1248–1256 CC, 1257–1264c RC (`remove_component`, below), 1265–1270 NE (the recipe build on a glyph that is not empty, below), 1271–1300 TL (a temporary layer in the target glyph, below), 1301–1314 H1 (what turned a component into a plain shape, below), 1315–1327 run C (the moment of the flattening, below), 1328–1345 PB (the temporary-layer route on a Power Brush target, below), 1346–1353b NB (`add_component` on a glyph that is not empty, below), 1354–1358a NB2 (the one-layer rule, below), 1359–1363a NB3 (the list form under that rule, below), 1364–1375 KG (kerning groups, the master's group container, below), 1376–1379 KGL (`get_kerning_groups` live, below), 1380–1390 KD (removing a kerning pair, below), 1391–1397 KDC (removing an exception over a class, below), 1398–1402 RK (`remove_kerning` live, below), 1403 (checklist #20, below), 1404 (checklist #38, below), 1405–1408 (checklist #16, below), 1409–1419 CW (class entries written and removed by probe, below; 1418, 1419 not run), 1420–1432a CK (class kerning in `set_kerning` and `remove_kerning` live, below), 1433–1436a CK2 (a class pair's own rules in the instructions and the OUTPUT line, below), 1437 (`flGlyph.advanceWidth` names only, below), 1438–1449c AW (the advanceWidth round, below), 1450–1458 AW2 (fractional widths, below), 1459–1467 AW3 (whole-unit widths in `set_glyph_width` live, below), 1468–1469 the KERNING panel with a class pair and its exceptions (below), 1470–1489 AW4 (`advanceWidth` on other kinds of glyph, below), 1490–1498 AW5 (`get_glyph_width` with the legacy cross-check, live, below), 1499–1504 GE0 (editing kerning groups, the API by name, below), 1505–1522 GE (renaming and removing a kerning group by probe, below), 1523–1529 GR (a refresh call after a group rename, below), 1530–1534 GL (removing a group of two members, with the refresh, below), 1535–1545 GK (removing with kept pairs: a class : class entry and a Kerning both group, below), 1546–1576 GT (`rename_kerning_group` and `remove_kerning_group` live, below), 1577–1582 TO (the client's time limit during a FontLab dialog, below), 1583–1587 TO2 (the same from the Desktop chat, below), 1588–1593 SC (a dialog that closes itself, below), 1594–1598 CD (a countdown in the self-closing dialog, below), 1599–1617 SD (self-closing dialogs and the `.notdef` notice live, below), 1618–1634 CL (the change log live, below), 1635–1640 CB (`changes_by_font` always answers), 1641–1647 WF (two wording fixes), 1648–1649 FN (the full stop before the font note), 1650–1656 ED3 (a contour added beside a cubic outline, by probe), 1657–1664 ED4 (cubic and open contours added, by probe), 1665–1680 AD (`add_contours` live, below), 1681–1685 AD2 (`add_contours` and two shapes, below), 1686–1693 WX (server 0.90's wording fixes live, below), 1694–1703 ED5 (removing contours, by probe, below), 1704–1712 ED6 (the empty shape after the last contour, by probe, below), 1713–1719 ED7 (the sync removes the empty shape, by probe, below), 1720–1725 IL (`set_glyph_width` right after a draw, checklist #44, below), 1726–1727 SP (empty `space` in another imported font, checklist #16, below), 1728–1737 RX and 1738–1752 RX2 (`remove_contours` live, below), 1753–1772 RX3 (the checks of 0.211 / 0.92, below), 1773–1795 RX4 (`remove_contours`: curves, open contours, a component, no answer, below), 1796–1806 RX5 (the several-shapes refusal names the component, below), 1807–1832 ED8 (one shape among several, by probe, below), 1833–1839 ED9 (either of two plain shapes, by probe, below), 1840–1856 ED10 (a new plain shape beside existing shapes, by probe, below), 1857–1895 MS (several shapes in the three edit tools live, below), 1896–1906 MS2 (the two findings of MS live, below), 1907 (`flPackage` names only, below), 1908 (`flPackage` names only, continued, below), 1909–1931 AG2 (Antigravity's read-only tools, below), 1932–1934 AG3 (Antigravity's cached tool descriptions after a server update, below), 1935–1944 (the live checks of listener 0.217 / server 0.96, below), 1945–1951 FC (server 0.97's `fonts_changed` live, below), 1952 (the shape classes' transform and history names only, below), 1953–1957 XT (FontLab's own Expand Transformation and its Undo, below), 1958–1962 XT2 (`applyTransform()` by probe and Edit > Undo, below), 1963 (`flItems` names only, below), 1964–1970 XT3 (FontLab's history values by probe, below), 1971–1981 XT4 (the change mark's variants, Undo and Redo, rounding, below); a series name followed by a range always gives the whole series as listed here, and a narrower claim adds its own numbers after a semicolon, for example "(AC2 1178–1215; the list form 1180–1213)"; details in [LIVE-TESTS.md](LIVE-TESTS.md) and [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §4).

### K-series: reading kerning (decision of the user of 2026-10-27: before the T-series)

**Stage for all K tests:** FontLab started, **Arial opened from the system** (`:/Arial: Normal`, 4548 glyphs on the old PC; **4651 glyphs on the new PC with FontLab 8.9.5**, possibly a different Arial version, but K2 found the kerning unchanged: `table_size` 1370 and the same 13 values), listener **v0.95 or newer** running (the Output panel shows the version; current versions: [CURRENT-STATUS.md](CURRENT-STATUS.md)), server v0.31 or newer in Claude Desktop (fully restarted). Nothing is written by these tests (pure reads), so nothing can be damaged and nothing needs saving. One variable per test; FontLab's KERNING panel is the oracle (the user reads it and reports the numbers). Numbering continues from **155** (A4 to A7 in Appendix A use 155 to 158). Predicted values come from probes 150, 151, 154b; the stub values of the tests (for example `A:space` -113) are FAKES and must not be used as expectations.

| Id | Test | How | Expected | Status |
|---|---|---|---|---|
| **K1** | Deployment check | `Invoke-RestMethod http://127.0.0.1:8765/version` and, through Claude Desktop, `fontlab_status` (this is also T1) | listener `0.95`; `server_version` 0.31, `listener_version` 0.95, no `compatibility_note`; if `get_kerning` is missing from the tool list, fully restart Claude Desktop again (stale descriptions need a second restart, section 2) | DONE 2026-11-01 on the new PC: `/version` 0.95; `fontlab_status` through Claude Code: server 0.31, listener 0.95, no `compatibility_note`, `get_kerning` listed; through the Desktop chat the user confirmed the connection works (versions not read there) |
| **K2** | The listener route on the 13 pairs already proven by probes (GET) | A4 (155) | `errors` 0, `table_size` 1370, `units_per_em` 2048.0, `side_effect_detected` false; values A:V -152, V:A -152, T:o -227, A:B 0 / `kerned` false, Aacute:V 0, Adieresis:V 0, T:oacute 0, T:odieresis 0, A:Wgrave.c2sc -76, Aacute:Wgrave.c2sc -76, Atilde:Ydieresis.c2sc -152, A:Tbar.c2sc -80, Aacute:Tbar.c2sc -80 (floats such as `-152.0`); a text row `AVATAR` also answers (compare with K5) | DONE 2026-11-01 on the new PC (listener 0.96, FontLab 8.9.5): every predicted value exactly as expected, `count` 13, `errors` 0, `table_size` 1370, `units_per_em` 2048.0, `side_effect_detected` false. `AVATAR`: AV -152, VA -152, AT -152, TA -152, AR 0 / `kerned` false (AT, TA, AR not predicted; check against the panel in K5). Not compared with the KERNING panel |
| **K3** | The POST route gives the SAME answer as GET | A5 (156) | identical `results`; `count` equal | DONE 2026-11-01 (listener 0.96): both POST answers (13 pairs, `text` AVATAR) byte-identical to the K2 GET answers, `count` 13 and 5, `errors` 0, `table_size` 1370, `side_effect_detected` false |
| **K4** | The tool through Claude Desktop (agent level): "What is the kerning between A and V, T and o, and A and B in the open font?" | a normal request, no PowerShell | the agent calls `get_kerning` with exactly those 3 pairs (not the whole table, no `list_glyphs`), answers -152, -227 and "no kerning" for A/B, mentions font units (upm 2048), says nothing about saving (no change was made), does NOT call `finish_changes` | DONE 2026-11-01 in the Claude Desktop chat (server 0.32, listener 0.96): ONE Glyphbridge call, `get_kerning` (mode `pairs`, `count` 3: A:V, T:o, A:B), no `list_glyphs`, no `finish_changes`; answer -152, -227, "no kerning" for A/B, upm 2048 mentioned, no save remark. The agent also said the values are "the numbers FontLab's Kerning panel shows": that comes from the tool description and is unchecked on this PC until K5 |
| **K5** | `text` mode against the KERNING panel | ask the agent: "Show the kerning of every neighbouring pair in the words AVATAR, Type, Wa, Yo"; the user then reads the panel for the same pairs (filter by the left glyph) | every value equals the panel (panel integer = tool integer, `-152` = `-152.0`); a pair FontLab has no entry for is 0 / `kerned: false`; any difference is recorded WITH the pair and both numbers and the investigation is one variable at a time (do not guess) | DONE 2026-11-01 (server 0.32, listener 0.96): four `text` calls, one per word, 10 pairs, `errors` 0. Direct panel rows equal the tool: A:V, V:A, A:T, T:A -152, T:y -113, W:a -76. Y:o -188 equals the group row Y : `e` (2 members) -188; T : `e` -227 equals T:o, so the group is probably {e, o} (inferred, members not seen). A:R, y:p, p:e have no row and read 0 / `kerned` false: consistent, but the filter does not expand group members, so the zeros are conclusive only after K10 (corrected by 166–167: the filter does expand members; the zeros are conclusive for the table). The agent guessed that the AVATAR pairs were class kerning; the panel shows four direct pairs |
| **K6** | `text` mode special characters | `A V` (space: pairs `A` + `space`, `space` + `V`), `éA` (accented letter: must map to `eacute` if exactly one glyph holds U+00E9), a character the font does not have (for example a CJK character: pair `error`, others still read), and, if one can be found, a character that SEVERAL glyphs hold as primary Unicode (pair `error` listing the holders) | spaces and accents map correctly; a missing or ambiguous character gives a per-pair `error` and never a zero; the values equal the panel (`space` pairs may well be 0 or absent) | DONE 2026-11-01 (listener 0.96, server 0.32), tests 159–162, `table_size` 1370 throughout. `A V`: `A:space` -113, `space:V` 0 / `kerned` false. `éA`: `eacute:A` 0. `AV中`: `A:V` -152, `V:中` `error` ("no glyph has this codepoint as its primary Unicode"), `errors` 1. `pairs` `space:A`: -113. Panel: `A:space` and `space:A` -113, equal; no `space:V` row; no row names `eacute` (1370/0). The zeros are consistent, conclusive only after K10 (corrected by 166–167: the filter does expand members; the zeros are conclusive for the table). Not found: a character that several glyphs hold (stub-tested only). The stub's fake `A:space` -113 is also Arial's real value |
| **K7** | Error cases | A6 (157) and through the agent: a made-up glyph name (`A:Qzq`), both `pairs` and `text`, neither, an empty list, a name with a space / colon / 64 characters, `text` of one character, a control character, a POST body with an extra key | each refused with a specific message BEFORE anything is read (HTTP 400 for PowerShell); the made-up name gives ONE pair `error` while the other pairs of the same request are still read; nothing changes; no dialog in FontLab | DONE 2026-11-01 (listener 0.96, server 0.32): 14 listener requests (A6 and the 157b line: space and colon inside a name, 64 / 63 characters, U+0001, tab), each as predicted: HTTP 400 with a specific message, or HTTP 200 with one pair `error` while A:V still reads -152; the 63/64 boundary is exact; `side_effect_detected` false; no dialog. Through the Desktop chat ("A and Qzq, and A and V"): one `get_kerning` call, A:Qzq reported as unreadable (never zero), A:V -152, no other tool, alternatives offered but not read. Not triggered through the agent: both, neither, an empty list (proven live at the listener, stub-tested in the server) |
| **K8** | The 250-pair approval flow through Claude Desktop | ask the agent for ALL pairs between 18 letters (18 x 18 = 324 pairs), for example `A V T o W Y L P F r y a e c d s n m`; then answer "yes" | first the refusal ("This request would read 324 kerning pairs, more than the 250-pair threshold ..."); the agent WARNS the person, says how many pairs and why, and ASKS; only after "yes" it repeats the call with `confirmed_large_read=true`; the reply has `large_read_confirmed: true`, `count` 324. Watch that the agent does NOT set the flag by itself. Also try a request of exactly 250 pairs (no approval expected) and one of 251 (approval expected) | DONE 2026-11-01 in the Claude Desktop chat (server 0.32, listener 0.96), tests 163–165, a new chat each, `table_size` 1370 throughout. 163 (324 pairs, 18 letters): the agent counted 324, warned, named the threshold and the token cost, and asked BEFORE any `get_kerning` call; after "yes" one call, `count` 324, `errors` 0. 164 (10 × 25 = 250): one call, no question, `count` 250. 165 (250 + `z:A` = 251): asked before any call ("one over the 250-pair limit"); after "yes" `count` 251, `errors` 0. The values shared by the three reads are identical and match K2/K5. The flag after "yes" is inferred: a large read without it is refused before FontLab is asked; `large_read_confirmed` was not seen (output cut). Not triggered live: the server's own refusal, because the agent never sent a large call without approval (stub-tested only). In 163 and 164 the agent suggested missing pairs "may" sit in GPOS lookups (unproven, see K10 / K11) |
| **K9** | An EXACT-pair entry that overrides a class value (the one untested semantics) | in the KERNING panel find a pair that has BOTH its own row and a group row with a different number (for example by filtering a glyph that is in a group and looking for two rows for the same other glyph); read both with `get_kerning` | the tool equals the number the panel shows as effective for that pair (the direct pair is expected to win); record which row FontLab shows and which number the tool returns; if they differ, report it at once with the evidence and PROPOSE a fix | DONE 2026-11-01 (listener 0.97, server 0.32), tests 168–176, in a NEW disposable font because no override case was found in Arial (`Aring`, `comma`, `_3572`, `_35722` checked: Arial leaves exceptions out of the group instead). Setup: recipe below. FontLab applies the exception (-50; a gap appears) and the class value to the other member (-100). `get_kerning` read 0 and "no kerning at all" (169, 170: defect A). `/debug/trypkgkern` on the master's table: class pair only, -100 / -100 (172, 173); with the exception and the class named `kn1R`: -100 / -100 (174, 175: defect B); after renaming the class to `kn1grp`: **-50** / -100 (176). So **the exception wins** when the names are unambiguous. Legacy `font.kerning` stayed `len` 0 throughout. Details: [topics/kerning.md](topics/kerning.md) §9. Follow-ups for the fix (P0.8), tests 177–188: §9.6 |
| **K10** | Does the current master's kerning table (`flPackage.kerning`, read since listener 0.104) match what FontLab APPLIES to text? (decides whether "FontLab's own kerning" is complete) | ask the user to type, in an editor text line of FontLab with kerning on, the pairs `AV`, `ÁV` (Aacute + V), `To` and the word `Type` (y:p and p:e must show no kerning: this makes the K5 zeros conclusive) and say whether the spacing of `ÁV` is tightened like `AV`; compare with the tool (`A:V` -152, `Aacute:V` none) | if `ÁV` is tightened on screen but the tool says none, kerning exists somewhere the master's kerning table does not hold (K11): record it, tell the agent instruction to say so, propose the next step; if it is NOT tightened, the tool is complete for Arial | DONE 2026-11-02 (listener 0.104, server 0.33, FontLab 8.9.5), test 224. The tool on Arial (`table_size` 1370, master Regular): A:V -152 `glyph : glyph`, Aacute:V 0 `none`, T:o -227 `glyph : class` `e`, T:y -113 `glyph : glyph`, y:p 0 `none`, p:e 0 `none`. A text line `AV ÁV To Type` with kerning shown: To and Ty tuck under the T, y–p and p–e are plain; in a zoomed screenshot ÁV is about 28 px looser than AV, about 155 units at the measured scale. So Á is not kerned against V on screen either (`Aacute` is in the class `Aring`, `A` is not, and there is no `Aring : V` entry), and the K5 zeros y:p and p:e are confirmed in text. Measured by the agent from screenshots, not in FontLab. Not covered: other fonts, OpenType feature code (K11) |
| **K11** | Feature-based (GPOS) and contextual kerning: names-only first | A7 (158): `/debug/fontdir?stage=sub&attr=features` (type, `len`, docstring, public names of the features object; nothing is called) | learn whether a `kern` feature / class code exists in Arial's `font.features`; then DESIGN (propose first) whether a read of the feature text is wanted (large: respect the token rule, a size / head read only) | DONE 2026-11-03 for Arial (FontLab 8.9.5, listener 0.106–0.108, `/debug/fontdir` then `/debug/features`). 158: an `fgOTLayout`, `len` 29. 230: `keys`, `has_key`, `get_feature`, `get_prefix` are methods (names only). 231: 29 tags, `kern`, `mark`, `mkmk`, `cpsp` among them. 232: `kern` 52,450 characters, 1,558 lines, 1,417 with `pos`. 233: decompiled GPOS ("# Lookups: 11"), 61 classes, 211 `pos` lines start from a class. 234: `pos A V -152`; nothing pairs `@_Aring` (which holds `Aacute`) or `Aacute` with V, as K10 found. 235: 14 pairs through `get_kerning` equal the feature lines. `side_effect_detected` false throughout. Open: the 47 extra `pos` lines (1,417 / 1,370), the Features panel, other fonts, which one FontLab exports. Details: [topics/kerning.md](topics/kerning.md) §11 |
| **K12** | Other fonts: (a) a NEW unsaved font (`/debug/tryfont?stage=construct&go=yes`, once per listener run): `table_size` 0 and the sentence "this font has no kerning at all"; (b) `savedtestfont.vfc` (kerning unknown): `table_size`, any pair; (c) two fonts open (T5): which font is read (the current one) | one font per test, nothing saved | (a) `table_size` 0, every pair `value 0` / `kerned false`, `errors` 0 for existing glyphs, `.notdef` pairs fine; (b) record what is found; (c) record which font answers | DONE 2026-11-03: (a) the `table_size` 0 path proven live on 2026-11-01 (test 168: a new font with three glyphs and no kerning: `table_size` 0, both pairs 0 / `kerned` false, the sentence "no kerning at all"); (b) test 243 (listener 0.110, server 0.36, FontLab 8.9.5): `savedtestfont.vfc`, opened from a portable drive, the only open font. Master `test_font`, `master_count` 1, upm 1000, `table_size` 0. A:A, A:testglyph1, testglyph1:testglyph2, testglyph3:testglyph4 and .notdef:A all read 0 / `kerned` false / `none`, with `errors` 0 and `side_effect_detected` false. Control: A:Qzq gave the `error` "no glyph named 'Qzq'", while A:A beside it still read 0. The KERNING panel shows no rows (read by the user). Read at the listener, not through an agent. Not covered: a `.vfc` that has kerning; (c) superseded: since listener 0.104 / server 0.33 `get_kerning` refuses when not exactly one font is open (221), until T5. Defect A (GUI-made kerning missing from `font.kerning`) is fixed in 0.104 |
| **K13** | No font open | FontLab started, NO font open, listener running | HTTP 200 `{"open": false}` from the listener; the tool answers the `NO_FONT` text; no placeholder `Paper` font is read (since listener 0.105 every product route uses `CountFonts()`, P0.2) | DONE 2026-11-03: closing the only font in a running FontLab (227: `font_open: false`, reads and a create refused); test 244 (listener 0.110, server 0.36, FontLab 8.9.5), FontLab freshly started with no font open: `/font/current`, `/font/glyphs`, `/glyph/width`, `/glyph/sidebearings`, `/glyph/unicode`, `/glyph/outline` (each with `name=Paper`, the placeholder's glyph), `/kerning/pairs?pairs=A:V` and `/font/notdef` each gave HTTP 200 `{"open": false}`; `fontlab_status` `font_open: false`; `get_kerning` the no-font text; no dialog. OUTPUT: `[Glyphbridge] … reads: no font open: font info 1, glyph list 1, width 1, sidebearings 1, unicode 1, outline 1, kerning 1, .notdef check 1` (the reads sent without a client name) and `[local-agent-mode > Glyphbridge] … reads: no font open: font info 1, kerning 1`. Not covered: the write routes (T12) |
| **K14** | Real timings and FontLab's behaviour during big reads | `Measure-Command { Invoke-RestMethod ... }` as ONE validated line for 250 pairs and for 2000 pairs (POST, A5 style with a generated list); watch the FontLab window during the run | seconds per run; the server's timeout is `max(5, 5 + pairs/50)` s since server 0.33 (10 s for 250 pairs, 45 s for 2000): record whether the real time stays inside; whether FontLab freezes visibly | DONE 2026-11-03 (listener 0.110, FontLab 8.9.5, Arial the only open font, `table_size` 1370, master `Regular`). Timed with a Python script (`urllib`, `time.perf_counter`) around one POST each, instead of `Measure-Command`: the listener's time plus the local HTTP round trip, without the MCP server and the agent. **245**, 250 pairs (`A T V W Y L P F K R` × `a`–`y`): 0.079 s and 0.069 s, `count` 250, `errors` 0, 35 kerned, `side_effect_detected` false; the two replies byte-identical, and identical to an unplanned first run (0.065 s) sent before the prediction was written, because a font was open unnoticed. **246**, 2,000 pairs (`A`–`Z a`–`n` × `A`–`Z a`–`x`, body 24,011 bytes, reply 152,975 bytes): **0.084 s** against the 45 s limit, `count` 2000, `errors` 0, 50 kerned, A:V -152 as in K2, `side_effect_detected` false. The prediction (about linear, 0.3–1 s) was **wrong**: eight times the pairs took about the same time, so the cost is mostly per request (cause not investigated). The user watched FontLab during 246: it stayed responsive, nothing unusual. The timeout formula is left as it is (generous, costs nothing). Not covered: other fonts and machines, the time through the server and the agent |
| **K15** | Transport limits | LAST BLOCK: a POST body near 1,000,000 bytes (about 30,000 pairs) and one above it | at or below the limit the answer is complete; above it the body is cut and the answer is HTTP 400 "request body was not valid JSON" (stub-known only) | DROPPED 2026-11-03 by the user's decision ([archive/DECISIONS-ARCHIVE.md](archive/DECISIONS-ARCHIVE.md)): not run; the limit stays stub-tested only |
| **K16** | Encoding end to end | `text` with `+`, `&`, `%`, a space and a non-ASCII letter through GET with `[uri]::EscapeDataString` and through POST, and through the agent | the same characters arrive (UTF-8, a `+` unescaped in a GET address becomes a space: expected); the pairs list in the reply shows the real characters | DONE 2026-11-03 (listener 0.110, server 0.36, Arial, `table_size` 1370), text `A V+é&%`. **247**, the reference by glyph names (A:space, space:V, V:plus, plus:eacute, eacute:ampersand, ampersand:percent): `errors` 0, A:space -113 `glyph : glyph`, the other five 0 / `none`. **248**, GET with `[uri]::EscapeDataString` (`A%20V%2B%C3%A9%26%25`): equal to 247, `chars` showing the real characters. **249**, the same with a raw `+`: it arrived as a space (V:space, space:eacute; the other four pairs as 247), as expected. **250**, POST from Windows PowerShell 5.1 with `-ContentType 'application/json'`: HTTP 400 "request body was not valid JSON" (the body was not sent as UTF-8; predicted as possible). **250b**, the same with `; charset=utf-8`: equal to 247. **251**, `get_kerning` through Claude Code: equal to 247. **252**, a new Claude Desktop chat ("What is the kerning of every neighbouring pair in the text `A V+é&%`?"): the 6 pairs with their characters, values and sources as 247, no guessing; it noted that A and V are not neighbours because of the space and offered `AV` without reading it. Its tool calls were not seen; its words suggest `fontlab_status` before `get_kerning` (one call was predicted). All values but one are 0, so the check rests on the glyph names each character mapped to |

**Remaining K tests:** none. All are DONE (2026-11-03) except K15, which was dropped.

**P0.8 probe tests (not K tests):** 177–188 in the K9 font ([topics/kerning.md](topics/kerning.md) §9.6); 191 on Arial, the 13 K2 pairs through `/debug/trypkgkern`: both tables agree, DONE 2026-11-01 (§9.7); 192–197 in a new font (recipe below), step (c): the glyph : class exception wins over the class pair, defect B occurs on the left side too, and the exact glyph pair misses a glyph : class exception, DONE 2026-11-01 (§9.8); 198–218 in the same font with listener 0.103 (`/debug/trykerngroups`, class-name keys, the precedence of glyph : class over class : glyph in both creation orders, a "Kerning both" class, an added member), DONE 2026-11-01 (§9.9); 219–223 the live checks of the fix (listener 0.104 / server 0.33): L1 the test font, L5 a removed class member, L6 two fonts refused, L2 Arial's 13 pairs, L4 the Desktop agent; L3 (a fresh GUI-kerned font) is covered by L1, DONE 2026-11-01 (§10). P0.8 is done.

**Rebuild recipe for the step (c) font** (nothing is saved; repeat after any FontLab restart, with a NEW prefix each round, e.g. `kc2`):
1. Close every other font with the **X at the top left** of its font window (the File menu has no Close; the X at the top right closes something else). File > New Font.
2. Through the tools: `create_glyph` `kc1A`, `kc1B`, `kc1C`, `kc1D`; `draw_polygon` each with `[[50,0],[450,0],[450,700],[50,700]]`; `set_glyph_width` 500 each; `finish_changes` once.
3. Font window: select `kc1A`, Ctrl+click `kc1B`; Classes panel **+** > **Kerning Left** (FontLab names it `kc1A`); double-click the name and rename it `kc1lft`. The same for `kc1C` and `kc1D` with **Kerning Right** (named `kc1C`), renamed `kc1rgt`.
4. Glyph window with the text `/kc1A/kc1C`, Kerning tool, click the right glyph, **Left arrow** once: a class pair at -1; set it to -100 in the KERNING panel. Then **Ctrl + Left arrow** once: the exception `kc1A : kc1rgt` (nested, red) at -101; set it to -50.
5. Screen check with the text `/kc1A/kc1C/kc1A/kc1D/kc1B/kc1C`: the text bar shows with the **Element tool (V)**, not with the Text tool. With the Element tool, arrow keys and drags move the selected outline; touch neither. Do not press Ctrl+Z during the stage: it may undo a kerning edit. Alt + Left arrow keeps the left side as the current entry has it: on a pair whose entry is glyph : class it makes a glyph : glyph entry, so a class : glyph exception is made from a pair whose entry is the class pair (here kc1B–kc1C). The panel's **-** button (bottom left) removes the selected row. Double-clicking a value can reduce the text line to that one pair. The Classes panel's **+** also offers **Kerning both**; a class's members can be edited in its text line (`kc1E kc1F`, Enter).
6. Stage B: rename `kc1lft` to `kc1A` (the only change). The glyph's floating panel shows the old class name until a switch to the font window tab and back.

**Rebuild recipe for the K9 test font** (nothing is saved; repeat after any FontLab restart, with a NEW glyph prefix each round):
1. Close other fonts without saving; File > New Font (one font open).
2. Through the tools: `create_glyph` `kn1L`, `kn1R`, `kn1S`; `draw_polygon` each with `[[50,0],[450,0],[450,700],[50,700]]`; `set_glyph_width` 500 each.
3. Font window: select `kn1R` and `kn1S` (Ctrl+click). Classes panel: **+** > **Kerning Right**: FontLab names the class after the first member (`kn1R`). To avoid defect B, rename it (double-click the name) to `kn1grp`.
4. Glyph window, text `/kn1L/kn1R`, Kerning tool (AV), click the right glyph, **Left arrow** once: a class pair (bold, "(2)") at -1. Double-click the value in the KERNING panel, type -100.
5. Same pair, **Alt + Left arrow** once: an exception (red, nested, plain names) at -101. Double-click its value, type -50. (FontLab help: Alt = right side a glyph, Ctrl = left side a glyph, Ctrl+Alt = glyph : glyph.)
6. Read with `/debug/trypkgkern?a=kn1L&b=kn1R&go=yes` (and `b=kn1S`). Expected: -50 and -100 with the class named `kn1grp`. Tests of defect B need the class named `kn1R` (rename it back); `&mode=flags&flags=FF` then gives -50 for `kn1R` and `None` for `kn1S`.

### KW series: writing kerning (research, 2026-11-04, listener 0.122 / 0.123; results in [topics/kerning.md](topics/kerning.md) §13)

**Stage recipe** (nothing is saved; repeat after any FontLab restart with a NEW prefix, e.g. `ks2`): one new font (File > New Font, no other font open); through the tools `create_glyph` `ks1L`, `ks1R`; `draw_polygon` each with `[[0,0],[500,0],[500,500],[0,500]]`; `set_glyph_width` 500 each. Check `get_kerning` `ks1L:ks1R` 0 `none`, `table_size` 0. Screen checks: double-click a glyph in the grid, text `/ks1L/ks1R` in the glyph window's text field; the KERNING panel open on the right.

| Test | What | Result |
|---|---|---|
| 542, 543 | names only: `fgKerning` and `flPackage` docstrings | `set(pair, double)`, documented as returning an int; `kerningContainer()` |
| 544 | `/debug/trysetkern?a=ks1L&b=ks1R&value=-100&form=tuple&go=yes` | written: `None` → -100.0, `len` 0 → 1; `set` returned `None` |
| 545–547 | KERNING panel: as is, after a glyph window opened, after reopening the panel | no row |
| 546 | text line `/ks1L/ks1R` | about 100 units of overlap: applied |
| 548 | names only: `kern` in the `fontlab` and `fontgate` modules | none in `fontlab`; six in `fontgate` |
| 549, 550 | `/ks1R/ks1L` edge to edge; Kerning tool, Alt + Left arrow | GUI pair -1; the panel lists only that pair |
| 551 | `get_kerning` on both pairs | -100 and -1, `table_size` 2 |
| 552 | names only: `Update`, `flObject`, `flPackage` change members | `Update([fgGlyph\|fgFont\|flObject])` |
| 553–556 | `/debug/trykernrefresh` `container`, `update`, `changed`, `update` | no error, no panel row; `changed()` sets the container's `isChanged`, `Update` clears it |
| 557 | `get_kerning`, unsaved | -100 and +20, `table_size` 2 |
| 558 | File > Save As a new `.vfc` outside the repository | table and panel unchanged |
| 559 | close with the font window's X | no save question |
| 560 | File > Open Fonts… of that file | the panel lists both pairs, footer 2; `get_kerning` the same |
| 561 | S1 on the 560 file: (a) close with X, reopen; (b) `/debug/trysetkern?a=ks1L&b=ks1L&value=-50&form=tuple&go=yes`; (c) `get_kerning`; (d) close with X | (a) no question; the changed icon in the font's tab not blue; FontLab selects `.notdef` on opening; (b) `None` → -50.0, `len` 2 → 3; (c) -100, +20, -50, `table_size` 3; icon not blue, panel two rows; (d) **no save question** |
| 562 | reopen, `get_kerning` | -100, +20, `ks1L:ks1L` 0 `none`, `table_size` 2: the pair was lost |
| 563 | Undo on the reopened 560 file: (a) Edit menu; (b) `/debug/trysetkern?a=ks1L&b=ks1L&value=-50&form=tuple&go=yes`; (c) `get_kerning`; (d) Edit menu | (a) Undo and Redo greyed out; (b) `None` → -50.0, `len` 2 → 3; (c) -100, +20, -50, `table_size` 3; (d) **Undo still greyed out**, icon not blue, panel two rows; "Paste" had become an active "Paste Artwork", probably from a screenshot on the clipboard (inferred); cleanup close: no question |
| 564 | the `flags` form on the reopened 560 file: (a) reopen; (b) `/debug/trysetkern?a=ks1L&b=ks1L&value=-50&form=flags&go=yes`; (c) `get_kerning`; (d) screen | (a) icon not blue; (b) no error, `None` → -50.0, `len` 2 → 3, returned `None`; (c) -100, +20, -50, `table_size` 3; (d) icon not blue, panel two rows; cleanup close: no question |

**Open in the KW series:** pairs with classes; other masters; removing a pair.

### SK series: `set_kerning` live checks (2026-11-04, listener 0.124 / server 0.44; results in [topics/kerning.md](topics/kerning.md) §14)

On the saved KW file at the 560 stage (`ks1L:ks1R` -100, `ks1R:ks1L` +20), one font open unless stated.

| Test | What | Result |
|---|---|---|
| 565 | `set_kerning [["ks1L", "ks1L", -50]]` | set, 0 `none` → -50 `glyph : glyph`, `table_size` 2 → 3; OUTPUT `kerning ks1L:ks1L: 0 -> -50 (verified)`; icon not blue, panel two rows |
| 566 | `ks1L:ks1R` -80, then -100 | both set, `table_size` 3; after -80 the panel row still read -100 |
| 567 | `ks1L:ks1L` -12.5 | not set: the entry reads -13.0; change counted |
| 568 | `ks1L:ks1L` 12.5 | not set: 13.0 |
| 569 | `ks1L:ks1L` 12.4 | not set: 12.0 (whole units, nearest, halves away from zero) |
| 570 | `ks1L:ksZZ` -10 | refused: no glyph `ksZZ`; nothing changed |
| 571 | `ks1L:ks1R` -1001 | refused: larger than upm 1000; nothing changed |
| 572 | File > New Font in front (2 fonts); `.notdef:.notdef` -10; `get_kerning` | both refused (no file path); after closing it, `.notdef:.notdef` in the KW file `none`; the panel then listed three rows, 12 included |
| 573 | `ks1R:ks1R` -30; (b) the font tab and the editor tab; (c) File > New Font, then the KW font's tab | set, `table_size` 3 → 4; (b) panel three rows; (c) **four rows**, `-30` included; cleanup close: no question |
| 574 | `ks1L:ks1R` -80; the panel row; File > New Font, then the KW font's tab | set; the row read -100, then **-80** after the switch |
| 575 | server 0.45: `set_kerning [["ks1L", "ks1L", 12.4]]` | refused before sending ("whole font units"); `ks1L:ks1L` still 12 |
| 576 | server 0.45: `ks1L:ks1R` -100 | set, -80 → -100; the reply carries `matched_by` "only font" and the new panel wording |
| 577 | KW file reopened at the 560 stage; `set_kerning` `ks1R:ks1R` -30; File > Save As `kw-save-577.vfc` (outside the repository); close; reopen | set (`table_size` 2 → 3); saved (OUTPUT line); reopened: panel 3 rows with -30; `get_kerning` -30 `glyph : glyph`, `table_size` 3; no save question at any point |

### CP series: components (2026-11-09, FontLab 8.9.5, listener 0.126 / server 0.47; results in [topics/reading.md](topics/reading.md); the crash in [FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §9)

Disposable, unsaved, one-master fonts, each lost afterwards. Two fonts: `cp1base` (a tool-drawn rectangle from (100, 50) to (400, 250), width 600) with `cp1comp` and `cp2comp` (empty, made by `create_glyph`); then a GUI-only font with `cp3base`, `cp3one` to `cp3four` and the tool-made `cp3five`. Components were added with Glyph > Add Component, X and Y 0. Rotation, slant, mirroring, vertical scale, several components in one glyph and other masters were not tested.

| # | Test | Predicted | Result |
|---|---|---|---|
| 606 | `/debug/currentshapes`, `cp1comp`, no offset | 1 shape, `is_component` true, identity; contours 1 (guess); layer nodes 4 or 0 | as predicted; layer nodes **4**; `is_composite` true; `shape_type` `ShapeContours`, the same as a plain shape |
| 607 | `get_glyph_outline cp1comp` | LSB 100, RSB −400, width 0, the 4 nodes; not `verified`; component count 1; a note that components are not included | numbers and nodes right; **`verified`, no component count, no note**: three predictions wrong, and the reply does not say the glyph is a component |
| 608 | Transform panel X 50, Y 30, Apply | LSB 150, RSB −450, ink x 150–450, y 80–280, `dx` 50, `dy` 30, `verified` (guess) | as predicted; FontLab showed Δ=(50,30); nodes at the moved position with `raw_x` / `raw_y`; `cp1base` unchanged |
| 609 | `/debug/walk` to `shapes[0].shapeData` of `cp1comp`: `componentGlyph`, `componentLayer`, `isComponent`, `isComposite`, `referenceCount` | `cp1base`; `Regular` or empty; true, true; 2 (guess) | `cp1base`, `Regular`, true, true; `referenceCount` **1** |
| 610 | control: the same read on `cp1base` | empty, empty, false, false; `referenceCount` 1 (guess) | empty, empty, false, false; `referenceCount` **2** |
| 611 | Transform panel X 0, Y 0, width 200%, Apply | left edge 150 or 300 | FontLab: LSB 100, RSB −700, Δ=(−100, 30); the tool agreed: `m11` 2, `m22` 1, `dx` −100, `dy` 30, ink x 100–700, y 80–280, `verified`, `componentGlyph` still `cp1base`. Both predictions of the panel's origin wrong |
| 612 | `create_glyph cp2comp` after `cp1comp` held a component, then Add Component `cp1base` on it | no crash | **FontLab crashed** a few seconds after OK. It offered a backup; the same steps on the recovered font crashed again (whether the listener was running then is not known). Both: Windows `c0000005`, `FontLab 8.exe`, offset `0xf5361d`. Font lost |
| 613 | fresh FontLab, listener confirmed unreachable; GUI only: `cp3base`, then components in `cp3one` and `cp3two` | weak lean to a crash | no crash; the Elements badge went 2, then 3 |
| 614 | as 613; `cp3one`'s component set to X 70, Y 30, 200%; a new GUI glyph `cp3three` gets a component | none | no crash; badge 4 |
| 615 | as 614, listener running, only `fontlab_status` sent; a new GUI glyph `cp3four` gets a component | no crash, badge 5 | as predicted |
| 616 | as 615; `create_glyph cp3five`, then Add Component `cp3base` on it | crash if `font.update()` is the cause | **crashed**: the same `c0000005` at `0xf5361d`. Font lost |
| 617 | new font: GUI-made `cp4base`, `cp4one` with a component; listener on; gated `/debug/trycreate how=plain name=cp4plain` (`font.createGlyph` and the glyph list, no `font.update()`); Add Component `cp4base` on it (how it was opened was not noted) | no crash (`font.update()` the suspect) | **crashed**, same address: `font.update()` is not needed. Prediction wrong. Font lost |
| 618 | new font, same setup with `cp5`; gated `/debug/tryrefresh stage=create how=Update_flGlyph name=cp5sync` (`font.createGlyph`, then one `fontlab.Update(<modern glyph>)`); opened from the grid; Layers & Masters panel empty for it; Add Component `cp5base` | slight lean to a crash, once the empty panel was seen | **crashed**, same address: this sync does not prevent it. Font lost |
| 619 | new font, same setup with `cp6`; `create_glyph cp6wide`, then `set_glyph_width cp6wide 500` (reply `layer_created: "Regular"`, width 500, synced); the panel listed `Regular`; Add Component `cp6base` | no crash if the missing layer is the cause; badge 3, LSB 123, RSB 150, width 500 | **no crash**; as predicted |
| 620 | listener 0.127 / server 0.48; new font, GUI-made `cp7base`, `cp7one` with a component; real `create_glyph cp7tool` (reply `layer_created: "Regular"`, `layer_name_source: "other glyphs"`, synced; the panel listed `Regular`; no width write); Add Component `cp7base` | no crash; badge 3, LSB 122, RSB −361, width 0 | **no crash**; as predicted |
| 621 | same font; `create_glyph cp7draw`, then `draw_polygon` from (100, 50) to (400, 250) into its empty layer | `verified`, no second `layer_created` | as predicted; synced |
| 622 | `set_glyph_width cp7draw 640` on the existing layer, then `get_glyph_outline` | 0 → 640, outline unchanged | as predicted; `verified`, LSB 100, RSB 240, ink x 100–400, y 50–250 |
| 623 | `check_notdef` after those creates | `empty`, one dialog | as predicted: `empty`, `dialog_shown` true; the `.notdef` still holds 0 layers |
| 624 | listener 0.128 / server 0.49; new font, GUI-made `cp8base`, `cp8one` with a component, no transform; `get_glyph_outline cp8one` | `is_component` true, `component_glyph` the source, one note, `verified` | as predicted: `cp8base`, layer `Regular`; ink x 128–318, y 171–363, LSB 128, RSB 182, width 500 |
| 625 | `get_glyph_outline cp8base` (plain) | `is_component` false, no component note | as predicted; the same geometry |
| 626 | `cp8one`'s component set to X 50, Y 30 in the small element panel; `get_glyph_outline` | LSB 178, RSB 132, ink x 178–368, y 201–393, the labels kept, `offset (50, 30)` | as predicted; FontLab showed 178 / 132 / 500 and Δ=(50,30); `verified` |

Reading: Add Component crashes on a glyph with no layer once the font already has a component; a glyph made by `font.createGlyph` has no layer. One run with a layer (619), in which the width call also set the width and synced. Not explained: `cp1comp`, also layerless and made before any component existed in its font, took a component without a crash (one run). Whether `delete_glyph` or `set_glyph_unicode` matter is not tested; 617 showed that `font.update()` is not needed. Listener 0.127 creates the layer in `create_glyph`: 620, with no width write, took a component without a crash (one run, one master). Not run live: multi-master, and `layer_note`.

**The small element panel** (bottom of the Glyph window; seen on `cp1comp` and `cp3one`): X and Y set the component's absolute offset, and width % its scale, keeping the offset: X 0, then 40, on `cp1comp` read LSB 200, then 240, and `dx` 0, then 40; on `cp3one` X 70, Y 30, width 200% gave LSB 376, RSB −280 as predicted. The rectangle moves while typing; LSB, RSB and Δ change on Enter or when the field loses focus. One attempt to set X, Y and width together on `cp1comp` changed nothing and left the source glyph in front; the single-field edits did not ([WATCH-POINTS.md](WATCH-POINTS.md)).

### MX series: Ö and Ü from shared components (2026-11-09, FontLab 8.9.5, listener 0.128 / server 0.49; results in [topics/reading.md](topics/reading.md))

One disposable, unsaved, one-master font holding only `.notdef` at the start; prefix `mx1`. Tool-drawn `mx1O` (width 700), `mx1U` (640) and `mx1dieresis` (two circles, 400); `mx1Odieresis` and `mx1Udieresis` empty at first. The person added the components with Glyph > Add Component and set X in the small element panel. Numbers are LSB / RSB / width. A "read" is `get_glyph_outline` or `get_glyph_sidebearings`.

| # | Test | Predicted | Result |
|---|---|---|---|
| 627 | `create_glyph`, `draw_path`, `set_glyph_width` for the three sources; read | `mx1O` ink x 50–650, y 0–700, 50 / 50 / 700; `mx1U` 60–580, 0–700, 60 / 60 / 640; `mx1dieresis` 70–330, 780–880, 70 / 70 / 400; all `verified` | as predicted |
| 628 | `create_glyph` for the two accented glyphs, Unicode 214 and 220, widths 700 and 640 | a layer on each | `layer_created: "Regular"`, as predicted |
| 629 | Add Component `mx1O` on `mx1Odieresis` | no crash, 50 / 50 / 700, labelled | as predicted on screen and in the read, `verified`; Elements badge on `mx1O` 2 |
| 630 | Add Component `mx1dieresis` on it | no crash, 2 components, ink y 0–880, dots at drawn place | as predicted, `verified`, 48 nodes; the read lists `mx1O` first, the Elements panel has `mx1dieresis` on top |
| 631 | by accident, X 150 on `mx1O` (set back to 0 afterwards) | `dx` 150, ink x 70–800, 70 / −100 / 700 | as predicted, `verified`, `dx` 0 on the other component; the panel still showed 50 / 50 |
| 632 | font tab, then back | panel 70 / −100 / 700 | as predicted; Elements panel Δ=(150,0) |
| 633 | X 150 on `mx1dieresis` | dots x 220–320, 380–480; 50 / 50 / 700 | numbers as predicted, Δ=(150,0) on screen; status **`unverified`**, not predicted: the box fits with and without the transform |
| 634 | Add Component `mx1U` on `mx1Udieresis` | `verified`, 60 / 60 / 640 | as predicted; read only, no screenshot |
| 635 | Add Component `mx1dieresis` on it | 2 components, dots at drawn place, `verified`, badge 3 if it counts uses | as predicted on screen and in the read; badges `mx1dieresis` 3, `mx1U` 2 |
| 636 | X 120 on `mx1dieresis` in `mx1Udieresis`; both glyphs read | dots x 190–290, 350–450; 60 / 60 / 640; `unverified`; Ö still 150 | as predicted; Δ=(120,0) on screen |
| 637 | names only, `/debug/classdir` on `flShape` | n/a | lists `inkBox([QTransform])` and `boundingBox` (QRectF); neither called |
| 638 | `set_glyph_sidebearings mx1dieresis` 270, −130 | source 270 / −130 / 400; Ö 50 / 20 / 700; Ü 60 / −10 / 640; `verified` | as predicted in the read. The source got an element offset `dx` 200, its nodes unmoved. Font tab: old numbers and thumbnails; back on the glyph tab: 60 / −10 / 640, right dot past the stem |
| 638b | restore: 70, 70 | source 70 / 70 / 400, `dx` 0; Ö 50 / 50, Ü 60 / 60 | source as predicted. **Ö stayed 50 / 20, Ü 60 / −10**, `verified`; prediction wrong. Unchanged after a re-read, a tab switch, closing and reopening the Ü tab (screen and read agree), and opening the source (screen 70 / 70 / 400) |
| 639 | GUI: Element tool, click a dot, X 10 in the small panel of `mx1dieresis` | 80 / 60 / 400; Ö 50 / 50; Ü 60 / 60 | as predicted (margins read, dot positions not); Δ=(10,0) |
| 640 | `set_glyph_sidebearings mx1dieresis` 260, −120 | Ö 50 / 30; Ü 60 / 0, if a non-zero offset reaches them | **Ö 50 / 50, Ü 60 / 60, unchanged**; source 260 / −120, drawn at once, Δ=(190,0); the bottom boxes stale at 80 / 60 and X 10. Theory dropped |
| 641 | names only: `flGlyph`, `flShape`, `flShapeData`, module `fontlab` | n/a | `bindDependencies()` on the three, `isUnbindedDependecies()` on `flGlyph`, `isUnbindedDependencies` on `flShape`; none called |
| 642 | gated `/debug/tryrefresh?stage=unicode&name=mx1Odieresis&value=214&go=yes`: one `fontlab.Update` on Ö; Ü the control | Ö 50 / 30 if `Update` helps; Ü unchanged | no error, Unicode 214; **no change** in either |
| 642b | `draw_path` two diamonds into `mx1dieresis` | refused | refused ("not KNOWN to be empty"), nothing changed |
| 643 | GUI: Contour > Convert > To Line on one circle of `mx1dieresis` | Ö 40 nodes, 50 / 30 / 700; Ü 34 nodes, 60 / 0 / 640 | as predicted, `verified`; both also took the offset of 640 |
| 644 | listener 0.129; gated `/debug/tryshapebox?stage=shapebox&name=mx1Odieresis&go=yes` | `mx1O` x 50–650, y 0–700; `mx1dieresis` x 410–670, y 780–880 | as predicted; no crash, `side_effect_detected` false; `top` holds the lower y; the layer's `componentsCount` read 0 |
| 645 | the same on `mx1Udieresis` | `mx1U` x 60–580, y 0–700; `mx1dieresis` x 380–640, y 780–880 | as predicted, no side effect |
| 646 | the same on `mx1dieresis` | x 260–520, y 780–880 | as predicted, no side effect |
| 647 | gated `stage=dependencies` on the source, Ö and Ü, in step | no prediction | a real bool, `false` on all three; no side effect |
| 648 | `set_glyph_sidebearings mx1dieresis` 280, −140 | Ö 50 / 10, Ü 60 / −20 if they follow; 50 / 30, 60 / 0 if they miss it | source 280 / −140; **Ö 50 / 30 / 700, Ü 60 / 0 / 640: missed** |
| 649 | `stage=dependencies` again on the three, out of step | no prediction | `false` on all three, as in 647; no side effect |
| 650 | `stage=shapebox` again on the three, out of step | the source moved, the composites' elements old | source x 280–540; Ö `mx1dieresis` x 410–670, Ü x 380–640. Source box plus offset would be 430–690 and 400–660: **the sum differs**, where it agreed in 644–646. No side effect |
| 651 | listener 0.130 / server 0.50; `get_glyph_outline` on Ö and Ü as left by 648 | `unverified`, `source_in_step` false; Ö 410–670 against 430–690 | as predicted; Ü 380–640 against 400–660; the reply tells the agent what to say; the identity components read true |
| 652 | GUI: X 0 on the element of `mx1dieresis`; both read | back in step, accent inside the base: `verified`, `element_boxes_checked` true, `source_in_step` true; 50 / 50 / 700, 60 / 60 / 640 | as predicted |
| 653 | `set_glyph_sidebearings mx1dieresis` 90, 50; Ö read | `unverified`, false, 220–480 against 240–500 if missed | **missed**, as described; `element_boxes_checked` still true; the reply carries `component_note` |
| 654 | `get_glyph_outline mx1U`, no components | unchanged, no new fields | as predicted, `verified` |
| 655 | GUI: width 50 % in the small panel on the element of `mx1dieresis` (meant for the component in Ü; see 656); Ü read, Ö margins | the composites follow; Ü dots x 175–305, `verified`, in step | as predicted; X read 20 in the panel; Ö 50 / 50 / 700 |
| 656 | GUI: width 40 % on the `mx1dieresis` component in Ü (X 120); read | `source_in_step` `"unknown"`, dots x 142–194, `verified` as before the build | as predicted; 60 / 60 / 640 on screen |

### S series: the changed icon and the save question (2026-11-09, FontLab 8.9.5, listener 0.130 to 0.133 / server 0.50 to 0.53; a new font each round; facts in [WATCH-POINTS.md](WATCH-POINTS.md))

| # | Step | Predicted | Result |
|---|---|---|---|
| 657 | new font; `/debug/trysync?stage=state` | package `isChanged` false, 1 glyph | as predicted; workspace false; icon dark |
| 658 | `create_glyph s1a_one`; state | flags false, 2 glyphs, icon dark | as predicted |
| 659 | GUI: Font > New Glyph `s1b_gui`; state; `/debug/walk` for `hasChanges` | icon blue, 3 glyphs; flags unknown | blue; all flags and `hasChanges` false on package and workspace |
| 659b | listener 0.131; `stage=state` on both glyphs; then close | history moved, `s1b_gui` showing it | package `hasHistoryStates` true, current 1, initial 0; workspace and both glyphs 0: **the glyph part wrong**. Closed: asked to save |
| 660 | new font; `create_glyph s2a_one`; state | package false, 0, 0; icon dark | current 0, initial 0, icon dark; `hasHistoryStates` true: **wrong** |
| 661 | `which=changes_applied` on the class, `s2a_one`; hover over the title | no crash, package history 0 → 1; icon unsure | no crash, `None`; package still 0: **wrong**; glyph `hasChanges` true, history 0 → 2 (current and initial); content unchanged; icon blue on the hover; Undo greyed out |
| 662 | close | asks to save | asked |
| 663 | control: new font; `create_glyph s3a_one`; state; hover; close, no call | flags and history unmoved, dark, no question | as predicted |
| 664 | new font; `create_glyph s4a_one`, `draw_polygon` square; state; outline; hover | `verified`, glyph `hasChanges` false, dark | as predicted |
| 665 | `which=changes_applied`, `s4a_one`; outline; hover | same nodes, `hasChanges` true, blue | as predicted; history 0 → 3 |
| 666 | `create_glyph s4b_one`; outline; state | the drawing survives | as predicted: 4 nodes, `verified`, 3 glyphs |
| 667 | close | asks to save | asked |
| 668 | listener 0.132 / server 0.51; new font; `create_glyph s5a_one`; state; close | `called` true, `glyph_has_changes` true; blue after a hover; asks to save | `called` true; `glyph_has_changes` false: **wrong**, and `save_question_note` came; glyph history 0 → 1; blue **without a hover**; asked |
| 669 | repeat on a new font, `s6a_one` | as 668: `glyph_has_changes` false, history 1 | `glyph_has_changes` true and history 0 → 2: **wrong**; no note; blue without a hover; asked |
| 670 | listener 0.132 / server 0.52; new font holding a GUI glyph; `create_glyph s7a_one` | `called` true, no `save_question_note`, whether `glyph_has_changes` reads true or false | as predicted; it read true, so the false case of 668 did not occur |
| 671 | `create_glyph s7b_one`; `draw_polygon` square | `verified`, `called` true, no note | as predicted; 4 nodes |
| 672 | `create_glyph s7c_one`; `set_glyph_width` 412 | 0 → 412, `called` true, no note | as predicted |
| 673 | `create_glyph s7d_one`; `draw_polygon`; `set_glyph_sidebearings` 50 / 70 | advance 320, `called` true, no note | as predicted |
| 674 | `create_glyph s7e_one`; `draw_path` with one cubic segment | `verified`, `nodes_match`, `called` true, no note | as predicted; 6 nodes, ink width 475 |
| 675 | `create_glyph s7f_one`; `set_glyph_unicode` 57344 | none → 57344, `called` true, no note | as predicted |
| 676 | `create_glyph s7g_one`; two writes to it: `draw_polygon`, then width 350 | each marked, no note, the outline stays | as predicted; read `verified`, left 100, advance 350. All 15 marks of 670–676: `glyph_has_changes` true |
| 677 | the person saves to a disposable file (Ctrl+S): icon blue → dark; `set_glyph_width s7a_one` 300, alone | 0 → 300, `called` true, no note, blue without a hover | as predicted |
| 678 | Ctrl+S, dark; `set_glyph_sidebearings s7b_one` 60 / 60, alone | advance 320, `called` true, no note, blue | as predicted |
| 679 | Ctrl+S, dark; `draw_polygon s7c_one`, alone | `verified`, right 112, advance 412, `called` true, no note, blue | as predicted |
| 680 | Ctrl+S, dark; `draw_path s7f_one`, alone | `verified`, `nodes_match`, `called` true, no note, blue | as predicted |
| 681 | Ctrl+S, dark; `set_glyph_unicode s7a_one` 57345, alone | none → 57345, `called` true, no note, blue | as predicted |
| 682 | close with X, after 681 only; Cancel | asks to save | asked; Cancel left the font open, unsaved |
| 683 | listener 0.132 / server 0.52; the font of 670–682, saved (dark); `delete_glyph s7g_one`, Yes; close with X | `deleted`, no mark, no note, dark, no question | as predicted; the delete was lost |
| 684 | new font; `create_glyph s8a_one`, `s8b_one`; the person saves | dark | as predicted |
| 685 | `delete_glyph s8b_one`, Yes | 3 → 2, no mark, dark | as predicted |
| 686 | gated `/debug/trynotify?stage=call&name=s8a_one&which=changes_applied&go=yes`, on a surviving, unchanged glyph | no crash, content unchanged, blue | `None`, no side effect, content unchanged; history 77 → 79, initial stays 77; **dark until a hover**, then blue |
| 687 | close with X; Cancel | asks to save | asked |
| 688 | listener 0.133 / server 0.53; new font; `create_glyph s9a_one`, `s9b_one`; saved; `delete_glyph s9b_one`, Yes; close with X; Cancel | `called` true, `via_glyph` `s9a_one`, no note, blue, asks | as predicted; blue at once, no hover. Setup: the first mark after the listener start (`s9a_one`) read `glyph_has_changes` false, with no note |
| 689 | saved; `delete_glyph s9a_one`, Yes, only `.notdef` left; close with X | `called` false with its reason, `save_question_note`, dark, no question | as predicted |
| 690 | new font; GUI glyph `s10a_brush`, one Power Brush stroke, its tab open; `create_glyph s10b_one`; saved; `delete_glyph s10b_one`, Yes; outline; `create_glyph s10c_one`; outline | `via_glyph` `s10a_brush`, three reads identical, still a brush element | as predicted; 117 nodes, fractions kept, 70 / −7 / 500 as in FontLab; blue at once; the Elements panel still shows the brush element |
| 691a | the font of 690 saved, dark, behind; a new font in front; `create_glyph s11a_one`, `s11b_one` | each gets its layer and is marked, as with one font | **wrong**: `layer_note`, no layer (the master name is used only with one font open), `called` false, `save_question_note` |
| 691b | GUI: open `s11a_one` in an editor tab; `create_glyph s11c_one` | layer from the other glyphs, marked | as predicted; the Layers panel then lists Regular |
| 691c | saved, blue → dark; `delete_glyph s11c_one`, Yes | `via_glyph` `s11a_one`; only the front font blue | as predicted; the font behind stayed dark |
| 692 | listener 0.133 / server 0.53; new font, the only one open; GUI glyph `s12a_brush`, one Power Brush stroke, its tab open; outline | `verified`, numbers equal to the panel, a brush element | as predicted; 77 nodes, 6 with fractions, 54 / 61 / 500 |
| 693 | saved, dark; `set_glyph_width` 540, alone; outline | 500 → 540, right 101, nodes identical, `called` true, no note, blue, brush kept | as predicted; the panel showed 54 / 101 / 540 without a tab switch |
| 694 | saved, dark; `set_glyph_sidebearings` 60 / 70, alone; outline | 60 / 70 / 515, `dx` 6, raw nodes identical, `called` true, no note, blue, brush kept | as predicted; the Elements panel Δ=(6,0); the Transform panel's X read 0, not 6 as guessed ([WATCH-POINTS.md](WATCH-POINTS.md)) |
| 695 | saved, dark; `set_glyph_unicode` 57346, alone, after the write and the read of 694; outline | none → 57346, nodes and `dx` identical, `called` true, no note, blue, brush kept | as predicted; the panel showed E002; F1 did not fire (one run) |
| 696, 697 | saved, dark; `draw_polygon`, then `draw_path`, on `s12a_brush`; outline | each refused, nothing changed, stays dark | as predicted; "not KNOWN to be empty"; 77 nodes, `dx` 6, 60 / 70 / 515; dark, brush kept |
| 698 | saved, dark; `set_glyph_width s12a_brush` 530, alone; close with X; Cancel | 515 → 530, `called` true, no note, asks to save | as predicted; asked, Cancel kept the font open |
| 699 | setup: `create_glyph s12b_one`, `s12c_one` (layers made, marked, no note); saved, dark; `set_glyph_sidebearings s12a_brush` 50 / 80, alone; close with X; Cancel | 50 / 80 / 515, `dx` −4, `called` true, no note, asks | as predicted; the panel 50 / 515 / 80, the Elements panel Δ=(-4,0); asked |
| 700 | saved, dark; `draw_polygon s12b_one`, alone; close with X; Cancel | `verified`, 4 nodes, 100 / −300 / 0, `called` true, no note, asks | as predicted; asked |
| 701 | saved, dark; `draw_path s12c_one`, alone; close with X; Cancel | `verified`, `nodes_match`, 6 nodes, ink width 475, `called` true, no note, asks | as predicted; asked |
| 702–706 | setup: `create_glyph s12d_one`, `s12e_one`; saved, dark; File > New Font, its icon dark; one click back on the first font; in one run on the font in front: `s12b_one` width 300 (702), sidebearings 50 / 50 (703), Unicode 57347 (704); `draw_polygon s12d_one` (705); `draw_path s12e_one` (706) | each lands in the front font, `fonts_open` 2, `called` true, no note; front blue, the font behind stays dark | as predicted; all five `verified` or re-read, no note; front blue, behind dark. Only the first write could turn the front icon blue |
| 707 | the font of 702–706 (blue, in front), an empty new font behind; close with X; Save | asks with two fonts open; closes; no file dialog | as predicted |
| 708 | `fontlab_status`, before the reopen | the other font in front, `fonts_open` 1, switch noted | as predicted |
| 709 | File > Open Fonts… the same file; 6 glyphs; outlines, Unicode | plain glyphs unchanged; `s12a_brush` 50 / 80 / 515, the same raw nodes and 6 fractions, `dx` −4, E002 | plain glyphs and Unicode as predicted (nodes, metrics, E003); brush: advance, `dx`, E002, 77 nodes and the brush element as predicted, the panel 50 / 515 / 80, Δ=(-4,0); **wrong for the nodes**: nearly all with new fractions, each under one unit away, left 50.466, right 80.362, ink width 384.171 |
| 710 | control: new glyph `s13a_brush`, one Power Brush stroke in the GUI, no tool write; outline | `verified`, equal to the panel, mostly whole units | as predicted; 84 nodes, 6 with fractions, 32 / 44 / 500, ink width 424 |
| 711 | close with X; Save; `fontlab_status`; File > Open Fonts… | asks; closes; no file dialog | as predicted; 7 glyphs |
| 712 | outline of `s13a_brush`; sidebearings of `s12a_brush` | same node count, brush kept, most nodes with fractions, ink width within one unit; `s12a_brush` still 50.466 / 80.362 | as predicted; 84 nodes, nearly all with fractions, 32.466 / 43.834 / 500, ink width 423.700, `verified`; `s12a_brush` unchanged (its nodes were not re-read) |
| 713 | close the empty new font behind; `fontlab_status` | closes, one font, icon of the saved font dark | as predicted |
| 714 | `set_kerning s12b_one : s12c_one` −30, alone; hover | 0 `none` → −30 `glyph : glyph`, table 0 → 1, reply warns; dark | as predicted, but `matched_by` `only font`, not `path` (wrong prediction: one font open); dark after a hover |
| 715 | gated `/debug/trynotify?stage=call&name=s12b_one&which=changes_applied&go=yes`, once, the pair's left glyph | `None`, no side effect, content unchanged, blue, perhaps after a hover | as predicted; **blue at once**; glyph `hasChanges` false → true, history 0 → 40; package flags unchanged |
| 716 | close with X; Cancel | asks | asked; the KERNING panel still empty |
| 717 | close with X; Save; File > Open Fonts…; `get_kerning` | −30 `glyph : glyph`, `table_size` 1, the panel lists it, 7 glyphs | as predicted |
| 718 | listener 0.134 / server 0.54; the font of 717, dark; `set_kerning s12d_one : s12e_one` −40 | 0 `none` → −40, table 1 → 2, `called` true, `via_glyph` `s12d_one`, no note, new point (2), blue | as predicted; `glyph_has_changes` false (the first mark after a listener start, as in 668 and 688); blue **only after a hover** |
| 719 | close with X; Cancel | asks | asked; the KERNING panel still lists one pair |
| 720 | Ctrl+S, dark; `set_kerning` the same pair and value | `changed` false, `called` false "no kerning entry is known to have changed", no note, `font_modified` false, stays dark | as predicted; the instruction still says closing loses the pair: a wording flaw |
| 721 | close with X, no question; File > Open Fonts…; `get_kerning` | −30 and −40, both `glyph : glyph`, `table_size` 2, the panel lists both | as predicted (saved by the Ctrl+S of 720, not at the question) |
| 722 | listener 0.134 / server 0.54; the font of 721, just reopened, dark; mouse on Claude Desktop, FontLab unfocused; new pair `s12c_one : s12d_one` −20, alone | `called` true, `via_glyph` `s12c_one`, no note; icon not predicted | as predicted; dark until a hover |
| 723 | Ctrl+S, dark; same conditions; existing pair `s12b_one : s12c_one` −30 → −35, alone | `called` true, `via_glyph` `s12b_one`, no note, table unchanged | as predicted; dark until a hover. Saved and reopened by the person: −35 and the −20 of 722 read back, the panel lists both |
| 724 | just reopened, dark; FontLab focused, mouse still in the grid (write 20 s after the person's reply); new pair `s12e_one : s12b_one` −15 | `called` true, no note; icon not predicted | as predicted; **blue at once** |
| 725 | Ctrl+S, dark; FontLab focused, mouse still; existing pair −15 → −25 | blue at once, if focus were the cause | **wrong**: dark until a hover; the focus idea is dropped |
| 726 | Ctrl+S, dark; mouse on Claude Desktop, FontLab unfocused; new pair `s12c_one : s12e_one` −10 | dark until a hover | as predicted |
| 727 | listener 0.134 / server 0.55; existing pair `s12c_one : s12e_one` −10 → −12 | `called` true, `via_glyph` `s12c_one`, marked point (2), point (4), no note | as predicted; the icon was not observed in this run |
| 728 | the same pair and value again | `changed` false, `called` false, point (2) "changed no entry", no point (4), no note, `font_modified` false | as predicted |

### KP series: the KERNING panel (2026-11-10, FontLab 8.9.5, a saved disposable font, one master; listener 0.134 to 0.136 / server 0.55 to 0.57; results in [topics/kerning.md](topics/kerning.md) §14)

"No row" means the panel did not list the pair after a hover over the panel. Probe: `/debug/trynotify?stage=call&name=p1a_one&which=W&on=class&go=yes`, plus `&id_from=fg` from 737.

| # | Step | Predicted | Result |
|---|---|---|---|
| 729 | names only: `/debug/classdir?name=flItems`, docstrings of 15 members | the four calls exist with the probe's arguments | as predicted; no name mentions kerning or classes; `notifyFontSelected(uint id)`, `notifyPackagesUpdated()`, `notifyFeaturesChanged(uint, bool)`, `notifyModelChanged()` seen |
| 730 | new `p1a_one`, `p1b_one`; `set_kerning p1a_one : p1b_one` −30 | set, no row | as predicted; table 5 → 6, footer 5 |
| 731 | `glyph_updated`, object ids | no error, no row | **wrong on the error**: `SystemError` "returned a result with an exception set"; no side effect; no row |
| 733 | `package_updated`, the `flPackage` (run before 732) | no error, **a row** | no error, no side effect; **wrong: no row**. The grid selection moved by the person's click; those clicks refreshed nothing |
| 732 | `package_content`, object id | `SystemError`, no row | as predicted |
| 734 | `workspace_has_changes` | no error, no row | as predicted |
| 735 | names only: `flPackage`, `flWorkspace`, `flGlyph` docstrings | another id-like name; no "set current package" | `fgId` `int`, `findFgId(uint)`, `findPackageId(uint)`, `fgGlyphId` `FgTypeId`, `id` "object id"; `activateNext`, `activatePrev` unexplained |
| 736 | listener 0.135; `stage=ids&name=p1a_one&go=yes` | `fgId` small, `findPackageId` returns this package | as predicted: `fgId` 1, `fgGlyphId` 11, `same_package` true, no side effect |
| 737 | `font_selected`, `fgId` 1 | no error, no row | as predicted |
| 738 | `package_content`, `fgId` 1 | no error, no row | no error; **wrong: a row appears**, footer 6, no hover (the panel sat a little higher afterwards) |
| 739 | `p1b_one : p1a_one` −20 | set, no row | as predicted; table 7, footer 6 |
| 740 | `font_selected` alone, repeat of 737 | no row | as predicted, after a wait |
| 741 | `package_content`, same pair | a row, footer 7 | as predicted, the mouse on Claude Desktop |
| 742 | `p1a_one : p1a_one` −10 (no row, footer 7), then `package_content` with no `font_selected` between | a row, footer 8 | as predicted |
| 743 | new listener run; −10 → −15 (row still −10, after a hover), then `package_content` | row −15, footer 8 | as predicted, at once |
| 744 | 0.136 / 0.56; `p1b_one : p1b_one` −25 | row at once, `called` true, "was asked" text | as predicted; footer 9, no hover; `glyph_has_changes` false (first mark after a listener start) |
| 745 | −25 → −28 | −28 at once | as predicted |
| 746 | −28 again | no calls, panel unchanged | as predicted; point (1) still said the panel "does not show it yet": a wording flaw, fixed in 0.57 |
| 747 | two saved fonts, the test font in front; `s12b_one : p1a_one` −33 | `matched_by` `path`, row at once; the other font does not gain it | as predicted; table 10; the other font's list empty, footer 0. Its `fgId` was not read |
| 749 | font saved, icon dark; mouse on Claude Desktop, FontLab unfocused; new `s12c_one : p1a_one` −11 | blue at once | as predicted |
| 750 | same conditions; −11 → −13 | blue at once | as predicted; footer stays 11 |
| 751 | same; new `s12d_one : p1a_one` −14 | blue at once, footer 12 | as predicted |
| 752 | same; −14 → −16 | blue at once | as predicted |
| 753 | same; new `s12e_one : p1a_one` −17 | blue at once, footer 13 | as predicted |
| 748 | server 0.57, FontLab freshly started and the font reopened (the pair of 753 read back); `s12b_one : p1b_one` −9, the mouse off FontLab | row at once, blue at once, no hover note | as predicted; table 13 → 14, footer 14 |
| 754 | −9 again | no calls, point (1) "already set" | as predicted, `font_modified` false |

### OS series: open contours through a save and reopen (2026-11-10, FontLab 8.9.5, listener 0.136 / server 0.57, through Claude Code; a font made with File > New Font, one master, prefix `os1_`; results in [topics/geometry.md](topics/geometry.md) §8g)

| # | Step | Predicted | Result |
|---|---|---|---|
| 755 | other font closed; File > New Font, saved by the person to a disposable file; `fontlab_status`, `list_glyphs` | one font, a path, only `.notdef` | as predicted |
| 756 | `create_glyph os1_v`; `draw_path` the open V (24, 482), (132, 69), (228, 462); outline | `verified`, `closed` [false], 3 `On` nodes, 24 / −228 / 0, `svg_path` without Z, `called` true, no note | as predicted |
| 757 | `create_glyph os1_arch`; `draw_path` the open arch On (105, 104), Curve (105, 280), Curve (398, 255), On (398, 104); outline | `verified`, `closed` [false], box 105 / 398 / 104 / 226.804, last node `smooth` false | as predicted |
| 758 | `create_glyph os1_mix`; `draw_path` the open V and a closed counterclockwise square (300, 0) to (450, 150); outline | `closed` [false, true], `verified`, box 24 / 450 / 0 / 482 | as predicted |
| 759 | control: `create_glyph os1_gui`; the person draws an open V with the Pen tool; outline | `verified`, `closed` [false] | as predicted: (38, 451), (150, 97), (243, 407), 38 / −243 / 0 |
| 760 | close with X; Save | asks; no file dialog; closes | as predicted |
| 761 | `fontlab_status` | `font_open` false | as predicted |
| 762 | File > Open Fonts… the file; `fontlab_status`, `list_glyphs` | 5 glyphs | as predicted; FontLab reopened the `os1_gui` editor tab by itself |
| 763 | outlines of the four glyphs | identical to 756–759, `verified` | as predicted: nodes, kinds, smooth and `closed` flags, boxes and margins identical |
| 764 | the person's screenshot, `os1_mix` selected | the Elements panel lists an open "3/3" and a closed "4/4" with different icons | as predicted; the bottom bar 24 / 0 / −450 |

### RT series: rotated components (2026-11-10, FontLab 8.9.5, listener 0.136 / server 0.57, through Claude Code; the disposable font of the OS series, one master, prefix `rt1_`; results in [topics/reading.md](topics/reading.md) "Components: rotation")

Rotations were set in the Transform panel with Apply, its origin selector left at the bottom-left dot. The person saved the font once, before 769 (Ctrl+S, seen in the OUTPUT panel).

| # | Step | Predicted | Result |
|---|---|---|---|
| 765 | `create_glyph rt1_base`; `draw_polygon` (100, 50) to (400, 250); width 600; outline | `verified`, 100 / 200 / 600 | as predicted |
| 766 | `create_glyph rt1_curve`; `draw_path` the bulging square of the tool description; width 600; outline | `verified`, ink width 475, y 0–400 | as predicted; 0 / 125 / 600 |
| 767 | `create_glyph rt1_one`; the person: Add Component `rt1_base`, X 0, Y 0; outline | no crash; `is_component` true, identity, `source_in_step` true | as predicted; the panel 100 / −400 / 0 |
| 768 | rotation 90°, Apply; the person's screenshots; outline | m11 ≈ 0, m22 ≈ 0, \|m12\| 1; 200 × 300; `verified`; `source_in_step` `"unknown"`; direction not predicted | as predicted: m12 1, m21 −1, offset (150, −50), counterclockwise; ink −100–100 × 50–350; the panel −100 / −100, Δ=(150,−50). The first screenshot, said to be after Apply, showed the field at 90 and the shape not turned; the second, after a return to FontLab, turned. Not settled; 769 showed no lag |
| 769 | `create_glyph rt1_two`; the person adds `rt1_base` and types 30 without Apply; reads at 45 s and 75 s, then Apply with reads every 15 s; outline | 359.808 × 323.205, `verified` | the first reads: identity (Apply not yet clicked); after Apply every read showed the 30° matrix from the first, within 15 s; the canvas turned at once; offset (38, −43); ink −0.397–359.410 × 50.301–373.506, `verified` |
| 770 | `create_glyph rt1_three`; the person adds `rt1_curve` and rotates it 30° | 554.026 × 546.410, `verified` | as predicted: ink −200–354.026 × 0–546.410, offset (0, 0); the panel −200 / −355 (rounded) |
| 771 | `create_glyph rt1_four`; the person adds `rt1_base` twice; the second: width 30 %, height 30 %, rotation 90°, Apply; then X 250 and Y 80 in the small element panel | inside the first, x 175–235, y 110–200; `unverified`, `element_boxes_note` | after Apply as expected (Δ=(115,20), small); **wrong** after X and Y: the scale was dropped (m11 0, m12 1, m21 −1, m22 0, offset (250, 80)), the component full size at 0–200 × 180–480; the glyph `verified`, 0–400 × 50–480. The inside case was not reached |

### T9 series: save and reopen of a font made by `flPackage()` (2026-11-10, FontLab 8.9.5, listener 0.136 / server 0.57, through Claude Code; one master, prefix `t9a_`; results in [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k)

| # | Step | Predicted | Result |
|---|---|---|---|
| 772 | no font open, listener freshly started; `fontlab_status` | reachable, 0.136 / 0.57, `font_open` false | as predicted |
| 773 | gated `/debug/tryfont?stage=construct&go=yes` | `CountFonts` 0 → 1, master `Regular`, path empty | as predicted: upm 1000, 1 glyph, `fileName` "Unnamed Regular.xfo", `hasPackage` true; the font window "Unnamed Regular" opened |
| 774 | `fontlab_status`, `list_glyphs` | 1 font, no path, only `.notdef` | as predicted |
| 775 | `create_glyph t9a_box`, `draw_polygon` (100, 0) to (500, 700), width 600, sidebearings 60 / 40, Unicode E000; `create_glyph t9a_curve`, `draw_path` the bulging square from x 50; `create_glyph t9a_open`, `draw_path` the open arch of 757; widths 620 and 500; outlines | every write verified and marked; the first glyph's layer `Regular` from the package master | as predicted: `layer_name_source` "package master", then "other glyphs"; `called` true eleven times (`glyph_has_changes` false only on the first create); all three `verified` |
| 776 | close with X | FontLab asks; a file dialog, since there is no path | as predicted; the dialog "Save Font File" offered the name `Unnamed-Regular` and FontLab Compact (*.vfc); the person saved; the font closed |
| 777 | `fontlab_status` | `font_open` false | as predicted |
| 778 | File > Open Fonts… the file; `fontlab_status`, `list_glyphs`, three outlines, `check_glyph_unicode t9a_box` | a path, 4 glyphs, everything as in 775 | as predicted: nodes, `closed` flags, boxes, margins, widths and E000 identical, all `verified`. The layer name was not re-read |

### EX series: open contours on export (2026-11-10, FontLab 8.9.5, listener 0.136 / server 0.57, through Claude Code; the saved font of the T9 series, one master, prefix `ex1_`; results in [topics/geometry.md](topics/geometry.md) §8g)

The person exported with File > Export > Export Font As…, default settings, only the profile chosen, to a disposable folder outside the repository. The exported files were read twice: by a read-only standard-library script outside the repository (TrueType `glyf`, CFF charstrings), and by FontLab after File > Open. The OUTPUT panel printed only FontLab's line "Font has been successfully exported to: …" for each export.

| # | Step | Predicted | Result |
|---|---|---|---|
| 779 | `fontlab_status`, `list_glyphs` | a new unsaved font, only `.notdef` | **wrong, no effect on the test**: the saved T9 font, 4 glyphs |
| 780 | `create_glyph ex1_v`; `draw_path` the open V of 756 | `verified`, `closed` [false], 3 nodes | as predicted; advance 0 |
| 781 | `create_glyph ex1_mix`; the open V and the closed square of 758 | `closed` [false, true], `verified` | as predicted |
| 782 | control: `create_glyph ex1_sq`, the closed square alone | `verified`, `closed` [true] | as predicted |
| 783 | the person: export, profile **TrueType** | a `.ttf`; a warning about open contours possible | `t9a.ttf`; no warning, only the success line |
| 784 | the script reads the `.ttf` | each open contour closed by an implicit segment (the V a 3-point triangle); dropped or outlined as alternatives | **wrong: dropped.** `ex1_v` and `t9a_open` (the open arch of 775) empty; `ex1_mix` only the square; `ex1_sq` unchanged. The squares clockwise, cubics turned quadratic, `t9a_box` named `uniE000`, `.null`, `uni000D`, `space` added, 10 glyphs |
| 785 | the person saves and closes the `.vfc`, opens the `.ttf` | one font, the `.ttf` | as predicted (the save was not planned; harmless) |
| 786 | outlines of the four glyphs in the `.ttf` | as in 784 | as predicted: both empty, the squares `verified` and clockwise; FontLab lists `.null` as `NULL` |
| 787 | the person closes the `.ttf` and reopens the `.vfc`; outlines of `ex1_v`, `ex1_mix` | the open V intact | as predicted: nodes and `closed` flags as in 780, 781, `verified` |
| 788 | the person: export, profile **OpenType PS** | `ex1_v` and `t9a_open` empty, `ex1_mix` only the square; or the V kept as a closed path | `t9a.otf`; no warning, only the success line |
| 789 | the script reads the `.otf` | as predicted in 788 | as predicted: dropped; the squares counterclockwise, cubics kept, null glyph `uni0000`, 10 glyphs |
| 790 | the person opens the `.otf` (the `.vfc` behind); outlines | as in 789 | as predicted, `fonts_open` 2 |
| 791 | the person closes the `.otf` | the `.vfc` left open | as predicted: `fontlab_status` before 792 showed one font, `t9a.vfc` |

### PB series: Power Brush fractions at load (2026-11-10, FontLab 8.9.5, listener 0.136 / server 0.57, through Claude Code; the font of the EX series, one master, prefix `pb1_`; results in [topics/reading.md](topics/reading.md) §8p)

No tool wrote to the brush glyphs. The `.vfj` file was read read-only as JSON, outside the repository. FontLab's Thickness tool sets only local thickness (its tooltip), so no second brush could be set; `pb1_b` uses the default brush too.

| # | Step | Predicted | Result |
|---|---|---|---|
| 792 | the person: Font > New Glyph > Create Blank `pb1_a`, one Power Brush stroke, default brush | n/a | drawn; the panel 117 / 112 / 500 |
| 793 | the same for `pb1_b` (the plan said another brush width: not available) | n/a | drawn, thickness unchanged; the panel 52 / 88 / 500 |
| 794 | outlines | `verified`, mostly whole units, a few fractions | as predicted: `pb1_a` 75 nodes, 6 fractional (control points), 117 / 112, ink width 271; `pb1_b` 71 nodes, 18 fractional, 52 / 88, ink width 360; one brush element (`is_composite` true) each |
| 795 | the person: File > Save As, FontLab JSON, `pb1.vfj` | the font stays open | as predicted; OUTPUT "is saved to" the file |
| 796 | the `.vfj` read as text | the stroke stored; whole-unit or no outline nodes; or fractional nodes as the alternative | **half right**: each glyph stores its outline as in memory (the same 6 and 18 fractions, written to 6 significant digits, e.g. 295.232 for 295.23195…) **and** its open skeleton in whole units (9 and 12 nodes) with `"strokeBrush": "50,50,60,1,1,100,100,100,100,100"` |
| 797 | outline of `pb1_a` | unchanged | as predicted (`pb1_b` not re-read) |
| 798 | the person closes with X (no question) and opens `pb1.vfj` | reopens | as predicted |
| 799 | outlines; the person reads the panel | nearly all nodes fractional; `pb1_a` gains .466 on the left; `pb1_b` another fraction if the brush sets it; the panel in whole numbers | node counts 75 and 71 kept, **every node fractional**, each under one unit away, `verified`; `pb1_a` 117.023 / 112.466, ink width 270.511 (**wrong**: .466 on the right, not the left); `pb1_b` 52.466 / 88.466, ink width 359.068 (no second brush, so not a test of the brush); on both, x extremes end in .466 / .534 and y extremes in .472 / .528; the panel 117 / 112 and 52 / 88, in the grid bar and the editor |

### Server 0.58 check (2026-11-10, FontLab 8.9.5, listener 0.136 / server 0.58, through Claude Code after a full restart of Claude Desktop; `pb1.vfj`, prefix `ex2_`)

| # | Step | Predicted | Result |
|---|---|---|---|
| 800 | `fontlab_status` | 0.136 / 0.58 | as predicted |
| 801 | `create_glyph ex2_v`; `draw_path` the open V of 756 | `verified`, `closed` [false], the new `agent_instruction` (export drops open contours) | as predicted, nothing else changed. The `draw_path` description loaded in this Claude Code session after one restart still had the 0.57 text (stale tool description) |

### PB2 series: a `.vfc` against a `.vfj` at load (2026-11-10, FontLab 8.9.5, listener 0.136 / server 0.58, through Claude Code; a font made with File > New Font, one master, prefix `pb2_`; stage A of three, stages B and C below; results in [topics/reading.md](topics/reading.md) §8p)

No tool wrote anything (the change counter stayed at 2). Both files were saved from the same font in memory, to a disposable folder outside the repository, and each was reopened alone with File > Open Fonts… The `.vfc` itself was not read (binary). The PB line "x extremes end in .466 / .534" (799) holds only for the right extreme: `pb1_a` ended in .023 on the left.

| # | Step | Predicted | Result |
|---|---|---|---|
| 802 | `fontlab_status` | 0.136 / 0.58, no font open | as predicted |
| 803 | the person: File > New Font, Encoding None | one unsaved font | as predicted: "Unnamed Regular", no path, `.notdef` only |
| 804 | the person: Create Blank `pb2_a`, one Power Brush stroke, default brush | drawn | the panel 55 / 124 / 500 |
| 805 | outline | `verified`, mostly whole units, a few fractional control points | as predicted: 66 nodes, 4 fractional (control points), ink box 55..376 × 125..438, 55 / 124 / 500, one brush element, identity |
| 806 | the person: File > Save As, FontLab JSON, `pb2.vfj` | the font stays open | as predicted (6,196 bytes) |
| 806b | the `.vfj` read as text | as 796 | as predicted: the outline as in memory (fractions to 6 significant digits, `56.0409 330.065`), an open skeleton in whole units (11 node entries), the default `strokeBrush` |
| 807 | the person: File > Save As, FontLab Compact, `pb2.vfc` | the font stays open, its path the `.vfc` | as predicted (7,578 bytes) |
| 808 | outline | as 805 | as predicted |
| 809 | the person closes with X, opens `pb2.vfc` | no question | as predicted; FontLab reopened the `pb2_a` tab by itself |
| 810 | outline; the person reads the panel | every node fractional, count kept; x extremes .466 / .534, y .472 / .528; the panel 55 / 124 / 500 | 66 nodes, **every node fractional**, each under one unit away, `verified`; 55.211 / 124.466 / 500, ink box 55.211..375.534 × 125.101..437.528: **half right**, the right and top end in .534 / .528, the left and bottom in .211 / .101; the panel 55 / 124 / 500 in the grid bar and the editor |
| 811 | the person closes with X, opens `pb2.vfj` | no question | as predicted; `font_note`: another font with the same name, from a different file |
| 812 | outline | identical to 810 | as predicted: **identical node by node, to full precision** |

**Stage B: another brush** (2026-11-10, the same session and font, `pb2.vfj` open; saved as `pb2b.vfj` next to the other files; no tool wrote anything).

| # | Step | Predicted | Result |
|---|---|---|---|
| 813 | the person selects the Brush tool (B) and hovers over its property bar; then Window > Panels; then Window > Panels > Brush | brush fields in the bar, or a panel | the bar picks only the kind: Simple brush, Power brush (editable), Erasing brush, Soft brush. **Window > Panels > Brush** shows an ellipse marked 60° and 50%, a size field 50 and a slider. Window > Panels also lists Stroke (not opened) |
| 814 | the person: Create Blank `pb2_b`, its empty editor in front | an empty glyph | as predicted: 0 / 0 / 500, no element |
| 815 | the person: Brush panel size 50 → 80, Enter | the field 80; `pb2_a` unchanged | as predicted: `pb2_a` identical to 812 |
| 816 | the person: one Power Brush stroke in `pb2_b` | drawn | the panel 41 / 13 / 500 |
| 817 | outline | `verified`, mostly whole units | as predicted: 55 nodes, 12 fractional (control points), ink box 41..487 × 62..505, one brush element |
| 818 | the person: File > Save As, FontLab JSON, `pb2b.vfj` | `pb2.vfj` kept | as predicted (9,901 bytes; the older files unchanged) |
| 819 | `pb2b.vfj` read as text | `pb2_b`'s `strokeBrush` begins with 80, `pb2_a`'s with 50 | as predicted: `"80,50,60,1,1,100,100,100,100,100"` and `"50,50,60,…"`; `pb2_b`'s skeleton in whole units (7 entries). Not predicted: `pb2_a`'s stored outline now has a fraction in every coordinate (132 numbers), the outline rebuilt at the 811 load |
| 820 | the person closes with X (no question) and opens `pb2b.vfj` with File > Open Fonts…; outlines; the person reads the grid bar and the editor | `pb2_a` as 812; `pb2_b` fractions other than .534 / .528 | as predicted: `pb2_a` identical to 812; `pb2_b` 55 nodes, every node fractional, `verified`, **40.546 / 12.546** / 500, ink box 40.546..487.454 × 61.951..505.049 (each side 0.454 out, top and bottom 0.049 out). The grid bar and the editor: **40 / 12 / 500** |
| 821 | the person: size 80 → 50 (asked to click empty canvas first if the stroke was selected) | the field 50; `pb2_b` unchanged | **wrong**: FontLab rebuilt `pb2_b`'s stroke with size 50 at once: 60 nodes, ink box **50..478 × 75..492 in whole units**, a few fractional control points, 50 / 22 / 500, `verified`. The stroke's element stays the active one without a selection. Closed with Don't Save at FontLab's question (822a) |

**Stage C: how the panel shows fractions** (2026-11-11, FontLab 8.9.5, listener 0.136 / server 0.58, through Claude Code; a font made with File > New Font, prefix `pb3_`; never saved).

| # | Step | Predicted | Result |
|---|---|---|---|
| 822 | the person: File > New Font, Encoding None | one unsaved font | as predicted |
| 823 | `create_glyph pb3_c` | created | as predicted, layer `Regular`, marked |
| 824 | `draw_path`: a curve from (100, 0) to (100, 200) with controls at x 49, a line to (300, 200), a curve to (300, 0) with controls at x 351 | `verified`, `nodes_match` | as predicted: 8 nodes, nothing rounded |
| 825 | outline | ink x 61.75..338.25 | as predicted, `verified`, y 0..200. Not predicted: **advance 0**, so RSB −338.25 |
| 827a | the person reads the grid bar | 61 / 0; RSB −338 if truncated, −339 if rounded down | **61 / 0 / −339**: rounded down |
| 826 | `set_glyph_width pb3_c 300`; `get_glyph_sidebearings` | RSB −38.25 | as predicted: 61.75 / −38.25 / 300 |
| 827b, c | the person reads the grid bar, then the editor | 61 / 300 / −39 | as predicted, in both |
| 828 | `finish_changes` (3 changes); the person closes with X | FontLab asks | as predicted; Don't Save |

### Server 0.59 check (2026-11-11, FontLab 8.9.5, listener 0.136 / server 0.59, through Claude Code after a full restart of Claude Desktop; a font made with File > New Font, prefix `sb1_`; never saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 829 | `fontlab_status` | 0.136 / 0.59 | as predicted, no font open |
| 830 | `create_glyph sb1_c`; `draw_path` the `pb3_c` shape; `get_glyph_sidebearings`; `finish_changes`; the person closes with X | 61.75 / −338.25 / 0 with the new `note`; FontLab asks | as predicted; Don't Save. The `get_glyph_sidebearings` description loaded in this Claude Code session after one restart still had the 0.58 text (stale tool description) |

### NF series: how new fonts are named, File > New Font and `flPackage()` (2026-11-11, FontLab 8.9.5 in Demo mode, listener 0.136 / server 0.59, through Claude Code; no File > Save stage, nothing saved; results in [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k)

| # | Step | Predicted | Result |
|---|---|---|---|
| 831 | no font open; File > New Font, the user sets Encoding None; `fontlab_status`, `/debug/tryfont?stage=state`, `/font/current` | 1 font, no path, current | as predicted: `Unnamed Regular`, `ffn` "Unnamed Regular", `psn` "Unnamed-Regular", `fileName` "Unnamed Regular.xfo", upm 1000, 750 / −250 / 700 / 500; `constructed` false |
| 832 | a second File > New Font, the user sets Encoding None | (a) the same name, or (b) a unique one | (b): title bar `Unnamed1 Regular`, family `Unnamed1`, `psn` "Unnamed1-Regular", `fileName` "Unnamed1 Regular.xfo"; FONTS panel "Unnamed1 (one font)" |
| 833 | `fontlab_status`, the probe state, `/font/current` | the new font current | as predicted: `fonts_open` 2, `font_changed` from `Unnamed Regular`; `/font/current` gave `package_names_unavailable` (no path to match) |
| 834 | gated `/debug/tryfont?stage=construct&go=yes`, the two fonts open | `CountFonts` 2 → 3; (a) `Unnamed2 Regular` or (b) `Unnamed Regular` | (a): `Unnamed2 Regular`, `psn` "Unnamed2-Regular", current, its tab in front (screenshot), FONTS panel 1/3; the tab showed Encoding None, cause not settled |
| 835 | listener restarted; the user set the `Unnamed2` tab to Encoding Type 1 Adobe Standard; the same construct | `Unnamed3 Regular`, in front; Encoding Type 1 Adobe Standard (taken over), None (the API font's own) or Latin Simple (the GUI default) | `Unnamed3 Regular`, `psn` "Unnamed3-Regular", current, in front, FONTS panel 1/4; Encoding **None** |

### EN series: can the API set the Font window's encoding? (2026-11-11, the same stage as NF, five fonts open at the end; names-only probes, nothing constructed or changed; results in [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k, E1)

| # | Step | Predicted | Result |
|---|---|---|---|
| 836 | `/debug/fldir?contains=encod,codepage,codepg`, `/debug/moddir?contains=encod,codepage`, `/debug/fontdir?stage=dir` | unknown | no encoding name in the `fontlab` module; the legacy font has a member `coding` |
| 837 | `/debug/fontdir?stage=sub&attr=coding`, then `memberdir` `encoding` | unknown | an `fgCoding`: `cmaps`, `codepageRange`, `encoding` (an `fgExtMapUIntToString`), `encodingType` (`encDefault` / `encStandard` / `encCustom`), `importedEncoding`, `unicodeRange`: the font's own encoding data, not the window's |
| 838 | `/debug/classdir` of `flPreferences`, `flWorkspace`, `MainWindow` | unknown | `flPreferences` (555 names) has `fontDefaultEncoding` (QString), `fontDefaultMode`, `fontFriendlyEncoding`; `flWorkspace.currentFontPanel` and `activeFontPanel` return the Font window as a `QWidget*`; `uiState` a QString |
| 839 | the user opens Preferences > Font Window, changes nothing, Cancel | a default-encoding setting | "Filter: Default: Encoding None"; the user recalls never changing it |
| 840 | File > New Font, the Encoding box untouched; screenshot | `Unnamed4 Regular`, Latin Simple (E1) | as predicted: File > New Font ignores the preference |

### NM series: writing a font's names, in Font Info and through the API (2026-11-11 and, from 881, 2026-11-12; FontLab 8.9.5 in Demo mode, listener 0.136–0.145 / server 0.59, through Claude Code; one font open, from 894 up to three; no File > Save stage, nothing saved; results in [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k)

| # | Step | Predicted | Result |
|---|---|---|---|
| 841 | `Unnamed4 Regular` alone (File > New Font, Latin Simple); `/font/current` | both views agree | as predicted: package and legacy `Unnamed4` / `Regular` / `Unnamed4 Regular` / `Unnamed4-Regular`, `sgn` `Unnamed4` |
| 842 | the user sets Encoding None; read | no name changes | as predicted |
| 843 | Font Info: Family name `Nm Test`, Tab, screenshot, OK; read | Full name, PostScript, Style group follow | wrong: before OK nothing followed; after OK only `tfn` = `Nm Test`; legacy all `Unnamed4` |
| 844 | look | | tab title `Unnamed4 Regular` (the Full name), FONTS panel `Nm Test` |
| 845 | Font Info: Build Names, screenshot, OK; read | `Nm Test Regular`, `NmTest-Regular`, `Nm Test` | the dialog as predicted. The first read came before OK took effect (old names) and is void, as the user pointed out; the repeated read: the package as predicted; legacy family `Nm Test`, Full and PostScript names still `Unnamed4…` |
| 846 | look; Font Info reopened | tab `Nm Test Regular`, FONTS `Nm Test` | as predicted; Font Info shows the built names |
| 847 | the font closed unsaved, no font open; File > New Font, Encoding None; read | `Unnamed` or `Unnamed5`: open | `Unnamed Regular`: the name was reused (lowest free number or a restarted count, not told apart). `CurrentFont()` now returned nothing with no font open; at the start of this FontLab run it returned the placeholder ([WATCH-POINTS.md](WATCH-POINTS.md)) |
| 848 | Font Info: Family name `Nm Retest`, OK; read after the user confirmed the dialog closed | as 843 | as predicted |
| 849 | Build Names, screenshot, OK; read after the dialog closed | as the repeated 845 | as predicted: `Nm Retest Regular`, `NmRetest-Regular`, `Nm Retest`; the legacy family caught up, its Full and PostScript names did not |
| 850 | look | tab `Nm Retest Regular`, FONTS `Nm Retest` | as predicted |
| 851 | listener 0.137; `/debug/trynames?stage=state` | as 849 | as predicted; `fileName` still `Unnamed Regular.xfo` |
| 852 | the font closed unsaved; `/debug/tryfont?stage=state` | no font | as predicted |
| 853 | gated `/debug/tryfont?stage=construct&go=yes`; `trynames` state | `Unnamed Regular`, all names agree | as predicted |
| 854 | gated `trynames` `set tfn = Nm Api` | read back; only `tfn` changes | as predicted; legacy family `Unnamed` |
| 855 | look | tab unchanged; FONTS panel: open | tab `Unnamed Regular`, FONTS **`Unnamed`**: the display did not follow |
| 856–857 | gated `refresh` (`notifyPackageContentUpdated(24)`); look | no name changes | no error, no change; FONTS `Unnamed` |
| 858 | gated `/debug/trysync?stage=package_update` (`flPackage.update()`); look | no name changes | returned true, no change; FONTS `Unnamed` |
| 859 | gated `trysync?stage=workspace_update` (`flWorkspace.instance().update()`); look | no name changes | returned true, no change; FONTS `Unnamed` |
| 860 | Font Info opened, screenshot | Family `Nm Api` | as predicted: the package's `tfn` is the field Font Info edits |
| 861 | Cancel; look | | FONTS `Unnamed`: opening Font Info redraws nothing |
| 862 | listener 0.138; `refresh&which=packages` (`notifyPackagesUpdated()`); look | no name changes | no error, no change; FONTS `Unnamed` |
| 863 | `refresh&which=package` (`notifyPackageUpdated(24)`); look | no name changes | no error, no change; FONTS `Unnamed` |
| 864 | listener 0.139; gated `store` (`store_font_info(<fgFont>)`); look | (a) package → legacy, (b) legacy → package, (c) nothing | (c): no error, no name changed; FONTS `Unnamed` |
| 865 | gated `legacy_set familyName = Nm Api`; look | read back | as predicted; both views `Nm Api`; FONTS `Unnamed` |
| 866 | `refresh&which=packages` again; look | no name changes | no error, no change; FONTS `Unnamed` |
| 867 | listener 0.140 (`fontlab_status` now named the font "Nm Api Regular" from the legacy family, with a `font_changed` note); `refresh&which=model` (`notifyModelChanged()`); look | no name changes | no error, no change; FONTS `Unnamed` |
| 868 | `refresh&which=properties` (`notifyPropertiesChanged(<flPackage>)`); look | no name changes | no error, no change; FONTS `Unnamed` |
| 869 | `refresh&which=changed` (`flPackage.changed()`); look | no name changes | no error, no change; FONTS `Unnamed`; the icon looked unchanged, not blue |
| 870 | Font Info opened (Family `Nm Api`, the rest `Unnamed…`), OK without an edit; look | the panel redraws | wrong: FONTS `Unnamed` |
| 870b | the mouse rested on the FONTS line, no click | | no change |
| 871 | File > New Font; look | open | the panel rebuilt: "Nm Api (one font)" and "Unnamed (one font)"; the new font took the family `Unnamed`, the lowest free family name, so both tabs read "Unnamed Regular" |
| 872 | the new font closed unsaved; listener 0.141; `trynames` state; look | the legacy family `Nm Api` | the legacy family read **`Unnamed`** again, `tfn` `Nm Api`; FONTS "Nm Api": the panel shows `tfn` ([WATCH-POINTS.md](WATCH-POINTS.md)) |
| 873 | gated `set tfn = Nm Two`; look | read back; FONTS stays `Nm Api` | as predicted |
| 874 | `refresh&which=applied` (`notifyChangesApplied('Glyphbridge test', <flPackage>, False)`); look | no name changes | no error, no change; the icon turned **blue**; FONTS `Nm Api` |
| 875 | `refresh&which=readed` (`notifyPackageReaded(<flPackage>)`); look | no name changes | no error, no change, still 1 font and 1 package; FONTS `Nm Api` |
| 876 | `refresh&which=added` (`notifyPackageAdded(<flPackage>)`); look | no change, or a duplicate line | no error, no change, still 1 font and 1 package; FONTS `Nm Api`, no duplicate |
| 877 | the font closed unsaved; listener 0.142; `/debug/tryfont?stage=state` | no font | as predicted |
| 878 | gated `construct_named&family=Nm Three`; look | all four names read back; tab and FONTS: open | as predicted for the names (`tfn` Nm Three, `ffn` Nm Three Regular, `psn` NmThree-Regular, `sgn` Nm Three); tab "Unnamed Regular", FONTS "Unnamed": FontLab takes its copy inside `flPackage()`. Read only (walker): `flPackage.info.openTypeNamePreferredFamilyName` "Unnamed", the other info names as written |
| 879 | File > New Font; look | open | FONTS "**Unnamed (2 fonts)**": the Nm Three font grouped with the new one; its tab still "Unnamed Regular"; the new font's Preferred family "Unnamed" |
| 880 | the new font closed unsaved; listener 0.143; `trynames` state; look | Preferred family "Unnamed" | as predicted; FONTS "**Nm Three (one font)**" (closing a font rebuilds the list), tab "Unnamed Regular"; legacy family "Unnamed" |
| 881 | 2026-11-12, no font open, a new listener run (0.143); gated `/debug/tryfont?stage=construct_named&family=Nm Four&go=yes`; `trynames` state | as 878: the four names read back; Preferred and legacy family "Unnamed" | as predicted: `tfn` Nm Four, `ffn` Nm Four Regular, `psn` NmFour-Regular, `sgn` Nm Four; Preferred family "Unnamed"; legacy family "Unnamed"; `fileName` `Unnamed Regular.xfo` |
| 882 | gated `trynames` `info_set` `openTypeNamePreferredFamilyName = Nm Four`; look | read back equal, no other reading changes; tab and FONTS unchanged | as predicted; tab "Unnamed Regular", FONTS "Unnamed (one font)" (the display before the write taken from 878, not looked at again) |
| 883 | File > New Font; look | two lines, "Nm Four" and "Unnamed" (the Preferred family as the grouping key) | wrong: FONTS "**Unnamed (2 fonts)**", both tabs "Unnamed Regular": the Preferred family is not the key |
| 884 | the new font closed unsaved; look; `trynames` state | FONTS "Nm Four (one font)"; Preferred family "Nm Four", legacy family "Unnamed" | as predicted; tab "Unnamed Regular" |
| 885 | gated `legacy_set` `familyName = Nm Four` | read back equal, no other reading changes | as predicted |
| 886 | File > New Font; look | two lines | as predicted: "**Nm Four (one font)**" and "Unnamed (one font)": the legacy family takes part in the grouping (not proven to be the only key: 323 grouped two fonts with different legacy families and the same `tfn`); both tabs "Unnamed Regular" |
| 887 | the new font closed unsaved; `trynames` state | legacy family "Unnamed" again (as 872) | legacy family "Nm Four". **Void:** every family name read "Nm Four", so a kept value and a rebuilt one look the same |
| 888 | the listener restarted, nothing else touched; state | legacy family "Unnamed" | legacy family "Nm Four". **Void**, for the same reason |
| 889 | gated `legacy_set` `familyName = Nm Five` | read back equal, no other reading changes | as predicted; `tfn` and the Preferred family stay "Nm Four" |
| 890 | the listener restarted, nothing else touched; state | legacy family "Nm Four" again | wrong: "**Nm Five**": a restart does not rewrite it |
| 891 | File > New Font; look | two lines, labelled "Nm Four" and "Unnamed" | as predicted: the label is `tfn`, not the legacy family |
| 892 | the new font closed unsaved; look; state | legacy family "Nm Five" | as predicted; FONTS "Nm Four (one font)", tab "Unnamed Regular" |
| 893 | the listener restarted after the close (the order of 872); state | legacy family "Nm Five" | as predicted; every name unchanged. What reverted the legacy family in 872 stays open ([WATCH-POINTS.md](WATCH-POINTS.md)) |
| 894 | `/debug/tryfont?stage=construct&go=yes` (font A); gated `legacy_set` `familyName = Nm Six`; File > New Font; look | B "Unnamed" (free name by the legacy family) or "Unnamed1" (by `tfn`); one line if either name matches, else two | B "**Unnamed1 Regular**", the second case; two lines, "Unnamed" and "Unnamed1", which says nothing about the grouping key |
| 895 | B closed; gated `set` `tfn = Nm Seven`; File > New Font; look | B "Unnamed" (the free name follows `tfn`); lines "Nm Seven" and "Unnamed" | B "Unnamed Regular" as predicted; **one** line "Unnamed (2 fonts)" although `tfn` and the legacy family differ (wrong) |
| 896 | B closed; gated `set` `ffn = Nm Seven Regular`; look | tab and FONTS unchanged | as predicted: tab "Unnamed Regular", FONTS "Unnamed (one font)", though `tfn` read "Nm Seven" (open, [WATCH-POINTS.md](WATCH-POINTS.md)) |
| 897 | File > New Font; look | one line (any one name matching) | wrong: two lines, "Nm Seven" and "Unnamed"; A's tab unchanged; "any name" dropped |
| 898 | B closed; gated `legacy_set` `familyName = Unnamed`; File > New Font; look | one line (Full name or legacy family) | wrong: two lines; that rule dropped |
| 899 | B closed; gated `set` `tfn = Nm Eight`; look; File > New Font; look | lag model: "Nm Seven" stays; no lag: "Nm Eight" | "Nm Seven" before and after the add |
| 900 | File > New Font (A, B open); look | A "Nm Eight", three lines | wrong for A: "Nm Seven"; C "Unnamed1 Regular", three lines "Nm Seven", "Unnamed", "Unnamed1" as predicted |
| 901 | C closed; look; File > New Font; look | the close changes nothing; the add shows "Nm Eight" | wrong for the close: A "Nm Eight" at once; the add (D "Unnamed1 Regular") gave three lines "Nm Eight", "Unnamed", "Unnamed1", A unchanged. A close rebuilds from the current `tfn` ([topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k) |
| 902 | on font D (one of two fonts, names written through the API); Font Info on the Names page: only the Full name typed (`Nm Nine Regular`), OK; look | the tab follows; the FONTS line keeps "Unnamed1" | as predicted: the tab read "Nm Nine Regular", FONTS unchanged |
| 903 | Font Info: only the Family typed (`Unnamed`, the `tfn` of another font), OK; look | one grouped line "Unnamed (2 fonts)" at once | as predicted; D's tab unchanged (the Full name was not edited): a Font Info edit refreshes the FONTS panel at once, and 323 is explained |
| 904 | the other fonts closed (no question); D alone; `trynames` state | package `tfn` "Unnamed", `ffn` "Nm Nine Regular", `psn`, `sgn` unchanged; the legacy family "Unnamed" if Font Info writes it | as predicted except the legacy family: **"Unnamed1"**, unchanged; a Font Info edit writes only the package names that were typed |
| 905a | listener 0.144; gated `trynames?stage=title&go=yes` (`title_name(True)`) on D before any write | "Nm Nine Regular"; no change, no crash | as predicted; `elidedName` "Regular" before and after |
| 905b | gated `set` `ffn = Nm Ten Regular`; look | read back equal; tab and FONTS unchanged | as predicted |
| 905c | gated `title` again; look | "Nm Ten Regular" (computed live); the tab unchanged | as predicted: `title_name` follows the package, the tab does not |
| 906 | Font Info opened (header "Nm Ten Regular", Full name the same), OK with no edit; `trynames` state | the tab changes to "Nm Ten Regular", or stays | the tab stayed "Nm Nine Regular"; no name changed: an empty OK writes nothing |
| 907 | Font Info: the Full name selected and retyped identically (`Nm Ten Regular`), OK | the tab changes (typing counts as an edit), or stays | stayed: Font Info compares values |
| 907b | (an extra step by the person) Font Info: Full name `Nm Eleven Regular`, OK; `trynames` state | the tab follows; only the package `ffn` changes | the tab "Nm Eleven Regular"; `ffn` "Nm Eleven Regular", every other name unchanged |
| 908 | gated `title&full=no` (the third and last call of the run) | the same text as `full=yes` | as predicted: "Nm Eleven Regular"; nothing changed |
| 909 | gated `set` `ffn = Nm Twelve Regular`; File > New Font (E); a click on D's tab | D's tab stays "Nm Eleven Regular" after each step | as predicted after the write, the add and the click |
| 910 | Font Info: Full name `Nm Thirteen Regular`, OK; reopened (header "Nm Thirteen Regular"); Full name `Nm Twelve Regular`, OK | the tab "Nm Thirteen Regular", then "Nm Twelve Regular" | as predicted both times: typing a different name, then the wanted one, brings a stale tab up to date (`trynames` was refused with two fonts open, so the package was read from Font Info's header) |
| 911 | all fonts closed; File > New Font (F, one font); gated `set` `ffn = Nm Fourteen Regular`; look; close | tab and icon unchanged; no save question | as predicted: tab "Unnamed Regular", icon dark, closed at once with no question |
| 912 | File > New Font (G); gated `set` `ffn = Nm Fifteen Regular`; icon dark; gated `refresh&which=applied`; icon; close | the icon blue after the mark; FontLab asks | as predicted: dark after the write, blue after the mark; closed with "Don't Save" after FontLab asked |
| 913 | listener restarted, no font open; gated `tryfont?stage=construct_named&family=Nm Sixteen&go=yes`; the icon; gated `refresh&which=applied`; the icon; close | tab "Unnamed Regular", FONTS "Unnamed", icon dark, then blue; FontLab asks | as predicted; the dialog read "Save changes to "Nm Sixteen Regular" before closing?" (the package Full name, not the tab); the grid's `.notdef` selection cleared after the mark (not predicted) |
| 914 | listener 0.145 restarted; two fonts from File > New Font (X, Y); gated `construct_named&family=Nm Seventeen&mark=yes&go=yes`; the three icons; X, Y, Z closed in turn | `mark.called` true; only Z blue; only Z asks | as predicted: `CountFonts` 2 → 3, Z first "Unnamed2", names read back equal, `mark.called` true with no error; only Z's icon blue; X and Y closed silently, Z asked "Save changes to "Nm Seventeen Regular" before closing?". Not predicted: the FONTS line for Z stayed "Unnamed2" after two closes ([WATCH-POINTS.md](WATCH-POINTS.md)) |

### CF series: `create_font` live (2026-11-13, FontLab 8.9.5 in Demo mode, listener 0.146 / server 0.60, through Claude Code; one listener run, no font open at the start; no File > Save stage, nothing saved; results in [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k)

| # | Step | Predicted | Result |
|---|---|---|---|
| 915 | `create_font` without a family, no font open; `list_glyphs`; the person reads the tab, FONTS and OUTPUT | fonts 0 → 1, "Unnamed Regular", upm 1000, master `Regular`, `.notdef` only, no mark, notes: unsaved | as predicted; tab "Unnamed Regular", FONTS "Unnamed (one font)", Encoding None, both notes in OUTPUT |
| 916 | `create_font` without a family, 915's font open, same listener run | fonts 1 → 2, "Unnamed1 Regular", a third note (first glyph) | as predicted, with a fourth note not predicted (keep the window in front); tab "Unnamed1 Regular", its own FONTS line, all four notes in OUTPUT |
| 917 | `create_font` `family=GBtest917`, two fonts open | fonts 2 → 3, the four names read back, `mark.called` true, tab and FONTS keep "Unnamed2" | as predicted; legacy family set; five notes; tab "Unnamed2 Regular", FONTS "Unnamed2 (one font)" |
| 918 | the person closes "Unnamed1" (untouched, unmarked) | no question; FONTS may refresh | no question; FONTS rebuilt: "GBtest917 (one font)" listed first, then "Unnamed" (unlike 896, 914); GBtest917's grid read 0/1, `.notdef` not highlighted (second sighting of 913) |
| 919 | the person closes GBtest917 (tab "Unnamed2 Regular", marked) | FontLab asks; Don't Save | as predicted: "Save changes to "GBtest917 Regular" before closing?" (the live Full name), Don't Save / Cancel / OK; the remaining font's grid read 1/1 |
| 920 | the person closes "Unnamed" (untouched, unmarked); `fontlab_status` | no question; `font_open` false | as predicted |
| 921 | `create_font` `family=GBtest921`, no font open; the person: Font Info > Names, Build Names, OK | tab "Unnamed Regular" and FONTS "Unnamed" unchanged (identical values) | as predicted: Build Names changed no field; nothing refreshed. The grid read 1/1 with the mark (against 913, 918). `font_changed` named the closed GBtest917 as the previous font |
| 922 | the same font; the person retypes the identical Family name, OK | unchanged (cf. 907) | as predicted: nothing refreshed. No single Font Info step with unchanged values refreshes the display; the user chose a plain note with no workaround (2026-11-13) |
| 923 | listener 0.147 restarted, Claude Desktop fully restarted; `fontlab_status` | 0.147 / 0.61, no font | as predicted; the `create_font` description in Claude Code was still the 0.60 text (a stale copy, CLAUDE.md) |
| 924 | `create_font` `family=GBtest924`, no font open; the person reads OUTPUT | fonts 0 → 1, marked; two notes (short unsaved note, one display note naming "Unnamed"); the instruction holds the OUTPUT panel sentence | as predicted, in the reply and in OUTPUT; the grid read 1/1 with the mark |
| 925 | the person closes GBtest924 | FontLab asks in the live Full name; Don't Save | as predicted: "Save changes to "GBtest924 Regular" before closing?" |
| 926 | use, not a planned test (one run, no prediction): `create_font` unnamed; six glyphs drawn, deleted after six Yes clicks and recreated; `draw_path` into 12 glyphs (up to 4 contours, counters, cubic arcs) and into `.notdef` (3 contours); sidebearings | every write verified | all verified; `.notdef` got its layer from `draw_path` (`layer_created`); the delete that left only `.notdef` was unmarked (`save_question_note`, as known); `C.crack` re-read `verified` with FontLab's ink box |

### PK series: the package of a glyph, and a new font's first glyph with other fonts open (2026-11-13, FontLab 8.9.5 in Demo mode, listener 0.147–0.150 / server 0.61–0.62, through Claude Code; new unsaved fonts only, no File > Save stage, nothing saved; ROADMAP P0.9; results in [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8k)

| # | Step | Predicted | Result |
|---|---|---|---|
| 927 | listener 0.147, one new font; names only: `/debug/classdir` of `fgFont`, `fgGlyph`, `flGlyph` | a member naming a package or `fgId` | `fgFont` and `fgGlyph` are not names of the `fontlab` module; `flGlyph` has `package` ("flObject") and `fgPackage` ("fgFont") |
| 928 | listener 0.148, the same font alone; `/debug/trypackage?name=.notdef&go=yes` | an `flPackage`, not null, `isEqual` the current one, one master `Regular`, counts match, no side effect | as predicted; `fgId` 5 |
| 929 | a second font (File > New Font) in front, its `.notdef` | as 928, `fgId` not 5 | as predicted; `fgId` 8, `wrapper: built` |
| 930 | listener 0.149; 930a the second font's `.notdef` (`fgId` 8); the first font brought to the front; 930b its `.notdef` (`fgId` 5); 930c `stage=cached` | the cached wrapper of the second font: `fgId` 8, `isEqual` **false** | `fgId` 8 as predicted; **wrong: `isEqual` true** for packages of `fgId` 5 and 8. Both wrappers passed the key and `isValid` checks; no side effect |
| 931 | `create_glyph pk931a` in the first font (2 fonts open), then `stage=cached` | `isEqual` false once the glyph counts differ | `layer_note`, no layer, unmarked (as 691a); **`isEqual` still true** for `fgId` 5 (2 glyphs) against 8 (1 glyph): it does not compare contents |
| 932 | listener 0.150 / server 0.62 after a restart (one font, "Unnamed"); `create_font` | created, in front through `fgId`, no double-click note | as predicted: "Unnamed1 Regular", 2 fonts, three notes |
| 933 | `create_glyph pk933a` in Unnamed1 | `layer_created` `Regular`, `package master`, marked | as predicted; synced |
| 934 | `draw_path` into `pk933a` | `verified` | as predicted; `nodes_match`, synced, marked |
| 935 | "Unnamed" brought to the front (how it was made is not known); `create_glyph pk935a` | as 933 | as predicted |
| 936 | both fonts closed with Don't Save; `create_font`, then `create_glyph pk936a` with one font open | unchanged from 620 | as predicted |

### DL series: `delete_glyph` after a read or write of a Power Brush glyph (2026-11-14, FontLab 8.9.5 in Demo mode, listener 0.150 / server 0.62, through Claude Code; one new unsaved font, one master, prefix `dl1_`; no File > Save stage, nothing saved; results in [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l)

| # | Step | Predicted | Result |
|---|---|---|---|
| 937 | `create_glyph` `dl1_xa`, `dl1_xb`, `dl1_xc`, before any brush glyph exists | created, layers, synced | as predicted |
| 938 | the person: Create Blank `dl1_a`, one Power Brush stroke, default brush (50), tab open; outline | `verified`, equal to the panel | as predicted: 46 nodes, 10 with fractions, 78 / 127 / 500, brush element |
| 939 | `delete_glyph dl1_xa`, Yes | deleted, marked | as predicted; `via_glyph` `dl1_xb` |
| 940 | outline `dl1_a` | identical to 938 | as predicted |
| 941 | the Elements panel of `dl1_a` | brush element | as predicted |
| 942 | `dl1_a`'s tab found closed; the person: Create Blank `dl1_b`, one stroke, tab open; outline | `verified` | as predicted: 59 nodes, 12 with fractions, 103 / 55 / 500 |
| 943 | `set_glyph_width dl1_b 510` | modern, synced | as predicted |
| 944 | `delete_glyph dl1_xb`, Yes | deleted | as predicted; `via_glyph` `dl1_xc` |
| 945 | outline `dl1_b` | identical nodes, 103 / 65 / 510 | as predicted |
| 946 | the Elements panel of `dl1_b` | brush element | as predicted |
| 947 | the person: Create Blank `dl1_c`, one stroke, its tab active, `dl1_b`'s tab still open behind it; outline | `verified` | as predicted: 73 nodes, 18 with fractions, 119 / 117 / 500 |
| 948 | `set_glyph_sidebearings dl1_c` 129 / 117 | verified, synced | as predicted; offset (10, 0) on the element |
| 949 | `delete_glyph dl1_xc`, Yes | deleted | as predicted; `via_glyph` `dl1_a` |
| 950 | outline `dl1_c` | identical, moved by 10 | as predicted; brush element kept |
| 951 | outline `dl1_a` | identical to 940 | **wrong: flattened**: 46 nodes, all whole units, `is_composite` false |
| 952 | outline `dl1_b` | identical to 945 | **wrong: flattened** the same way; 103 / 65 / 510 kept |
| 953 | the person closed all tabs, then opened `dl1_b`; its Elements panel | brush element | **wrong:** a plain contour, "59/21"; 951 and 952 had read the flattening before any tab was touched |

### ED series: the editing API by name (2026-11-14, FontLab 8.9.5 in Demo mode, listener 0.150, through Claude Code; `/debug/classdir`, names and docstrings only; the open font unchanged)

| # | Step | Predicted | Result |
|---|---|---|---|
| 954–958 | `classdir` of `flLayer`, `flShape`, `flShapeData`, `flContour`, `flNode` | members for node, contour and shape edits | as predicted; lists in the topic file |
| 959–963 | `members=` 12 candidates per class | docstrings with signatures | as predicted, 60 docstrings |

### ED2 series: `/debug/tryedit` live (2026-11-14, FontLab 8.9.5 in Demo mode, listener 0.151 / server 0.62, through Claude Code; a font made by `create_font` with no other font open, one master, prefix `edp1_`; no File > Save stage, nothing saved; results in [topics/geometry.md](topics/geometry.md) "Editing existing outlines")

| # | Step | Predicted | Result |
|---|---|---|---|
| 964–966 | `create_font`; `create_glyph edp1_a`; `draw_path`, squares (100–500) and (200–400) | verified | as predicted |
| 967 | `movenode` contour 0 node 2 (500, 500) by (+50, −50) | (550, 450), nothing else changed, synced, marked | as predicted |
| 968 | `get_glyph_outline edp1_a` | `verified` | **wrong:** `unverified`; the sidebearings read 100 / −500 (should be −550); `inkBox()` current |
| 969 | the person opened `edp1_a` | the moved corner; 100 / −550 | as predicted, in the grid bar and the editor panel |
| 970 | `get_glyph_sidebearings edp1_a` | — | 100 / −550: caught up |
| 971–973 | `edp1_b`, one square; `addcontour` | the square (600–650) last, synced, marked | as predicted |
| 974 | outline | sidebearings stale, as 968 | as predicted: −500 (should be −650); `inkBox()` top 650, current |
| 975–976 | `edp1_c`, two squares; `removecontour` 0 | the inner square alone | as predicted |
| 977 | outline | sidebearings stale | **wrong:** 200 / −400, current, `verified` |
| 978–979 | `edp1_d`, one square; `replace` | the triangle (100, 0), (300, 0), (200, 300), synced, marked | as predicted |
| 980 | outline | not predicted | stale: −500 (should be −300); `inkBox()` current |
| 981 | the person single-clicked `edp1_d` in the grid | — | the grid bar showed 100 / 0 / −300 |
| 982–983 | `get_glyph_sidebearings` `edp1_d`, `edp1_b` (never clicked) | — | 100 / −300 and 100 / −650: both caught up |

### B1 series: refresh calls by name (2026-11-14, listener 0.151, `/debug/classdir`, names and docstrings only; nothing called)

| # | Step | Predicted | Result |
|---|---|---|---|
| 984–988 | `members=` of `flLayer`, `flShape`, `flShapeData`, `flContour`, `flGlyph`: `update`, `changed`, `resetInkBox` and the like | docstrings | bare signatures only (`update()`, `changed()`, `resetInkBox()`); `resetMetricsLeft/Right/Width()` left out of B2 |

### B2 series: one refresh call after an edit (2026-11-14, FontLab 8.9.5 in Demo mode, listener 0.152 / server 0.62, through Claude Code; the ED2 font, one font open; prefix `edp2_`; no File > Save stage, nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 989 | `create_glyph` and `draw_path` `edp2_a`–`edp2_h`, one square (100–500) each | verified | as predicted |
| 990–997 | `movenode` contour 0 node 2 by (+50, −50), `refresh=` one member each: `contour.update`, `shape.update`, `shapedata.update`, **`layer.update`**, `glyph.update`, `layer.changed`, `shape.changed`, **`layer.resetinkbox`** | stale before the refresh (RSB −500, expected −550); after it: open | stale before in all 8; current after only `layer.update` (993) and `layer.resetinkbox` (997); every edit exact, no node moved by a refresh, no error, synced, marked |
| 998–1000 | sidebearings of `edp2_d`, `edp2_h`, and `edp2_a` (control) | 100 / −550, 100 / −550, 100 / −500 | as predicted: the refresh acts on its own layer only |

**Not reproduced on 2026-11-15** (MN 1003–1006): neither `layer.update` nor `layer.resetinkbox` refreshed the sidebearings; 993 and 997 are no longer counted as facts.

### MN series: `move_nodes` live (2026-11-15, FontLab 8.9.5 in Demo mode, listener 0.153 / server 0.63, through Claude Code; `create_font` without a family, one font open, `Unnamed`; nothing clicked in FontLab unless said)

| # | Step | Predicted | Result |
|---|---|---|---|
| setup | `create_glyph mna1`, `draw_path` square (100,0)–(300,200), `set_glyph_width` 400, `get_glyph_outline` | verified, 100 / 100 | as predicted |
| 1001 | `move_nodes mna1` node 1 (300,0) → (350,0) | verified, right 50 | **wrong:** nodes exact, synced, marked, but FontLab's right read 100 (stale), so `verified: false`; `get_glyph_sidebearings` afterwards: still 100 |
| 1002 | the same call again | refused, nothing moved | as predicted; the message printed `(350, -0)` (fixed in 0.154) |
| 1003 | probe `edpm1` (same square, width 400): `movenode` node 1 by (+50, 0), `refresh=layer.resetinkbox` | stale before, current after (997) | **wrong:** right 100 before and after (expected 50) |
| 1004 | probe `edpm2`: by (+50, −50), `resetinkbox` | as 1003 if y does not matter | stale before and after |
| 1005 | probe `edpm3`: by (+50, 0), `refresh=layer.update` | current after (993) | **wrong:** stale before and after |
| 1006 | probe `edpm4`, width never set (advance 0): by (+50, 0), `resetinkbox` | current after, if the width mattered | stale: −300 before and after (expected −350) |
| 1007 | sidebearings of `mna1`, `edpm1`, `edpm4` | — | `mna1` and `edpm1` current (right 50), `edpm4` still −300 minutes later: time alone does not refresh |
| 1008–1010 | on another glyph `edpm5`: `create_glyph`, `draw_path`, `set_glyph_width` 400; `edpm4` read after each | −350 if that write refreshes | −300 each time |
| 1011 | `get_glyph_outline edpm4`, then the raw `inkBox()` | — | still stale; `inkBox()` right 300 while the node is at 350: the ink box lags too (ED2 968–980 checked it vertically only) |
| 1012 | the person clicked FontLab's title bar | −350 if a focus event refreshes | −300, `inkBox()` right 300 |
| 1013 | the person single-clicked `edpm5` in the grid | −350 (as 982–983) | −300: not reproduced; in 981 the clicked glyph was itself an edited one |
| 1014 | `inkBox()` and sidebearings of all five moved glyphs | — | `mna1`, `edpm1` current; `edpm2`–`edpm4` stale; what refreshed the first two is not isolated |
| 1015 | the person restarted the listener (empty wrapper cache); `edpm2`–`edpm4` read through new `flGlyph` wrappers | current, if the cached wrapper were the cause | stale: the cache is not the cause |

Consequence: listener 0.154 / server 0.64 confirm a move by the re-read nodes and compute the sidebearings from them ([CHANGELOG.md](CHANGELOG.md)).

### MN round 2: `move_nodes` of 0.154 / 0.64 live (2026-11-15, FontLab 8.9.5 in Demo mode, through Claude Code; `create_font` without a family, one font open, `Unnamed`; prefix `mnb`; every glyph a tool-drawn outline with width set; no File > Save stage, nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| setup | `fontlab_status` | 0.154 / 0.64 | as predicted, no font open (the restart had been done) |
| 1016 | `mnb1` square (100,0)–(300,200), width 400: node 1 (300,0) → (350,0) | `verified`, computed right 50, FontLab's 100, `fontlab_sidebearings_current` false, `person_note` | as predicted |
| 1017 | `mnb2` (same square): node 2 (300,200) → (350,250) and node 3 (100,200) → (100,250) in one call | `verified`, 100 / 50, ink width 250 | as predicted; FontLab's 100 / 100 |
| 1018 | `mnb3`, the tool's bulging square (cubic, nodes 0–5), width 600: control point node 2 (500,100) → (550,100) | `verified`, right ≈ 105.32 (cubic extent ≈ 494.68) | as predicted: right 105.3305, extent 494.6695, equal to a separate computation; FontLab's right 125 |
| 1019 | `mnb4`, the tool's circle (four smooth nodes), width 400: smooth node 0 (400,200) → (420,200) alone | refused, nothing moved | as predicted; the message names the node and its position after the move |
| 1020 | the same node with its handles, nodes 1 and 11, all by +20 in x | `verified`, right −20, ink width 420 | as predicted |
| 1021a | `create_glyph mnb5`; the person opened it and added `mnb1` with Glyph > Add Component…; `get_glyph_outline mnb5` | `verified` | **wrong:** `unverified`, `source_in_step` false: the component showed `mnb1`'s moved nodes (x to 350), compared with FontLab's still stale box of `mnb1` (x to 300); its `agent_instruction` asked to tell the person the glyph was out of step (a false alarm) |
| 1021 | `move_nodes mnb5` node 1 (350,0) → (360,0) | refused (component), nothing moved | as predicted ("isComponent reads True") |
| 1021b | `get_glyph_outline mnb1`, then `mnb5` again | — | `mnb1` `verified`, FontLab's right now 50 (caught up); `mnb5` `verified`, `source_in_step` true |
| 1021c | `get_glyph_sidebearings mnb2` (never clicked or used) | — | 100 / 100, still stale (true right 50): only the component's source caught up; whether Add Component or the read in 1021a refreshed it is not isolated |
| 1022a | `mnb6` square, width 400; the person drew a rectangle with the Rectangle tool beside it | a second shape | **one shape with two contours** (the Elements panel's two rows are contours); FontLab's right 36. The two-shapes refusal stays untested |
| 1022 | `mnb6` contour 1 node 1 (364,246) → (380,246) | accepted (one plain shape), `verified`, right 20, FontLab's 36 | as predicted; the person's screenshot: the outline repainted at once, the fill and the bar (36) did not |
| 1023 | the person chose Edit > Undo once, `mnb6` in front | the GUI rectangle undone, the move not on the undo list | **wrong:** the nodes read back unchanged (380 still), but FontLab's sidebearings, fill and bar caught up (right 20, `verified`); the Edit menu then read "Undo Add Rectangle" and "Redo Glyphbridge Move Nodes": the undo entry comes from the mark (`notifyChangesApplied` with the title "Glyphbridge move nodes", shown title-cased), and undoing it did not move the node back. A second Undo was skipped: it would undo the GUI rectangle only |
| 1024 | the person closed the font with the X at the left of its title | the save question; Cancel | as predicted; not isolated, since the GUI rectangle is a change of its own |

| 1025 | server 0.65 after a full Claude Desktop restart (`fontlab_status` 0.154 / 0.65; the client still showed the 0.64 tool description): in the same font, `mnc1` square, width 400, node 1 (300,0) → (350,0) | `verified`, `undo_note`, no `display_note`, the instruction ending with "Tell the person undo_note once per conversation." | as predicted; the lag note came first, right 50 against FontLab's 100 |

`finish_changes`: 22 changes, the writes of this round (1 font, 6 creates, 5 drawings, 5 widths, 5 moves), one reminder; `fontlab_status` at the start had shown 3 from an earlier session.

### PC series: placing a component through the API (2026-11-17, FontLab 8.9.5 in Demo mode, listener 0.155–0.168 / server 0.65, through Claude Code; `create_font` without a family, one font open, `Unnamed`; `cpp1src` a tool-drawn triangle (100,0) (300,0) (200,300), `cpp1base` a rectangle (0,0)–(400,300), `cpp1tgt` and `cpp1tgt2` empty with their layers, all widths 0 (`cpp2tgt` added in 1045); probe `/debug/trycomponent`, one call per request; no File > Save stage, nothing saved; results in [topics/reading.md](topics/reading.md) "Components: placing one through the API")

Names only first (`/debug/classdir`, `/debug/moddir`, nothing called): `flLayer.addComponent(flComponent)`, and `flComponent` is no public name; `bool setGlyphComponents(QList<GlyphComponent> result, double width, flPackage package, bool colorize, uint flags)`; `GlyphComponent(string name)` and `(uint id, QTransform tx, double w, bool ua)`; `flShape(flShapeData)` among `flShape`'s constructors.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1026 | `glyphcomponents`: `GlyphComponent("cpp1src")`, transform (1,0,0,1,100,200) read back, then `cpp1tgt.setGlyphComponents([gc], 0.0, package, False, 0)` | a component at (100,200) | **IndexError: Unexpected SeqBase<T> length.**; nothing changed; `name_id` read 5113 |
| 1027 | `shapedata`: `flShape(<cpp1src's shape>.shapeData)` into `cpp1tgt2` | a shared shape | **TypeError: Error creating object of type flShapeBuilder**; `addShape` not called; a dead form already recorded in [topics/geometry.md](topics/geometry.md) and re-run by mistake |
| 1028 | the person: `cpp1tgt` open, Glyph > Add Component… `cpp1src` | one component | as predicted: `get_glyph_outline` `verified`, identity, `source_in_step` true, `is_composite` true; Layers panel "1 component", Elements badge 2 |
| 1029 | `readcomponents` on `cpp1tgt`: `layer.components` | a list of (name, transform) | **wrong:** a real, empty list; `componentsCount` 0 ([WATCH-POINTS.md](WATCH-POINTS.md)); the component's shape data is an `flShapeData` |
| 1030 | `generate`: `package.generateGlyph("cpp1src", "Regular", FontMetrics(package, "Regular"), False)` | (list, width), nothing changed | **a list of one item**, no width; nothing changed (0.157 did not describe the item) |
| 1032 | the same, 0.158 | as 1030 | as 1030; the item is a `GlyphComponent`, `name_id` 5113, identity, `width_scale` 1.0, `use_anchors` false |
| 1031 | `setgenerated`: that list, as is, `setGlyphComponents(list, 0.0, package, False, 0)` | a component, or the 1026 error | the 1026 error word for word; nothing changed |
| 1033 | the same with 4 arguments (no `0`) | — | **TypeError: argument type must be Int!**; nothing changed |
| 1034 | 4 arguments, the package's `fgId` (5) third | — | **Wrong argument type. flPackage expected.**; nothing changed |
| 1035 | 4 arguments, `0` fourth | — | **argument type must be Boolean!**; nothing changed |
| 1036 | 4 arguments, the width as the whole number `0` | — | **must be Int!**, as 1033; nothing changed. FontLab's archived FontLab 7 reference: `bool setGlyphComponents(QList result, double width, flPackage package, bool colorize)` |
| 1037 | 4 arguments, `[5113]` as the list | — | **Wrong argument type. GlyphComponent expected.**; nothing changed. Every argument of the 4-argument form is now confirmed; its "must be Int" most likely asks for the fifth (`uint flags`); the 5-argument "SeqBase" is unexplained |
| 1038 | `auto&step=read` on `cpp1tgt2` | recipe empty, `autoLayer` false | as predicted |
| 1039 | `step=setrecipe`: `layer.recipe = "cpp1src"` | read back, nothing else | as predicted |
| 1040 | `step=build`: `layer.buildAuto()` | a component, or False | **False**, nothing changed (`autoLayer` off) |
| 1041a | `step=setauto`: `layer.autoLayer = True` | read back, nothing else | as predicted; nothing built by itself |
| 1041b | `step=build` again | a component | **True: one component of `cpp1src`, identity**; width 0, `cpp1src` and the glyph count unchanged; synced, marked (`glyph_has_changes` true); `get_glyph_outline` `verified`, `source_in_step` true |
| 1041c | the person's screenshots | — | grid cell with the triangle and a blue marker; Layers "Regular" with an extra icon and "1 component"; Elements row `cpp1src` without a badge, unselected; the canvas a flat grey fill. Corrected by 1042b: the fill and the small icon before the name are how FontLab shows any unselected component; only the layer icon and the missing badge differ from 1028 |
| 1042 | listener 0.166, `step=unauto` on `cpp1tgt2`: `layer.autoLayer = False` | read back, the component kept | as predicted: `autoLayer` false, the same component (source, layer, identity), the same outline, recipe still `cpp1src`, width 0, glyph count 5; `component_normal` true; synced, marked (`glyph_has_changes` true) |
| 1042a | the person's screenshot, the component selected | as 1028 | as predicted: no layer icon, "1 component", badge 3 (`cpp1src` now used by two glyphs), outline with a selection box, element bar X 0, Y 0, 100 %, 0° |
| 1042b | the person's screenshot after a click beside it (Contour tool) | — | a flat grey fill, badge 3, no layer icon: the unselected look of 1041c |

Before 1043, names only (`/debug/classdir?name=flShape`, nothing called): `transform` (docstring "transform"), `applyTransform([QTransform transform])`, `fl_transform` ("flTransform"); no `setTransform`, `translate` or `move`. Listener 0.167 restarted before 1043 (one `/debug/trycomponent` call per request, 6 per run).

| # | Step | Predicted | Result |
|---|---|---|---|
| 1043 | listener 0.167, `stage=offset&how=assign&dx=100&dy=50` on `cpp1tgt2` (one component of `cpp1src` at identity, `autoLayer` false): `shape.transform = QTransform(1, 0, 0, 1, 100, 50)` | matrix (…, 100, 50), ink box 200–400 × 50–350, the source and width unchanged, marked; or an error / no change | **as predicted:** no error; matrix (1, 0, 0, 1, 100, 50), source and layer unchanged; the element's ink box 100–300 × 0–300 → 200–400 × 50–350; the raw nodes of `getContours()` unchanged (the source's own); width 0, 5 glyphs, recipe `cpp1src`, `autoLayer` false, `cpp1src` unchanged; `offset_placed` true; synced, marked (`glyph_has_changes` true). The probe's own after-read gave FontLab's LSB as 100 |
| 1044 | `get_glyph_outline cpp1tgt2` | `verified`, `source_in_step` true | as predicted: nodes (200,50) (400,50) (300,350), raw (100,0) (300,0) (200,300), "offset (100, 50)"; FontLab's LSB 200 and ink box agree |
| 1043a | the person's screenshot, the component selected (Element tool) | X 100, Y 50, 100 %, 0° | as predicted: element bar X 100, Y 50, 100 % / 100 %, 0° / 0°; Elements `cpp1src` Δ=(100,50), badge 3; Layers "Regular · 1 component", no layer icon; glyph bar LSB 200, RSB −400, width 0; outline at 200–400 × 50–350; the tab read "cpp1tgt2 •" |
| 1045 | `create_glyph cpp2tgt` | created with its layer | as predicted: `layer_created` "Regular", synced, marked, 5 → 6 glyphs |
| 1046 | `stage=auto&step=read` on `cpp2tgt` | recipe `""`, `autoLayer` false | as predicted; nothing changed |
| 1047 | `step=setrecipe&recipe=cpp1src%2Bcpp1base` | read back | as predicted: `cpp1src+cpp1base`, nothing else changed |
| 1048 | `step=setauto` | `autoLayer` true, nothing built | as predicted |
| 1049 | `step=build&recipe=cpp1src%2Bcpp1base` | two components at identity, width 0; or FontLab offsets the second | **the second outcome:** returned True; `cpp1src` at identity, then **`cpp1base` at (−200, 0)**; **width 0 → 500**; the sources and the glyph count unchanged; `placed` false, `side_effect_detected` true (the width), so synced, NOT marked |
| 1050 | `step=unauto` | both kept, marked | as predicted: `autoLayer` false, both components with the same matrices, recipe kept, width 500; `component_normal` true; synced, marked. `get_glyph_outline`: `verified`, triangle 100–300, rectangle −200 to 200, ink −200 to 300 × 0–300, LSB −200, advance 500, `source_in_step` true for both. `finish_changes`: 1 change (the create; the probe is not counted), one reminder |
| 1050a | the person's screenshots: grid, then each component and both selected | "2 components", no layer icon, width 500, Δ=(-200,0) | as predicted: the grid cell shows both, tooltip width 500; Layers "Regular · 2 components", no layer icon; Elements `cpp1base` Δ=(-200,0) badge 2, `cpp1src` badge 4; element bar X −200, Y 0 for `cpp1base`, X 0, Y 0 for `cpp1src`, 100 %, 0°; glyph bar LSB −200, width 500, RSB 200; the advance line at 500 |
| 1051 | listener 0.167 restarted (calls counted anew); `create_glyph cpp3tgt` | created with its layer | as predicted: layer "Regular", synced, marked, 6 → 7 glyphs |
| 1052 | `stage=auto&step=setrecipe&recipe=cpp1src` on `cpp3tgt` | read back | as predicted |
| 1053 | `step=setauto` | `autoLayer` true, nothing built | as predicted |
| 1054 | `step=build&recipe=cpp1src` | one component at identity, width 0 | as 1041b: one component of `cpp1src`, identity, width 0, `component_placed` true, synced, marked (the plan's "not yet marked" was an error in the prediction table; 1041b was marked too) |
| 1055 | `step=killauto`: ONE `layer.killAuto()` | `autoLayer` false, the component kept; or decomposed or removed | **neither:** returned None; `autoLayer` still true, recipe `cpp1src`, the component, outline, width and glyph count unchanged; `component_normal` false (`autoLayer` did not change); not marked |
| 1055a | the person's screenshots of `cpp3tgt` (Element tool: a click inside, a click outside, a drag selection) | as 1041c | as predicted: the layer icon after "Regular", "1 component", `cpp1src` with a lock and no badge; glyph bar 100 / −300 / 0. Seen besides: a click does not select the component, a drag selection draws a blue outline around it, and the element bar shows only the name, no X / Y / scale / angle fields |
| 1056 | the person, in `cpp1src`: the top node (200, 300) set to Y 350 (Contour tool) | — | the bar read X 200, Y 350; `cpp1src` badge 4 |
| 1057 | `get_glyph_outline cpp1tgt2` (recipe `cpp1src`, `autoLayer` false, offset (100, 50)); `cpp1src` read too | offset kept, top node (300, 400) | **as predicted:** `verified`, matrix (…, 100, 50), nodes (200,50) (400,50) (300,400), raw top (200,350), FontLab's LSB 200 and ink box 50–400 agree; `cpp1src` (100,0) (300,0) (200,350) `verified`. So the leftover recipe was not re-applied by a GUI edit of the source, and the component followed it |
| 1058 | listener 0.168 restarted; `stage=auto&step=clearrecipe` on `cpp1tgt2` (one component at (100, 50), recipe `cpp1src`, `autoLayer` false): `layer.recipe = ""` | the recipe reads `""`, everything else unchanged, marked | **as predicted:** recipe `cpp1src` → `""`; the component (source, layer, matrix (…, 100, 50)), outline, width 0, 7 glyphs and `autoLayer` false unchanged; `recipe_cleared` true; synced, marked |
| 1059 | `clearrecipe` on `cpp2tgt` | as 1058, both matrices and width 500 kept | **refused, nothing written:** the layer no longer held components. `get_glyph_outline`: two plain contours (`is_component` false, no source), the second still at (−200, 0), the triangle's top at (200, 300), the old source, not 350 (1056); width 500, `verified` as an outline. `cpp1tgt`, `cpp1tgt2`, `cpp3tgt` still components of `cpp1src`, each with the edited top (350) |
| 1059a | the person's screenshots of the steps after 1056 (`cpp1src`, the Font window, `cpp1tgt2`); `cpp2tgt` not opened after 1050a | — | the `cpp1tgt` and `cpp1tgt2` cells carry the grey marker of a glyph with a component, `cpp3tgt` a blue one, `cpp2tgt` none (it had one in 1050a); `cpp1src` badge 4 (three users). So `cpp2tgt` changed between the "Current state" screenshot before 1051 (still "2 components") and 1056, with no GUI action on it |
| 1060–1065 | **R1:** `create_glyph cpp4tgt`; `setrecipe cpp1src%2Bcpp1base`, `setauto`, `build`, `unauto`; read | as 1045–1050 | as predicted: `cpp1base` at (−200, 0), width 0 → 500 (build synced, unmarked), both kept by `unauto` (marked); two components, `verified` |
| 1066 | `create_glyph cpp4x`, then read `cpp4tgt` | contours if `create_glyph` is the trigger | **still two components**: not reproduced |
| 1067–1075 | **R2,** listener restarted: `create_glyph cpp5tgt`; on it `setrecipe cpp1src`, `setauto`, `build`, `killauto`, each followed by a read of `cpp4tgt` | contours after the step that triggers it | **never:** `cpp4tgt` two components after every step; `build` placed and marked one component; `killAuto()` returned None and changed nothing read again (second run). `finish_changes`: 4 changes |
| 1076 | **R3:** the person opened `cpp4tgt`, selected both components (Element tool, click and Shift+click) and left the tab active | "2 components", both selected | as predicted; `cpp1src` badge 6 (five users) |
| 1077–1078 | `create_glyph cpp6x` (10 → 11), then read `cpp4tgt` | contours if the open, selected tab matters | **still two components**: not reproduced |
| 1078a | the person's screenshot of the same tab, nothing touched | as 1076 | as predicted. `finish_changes`: 1 change |

### AC series: `add_component` live (2026-11-17, FontLab 8.9.5 in Demo mode, listener 0.169 / server 0.66, then listener 0.170, through Claude Code; the PC test font `Unnamed` (source `cpp1src`, top node at (200, 350) since 1056), then new fonts `Unnamed1`, `Unnamed2`; one run each; nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1079 | `fontlab_status` 0.66 / 0.169; `create_glyph cpp7tgt` | created with its layer | as predicted, 11 → 12 glyphs |
| 1080 | `add_component(cpp7tgt, cpp1src, 0, 0)` | placed, verified, marked | as predicted; width 0 |
| 1081 | `get_glyph_outline cpp7tgt` | one component at identity, `verified` | as predicted: nodes (100,0) (300,0) (200,350); FontLab's LSB 100 and ink box 0–350 agree |
| 1081a | the person's screenshot, the component selected | "1 component", no layer icon, badge 7, X 0, Y 0 | as predicted; OUTPUT "component cpp7tgt: cpp1src at (0, 0) (verified)" |
| 1082–1084 | `create_glyph cpp8tgt`; `add_component(cpp8tgt, cpp1src, 120, 40)`; read | placed at (120, 40), drawn 220–420 × 40–390 | as predicted: matrix (…, 120, 40), nodes (220,40) (420,40) (320,390), FontLab's LSB 220 agrees |
| 1084a | the person's screenshot | Δ=(120,40), badge 8, X 120, Y 40 | as predicted; glyph bar LSB 220, RSB −420 |
| 1085–1089 | refusals: `cpp8tgt` again (not empty); source `cpp7tgt` (holds a component); target `cppzz` (missing); source `cppnone` (missing); `cpp4x` as its own component | each refused, nothing changed | as predicted; 1089 refused by the server before sending; re-read: `cpp8tgt` (120, 40), `cpp7tgt` (0, 0), `cpp4x` empty; the OUTPUT panel logged the four the listener saw as "NOT DONE component …" |
| 1090 | the person, in `cpp8tgt`: Edit menu | "Undo Glyphbridge Add Component" | **wrong:** Undo and Redo greyed out, no Glyphbridge entry (unlike `move_nodes`, 1023); nothing to choose |
| 1091 | the person: File > New Font (`Unnamed1`); `fontlab_status` | 2 fonts, Unnamed1 in front | as predicted; 4 changes counted, the refusals not |
| 1092–1094 | the person clicked the Unnamed tab; `create_glyph cpp9tgt`; `add_component(cpp9tgt, cpp1src, 50, 0)`; read | placed in Unnamed Regular, every reply naming it with 2 fonts open | as predicted: nodes (150,0) (350,0) (250,350), `verified` |
| 1095 | the person clicked the Unnamed1 tab; `list_glyphs` | `.notdef` only | as predicted: 1 glyph |
| 1096 | listener 0.170 restarted; `fontlab_status` | 0.66 / 0.170, Unnamed1 in front | as predicted |
| 1097 | `/debug/markswitch?on=0&go=yes`; in Unnamed1 `create_glyph cpq1src`, `draw_polygon` (100,0) (300,0) (200,300), `create_glyph cpq1tgt` | verified, not marked | as predicted: each reply "the changed mark is switched off in the listener", with `save_question_note` |
| 1098 | `markswitch?on=1&go=yes`; `add_component(cpq1tgt, cpq1src)` | placed, marked | as predicted |
| 1099 | the person closed Unnamed1 (X at the left of its title) | the save question | **as predicted:** "Save changes to "Unnamed1 Regular" before closing? If you don't save, your changes will be lost." (Don't Save, Cancel, OK); Cancel |
| 1100 | the person: File > New Font (`Unnamed2`, 3 fonts); mark off; `create_glyph cpq2src`, the same triangle, `create_glyph cpq2tgt`; mark on; no `add_component` | not marked | as predicted |
| 1101 | the person closed Unnamed2 | no question (control) | **as predicted:** it closed without asking. So `add_component`'s mark alone brought the question in 1099. `finish_changes`: 13 changes, one reminder |

### PC2 series: several components in one glyph (2026-11-17, FontLab 8.9.5 in Demo mode, listener 0.171 / server 0.67, through Claude Code; `create_font` without a family, one font open, `Unnamed`; `cpp1src` the triangle (100,0) (300,0) (200,300), `cpp1base` the rectangle (0,0)–(400,300), `cpp1dot` the square (0,400)–(100,500), all drawn by `draw_path`, widths 0; probe `/debug/trycomponent`, 6 calls per listener run, restarted between 1115 and 1119; one run each; no File > Save stage, nothing saved; results in [topics/reading.md](topics/reading.md))

| # | Step | Predicted | Result |
|---|---|---|---|
| 1102 | `fontlab_status`; `create_font` | 0.67 / 0.171; `Unnamed`, one font | as predicted |
| 1103–1107 | `create_glyph cpp1src`, `cpp1base`, `cpp5tgt`; `draw_path` the triangle and the rectangle | created with layers; `verified` | as predicted, 1 → 4 glyphs |
| 1108–1109 | `stage=auto` on `cpp5tgt`: `setrecipe cpp1src%2Bcpp1base`, `setauto` | read back, nothing built | as predicted |
| 1110 | `step=build` | as 1049: `cpp1src` at identity, `cpp1base` at (−200, 0), width 0 → 500, not marked | as predicted; `placed` false, `side_effect_detected` true (the width), synced, not marked |
| 1111 | `step=unauto` | both kept, marked | as predicted; width 500 |
| 1112 | `stage=offset&how=assign&element=1&dx=0&dy=0` | `cpp1base` matrix (0, 0), its ink box −200…200 → 0…400; `cpp1src` box 100…300 unchanged; width 500; `offset_placed`, marked | as predicted: `others_kept` true, raw nodes unchanged |
| 1113 | `set_glyph_width cpp5tgt 0` | 500 → 0, outline untouched | as predicted |
| 1114 | `get_glyph_outline cpp5tgt` | `verified`, both at (0, 0), ink 0–400 × 0–300 | as predicted; `source_in_step` true for both, LSB 0, advance 0 |
| 1115 | `step=clearrecipe` | recipe `""`, components and width kept, marked | as predicted |
| 1116–1118 | `create_glyph cpp1dot`, `cpp6tgt`; `draw_path` the square | `verified` | as predicted, 4 → 6 glyphs |
| 1119–1120 | listener restarted; on `cpp6tgt`: `setrecipe cpp1src%2Bcpp1base%2Bcpp1dot`, `setauto` | read back, nothing built | as predicted |
| 1121 | `step=build` | three components; `cpp1src` at identity, `cpp1base` at (−200, 0); a guess for `cpp1dot`: (−50, 0), centred on the first glyph's advance (0); the width changes | as predicted, the guess included: `cpp1dot` at (−50, 0); width 0 → 500 again; not marked |
| 1122 | `step=unauto` | all three kept, marked | as predicted; width 500 |
| 1123 | `offset&element=2&dx=150&dy=0` | `cpp1dot` box −50…50 → 150…250, y 400…500; the others kept; `offset_placed`, marked | as predicted |
| 1124 | `offset&element=1&dx=0&dy=0` | as 1112 | as predicted (call 6; the leftover recipe stays on `cpp6tgt`) |
| 1125 | `set_glyph_width cpp6tgt 400` | 500 → 400, outline untouched | as predicted |
| 1126 | `get_glyph_outline cpp6tgt` | `verified`; (0, 0), (0, 0), (150, 0); ink 0–400 × 0–500; LSB 0, RSB 0 | as predicted; `element_boxes_checked`, `source_in_step` true for all three |
| 1126a | the person's screenshots of `cpp6tgt` | three components, width 400 | as predicted: "Regular · 3 components"; Elements `cpp1dot` Δ=(150,0) badge 2, `cpp1base` badge 3, `cpp1src` badge 3; element bar of `cpp1src` X 0, Y 0, 100 %, 0°. **Not predicted:** a padlock before each element's name and in the element bar |
| 1126b | the person clicked `cpp1dot`, then `cpp1base` | — | each selected by a click (unlike the auto layer of 1055a); element bar X 150, Y 0 and X 0, Y 0; glyph bar 0 / 0 / 400 |
| 1126c | the person hovered the padlock column of the Elements panel | — | tooltip "Lock / unlock element content", grey in every row |
| 1126d | the person opened `cpp5tgt` (recipe cleared in 1115), no click | the padlock absent if the leftover recipe caused it | **wrong:** the same padlock before `cpp1base` and `cpp1src`; "Regular · 2 components", glyph bar 0 / −400 / 0, X 0, Y 0 |
| 1127 | `create_glyph cpp7tgt` | created with its layer | as predicted, 6 → 7 glyphs |
| 1128 | control: the person, Glyph > Add Component `cpp1src` into `cpp7tgt`, X 0, Y 0; hovers | one component at (0, 0); the padlock not predicted | as predicted, and **the same padlock** before `cpp1src`: FontLab marks every component so, not one placed by Glyphbridge; badge 3 → 4; glyph bar 100 / −300 / 0; Layers panel tooltip "Lock / unlock layer (Alt: all layers)"; no OUTPUT line (a GUI action) |

### PC3 series: four to 30 components and a repeated source (2026-11-17, FontLab 8.9.5 in Demo mode, listeners 0.172 and 0.173 / server 0.67, through Claude Code; the PC2 font `Unnamed`; new sources by `draw_path` or the listener's `/glyph/polygon`, widths 0; probe `/debug/trycomponent`, 6 calls per listener run, restarted before 1144, 1161 and 1170; one run each; no File > Save stage, nothing saved; results in [topics/reading.md](topics/reading.md))

| # | Step | Predicted | Result |
|---|---|---|---|
| 1129 | `fontlab_status` | 0.67 / 0.172 | as predicted; 12 changes counted |
| 1130–1135 | `create_glyph cpp1bar`, `cpp1top`, `cpp8tgt`, `cpp9tgt`; `draw_path` `cpp1bar` (0,−100)–(600,−50), `cpp1top` (0,600)–(50,650) | created with layers; `verified` | as predicted, 7 → 11 glyphs |
| 1136–1137 | on `cpp8tgt`: `setrecipe cpp1src+cpp1base+cpp1dot+cpp1bar`, `setauto` | read back, nothing built | as predicted |
| 1138 | `step=build` | four components, `cpp1bar` at (−300, 0) if centred on the first glyph's advance; width 600 if the ink width, 500 if fixed | `cpp1bar` at (−300, 0) as predicted; **width 500, not 600: the ink-width explanation is contradicted**; not marked |
| 1139–1141 | `unauto`; `offset&element=3&dx=0&dy=0`; `clearrecipe` | kept; `cpp1bar` box −300…300 → 0…600, the others kept; recipe `""` | as predicted |
| 1142–1143 | `set_glyph_width cpp8tgt 0`; `get_glyph_outline` | 500 → 0; `verified`, ink −200…600 × −100…500 | as predicted; `source_in_step` true for all four |
| 1144–1146 | listener restarted; on `cpp9tgt`: `setrecipe` with `+cpp1top`, `setauto`, `build` | five; `cpp1top` at (−25, 0); width 500 | as predicted |
| 1147–1149 | `unauto`; `element=4&dx=175&dy=0`; `clearrecipe` | kept; `cpp1top` box −25…25 → 175…225, the others kept | as predicted |
| 1150–1151 | `set_glyph_width cpp9tgt 350`; `get_glyph_outline` | `verified`, ink −300…300 × −100…650 | as predicted; LSB −300, RSB 50 |
| 1152 | listener 0.173 restarted; a script through the listener: `cpp30s01`…`cpp30s30` (source k the rectangle (0, 20k)–(10k, 20k+10)), `cpp15tgt`, `cpp30tgt` | every drawing as asked; 43 glyphs | the script stopped after `cpp30s01` only because the listener's raw replies have no `verified` (the server adds it); rerun with a node re-read of each source: all 30 as asked, both targets with layers. **An agent error:** an unintended `POST /glyph/create` made an empty glyph `zzprobe_none` (left in place), so 44 glyphs |
| 1153–1155 | on `cpp15tgt`: `setrecipe cpp30s01…s15`, `setauto`, `build` | 15 components, `cpp30sk` at (−5k, 0); width 500; under 1 s | as predicted; build 0.000 s, request 0.003 s |
| 1156–1158 | `unauto`; `element=14&dx=0&dy=0`; `clearrecipe` | kept; `cpp30s15` box −75…75 → 0…150, the other 14 kept | as predicted; 15 ink boxes read in a request of 0.006 s |
| 1159–1160 | `set_glyph_width cpp15tgt 300`; `--check --outline cpp15tgt` | `verified`, ink −70…150 × 20…310 | as predicted; all 15 `source_in_step` true; `--check` also ran its other checks (no dialog appeared) |
| 1161–1163 | listener restarted; on `cpp30tgt`: `setrecipe cpp30s01…s30`, `setauto`, `build` | 30 components by the same rule; width 500 | as predicted, in recipe order, the last at (−150, 0); build 0.001 s, request 0.006 s |
| 1164–1166 | `unauto`; `element=29&dx=0&dy=0`; `clearrecipe` | kept; `cpp30s30` box −150…150 → 0…300, the other 29 kept | as predicted; 30 ink boxes read in a request of 0.009 s |
| 1167–1168 | `set_glyph_width cpp30tgt 600`; `get_glyph_outline` (server function, timed) | `verified`, ink −145…300 × 20…610; `source_in_step` true | `verified`, ink and margins as predicted, 0.035 s; **wrong: all 30 `source_in_step` "unknown"**, "the glyph has 30 elements, more than 20" (the outline route's own cap, `_COMPONENT_BOX_MAX`, v0.130) |
| 1169 | `create_glyph cpp10tgt` | created with its layer | as predicted, 44 → 45 |
| 1170–1172 | listener restarted; `setrecipe cpp1src+cpp1src+cpp1src`, `setauto`, `build` | three separate components; copies 2 and 3 at (−100, 0) if FontLab moves by half the ink width, (−200, 0) if it moves the ink centre onto 0 (the two rules first differ here: `cpp1src`'s ink is 100…300) | three separate components; **copies at (−200, 0): the ink centre moves onto 0**; width 500 |
| 1173–1175 | `unauto`; `element=1&dx=150&dy=0`; `clearrecipe` | kept; copy 2's box −100…100 → 250…450; copies 1 and 3 kept | as predicted, copy 3 unchanged although it sat where copy 2 had been |
| 1176–1177 | `set_glyph_width cpp10tgt 0`; `get_glyph_outline` | `verified`, (0,0), (150,0), (−200,0); ink −100…450 × 0…300 | as predicted; all three `source_in_step` true |

### AC2 series: `add_component`'s list and the caps removed, live (2026-11-17, FontLab 8.9.5 in Demo mode, listener 0.174 / server 0.68, through Claude Code; the PC3 font `Unnamed`; one run each; nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1178 | listener restarted, Claude Desktop restarted; `fontlab_status` | 0.68 / 0.174 | as predicted. **The `add_component` schema this (resumed) session loaded stayed the old one** (no `components`), also after a second restart, while the server itself published the new one (checked by listing its tools from the repository): a resumed session keeps its cached tool definitions; the list-form checks moved to a new session |
| 1179 | `get_glyph_outline cpp30tgt` | `verified`; all 30 components `source_in_step` true (all "unknown" in 1168); a timing | as predicted: `verified`, ink −145…300 × 20…610, all 30 `source_in_step` true, `element_boxes_seconds` 0.001 |
| 1180 | new session; `fontlab_status`; `add_component`'s loaded schema | 0.68 / 0.174, `Unnamed`, one font; `components` and `confirmed_untested_size` present | as predicted (a new session loads the new schema, unlike the resumed one of 1178); 45 glyphs |
| 1181–1183 | `create_glyph ac2t02`; `add_component(ac2t02, components=[cpp1src (0,0), cpp1base (0,0)])`; read | placed, `verified`, width back to 0; both at identity, ink 0–400 × 0–300 | as predicted; build 0 s, request 0.003 s; both `source_in_step` true |
| 1184–1186 | `create_glyph ac2t03`; `[cpp1src (0,0), cpp1src (250,0)]`; read | two separate components, the copy drawn (350,0) (550,0) (450,300); ink 100–550 | as predicted; matrix of the copy (…, 250, 0); width 0 |
| 1187–1189 | `create_glyph ac2t15`; 15 entries `cpp30s01`–`s15`, x −100 / 0 / 100 for k mod 3 = 0 / 1 / 2, y 50 for even k; read | placed, `verified`, ink −100…240 × 20…340, width 0 | as predicted, every offset as asked; request 0.006 s; all 15 `source_in_step` true; `element_boxes_seconds` 0.001 |
| 1190–1192 | `create_glyph ac2t31`; 31 entries (`cpp30s01`–`s30`, then `cpp30s01`), no flag; read | `needs_confirmation`, nothing changed, the glyph empty | as predicted: `changed: false`, the agent_instruction to ask the person; `ac2t31` empty |
| 1193–1196 | `create_glyph cppx.alt`, `cppx_a`; `draw_path` the square (0,0)–(100,100) and the rectangle (0,0)–(50,200) | created with layers; `verified` | as predicted |
| 1197–1199 | `create_glyph ac2tdot`; `[cpp1src (0,0), cppx.alt (500,0)]`; read | (a guess) the name read literally: placed, `cppx.alt` drawn 500–600 × 0–100; otherwise `placed: false` with the clean-up | placed, `verified`, ink 100…600 × 0…300, as guessed |
| 1200–1202 | `create_glyph ac2tund`; `[cpp1src (0,0), cppx_a (500,0)]`; read | as 1198 | **wrong:** FontLab's build placed only `cpp1src`; `placed: false`, failed checks `element_count`, `components`; clean-up ran (recipe cleared, width restored, auto layer off), not marked, with `save_question_note`; `component_states` both "not reached" **although `cpp1src` is in the glyph** at (0,0); read: one component, `verified` |
| 1203–1205 | control, the single form: `create_glyph ac2tund1`; `add_component(ac2tund1, cppx_a)`; read | fails as 1201 if the name alone is misread | **wrong:** placed, `verified`, drawn 0–50 × 0–200. So only a recipe of several glyphs drops `cppx_a` |
| 1206–1208 | control, the order swapped: `create_glyph ac2tund2`; `[cppx_a (500,0), cpp1src (0,0)]`; read | fails as 1201 (low confidence) | as predicted: only `cpp1src`, at (0,0); the same reply. The order does not matter |
| 1209–1213 | refusals, list form: target `ac2t02` (2 components); `create_glyph ac2tref`, source `ac2t03` (holds components); reads | each refused, nothing changed | as predicted; `ac2t02` unchanged, `ac2tref` empty; OUTPUT "NOT DONE component …" for both |
| 1214 | the person asked whether to place 31 with `confirmed_untested_size=true` | — | the person declined; not run. The question named the glyph `ac2tt31` by an agent typo (meant `ac2t31`) |
| 1214a | the person's screenshots: the grid, then `ac2tund` opened | one component of `cpp1src` at X 0, Y 0; width 0 | as predicted: grid thumbnails agree with every read (`ac2t31`, `ac2tref` empty); glyph bar LSB 100, RSB −300, width 0; element bar X 0, Y 0, 100 %, 0°; Elements panel one row; tab "ac2tund" with a dot after it; OUTPUT "checking the built components against the list failed: … the glyph DID change" |
| 1215 | `finish_changes` | one reminder | 20 changes, one reminder |

### AC2u series: underscore names in a recipe of several glyphs (2026-11-17, same session, font and versions as AC2; one run each; nothing saved)

Hypothesis H1: a recipe of several glyphs reads `a_b` as a ligature of `a` and `b`. Predictions per step were not written down before the runs; the "Predicted" column gives what H1 implies. Recorded on 2026-11-17 from the session's hand-over notes. Every square and rectangle below was drawn with `draw_path`.

| # | Step | Predicted (from H1) | Result |
|---|---|---|---|
| 1216 | `fontlab_status` | 0.68 / 0.174 | as predicted |
| 1217–1220 | control: `create_glyph cppxa`, the rectangle (0,0)–(50,200); `create_glyph ac2u1`; `[cpp1src (0,0), cppxa (500,0)]`; read | placed, `verified` (no underscore) | as predicted |
| 1221–1228 | `cpp_x` (underscore in the middle) into `ac2u2`, `_cppx` (leading underscore) into `ac2u3`, each the same rectangle, each listed after `cpp1src`; reads | both dropped (no glyphs named by the parts) | as predicted: only `cpp1src` built in each; `placed: false`, clean-up ran |
| 1229–1234 | `create_glyph cpp`, the square (0,0)–(30,30); `create_glyph x`, the square (0,400)–(20,420) (FontLab gave it U+0078); `create_glyph ac2u4`; `[cpp1src (0,0), cpp_x (500,0)]`; read | the parts `cpp` and `x` placed instead of `cpp_x` | as predicted: FontLab built `cpp1src` (0,0), `cpp` (−15,0) and `x` (0,0), read `verified`; `cpp_x` itself ignored; the tool's name check caught the wrong parts. H1 holds (one run) |
| 1235 | `finish_changes` | one reminder | 18 changes, one reminder |

### AC3 series: the 0.175 / 0.69 build live (2026-11-17, FontLab 8.9.5 in Demo mode, listener 0.175 / server 0.69, through Claude Code in a new session with the 0.69 tool description; `create_font` without a family, one font open, `Unnamed`; prefix `ac3`; one run each; no File > Save stage, nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1236 | setup: `fontlab_status` (0.69 / 0.175, no font open); `create_font`; `create_glyph` `ac3s1`, `ac3s2`, `ac3s_x`, `ac3t1`–`ac3t3`; `draw_polygon` `ac3s1` the triangle (100,0) (300,0) (200,300), `ac3s2` the rectangle (0,0)–(400,300), `ac3s_x` the square (50,400)–(150,500); widths 0 | every step `verified`, layers created | as predicted; the first glyph's mark read `glyph_has_changes: false`, every later one true (as in 668; information only since server 0.52) |
| 1237 | `add_component ac3t1`, `[ac3s1 (0,0), ac3s_x (500,0)]`; then `get_glyph_outline ac3t1` | refused before any write; `ac3t1` empty | as predicted: the server refused, naming `components[1] 'ac3s_x'` and 1234; `ac3t1` read `empty: true`. The listener's own refusal was not reached (stub only) |
| 1238 | `add_component ac3t2`, single form, `ac3s_x` at (0, 0) | placed, `verified`, width 0 | as predicted |
| 1239 | `add_component ac3t3`, `[ac3s1 (0,0), ac3s2 (500,0)]` | both placed, `verified`, width written back to 0 | as predicted; `elapsed_seconds` 0.003 |
| 1239a | `finish_changes` | one reminder | 12 changes, one reminder |

Not reached live: the per-entry states after a dropped entry and `components_after`. The only drop seen live came from an underscore name, which the server and the listener now refuse, so no known request makes the build drop an entry; both stay stub-tested.

### RM series: removing a component through the API (2026-11-17, FontLab 8.9.5 in Demo mode, listener 0.176 / server 0.69, through Claude Code; the AC3 font `Unnamed`, FontLab not restarted, listener restarted once before 1240a; prefix `cppr`; probe `/debug/trycomponent`, stages `removeshape` and `clearcomponents`, 5 of 6 calls used; one run each; no File > Save stage, nothing saved; results in [topics/reading.md](topics/reading.md) "Components: removing one through the API")

| # | Step | Predicted | Result |
|---|---|---|---|
| 1240 | names only, listener 0.175: `/debug/classdir?name=flLayer&members=…` and `name=flShape&members=…` (nothing called) | candidate calls with signatures | `flLayer.removeShape(flShape[, bool recursive=true])`, `clearComponents()`, `removeAllShapes([ShapeType shape_type=AnyShape])`, `cleanEmptyShapes()`, `replaceShape(old, new)`, `components` "list(name, transform)"; `flShape.remove([flObject])`, `decomposite()`, `ejectTo([clone[, apply_tx]])` |
| 1240a | setup, listener 0.176: `create_glyph` `cpprs1`–`cpprs3`, `cpprt1`–`cpprt5`; `draw_polygon` `cpprs1` the triangle (100,0) (300,0) (200,300), `cpprs2` the rectangle (0,0)–(400,300), `cpprs3` the square (0,400)–(100,500); `add_component`: `cpprt1` and `cpprt2` `[cpprs1 (0,0), cpprs2 (500,0)]`, `cpprt3` `[cpprs1 (0,0), cpprs1 (300,0)]`, `cpprt4` `cpprs2` at (0,0), `cpprt5` `[cpprs1 (0,0), cpprs2 (500,0), cpprs3 (0,0)]`; widths 0 | every step `verified` | as predicted |
| 1241 | `removeshape&target=cpprt1&element=1&recursive=0` | `removed` true: `cpprs1` at (0,0) left, its box kept; sources, width, glyph count, `autoLayer`, recipe unchanged; synced and marked | as predicted: `call_returned` None, shapes 2 → 1, nodes 7 → 3, 0.002 s; `glyph_has_changes` true. FontLab's right sidebearing read −900, not −300 (the known lag) |
| 1242 | the person, Edit menu (nothing chosen) | Undo offers nothing, as after `add_component` (1090) | as predicted: Undo and Redo greyed out; the grid thumbnail of `cpprt1` showed the triangle only |
| 1243 | `removeshape&target=cpprt2&element=0&recursive=1` | as 1241: `cpprs2` at (500,0) left | as predicted; no difference from `recursive=0` seen |
| 1244 | `removeshape&target=cpprt3&element=0&recursive=0` (one source twice) | the copy at (300,0) left | as predicted; `reference_count` read 1 on every component before and after, also for the source used twice |
| 1245 | `removeshape&target=cpprt4&element=0&recursive=0` (the only component); then `add_component cpprt4`, `cpprs3` at (0,0) | empty, layer kept; placing again `verified` | as predicted: shapes 1 → 0, `empty_after` true, layer `Regular` kept; `add_component` `verified` |
| 1246 | `clearcomponents&target=cpprt5` (three components) | all three gone, layer kept, sources unchanged | **wrong:** returned None and changed nothing (elements, boxes, outline, state the same); `changed` false, `removed` false, not marked. `componentsCount()` read 0 on every target of this series, before and after |
| 1247 | the person's screenshot of the grid | thumbnails agree with the reads | as predicted: `cpprt1` triangle, `cpprt2` rectangle, `cpprt3` one triangle, `cpprt4` the small square, `cpprt5` all three |
| 1247a | `finish_changes` | one reminder | 17 changes, one reminder |

### CC series: the component count (0.177 / 0.70) and the width write-back (0.178 / 0.71) live (2026-11-17, FontLab 8.9.5 in Demo mode, through Claude Code in a resumed session; the RM font `Unnamed`; one run each; no File > Save stage, nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1248 | `fontlab_status` | 0.177 / 0.70 | as predicted |
| 1249 | `get_glyph_outline cpprt5` (3 components) | `verified`; the new note | as predicted: "3 of the glyph's elements are components; their outlines are included in this reply" |
| 1250 | `add_component .notdef`, `cpprs2` | placed, or refused if `.notdef` has no layer | refused, nothing changed: no layer |
| 1250a | `set_glyph_width .notdef 500` (layer created, 250 → 500), then the same `add_component` | placed | **`placed: false`**, only `width_unchanged` failed; the component is in the glyph; not marked |
| 1250b | `get_glyph_sidebearings .notdef` | — | width **0**: the single form had no width write-back (the list form had one); `.notdef` left so |
| 1250c | `check_notdef` | `has_outline`, evidence "components 1" | as predicted: "nodes 4, shapes 1, components 1" |
| 1251 | `move_nodes` on `cpprt1` | refused, a component | as predicted |
| 1252 | `add_component` into `cpprt1` | refused, not empty | as predicted |
| 1253 | after listener 0.178 / server 0.71: `fontlab_status`; setup `cppw1`–`cppw3` at width 500, `cppws` the square (0,0)–(200,200) at advance 300 | 0.178 / 0.71; setup `verified` | as predicted |
| 1254 | single form, `cpprs2` (advance 0) into `cppw1` | `verified`, width 500, `width_set_by_build` 0 | as predicted |
| 1255 | control: single form, `cppws` (advance 300) into `cppw2` | `width_set_by_build` 300 if FontLab takes the source's advance | **300**; `verified`, width 500: a one-glyph recipe build sets the width to the source's advance (one run each, 1254 and 1255) |
| 1256 | list form `[cpprs1, cpprs2]` into `cppw3` | `verified`, width 500, `width_set_by_build` 500 | `verified`, width 500, no `width_set_by_build`: FontLab's width equalled the target's 500, so this run cannot tell |
| 1256a | `finish_changes` | one reminder | 12 changes, one reminder |

### RC series: `remove_component` live (2026-11-18, listener 0.179 / server 0.72, FontLab 8.9.5 in Demo mode, through Claude Code in a resumed session; a new font `Unnamed`; one run each; no File > Save stage, nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1257 | `fontlab_status` | 0.179 / 0.72 | as predicted; no font open (the RM font was gone) |
| 1257a | setup: `create_font` (`Unnamed`); `create_glyph` `rmcs1`–`rmcs3`, `rmct1`–`rmct6`; `draw_polygon` `rmcs1` the triangle (100,0) (300,0) (200,300), `rmcs2` the rectangle (0,0)–(400,300), `rmcs3` the square (0,400)–(100,500); `add_component`: `rmct1`, `rmct3`, `rmct4` `[rmcs1 (0,0), rmcs2 (500,0)]`, `rmct2` the same plus `rmcs3 (0,0)`, `rmct5` `rmcs1`, `rmct6` 30 (`rmcs3` and `rmcs1` in three rows, x 0–1350 by 150) | every step `verified` | as predicted; each list build reported `width_set_by_build` 500, written back to 0 |
| 1257b | `get_glyph_outline rmct1` | element 1 `rmcs2` at (500, 0) | as predicted; both component shapes read `is_composite` **true** |
| 1258 | `remove_component rmct1`, index 1, `rmcs2`, (500, 0) | `removed`, `rmcs1` left, width 0 | as predicted, 0.003 s, synced and marked |
| 1259 | `rmct4`, index 1 named `rmcs1` | refused, nothing changed | as predicted |
| 1259a | `rmct4`, index 1 `rmcs2` at (499, 0) | refused, nothing changed | as predicted; the text read the offset as "(500.0, -0.0)" |
| 1259b | `get_glyph_outline rmct4` | unchanged | as predicted: two components, `verified` |
| 1260 | `rmct2`, list: index 0 `rmcs1`, index 2 `rmcs3` | `removed`, `rmcs2` at (500, 0) left | as predicted, 0.003 s |
| 1261 | `rmct3`, list: both | `removed`, `empty_after` true | as predicted |
| 1262 | `rmct6`, list: all 30 | `removed`, empty, under 0.05 s | as predicted, 0.004 s |
| 1263a | the person drew a rectangle in `rmct5` with FontLab's Rectangle tool; `get_glyph_outline` | element 0 the component, element 1 a contour | as predicted: the contour (318,281)–(460,446), `is_composite` false |
| 1263 | `rmct5`, index 0 `rmcs1` | `removed`, the contour kept | as predicted, 0.006 s, `components_after` `["not a component"]` |
| 1263b | `get_glyph_outline rmct5` | the rectangle alone | as predicted, node for node, `verified` |
| 1264 | `create_font` | `Unnamed1`, fonts 1 → 2 | as predicted |
| 1264a | `rmct4`, index 1 `rmcs2` (500, 0), `Unnamed1` in front | refused: no such glyph | as predicted |
| 1264b | the person clicked the `Unnamed` tab; the same call | `removed` in `Unnamed Regular`, `fonts_open` 2, the switch noted | as predicted |
| 1264c | `finish_changes` | one reminder | 26 changes, one reminder |

### NE series: the recipe build on a glyph that is not empty (2026-11-18, listener 0.180 / server 0.72, FontLab 8.9.5 in Demo mode, through Claude Code; probe `/debug/trycomponent` `stage=auto&nonempty=yes`, requests sent straight to the listener after the user's go-ahead; a new font `Unnamed`; one run each; no File > Save stage, nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1265 | `fontlab_status` | 0.180 / 0.72 | as predicted; no font open |
| 1265a | setup: `create_font` (`Unnamed`); `create_glyph` `cppnes1`, `cppnet1`, `cppnes2`, `cppnet2`, `cppnet3`; `draw_polygon` `cppnes1` the triangle (100,0) (300,0) (200,300), `cppnes2` the square (0,400)–(100,500), `cppnet1` the rectangle (500,0)–(700,200); `add_component` `cppnes2` at (300, 0) into `cppnet2` and `cppnet3` | every step `verified` | as predicted; every width 0 |
| 1265b | the gate without `go` | the step described, nothing changed | as predicted |
| 1266 | `cppnet1` (one contour), `setrecipe` `cppnes1` | recipe set, outline unchanged, `existing_kept` true | as predicted |
| 1267 | `setauto` | `autoLayer` true; nothing built yet (as 1041a), the other candidate a rebuild | as predicted: nothing built, `existing_kept` true |
| 1268 | `build` | A (about 60 %): the layer rebuilt from the recipe alone, the rectangle lost; B: the component added beside it | **A**: `buildAuto()` returned True; the layer holds one shape, a component of `cppnes1` at identity (ink 100…300 × 0…300); the rectangle is gone (`existing_missing`, `existing_kept` false, `placed` false); width 0, sources and glyph count unchanged; synced, not marked |
| 1269 | `unauto` | `autoLayer` false, elements as after 1268 | as predicted; `component_normal` true, `existing_kept` false, not marked |
| 1270 | `clearrecipe` | recipe `""`, elements unchanged | as predicted; `recipe_cleared` true, not marked |

### TL series: a temporary layer in the target glyph (2026-11-18, listener 0.181 / server 0.72, FontLab 8.9.5 in Demo mode, through Claude Code; probe `/debug/trycomponent` `stage=templayer`, requests sent straight to the listener after the user's go-ahead; the font `Unnamed` of NE; one run each; no File > Save stage, nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1271 | `fontlab_status` | 0.181 / 0.72, `Unnamed` open | as predicted |
| 1271a | setup: `create_glyph cppnet4`, `draw_polygon` the rectangle (500,0)–(700,200) | `verified` | as predicted; the gate text of `stage=templayer` shown without `go` |
| 1272 | `cppnet2` (one component of `cppnes2` at (300, 0)), `addlayer` | about 65 %: the layer added, Regular stays active; the alternative: the new layer becomes active | **the alternative**: layers `Regular`, `gb_temp_component`; the active layer is now `gb_temp_component` (empty, autoLayer off, recipe `""`); `Regular` unchanged (the component, its ink box (300…400 × 400…500), contours); width, source and glyph count unchanged; `layer_added` false only because the active layer changed; sync verdict `at_risk` (most likely the check compares the legacy view with the now empty active layer; not isolated); not marked. The series stopped here, as agreed |
| 1273 | after the listener restart (0.182): `fontlab_status` | 0.182 / 0.72, `Unnamed` open | as predicted |
| 1273a | `create_glyph cppnet5` (not a test of the probe: the setup for the next series) | created with its layer `Regular` | **created without a layer**: `layer_note` "the glyphs of this font have different layer names (['Regular', 'gb_temp_component'])": the temporary layer left in `cppnet2` (1272) stops `create_glyph` from choosing the new glyph's layer name; not marked. So a temporary layer left behind affects other tools. `cppnet5` is not used; Glyph > Add Component must not be used on it (the crash of 612–619) |
| 1274 | `cppnet4` (the rectangle (500,0)–(700,200)), `addlayer` | as 1272: added, the new layer active | as predicted (as 1272): `gb_temp_component` added and active, `Regular` unchanged, sync `at_risk`, not marked |
| 1275 | `activate` | about 70 %: `Regular` active, `isActive` agrees, nothing else changed | as predicted: `Regular` active, `is_active` working True / temp False, `layers_unchanged`, `working_active` true; sync `synced` |
| 1276 | `build` `cppnes1` | about 60 %: five sub-calls ok, one component on the temporary layer | as predicted: every sub-call read back as set, `buildAuto()` True; the temporary layer holds one component of `cppnes1` at identity (ink 100…300 × 0…300); `Regular`, widths, source, glyph count unchanged; `built` true |
| 1277 | `move` | `Regular` gains it; the temporary layer still holds it (about 55 %) | as predicted: `Regular` holds the rectangle and the component, the temporary layer still holds it; `addShape` returned an `flShape` (not the Python object passed); `moved` true |
| 1278 | `removelayer` | about 50 / 50: the component survives or goes with the layer | **survives**: only `Regular` left, active; the rectangle and the component as before; `placed_beside` true; marked, synced |
| 1279–1283 | `cppnet3` (a component of `cppnes2` at (300, 0)): `addlayer`, `activate`, `build`, `move`, `removelayer` | as for `cppnet4` | as predicted, step for step: the new layer active after 1279, `working_active` true (1280), `built` (1281), `moved` with the temporary layer still holding it (1282), `placed_beside` true, marked (1283) |
| 1283a | `get_glyph_outline cppnet4` | `verified`: the rectangle and a component of `cppnes1` on layer `Regular` | `verified` (ink 100…700 × 0…300, FontLab's box), the rectangle and the triangle as drawn; **but the component names `component_layer` `gb_temp_component`**, a layer `cppnes1` does not have; `source_in_step` `"unknown"` for that reason. The probe's checks compared the moved component with the one on the temporary layer, which named the same layer, so they did not catch it |
| 1284 | the person opened `cppnet4` in a glyph window (screenshot, nothing clicked in the glyph) | FontLab shows two elements; perhaps a warning or the layer name for the component | LAYERS & MASTERS: only `Regular`, "1 cpn., 1 el."; ELEMENTS: a component row `cppnes1` with the padlock and reference badge **4** (uses plus one: `cppnet1`, `cppnet3`, `cppnet4`, as in the Elements-badge watch point), and the rectangle, 4/4 nodes; the triangle drawn grey at (100,0)–(300,0)–(200,300), the rectangle at (500,0)–(700,200); no warning, and the panel shows no source-layer name, so this view cannot tell `gb_temp_component` from `Regular` |
| 1285 | after the listener restart (0.183): `fontlab_status`; the gate text of `stage=fixlayer` | 0.183 / 0.72 | as predicted |
| 1285a | `fixlayer` `cppnet4`, element 1 (`cppnes1`, naming `gb_temp_component`) | A (about 55 %): set, nothing else changed; B: refused or not read back | **A**: `componentLayer` reads `Regular`; the component's source, matrix and ink box (100…300 × 0…300), the rectangle, the outline, width, source and glyph count unchanged; `layer_set` true; marked, synced; 0.008 s |
| 1286 | `get_glyph_outline cppnet4` | `verified`, layer `Regular`, `source_in_step` true | as predicted |
| 1287 | `fixlayer` `cppnet3`, element 1 | as 1285a | as predicted: `layer_set` true; `cppnes2` at (300, 0) unchanged; marked |
| 1288 | `get_glyph_outline cppnet3` | as 1286 | as predicted: both components on `Regular`, `source_in_step` true each, `verified` |
| 1289 | control: `fixlayer` `cppnet3`, element 0 (`cppnes2`, already `Regular`) | refused, nothing changed | as predicted: "already names the layer 'Regular'" |
| 1290 | after the listener restart (0.184): `fontlab_status`, the gate texts; `droptemp` `cppnet2` | about 80 %: `setActive()`, then the layer removed, its component unchanged | as predicted for the layer: `setActive()` made `Regular` active, `removeLayer` left only `Regular`, active; `working_kept`, `temp_dropped` true; not marked (a clean-up step). **But the element `droptemp` found in `Regular` was already a plain shape** (`is_component` false, offset (300, 0)), not the component of `cppnes2` it held after 1272 |
| 1291 | `get_glyph_outline cppnet2` | `verified`, one component of `cppnes2` at (300, 0) | `verified`, the square (300…400 × 400…500), **one plain shape**, `is_component` false, its transform (300, 0) kept: the component had become contours between 1272 and 1290 ([WATCH-POINTS.md](WATCH-POINTS.md), the second occurrence) |
| 1292 | `create_glyph cppnet6` | `layer_created` `Regular` again | as predicted: the font's layers agree again |
| 1293 | `draw_polygon cppnet6`, the rectangle (500,0)–(700,200) | `verified` | as predicted |
| 1294–1296 | `cppnet6`: `addlayer`, `activate`, `build` `cppnes1` | as 1274–1276 | as predicted: the new layer active, then `Regular` again; `built` true |
| 1297 | `setlayer` | about 75 %: `temp_layer_set` true | as predicted: the component on the temporary layer names `Regular`, nothing else changed |
| 1298 | `move` | `moved`, `component_layer_matches` true | as predicted |
| 1299 | `removelayer` | `placed_beside` true, marked | **as predicted: the first full pass of the route**; only `Regular`, active; the rectangle and the component; marked, synced |
| 1300 | `get_glyph_outline cppnet6` (and `cppnet1` as a check) | `verified`, the component on `Regular`, `source_in_step` true | as predicted; `cppnet1`'s recipe-built component is still a component |
| 1283b | `get_glyph_outline cppnet3` | as 1283a | `verified` (ink 100…400 × 0…500); `cppnes2` at (300, 0) on `Regular`, `source_in_step` true; the new `cppnes1` component names `gb_temp_component`, as in 1283a |

### H1 series: what turned `cppnet2`'s component into a plain shape (2026-11-18, listener 0.184 / server 0.72, FontLab 8.9.5 in Demo mode, through Claude Code; probe `/debug/trycomponent` `stage=templayer`, requests sent straight to the listener after the user's go-ahead; the TL font `Unnamed`, one font open; one run; no File > Save stage, nothing saved)

Hypothesis H1: `create_glyph`'s `font.update()`, run after a listener restart had emptied the update guard's memory, flattens the component of a glyph whose empty temporary layer is active and unsynced. Predicted for the whole series: only R4 (`cppnet10`) flattens. The targets were not read between steps, only by the probe's own replies and at the end (1314).

| # | Step | Predicted | Result |
|---|---|---|---|
| 1301 | `fontlab_status`, `list_glyphs` | 0.184 / 0.72, `Unnamed` open | as predicted; the nine glyphs of TL |
| 1302 | setup: `create_glyph` `cppnet7`–`cppnet10`, then `add_component` `cppnes2` at (300, 0) into each | layers `Regular`, `verified` | as predicted: each `layer_created` `Regular`, `placed`, `verified`, synced, marked; `font.update()` ran in each `create_glyph` (no temporary layer existed) |
| 1303–1304 | R1 (control) `cppnet7`: `addlayer`, `droptemp` | the temporary layer active, then dropped; the component kept | as predicted: `gb_temp_component` active, sync `at_risk`; `droptemp`: `setActive()` of `Regular`, the layer removed, the component of `cppnes2` / `Regular` at (300, 0) before and after, synced |
| 1305 | R2 `addlayer cppnet8` | as 1303 | as predicted |
| 1306 | R2 `create_glyph cppnex1` | the refresh skipped to protect `cppnet8`; created **without** a layer (as 1273a) | the refresh skipped, `display_refresh_skipped_to_protect` `["cppnet8"]` (as predicted); **but created with its layer `Regular`** (`layer_name_source` "other glyphs"), against 1273a |
| 1307 | R2 `droptemp cppnet8` | the component kept | as predicted: a component before and after, synced |
| 1308–1309 | `addlayer` `cppnet9`, `cppnet10`, left | as 1303 | as predicted: each temporary layer active, `at_risk` |
| — | the person restarted the listener (0.184 in the OUTPUT panel; FontLab's grid still showed 13 glyphs, without `cppnex1`) | | |
| 1310 | `fontlab_status` | 0.184 / 0.72 | as predicted |
| 1311 | R3 `droptemp cppnet9` (no `create_glyph` before it) | the component kept | as predicted: a component before and after, synced |
| 1312 | R4 `create_glyph cppnex2` | `font.update()` runs (no skip), no layer | `font.update()` ran (no skip, as predicted); **created with its layer `Regular`** |
| 1313 | R4 `droptemp cppnet10` | `Regular` holds a plain shape | as predicted: `Regular` held one plain shape at (300, 0) before the clean-up; the layer dropped |
| 1314 | `get_glyph_outline` `cppnet7`–`cppnet10`, `cppnet1`, `cppnet3`, `cppnet4`, `cppnet6` | only `cppnet10` a plain shape | **not as predicted: `cppnet8`, `cppnet9` and `cppnet10` are plain shapes** (the square at 300…400 × 400…500, `is_component` false, the offset (300, 0) kept, `verified`); `cppnet7`, and the components of `cppnet1`, `cppnet3`, `cppnet4`, `cppnet6`, are still components, `source_in_step` true |

Reading: `font.update()` ran only in 1302 (before any temporary layer) and 1312; `cppnet9` was a component in 1311, so 1312 is the likely moment for it. `cppnet8` changed somewhere between 1307 and 1314, not narrowed. H1 as predicted ("only the glyph with the active temporary layer") is contradicted; why `cppnet7` stayed a component is open ([WATCH-POINTS.md](WATCH-POINTS.md)). Lesson: read every target after every step.

### Run C: the moment of the flattening (2026-11-18, the same conditions as the H1 series; every target read straight from `/glyph/outline` after every step)

Targets `cppnec1`–`cppnec4`, each a component of `cppnes2` at (300, 0); `cppnec1` mirrors `cppnet7`, `cppnec2` `cppnet8`, `cppnec3` `cppnet9`; `cppnec4` never gets a temporary layer. "All components" below means all four read as components, unless a row says otherwise.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1315 | `fontlab_status`; the reading script checked on `cppnet7`, `cppnet8`, `cppnet4` | 0.184 / 0.72 | as predicted; the script agreed with 1314 |
| 1316 | setup: `create_glyph`, then `add_component` `cppnes2` at (300, 0), for `cppnec1`–`cppnec4` | four components, `verified` | as predicted |
| 1317 | C1 `addlayer cppnec1` | all components (90 %) | as predicted; while its temporary layer was active, `/glyph/outline` of `cppnec1` listed no elements (`available` false; also 1319, 1320, 1322, 1323 for the glyph then holding one) |
| 1318 | C2 `droptemp cppnec1` | all components (90 %) | as predicted |
| 1319 | C3 `addlayer cppnec2` | all components (90 %) | as predicted |
| 1320 | C4 `create_glyph cppnexc1` | the refresh skipped; all components (75 %) | as predicted: skipped to protect `cppnec2`; `cppnexc1` got its layer `Regular` |
| 1321 | C5 `droptemp cppnec2` | all components (80 %) | as predicted |
| 1322 | C6 `addlayer cppnec3`, left | all components (90 %) | as predicted |
| — | the person restarted the listener | | |
| 1323 | `fontlab_status`; read | all components (70 %) | as predicted: the restart alone changed nothing |
| 1324 | C7 `droptemp cppnec3` | all components (85 %) | as predicted |
| 1325 | C8 `create_glyph cppnexc2`: `font.update()` runs | if H1 repeats, `cppnec2` and `cppnec3` flatten, `cppnec1` and `cppnec4` do not (about 55 %) | **as predicted**: `cppnec2` and `cppnec3` plain shapes, the offset (300, 0) kept; `cppnec1`, `cppnec4` (and `cppnet7`, read as well) components |
| 1326 | C9 `create_glyph cppnexc3`: a second `font.update()` | no further change (70 %) | as predicted |
| 1327 | `get_glyph_outline` `cppnec1`–`cppnec4` | as 1326 | as predicted, all `verified`; `source_in_step` true on the two components |

Reading (one run, consistent with 1301–1314): the plain shapes appear at the next `font.update()` that runs, not at the restart nor at a skipped `create_glyph`. A glyph flattened only when, while its temporary layer was active, a `create_glyph` ran with its refresh skipped (`cppnec2`, `cppnet8`) or the listener restarted (`cppnec3`, `cppnet9`, `cppnet10`, `cppnet2`). A temporary layer added and dropped with nothing in between (`cppnec1`, `cppnet7`) and the route run step by step with nothing in between (`cppnet6`) did not flatten at later updates. The cause inside these two events is not isolated ([WATCH-POINTS.md](WATCH-POINTS.md)).

### PB series: the temporary-layer route on a Power Brush target (2026-11-18, listener 0.185 / server 0.72, FontLab 8.9.5 in Demo mode, through Claude Code; probe `/debug/trycomponent` `stage=templayer&brush=yes`, requests sent straight to the listener after the user's go-ahead (build approval of 0.185); the font `Unnamed`, one font open; one run; no File > Save stage, nothing saved)

The brush glyphs were drawn by the person (Font > New Glyph > Create Blank, the Power Brush tool, default brush 50, one stroke, the tab closed afterwards). Every read went through `/glyph/outline` (modern layer only). Hypothesis: the guard's full check (`sync=full`, it reads `glyph.layers` and `glyph.layer`) arms F1, the light check (`sync=light`) does not.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1328 | `fontlab_status` after the listener restart | 0.185 / 0.72 | as predicted |
| 1329 | the person: `cpppb1`, `cpppb2`, `cpppb3`, one stroke each, tabs closed | — | done, one glyph at a time |
| 1330 | read all three | one brush shape each (`isComposite` true, not a component) | as predicted: 51, 69 and 51 nodes |
| 1331–1336 | PB-L: `cpppb2`, `addlayer`, `activate`, `build cppnes1`, `setlayer`, `move`, `removelayer`, `sync=light` | as on a plain target; the brush kept | as predicted: every step `synced` (also `addlayer`), `working_active`, `built`, `temp_layer_set`, `moved`, `component_layer_matches`, `placed_beside` true, marked; the brush shape unchanged beside the new component (69 + 3 nodes) |
| 1337 | `create_glyph cpppbx1` (`font.update()` ran); read all three | all keep their brush (70 %) | as predicted |
| 1338–1343 | PB-F: the same route on `cpppb3`, `sync=full` | as PB-L | as predicted; `addlayer` read `at_risk` (as with plain targets), the later steps `synced`; `placed_beside` true, marked |
| 1344 | `create_glyph cpppbx2`; read all three | **`cpppb3` flattened (75 %)**, the others kept | **not as predicted**: all three still hold their brush |
| 1345 | added: `create_glyph cpppbx3`, a second `font.update()`; read; `get_glyph_outline cpppb3` | about 50 / 50 for `cpppb3` | all three still brush; `cpppb3` `verified`, the brush element with fractional nodes, the component `source_in_step` true |

Reading (one run): the route places a component beside a Power Brush shape and leaves it unchanged, in both modes. The full check's legacy reads, followed by two `font.update()` calls, did not flatten these GUI-drawn brush glyphs with closed tabs, so the hypothesis is contradicted here; what arms F1 stays open ([WATCH-POINTS.md](WATCH-POINTS.md)).

### NB series: `add_component` on a glyph that is not empty, live (2026-11-18, listener 0.186 / server 0.73, FontLab 8.9.5 in Demo mode, through a NEW Claude Code session with the 0.73 tool description; FontLab had been closed, so `create_font` without a family, one font open, `Unnamed`; prefix `cpq`; one run each; no File > Save stage, nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1346 | `fontlab_status` (0.73 / 0.186, no font open); `create_font`; `create_glyph` `cpqs1`, `cpqs2`, `cpqt1`–`cpqt5`; `draw_polygon` `cpqs1` the triangle (100,0) (300,0) (200,300), `cpqs2` the square (0,400)–(100,500), `cpqt1` and `cpqt4` the rectangle (0,0)–(400,300); `add_component cpqt2` `cpqs2` at (300, 0) | every step `verified`, all widths 0 | as predicted; the empty target's reply said `placement: "empty layer"` |
| 1347 | single form onto a contour: `cpqt1` ← `cpqs1` at (500, 0) | `placement` "temporary layer", `placed`, `verified`, `existing_kept`, width 0 | as predicted |
| 1348 | single form onto a component: `cpqt2` ← `cpqs1` at (0, 0) | as 1347 | as predicted |
| — | the person: one Power Brush stroke in `cpqt3` (empty) | — | done; ELEMENTS showed one brush element |
| 1349 | single form onto a brush: `cpqt3` ← `cpqs2` at (300, 0) | as 1347, the brush kept | as predicted |
| — | the person: one Power Brush stroke in `cpqt4` (beside the rectangle) | — | done; `Regular` read "2 elements" |
| 1350 | list form onto a brush with a contour: `cpqt4` ← `cpqs1` (500, 0), `cpqs2` (500, 0), `cpqs1` (800, 0) | as 1347, in list order | as predicted; `elapsed_seconds` 0.004 |
| 1351a | `draw_polygon cpqt5` the rectangle; the person: LAYERS & MASTERS **+**, Add Layer dialog defaults (current glyph only), OK | — | a second layer `New Layer`, which FontLab made the active one (ELEMENTS empty) |
| 1351b | the person clicked `Regular` to make it active (see below why) | — | `Regular` active, the rectangle shown |
| 1351 | `cpqt5` ← `cpqs1` at (500, 0) | refused, nothing changed | as predicted: "a glyph that is not empty needs exactly one layer, the active one (it has ['New Layer', 'Regular'], active 'Regular')"; the text says "nothing was changed" twice |
| 1352 | `create_glyph cpqx1` (`font.update()` ran); `get_glyph_outline` `cpqt1`–`cpqt5` | all unchanged, the brushes still brush, `verified` | as predicted: every read `verified`, the old elements first, then the components in order, each `source_in_step` true; `cpqt3` and `cpqt4` brushes `is_composite` true, `is_component` false (63 and 33 nodes); `cpqt5` the rectangle only; widths 0 |

`finish_changes`: 19 changes. The code ([glyphbridge_fontlab_mcp_listener.py](../glyphbridge_fontlab_mcp_listener.py) `add_component`) tells empty from not empty by the active layer only, and the empty route does not count layers; 1353 ran that case ([WATCH-POINTS.md](WATCH-POINTS.md)).

| # | Step | Predicted | Result |
|---|---|---|---|
| — | the person clicked `New Layer` in `cpqt5` | — | `New Layer` active, ELEMENTS empty, the grid thumbnail empty |
| 1353 | `cpqt5` ← `cpqs1` at (500, 0) | `placement` "empty layer", `placed` and `verified` true, the component on `New Layer` (75 %); else a refusal | **partly as predicted**: the empty route ran (`steps_done` recipe … recipe_cleared) and wrote, but `placed` false, failed check `one_component`, though `elements_after` listed one component of `cpqs1` at (500, 0); no mark; `cleanup` empty; nothing restored |
| 1353a | `get_glyph_outline cpqt5` (`New Layer` active) | only the component | as predicted, but its `component_layer` is **`New Layer`**, which `cpqs1` lacks (as TL 1283); status `verified`, `source_in_step` "unknown" |
| 1353b | the person clicked `Regular`; read | the rectangle only | as predicted, `verified`; the panel read `New Layer` "1 component"; the grid thumbnail showed the rectangle and the triangle (seen once) |

Reading (one run): a glyph whose active layer is empty beside a full one takes the empty route; the build names the active layer as the source's layer, so the check fails, though under the name `one_component`; the read calls such a glyph `verified`. `finish_changes`: 1 change. `cpqt5`'s component on `New Layer` is left in place. Not run: a failure partway and its restore, the list form's refusals on a non-empty target, two fonts.

### NB2 series: the one-layer rule, live (2026-11-18, listener 0.187 / server 0.74, FontLab 8.9.5 in Demo mode, through a NEW Claude Code session after a listener restart and a full Claude Desktop restart, with the 0.74 tool description; the NB font `Unnamed`, one font open; one run each; no File > Save stage, nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1354 | `fontlab_status`; `list_glyphs`; `get_glyph_outline cpqt5` (`Regular` active since 1353b) | 0.74 / 0.187; 9 glyphs; the rectangle only, `verified`, width 0 | as predicted |
| 1355 | `cpqt5` ← `cpqs1` at (500, 0), `Regular` active; read | refused, nothing changed, "nothing was changed" once | as predicted: "Glyph 'cpqt5': nothing was changed: add_component needs a glyph with exactly one layer, the active one (it has ['New Layer', 'Regular'], active 'Regular')"; the rectangle unchanged, `verified` |
| — | the person clicked `New Layer` in `cpqt5` | — | `New Layer` active, "1 component"; ELEMENTS `cpqs1` Δ=(500,0) |
| 1356 | the same call, `New Layer` active; read | refused, the same text with "active 'New Layer'" | as predicted; the 1353 component only, `component_layer` `New Layer`, `verified`, `source_in_step` "unknown" |
| 1357 | `cpqx1` (empty, one layer) ← `cpqs2` at (0, 0) | `placement` "empty layer", `placed`, `verified`, width 0; `width_set_by_build` 500 (a guess) | as predicted, marked, but no `width_set_by_build`: the build left the width at 0, which is `cpqs2`'s advance (as 1254, 1255) |
| 1358 | `cpqt1` (the rectangle, `cpqs1` (500, 0)) ← `cpqs2` at (800, 0) | `placement` "temporary layer", `placed`, `verified`, `existing_kept`, width 0 | as predicted, marked |
| 1358a | read `cpqx1`, `cpqt1` | both `verified`, the components naming `Regular` | as predicted: `cpqx1` `cpqs2` at (0, 0); `cpqt1` the rectangle, `cpqs1` (500, 0), `cpqs2` (800, 0), each `source_in_step` true; widths 0 |

Reading (one run): the one-layer rule refuses a glyph with two layers, whichever is active, before any change; one-layer targets, empty and not, still take their routes. `finish_changes`: 2 changes. `cpqt5`'s component on `New Layer` is kept (the user's choice). Not run: the list form under 0.187, the auto-layer refusal, the restore after a failure, two fonts.

### NB3 series: the list form under the one-layer rule, live (2026-11-18, the same session, font and versions as NB2; one run each; no File > Save stage, nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1359 | `create_glyph` `cpqx2`, `cpqs_u`; `draw_polygon cpqs_u` the triangle (100,0) (300,0) (200,300); read `cpqt5` (`New Layer` active) | created, layer `Regular`; `verified`; `cpqt5` keeps its component (70 %) | as predicted; `cpqt5` unchanged after two `font.update()` calls with `New Layer` active |
| 1360 | list form, `cpqx2` (empty, one layer) ← `cpqs1` (0, 0), `cpqs2` (300, 0) | `placement` "empty layer", `placed`, `verified`, width 0 | as predicted; `width_set_by_build` 500, written back to 0 (a build of several glyphs sets 500, as 1110–1172; one glyph, the source's advance, as 1254, 1255, 1357) |
| 1361 | list form, `cpqx1` (`cpqs2` at (0, 0)) ← `cpqs1` (200, 0), `cpqs1` (600, 0) | `placement` "temporary layer", `placed`, `verified`, `existing_kept`, width 0 | as predicted, the repeated source placed twice |
| 1362 | list form, `cpqt5` (two layers, `New Layer` active) ← `cpqs1` (0, 0), `cpqs2` (300, 0) | the one-layer refusal, nothing changed | as predicted, the text of 1356 |
| 1363 | list form, `cpqt1` (one layer, content) ← `cpqs_u` (0, 0), `cpqs2` (0, 0) | the underscore refusal, nothing changed | as predicted; the text still advises the single form "into an empty glyph", though the single form places into a glyph with content since 0.186 (an underscore name there untested) |
| 1363a | read `cpqx1`, `cpqx2`, `cpqt1`, `cpqt5` | all `verified`; placed or unchanged | as predicted, every component naming `Regular` and `source_in_step` true, but `cpqt5`'s (`New Layer`, "unknown") |

Reading (one run): the list form follows the one-layer rule on both routes; its refusals on a target with content change nothing. `finish_changes`: 5 changes. The auto-layer refusal was skipped (the user's choice: its GUI step is not recorded). Not run: the restore after a failure, two fonts.

### KG series: kerning groups, the master's group container read as plain data (2026-11-19, listener 0.188 / server 0.74, FontLab 8.9.5 in Demo mode, through Claude Code; probe `/debug/trykerngroups`, requests sent straight to the listener after the build approval of 0.188; `create_font` without a family, one font open, `Unnamed`; prefix `kgt`; the classes made by the user in the Classes panel; one run each; no File > Save stage, nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1364 | `create_font`; `create_glyph` `kgt1`–`kgt8` | a new font, each glyph with layer `Regular` | as predicted |
| 1365 | `stage=tuples&contains=kgt1`, no class yet | `count` 0, sizes unchanged | `fgKerningGroups`, `values()` a list, `count` 0; table 0 → 0, groups 0 → 0 |
| 1366 | the user makes `kgtL` (Kerning Left) {kgt1, kgt2}; `stage=glyph&name=kgt1` | `kerningLeft` an id, `kerningRight` 0 | 5121 / 0 |
| 1367 | `kgtR` (Kerning Right) {kgt3, kgt4}; `stage=glyph&name=kgt3` | 0 / a new id | 0 / 5122 |
| 1368 | `kgtB` (Kerning both) {kgt5, kgt6}; `stage=glyph&name=kgt5` | one id on both sides | 5123 / 5123 |
| 1369 | `kgtF` (OpenType) {kgt7, kgt8}; `stage=all&contains=kgt1,kgt3,kgt5` | `count` 4, `kern_groups` 3; the three kerning groups with their ids and members | as predicted |
| 1370 | `stage=tuples&contains=kgt1,kgt3,kgt5` | `count` 3, each a 2-field tuple (members, side mode), for example `KernLeftGroupMode` | `count` 3, `shapes` {`tuple/2`: 3}: `(['kgt1', 'kgt2'], 'KernLeft')`, `(['kgt5', 'kgt6'], 'KernBothSide')`, `(['kgt3', 'kgt4'], 'KernRight')`, in that order; no group name; the side strings not as guessed |
| 1371 | `stage=glyph&name=kgt7` | 0 / 0 | 0 / 0 |
| 1372 | `stage=all&contains=kgtF` | one entry, kerning-group flag false | false, id **5125** (5124 skipped) |
| 1373 | names only, listener 0.188: `/debug/moddir?module=fontgate&name=fgKerningGroups&members=items,keys,values,asDict,has_key` | `items()` documented as (name, (members, side)) pairs | as predicted: `list( tuple('groupName', tuple( list('glyphName'), mode ) ) items()`; `values()` `list ( tuple( list('glyphName'), mode ) )`, `keys()` `list('groupName')`, `has_key('groupName')` bool, `asDict` "represent object as dictionary"; nothing called |
| 1374 | listener 0.189 (restarted, the same font): `stage=items&contains=kgtL,kgtR,kgtB` | `count` 3, `('kgtL', (['kgt1', 'kgt2'], 'KernLeft'))` and so on, no `kgtF`, sizes unchanged | as predicted: `kgtL`, `kgtB`, `kgtR` in that order (as `values()`), `shapes` {`tuple/2`: 3}; table 0 → 0, groups 3 → 3 |
| 1375 | `stage=items&contains=kgt5` (a member) | only `kgtB` | as predicted |

Reading (one run): the modern container gives each kerning group's members and side, but no name, and leaves the OpenType class out; `getAllGroups()` gives names, ids, members and the kerning flag; the legacy ids agree with both. No read changed the table or the groups. `finish_changes`: 9 changes. Seen by the user, no probe involved in it: the Classes panel's footer read "3 classes" with four listed, until its filter was switched to one class and back to All classes; three glyph reads (1366–1368) had run between the class edits. Facts: [topics/kerning.md](topics/kerning.md) §9.10. The font `Unnamed` holds `kgt1`–`kgt8` (empty) and the four classes, no pairs; 8 of 10 probe calls used in the 0.188 run, 2 in the 0.189 run (1374, 1375). 1373–1375: `items()` gives each kerning group's name, members and side in one modern call.

### KGL series: `get_kerning_groups` live (2026-11-19, listener 0.190 / server 0.75, FontLab 8.9.5 in Demo mode, through Claude Code, a new session; the KG font `Unnamed`, one font open, one master; one run each; reads only, no File > Save stage, nothing changed by a tool)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1376 | `all_groups` | 3 groups, all `confirmed`: `kgtL` `left` {kgt1, kgt2} 5121, `kgtR` `right` {kgt3, kgt4} 5122, `kgtB` `both` {kgt5, kgt6} 5123; no `kgtF` | as predicted, in the order `kgtL`, `kgtB`, `kgtR` (as 1374); `cross_check` done |
| 1377 | `groups` `kgtL`, `kgtX`, `kgtF` | `kgtL` as 1376; `kgtX` an error (no such group); `kgtF` its own error (a class, not a kerning group); `errors` 2 | as predicted |
| 1378 | `glyphs` `kgt5`, `kgt7` | `kgt5` in `kgtB` (`both`); `kgt7` an empty list with a note, no error | as predicted: note "in no kerning group on either side", `errors` 0 |
| 1379 | the user removes `kgt2` from `kgtL` in the Classes panel (panel: size 1); no listener restart; `groups` `kgtL` with `glyphs` `kgt2` | `kgtL` {kgt1}, id 5121, `confirmed`; `kgt2` in no group | as predicted |

Reading (one run): the tool reads every kerning group, named groups and glyphs as designed, keeps its two errors to their names, and sees a Classes-panel edit at once. FontLab's OUTPUT panel logged the reads as `kerning groups 3` before 1379. Not run live: the 250-group approval, a group with `confirmed` false, several fonts open, the Claude Desktop chat. The font `Unnamed` now holds `kgtL` = {kgt1}; the rest as after KG.

### KD series: removing one kerning pair (2026-11-19, FontLab 8.9.5 in Demo mode, through Claude Code; no File > Save stage)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1380 | names only, listener 0.190: `/debug/moddir?module=fontgate&name=fgKerning&members=remove,has_key,set,get&doc=600` | `remove` without a docstring | as predicted: `remove` `null`; `has_key(fgKerningObjectPair)`; `get` and `set` take an `fgKerningObjectPair` or `tuple('name1', 'name2')`; public names as in 148b; nothing called |
| 1381 | listener 0.191 (restarted), the KG font closed; `create_font`; `create_glyph` `kd1L`, `kd1R`, `kd1S` | `Unnamed`, one font; each glyph with layer `Regular` | as predicted |
| 1382 | `set_kerning` `kd1L:kd1R` -100, `kd1R:kd1L` +20 | both set, table 0 → 2, mark and refresh | as predicted |
| 1383 | `/debug/trydelkern?a=kd1L&b=kd1R&form=tuple&go=yes` | no error, returns `None`, -100.0 → `None`, `len` 2 → 1, `removed` true | removed as predicted; **wrong: `remove` returned `True`** (a bool) |
| 1384 | `get_kerning` both pairs | `kd1L:kd1R` 0 `none`, `kd1R:kd1L` +20, `table_size` 1 | as predicted |
| 1385 | the KERNING panel, no refresh | both rows still listed | as predicted: both rows, footer 2 |
| 1386 | `/debug/trynotify?stage=call&which=package_content&name=kd1L&on=class&id_from=fg&go=yes` | no error; only `kd1R kd1L 20` | as predicted: `notifyPackageContentUpdated(16)`, `None`, no flag changed; the panel one row, footer 1 |
| 1387 | `form=flags` on `kd1R:kd1L` | removed, `len` 1 → 0, returns `True` | removed as predicted; **wrong: returned `None`** |
| 1388 | `form=flags` on `kd1L:kd1S`, no entry | nothing changes, `removed` false | as predicted: no error, `None`, `len` 0 → 0 |
| 1389 | control: `set_kerning` `kd1R:kd1L` +20 (the state of 1387 again) | set, table 0 → 1 | as predicted |
| 1390 | `form=tuple` on `kd1R:kd1L` (only the form differs from 1387) | `True` if the form decides | as predicted: removed, `len` 1 → 0, returned `True` |

Reading (one run each): `remove` deletes exactly one glyph : glyph entry in both forms (1383, 1387, 1390), unlike a 0, which leaves an explicit entry; on a pair with no entry it changes nothing and raises nothing (1388). Its return value follows the form, `True` for the tuple, `None` for the flags form (1387 against 1390), never the outcome: only the re-read confirms. The KERNING panel keeps a removed row until `notifyPackageContentUpdated` (1385, 1386). Not checked: the save question for a removal alone (the font was already marked by the setup, and Demo mode cannot save to clear it), Edit > Undo, a pair over a class, other masters, several fonts. Probe calls: 4 of 10. The font `Unnamed` holds `kd1L`, `kd1R`, `kd1S` and an empty table; the panel was not refreshed after 1390.

### KDC series: removing a glyph : glyph exception over a class (2026-11-19, listener 0.191 / server 0.75, the KD font, one master, one font open; one run each; no File > Save stage)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1391 | the user makes the class `kdcL` (Kerning Left) {kd1L, kd1S} in the Classes panel; `get_kerning_groups` `groups` `kdcL`, `glyphs` `kd1L`, `kd1S` | both in `kdcL`, `left`, `confirmed` | as predicted, id 5130. Seen: the KERNING panel's stale `kd1R kd1L 20` row (left by 1390) was gone after the class edit, footer 0 (not isolated) |
| — | setup: `draw_polygon` (0,0)–(500,500) and `set_glyph_width` 500 on `kd1L`, `kd1R`, `kd1S`, each verified (the empty glyphs could not be clicked with the Kerning tool) | — | — |
| 1392 | the user: glyph window `/kd1L/kd1R`, Kerning tool, the right glyph, Left arrow once (a class pair at -1), then -80 in the KERNING panel (the panel has no command to add a pair) | — | the panel lists `kdcL` (2) `kd1R` -80, footer 1 |
| 1393 | `get_kerning` `kd1L:kd1R`, `kd1S:kd1R` | both -80 `class : glyph` (`kdcL`), `table_size` 1 | as predicted |
| 1394 | `set_kerning` `kd1L:kd1R` -50 | set, `exception_over_class` true, table 1 → 2 | as predicted |
| 1395 | `/debug/trydelkern?a=kd1L&b=kd1R&form=flags&go=yes` | the exception removed, `len` 2 → 1, the class pair untouched | as predicted: -50.0 → `None`, `removed` true, returned `None` |
| 1396 | `get_kerning` both pairs | `kd1L:kd1R` -80 `class : glyph` again, `table_size` 1 | as predicted |
| 1397 | `/debug/trynotify` `package_content` (`notifyPackageContentUpdated(16)`); the KERNING panel | no error; only the class row | as predicted: footer 1, no exception row; the kerning bar `kdcL -80 kd1R` |

Reading (one run): removing a glyph : glyph exception takes out only that entry, and FontLab then applies the class value again; the panel shows the class row after the refresh. Probe calls: 5 of 10. The font `Unnamed` holds `kd1L`, `kd1R`, `kd1S` (boxes, width 500), the class `kdcL` {kd1L, kd1S} and the class pair `kdcL : kd1R` -80.

### RK series: `remove_kerning` live (2026-11-19, listener 0.192 / server 0.76, FontLab 8.9.5 in Demo mode, through a NEW Claude Code session with the 0.76 tool description; the KD font `Unnamed`, one font open, one master; one run each; no File > Save stage, nothing saved)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1398 | `fontlab_status`; `get_kerning` `kd1L:kd1R`, `kd1S:kd1R`, `kd1R:kd1L`; `get_kerning_groups` `kdcL` | -80 `class : glyph` (`kdcL`) twice, `none`, `table_size` 1; `kdcL` left {kd1L, kd1S} | as predicted (the exception had gone in 1395); `kdcL` id 5130, `confirmed` |
| 1399 | setup: `set_kerning` `kd1L:kd1R` -50 | before -80 `class : glyph`, after -50 `glyph : glyph`, `exception_over_class`, table 1 → 2, mark and refresh | as predicted; mark via `kd1L` |
| 1400 | `remove_kerning` `kd1L:kd1R`, `kd1S:kd1R`, `kd1R:kd1L` | the first `removed`, -50 `glyph : glyph` → -80 `class : glyph`, `class_value_applies`; the second `no entry`, its note naming `kdcL` -80; the third `no entry`, a plain note; table 2 → 1; mark and refresh | as predicted: `removed_count` 1, `no_entry_count` 2; mark via `kd1L`, `glyph_has_changes` true; refresh called |
| 1401 | `get_kerning` the same three pairs | -80, -80 `class : glyph`, `none`, `table_size` 1 | as predicted |
| 1402 | the user's screenshot: KERNING panel, kerning bar, OUTPUT, the font tab | only the class row; the removed row gone at once; the changed icon blue | the panel `kdcL` (2) `kd1R` -80, footer 1; the bar `kdcL -80 kd1R`; OUTPUT `kerning remove 3 pairs: 1 removed, 2 had no entry (verified)`. The tab icon looked changed, but 1399 had already marked the font, so this says nothing about a removal alone |

Reading (one run): the product tool removes a glyph : glyph exception over a class, reports the class value that applies again, reports pairs with no entry without stopping the others, and the KERNING panel follows at once. Not checked: the save question for a removal alone (needs a save to clear the mark first; not possible in Demo mode), Edit > Undo, other masters, several fonts, the 250-pair approval (stub only). The font `Unnamed` holds `kd1L`, `kd1R`, `kd1S` (boxes, width 500), the class `kdcL` {kd1L, kd1S} and the class pair `kdcL : kd1R` -80, as after 1397.

### CW series: writing and removing class entries by probe (2026-11-20, listener 0.193 / server 0.77, FontLab 8.9.5 in Demo mode, through Claude Code; one master, one font open; one run each; no File > Save stage, nothing saved)

**Setup (unnumbered, as predicted):** no font open (`fontlab_status` 0.77 / 0.193); `create_font` `Unnamed`; `create_glyph` `cw1a`–`cw1f`, each with layer `Regular`; `draw_polygon` [[0,0],[500,0],[500,500],[0,500]] and `set_glyph_width` 500 on each, all `verified`. The user then made three classes in the Classes panel: `cwL` Kerning Left {cw1a, cw1b}, `cwR` Kerning Right {cw1c, cw1d}, `cwB` Kerning both {cw1e}. All predictions were written in chat before each call.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1409 | `get_kerning_groups` `all_groups`; `get_kerning` `cw1a:cw1c` | 3 groups `confirmed`, left / right / both; 0 `none`, `table_size` 0 | as predicted; ids `cwL` 5119, `cwR` 5120, `cwB` 5121 |
| 1410 | `/debug/trysetkern?a=cwL&b=cwR&left=class&right=class&form=flags&value=-80&go=yes` | returns `None`, `((cwL, True), (cwR, True))` `None` → -80.0, `len` 0 → 1, groups 3 → 3, both classes `confirmed` | as predicted |
| 1411 | `get_kerning` `cw1a:cw1c`, `cw1b:cw1d`, `cw1a:cw1e` | -80 `class : class` (`cwL` / `cwR`) twice; 0 `none`; `table_size` 1 | as predicted |
| 1412 | the user: the KERNING panel; a glyph window, text `/cw1a/cw1c/cw1b/cw1d` | no panel row; `cw1c` and `cw1d` each 80 units into their left neighbour, `cw1c` / `cw1b` edge to edge | as predicted: panel empty, footer 0; measured on the ruler in the screenshot: `cw1c` starts at ≈ 422, the seam at ≈ 921, the line ends at ≈ 1843 (predicted 420, 920, 1840; unkerned 2000) |
| 1413 | probe `a=cw1a&b=cwR&right=class`, -50; `get_kerning` `cw1a:cw1c`, `cw1b:cw1c` | `((cw1a, False), (cwR, True))` `None` → -50.0, `len` 1 → 2; -50 `glyph : class` (`cwR`); -80 `class : class` | as predicted; `cw1a:cw1d` also -50 `glyph : class` (not predicted, follows from the entry) |
| 1414 | probe `a=cwL&b=cw1d&left=class`, -30; `get_kerning` `cw1b:cw1d`, `cw1a:cw1d`, `cw1b:cw1c` | `len` 2 → 3; -30 `class : glyph` (`cwL`); -50 `glyph : class` (it outranks class : glyph); -80 | as predicted |
| 1415 | probe `a=cwB&b=cwB&left=class&right=class`, -20; `get_kerning` `cw1e:cw1e`, `cw1d:cw1e` | `len` 3 → 4; -20 `class : class` (`cwB` / `cwB`); 0 `none` | as predicted |
| 1415a | the user: text `/cw1a/cw1c/cw1b/cw1d/cw1e/cw1e` | boxes start at 0, 450, 950, 1420, 1920, 2400; the line ends at 2900 (unkerned 3000) | as predicted within a few units (≈ 450, 946, 1435, 1914, 2402, 2893), measured on the ruler in the screenshot |
| 1416 | `/debug/trydelkern?a=cwL&b=cwR&left=class&right=class&form=flags&go=yes`; `get_kerning` `cw1b:cw1c`, `cw1a:cw1c`, `cw1b:cw1d` | returns `None`, -80.0 → `None`, `removed` true, `len` 4 → 3; 0 `none`, -50, -30 | as predicted |
| 1417 | `/debug/trynotify?stage=call&which=package_content&on=class&id_from=fg&name=cw1a&go=yes`; the KERNING panel | no error; 3 rows: `cw1a` `cwR` -50, `cwL` `cw1d` -30, `cwB` `cwB` -20; class labels not predicted | as predicted: `notifyPackageContentUpdated(5)`, `None`, no flag changed; footer 3; a class shows in bold with a class marker and its member count (`cwL` 2, `cwR` 2; `cwB`, one member, no count) |
| 1418, 1419 | the mark after a class write alone; the save question on close | — | **not run**: the setup's glyph writes had already marked the font, and clearing the mark needs a save (Demo mode) |

Reading (one run each): `set` and `remove` with a `True` flag on a side write and remove a real class entry of each kind, which FontLab applies to every member, on screen too (1412, 1415a); `set` and `remove` return `None` in the flags form, so only the re-read confirms; the group container did not change (`len` 3 throughout). The KERNING panel lists class entries only after `notifyPackageContentUpdated`, as for glyph pairs. Not checked: the mark and the save question for a class write alone, Edit > Undo, whole-unit rounding of a class value, other masters, several fonts. Probe calls: `trysetkern` 4 of 10, `trydelkern` 1 of 10, `trynotify` `package_content` 1 of 3. The font `Unnamed` (unsaved) holds `cw1a`–`cw1f` (boxes, width 500), the classes above and the entries `cw1a : cwR` -50, `cwL : cw1d` -30, `cwB : cwB` -20.

### CK series: class kerning in `set_kerning` and `remove_kerning` live (2026-11-20, listener 0.194 / server 0.78, FontLab 8.9.5 in Demo mode, through Claude Code; one master, one font open; one run each; no File > Save stage, nothing saved)

**Setup:** none. The CW font `Unnamed` (unsaved, still open; its contents at the end of CW above) was reused; `list_glyphs` and `get_kerning_groups` `all_groups` read it first (unnumbered): `.notdef`, `cw1a`–`cw1f`; `cwL` left {cw1a, cw1b}, `cwR` right {cw1c, cw1d}, `cwB` both {cw1e}, all `confirmed`. Only kerning was written, so no new glyph prefix. All predictions were written in chat before each call. A sample is the first member of each class side (§17 in [topics/kerning.md](topics/kerning.md)).

| # | Step | Predicted | Result |
|---|---|---|---|
| 1420 | `get_kerning` `cw1a:cw1c`, `cw1b:cw1c`, `cw1b:cw1d`, `cw1a:cw1d`, `cw1e:cw1e` | -50 `glyph : class` (`cwR`); 0 `none`; -30 `class : glyph` (`cwL`); -50 `glyph : class`; -20 `class : class` (`cwB`); `table_size` 3 | as predicted |
| 1421 | `set_kerning` `@cwL : @cwR` -80 | `set`, `class : class`, `cwL` left 2, `cwR` right 2; sample `cw1a:cw1c` -50 `glyph : class` before and after, `covered`; `entry_before` null; 3 → 4; mark and panel refresh called | as predicted; mark via `cw1a` |
| 1422 | `get_kerning` `cw1b:cw1c`, `cw1a:cw1c` | -80 `class : class` (`cwL` / `cwR`); -50 `glyph : class` | as predicted |
| 1423 | `set_kerning` `@cwB : @cwB` -25 | sample `cw1e:cw1e` -20 → -25 `class : class`, `applied`; `entry_before` -20; 4 → 4 | as predicted |
| 1424 | `set_kerning` `cw1b : @cwR` -60 | `glyph : class`; sample `cw1b:cw1c` -80 `class : class` → -60 `glyph : class`, `applied`; `entry_before` null; 4 → 5 | as predicted |
| 1425 | `set_kerning` `cw1f : cw1e` -10 and `@cwB : cw1a` -15, one call | the glyph pair 0 `none` → -10 `glyph : glyph`, no `exception_over_class`; the class pair `class : glyph`, sample `cw1e:cw1a` 0 → -15, `applied`; 5 → 7, `set_count` 2 | as predicted |
| 1426 | `set_kerning` `@cwR : cw1a` -10 | refused before any change: `cwR` is a right group | as predicted: "the kerning group '@cwR' is a right group, so it cannot stand on the left side of a pair; nothing was set" |
| 1427 | `set_kerning` `@cwX : cw1c` -10 | refused: not the name of any kerning group | as predicted |
| 1428 | `set_kerning` `@cwB : @cwB` -99 then `@cwR : cw1a` -10, one call; `get_kerning` `cw1e:cw1e` | the whole call refused (the second pair); -25 unchanged, `table_size` 7 | as predicted |
| 1429 | `remove_kerning` `@cwL : @cwR` | `removed`, `entry_before` -80; sample `cw1a:cw1c` -50 `glyph : class` before and after, `class_value_applies` true; 7 → 6 | as predicted |
| 1430 | the same removal again | `no entry` with a note; nothing changed; 6; no mark, no panel refresh | as predicted; note "no class : class entry for @cwL:@cwR …"; but the reply's general `agent_instruction` says such a pair "had no glyph : glyph entry" ([WATCH-POINTS.md](WATCH-POINTS.md)) |
| 1431 | `remove_kerning` `cw1a : @cwR` | `removed`, `entry_before` -50; sample -50 → 0 `none`; `class_value_applies` false; 6 → 5 | as predicted, except that `class_value_applies` is absent: the server adds it only when true (the code, as for glyph pairs), so the prediction's form was wrong |
| 1432 | the user: the KERNING panel | 5 rows: `cw1b` `cwR` -60, `cwL` `cw1d` -30, `cwB` `cwB` -25, `cw1f` `cw1e` -10, `cwB` `cw1a` -15; footer 5 | as predicted (screenshot); class labels as in 1417 |
| 1432a | the user: text `/cw1b/cw1c/cw1e/cw1a` | boxes start at 0, 440, 940, 1425; the line ends at 1925 (unkerned 2000) | as predicted within a few units (≈ 438, 936, 1430; end ≈ 1922), measured on the ruler in the screenshot; FontLab's OUTPUT panel logged the refusals and removals |

Reading (one run each): the product tools write, overwrite and remove class entries of each kind, verified by the exact entry and one sample pair, with both verdicts `covered` and `applied` seen; a refusal for a class side changes nothing, also when a valid pair comes first; the KERNING panel and a text line agree. `finish_changes` counted 6 changes. Not checked: the mark and save question for a class write alone (Demo mode), Edit > Undo, other masters, several fonts, an OpenType class or a glyph named like a group as a side, `no sample`, a listener older than 0.194. The font `Unnamed` (unsaved) now holds the entries `cw1b : cwR` -60, `cwL : cw1d` -30, `cwB : cwB` -25, `cw1f : cw1e` -10, `cwB : cw1a` -15.

### CK2 series: a class pair's own rules in the general instructions and the OUTPUT line (2026-11-20, listener 0.195 / server 0.79, FontLab 8.9.5 in Demo mode, through Claude Code; one master, one font open; one run each; no File > Save stage, nothing saved)

**Setup:** none. After the build the user restarted the listener and Claude Desktop; `fontlab_status` in the same Claude Code session reported server 0.79 / listener 0.195 and the CK font `Unnamed` (its contents at the end of CK above). 0.79 changed only reply text, no tool description or parameter, so the session's loaded tool definitions did not matter. All predictions were written in chat before each call.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1433 | `get_kerning` `cw1b:cw1c`, `cw1a:cw1c`, `cw1e:cw1a` | -60 `glyph : class` (`cwR`); 0 `none`; -15 `class : glyph` (`cwB`); `table_size` 5 | as predicted |
| 1434 | `remove_kerning` `@cwL : @cwR` (no entry) | `no entry`, note "no class : class entry for @cwL:@cwR, so nothing was removed; the sample pair cw1a:cw1c kerns at 0 (none)"; the instruction says "had no entry of its kind, so" and "to restore a glyph pair, call set_kerning with its 'before' value; a class pair: see below.", without "had no glyph : glyph entry"; 5 → 5; no mark, no panel refresh | as predicted |
| 1435 | control: `remove_kerning` `cw1a : cw1c` (no entry) | note "no glyph : glyph entry and no class kerns this pair, so there was nothing to remove"; the instruction keeps "had no glyph : glyph entry, so" and "to restore one, call set_kerning", no "see below"; 5 → 5 | as predicted |
| 1436 | `set_kerning` `@cwL : @cwR` -70 | `set`, `class : class`; sample `cw1a:cw1c` 0 `none` → -70, `applied`; `entry_before` null; 5 → 6; the instruction says "to revert a glyph pair, if 'before' was" and "restore the prior state; a class pair: see below." | as predicted; mark via `cw1a`, panel refresh called |
| 1436a | the user: FontLab's OUTPUT panel | "kerning remove @cwL:@cwR: no class : class entry, nothing removed"; "kerning remove cw1a:cw1c: no glyph : glyph entry, nothing removed"; one line for 1436 with -70 (its wording not predicted) | as predicted (screenshot): the listener started as v0.195, and 1436 logged "kerning @cwL:@cwR: 0 -> -70 (verified)" |

Reading (one run each): a reply with a class side now names the class pair's own rules in its general instruction, and the OUTPUT line names the pair's kind; a glyph-only reply is unchanged word for word (1435). `finish_changes` counted 1 change. The font `Unnamed` (unsaved) now holds the entries `cw1b : cwR` -60, `cwL : cw1d` -30, `cwB : cwB` -25, `cw1f : cw1e` -10, `cwB : cw1a` -15, `cwL : cwR` -70.

### T-series (after the K-series unless the user chooses otherwise; the commands A2 / A3 are in [RUNBOOK.md](RUNBOOK.md): T3 ran as tests 256–258, T4 as 145a–c and 259)

| Id | Test | Stage / how | Expected | Status |
|---|---|---|---|---|
| **T1** | Deployment check through Claude Desktop (no PowerShell): `fontlab_status` | listener running, Claude Desktop FULLY restarted (same as K1) | `server_version` 0.31, `listener_version` 0.95, no `compatibility_note` | DONE 2026-11-01 together with K1 (see K1) |
| **T2** | Agent-level check of v0.89 through Claude Desktop (this also closes P3a, `finish_changes` live): ONE request such as "create a glyph, draw a rectangle, set the sidebearings, then tell me what you did" on a disposable font | glyphs named with a NEW prefix | the write replies show `fontlab_sync` and `synced_with_fontlab: true`; the agent does NOT ask for an editor tab; the chat ends with ONE bold "You must save..." line from `finish_changes`; a read-only request gives none; no extra FontLab dialog | DONE 2026-11-03 (listener 0.110, server 0.36, FontLab 8.9.5), a new font from File > New Font (`Unnamed Regular`, only `.notdef`), a new Claude Desktop chat. **253**: "In the open font, create a glyph named `t2a`, draw a rectangle from (100, 0) to (400, 700) in it, set its sidebearings to 50 left and 50 right, then tell me what you did." OUTPUT: `create t2a: created (verified, glyphs 1 -> 2)`, `draw t2a: 1 contour, 4 points (verified)`, `sidebearings t2a: L 50, R 50 (verified)`; no "unsynced" word, which the log always prints, so synced is inferred, not seen in the replies. The agent reported no Unicode, x 50..350 and width 400, said it read the values back, did not ask for an editor tab, and ended with the reminder once, in bold, after its summary. No dialog (no `.notdef` notice: the agent did not call `get_current_font`). `finish_changes` and its count were not seen (server-only); the exact reminder text implies the call. **254**, same chat, "What is the advance width of `t2a`?": 400 and no reminder, but **no read**: the agent answered from the sidebearings reply and said so; no `width` line in OUTPUT long after the 10 s flush (predicted wrongly: a `get_glyph_width` call). **254b**, "Please read the advance width of `t2a` from FontLab now.": OUTPUT `reads: width 1`, 400, no reminder. The user had opened panels and menus before 254b, no effect seen. **255**, `t2a` selected with one click: FontLab's bottom bar LSB 50, width 400, RSB 50; the Elements panel one contour, 4 nodes |
| **T3** (highest value) | The ORIGINAL stale scenario with the sync: a glyph whose editor tab is OPEN while the API writes sidebearings (Appendix A, 144a / 144b) | disposable font open; 144a, then ONE GUI action (open `opn91a` in an editor tab, leave it open), then 144b | `set_glyph_sidebearings` reply `synced_with_fontlab: true`; the outline read right after shows `margins_agree: true`, x 20..420, no `modern_outline`. If `margins_agree: false` appears, the fallback (0.88) answers correctly and `Update` does not refresh an open editor's glyph: record it; then also read whether closing and reopening the tab changes anything | DONE 2026-11-03 (listener 0.110, server 0.36, FontLab 8.9.5), the `Unnamed` font of T2, glyph `t3a`; writes through the tools, reads at the listener. **256**: `create_glyph t3a` (Unicode none), `draw_polygon` [[0,0],[400,0],[400,300],[0,300]]: `verified`, `synced_with_fontlab: true`, `fontlab_sync.synced: true`; advance width 0 (left 0, right -400: what `create_glyph` leaves; not predicted, harmless); `/glyph/outline` x 0..400, `agree` and `margins_agree` true. Then ONE GUI action: the user double-clicked `t3a` and left the editor tab open (panel 0 / -400 / 0). **257**, tab open: outline before unchanged; `set_glyph_sidebearings(20, 30)`: `verified`, `synced_with_fontlab: true`, `fontlab_sync.synced: true`, advance 0 -> 450; the outline right after: legacy nodes x **20..420**, `margins_agree: true`, **no `modern_outline`**; `/glyph/sidebearings` 20 / 30 / 450; `/debug/trymodern?stage=state`: legacy and modern 1 shape, 4 nodes, width 450 on both, verdict `synced`. **258**, the user's screenshot of the open tab: the outline moved (left edge at 20, advance line at 450, `30` label); the metrics panel still showed 0 / -400 / 0 (display lag, §8f). `finish_changes`: 3 changes, 0 uncertain. So `Update` keeps the legacy view fresh with the editor tab open; the 0.88 fallback was not needed. Not covered: other writes with the tab open, several layers, what refreshes the panel |
| **T4** | Width and sidebearings on an EXISTING glyph with legacy layers of a real font (Appendix A, 145; `testglyph2` of `savedtestfont.vfc`, then optionally `A`, the Power Brush composite) | disposable font opened from the file, nothing saved | each write reply `synced: true`; legacy margins equal the modern ones; node shift equals the requested sidebearing change; `A` unchanged except for the translation (compare with FontLab's numbers). Never save | DONE 2026-11-03 for `testglyph2` (listener 0.110, FontLab 8.9.5), `savedtestfont.vfc` opened from its file, requests sent straight to the listener, one write per stage. **145a**, read: LSB 102.15479625533814, RSB 117, advance 500, ink 280.845, 7 nodes, first node (128, 414), one legacy layer `test_font`, `margins_agree` true, verdict `synced`: as test 143. **145b**, width 560: `set: true`, `synced: true`, advance 560, RSB 177, LSB and every node unchanged, legacy width = modern advance; `updated_fg_glyphs` went from 0 to 4 ids (not predicted, unexplained). **145c**, sidebearings 50 / 60: every node moved by a whole **−52** in x (predicted −52.1548), y unchanged; LSB 50.1548, RSB 60, advance 391 (predicted 50 / 60 / 390.845); the reply said `set: false`, `changed: true`, `lsb_ok` and `advance_ok` false, with its reason (honest, no false success); `synced: true`, `margins_agree` true, legacy width = modern advance = 391. **259**, `testglyph2` selected with one click: FontLab's bottom bar LSB 50, width 391, RSB 60. **145d**, `A` read: 54 nodes, one Power Brush shape (`is_composite: true`), identity transform, fractional coordinates; LSB 192.466, RSB 174.466, advance 639. **145e**, width 700: `set: true`, `synced: true`, RSB 235.466, LSB and all 54 nodes unchanged. **145f**, sidebearings 50 / 60: the raw nodes did NOT move; FontLab set the element transform to dx **−142.0** (exact shift −142.466); effective LSB 50.466, advance **383** (382.534 stored as 383), RSB 60.466; the reply `set: false`, `changed: true`, all three checks false, with its reason; `synced: true`, `margins_agree` true. **145g**, `--check --outline A`: `verified`, FontLab's own transform applied, box 50.466..322.534 equal to FontLab's, margins agree. **260**, `A` selected: the bottom bar LSB 50, width 383, RSB 60; the Elements panel shows Δ=(-142,0). So the shift is a whole unit (the fractions of `A` were kept); a plain contour has its nodes moved, a Power Brush shape gets an element transform. Open: whether the advance rounds to the nearest unit or up; a plain contour with fractional nodes |
| **T5** | Two fonts open (P0.5): which font is current and what `CurrentFont()` and the tools address after `flPackage()`; read-only probes first (`/debug/tryfont?stage=state`), then ONE gated step | two fonts open, nothing saved | decide the design of `create_font` and of "open" checks | PARTLY 2026-11-03, read-only part (listener 0.111, FontLab 8.9.5), `/debug/tryfont?stage=state`. **261**, `savedtestfont.vfc` only: `CountFonts` 1, one package; the current package's `name` is EMPTY (as predicted), so it cannot identify a font: listener 0.111 also reads its `path` and `fileName`. **262**, the user opened Arial as well, the test font's window in front: `CountFonts` 2, `packages()` a `list` of 2; `CurrentFont()` and the current package both the test font (package `path` = the `.vfc` path, `fileName` `savedtestfont.xfo`). **263**, after ONE click on the Arial tab: both Arial (`path` `:/Arial: Normal`, `fileName` `Arial: Normal.xfo`, 4651 glyphs). **264**, after ONE click back: both the test font again. Arial is listed first in the Fonts panel, so being opened last does not decide. **265–268**, listener 0.112 / server 0.37, through the tools: **265** `fontlab_status` 0.37 / 0.112, Arial current; **266** Arial in front: A:V −152 (`glyph : glyph`), T:o −227 (`glyph : class`, right class `e`), `fonts_open` 2, `matched_by` `path`, `family_name` Arial, as predicted; **267** after ONE click on the test font tab: `testfont`, master `test_font`, upm 1000, `table_size` 0; A:V and T:o answered `no glyph named …` errors (predicted 0 / `none`, wrongly: the font has no V, T, o); **267b** A:testglyph1: 0, `none`; **268** after File > New Font (3 fonts, the new one in front): refused, "the current font has no file path (a new, unsaved font)", nothing read. K12(c) answered (266, 267). **269–272**, listener 0.113 / server 0.38, FontLab restarted with no font open: **269** `fontlab_status` 0.38 / 0.113, `font_open` false, no font fields; **270** `savedtestfont.vfc` only: `get_glyph_width A` 639, `font` testfont Regular, `fonts_open` 1, no note; **271** Arial opened, in front: 1366, Arial Regular, 2, `font_changed` testfont Regular → Arial Regular, with the note; **272** ONE click on the test font tab: 639, testfont Regular, `font_changed` Arial Regular → testfont Regular; all as predicted. **273–281**, the write tools with two fonts open (listener 0.113 / server 0.38, through Claude Code, prefix `w5a_`): font A `savedtestfont.vfc` and font B, a copy made in Explorer (`savedtestfont-b.vfc`, also "testfont Regular"); FontLab showed both tabs as "fullname of test font", told apart only by their order. **273** B in front: `fontlab_status` `fonts_open` 2, `font_changed` "another font with the same name … from a different file"; **274–276** in B: `create_glyph w5a_one` (6 → 7 glyphs), `draw_polygon` 50–350 × 0–300 (`verified`, `synced`), `set_glyph_width` 0 → 500 (modern route, `synced`); **277** after ONE click on A's tab: `get_glyph_width w5a_one` "No glyph named", but as a bare error without font fields, and the next call (277b, `fontlab_status`) showed no `font_changed` either: a failed call swallows the switch note (not predicted; [topics/fonts-and-sync.md](topics/fonts-and-sync.md)); **278** in A: `w5a_two` created (6 → 7), drawn 0–200 × 0–400, sidebearings 50 / 50, width 300, all `verified`, FontLab's status bar 50 / 300 / 50; **279** ONE click back to B: `w5a_one` 500, outline `verified` (margins 50 / 150), with the switch note; `w5a_two` "No glyph named"; **280** in B: `set_glyph_unicode w5a_one` 57344, `font.update()` ran (no `display_refresh: skipped`), outline unchanged and `verified`; **281** ONE click on A: `w5a_two` outline `verified`, 50 / 300 / 50, with the switch note; `finish_changes` counted 7 changes across both fonts, one reminder. All as predicted except 277. Also seen: the `fontlab_status` reply carries the font's full file path. **282–284**, server 0.39 (the fix for 277), the same two fonts: **282** `fontlab_status` 0.39 / 0.113, A in front, `fonts_open` 2, no switch note (a new server process); **283** after ONE click on B's tab: `get_glyph_width w5b_missing` failed with "No glyph named …" followed by the font note with the switch ("another font with the same name … from a different file"); **284** `get_glyph_width w5a_one` 500, no `font_changed`; all as predicted. **285–290**, two new unsaved fonts (listener 0.113 / server 0.39, prefix `w6a_`, both saved fonts closed first): **285** File > New Font: `Unnamed Regular`, `fonts_open` 1, path null, and a `font_changed` from testfont (the server remembers the last font across a no-font call; not predicted); **286** `create_glyph w6a_one` (1 → 2); **287** a second File > New Font is named **"Unnamed1 Regular"** (predicted: the same name), so `get_glyph_width w6a_one` failed with the switch noticed by name; **288** `create_glyph w6a_two`, then `draw_path` REFUSED (a brand-new font's first layer is not created while several fonts are open, the stub-tested limit, seen live; nothing drawn); **288c** after the glyph was opened once in an editor tab: drawn, `verified`, ink 50–402.5; **289** one click on Unnamed: `w6a_two` "No glyph named", `w6a_one` width 0; **290** `delete_glyph w6a_one`, Yes in the dialog (which then said "Claude (via Glyphbridge)" and "the current font"): 2 → 1 in Unnamed; one click back, `w6a_two` unchanged and `verified`; `finish_changes` counted 4. **309–316**, the read tools with two fonts open (listener 0.118 / server 0.41, through Claude Code): the new unsaved Unnamed of 303–308 and `savedtestfont.vfc`, opened by the user and in front: **309** `fontlab_status` `fonts_open` 2, testfont Regular, `font_changed` from Unnamed Regular; **310** `list_glyphs`: 6 (`.notdef`, `A`, `testglyph1`–`testglyph4`), no `w5a_` glyph (never saved); **311** after ONE click on Unnamed's tab: 1 (`.notdef`), with the switch note and the warning that a switch between unsaved fonts of the same name cannot be noticed; **312** ONE click back: `get_glyph_outline A` `verified`, advance 639, 54 nodes, identity transform (the −142 offset of 260 was never saved), with the switch note; **313** `get_glyph_sidebearings A` 192.466 / 174.466 / 639; **314** `check_glyph_unicode A` 65, matches; **315** `get_current_font`: PostScript names `test-font` / `fullname of test font` from the package, no `legacy_*` fields (the reply does not show how the package was matched), `.notdef` empty with its dialog; **316** `check_notdef` empty, `already_warned`, no dialog. All as predicted. **317–319**, three fonts open (the same two plus File > New Font, named **"Unnamed1 Regular"**): **317** `list_glyphs` in front: Unnamed1 Regular, 1 (`.notdef`), `fonts_open` 3, `font_changed` from testfont Regular; **318** ONE click on testfont: `get_glyph_width A` 639, switch noted; **319** ONE click on Unnamed: 1 (`.notdef`), Unnamed Regular, switch noted. All as predicted; the two unsaved fonts were told apart by name only. **320–321**, a write with three fonts: **320** Unnamed in front, `create_glyph w8a_one` (1 → 2), `fonts_open` 3, no switch note; **321** ONE click on Unnamed1: `list_glyphs` 1 (`.notdef` only), switch noted; `finish_changes` 1 change. All as predicted. **322–324**, two unsaved fonts of the same name by a Font Info rename: the person changed Unnamed1's Family name to `Unnamed` and pressed OK; **322** `list_glyphs`: still "Unnamed1 Regular" (the reply's name comes from the legacy `font.info.familyName`; either outcome was predicted), 1 glyph; **323** ONE click on the leftmost Unnamed tab: "Unnamed Regular", 2 (`w8a_one`), switch noted; the user's screenshot: the Fonts panel lists "Unnamed (2 fonts)", the tabs read "Unnamed Regular", "fullname of test font", "Unnamed1 Regular"; **324** ONE click on the rightmost tab: still "Unnamed1 Regular", switch noted. So a rename does not produce the unnoticed same-name case, but the reply's name differs from Font Info ([WATCH-POINTS.md](WATCH-POINTS.md)). **325–331**, the other writes with three fonts, testfont in front, prefix `w8b_`: **325** `create_glyph w8b_one` 6 → 7, switch noted; **326** `draw_polygon` 0–200 × 0–400 `verified`, layer `test_font` created, synced; **327** sidebearings 50 / 50, width 0 → 300; **328** `set_glyph_width` 400 (modern route, outline untouched); **329** `set_glyph_unicode` 57345, no other holder; **330** ONE click on Unnamed1: `list_glyphs` 1 (`.notdef`), switch noted; **331** ONE click back: `delete_glyph w8b_one` 7 → 6; the dialog, from the user's screenshot: "local-agent-mode (via Glyphbridge) is requesting to delete the glyph 'w8b_one' from the font "testfont Regular" (file savedtestfont.vfc; 1 of 3 open fonts, the one whose window is in front)." (file name only, no path); `finish_changes` 6 changes. All as predicted. Open: the gated `flPackage()` step, two unsaved fonts of the SAME name, a switch during one call, with three fonts `draw_path` and the read tools other than `list_glyphs` and `get_glyph_width` |
| **N1** | Font names (item 3 of the 2026-11-03 scan): can the tools tell a name FontLab filled in from one a person typed? | the two unsaved fonts of 285–290, then Unnamed1 alone | a marker, or the honest fallback (design C) | DONE 2026-11-03, FontLab 8.9.5. **291** `/debug/fontdir?stage=sub&attr=info`: `fgFontInfo`, 101 UFO-style names, no marker; **292** `/font/current` on Unnamed1: PostScript names = family and style joined (`Unnamed1-Regular`, `Unnamed1 Regular`); **293** `info.dict`: `fgFontInfoDict`, no `len`; **294** (0.115 `memberdir`): members `flags`, `hinting`, `metrics`, `names`, `values`; **295** (0.116) `dict.flags`: `fgFlagsDict` (`asDict`, `del`, `has_key`, `keys`, `value`); **296** `dict.names`: `fgStringDict`, the same members; **297** (0.117, gated) `dict.names.keys()`: 5 keys (`compatible`, `family`, `pref_family`, `pref_subfamily`, `subfamily`), no PostScript key; **298** the person set PostScript to `W6aTest-Regular` in Font Info and pressed OK: 15 keys (Creator and Legal fields added), still no PostScript key, and `font.info.postscriptFontName` still `Unnamed1-Regular` (two variables changed in one run: a design error); **298c** Font Info shows `W6aTest-Regular`; **299** `/debug/walk` on `flWorkspace.instance().currentPackage`, `stage=dir`: name members `psn`, `ffn`, `tfn`, `tsn`, `sgn`; **300** read: `W6aTest-Regular`, `Unnamed1 Regular`, `Unnamed1`, `Regular`, `Unnamed1`; **301** (listener 0.118) two unsaved fonts: `package_names_unavailable`, no file path; **302** Unnamed closed without saving, Unnamed1 alone: `package_names` with `psn` `W6aTest-Regular`, matched as the only font. All as predicted except 297 (unknown in advance) and 298 |
| **F1** | A Power Brush glyph flattened in memory (found in 332; [WATCH-POINTS.md](WATCH-POINTS.md)): what turns `A` of `savedtestfont.vfc` (one Power Brush element, fractional nodes, left 192.466) into a plain contour with whole-unit nodes (left 192)? | `savedtestfont.vfc`, closed WITHOUT saving and reopened before each round; `A` read with `get_glyph_sidebearings` after every step (192.466 intact, 192 flattened) | the step that flattens it | TRIGGER FOUND, 2026-11-03 (listener 0.118 / server 0.41, FontLab 8.9.5, through Claude Code). **332** `get_glyph_outline A` (three fonts: the Unnamed and renamed Unnamed1 of 303–324, testfont): whole-unit nodes, `is_composite` false, three smooth flags lost, no Power Brush note; 312 had read it intact; the user's screenshots: a brush element before 325, a plain "54/18" contour after 332. During 325–331 the user had opened and closed Caladea Bold Italic once (time and button not remembered). **333** reopened: intact, brush shown. **334–343** `w9a_one`: create, draw, sidebearings, width, Unicode, each followed by a read: intact (Unicode predicted to flatten: wrong). **344–349** tab switch, `delete_glyph` (Yes), `get_glyph_outline A`: intact. **350** Caladea opened: the "Coordinates Rounding" dialog ("The font contains fractional coordinates …", Keep fractional / Round); Round; intact. **351** Caladea closed: intact. **352** `create_glyph w9b_one`; **353** read: **192 / 174, flattened**; **354** `draw_polygon` (sent in one batch with 353). Screenshots: brush gone; Preferences > Open Fonts and testfont's Font Info > Family Dimensions both show "Round coordinates" checked (closed with Cancel). **355** reopened: still checked in the file, `A` intact. **356** the user's own Font > New Glyph `w9c_gui`: intact. **357** `create_glyph w9d_one`; **358**: **flattened**. **359** reopened: intact; `/debug/trycreate` refused (3 fonts open), nothing called; the user closed both Unnamed fonts. **360** one font: intact. **361 / 362** `/debug/trycreate how=plain` (`createGlyph` only), read: intact. **363 / 364** `how=legacy_update` (`createGlyph`, `font.update()`), read: intact (predicted flattened: wrong). **365 / 366** `create_glyph w9f_one`, read: intact. **367 / 368** File > New Font (2 fonts), `create_glyph w9g_one`, read: intact. **369 / 370** Caladea with Round, closed; `create_glyph w9h_one`, read: intact. **371 / 372** a new font, its Family name set to `Unnamed` in Font Info (OK); `create_glyph w9i_one`, read: intact. **373 / 374** Caladea with Round, closed; `create_glyph w9j_one`, read: intact. In every `create_glyph` reply `font.update()` ran (no `display_refresh: skipped`), so the tool did what the 363 probe did. Flattened only with the original two Unnamed fonts open, after a Round. **Replay 375–404** (prefix `w10`; FontLab restarted after 375): **375** `get_current_font`, Unnamed alone, no `.notdef` dialog (`already_warned`: the listener had run before, so FontLab was restarted). **376–381** (as 303–308): dialog shown; `w10a_one`, `w10b_one` created and deleted (Yes); **379** `finish_changes` 10 changes (8 carried over from an earlier session; predicted 2: wrong). **382–390** (309–316) testfont opened: `A` intact at 384, 386 (`verified`, 54 fractional nodes, Power Brush flag) and 387; 389 `.notdef` dialog shown. **391–397** (317–321) File > New Font, Unnamed1: `A` intact (393); **395** `create_glyph w10c_one` in Unnamed. **398–400** (322–324) Unnamed1's Family name set to `Unnamed` (OK): replies as in 322–324, the Fonts panel "Unnamed (2 fonts)". **401** testfont in front: `A` intact. **402** `create_glyph w10d_one` (6 → 7); **403** `A` **192 / 174, flattened** (predicted intact: wrong; no Caladea, no Round). **404** `get_glyph_outline A`: the modern layer 54 whole-unit nodes, smooth flags lost; the legacy view still 192.466 / 174.466 (`stale_legacy_view`). So one `create_glyph` call flattened `A`'s modern layer. **405–416** (prefix `w11`; `savedtestfont.vfc` alone, a fresh FontLab start before 405 and before 410): **405–409** `A` intact; `get_glyph_outline A` (`verified`, fractional, brush flag); `create_glyph w11a_one`; `A` **192 / 174, flattened** (predicted: right). **410** no font open; the user opened the file, the Elements panel showed the brush. **411–413** `A` intact; `create_glyph w11b_one` (6 → 7) with no outline read; `A` intact (predicted: right). **414–416**, the same run: `get_glyph_outline A`; `create_glyph w11c_one` (7 → 8); `A` **flattened** (predicted: right). So the trigger is a `get_glyph_outline` read of the Power Brush glyph followed by `create_glyph` in the same font; several fonts, the rename and the Round are not needed (the fact: [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l). **417–435**, four rounds (prefix `w12`), each after a fresh FontLab start with the file alone; `A` intact before each round's probe; all predictions right. **P1, 417–423**: `get_glyph_outline A`; **420** `/debug/trycreate?how=plain&go=yes` (`createGlyph` only, 6 → 7); **421** `A` intact; **422** `create_glyph w12b_one` (with `font.update()`); **423** `A` flattened. **P2, 424–427**: `/glyph/outline?name=A&modern=no` (the legacy part only); `create_glyph w12c_one`; flattened. **P3, 428–431**: `/debug/layerstats?name=A` (the warm-up, `bodyLayer`, the counts 1 / 54 / 1 / 1); `create_glyph w12d_one`; flattened. **P4, 432–435**: `/debug/objdir?name=A&target=glayer&stage=dir` (`glyph.layer` twice, returned None; nothing else); `create_glyph w12e_one`; flattened. So touching the legacy `glyph.layer` of the Power Brush glyph is the trigger, and `font.update()` writes the flattened copy (the fact: [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l). **436–453**, listener 0.119 (`/debug/tryrefresh`, prefix `w13`), each round after a fresh start with the file alone. **R0, 438** `/debug/classdir?name=flGlyph`: 123 names, no Unicode member; sync names `update`, `updateFgGlyph`, `updatedFgGlyphs`, `clearUpdateFgGlyphs`, `fillFgData`, `ensureFgData`, `updateActiveLayer`, `updateSidebearings`, `updateAudit`. **R1, 436–447**: `A` intact (437); outline read (439); **440** `create w13a_one how=Update_flGlyph` (6 → 7); **441** `create w13b_one how=none` (7 → 8); **442** `A` intact (predicted: right); **443** the grid showed neither new glyph, 6 cells, status bar "0/6" (predicted `w13a_one` shown: wrong); **444** `draw_polygon w13a_one` verified and synced; **445** `A` intact; **446** `list_glyphs` 8; **447** the grid unchanged, status bar "0/6/8". **R2, 448–453**: `A` intact (449); outline read (450); **451** `tryrefresh unicode A value=57346`: 65 → 57346, read back; **452** `A` **flattened** (predicted intact: wrong); **453** `check_glyph_unicode A` 57346; the control with `set_glyph_unicode` skipped (`A` already flat). Open: whether the legacy set or the `Update` in 451 flattened `A` (one round each); whether `set_glyph_unicode`, `delete_glyph` and the legacy width route flatten too; why 334 stayed intact (the read at 333 is not recorded) |
| **F1b** | Choose the F1 fix (planned 2026-11-03): does an outline read from the modern layer only avoid the trigger, also for `set_glyph_unicode`, and does FontLab's own GUI leave the legacy copy behind? A fix must pass three checks: no glyph changes unless a tool was asked to change it; new glyphs show in the grid; outline reads stay `verified` | listener 0.119, no build; `savedtestfont.vfc` alone, a fresh FontLab start before each round; `A` read with `get_glyph_sidebearings` before and after each step (192.466 intact, 192 flattened); a new glyph-name prefix per round; never save | **Round 1:** read `A` → `/debug/readmodern?name=A&stage=layer` (the modern layer only: it never touches `glyph.layer`, `bodyLayer` or `findNode`) → `create_glyph` → read `A` → `set_glyph_unicode A 57346` → read `A`; predicted: intact throughout. **Round 2:** read `A` → the person opens `A` in an editor tab and closes it (one GUI action, nothing else) → `create_glyph` → read `A`; no prediction. Then: if round 1 holds, propose listener 0.120: the outline reader and `check_notdef` read glyphs that have an outline from the modern layer only, with stub tests that fail if a read route touches the legacy layer of such a glyph; if round 1 fails, re-plan before any build; if round 2 flattens, FontLab's GUI leaves the trigger too: add an honest warning or a guard. Only if the trigger-side fix fails: one round each for the legacy set and the `Update` in 451 | DONE 2026-11-03 (listener 0.119 / server 0.41, FontLab 8.9.5, through Claude Code; prefixes `w14`, `w15`). **Round 1, 454–460:** **454** `fontlab_status` 0.41 / 0.119, 1 font; `A` 192.466 / 174.466 / 639; **455** `/debug/readmodern?name=A&stage=layer`: layer `test_font`, 1 shape, 54 nodes, no components, `getContours()` and `shapes` lists of 1, `getShapes()` a caught `IndexError` ("Unexpected SeqBase<T> length"; no crash), the wrapper cached by 454; **456** `create_glyph w14a_one` 6 → 7, `font.update()` ran; **457** `A` intact; **458** `set_glyph_unicode A 57346`: 65 → 57346, read back, `glyphs_scanned` 6 in a font of 7 glyphs (probably `A` itself left out; not checked); **459** `A` intact; **460** the user's screenshot: the brush element shown, `w14a_one` in the grid ("1/7"), OUTPUT as sent. **Round 2, 461–466:** **461** `fontlab_status`, the change counter 39 → 41; **462** `A` intact; **463** the person opened `A` in an editor tab and closed it, nothing else; **463b** `A` intact (an extra read, not planned; sidebearing reads do not trigger F1, 411–413); **464** `create_glyph w15a_one` 6 → 7; **465** `A` intact; **466** screenshot: brush shown, `w15a_one` in the grid. Round 1 as predicted; round 2 had no prediction. So a read that keeps off the legacy layer avoids the trigger for `create_glyph` and `set_glyph_unicode`, and opening and closing an editor tab leaves no trigger. Not covered: edits inside the tab; `delete_glyph` and `_set_width_legacy` after an outline read; whether a modern-only reader stays `verified`. Next: the listener 0.120 proposal |
| **S1** | Does FontLab ask about saving when a font changed only through Glyphbridge is closed? | `savedtestfont.vfc` alone, listener 0.119 / server 0.41, FontLab 8.9.5; the person closes the font (or quits FontLab) and presses Don't Save if asked | no question after tool changes; the question after a GUI change | DONE 2026-11-03. After F1b round 1 (a create and `A`'s Unicode change) FontLab quit without the question (between 460 and 461, unnumbered). **467** after round 2 (one create), the font closed: no question. **Control: 468** reopened; **469** the person's Font > New Glyph… > Create Blank `w16a_gui`: advance 500 and a `test_font` layer (a glyph from `create_glyph` has width 0 and no layer), the icon before the font name in the title turned blue; **470** closed: "Save changes to "savedtestfont.vfc" before closing? If you don't save, your changes will be lost." with Don't Save, Cancel, OK, the preview showing `A`; Don't Save. **471** reopened: `w16a_gui` gone, the icon dark; **471a** `get_glyph_width testglyph1` 333; **471b** `set_glyph_width testglyph1 444`: modern route, read back, synced; **471c** screenshot: the icon still dark; **472** closed: no question. All as predicted. So changes made only through the tools do not make FontLab ask (fact: [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §2; why: [WATCH-POINTS.md](WATCH-POINTS.md)) |
| **F1c** | Does a modern write leave the F1 trigger too? The sync check after every modern write (`_auto_sync` → `_guard_classify` → `_tryshape_state`) touches `glyph.layer`, and so does the guard before `font.update()` | listener 0.119 / server 0.41, FontLab 8.9.5, through Claude Code; a fresh FontLab start, `savedtestfont.vfc` alone, prefix `w17`; never save | `A` intact after the width write, **flattened** after the next `create_glyph` | DONE 2026-11-04. **473** `fontlab_status` 0.41 / 0.119, 1 font; `A` 192.466 / 174.466 / 639; **474** `set_glyph_width A 700`: 639 → 700, modern route, verdict `synced` (so the classification ran); **475** `A` 192.466 / 235.466 / 700, intact; **476** `create_glyph w17a_one` 6 → 7; **477** `A` **192 / 235 / 700, ink 273: flattened**; **478** `/debug/classdir?name=flLayer` (names only): among the members `boundingBox`, `inkBox`, `resetInkBox`, `isChanged`, `hasChanges`, `changed`, `getContours`, `getShapes`, `findNode`; **479** the user's screenshot: `A`'s element without its brush icon, a plain "54/18" contour, status bar 192 / 700 / 235, `w17a_one` in the grid. All as predicted. So a modern write on a Power Brush glyph followed by `create_glyph` flattens it with no outline read. The sync check in 474 did it: a glyph found synced is dropped from the guard's list (`_guard_mark`), so the guard before 476 did not classify `A` (from the code). FontLab quit without saving afterwards (fact: [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l) |
| **F1d** | Do the legacy reads `glyph.layers` (its length), `glyph.width` and `glyph.components` (its length), with no `glyph.layer`, arm F1? (the planned light sync check of listener 0.120) | listener 0.119 / server 0.41, FontLab 8.9.5, through Claude Code; a fresh FontLab start, `savedtestfont.vfc` alone, prefix `w18`; never save | `A` intact after the create | DONE 2026-11-04. **480** `fontlab_status` 0.41 / 0.119, 1 font; `A` 192.466 / 174.466 / 639; **481** `/debug/objdir?name=A&target=glyph&stage=read&attrs=layers,width,components`: `fgLayers` len 1, width 639.0, `fgComponents` len 0; **482** `create_glyph w18a_one` 6 → 7; **483** `A` **192 / 174 / 639, ink 273: flattened** (predicted intact: wrong); **484** `/debug/classdir?name=flLayer&members=boundingBox,inkBox,resetInkBox` (documentation only): `QRectF boundingBox()`, `QRectF inkBox([QTransform tx = QTransform()])`, `resetInkBox()`. So at least one of the three reads arms F1; the light check was dropped. FontLab quit without saving |
| **F1e** | Which of the three reads of F1d arms F1? One read per round | as F1d, a fresh FontLab start before each round; prefixes `w19`, `w20`, `w21` | no prediction | DONE 2026-11-04. **Round 1, 485–488:** **485** `fontlab_status`, `A` intact, 6 glyphs; **486** `get_glyph_width A` (the tool, legacy `glyph.width`): 639; **487** `create_glyph w19a_one` 6 → 7; **488** `A` **intact**. **Round 2, 488b–492:** **488b** `A` intact; **489** `list_glyphs` 6 (unplanned; it reads only the glyph names, as every route does); **490** `/debug/objdir … attrs=layers`: `fgLayers` len 1; **491** `create_glyph w20a_one` 6 → 7; **492** `A` **192 / 174 / 639, ink 273: flattened**. **Round 3, 493–496:** **493** `A` intact; **494** `/debug/objdir … attrs=components`: `fgComponents` len 0; **495** `create_glyph w21a_one` 6 → 7; **496** `A` **intact**. So reading `glyph.layers` arms F1 as `glyph.layer` does; `glyph.width` and `glyph.components` did not (fact: [topics/fonts-and-sync.md](topics/fonts-and-sync.md) §8l) |
| **V120** | Live checks of listener 0.120 / server 0.42 (the F1 fix) | `savedtestfont.vfc` alone, a fresh FontLab start before each F1 round, Claude Desktop fully restarted after the build; prefixes `w22`, `w23`, `w24`; never save | as listed in each step | DONE 2026-11-04, through Claude Code. **Check 1, 497–501:** **497** `fontlab_status` 0.42 / 0.120, 1 font, no change counter (a fresh server process); **498** `A` 192.466 / 174.466 / 639; **499** `get_glyph_outline A`: `verified` from the modern layer only, 54 fractional nodes in one cubic contour, one element `is_composite` true with an identity transform, `y_extent_checked` false, the note that the legacy layer was not read; **500** `create_glyph w22a_one` 6 → 7; **501** `A` **intact**. **Checks 2, 4, 5, 502–511:** **502** status; **503** `A` intact; **504** `set_glyph_width A 700`: 639 → 700, modern route, verdict `synced` (the light check); **505** 192.466 / 235.466 / 700; **506** `create_glyph w23a_one` 6 → 7; **507** `A` **intact**; **508** `draw_polygon w23a_one` 50–350 × 0–300: `verified`, layer created, `synced` (the full check); **509** `create_glyph w23b_one` 7 → 8; **510** `get_glyph_outline w23a_one` `verified`, 4 nodes, `A` still 192.466 / 235.466 / 700; **511** `check_notdef`: `empty` by the legacy check (`.notdef` has no modern layer), its dialog shown (a new listener run). **Check 3, 512–518:** **512** status; **513** `A` intact; **514** `set_glyph_sidebearings A 50 60`: FontLab moved `A` by a whole −142 to 50.466 / 60.466 / 383, reported as not matching the request (as in 145f); **515** `get_glyph_outline A`: `verified` with the element offset −142 applied (box left 50.466 = lsb), `raw_x` kept, `y_extent_checked` false: so the modern node coordinates are the element's own values, before its transform; **516** `create_glyph w24a_one` 6 → 7; **517** `A` **50.466 / 60.466 / 383, intact**; **518** the user's screenshot: the brush icon with Δ=(-142.0), status bar 50 / 383 / 60. **Check 6, 519–520:** **519** `/debug/readmodern?name=A&stage=box&go=yes` (gated, approved): `boundingBox()` raised "TypeError: 'QRectF' object is not callable" (no crash: a property, although its docstring says `QRectF boundingBox()`); `inkBox()` returned a QRectF with left 50.466, right 322.534, `top` 88.472, `bottom` 419.528 (Qt names them y-down), equal to the ink box the server computed in 515; **520** `A` intact. All as predicted; no prediction was made for `boundingBox()`. FontLab quit without saving afterwards |
| **INK** | Can `flLayer.inkBox()` check the vertical extent on the modern route? (the gated probe of listener 0.120 on more glyphs, then F1, then FontLab's own display) | listener 0.120 / server 0.42, `savedtestfont.vfc` alone, FontLab 8.9.5 freshly started; `/debug/readmodern?stage=box&go=yes` approved; prefix `w25`; never save | `inkBox()` equals the exact curve extents within 0.05 in x and y, `top` the lower y; `A` intact after a create; FontLab shows y 203.81 / height 210.19 for `testglyph2`, or 172 / 242 if it shows the box of the points | DONE 2026-11-04, through Claude Code. **521–528:** `get_glyph_outline`, then the probe, on `testglyph1` (quadratic, scale 0.951 × 0.969, offset 15 / 24: x 78.748..258.694 = lsb and advance − rsb; y 83.880..436.234, equal to the exact quadratic extents computed separately; the server's on-curve box was not exact), `testglyph2` (cubic: equal to the `verified` box 102.155..383 × 203.806..414), `testglyph3` (quadratic: 101.870..383 × 203.238..414, equal to the exact extents), `testglyph4` (10° slant: equal to 158.875..431.314 × 203.806..414); **529–530** `A` `verified` 192.466..464.534 × 88.472..419.528, `inkBox()` equal. `top` was the lower y each time; `boundingBox()` raised its TypeError each time, no crash. **531** `create_glyph w25a_one` 6 → 7; **532** `A` 192.466 / 174.466 / 639, **intact**. **533** the user's screenshot of `testglyph2`, all nodes selected: X 83, Y 172, 300 × 242 (the box of the points, handles included), glyph panel 102 / 500 / 117; the tab read "testglyph2•" ([WATCH-POINTS.md](WATCH-POINTS.md)). All as predicted |
| **V121** | Live checks of listener 0.121 / server 0.43 | listener restarted, Claude Desktop fully restarted; `savedtestfont.vfc` alone, a fresh FontLab start for the F1 round; prefix `w26`; never save | `fontlab_status` 0.43 / 0.121; `get_glyph_outline` `verified` with `y_extent_checked: true` on `testglyph1`–`4` and `A`, the boxes of INK; `A` intact after outline, create, read | DONE 2026-11-04, through Claude Code. **534** `fontlab_status` 0.43 / 0.121, 1 font, no change counter; **535–538** `get_glyph_outline`: `testglyph1` (quadratic, now exact) 78.748..258.694 × 83.88..436.234, `testglyph2` 102.155..383 × 203.806..414, `testglyph3` (quadratic, `unverified` before 0.43) 101.87..383 × 203.238..414, `testglyph4` 158.875..431.314 × 203.806..414, each `verified`, `y_extent_checked` true, `ink_box_vs_fontlab` equal; **539** `A` `verified`, 192.466..464.534 × 88.472..419.528, y checked; **540** `create_glyph w26a_one` 6 → 7; **541** `A` 192.466 / 174.466 / 639, **intact**. All as predicted. The `get_glyph_outline` description the client showed was still the 0.42 text (stale after one restart, as [CLAUDE.md](../CLAUDE.md) warns) |
| **T6** | `/debug/trymodern?stage=create` (modern glyph creation without the legacy `font.update()`): only if a design needs it | gated, disposable font, once per listener run | the name reads back, the glyph exists in the legacy font, no layer lost; it would offer a creation route that never calls `font.update()` | OPEN, LOW PRIORITY (guard + auto sync already protect `create_glyph`, but not a glyph Glyphbridge never changed: F1, 414–416) |
| **T7** | Multi-layer / multi-master glyph: which layer `Update` and the reader address (P1.3) | a font with two masters or layers | names-only probes first | OPEN |
| **T8** | Quadratic (TrueType) font: `Update`, the reader, `draw_path` meaningful? (P2.3; real quadratic data can be READ from Arial opened from the system) | Arial from the system, read-only first | `Off` runs read; `unverified` expected for quadratic | OPEN |
| **T9** | Save and reopen after API work, including a NEW font from `flPackage()` and an auto-synced glyph: do shapes, widths, sidebearings and layer survive? (test 135 and all File > Save tests) | the person saves a COPY | everything survives | **run on a font made with File > New Font: 707–712, plain tool-made glyphs survive exactly, a Power Brush glyph's nodes change at load ([topics/reading.md](topics/reading.md) §8p); open contours survive exactly: 755–764; a font made by `flPackage()`: the same, 772–778; KW 557–560 for kerning; save tests by preference only, with the user's agreement ([DECISIONS.md](DECISIONS.md))** |
| **T10** | Older live checks still open (P3): `create_glyph('uni00e8')` shows the lowercase-hex warning; `.notdef` items (explicit `check_notdef` through Claude, the `missing` dialog on a throwaway font, a timed-out write while a dialog is open (checklist 19), a wait between 90 and 120 s); `set_glyph_width` on a glyph whose layer exists but is inactive (checklist 44) | per checklist rows 18, 19, 20, 44 | as in the checklist | PARTLY 2026-11-19: checklist #20 done live 1403; #44 tried once 2026-11-25 (IL 1720–1725), the state not reached, stays stub-only; the other T10 checks remain open |
| **T11** | Rotation and mirroring transforms on real data (checklist 12c / 12d / 12e, 13, 14): with v0.88 the margin comparison also has to hold for them | reference glyphs built by the person with the Element tool | `margins_agree: true`, `verified` | PARTLY: rotation of components `verified`, 765–771 (RT series); mirroring, combined, Power Brush OPEN |
| **T12** | After P0.2 is built: with NO font open every tool answers `open: false` (no placeholder `Paper` font); stub tests with a faked `CountFonts()` first | restart FontLab, no font open | `open: false` everywhere | PARTLY 2026-11-02 (listener 0.105, server 0.34), test 227: Arial closed in a running FontLab: `fontlab_status` `font_open: false`, `get_glyph_width A` and `create_glyph kn6A` refused with "no font is open"; OUTPUT `reads: no font open: font info 1, width 1` and `REFUSED create kn6A: no font is open`. Test 244 (2026-11-03, listener 0.110): a freshly started FontLab, every read route `open: false` (K13). Open: delete, sidebearings, Unicode and drawing live (stub only) |
| **T13** | LAST block (user decision): big glyphs: time of `Update` on 180 / 990 nodes against the 5 s tool timeout; near-cap (1980 nodes) request, 2001-node refusal, real timings with `Measure-Command`, the outline route on 1000+ nodes (needs P2.4), a real large glyph (checklist 17, 42) | disposable font | see the LAST block | POSTPONED to the very end |

### T10 follow-up: lowercase-hex glyph name (checklist #20, 2026-11-19)

**1403** (`fontlab_status`): listener reachable, no font open; connected server 0.76, listener 0.192. **Setup:** `create_font` made an unsaved `Unnamed Regular` font, one master (`Regular`), one glyph (`.notdef`), FontLab 8.9.5 Demo mode. No File > Save stage.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1403 | `create_glyph('uni00e8')` | created, glyph count 1 → 2, FontLab assigns U+00E8 (232), `name_warnings` recommends `uni00E8`; new layer `Regular` | all as expected: `created: true`, `unicode: 232`, `unicode_status: assigned`, `unicode_assigned_by_fontlab: true`, `layer_created: Regular`, `layer_name_source: package master`, synced; warning: “The name uses lowercase hex digits; the naming convention requires UPPERCASE (use 'uni00E8'). FontLab maps lowercase hex anyway (seen live: 'uni00e8' -> 232), but other tools may not.” The GUI Unicode display was not separately checked |
| 1403 | `finish_changes` | one package reminder; nothing saved | `changes_in_package: 2` (font creation and glyph creation), 0 uncertain; save reminder returned and shown in chat |

The "Predicted" column was filled in after the run: no prediction was stated in chat beforehand. Read it as the behaviour expected from the code, not as a prediction tested by this run.

Reading (one run): the lowercase-hex warning appears and FontLab assigns 232 to `uni00e8`. The test font remains unsaved and disposable.

### Checklist #38 follow-up: `draw_polygon` rounding report (2026-11-19)

**1404** (`fontlab_status`): `Unnamed Regular`, one font open, one master; connected server 0.76, listener 0.192. The existing disposable font from 1403 was unsaved and held `.notdef` and `uni00e8`. A fresh prefix `r38a` was used. FontLab 8.9.5 Demo mode; no File > Save stage.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1404 | `create_glyph('r38a')`; `draw_polygon('r38a', [[10.2,20.2],[110.7,20.2],[110.7,220.7],[10.2,220.7]])` | glyph count 2 → 3; eight changed coordinates reported; verified outline `(10,20)`, `(111,20)`, `(111,221)`, `(10,221)` | all as expected: `drawn: true`, `verified: true`, 4 points, 1 contour, 1 shape, 4 nodes, `coordinates_rounded` contained the eight requested/used values and `rounding_note` stated Rule B; readback metrics left 10, ink width 101; synced. The editor panel was not separately inspected |
| 1404 | `finish_changes` | one package reminder; nothing saved | `changes_in_package: 2`, 0 uncertain; save reminder returned and shown in chat |

The "Predicted" column was filled in after the run: no prediction was stated in chat beforehand. Read it as the behaviour expected from the code, not as a prediction tested by this run.

Reading (one run): the reply reports every fractional coordinate that changed and the outline verifies at the rounded positions. The disposable font remains unsaved.

### Checklist #16: an empty glyph against the layerless `.notdef` (2026-11-19)

**Setup:** `fontlab_status`: no font open; server 0.77, listener 0.192, FontLab 8.9.5 Demo mode. The user opened Arial Regular from the system (4,652 glyphs; `.notdef` index 0, `_001`, `_002`, `space` index 3), then made a font with File > New Font (`Unnamed Regular`, `.notdef` only, so no `space` there). Instrument: `GET /glyph/outline?name=X&modern=no` (read-only, ungated): a glyph with no layer answers `layer_name: null`, `layer_count: 0`; one with a layer names it. No glyph was clicked before the API reads; nothing was written or saved; no File > Save stage. Each prediction was written in chat before its read; FontLab's OUTPUT panel logged each read (`reads: outline 1`).

| # | Font in front | Glyph | Predicted | Result |
|---|---|---|---|---|
| 1405 | Unnamed | `.notdef` (zero-layer control) | `layer_name: null`, `layer_count: 0`, 0 nodes | as predicted; `component_count: 0` |
| 1406 | Arial | `.notdef` (has-a-layer control) | a named layer, 8 nodes, 2 contours | as predicted: `Regular`, 8 nodes, 2 contours (the squares (256,0)–(1280,1280) and (288,32)–(1248,1248)) |
| 1407 | Arial | `space` (the question) | `Regular`, 0 nodes | as predicted: `Regular`, 0 nodes, 0 shapes, 0 components, width 569 |
| 1408 | Unnamed | `.notdef` again, after the user selected it in the Font window | still no layer | as predicted: `layer_count: 0`; the Layers & Masters panel listed no row |

GUI (after the reads): with Arial's `space` selected, the Layers & Masters panel listed one row, `Regular`; the status bar showed width 569 and `#0020`. The layerless `.notdef` was shown with width 250.

Reading (one run): Arial's empty `space` has one empty layer; it is not layerless like the empty `.notdef` of a font made with File > New Font. The Layers panel agrees with the API in both cases, and selecting a glyph in the Font window does not create a layer. Not run: an empty glyph made by FontLab other than `.notdef` (for example Font > New Glyph… in a new font), other imported fonts.

### Legacy-call research: `flGlyph.advanceWidth` (2026-11-20, listener 0.195, FontLab 8.9.5 in Demo mode, through Codex)

| # | Call | Result |
|---|---|---|
| 1437 | `/debug/moddir`, names only (nothing called) | `flGlyph.advanceWidth` is a public member, documented as `double`. Recorded afterwards from Codex's chat reply; no prediction was stated and the raw reply was not kept. Its value on a glyph was not read |

### Listener 0.196 `/debug/tryadvancewidth`: live checks skipped (2026-11-20)

At the user's request, both the names-only and gated read stages were skipped because they need an existing glyph whose name starts with `tri`. No `flGlyph.advanceWidth` value was read in FontLab, and no live result is claimed. The four stub harnesses passed; their synthetic `tri` glyph does not replace the skipped FontLab checks.

### AW: the advanceWidth round (2026-11-20, listener 0.196 / server 0.79, FontLab 8.9.5 in Demo mode, through Claude Code)

The CK font `Unnamed` (unsaved), one master. Tools through Claude Code; probe requests through PowerShell `Invoke-RestMethod` / `Invoke-WebRequest` to `127.0.0.1:8765`; FontLab's display read by the user (screenshots). Every prediction was stated in chat before its call, except where the row says "no prediction". Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1438 | `fontlab_status` | 0.79 / 0.196, `fonts_open` 1 | versions as predicted; **`fonts_open` 2** (`Unnamed1` in front): the probe needs one font, so the round paused. The reply counted 1 Glyphbridge change and a switch from `Unnamed`, both from before this session (the server process outlives sessions, [WATCH-POINTS.md](WATCH-POINTS.md)) |
| 1438a | the user closed `Unnamed1` (the X at the left of its title); `fontlab_status` | 1 font, `Unnamed Regular`, a switch note | as predicted |
| 1439 | `create_glyph tri1a` | created, +1, `layer_created`, no Unicode | as predicted: 7 → 8, layer `Regular`, synced, marked |
| 1440 | `set_glyph_width tri1a 500` | `route` modern, 0 → 500, no `layer_created` (revised before the call: 1439 had made the layer) | as predicted, outline untouched, synced, marked |
| 1441 | `get_glyph_width tri1a` (legacy `glyph.width`) | 500 | as predicted |
| 1442 | the user clicked `tri1a` once in the Font window | bottom bar 500 | as predicted: bar 500, LSB 0, RSB 0; tooltip ↔ 500 |
| 1443 | `/debug/tryadvancewidth?name=tri1a&stage=names` | `found`, `wrapper` "cached", `advance_width_listed`, no read, 8 → 8, no side effect, `calls_so_far` 0 | as predicted; 147 member names, of them `advanceWidth` and `metricsWidth` contain "width" |
| 1444 | `stage=read` without `go=yes` | refused, nothing read | as predicted |
| 1445 | `stage=read&go=yes` | `advance_width` 500.0, call 1, no side effect | as predicted (the raw JSON `500.0`, a float) |
| 1445x | an extra `stage=names` request, sent by mistake in the same command as 1445 | — | not planned; names only, nothing read, the counter unchanged |
| 1446 | `set_glyph_width tri1a 437`, then the gated read | modern, 500 → 437; 437.0, call 2 | as predicted: the probe follows the width |
| 1447 | `get_glyph_width tri1a` | 437 | as predicted |
| 1448 | the user clicked `tri1a` again | bottom bar 437 | as predicted |
| 1449 | `set_glyph_width tri1a 437.5` | modern, 437 → 437.5 (a refusal was named as possible) | **not predicted:** the error "Width of glyph 'tri1a' was NOT changed: width did not change to the requested value after setting"; OUTPUT "NOT DONE width tri1a: …" |
| 1449a | the gated read | 437.0, or a whole number from rounding | **438.0**, call 3: the width did change, so "NOT changed" was false |
| 1449b | `get_glyph_width tri1a` | no prediction | **437.5**: the legacy and modern reads disagree |
| 1449c | the user clicked `tri1a` | no prediction | tooltip ↔ 438, bottom bar 437: does not decide (the bar may lag, or round 437.5 down as panels do with sidebearings) |
| — | `finish_changes` | at least 3 changes; whether 1449 counts not predicted | 3 changes: the 1449 write, which changed the width, was **not counted** |

Withdrawn after the round, before any test: "the sync guard will skip the next refresh because of `tri1a`". The guard forgets a glyph once a write syncs it (1446), and the failed write never registered it (`_guard_mark` runs only on success).

### AW2: fractional widths (2026-11-20, the same font and versions)

| # | Step | Predicted | Result |
|---|---|---|---|
| 1450 | `fontlab_status` | 1 font, `Unnamed Regular`, 0.79 / 0.196 | as predicted |
| 1451 | `get_glyph_width tri1a` | 437.5 | as predicted |
| 1452 | the gated read `tri1a` | 438.0, call 4, no side effect | as predicted |
| 1453 | `create_glyph tri2a` (its `font.update()` is the one variable for `tri1a`) | 8 → 9, layer, no `display_refresh: skipped` | as predicted |
| 1454 | `get_glyph_width tri1a` | no prediction | 437.5: unchanged by the refresh |
| 1455 | the gated read `tri1a` | no prediction (438.0 expected, not sure) | 438.0, call 5 |
| 1456 | the user clicked `tri2a` (width 0), typed `437.5` in the bottom bar's width field and pressed Enter | no prediction | the field showed `437.5` while typed, **438 after Enter**: the GUI rounds the width to a whole unit |
| 1457 | `get_glyph_width tri2a` | 438 if the GUI rounded | as predicted: 438 |
| 1458 | the gated read `tri2a` | 438.0, equal to 1457; call 6 | as predicted |
| — | `finish_changes` | 1 change | as predicted |

Reading: for a width made as a person makes one (the GUI, or `set_glyph_width` with a whole number) the legacy `glyph.width`, `flGlyph.advanceWidth` and FontLab's display agree (500, 437, 438). Only `advanceWidth = 437.5` written through the API gave a fraction, and then the two reads disagree (437.5 against 438.0), stable and unchanged by `font.update()`. Not settled: what FontLab stores and would save or export for `tri1a` (needs a save, unavailable in Demo mode; [WATCH-POINTS.md](WATCH-POINTS.md)). The test font holds `tri1a` (437.5 legacy / 438 modern) and `tri2a` (438), nothing to keep.

### AW3: whole-unit widths (2026-11-20, listener 0.197 / server 0.80, the same font, FontLab 8.9.5 in Demo mode, through Claude Code)

A new Claude Code session, so the 0.80 tool definitions were loaded. FontLab's display and OUTPUT panel read by the user (a screenshot). Every prediction was stated in chat before its call, except 1460, whose prediction was written in the brief before the load. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1459 | `fontlab_status` (run by the session that started this one) | — | server 0.80 / listener 0.197, one font, `Unnamed Regular`, unsaved |
| 1460 | read the loaded `set_glyph_width` description | contains "The width is rounded to a whole unit (a half rounds up)" | as predicted |
| 1461 | `create_glyph tri3a` | 9 → 10, `layer_created`, no Unicode | as predicted: layer `Regular`, synced, marked |
| 1462 | `set_glyph_width tri3a 437.5` | modern, 0 → 438, `width_rounded` {437.5, 438}, `rounding_note`; OUTPUT "width tri3a: 0 -> 438 (rounded from 437.5, verified)" | the reply as predicted; **OUTPUT "width tri3a: 0 -> 438 (verified)"** (read in 1465): the server rounds before it calls the listener, which receives 438 and has nothing to report; "rounded from" appears only for a fraction posted to the listener directly |
| 1463 | `get_glyph_width tri3a` (legacy `glyph.width`) | 438 | as predicted: the legacy read agrees, unlike `tri1a` (1449b) |
| 1464 | the gated read `tri3a` | 438.0, call 1, no side effect | as predicted, 10 → 10 |
| 1465 | the user clicked `tri3a` once in the Font window | bottom bar 438 | as predicted: bar 438, LSB 0, RSB 0; tooltip ↔ 438 |
| 1466 | `set_glyph_width tri3a 437.4` | modern, 438 → 437, `width_rounded` {437.4, 437}; OUTPUT without "rounded from" (revised after 1465) | as predicted: the reply, and OUTPUT "width tri3a: 438 -> 437 (verified)" (read by the user after the record was first written) |
| 1467 | `finish_changes` | 3 changes | as predicted: 3, 0 uncertain |

Reading: through the tool, a fractional request is written as the rounded whole width, and the legacy read, `advanceWidth` and FontLab's display agree; the rounding shows in the chat reply (`width_rounded`), not in FontLab's OUTPUT line. Not run live: a width that moved but not to the request (nothing known produces it), the legacy route, a fraction posted to the listener directly. The test font now also holds `tri3a` (437), nothing to keep.

### Panel: a class pair with exceptions (2026-11-20, the same font, FontLab 8.9.5 in Demo mode; the user's screenshots)

No call and no change: two screenshots of FontLab's KERNING panel, taken after AW3. No prediction was written beforehand; before 1469 Claude only said what a footer of 6 would mean. One run, no control. The font held the six entries listed at the end of CK2.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1468 | the panel as it was (collapsed) | — | 4 top-level rows: `cwB` `cwB` -25, `cwB` `cw1a` -15, `cwL` `cwR` -70, `cw1f` `cw1e` -10; the `cwL : cwR` row has `>` and its class names in red, its value in black; footer 6 |
| 1469 | the user clicked `>` on `cwL` | — | nested under `cwL : cwR`: `cw1b` `cwR` -60 and `cwL` `cw1d` -30, names in black, values in red; footer still 6 |

Reading: the two exceptions of `cwL : cwR` (one member on the left, one on the right) sit under it once the class pair exists; before 1436 they were top-level rows (1432). The footer matched the entry count (6), not the top-level rows (4) ([topics/kerning.md](topics/kerning.md) §4).

### AW4: `advanceWidth` on other kinds of glyph (2026-11-20, listener 0.197 / server 0.80, the same font, FontLab 8.9.5 in Demo mode, through Claude Code)

Research for the swap of `get_glyph_width` to `flGlyph.advanceWidth` (the user's choice C: research before the design). The probe `/debug/tryadvancewidth` (listener 0.196) read each glyph once, gated; its counter went from 1 to 4 of 10 (AW3 1464 counted in the same listener run). Prefix `trib`. Every prediction was stated in chat before its call; 1473's was revised after 1472, and those of 1484–1486 were refined from the user's screenshot before the calls. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1470 | `fontlab_status` | 0.80 / 0.197, 1 font | as predicted: `Unnamed Regular`, unsaved; it counted 3 changes from AW3 (the count runs since the server started) |
| 1471 | the user: Font > New Glyph… `trib1`, Create Blank | in the grid | as predicted |
| 1472 | `get_glyph_sidebearings trib1` | a layer (low confidence), otherwise "no editable layer" | a modern layer: left 0, right 0, advance 500 (`ink_width` 500 is the formula on an empty glyph) |
| 1473 | `get_glyph_width trib1` | 500 (revised after 1472) | 500 |
| 1474 | the gated read `trib1` | 500.0, no side effect | as predicted: call 2, 11 → 11 |
| 1475 | `create_glyph trib2s` | created, `layer_created` | as predicted: 11 → 12, `Regular` |
| 1476 | `draw_polygon trib2s` (100,0) (300,0) (300,500) (100,500) | `verified` | as predicted; advance 0 |
| 1477 | `set_glyph_width trib2s 400` | 0 → 400 | as predicted: modern, outline untouched |
| 1478 | `create_glyph trib2c` | created, `layer_created` | as predicted: 12 → 13 |
| 1479 | `add_component trib2c` from `trib2s` | placed, the width written back (0) | as predicted: `verified`, `empty layer`, `width_set_by_build` 400, advance 0 |
| 1480 | `set_glyph_width trib2c 600` | 0 → 600 | as predicted |
| 1481 | `get_glyph_width trib2c` | 600 | as predicted |
| 1482 | the gated read `trib2c` | 600.0 | as predicted: call 3, 13 → 13 |
| 1483 | the user: New Glyph `trib3p`, Create Blank, opened in an editor tab, one Power Brush stroke, back to the Font window | — | screenshot: one brush element; bottom bar LSB 41, width 500, RSB 129 |
| 1484 | `get_glyph_outline trib3p` | modern route, one Power Brush shape, left ≈ 41, right ≈ 129 | as predicted: `verified`, 37 nodes, `is_composite` true, identity; left 41, right 129, advance 500; fractional control points (for example x 251.97450422292602) |
| 1485 | `get_glyph_width trib3p` | 500 | as predicted |
| 1486 | the gated read `trib3p` | 500.0 | as predicted: call 4, 14 → 14 |
| 1487 | `create_glyph trib3x` (its `font.update()` is the F1 trigger) | created | as predicted: 14 → 15, no `display_refresh: skipped` |
| 1488 | `get_glyph_outline trib3p` | not flattened | as predicted: the 37 nodes identical to 1484, fractions kept, `is_composite` true |
| 1489 | `finish_changes` | 7 | as predicted: 7, 0 uncertain |

Reading: on a glyph made with FontLab's New Glyph, a composite and a Power Brush glyph, `advanceWidth` equals the legacy `glyph.width` (500, 600, 500), with no side effect. Building the wrapper and one `advanceWidth` read of a Power Brush glyph, followed by `font.update()`, did not flatten it (one run). Outline reads were already proven safe in V120, so the probe read was the only new step. Not reached: a glyph with no layer (FontLab's New Glyph gives one, as `create_glyph` does in a one-master font). Not run: several fonts (the probe needs one), and the fractional case of `tri1a` (it needs a save). Seen, not predicted: FontLab's New Glyph starts a glyph at width 500, `create_glyph` at 0. The test font now also holds `trib1`, `trib2s`, `trib2c`, `trib3p` and `trib3x`, nothing to keep.

### AW5: `get_glyph_width` reads `advanceWidth` (2026-11-20, listener 0.198 / server 0.81, the same font, FontLab 8.9.5 in Demo mode, through Claude Code)

The live checks of design B ([DECISIONS.md](DECISIONS.md)). The listener and Claude Desktop were restarted before 1490. This session was a resumed one and kept the 0.80 tool description, so 1491 ran in a new Claude Code session started from it; the replies of 1492–1498 come from the running 0.81 server. Every prediction was stated in chat before its call; 1498's number was added before the call. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1490 | `fontlab_status` | 0.81 / 0.198, 1 font, `Unnamed Regular` | as predicted |
| 1491 | a new session reads the loaded `get_glyph_width` description | contains "modern advance width", `widths_disagree`, "do not choose one", `width_source "legacy"` | as predicted: all four, the 0.81 text word for word (its transcript read by this session) |
| 1492 | `get_glyph_width trib2c` (a composite) | 600, `modern`, no `legacy_width` | as predicted |
| 1493 | `get_glyph_width tri1a` | 438, `modern`, `legacy_width` 437.5, `widths_disagree`, note and instruction | as predicted |
| 1494 | `get_glyph_width .notdef` | `legacy`, "the glyph has no active modern layer" (medium confidence); no number | as predicted: 250, with the `width_note` |
| 1495 | `get_glyph_width trib3p` (Power Brush) | 500, `modern` | as predicted |
| 1496 | `create_glyph tric1` (the F1 trigger) | created | as predicted: 15 → 16, synced |
| 1497 | `get_glyph_outline trib3p` | not flattened | as predicted: the 37 nodes identical to 1484, `is_composite` true |
| 1498 | `finish_changes` | 1 | as predicted |

Reading: `get_glyph_width` answers from `advanceWidth` on a composite and a Power Brush glyph, which stays unflattened. It shows both values where FontLab's two views disagree (`tri1a`). It falls back to the legacy width, with a note, on a glyph with no active modern layer (`.notdef`, the first live run of that path). One run each. Stub-tested only: a failed legacy read. Not run: several fonts. The test font now also holds `tric1`, nothing to keep.

### GE0: editing kerning groups, the API by name (2026-11-20, listener 0.198, FontLab 8.9.5 in Demo mode, no font open, through Claude Code)

Names only: `/debug/moddir` and `/debug/classdir` read `dir()` and `__doc__`; nothing was called, constructed or changed. Predictions were stated in chat before 1499–1502; 1503 and 1504 had none and are reported as found. No stage needed a save.

| # | Read | Predicted | Result |
|---|---|---|---|
| 1499 | `fontgate.fgKerningGroups`, members and docstrings | the 8 names of R0; `remove` and `rename` without a docstring | names held; docstrings wrong: `remove('groupName'[, deleteDependentKerningPairs = false])`, `bool/Nothing rename('oldGroupName', 'newGroupName')`; `items`, `keys`, `values`, `has_key`, `clear` documented too |
| 1500 | `fontgate.fgKerning`: `addGroup`, `deleteGroup`, `deleteAllGroups`, `renameGroup` | no docstrings | held; `hasGroupKerning` none either, `groups` an empty one |
| 1501 | `fontgate.fgGroup` | the 7 attributes of R0; no way to build one | attributes held; a constructor is documented: `fgGroup(tuple('name', list(ids), mode, 'mainglyphname'))`, modes `FeaClassGroupMode`, `KernLeftGroupMode`, `KernRightGroupMode`, `KernBothSideGroupMode` |
| 1502 | `flPackage` names with `group`, `class` or `kern` | `getAllGroups`, `findGroup` and a setter | no setter: `autoKern`, `deleteGroups`, `findGroup`, `getAllGroups`, `kerning`, `kerningContainer` |
| 1503 | `flPackage` docstrings of those four, and its names that start like a setter | (none stated) | `deleteGroups(QSet<uint> ids, bool deleteDependentContent)`, `fg::GlyphGroup* findGroup(int _id)`; no group setter among the `add`, `set`, `create`, `update`, `replace` names |
| 1504 | `fontgate` names with `group`; `fgGroups` docstrings | (none stated) | `fgGroup`, `fgGroups`, `fgKerningGroups`; `fgGroups` has `fromDict(dict('name':fgGroup))`, `bool remove('name')`, `bool rename('old_name', 'new_name')` |

Also read, as a source of names only ([DECISIONS.md](DECISIONS.md), 2026-11-20): FontLab's Python documentation, which redirected to its FontLab 7 archive. It lists `__setitem__` and `__delitem__` on `fgKerningGroups`, `fgGroups`, `fgGroup` and `fgKerning`, which the probes cannot see (they list public names only). Reading: renaming and removing a kerning group have documented calls on the master's group container; creating a group or changing its members has none but a subscript assignment, which needs its own gated proof ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md)). Research probe built: listener 0.199 (`/debug/trykerngroupedit`, [topics/server-and-endpoints.md](topics/server-and-endpoints.md) §3).

### GE: renaming and removing a kerning group by probe (2026-11-20, listener 0.199 / server 0.81, FontLab 8.9.5 in Demo mode, through Claude Code)

The probe `/debug/trykerngroupedit` ([topics/server-and-endpoints.md](topics/server-and-endpoints.md) §3) on a new unsaved font, one master, one font open except where a font switch is named. The listener was restarted before 1505. Every prediction was stated in chat before its call or GUI step. Classes made by the person in the Classes panel; class entries written by `set_kerning`. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1505 | `fontlab_status` | 0.199 / 0.81, no font open | as predicted |
| 1506 | `create_font`, no family | `Unnamed Regular`, 1 font open | as predicted |
| 1507a–d | `create_glyph kge1`–`kge4` | created, layer, no Unicode; 1 → 5 glyphs | as predicted |
| 1508 | the person makes `kgeL` (Kerning Left: kge1, kge2); `get_kerning_groups kgeL` | left, confirmed | as predicted: id 5140 |
| 1509 | the person makes `kgeR` (Kerning Right: kge3); `get_kerning_groups kgeR` | right, confirmed, id probably 5141 | as predicted: 5141 |
| 1510 | `set_kerning` `@kgeL : kge4` −60, `kge1 : @kgeR` −40 | both set, `applied` | as predicted: table 0 → 2, mark and panel refresh made |
| 1511 | probe `op=rename&name=kgeL&new=kgeL2&glyph=kge4` | returns True; same id, members, side; table and groups unchanged; entry −60 follows to the new name | returned True; members, side, sizes as predicted; the entry followed (old name `None`, new −60); **the id changed, 5140 → 5142**, so the probe's `renamed` read false |
| 1512 | `get_kerning kge1:kge4, kge2:kge4, kge1:kge3` | −60 from `kgeL2` (alternative: an error for id 5140) | the alternative: three errors, "belongs to kerning class id 5140, which FontLab's class list does not contain" |
| 1513 | `get_kerning_groups`, every group | `kgeL2` 5142 and `kgeR` 5141, both confirmed | as predicted |
| 1514 | the person selects the `kgeL` row in the Classes panel | repaints as `kgeL2` | not so: still `kgeL`, its member area empty, Size 2; the KERNING panel still `kgeL 2 \| kge4 \| -60` |
| 1515 | File > New Font, then back to the test font | Classes `kgeL2`; KERNING `kgeL2 \| kge4 \| -60` | as predicted |
| 1516 | `get_kerning` as 1512 (the second font closed) | still the id 5140 errors (alternative: the values) | the alternative: −60 `class : glyph` `kgeL2` twice, −40 `glyph : class` `kgeR` |
| 1517 | probe `op=rename&name=kgeL2&new=kgeR` | refused before any call | as predicted; `calls_so_far` 1 |
| 1518 | probe `op=remove&name=kgeR&pairs=keep&glyph=kge1` | returns None; gone from both sources, groups 2 → 1; table 2 → 2; entry still −40 | as predicted except the entry: the class key reads `None` after (`entry_gone` true) while the table kept 2 entries |
| 1519 | `get_kerning kge1:kge3, kge1:kge4` | an error for id 5141 | as predicted; `kge1:kge4` −60 from `kgeL2` |
| 1520 | probe `op=remove&name=kgeL2&pairs=delete&glyph=kge4` | returns None; groups 1 → 0; table 2 → 1; entry −60 → `None` | as predicted |
| 1521 | File > New Font, then back | Classes empty; KERNING one row `kge1` against the removed class, −40 (label unknown) | Classes 0 classes, as predicted; KERNING one plain row `kge1 \| kge3 \| -40`, no class marker |
| 1522 | `get_kerning kge1:kge3, kge1:kge4, kge2:kge4` (the second font closed) | −40 `glyph : glyph`; the others `none` | as predicted |

Reading (one run each): `rename` on the master's group container renames the group in FontLab's data with its members, side and class entries, but gives it a new id; `remove(name)` takes the group out and turns its class entry into a glyph : glyph pair of its one member; `remove(name, True)` also deletes the group's entries. FontLab's Classes and KERNING panels, and the glyphs' own group ids, lag behind until a switch to another font and back; until then `get_kerning` answers an error for the members, never a value. Facts and open questions: [topics/kerning.md](topics/kerning.md) §18. Seen, not explained: after the removals the status bar still named `kgeR` beside `kge3` ([WATCH-POINTS.md](WATCH-POINTS.md)). The test font `Unnamed` (`kge1`–`kge4`, one pair `kge1 : kge3` −40) holds nothing to keep.

### GR: a refresh call after a group rename (2026-11-20, listener 0.199 / server 0.81, the GE font, FontLab 8.9.5 in Demo mode, through Claude Code)

One variable against GE: after the probe's rename, ONE `flItems.notifyPackageContentUpdated(<package fgId>)` (the call `set_kerning` makes after a write, §14), through `/debug/trynotify?stage=call&which=package_content&on=class&id_from=fg`, and no font switch. One font open throughout. Every prediction was stated in chat before its call or GUI step. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1523 | the person makes `kgeM` (Kerning Left: kge1, kge2); `get_kerning_groups kgeM` | left, confirmed, id probably 5143 | as predicted: 5143 |
| 1524 | `set_kerning` `@kgeM : kge4` −70 | set, `applied`; table 1 → 2 | as predicted |
| 1525 | probe `op=rename&name=kgeM&new=kgeN&glyph=kge4` | as 1511: entry follows, the id changes | as predicted: 5143 → 5144, entry −70 under `kgeN`, old name `None`, table and groups unchanged |
| 1526 | `get_kerning kge1:kge4` (the control) | an error for id 5143 | as predicted |
| 1527 | `notifyPackageContentUpdated(4186)` on the `flItems` class | no error, nothing else changed | as predicted: returned `None`, `side_effect_detected` false, the glyph's content and the glyph count unchanged |
| 1528 | `get_kerning kge1:kge4, kge2:kge4` | still the id 5143 error (low confidence; alternative: the values) | the alternative: both −70 `class : glyph` `kgeN` |
| 1529 | screenshot of the Classes and KERNING panels, no click, no font switch | `kgeN` in both | as predicted: Classes `kgeN` (2), KERNING `kgeN 2 \| kge4 \| -70`, the status bar `kgeN` beside `kge2` |

Reading (one run): after an API group rename, one `notifyPackageContentUpdated(<package fgId>)` brings FontLab's Classes and KERNING panels and the glyphs' group ids up to date without a font switch. Not run: the same call after a removal. The GE font now also holds `kgeN` (kge1, kge2) and its entry `kgeN : kge4` −70, nothing to keep.

### GL: removing a group of two members, with the refresh (2026-11-20, listener 0.199 / server 0.81, the GE font, FontLab 8.9.5 in Demo mode, through Claude Code)

The state before: the class `kgeN` (kge1, kge2, left, id 5144), the entry `kgeN : kge4` −70 and the glyph pair `kge1 : kge3` −40, table 2. One font open throughout, no font switch. Every prediction was stated in chat before its call or GUI step. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1530 | probe `op=remove&name=kgeN&pairs=keep&glyph=kge4` | returns None; groups 1 → 0; table 2 → 3 (one glyph pair per member; alternative: 2); the class key `None` after | as predicted: table 2 → 3 (`table_entries_removed` −1) |
| 1531 | `get_kerning kge1:kge4, kge2:kge4`, before the refresh | errors for id 5144 | errors, as predicted, with another reason: no group was left, so `getAllGroups()` returned `None` ("the class names could not be read") |
| 1532 | `notifyPackageContentUpdated(4186)` on the `flItems` class | no error, nothing else changed | as predicted |
| 1533 | `get_kerning kge1:kge4, kge2:kge4, kge1:kge3` | −70, −70, −40, all `glyph : glyph` | as predicted |
| 1534 | screenshot of the Classes and KERNING panels, no click, no font switch | 0 classes; three plain rows | as predicted: `kge1 \| kge3 \| -40`, `kge1 \| kge4 \| -70`, `kge2 \| kge4 \| -70`; the status bar's class field empty for the selected `kge2` |

Reading (one run): `remove(name)` replaces a class entry with one glyph pair per member, with the class value; after a removal, one `notifyPackageContentUpdated(<package fgId>)` brings `get_kerning` and both panels up to date, as after a rename (GR). Seen: before the refresh, `get_kerning` names an empty class list as the reason a member's pair could not be read; still an error, never a zero. The GE font now holds `kge1`–`kge4`, no class, and the glyph pairs `kge1 : kge3` −40, `kge1 : kge4` −70, `kge2 : kge4` −70; nothing to keep.

### GK: removing with kept pairs, a class : class entry and a Kerning both group (2026-11-20, listener 0.199 / server 0.81, the GE font, FontLab 8.9.5 in Demo mode, through Claude Code)

The state before: no class; the glyph pairs `kge1 : kge3` −40, `kge1 : kge4` −70, `kge2 : kge4` −70; table 3. One font open throughout, no font switch. Classes made by the person in the Classes panel. Every prediction was stated in chat before its call or GUI step. The listener was restarted before 1543 to reset the refresh probe's limit. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1535 | `create_glyph kge5` | created; 5 → 6 glyphs | as predicted |
| 1536a–c | the person makes `kgeP` (Kerning Left: kge1, kge2), `kgeQ` (Kerning Right: kge3, kge4), `kgeB` (Kerning both: kge5) | — | made, seen in the Classes panel |
| 1537 | `get_kerning_groups`, every group | three groups, confirmed, left / right / both | as predicted: ids 5146, 5147, 5148 |
| 1538 | `set_kerning` `@kgeP : @kgeQ` −30, `@kgeB : kge1` −20, `kge2 : @kgeB` −25 | all set; −30 `covered` (its sample `kge1 : kge3` keeps −40), the others `applied`; table 3 → 6 | as predicted |
| 1539 | probe `op=remove&name=kgeQ&pairs=keep` | groups 3 → 2; table 6 → 7: the class : class entry becomes one class : glyph entry per member (low confidence; alternative: 6) | the call ran, but its reply was lost: the agent's command ran in the wrong folder and piped the reply into a command that failed. Its return value and its own before-and-after readings are not on record |
| 1539b | `get_kerning_groups`, every group; `get_kerning kge2:kge3` (for `table_size`) | `kgeP` and `kgeB` only; table 7; the pair an error before the refresh | as predicted: `table_size` 7; the error names id 5147 |
| 1540 | `notifyPackageContentUpdated(4186)` | no error | as predicted (call 3 of 3 of that listener run) |
| 1541 | `get_kerning kge2:kge3, kge2:kge4, kge1:kge3, kge1:kge4` | −30 `class : glyph` `kgeP`; −70, −40, −70 `glyph : glyph` | as predicted |
| 1542 | probe `op=remove&name=kgeB&pairs=keep&glyph=kge1` | groups 2 → 1; table 7 → 7; the entry `kgeB : kge1` −20 → `None` | as predicted; returned `None` |
| — | the person's screenshot after the listener restart, before 1543 | (none stated) | KERNING: `kgeP \| kge3 \| -30`, `kgeP \| kge4 \| -30`, and still `kgeB \| kge1 \| -20`, `kge2 \| kgeB \| -25`; Classes still `kgeP`, `kgeB` |
| 1543 | `notifyPackageContentUpdated(4186)`, after the restart | no error | as predicted |
| 1544 | `get_kerning kge5:kge1, kge2:kge5, kge2:kge3` | −20, −25 `glyph : glyph`; −30 from `kgeP` | as predicted |
| 1545 | screenshot of the Classes and KERNING panels, no click, no font switch | Classes `kgeP` only; KERNING the four rows, no `kgeB` | as predicted: `kgeP \| kge3 \| -30`, `kgeP \| kge4 \| -30`, `kge2 \| kge5 \| -25`, `kge5 \| kge1 \| -20`; the status bar's class field empty for `kge5` |

Reading (one run each): under `remove(name)`, a class : class entry against the removed group becomes one class : glyph entry per member of the removed group, and member pairs that already had a glyph entry keep it; a Kerning both group's entries on either side become glyph pairs of its member; after each removal one `notifyPackageContentUpdated(<package fgId>)` brought `get_kerning` and both panels up to date. Not run: removing the left group of a class : class pair. The GE font now holds `kge1`–`kge5`, the class `kgeP` (kge1, kge2), the entries `kgeP : kge3` −30, `kgeP : kge4` −30, and the glyph pairs `kge1 : kge3` −40, `kge1 : kge4` −70, `kge2 : kge4` −70, `kge5 : kge1` −20, `kge2 : kge5` −25; nothing to keep.

### GT: `rename_kerning_group` and `remove_kerning_group` live (2026-11-20, listener 0.200 / server 0.82, FontLab 8.9.5 in Demo mode, through Claude Code, a new session)

A new unsaved font, one master, one font open except in 1573–1575. Classes made by the person in the Classes panel; class entries written by `set_kerning`. Every prediction was stated in chat before its call or GUI step; 1546 and the GUI steps 1550a–c, 1573 and 1575 had none. 1559–1560 were added during the run to test a theory raised by 1556–1558. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1546 | the person closes the open `Unnamed` (the GE font) without saving | (none stated) | closed |
| 1547 | `fontlab_status` | 0.200 / 0.82, no font open | as predicted |
| 1548 | `create_font`, no family | `Unnamed Regular`, 1 font open | as predicted |
| 1549a–e | `create_glyph kgr1`–`kgr5` | created, layer, no Unicode; 1 → 6 glyphs | as predicted |
| 1550a–c | the person makes `kgrL` (Kerning Left: kgr1, kgr2), `kgrR` (Kerning Right: kgr3), `kgrO` (OpenType: kgr5) | — | made; the Classes footer read "2 classes" with three rows listed, "3 classes" by 1555 |
| 1551 | `get_kerning_groups`, every group | `kgrL` left, `kgrR` right, confirmed; `kgrO` not listed | as predicted: ids 5154, 5155 |
| 1552 | `set_kerning` `@kgrL : kgr4` −60, `kgr1 : @kgrR` −40 | both set, `applied`; table 0 → 2 | as predicted |
| 1553 | rename `kgrL` → `kgrM` | `renamed`; left, kgr1 and kgr2; id changed; table 2 → 2; mark, refresh, `caught_up` true; OUTPUT without the lag clause | as predicted: id 5154 → 5158 |
| 1554 | `get_kerning kgr1:kgr4, kgr2:kgr4`, no font switch | −60 twice, `class : glyph` `kgrM` | as predicted |
| 1555 | screenshot of the Classes, KERNING and OUTPUT panels, no click | `kgrM` in both panels; the OUTPUT line "renamed (verified, id 5154 -> 5158)" | as predicted: `kgrM 2 \| kgr4 \| -60`, `kgr1 \| kgrR \| -40` |
| 1556 | rename `@kgrM` → `kgr1` (a member's name) | `renamed`, `same_name_glyph` true; the id changes to a higher number | `renamed`, `same_name_glyph` true, `caught_up` true; **the id went 5158 → 5149**, lower than every id seen in the font |
| 1557 | `get_kerning kgr1:kgr4` | −60 from the class `kgr1` | as predicted |
| 1558 | rename `kgr1` → `kgrL` | `renamed`, `same_name_glyph` false; id changed (no direction stated) | as predicted: 5149 → **5154**, the id `kgrL` had in 1551 |
| 1559 | rename `kgrL` → `kgr2` (a test of the theory: an id follows the name, glyph names numbered first) | `renamed`, `same_name_glyph` true; id **5150** | as predicted |
| 1560 | rename `kgr2` → `kgrL` | `renamed`; id **5154** | as predicted |
| 1561 | rename `kgrL` → `kgrR` | refused: a kerning group's name; nothing changed | refused as predicted; the reply ends "nothing was renamed", not the predicted "Nothing was changed" |
| 1562 | rename `kgrL` → `kgrO` | refused: a class's name | as predicted (wording as 1561) |
| 1563 | rename `kgrO` → `kgrX` | refused: a class, not a kerning group | as predicted (wording as 1561) |
| 1564 | `remove_kerning_group kgrO keep` | refused before any dialog | as predicted: no dialog; "nothing was removed" |
| 1565 | `remove_kerning_group kgrQ delete` | refused: no such kerning group | as predicted |
| — | control: `get_kerning_groups`, `get_kerning kgr1:kgr4, kgr1:kgr3`; screenshot of OUTPUT | nothing changed; five REFUSED lines | as predicted: 5154 left, 5155 right; −60, −40; table 2 |
| 1566 | `remove_kerning_group kgrR keep`, the person to click No | the dialog names `kgrR` (Kerning Right, 1 member: kgr3) and kept kerning; after No: not approved, nothing changed | the dialog as predicted; **the call ended after 60 s with "Request timed out"** (Claude Code's MCP log: "failed after 60s") while the dialog stayed open; the person clicked No about 2.5 minutes after the timeout; the OUTPUT line "you answered No in FontLab, nothing removed" |
| 1567 | `get_kerning_groups`; `get_kerning kgr1:kgr3, kgr1:kgr4` | `kgrR` still there; −40 from `kgrR` | as predicted; nothing changed. This call took 830 ms (others 40–80 ms) |
| 1568 | `remove_kerning_group kgrR keep`, the person clicks Yes | `removed`; table 2 → 2; `caught_up` true | as predicted (kgr3's group id 0); 34 s with the dialog |
| 1569 | `get_kerning kgr1:kgr3` | −40 `glyph : glyph` | as predicted |
| 1570 | `remove_kerning_group kgrL delete`, Yes | `removed`; table 2 → 1; `caught_up` true | as predicted; 7 s with the dialog |
| 1571 | `get_kerning kgr1:kgr4, kgr2:kgr4, kgr1:kgr3` | none, none, −40 | as predicted |
| 1572 | screenshot of the three panels, no click, no font switch | Classes `kgrO` only; KERNING one plain row; the No, keep and delete lines in OUTPUT | as predicted: `kgr1 \| kgr3 \| -40`; "kerning entries 2 -> 2", "2 -> 1" |
| 1573 | the person: File > New Font (`Unnamed1` in front) | — | done |
| 1574 | rename `kgrO` → `kgrZ` | refused: the current font cannot be matched to its kerning table; `fonts_open` 2 | as predicted; the reply also named the font switch |
| 1575 | the person closes `Unnamed1` | — | closed, no question |
| 1576 | `finish_changes` | a save reminder | the reminder, but **`changes_in_package` 2**; `fontlab_status` then gave `glyphbridge_changes_this_session` 2, where about 14 changes were made (1548–1570) |

Reading (one run each): both tools work in FontLab as designed: renames verified by both sources, entries following the new name, the panels and `get_kerning` up to date at once through the refresh; removals with `keep` and `delete` as the GE research found; No changed nothing; every refusal came before any change or dialog. **Seen, not explained** ([WATCH-POINTS.md](WATCH-POINTS.md)): a group's id followed its name (`kgrL` 5154 three times, `kgr1` 5149, `kgr2` 5150); and Claude Code ended the removal call at 60 s while FontLab's dialog still waited. After that timeout the change count started again from zero: a new Glyphbridge server process, started by Claude Desktop's main process at the moment of 1567, ran from then on, while the server process Claude Code started at the session's start kept running and its MCP log shows one connection only; which process served which call was not read. The test font `Unnamed` (`kgr1`–`kgr5`, the OpenType class `kgrO`, one pair `kgr1 : kgr3` −40) holds nothing to keep.

### TO: the client's time limit during a FontLab dialog (2026-11-21, listener 0.200 / server 0.82, FontLab 8.9.5 in Demo mode, through Claude Code 2.1.326 in Claude Desktop's Code tab)

A new unsaved font, one master, one font open. Research question (a) of the item in [ROADMAP.md](ROADMAP.md). Every prediction was stated in chat before its call; 1582 was added during the run. No stage needed a save. Nothing was saved. Before the run three Glyphbridge server instances ran: two started by Claude Desktop's main process (Python processes 13588 and 15820), one by Claude Code from `.mcp.json` (17740).

| # | Step | Predicted | Result |
|---|---|---|---|
| 1577 | `fontlab_status` | listener 0.200, server 0.82 | as predicted; no font open |
| 1578 | `create_font`, no name | a new unsaved font `Unnamed…` in front | `Unnamed Regular`, fonts 0 → 1 |
| 1579 | `create_glyph tmo1` | created, verified | created, layer `Regular`, synced |
| 1580 | a monitor records every 0.5 s which process holds a connection to port 8765; `delete_glyph tmo1`; the person waits until the call has ended, then clicks No | the call ends at 60 s ±3 with "Request timed out"; a process started by Claude Desktop holds the connection | as predicted: 60.007 s (Claude Code's MCP log: "failed after 60s"); 15820 held the connection from the call's start until the No, 79 s after the call began; OUTPUT: "you answered No in FontLab, nothing deleted" |
| 1581 | `list_glyphs`; the process list before and after | `.notdef`, `tmo1`; a new instance started by Claude Desktop appears | as predicted: after the call 15820 was gone and a new instance, started by Claude Desktop at the moment of the call, ran; 17740 still ran |
| 1582 | `fontlab_status`, then `finish_changes` | no change count; `save_reminder` null | as predicted: `changes_in_package` 0, although the font holds two tool changes |

Reading (one run): the Code tab's Glyphbridge calls went to a server instance started by Claude Desktop, not to the one Claude Code started. The call ended at 60 s while the server and the listener went on waiting, and FontLab acted on the later answer. Claude Desktop then replaced that instance, and the new one counted no changes, so the save reminder was lost. Not measured: which instance served 1577–1579 and 1581–1582 (the monitor misses short calls). Claude Code's own limit for a stdio server is about 28 hours (its code and its documentation) and covers the instance it started, which was not used; so the 60 s lies on the path through Claude Desktop, either in Claude Desktop's own client or in the link from Claude Code to it. Claude Desktop's code could not be read. The font `Unnamed` (`tmo1`) holds nothing to keep.

### TO2: the same from the Desktop chat (2026-11-21, listener 0.200 / server 0.82, FontLab 8.9.5 in Demo mode; the delete from a new Claude Desktop chat conversation, the other calls through Claude Code in the Code tab)

The TO font, one font open. One variable changed from TO 1580: the client of the delete call. Every prediction was stated in chat before its call. No stage needed a save. Nothing was saved. A monitor logged each change in which process held a connection to port 8765.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1583 | the process list; the monitor started | instances 13588 and 3076 (started by Claude Desktop), 17740 (Claude Code) | as predicted |
| 1584 | `create_glyph tmd1` | created, verified | as predicted; served by 3076 |
| 1585 | the person, in a new Desktop chat conversation: a prompt to call `delete_glyph tmd1` once and nothing else; No after the call has ended, or at 100 s | the call ends at 60 s ±3 with a timeout; 13588 holds the connection | **both failed:** the chat ended the call after about 80 s ("timed out after 80 seconds, with no reply from your computer", the machine named; the call showed 1m 22s); 3076 held the connection for 120.05 s, the server's own limit, which ran out ("did not answer /glyph/delete within 120s"). The chat's first call used a wrong argument (`glyph_name`) and was refused by the server before the listener. The person clicked No several minutes after the chat's reply; OUTPUT at 16:02:55: "you answered No in FontLab, nothing deleted", 6.4 minutes after the server had stopped waiting |
| 1586 | `list_glyphs`; the process list | `.notdef`, `tmo1`, `tmd1`; 3076 not replaced | as predicted |
| 1587 | `finish_changes` (Code tab) | 1 change | as predicted; not predicted: `uncertain_changes_in_package` 1, the chat's timed-out delete |

Reading (one run): the Desktop chat reaches this PC through a remote link and gave up after about 80 s (its own wording; not logged on this PC), not 60 s like the Code tab. It used the same server instance as the Code tab, so the Code tab's `finish_changes` counted the chat's uncertain delete; after the chat's timeout that instance was not replaced. The listener acted on the No given after the server had stopped waiting and printed its OUTPUT line; no agent was told. The TO font now also holds `tmd1`; nothing to keep.

### SC: a dialog that closes itself (2026-11-21, listener 0.200 for 1588–1589 and 0.201 for 1590–1593, FontLab 8.9.5 in Demo mode, probe calls through PowerShell)

Research for option C ([DECISIONS.md](DECISIONS.md), 2026-11-21). Every prediction was stated in chat before its call. The prediction of 1593 was changed before its run: first, that the Python timer would not fire, as the listener's poll timer does not run during a dialog; then, after reading that Qt only refuses to fire a timer again while its own handler runs, that it would fire. No font was touched; the TO font stayed open. No stage needed a save. The person acted only on the dialogs, with the mouse.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1588 | names only, `/debug/moddir`: `QTimer` in `PythonQt.QtCore` | all members present; a form that connects to another Qt object's slot | as predicted: `connect(signal, receiver, slot, type) -> bool`, `singleShot(msec, timerType, receiver, member)` |
| 1589 | names only: `QMessageBox` | in `PythonQt.QtGui`; all members present, `exec_` among them | in `PythonQt.QtGui` (`PythonQt.QtWidgets` is not loaded); `done`, `reject`, `close`, `clickedButton`, `result`, `open`, `exec` present; `exec_` is listed as "not a public member", although every product dialog calls it live |
| 1590 | `/debug/trydialogtimeout?how=slot&seconds=10&go=yes`; no click | closes itself at 10 s ±0.5; no button; not Yes | as predicted: 10.0 s, `clicked_button` null, `exec_result` 0 |
| 1591 | `how=slot&seconds=20`; the person clicks Yes | Yes; the timer stopped | as predicted: Yes at 1.375 s (`exec_result` 16384); the timer still ran at the click and was stopped. Reading the button's label failed ("'str' object is not callable": `text` is a property in PythonQt) |
| 1592 | `how=slot&seconds=20`; the person clicks No | No | as predicted: No at 1.656 s (65536); the same label failure |
| 1593 | `how=python&seconds=10`; no click | (changed before the run) the timer fires and closes the dialog at 10 s ±0.5 | as predicted: `timer_fired` 1 at 10.0 s, closed at 10.015 s, no button |

Reading (one run each): a single-shot `QTimer` owned by the dialog closes a waiting `exec_()` dialog on time, through a pure Qt connection to `reject()` or through a Python function; a click before then counts as usual. Only the timer that opened the dialog, the listener's poll, is held up during it. 4 of the probe's 10 runs were used.

### CD: a countdown in the self-closing dialog (2026-11-21, listener 0.201 for 1594–1595 and 0.202 for 1596–1598, FontLab 8.9.5 in Demo mode, probe calls through PowerShell)

Research for the countdown of the self-closing dialog design ([DECISIONS.md](DECISIONS.md), 2026-11-21). Every prediction was stated in chat before its call. No font was touched; the TO font stayed open. No stage needed a save. The person acted only on the dialogs, with the mouse, and reported what the button showed.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1594 | names only, `/debug/moddir`: `QMessageBox`: `button`, `defaultButton` | both present; `button(which)` returns a `QAbstractButton` | as predicted: `button(which) -> QAbstractButton`, `defaultButton() -> QPushButton` |
| 1595 | names only: `QAbstractButton`, `QPushButton`: `setText`, `text` | `setText(text)` a method; `text` a property | as predicted: `setText(text)` documented; `text` public with no docstring |
| 1596 | `/debug/trydialogtimeout?how=slot&seconds=10&countdown=yes&go=yes`; no click | the No button counts down "No (10)" to "No (1)"; closes at 10 s ±0.5; 9 or 10 ticks; not Yes | as predicted: 10.0 s, 9 ticks, last label "No (1)", no error; the person saw the label change each second |
| 1597 | `seconds=20&countdown=yes`; the person clicks No early | No, about 5 s; the ticks stop at the click | No at 11.45 s (the click came later than predicted; nothing the test checks depends on it); 11 ticks, stopped; clicked button read as "No (9)" |
| 1598 | `seconds=20&countdown=yes`; the person clicks Yes | Yes; the countdown changes nothing | as predicted: Yes at 4.985 s, 4 ticks to "No (16)", no error |

Reading (one run each): a second `QTimer` owned by the dialog relabels its button visibly once a second while `exec_()` waits; the closing timer is unaffected, and a click before the end counts as usual. The clicked button's label reads correctly as the property `text` (the flaw of SC 1591, 1592). 3 of the probe's 10 runs were used.

### SD: self-closing dialogs and the `.notdef` notice live (2026-11-24, listener 0.203 / server 0.84, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The live checks of listener 0.203 / server 0.83 (self-closing dialogs, the `.notdef` notice without a dialog) and server 0.84 (an empty `.notdef` in a font in progress left alone). A new session; no font open at the start; one font open throughout. Every prediction was stated in chat before its call or GUI step. The person acted only on the dialogs and in the Classes panel, and reported the dialogs and the OUTPUT panel by screenshot. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1599 | `fontlab_status` | 0.203 / 0.84, no `compatibility_note` | as predicted; no font open |
| 1600 | `create_font`, no family | `Unnamed Regular`; no `notdef_note`, no mention of `.notdef` | as predicted |
| 1601 | `get_current_font` | `notdef` `empty`, `font_mature` false, `noted_in_output_panel` false, "Say nothing about .notdef"; no `.notdef` line in OUTPUT | as predicted (0 of 52 letters) |
| 1602 | `check_notdef` | the same; the instruction begins "If the person asked about .notdef" | as predicted; OUTPUT for 1601–1602: only "reads: font info 1, .notdef check 2" |
| 1603 | `create_glyph sdc1` | created, layer `Regular`, no Unicode | as predicted |
| 1604 | `delete_glyph sdc1`; no answer | Yes/No, default No; the No button counts down; the text says what happens without an answer; closes at about 45 s; `not_answered_in_time`, nothing changed; one OUTPUT line | as predicted: the person's screenshot showed "No (10)" and "…closes by itself in 45 seconds and nothing is…"; OUTPUT "delete sdc1: not answered within 45 s, nothing deleted"; the call returned within the Code tab's 60 s. Seen: the Claude window partly covered the dialog ([WATCH-POINTS.md](WATCH-POINTS.md)) |
| 1604a | `list_glyphs` | `.notdef`, `sdc1` | as predicted |
| 1605 | `delete_glyph sdc1`; the person clicks No below "No (40)" | declined, expected behaviour, nothing changed | as predicted; OUTPUT "you answered No in FontLab, nothing deleted" |
| 1606 | `create_glyph sdc2` | created, layer `Regular`; 3 glyphs | as predicted |
| 1607 | `delete_glyph sdc1`; the person clicks Yes | deleted 3 → 2, marked `via_glyph` `sdc2`, no `save_question_note` | as predicted; OUTPUT "deleted after your Yes (verified, glyphs 3 -> 2)" |
| 1608 | `delete_glyph .notdef`; the person screenshots, then clicks No | its own warning (every font needs `.notdef` as glyph 0); default No, countdown; declined | as predicted: "This is the .notdef glyph. Every font needs one as glyph 0 … Deleting it leaves the font without one."; "No (25)"; OUTPUT "delete .notdef: you answered No in FontLab, nothing deleted" |
| 1609 | `create_glyph sdc3` | created, layer `Regular`; 3 glyphs | as predicted |
| 1609a | the person makes `sdcL` (Kerning Left: `sdc2`, `sdc3`) in the Classes panel | — | made; the panel shows `sdcL`, size 2 |
| 1610 | `get_kerning_groups sdcL` | `left`, `sdc2` `sdc3`, `confirmed` | as predicted, id 5116 |
| 1611 | `remove_kerning_group sdcL`, `pairs=delete`; no answer | the dialog names the group, side, members and that its entries are deleted; countdown; closes at about 45 s; `not_answered_in_time`, nothing changed; one OUTPUT line | as predicted: "(Kerning Left, 2 members: sdc2, sdc3)", "Its kerning entries are deleted with it.", "No Glyphbridge tool can bring a removed group back.", "No (33)"; OUTPUT "kerning group remove sdcL: not answered within 45 s, nothing removed" |
| 1611a | `get_kerning_groups sdcL` | unchanged | as predicted, id 5116 |
| 1612 | `create_glyph` `A`–`Z`, `a`–`z` (52 calls) | each created, layer `Regular`, its own codepoint assigned by FontLab; 55 glyphs; 52 OUTPUT lines | every reply as predicted. **OUTPUT not as predicted:** three lines, then "create: 49 more like this, all verified", the listener's documented folding of repeated lines ([topics/server-and-endpoints.md](topics/server-and-endpoints.md) §4); the prediction was wrong, not the code |
| 1613 | `get_current_font` (control: every letter, none drawn) | `letters_present` 52, `font_mature` false, not noted, "Say nothing" | as predicted (`letters_checked_for_outline` 52) |
| 1614 | `draw_polygon n` [[50,0],[450,0],[450,500],[50,500]] | `verified`, 1 shape, 1 contour, 4 nodes; width unchanged | as predicted; advance width 0 (a tool-made glyph's start) |
| 1615 | `get_current_font` | `font_mature` true, `noted_in_output_panel` true, the "may have been overlooked" instruction; one OUTPUT line | as predicted (`drawn_letter` `n`, `letters_checked_for_outline` 1, `already_noted` false); OUTPUT ".notdef is empty; … this font has every letter A-Z and a-z, so it may have been overlooked" |
| 1616 | `get_current_font` again | `already_noted` true, nothing noted, no second line | as predicted: "Mention .notdef again only if it is relevant"; no second line. The read summary after it said ".notdef check 2" for one call; perhaps the re-check of 1615's note is counted there (not tested) |
| 1617 | `finish_changes` | `changes_in_package` 58 (the font 1, glyphs 55, the delete 1, the drawing 1), if no app replaced the server | as predicted: 58, `uncertain` 0 |

Reading (one run each): both dialog tools close an unanswered dialog by themselves at 45 s with a visible countdown, before the Code tab's 60 s limit, and report `not_answered_in_time` with nothing changed; No and Yes within the time act as before; deleting `.notdef` gets its own text. An empty `.notdef` is not raised in a new font nor in one with every letter but none drawn; it is raised once, in chat and in OUTPUT, once a letter is drawn, then stays quiet. Not run: a font without `.notdef` (it needs a Yes to delete it). The SD font `Unnamed` (unsaved): `.notdef`, `sdc2`, `sdc3`, `A`–`Z`, `a`–`z` (`n` drawn), the class `sdcL`; nothing to keep.

### CL: the change log live (2026-11-24, listener 0.204 / server 0.85, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The live checks of listener 0.204 / server 0.85 (the change log, both counts; [CHANGELOG.md](CHANGELOG.md)). The listener, Claude Desktop and the session were restarted before 1618. The SD font `Unnamed` (unsaved) stayed open and untouched; the tests used a new font, prefix `clg`. Every prediction was stated in chat before its call or step. The person restarted the listener (1625) and reported the OUTPUT panel by screenshot. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1618 | `fontlab_status` | 0.204 / 0.85, no `compatibility_note`; `changes_by_font` empty or all zero (a new listener run); nothing counted this session | versions as predicted; `changes_by_font` absent: the server leaves it out when the log has no totals (and also when `/changes` cannot be read, [WATCH-POINTS.md](WATCH-POINTS.md)) |
| 1619 | `create_font` (no family), `create_glyph clg1`, `set_glyph_width clg1 500` | `Unnamed1 Regular`, 2 fonts; `clg1` created, layer `Regular`, no Unicode; width 0 → 500, verified, no `width_rounded` | as predicted; `create_font` did not mark the font (no name given) |
| 1620 | `fontlab_status` | this session 3, uncertain 0; `changes_by_font` one row, `Unnamed1 Regular` 3, uncertain 0 | as predicted, with `changes_by_font_note` naming the listener's start time |
| 1621 | `finish_changes` | 3, uncertain 0, `change_record` `complete`, no `counts_disagree`, no `other_changes`; `fonts_changed` `Unnamed1 Regular` with 3; reminder | as predicted, except that `fonts_changed` lists names only, without counts (the prediction was wrong, not the code) |
| 1622 | `finish_changes` again (control) | 0, reminder null, no `other_changes` | as predicted; `change_record` `complete` |
| 1623 | PowerShell POST `/glyph/create` `{"name":"clg2"}`, header `X-Glyphbridge-Client: powershell-test`, no request ID | created, 2 → 3; one OUTPUT create line naming `powershell-test` | as predicted: "[powershell-test > Glyphbridge] … create clg2: created (verified, glyphs 2 -> 3)". Not predicted: the read summaries count `/changes` reads as "change log" (3 for 1620–1622, 1 for 1624) |
| 1624 | `finish_changes` | 0 in the package; `other_changes` `powershell-test`, `Unnamed1 Regular`, 1, with "may already be saved"; reminder; `complete` | as predicted |
| 1625 | the person restarts the listener; both fonts stay open | — | a new 0.204 run in OUTPUT |
| 1626 | `create_glyph clg3` | created in `Unnamed1 Regular`, 3 → 4, layer `Regular` | as predicted |
| 1627 | `finish_changes` | 1, `change_record` `incomplete` (the listener restart), reminder, no `other_changes` (1623 was in the old run's log) | as predicted: "FontLab's listener was restarted (its record starts at …). This server's own count is used where it is higher." |
| 1627a | the person reports "restarted everything"; which parts was not said | — | the step had named only Claude Desktop. Whether the listener was restarted too is not confirmed ([LESSONS.md](LESSONS.md)) |
| 1627b | `fontlab_status` (new session) | 0.204 / 0.85, no `compatibility_note`; nothing counted this session; `changes_by_font` one row, `Unnamed1 Regular` 1 | versions as predicted. **`changes_by_font` absent**: the listener's log had no totals (or `/changes` could not be read), most likely because the listener was restarted too |
| 1628 | `finish_changes` first | 0 in the package; `other_changes`: the earlier server process's 1 change (`clg3`) in `Unnamed1 Regular`, "may already be saved"; reminder once. Revised after 1627b, still before the run: if the listener was restarted, no `other_changes` and reminder null | **void:** 0, `save_reminder` null, no `other_changes`, `change_record` `complete`, matching the revised prediction. Its precondition (the listener still running) was probably not met, so it says nothing about an earlier server process's changes |
| 1629 | `finish_changes` again (control) | 0, reminder null, no `other_changes` | as predicted, `complete`. Because 1628 is void, this shows only that a second call counts nothing |
| 1630 | `create_glyph clg4` in `Unnamed1 Regular`; no `finish_changes` | created, 4 → 5, layer `Regular` | run in an earlier session; its reply is not recorded here. The listener logged 1 change in `Unnamed1 Regular` at 21:35:38 by `local-agent-mode` (seen in 1632–1633) |
| 1631 | the person fully quits Claude Desktop (tray too), reopens it and starts a new Claude Code session. **Only Claude Desktop is restarted:** FontLab and its listener keep running, and the listener is not restarted from the Scripting panel | — | done before 1632; the listener's run started at 21:28:01, before `clg4`, so the listener was not restarted (1632) |
| 1632 | `fontlab_status` | 0.204 / 0.85; nothing counted this session; `changes_by_font` `Unnamed1 Regular` 1 (`clg4`) | as predicted; no `compatibility_note`; `changes_by_font_note` names the listener's start, 21:28:01 |
| 1633 | `finish_changes` | 0 in the package; `other_changes` 1 change in `Unnamed1 Regular`, "may already be saved"; reminder once; `complete` | as predicted: `other_changes` `local-agent-mode`, `Unnamed1 Regular`, 1, uncertain 0, 21:35:38; "may already have been saved" in `other_changes_note`; `fonts_changed` `Unnamed1 Regular`. The `by` label was not predicted |
| 1634 | `finish_changes` again (control) | 0, reminder null, no `other_changes` | as predicted, `complete` |

Reading (one run each): the listener's log and the server's count agree on a package; the bookmark moves, so a second call counts nothing; a change from another client is named in `other_changes` and brings the reminder on its own; after a listener restart the record is called incomplete even though the restart fell between packages and nothing was lost, as rule 2 ("when in doubt, remind") intends: the server cannot know that. The CL font `Unnamed1` (unsaved): `.notdef`, `clg1` (width 500), `clg2`, `clg3`; nothing to keep. 1628 is void: the person was asked to restart Claude Desktop, reported "restarted everything", and the listener's log was empty afterwards; 1630–1634 repeat it with the restart named. After 1630 the CL font also holds `clg4`. 1632–1634 answer what 1628 could not: with only Claude Desktop restarted, a new server process finds the earlier process's change in the listener's log, names it in `other_changes` and brings the reminder once; a second call counts nothing. Not tested: a font that was really saved in between.

### CB: `changes_by_font` always answers, live (2026-11-24, listener 0.204 / server 0.86, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The live check of server 0.86 (`changes_by_font` always answers; [CHANGELOG.md](CHANGELOG.md)). FontLab ran with two fonts open, the CL font `Unnamed1 Regular` in front; the session's server process was 0.86 from its start. Every prediction was stated in chat before its call or step; 1635's had two branches, because whether the listener had been restarted since 1634 was not known. The person restarted only the listener (1636) and reported the OUTPUT panel by screenshot. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1635 | `fontlab_status` | 0.204 / 0.86, no `compatibility_note`; nothing counted this session; `changes_by_font` either one row `Unnamed1 Regular` 1 (`clg4`, the listener run of 1632 still going) or `[]` with a note naming the listener's start (restarted since); never absent | the first branch: one row `Unnamed1 Regular` 1, uncertain 0; the note names the start 21:28:01 |
| 1636 | the person stops the listener (PowerShell `/shutdown`) and starts it again from the Scripting panel; FontLab with both fonts, Claude Desktop and the session keep running | a new 0.204 run in OUTPUT | as predicted: "Listener stopped." and a new 0.204 run; 1635 shows there as reads at 22:10:57 |
| 1637 | `fontlab_status` | 0.204 / 0.86; **`changes_by_font` `[]`**, the note naming the new start and saying earlier changes are not known (0.85 left the field out: 1618, 1627b) | as predicted: `[]`, "No change recorded since FontLab's listener started at 22:11:20; changes before that start are not known." |
| 1638 | `create_glyph cbf1` | created in `Unnamed1 Regular`, 5 → 6, layer `Regular`, no Unicode | as predicted; synced, `fontlab_changed_mark` called |
| 1639 | `fontlab_status` | this session 1, uncertain 0; `changes_by_font` one row `Unnamed1 Regular` 1, uncertain 0, the note naming 22:11:20 | as predicted |
| 1640 | `finish_changes` | 1, uncertain 0; `fonts_changed` `Unnamed1 Regular`; reminder; no `other_changes`; `change_record` `incomplete` (the listener restarted during this server process, as in 1627) | as predicted, with "FontLab's listener was restarted (its record starts at 22:11:20)" |

Reading (one run): after a listener restart with no change, `changes_by_font` answers `[]` with a note instead of being left out; after one change it shows the row. Not run live: `"unknown"` (an unreadable `/changes`), which cannot be caused without a code change; stub-tested only. The CL font `Unnamed1` (unsaved) now also holds `cbf1`; nothing to keep.

### WF: two wording fixes live (2026-11-24, listener 0.205 / server 0.87, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The live check of listener 0.205 / server 0.87 (the underscore refusal's advice and `remove_component`'s single "nothing was changed"; [CHANGELOG.md](CHANGELOG.md)). Before 1641 the person restarted the listener (v0.205 in OUTPUT, by screenshot) and then Claude Desktop; FontLab and both fonts stayed open. The CL font `Unnamed1 Regular` was in front, prefix `cbf`. Every prediction was stated in chat before its call. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1641 | `fontlab_status` | listener 0.205, no `compatibility_note`; server 0.87 if Claude Desktop was restarted, 0.86 if not; `changes_by_font` `[]`, the note naming the new start | 0.205 / 0.87; `[]`, the start 22:34:16 |
| 1642 | `create_glyph cbfs`; `draw_polygon cbfs` (0,0)–(50,200), counterclockwise | created, 6 → 7, layer `Regular`, no Unicode; `verified`, 1 contour, 4 nodes, nothing rounded | as predicted |
| 1643 | `add_component cbf1`, list `[cbfs (0,0), cbf_x (0,0)]` | the server's refusal before any request, ending "Place such a glyph with the single form (component, x and y); that was seen live into an empty glyph, not yet beside existing content."; no OUTPUT line | as predicted, word for word |
| 1644 | the same list as a direct POST `/glyph/component` (curl, client `curl-test`) | 200, `placed: false`, `underscore_refused: true`, the reason ending "the single form (one call per glyph) placed such a glyph into an empty glyph in testing, not yet beside existing content: nothing was changed"; an OUTPUT line not predicted | as predicted; OUTPUT showed "[curl-test > Glyphbridge] … NOT DONE component cbf1 (2 components): components[1] 'cbf_x' has an underscore …" (seen in the screenshot of ED3 1655) |
| 1645 | `add_component cbf1`, single form, `cbfs` at (0, 0) | placed, `verified`, `placement` "empty layer", width unchanged | as predicted; width 0 |
| 1646 | `remove_component cbf1`, index 0, expected `clg1` at (0, 0) (the source there is `cbfs`) | refused, nothing changed: "Glyph 'cbf1': nothing was changed: entry 0 (index 0): element 0 is a component of 'cbfs', not 'clg1' (read the glyph again with get_glyph_outline)", "nothing was changed" once | as predicted. Not predicted: the server's `font_note` follows the reason with no full stop ("… get_glyph_outline) 2 fonts are open …"); the join is older than 0.87 |
| 1647 | `finish_changes` | 3, uncertain 0, `complete`, no `other_changes` (1644 was a refusal), `fonts_changed` `Unnamed1 Regular`, reminder | as predicted |

Reading (one run each): both copies of the underscore advice read as built; `remove_component`'s refusal says "nothing was changed" once. Not run: an underscore name placed with the single form beside existing content. The CL font `Unnamed1` (unsaved) now also holds `cbfs` (a 50 by 200 rectangle) and `cbf1` with one component of `cbfs`; nothing to keep.

### FN: a full stop before the font note, live (2026-11-24, listener 0.205 / server 0.88, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The live check of server 0.88 ([CHANGELOG.md](CHANGELOG.md)). Before 1648 the person restarted only Claude Desktop; FontLab with both fonts and the listener kept running (the listener did not change). The CL font `Unnamed1 Regular` was in front. Every prediction was stated in chat before its call. Nothing was changed or saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1648 | `fontlab_status` | 0.205 / 0.88, no `compatibility_note`; `changes_by_font` one row `Unnamed1 Regular` 3, uncertain 0, the start 22:34:16 | as predicted |
| 1649 | `remove_component cbf1`, index 0, expected `clg1` at (0, 0), as in WF 1646 | refused, nothing changed; "… (read the glyph again with get_glyph_outline). 2 fonts are open in FontLab; …", a full stop where 1646 had none | as predicted, word for word |

Reading (one run): the font note now follows a refusal with a full stop. Not run live: a refusal that already ends with a full stop (stub test 22w4 only). `finish_changes` was not called: nothing was changed.

### ED3: adding a contour beside a cubic outline, by probe (2026-11-24, listener 0.205 / server 0.88, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Research for P2.2 (an add-contour tool) with the existing gated probe `/debug/tryedit?stage=addcontour` (listener 0.151, unchanged); results in [topics/geometry.md](topics/geometry.md) "Editing existing outlines". The probe needs exactly one font open: before 1650 the person closed the SD font `Unnamed` without saving (gone); `fontlab_status` then read one font, `Unnamed1 Regular`. Nothing was restarted. Prefix `edp3_`. The probe calls went through curl (client `curl-ed3`). Every prediction was stated in chat before its call or step. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1650 | `create_glyph edp3_a`; `draw_path edp3_a`, a circle of radius 200 around (200, 200), 4 smooth points, counterclockwise | created, 7 → 8, layer `Regular`; `verified`, `nodes_match`, 1 contour of 12 nodes, nothing rounded | as predicted |
| 1651 | `/debug/tryedit?stage=addcontour&name=edp3_a&go=yes` | the fixed square (600–650) added as contour 1; the circle unchanged node by node, handles and smooth flags included; `mismatches` empty; glyph count 8; no side effect; synced; marked; call 1 of the run | as predicted; the probe's margins after it still read rsb −400 (the nodes give −650) |
| 1652 | `get_glyph_outline edp3_a` | both contours as built; `unverified` (stale sidebearings); `inkBox()` current, top 650 | as predicted: ink width 400 against the nodes' 650; `inkBox()` 0–650 |
| 1653 | control: `create_glyph edp3_b` (8 → 9), `draw_polygon` (100, 100)–(500, 500), then the probe | `verified`; the square added after the first, no mismatches, glyph count 9, no side effect, synced, marked, call 2 (as ED2 973) | as predicted; margins after it rsb −500 (the nodes give −650) |
| 1654 | `finish_changes` | 4 (two creates, two drawings), uncertain 0, `complete`; the probe edits not in the change log; `other_changes` the earlier 0.87 process's 3 (WF); `fonts_changed` `Unnamed1 Regular`; reminder | as predicted: `other_changes` `local-agent-mode`, 3, 22:34:59–22:35:18; no `curl-ed3` entry |
| 1655 | the person opened `edp3_a` and pressed Edit > Undo once (screenshot) | the added square stays (as `move_nodes`, 1023) | as predicted: Undo greyed out. Seen as well: the glyph panel read LSB 0, RSB −650 (caught up after the glyph was opened) |
| 1656 | `get_glyph_outline edp3_a` | `verified`, both contours unchanged, ink width 650, rsb −650 | as predicted |

Reading (one run each): `shape.shapeData.addContour` leaves an existing cubic contour exactly as it was, smooth flags included; FontLab's sidebearings lag after the add until a GUI event (here opening the glyph), as in ED2; Edit > Undo offers nothing; the probe's edits mark the font but are not in the listener's change log (debug routes). Not tested: a curved or open contour added (the probe adds only its fixed square), a shape with its own transform, several shapes, components, Power Brush. The CL font `Unnamed1` (unsaved) now also holds `edp3_a` (circle and square) and `edp3_b` (two squares); nothing to keep.

### ED4: adding curved and open contours, by probe (2026-11-24, listener 0.206 / server 0.88, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Research for P2.2 (the add-contour tool, the user's choice B: a probe before the build) with `/debug/tryedit?stage=addcontour&kind=…` (listener 0.206, [CHANGELOG.md](CHANGELOG.md)); results in [topics/geometry.md](topics/geometry.md) "Editing existing outlines". Before 1657 the person restarted only the listener (new code); Claude Desktop and FontLab kept running. One font was open, the CL font `Unnamed1`. Prefix `edp4_`. The probe calls went through curl (client `curl-ed4`). Every prediction was stated in chat before its call or step. No stage needed a save. Nothing was saved.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1657 | `fontlab_status` | listener 0.206, server 0.88, one font `Unnamed1 Regular` | as predicted (the reply holds no glyph count); not predicted: the server counted the 4 ED3 changes, the listener's record empty since its start at 23:36:32 |
| 1658 | `create_glyph edp4_a`; `draw_path` a circle of radius 200 around (200, 200), 4 smooth points | created, 9 → 10, layer `Regular`; `verified`, 12 nodes, nothing rounded | as predicted; left 0, right −400, advance 0 |
| 1659 | probe `kind=cubic` on `edp4_a` | the circle of radius 100 around (700, 300) added last, its 12 nodes, handles and smooth flags as built; the first circle unchanged; no mismatch, no side effect; glyph count 10; synced; marked; call 1; the sidebearings still left 0 / right −400 | as predicted |
| 1660 | probe `kind=open` on `edp4_a` | the arch (105, 104)–(398, 104), handles (105, 280), (398, 255), added last with `closed` false; both circles unchanged; call 2; the sidebearings still left 0 / right −400 | as predicted except the sidebearings: right −800, the value after 1659, caught up between the calls with no GUI event made by the agent (cause unknown); the arch stays within 0–400, so this call could not show a lag of its own |
| 1661 | `create_glyph edp4_b`; `draw_path` a square (200, 0)–(300, 100) | created, 10 → 11; `verified`, 4 nodes, left 200, right −300 | as predicted |
| 1662 | probe `kind=open` on `edp4_b` | the arch added last, exact; the square unchanged; call 3; the sidebearings still left 200 / right −300 (the nodes give 105 / −398) | as predicted |
| 1663 | control: `create_glyph edp4_c` (11 → 12), the same circle as 1658, then probe `kind=square` (default) | the square (600–650) added last; the circle unchanged; call 4; the sidebearings still left 0 / right −400 (the nodes give −650) | as predicted |
| 1664 | the person opened FontLab's Edit menu (screenshot) | Undo greyed out (as ED3 1655) | as predicted: Undo and Redo greyed out |

Afterwards (no number, nothing predicted): `finish_changes` counted 6 (three creates, three drawings; the probe's edits are not in the change log), `change_record` `incomplete` (the listener restart), the reminder shown.

Reading (one run each): `shape.shapeData.addContour` adds a closed cubic contour and an open contour to the existing shape exactly as built, beside a straight and a cubic outline, and leaves every old node, kind and smooth flag as it was; FontLab's sidebearings lagged after the add (1662, 1663) and once had caught up before the next call (1660); Edit > Undo offered nothing. Not tested: a shape with its own transform, several shapes, components, Power Brush, other masters. The CL font `Unnamed1` (unsaved) now also holds `edp4_a` (two circles and the arch), `edp4_b` (square and arch), `edp4_c` (circle and square); nothing to keep.

### AD: `add_contours` live (2026-11-25, listener 0.207 / server 0.89, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The first live checks of `add_contours` (P2.2; design in [DECISIONS.md](DECISIONS.md), 2026-11-24). Before the session the person restarted the listener and Claude Desktop ("probably", the user's words); `fontlab_status` read listener 0.207 started at 00:17:38 with no change recorded, and server 0.89, so both ran the new code; FontLab kept running. A new Claude Code session. One font was open, the CL font `Unnamed1`. Prefix `adc1_`. Every prediction was stated in chat before its call or step, except where marked. No stage needed a save. Nothing was saved. One run each, one master.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1665 | `create_glyph adc1_o`; `draw_path` a square (100, 0)–(500, 600), counterclockwise | `verified`, 4 nodes, left 100, width W | as predicted, W = 0 (stated before 1666: right −500) |
| 1666 | `add_contours adc1_o`, `expected_contours` 1, a clockwise counter (200, 100)–(400, 500) | `added`, `verified`, `nodes_match`, `new_contour_indices` [1], nothing rounded; left 100, right −500, ink width 400; FontLab's values current (the counter is inside the old box); `undo_note`; one OUTPUT line | as predicted; `contour_sizes` [4] lists the new contour only (not said in the reply) |
| 1667 | `get_glyph_outline adc1_o` | `verified`, 2 contours, contour 0 counterclockwise, contour 1 clockwise | as predicted; FontLab's ink box 0–600 agrees. The person's screenshot: the grid thumbnail shows the hole unfilled, width 0; OUTPUT lines for the create, draw, add and read |
| 1668 | `create_glyph adc1_c`; `draw_path` a square (100, 0)–(300, 200) | `verified`, left 100, right −300, width 0 | as predicted |
| 1669 | `add_contours adc1_c`, a counterclockwise circle of radius 100 around (500, 100), 4 smooth points | `added`, `verified`, `nodes_match`, [1]; left 100, right −600, ink width 500; FontLab's values most likely lagging (right −300, `person_note`), current named as a variant (1660) | as predicted except the lag: FontLab's values current (right −600), no `person_note` |
| 1670 | `get_glyph_outline adc1_c` | `verified` if FontLab caught up: 2 contours, 16 nodes, contour 1 cubic and counterclockwise, ink box x 100–600, y 0–200 | as predicted, `verified`. Afterwards the person opened the glyph (screenshot): LSB 100, RSB −600, the circle's nodes as sent |
| 1671 | `create_glyph adc1_a`; `draw_path` the same square | `verified`, left 100, right −300 | as predicted |
| 1672 | `add_contours adc1_a`, an open arch (400, 0)–(700, 0), handles (400, 200), (700, 200) | `added`, `verified`, [1]; left 100, right −700, ink width 600; the open-contour instruction; FontLab's values current | as predicted (`open_contours_note` and the export warning in `agent_instruction`) |
| 1673 | `get_glyph_outline adc1_a` | `verified`, 2 contours, 8 nodes; contour 1 `closed` false, no direction, path without Z; ink box x 100–700, y 0–200 | as predicted. The person opened the glyph (screenshot): the arch unfilled, LSB 100, RSB −700 |
| 1674 | `create_glyph adc1_t`; `draw_path` the same square | `verified`, left 100, right −300 | as predicted |
| 1675 | `add_contours adc1_t`, two contours in one call: a clockwise counter (150, 50)–(250, 150), then a counterclockwise square (400, 0)–(500, 100) | `added`, `verified`, `contours_added` 2, [1, 2], `contour_sizes` [4, 4], `contours_now` 3; left 100, right −500, ink width 400; FontLab's values current; no open-contour note | as predicted except the lag: FontLab's values lagged (right −300, `fontlab_sidebearings_current` false, `person_note` given) |
| 1676 | `get_glyph_outline adc1_t` | before 1675: `verified`; revised after 1675 (written after the 1675 result): `unverified` while FontLab lags | `unverified`: box width 400 against FontLab's ink width 200; the nodes exact, 3 contours, 12 nodes, the counter clockwise, the square counterclockwise; the reply's top-level left, right, ink width are FontLab's lagging values (100, −300, 200) |
| — | the person opened `adc1_t` (screenshot) | FontLab shows LSB 100, RSB −500 (opening ended the lag in ED3) | as predicted |
| 1677 | `get_glyph_outline adc1_t` | `verified`, left 100, right −500, ink width 400 | as predicted |
| 1678 | `add_contours adc1_t`, `expected_contours` 1 (the glyph holds 3), a small square | refused, "holds 3 contour(s), not the expected 1 … nothing was added"; no mark; an OUTPUT refusal line; no change-log entry | refused as predicted, as a tool error (a separate `contours_found` field not visible); the text says "nothing was added" twice. The person's screenshot: OUTPUT `NOT DONE add contours adc1_t (1 contour): the glyph holds 3 contour(s), not the expected 1 …` |
| 1679 | `get_glyph_outline adc1_t` (control) | unchanged from 1677 | as predicted, node for node |
| 1680 | the person opened FontLab's Edit menu with `adc1_t` in front, nothing clicked (screenshot) | Undo greyed out (as ED3 1655, ED4 1664) | as predicted: Undo and Redo greyed out |

Afterwards (predicted before the call): `finish_changes` counted 12 (four creates, four drawings, four adds; the refusal of 1678 not counted), uncertain 0, `change_record` `complete`, no `other_changes`, `fonts_changed` `Unnamed1 Regular`; as predicted. The reminder was shown.

Reading (one run each): `add_contours` adds closed straight, closed cubic and open contours, one or two per call, after the existing ones, exactly as sent, and leaves the old contour unchanged; the stale count is refused before any change; Edit > Undo offers nothing. FontLab's own sidebearings were current right after the add in 1669 and 1672 and lagged in 1675; opening the glyph ended that lag. The hypothesis stated after 1670, that the product route's sync call prevents the lag, was contradicted by 1675 and dropped. Wording findings, no change made: `contour_sizes` lists only the new contours; `get_glyph_outline` gives FontLab's lagging values without saying they lag after an edit; the refusal says "nothing was added" twice. Not tested: several shapes (planned 1681–1684; run as AD2 1681–1685, below), a component, a Power Brush shape, an element transform, several fonts. The CL font `Unnamed1` (unsaved) now also holds `adc1_o`, `adc1_c`, `adc1_a`, `adc1_t`; nothing to keep.

### AD2: `add_contours` and two shapes (2026-11-25, listener 0.207 / server 0.89, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The last planned live check of `add_contours` (P2.2): the several-shapes refusal. No restart: `fontlab_status` read listener 0.207 and server 0.89, and the 12 changes of AD recorded by the same listener run, so the listener, FontLab and Claude Desktop had kept running since AD. A later Claude Code session. One font was open, the CL font `Unnamed1`. Prefix `adc1_`. Every prediction was stated in chat before its call or step. No stage needed a save. Nothing was saved. One run, one master.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1681 | `create_glyph adc1_s`; `draw_path` a counterclockwise square (100, 0)–(300, 200) | created, no Unicode, `layer_created`; `verified`, 4 nodes, left 100, right −300, width 0 | as predicted |
| 1682 | the person, in FontLab's GUI: Element > New > Element (Ctrl+Alt+Shift+S), then a rectangle with the Rectangle tool to the right of the square (screenshots) | a second element, not a second contour (1022a: a rectangle drawn without a new element joins the same shape) | as predicted: LAYERS & MASTERS `Regular` "2 elements"; ELEMENTS two rows, the new element listed first; transform bar X 0, Y 0, 100 %, 0°; FontLab's RSB −499 |
| 1683 | `get_glyph_outline adc1_s` | `verified`, 2 elements, 2 contours, 8 nodes, the square as drawn, the rectangle about x 336–499, y 73–148 (from the ruler); left 100, right −499, ink width about 399; element order not predicted | as predicted: 2 elements, both `ShapeContours`, identity; the rectangle (341, 73)–(499, 148); ink width 399. Element 0 is the square, element 1 the rectangle: the reverse of the ELEMENTS panel's order |
| 1684 | `add_contours adc1_s`, `expected_contours` 2 (the true count, so the shape check is the one tested), a counterclockwise square (600, 0)–(700, 100) | refused, several shapes (2), nothing added; an OUTPUT refusal line; no change-log entry | refused as predicted, as a tool error: "the glyph has 2 shapes; add_contours edits a glyph with exactly one plain shape (several shapes are not supported yet)"; the text says "nothing was added" twice, as in 1678. The OUTPUT line was not seen |
| 1685 | `get_glyph_outline adc1_s` (control, added in chat before 1684) | unchanged from 1683 | as predicted, node for node |

Afterwards (predicted before the call): `finish_changes` counted 2 (the create and the draw of `adc1_s`; the refusal and the person's GUI rectangle not counted), uncertain 0, `change_record` `complete`, no `other_changes`, `fonts_changed` `Unnamed1 Regular`; as predicted. The reminder was shown.

Reading (one run): `add_contours` refuses a glyph with two plain shapes before any change, with the true contour count passed; the glyph stays unchanged. FontLab's ELEMENTS panel lists elements in the reverse of the API's shape order. Not tested: a component, a Power Brush shape, an element transform, several fonts; the OUTPUT line of 1684. The CL font `Unnamed1` (unsaved) now also holds `adc1_s`; nothing to keep.

### WX: server 0.90's wording fixes live (2026-11-25, listener 0.207 / server 0.90, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The first live checks of server 0.90 ([CHANGELOG.md](CHANGELOG.md)): one "nothing was …" per refusal, `new_contour_sizes`, `computed_from_nodes`. No restart in this session: `fontlab_status` read server 0.90 and listener 0.207, and the 14 changes of AD and AD2 recorded by the same listener run. A new Claude Code session, so the 0.90 tool descriptions were loaded. One font was open, the CL font `Unnamed1`. Prefix `wx1_`. Every prediction was stated in chat before its call. No stage needed a save. Nothing was saved. One run, one master.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1686 | `add_contours adc1_s` (2 shapes, AD2), `expected_contours` 2, a counterclockwise square (600, 0)–(700, 100) | refused; "nothing was added" once, at the front (twice in 1684) | as predicted: "Glyph 'adc1_s': nothing was added: the glyph has 2 shapes; add_contours edits a glyph with exactly one plain shape (several shapes are not supported yet)" |
| 1687 | `get_glyph_outline adc1_s` (control) | unchanged from 1683 / 1685, 2 elements, 8 nodes | as predicted, node for node; `verified` |
| 1688 | `move_nodes adc1_s`, contour 0 node 1 from (300, 0) to (310, 0) | refused, several shapes; "nothing was moved" once, at the front | as predicted: "Glyph 'adc1_s': nothing was moved: the glyph has 2 shapes; move_nodes edits a glyph with exactly one plain shape (several shapes are not supported yet)" |
| 1689 | `create_glyph wx1_a`; `draw_path` a counterclockwise square (100, 0)–(300, 200) | created, `layer_created`; `verified`, 4 nodes, left 100, right −300 | as predicted; 17 → 18 glyphs, no Unicode; the `draw_path` reply keeps `contour_sizes` [4] |
| 1690 | `add_contours wx1_a`, `expected_contours` 1, a counterclockwise square (400, 0)–(500, 100) | added, `verified`; `new_contour_sizes` [4], no `contour_sizes`; `new_contour_indices` [1], `contours_now` 2 | as predicted; left 100, right −500, ink width 400 computed; FontLab's own values lagged (`fontlab_sidebearings` right −300, `fontlab_sidebearings_current` false, `person_note`) |
| 1691 | `get_glyph_outline wx1_a` | (narrowed after 1690 showed the lag, before this call) `unverified`, FontLab's values at the top (left 100, right −300, ink width 200); `computed_from_nodes` left 100, right −500, ink width 400; `outline_lag_note` and the lag instruction | as predicted: reason "the nodes' bounding box does not match the modern left sidebearing and ink width" (`width_ok` false, the y extent agreed); the nodes exact. Before the narrowing, the prediction left open whether the lag would appear (one run in three in AD) |
| 1692 | `add_contours wx1_a`, `expected_contours` 1 (stale: the glyph holds 2), a square (600, 0)–(700, 100) | refused, stale count; "nothing was added" once, at the front | as predicted: "Glyph 'wx1_a': nothing was added: the glyph holds 2 contour(s), not the expected 1: it may have changed since it was read; read it again with get_glyph_outline" |
| 1693 | `get_glyph_outline wx1_a` (control) | unchanged from 1691 | nodes unchanged, as predicted; **the status was not**: `verified`, left 100, right −500, ink width 400, no `computed_from_nodes` or `outline_lag_note`. FontLab's values had caught up between 1691 and 1693 (the time between them not measured; the person was not asked whether they touched FontLab) |

Afterwards (predicted before the call): `finish_changes` counted 3 (the create, the draw, the add; the refusals not counted), as predicted; uncertain 0, `change_record` `complete`, `fonts_changed` `Unnamed1 Regular`. Not predicted: `other_changes` listed the 14 changes of AD and AD2 (`local-agent-mode`, an earlier session). The reminder was shown.

Reading (one run): the refusals of `add_contours` (several shapes, a stale count) and `move_nodes` (several shapes) say "nothing was added / moved" once, at the front; the `add_contours` reply names its list `new_contour_sizes`; `get_glyph_outline` on a lagging glyph keeps FontLab's values at the top and adds `computed_from_nodes` and `outline_lag_note`, and once FontLab caught up the extras were gone. FontLab's lag after an add ended by itself this time, with no glyph opened (in AD 1675 opening the glyph ended it). Not tested live: the component tools' refusal wording; the lag case on a curved contour; the OUTPUT lines. The CL font `Unnamed1` (unsaved) now also holds `wx1_a`; nothing to keep.

### ED5: removing contours, by probe (2026-11-25, listener 0.207 / server 0.90, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Research for P2.2 (the remove-contour tool, the user's choice A of 2026-11-25) with `/debug/tryedit?stage=removecontour&contour=C` (listener 0.151, unchanged in 0.207; ED2 976 had removed one straight contour); results in [topics/geometry.md](topics/geometry.md) "Editing existing outlines". No restart: the listener, Claude Desktop and FontLab kept running from WX. One font was open, the CL font `Unnamed1`. Prefix `edp5_`. The probe calls went through a Python standard-library request (client `curl-ed5`); the glyphs were made with the product tools. Each test glyph held three contours from one `draw_path`: c0 a straight square (100, 0)–(400, 300), c1 the probe's cubic circle around (700, 300), radius 100, 4 smooth points, c2 the open arch (105, 104)–(398, 104), handles (105, 280), (398, 255); advance 0. Every prediction was stated in chat before its call or step. No stage needed a save. Nothing was saved. One run each, one master.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1694 | `fontlab_status` | listener 0.207, server 0.90, one font | as predicted, `Unnamed1 Regular`; not predicted: the server counted 3 changes (WX), the listener's record 17 for the font since its start |
| 1695 | `create_glyph edp5_a`; `draw_path` c0, c1, c2 | created, layer `Regular`; `verified`, 20 nodes, `closed` [true, true, false], nothing rounded, left 100, right −800 | as predicted; 18 → 19 glyphs, `contour_sizes` [4, 12, 4] |
| 1696 | probe: remove contour 1 (the circle) of `edp5_a` | the square, then the arch, unchanged; no mismatch, no side effect, `edited` true; glyph count 19; marked; call 1 | as predicted: node for node; synced; marked. The probe's own reading after the removal gave FontLab's sidebearings as before (100 / −800), the nodes giving 100 / −400: a lag |
| 1697 | `get_glyph_outline edp5_a` | 2 contours; the nodes give left 100, right −400; FontLab current (as ED2 977), so `verified` (low confidence) | as predicted: `verified`, 100 / −400, ink width 300, FontLab's ink box agreeing. FontLab had caught up between 1696 and 1697 with no GUI event made by the agent (as ED4 1660, WX 1693) |
| 1698 | probe: remove contour 1 (the arch) of `edp5_a` | the square alone, unchanged; margins stay 100 / −400 (the ink box does not change: a control for 1697); call 2 | as predicted |
| 1699 | probe: remove contour 0 (the last) of `edp5_a` | 0 contours, one empty shape left (`shapes` 1), no side effect, `edited` true; call 3 (low confidence on the shape) | as predicted: 0 contours and 0 nodes, `shapes` 1. Not predicted: FontLab's margins still read 100 / −400 with no ink |
| 1700 | `get_glyph_outline edp5_a` | an empty outline, 0 contours, no error | as predicted: `empty` true, "This glyph has no contours of its own."; the empty shape is not mentioned |
| 1701 | `create_glyph edp5_b`; `draw_path` c0, c1, c2 | as 1695 | as predicted; 19 → 20 glyphs |
| 1702 | probe: remove contour 0 (the square) of `edp5_b` | the circle, then the arch, unchanged; no mismatch, no side effect; glyph count 20; call 4; the nodes give left 105, right −800 | as predicted: node for node, smooth flags and `closed` false included; FontLab's own left lagged at 100 in the probe's reading |
| 1703 | the person opened FontLab's Edit menu with `edp5_b` in front (screenshot), nothing clicked | Undo greyed out (as ED3 1655, ED4 1664, AD 1680) | as predicted: Undo and Redo greyed out. Seen besides: the info box read 105 / −800 (FontLab had caught up); the ELEMENTS panel listed one element with two contours, "12/4" and "4/2"; the OUTPUT panel listed each probe call as "probe /debug/tryedit (go=yes): answered" |

Afterwards (predicted before the call): `finish_changes` counted 4 (two creates, two drawings; the probe's edits are not in the change log), as predicted; uncertain 0, `change_record` `complete`, `fonts_changed` `Unnamed1 Regular`. The reminder was shown.

Reading (one run each): `shape.shapeData.removeContour(<contour of layer.getContours()>)` removes that contour, first, middle or last, straight, cubic or open; the remaining contours keep their nodes, kinds, smooth and `closed` flags and order; the glyph count does not change, nor the shape count while a contour remains; the change syncs and marks. FontLab's own sidebearings lag right after a removal that changes the ink box (1696, 1702) and caught up by themselves before the next call or the screenshot, so ED2 977's "no lag after a remove" was one case only. Removing the last contour leaves one empty shape right after the call (1699, the probe's state read before its sync), which the sync then removes in the same request (corrected after ED7 1715, 1717); `get_glyph_outline` reports the glyph as empty (1700). Not tested: Edit > Undo beyond the menu; several shapes, components, Power Brush, an element transform; several fonts. The CL font `Unnamed1` (unsaved) now also holds `edp5_a` (empty; a square since ED6 1705) and `edp5_b` (the circle and the arch); nothing to keep.

### ED6: the empty shape after the last contour, by probe (2026-11-25, listener 0.208 / server 0.90, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Research for the design of `remove_contours` (the user's choice C: a call that removes every contour also removes the empty shape it leaves, ED5 1699) with listener 0.208's `/debug/tryedit?stage=removeshape` ([CHANGELOG.md](CHANGELOG.md)) and the read-only `/debug/trylayer?stage=state`. Before 1704 the person restarted only the listener (new code); Claude Desktop and FontLab kept running from ED5. One font was open, the CL font `Unnamed1`. Prefixes `edp5_` (ED5's glyph) and `edp6_`. The probe calls went through a Python standard-library request (client `curl-ed6`). Every prediction was stated in chat before its call. Steps 1706–1712 replaced the planned ones after 1705 failed (stated in chat before 1706), and the series stopped at 1712 when its remaining pairs could no longer separate anything (stated in chat). No stage needed a save. Nothing was saved. One run each, one master.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1704 | `fontlab_status` | listener 0.208, server 0.90, one font, `changes_by_font` `[]` | as predicted (the listener's record since 13:21:25). Seen before, on the person's screenshot after the restart: the grid drew `edp5_a` with FontLab's grey placeholder "a" |
| 1705 | `draw_path edp5_a`, a square (100, 0)–(300, 200) | refused, "not KNOWN to be empty": the empty shape of 1699 counts as one shape | **failed**: drawn, `verified`, 1 shape, 4 nodes, synced, marked. The empty shape was already gone (otherwise 2 shapes or a refusal); the theory that it stays was dropped |
| 1706 | `create_glyph edp6_a`; `draw_path` the same square | created, 20 → 21; `verified`, 4 nodes, 1 shape | as predicted |
| 1707 | probe `removecontour` 0 of `edp6_a` (13:22:32 in the OUTPUT panel) | 0 contours, `shapes` 1; call 1 | as predicted: `state_after` 1 shape, 0 nodes; synced, marked |
| 1708 | `/debug/trylayer?name=edp6_a&stage=state` (read-only) | the modern layer reads 1 shape, 0 nodes | the wrong instrument: it reports no modern shape count; its legacy view read 0 shapes, 0 contours, 0 nodes |
| 1709 | probe `removeshape` on `edp6_a` (13:22:42) | `shapes_before` 1, `shapes_after` 0, `edited`, marked; call 2 | **failed**: refused, "the glyph has 0 shapes … nothing was touched" (counted, call 2). The shape had gone between 1707 and 1709 with no edit |
| 1710 | `create_glyph edp6_b`; `draw_path` the same square | created, 21 → 22; `verified` | as predicted |
| 1711 | probe `removecontour` 0 of `edp6_b` (13:23:44.10 by the agent's clock) | 0 contours, `shapes` 1; call 3 | as predicted |
| 1712 | probe `removeshape` on `edp6_b` at once (13:23:44.28), nothing in between | `shapes_before` 1, then removed; call 4 | **failed**: `shapes_before` 0, refused, nothing touched. Ruled out: the legacy read of 1708 and "a while later"; left: the probe's sync or mark, or FontLab's event loop right after the request |

No `finish_changes` at the end of ED6; its 5 changes (the drawing into `edp5_a`, two creates, two drawings) were counted with ED7's.

Reading (one run each): the empty shape that removing the last contour leaves is gone by the next request, 0.18 s later with nothing in between (1712), also 10 s later (1709); the legacy view never shows it (1708); `draw_path` draws into such a glyph (1705). The probe stage `removeshape` never found a shape to remove. The CL font `Unnamed1` (unsaved) now also holds `edp6_a` and `edp6_b`, both empty; nothing to keep.

### ED7: the sync removes the empty shape, by probe (2026-11-25, listener 0.209 / server 0.90, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Research for the same question with listener 0.209's `state_after_sync` (read after the sync and the changed mark) and `&mark=no` (the sync without the mark) ([CHANGELOG.md](CHANGELOG.md)). Before 1713 the person restarted only the listener (new code); Claude Desktop and FontLab kept running. One font was open, the CL font `Unnamed1`. Prefix `edp7_`. Client `curl-ed6` for the probe calls. Each glyph got the square (100, 0)–(300, 200) from one `draw_path`. Every prediction was stated in chat before its call. The person did not touch FontLab during the run. No stage needed a save. Nothing was saved. One run each, one master.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1713 | `fontlab_status` | listener 0.209, server 0.90, one font, `changes_by_font` `[]` | as predicted (the listener's record since 13:27:57) |
| 1714 | `create_glyph edp7_a`; `draw_path` the square | created, 22 → 23; `verified`, 1 shape | as predicted |
| 1715 | probe `removecontour` 0 of `edp7_a`, default mark | `state_after` 1 shape; `state_after_sync` 0 (the sync or the mark removes it; the alternative, FontLab's event loop after the request, would read 1); synced, marked; call 1 | as predicted: `state_after` 1 shape, 0 nodes; `state_after_sync` 0 shapes; synced; marked |
| 1716 | `create_glyph edp7_b`; `draw_path` the square | created, 23 → 24; `verified` | as predicted |
| 1717 | probe `removecontour` 0 of `edp7_b`, `mark=no` | `state_after` 1; `state_after_sync` 0 (the sync alone); the mark skipped; call 2 | as predicted: 1, then 0 shapes; synced; `fontlab_changed_mark` "skipped by mark=no (research)" |
| 1718 | control: `create_glyph edp7_c`; `draw_path` the square and a second square (400, 0)–(500, 100) | created, 24 → 25; `verified`, 8 nodes | as predicted |
| 1719 | probe `removecontour` 0 of `edp7_c` (the first square) | `state_after` and `state_after_sync` both 1 shape, 4 nodes (the sync keeps a shape that still holds a contour); `edited`, marked; call 3 | as predicted; the second square unchanged |

Afterwards (predicted before the call): `finish_changes` counted 11 (ED6's 5 and ED7's 6: three creates, three drawings), `change_record` `incomplete` (the listener restarted at 13:27:57; the server's own count used), as predicted. The reminder was shown.

Reading (one run each): FontLab's sync, `Update(<flGlyph>)`, which every Glyphbridge write makes, removes a shape left with no contour, inside the same request (1715, 1717); it keeps a shape that still holds a contour (1719). So a write that removes the last contour leaves a glyph with no shape once synced, and `draw_path` draws into it (ED6 1705). Not tested: a glyph whose sync is not confirmed; several shapes; components; Power Brush; several fonts. The CL font `Unnamed1` (unsaved) now also holds `edp7_a`, `edp7_b` (both empty) and `edp7_c` (one square); nothing to keep.

### IL: `set_glyph_width` right after a draw, for checklist 44 (2026-11-25, listener 0.210 / server 0.91, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

One try at the state "wrapper without an active layer although the layer exists" ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §9, "Layer guard's own path"), by a different route: a width write straight after a draw, the moment named in the listener's comment on `_ensure_modern_layer`. An earlier Codex session the same day read `fontlab_status` and stopped before any write, because the tools cannot show whether a layer is inactive; the refusal text itself would show it. No restart before 1720; the listener's record ran from 13:49:40. One font was open, the CL font `Unnamed1`. Prefix `iw44`. Every prediction was stated in chat before its call. The person did not touch FontLab during the run. No stage needed a save. Nothing was saved. One run, one master.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1720 | `fontlab_status` | listener 0.210, server 0.91, one font | as predicted; `changes_by_font` `[]` |
| 1721 | `create_glyph iw44a` | created, `layer_created`, no Unicode, `font_modified` | as predicted: 25 → 26, layer `Regular` |
| 1722 | `get_glyph_width iw44a` | a whole number from the modern layer, 0 or 500 (no single number stated) | 0, `width_source` modern |
| 1723 | `draw_polygon iw44a`, (100, 0)–(300, 400) | `verified`, 1 shape, 4 nodes, no `layer_created`, width 0, left 100 | as predicted; synced |
| 1724 | `set_glyph_width iw44a 600` at once | most likely set (inconclusive); the target case a refusal naming an existing layer that is not active, width 0 | set: 0 → 600, route modern, `outline_untouched`; the state did not occur |
| 1725 | `get_glyph_width iw44a` | 600, modern, no disagreement | as predicted |

Afterwards: `finish_changes` counted 3 (a create, a drawing, a width), `change_record` `complete`; the reminder was shown.

Reading (one run): the state did not occur. The refusal needs the legacy view to call the glyph empty, and every tool write syncs at once (`synced: true` after 1723), so after a tool draw the legacy view already sees the nodes. Checklist 44 stays stub-only. Not tested: a glyph drawn in FontLab's editor, a multi-master font. The CL font `Unnamed1` (unsaved) now also holds `iw44a` (one rectangle, width 600); nothing to keep.

### SP: empty `space` in another imported font (2026-11-25, listener 0.210 / server 0.91, FontLab 8.9.5 in Demo mode, through Codex)

One read-only run in Times New Roman Regular, with two fonts open. Prediction (Codex's; that it was stated in chat before the read is not confirmed, so treat it as written after the run): `space` exists and has one `Regular` layer with zero contours and nodes. 1726: `get_glyph_outline("space")` returned `empty: true`, 0 contours and 0 nodes; FontLab's Layers & Masters panel showed one `Regular` layer (screenshot). The prediction held. 1727: the final `fontlab_status` still showed Times New Roman Regular in front, and the only recorded changes remained the pre-existing 3 in the other font (`Unnamed1 Regular`). Nothing was changed or saved. This adds one imported-font example; checklist row 16 remains open for other fonts.

### RX: `remove_contours` live (2026-11-25, listener 0.210 / server 0.91, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The first live checks of `remove_contours` (P2.2; design in [DECISIONS.md](DECISIONS.md), 2026-11-25). No restart before the run: `fontlab_status` read the new versions. One font was open, the CL font `Unnamed1`. Two rounds: RX 1728–1737 (prefix `rcx1_`) and RX2 1738–1752 (prefix `rcx2_`). Every prediction was stated in chat before its call. No stage needed a save. Nothing was saved. One run each, one master, straight squares only.

**RX 1728–1737.** The person clicked the buttons asked for, but afterwards could not tie a Yes to a test number: the agent had made call 1733 without first waiting for the person's go-ahead. The control read 1737 settled that nothing was removed beyond 1733. The person then asked for an easier procedure, and the run restarted as RX2 under it ([DECISIONS.md](DECISIONS.md), 2026-11-25, questions in FontLab during live tests).

| # | Step | Predicted | Result |
|---|---|---|---|
| 1728 | `fontlab_status` | 0.210 / 0.91, no `compatibility_note`; two fonts open, Times New Roman in front; `Unnamed1` 3 changes | versions as predicted; only one font open, `Unnamed1`, in front (Times New Roman had been closed); 3 changes |
| 1729 | `create_glyph rcx1_a`; `draw_path` three counterclockwise squares (0, 0)–(100, 100), (200, 0)–(300, 100), (400, 0)–(500, 100) | `layer_created`; `verified`, 12 nodes, left 0, right −500, ink width 500 | as predicted |
| 1730 | `get_glyph_outline rcx1_a` | `verified`, 3 contours of 4 nodes, starts (0, 0), (200, 0), (400, 0) | as predicted |
| 1731 | `remove_contours rcx1_a`, `expected_contours` 3, contour 1 (4 nodes, start (200, 0)); the person clicks No | the question names the client, the font, the glyph and contour 1, says Undo cannot bring it back, does not say the glyph will be empty; error "not approved … Nothing was changed" | as predicted. The person's screenshot: "local-agent-mode (via Glyphbridge) is requesting to remove 1 of the 3 contours of the glyph 'rcx1_a' in the font "Unnamed1 Regular" (not saved to a file yet): contour 1: 4 nodes, starting at (200, 0)"; No is the default and counts down |
| 1732 | `get_glyph_outline rcx1_a` (control) | unchanged | as predicted, node for node |
| 1733 | the same call; the person clicks Yes | `removed`, `verified`, `nodes_match`, `contours_now` 2, `glyph_empty` false, `removed_contours` the square from (200, 0); left 0, right −500, ink width 500; FontLab's values current; `undo_note` | as predicted; not predicted: `contours_removed` is the list `[1]`, and the removed contour shows `"index": 0` in `removed_contours` (wording finding) |
| 1734 | `get_glyph_outline rcx1_a` | `verified`, 2 contours, starts (0, 0) and (400, 0) | as predicted |
| 1735 | `remove_contours rcx1_a`, `expected_contours` 3 (it holds 2) | refused before any question | as predicted: "the glyph holds 2 contour(s), not the expected 3 … read it again with get_glyph_outline" |
| 1736 | `expected_contours` 2, contour 1 with start (200, 0) (it starts at (400, 0)) | refused before any question | as predicted: "entry 0: contour 1 starts at (400, 0), not at the given start (200, 0)"; no hint to read again (wording finding) |
| 1737 | `get_glyph_outline rcx1_a` (control, after the person's report of a Yes) | unchanged from 1734 | as predicted |

**RX2 1738–1752**, under the new procedure: each glyph is named after the button to click. The person typed one "go" before the first question and afterwards confirmed that every question and button was as planned (`rcx2_no` No; no question for `rcx2_nodlg`; `rcx2_yes` Yes; `rcx2_yesall` Yes).

| # | Step | Predicted | Result |
|---|---|---|---|
| 1738 | `fontlab_status` | 0.210 / 0.91, one font, `Unnamed1` 6 changes | as predicted |
| 1739–1742 | create and draw `rcx2_no`, `rcx2_yes` (the three squares of 1729), `rcx2_nodlg`, `rcx2_yesall` (the squares from (0, 0) and (400, 0)) | `layer_created` each; `verified`, 12 / 12 / 8 / 8 nodes, left 0, right −500 | as predicted; no question appeared |
| 1743 | `remove_contours rcx2_no`, contour 1; No | error "not approved … Nothing was changed" | as predicted |
| 1744 | `get_glyph_outline rcx2_no` | unchanged, 3 contours | as predicted |
| 1745 | `rcx2_nodlg`, `expected_contours` 3 | refused, no question | as predicted |
| 1746 | `rcx2_nodlg`, contour 1 with start (200, 0) | refused, no question | as predicted |
| 1747 | `get_glyph_outline rcx2_nodlg` | unchanged, 2 contours | as predicted |
| 1748 | `remove_contours rcx2_yes`, contour 1; Yes | as 1733 | as predicted |
| 1749 | `get_glyph_outline rcx2_yes` | `verified`, 2 contours, starts (0, 0) and (400, 0) | as predicted |
| 1750 | `remove_contours rcx2_yesall`, contours 0 and 1; Yes | `removed`, `verified`, `contours_now` 0, `glyph_empty` true, `empty_note`, both squares returned, width 0 | as predicted; the reply does not state the width; its `note` still speaks of "remaining contours" (wording finding) |
| 1751 | `get_glyph_outline rcx2_yesall` | `empty: true`, 0 contours | as predicted |
| 1752 | `draw_path rcx2_yesall`, one square (0, 0)–(100, 100) | accepted as an empty glyph: `verified`, 4 nodes, right −100 | as predicted |

Afterwards (predicted before the call): `finish_changes` counted 14 (since IL: five creates, six drawings, three removals; the No answers and refusals not counted), uncertain 0, `change_record` `complete`, `fonts_changed` `Unnamed1 Regular`; as predicted. The reminder was shown.

Reading (one run each): `remove_contours` removes a middle contour or every contour after a Yes, leaves the other contours unchanged and in order, and leaves a glyph that `draw_path` takes as empty; a No and two stale requests change nothing, and the stale requests are refused before any question. Wording findings, no change made: `removed_contours` renumbers the removed contours from 0 instead of giving their original index; after every contour is removed, the `note` still speaks of remaining contours; the wrong-start refusal lacks the "read it again" hint of the wrong-count refusal. Not tested: no answer (the 45 s close), Edit > Undo in FontLab's menu, curves, open contours, the several-shapes, component, transform and Power Brush refusals, an edit while the question is open. The CL font `Unnamed1` (unsaved) now also holds `rcx1_a` (2 squares), `rcx2_no` (3), `rcx2_yes` (2), `rcx2_nodlg` (2), `rcx2_yesall` (1); nothing to keep.

### RX3: listener 0.211 / server 0.92 live (2026-11-25, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The checks of RX's wording findings and the shorter questions ([CHANGELOG.md](CHANGELOG.md)). Before the run the listener was restarted in FontLab; FontLab and its one font, the CL font `Unnamed1`, were left open, and so were Claude Desktop and Claude Code (a new session, so its server was 0.92). The glyph-name procedure ([DECISIONS.md](DECISIONS.md), 2026-11-25), prefix `rcx3_`: the plan and every prediction were stated in chat, then the person typed one "go". No stage needed a save. Nothing was saved. One run, one master, straight squares only.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1753 | `fontlab_status` | 0.211 / 0.92; one font, `Unnamed1`; `changes_by_font` `[]` (a new listener run) | as predicted |
| 1754–1757 | `create_glyph rcx3_no`, `rcx3_yes`, `rcx3_yesall`, `rcx3_nodlg` | `layer_created` each | as predicted |
| 1758–1761 | `draw_polygon`: counterclockwise squares (100, 100)–(200, 200) and (300, 100)–(400, 200), and for `rcx3_yes` also (500, 100)–(600, 200) | `verified`, 8 / 12 / 8 / 8 nodes | as predicted |
| 1762–1765 | `get_glyph_outline` of the four | `verified`, starts (100, 100), (300, 100), (500, 100) | as predicted |
| 1766 | `remove_contours rcx3_no`, contour 0; No | the question's last line "If you don't answer, nothing will be removed."; error "not approved … Nothing was changed" | as predicted; the last line confirmed by the person |
| 1767 | `remove_contours rcx3_yes`, `expected_contours` 3, contour 1 (start (300, 100)); Yes | `removed_contours` shows `"index": 1`; 2 contours left, `verified`, `nodes_match` | as predicted; FontLab's sidebearings current |
| 1768 | `remove_contours rcx3_yesall`, contours 0 and 1; Yes | `glyph_empty` true; indexes 0 and 1; `note` exactly "The contours were removed after the person's Yes in FontLab. The advance width is unchanged." | as predicted |
| 1769 | `remove_contours rcx3_nodlg`, contour 0 with start (150, 150) (it starts at (100, 100)) | refused, no question; the message ends once with "Read the glyph again with get_glyph_outline." | as predicted: "… entry 0: contour 0 starts at (100, 100), not at the given start (150, 150). Read the glyph again with get_glyph_outline."; the person saw no question |
| 1770 | `get_glyph_outline rcx3_nodlg` (control) | unchanged, 2 contours | as predicted |
| 1771 | `get_glyph_outline rcx3_no` (control) | unchanged, 2 contours | as predicted |
| 1772 | `finish_changes` | 10 changes (4 creates, 4 drawings, 2 removals), `change_record` `complete` | as predicted: 10, uncertain 0, `complete`, `fonts_changed` `Unnamed1 Regular`; the reminder was shown |

Reading (one run): RX's three wording findings are fixed in FontLab, and the questions end with the new shorter line. Not run live: the hint in `move_nodes`, a question whose countdown cannot be set up (`countdown_error`), no answer. The CL font `Unnamed1` (unsaved) now also holds `rcx3_no` (2 squares), `rcx3_yes` (2), `rcx3_yesall` (empty), `rcx3_nodlg` (2); nothing to keep.

### RX4: `remove_contours` on curves, open contours, a component and no answer (2026-11-25, listener 0.211 / server 0.92, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Cases left open by RX ([CHECKLIST.md](CHECKLIST.md) row 31), the user's choice. No restart since RX3. One font open, the CL font `Unnamed1`. The glyph-name procedure ([DECISIONS.md](DECISIONS.md), 2026-11-25), prefix `rcx4_`, with the suffix `_noanswer` (the person clicks nothing), added for this run. The plan and every prediction were stated in chat, then the person typed one "go". No stage needed a save. Nothing was saved. One run each, one master.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1773 | `fontlab_status` | 0.211 / 0.92; `Unnamed1` 10 changes (RX3) | as predicted |
| 1774–1778 | `create_glyph rcx4_c_yes`, `rcx4_o_yes`, `rcx4_src`, `rcx4_k_nodlg`, `rcx4_w_noanswer` | `layer_created` each | as predicted |
| 1779–1783 | `draw_path rcx4_c_yes`: a square (0, 0)–(100, 100) and a counterclockwise circle, radius 100 around (300, 100), four smooth points; `draw_path rcx4_o_yes`: the square and an open arch (200, 0) to (400, 0), control points (200, 150), (400, 150); `draw_polygon rcx4_src` a 50 square, `rcx4_k_nodlg` the 100 square, `rcx4_w_noanswer` squares from (0, 0) and (300, 0) | `verified` each | as predicted: 16, 8, 4, 4, 8 nodes |
| 1784 | `add_component rcx4_k_nodlg`, `rcx4_src` at (200, 0) | `placement` `"temporary layer"`, `verified`, `existing_kept` | as predicted |
| 1785–1788 | `get_glyph_outline` of the four targets | `verified`; the circle 12 nodes, the arch 4 nodes from (200, 0) | as predicted; the circle starts at its on-curve point (400, 100); `rcx4_k_nodlg` reads 2 contours, the component's element `is_component`, `source_in_step` true |
| 1789 | `remove_contours rcx4_c_yes`, contour 1 (12 nodes, start (400, 100)); Yes | `verified`, `nodes_match`, 1 contour left; `removed_contours` index 1, 12 nodes, 8 `Curve`, the 4 on-curve points smooth; right −100, ink width 100; FontLab's sidebearings may lag | as predicted; FontLab's sidebearings current |
| 1790 | `remove_contours rcx4_o_yes`, contour 1 (4 nodes, start (200, 0)); Yes | `verified`; `removed_contours` index 1, `"closed": false`, 4 nodes; right −100 | as predicted |
| 1791 | `remove_contours rcx4_k_nodlg`, `expected_contours` 2, contour 0 | refused before any question, naming the component | refused before any question, but as "the glyph has 2 shapes; remove_contours edits a glyph with exactly one plain shape (several shapes are not supported yet)"; the component is not named (prediction failed) |
| 1792 | `remove_contours rcx4_w_noanswer`, contour 1; no click | countdown; closes at about 45 s; `not_answered_in_time`, nothing changed, within the Code tab's 60 s | as predicted |
| 1793–1794 | `get_glyph_outline rcx4_w_noanswer`, `rcx4_k_nodlg` (controls) | unchanged | as predicted |
| 1795 | `finish_changes` | 13 (5 creates, 5 drawings, 1 placement, 2 removals), `complete` | as predicted; the reminder was shown |

The person's screenshots of the three questions: each names the client, the font, the glyph and "contour 1: 12 nodes, starting at (400, 100)" (`rcx4_c_yes`), "4 nodes, starting at (200, 0)" (`rcx4_o_yes`) and "(300, 0)" (`rcx4_w_noanswer`), ends with "If you don't answer, nothing will be removed.", and counts down on No ("No (44)"). The person confirmed both Yes clicks, no question for `rcx4_k_nodlg`, and no click for `rcx4_w_noanswer`.

Reading (one run each): `remove_contours` removes a cubic contour and an open contour after a Yes, `verified`, returning their nodes, kinds, smooth flags and `closed`; an unanswered question closes by itself at 45 s and changes nothing. A component placed beside a plain shape is a shape of its own in `layer.shapes`, so the shared check (`_edit_case_of`, read in the listener code after the run) refuses the glyph as several shapes before its component case is reached; the refusal is true but does not name the component, and `move_nodes` and `add_contours` share the check (not run live here). Not tested: two plain shapes, an element transform, a Power Brush shape, an edit while the question is open, Edit > Undo in the menu. The CL font `Unnamed1` (unsaved) now also holds `rcx4_c_yes` (the square), `rcx4_o_yes` (the square), `rcx4_src`, `rcx4_k_nodlg` (a square and a component), `rcx4_w_noanswer` (2 squares); nothing to keep.

### RX5: the several-shapes refusal names the component (2026-11-25, listener 0.212 / server 0.93, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The live check of 0.212 / 0.93, built from RX4 1791 ([CHANGELOG.md](CHANGELOG.md)). The listener was restarted in FontLab's Scripting panel before the run; FontLab and the CL font `Unnamed1` were left running; a new Claude Code session, so the 0.93 tool descriptions were loaded. One font open. The glyph-name procedure ([DECISIONS.md](DECISIONS.md), 2026-11-25), prefix `rcx5_`. The plan and every prediction were stated in chat, then the person typed one "go". No stage needed a save. Nothing was saved. One run, one master.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1796–1797 | `create_glyph rcx5_src`, `rcx5_k_nodlg` | `layer_created` each | as predicted: `Regular`, glyphs 40 → 42 |
| 1798–1799 | `draw_polygon rcx5_src` a 50 square, `rcx5_k_nodlg` a 100 square, both from (0, 0) | `verified`, 4 nodes each | as predicted |
| 1800 | `add_component rcx5_k_nodlg`, `rcx5_src` at (200, 0) | `placement` `"temporary layer"`, `verified`, `existing_kept` | as predicted |
| 1801 | `get_glyph_outline rcx5_k_nodlg` | `verified`, 2 contours; the component's element `is_component`, `source_in_step` true | as predicted; contour 0: 4 nodes from (0, 0) |
| 1802 | `remove_contours`, `expected_contours` 2, contour 0 (4 nodes, start (0, 0)) | refused before any question: "the glyph has 2 shapes, 1 of them a component; …" | as predicted: "nothing was removed: the glyph has 2 shapes, 1 of them a component; remove_contours edits a glyph with exactly one plain shape (several shapes are not supported yet)" |
| 1803 | `add_contours`, `expected_contours` 2, a 20 square at (400, 0) | the same text | as predicted: "nothing was added: …" |
| 1804 | `move_nodes`, contour 0, node 0, (0, 0) → (10, 0) | the same text | as predicted: "nothing was moved: …" |
| 1805 | `get_glyph_outline rcx5_k_nodlg` (control) | unchanged from 1801 | as predicted, node for node |
| 1806 | `finish_changes` | 5 (2 creates, 2 drawings, 1 placement), nothing from elsewhere | as predicted: 5, uncertain 0, `complete`; the reminder was shown |

The person confirmed that no question appeared. FontLab's OUTPUT lines for 1802–1804 were not checked during the run; a screenshot taken later in ED8 shows the `move_nodes` line, "NOT DONE move rcx5_k_nodlg: the glyph has 2 shapes, 1 of them a component; …"; the other two lines had scrolled out of view.

Reading (one run): the several-shapes refusal of all three edit tools names one component beside a plain shape, before any question or change. Stub-only: several components ("2 of them components"), an unreadable component count; the listener's `component_shapes` is not shown by the server. The CL font `Unnamed1` (unsaved) now also holds `rcx5_src` (a 50 square) and `rcx5_k_nodlg` (a square and a component); nothing to keep.

### ED8: editing one shape among several, by probe (2026-11-25, listener 0.213 / server 0.93, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Research for P2.2, several shapes per glyph (the user's choice of 2026-11-25 after RX5). 1807 ran on listener 0.212; then listener 0.213 was built as approved ([CHANGELOG.md](CHANGELOG.md)) and the listener alone was restarted in FontLab's Scripting panel; FontLab, the CL font `Unnamed1` and Claude Desktop were left running (the server was unchanged). One font open. The glyph-name procedure ([DECISIONS.md](DECISIONS.md), 2026-11-25): every glyph `_nodlg` (no question may appear), prefix `edp8_` (the probe accepts only `edp` names). The probe was called directly on the listener (`GET /debug/tryedit … &go=yes`) after the person's "Proceed"; the predictions were stated in chat before each call. No stage needed a save. Nothing was saved. One run each, one master, straight contours.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1807 | `/debug/classdir`, `flShape` and `flShapeData`, names only (listener 0.212) | `flShape` lists `contoursCount`, `shapeData`, `addContour`, `removeContour`, `isComponent`, `isComposite`, `transform`; whether it has its own contour list was open | `flShape`: `contours` ("list(flContour)"), `getContours()` ("list(flContour) getContours()"), `contoursCount` (int), `getNodeAt`, `hasComponents`, and the predicted members; `flShapeData`: `contours()`, `componentGlyph`, `componentLayer`, `referenceCount`. Nothing called |
| (before 1808, unnumbered) | `fontlab_status` | 0.213 / 0.93; `Unnamed1`; `changes_by_font` [] | as predicted; the server's own session count read 5 (RX5, not predicted) |
| 1808–1810 | `create_glyph edp8_src_nodlg`, `edp8_a_nodlg`, `edp8_c_nodlg` | `layer_created` each; glyphs 42 → 45 | as predicted |
| 1811–1812 | `draw_polygon edp8_src_nodlg` a 50 square; `edp8_a_nodlg` a 100 square and a triangle (120, 0) (180, 0) (150, 60), one shape | `verified`; 4 nodes; 1 shape, 2 contours, 7 nodes | as predicted |
| 1813 | `add_component edp8_a_nodlg`, `edp8_src_nodlg` at (300, 0) | `temporary layer`, `verified`, `existing_kept` | as predicted |
| 1814 | `add_component edp8_c_nodlg`, `edp8_src_nodlg` at (0, 0) (the control) | `empty layer`, `verified` | as predicted |
| 1815 | `stage=movenode&shape=0&contour=0&node=2&dx=10&dy=-20` on `edp8_a_nodlg` | (100, 100) → (110, 80); `edited`, no side effect; others and source unchanged; counts [2, 1]; offset 0; the component's contour reads raw (0, 0)–(50, 50) in the layer list; call 1 | as predicted; synced, marked |
| 1816 | `stage=addcontour&shape=0` (the square (600, 600)–(650, 650)) | the square as layer contour 2, last within shape 0, before the component's contour; counts [2, 1] → [3, 1]; call 2 | as predicted |
| 1817 | `stage=removecontour&shape=0&contour=1` (the triangle) | counts [3, 1] → [2, 1]; `edited`; call 3 | as predicted |
| 1818–1820 | `get_glyph_outline edp8_src_nodlg`, `edp8_c_nodlg`, `edp8_a_nodlg` | unchanged, unchanged; `edp8_a_nodlg` `verified` (or `unverified` only through lagging sidebearings), `source_in_step` true | as predicted, all `verified`; FontLab's sidebearings current |
| 1821 | `finish_changes` | 7 changes, `change_record` `complete` | 7 changes; **`change_record` `incomplete` (prediction failed)**: the listener restart for 0.213 started a new record while the server still held RX5's changes; the prediction overlooked the restart |
| 1822–1823 | `create_glyph edp8_b_nodlg`; `add_component edp8_b_nodlg`, `edp8_src_nodlg` at (300, 0) | `layer_created`, glyphs 45 → 46; `empty layer`, `verified` | as predicted |
| (GUI) | the person: Element > New > Element in `edp8_b_nodlg`, then one rectangle with the Rectangle tool | — | the ELEMENTS panel listed the new element above the component |
| 1824 | `get_glyph_outline edp8_b_nodlg` | 2 elements: the component first, the rectangle second, identity (as AD2 1683) | as predicted: the rectangle (116, 230)–(289, 363); `verified` |
| 1825 | `stage=movenode&shape=1&contour=0&node=2&dx=10&dy=-20` | (289, 363) → (299, 343); offset 1; counts [1, 1]; call 4 | as predicted |
| 1826 | `stage=addcontour&shape=1` | the square as layer contour 2, after the rectangle; counts [1, 2]; call 5 | as predicted |
| 1827 | `stage=removecontour&shape=1&contour=0` (the rectangle) | counts [1, 1]; the component's contour, then the square; call 6 | as predicted |
| 1828–1831 | `get_glyph_outline` of `edp8_src_nodlg`, `edp8_c_nodlg`, `edp8_a_nodlg`, `edp8_b_nodlg` | the first three unchanged; `edp8_b_nodlg` the component at (300, 0) and the square, `verified`, `source_in_step` true | as predicted |
| 1832 | `finish_changes` | 2 changes, `complete` | as predicted |

Every probe edit read `edited` true, `side_effect_detected` false, `other_shapes_unchanged` and `sources_unchanged` true, the glyph count unchanged, synced (`synced`) and marked; `state_after_sync` kept 2 shapes and 1 component. The person's screenshot after case A: the grid thumbnail of `edp8_a_nodlg` showed the two baseline outlines and the square at the upper right (the moved corner is too small to see there); the ELEMENTS panel showed the component at Δ=(300,0) and a plain element of 2 contours; the status bar showed the right sidebearing −650, as read; the OUTPUT panel listed the three probe calls as answered.

Reading (one run each, straight contours, one master): `layer.getContours()` lists each shape's contours in shape order, whether the component or the plain shape comes first, and a component's contour there is its source's own, without its offset; `shapes[I].getContours()` gives exactly shape I's slice. Moving a node, adding a contour (it lands last within shape I) and removing a contour in a plain shape beside a component left the component's offset, its source and another glyph using that source unchanged. Not tested: curves, two plain shapes (stub only), a component with a transform other than an offset, Power Brush (refused by design). The CL font `Unnamed1` (unsaved) now also holds `edp8_src_nodlg` (a 50 square), `edp8_a_nodlg` (a four-sided outline and a square in shape 0, a component), `edp8_c_nodlg` (a component), `edp8_b_nodlg` (a component, then a square); nothing to keep.

### ED9: editing either of two plain shapes, by probe (2026-11-25, listener 0.213 / server 0.93, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Research for design question 2 of several shapes (the user's choice "research first"). Same listener run as ED8 (probe calls 7 and 8 of 8); FontLab and the CL font `Unnamed1` left running. One font open. Prefix `edp9_`, `_nodlg`. The predictions were stated in chat before each call. No stage needed a save. Nothing was saved. One run each, one master, straight contours.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1833 | `create_glyph edp9_t_nodlg` | `layer_created`; glyphs 46 → 47 | as predicted |
| 1834 | `draw_polygon edp9_t_nodlg`, a 100 square | `verified`, 1 shape, 4 nodes | as predicted |
| (GUI) | the person: Element > New > Element, then one rectangle | — | drawn above the square; LAYERS & MASTERS read "2 elements"; the ELEMENTS panel listed the new element first |
| 1835 | `get_glyph_outline edp9_t_nodlg` | 2 plain elements, identity; the square first, the rectangle second (as AD2 1683) | as predicted: the rectangle (28, 214)–(331, 411); `verified` |
| 1836 | probe `stage=addcontour&shape=1` | offset 1; the square (600, 600)–(650, 650) as contour 2; counts [1, 1] → [1, 2]; `edited`; call 7 | as predicted; synced, marked |
| 1837 | probe `stage=movenode&shape=0&contour=0&node=2&dx=10&dy=-20` | (100, 100) → (110, 80); offset 0; counts [1, 2]; call 8 | as predicted |
| 1838 | `get_glyph_outline edp9_t_nodlg` | `verified`, the three contours | as predicted; element 1 now holds 2 contours |
| 1839 | `finish_changes` | 2 changes, `complete` | as predicted |

Reading (one run each): in a glyph of two plain shapes, either shape's contours are found and edited through its own list, and the other shape is left unchanged. The CL font `Unnamed1` (unsaved) now also holds `edp9_t_nodlg` (two plain shapes, 3 contours); nothing to keep.

### ED10: a new plain shape beside existing shapes, by probe (2026-11-26, listener 0.214 / server 0.93, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Research for design question 5 (`add_contours` on a glyph of components only; the user's choice "research first"). Listener 0.214 built as approved ([CHANGELOG.md](CHANGELOG.md)); the listener alone was restarted; FontLab, `Unnamed1` and Claude Desktop were left running. One font open. Prefix `edp10_`, `_nodlg`. The predictions were stated in chat before each call. No stage needed a save. Nothing was saved. One run each, one master, straight contours.

| # | Step | Predicted | Result |
|---|---|---|---|
| (before 1840, unnumbered) | `fontlab_status` | 0.214 / 0.93; `changes_by_font` [] | as predicted; the server's own session count read 16 (not predicted) |
| 1840–1843 | `create_glyph edp10_src_nodlg`, `edp10_k_nodlg`, `edp10_c_nodlg`, `edp10_p_nodlg` | `layer_created` each; glyphs 47 → 51 | as predicted |
| 1844–1845 | `draw_polygon` a 50 square in `edp10_src_nodlg`, a 100 square in `edp10_p_nodlg` | `verified`, 4 nodes each | as predicted |
| 1846–1848 | `add_component` of `edp10_src_nodlg`: `edp10_k_nodlg` at (300, 0), `edp10_c_nodlg` at (0, 0) (the control), `edp10_p_nodlg` at (300, 0) | `empty layer`, `empty layer`, `temporary layer` with `existing_kept`; `verified` each | as predicted |
| 1849 | probe `stage=addshape` on `edp10_k_nodlg` (a component only) | shapes 1 → 2, the new shape last, plain, identity, the square (`new_shape_ok`); counts [1] → [1, 1]; the component, its source and the glyph count unchanged; call 1 | as predicted; synced, marked |
| 1850 | probe `stage=addshape` on `edp10_p_nodlg` (a square, then a component) | shapes 2 → 3, the new shape last; counts [1, 1] → [1, 1, 1]; call 2 | as predicted |
| 1851–1853 | `get_glyph_outline` of `edp10_src_nodlg`, `edp10_c_nodlg`, `edp10_k_nodlg` | unchanged, unchanged, the component and the square `verified` | as predicted |
| 1854 | `get_glyph_outline edp10_p_nodlg` | `verified` | **`unverified` (prediction failed)**: the outline as predicted and FontLab's ink box top 650, but FontLab's sidebearings still gave ink width 350 (their value before the add); no `outline_lag_note`, since the glyph holds a component at an offset |
| 1855 | `finish_changes` | 9 changes; `incomplete` (the listener was restarted) | as predicted |
| (GUI) | the person opened `edp10_p_nodlg` in a Glyph window, no edit | — | — |
| 1856 | `get_glyph_outline edp10_p_nodlg` (the control for 1854) | `verified`, ink width 650, right −650 | as predicted: FontLab's sidebearings had caught up, so 1854 was their lag, not a different ink width |

Reading (one run each): `flShape()`, its `shapeData.addContour`, then one `layer.addShape` adds a plain shape after the existing ones, beside a component alone and after a plain shape and a component; the component, its offset, its source and another glyph using that source stay unchanged. FontLab's sidebearings may lag after it until a GUI event, as after the other API edits; `get_glyph_outline` explained such a lag only for glyphs without element transforms (fixed in server 0.94, [CHANGELOG.md](CHANGELOG.md)). The CL font `Unnamed1` (unsaved) now also holds `edp10_src_nodlg` (a 50 square), `edp10_k_nodlg` (a component and a square), `edp10_c_nodlg` (a component), `edp10_p_nodlg` (a square, a component, a square); nothing to keep.

### MS: several shapes in the three edit tools live (2026-11-26, listener 0.215 / server 0.94, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The live checks of the build ([CHANGELOG.md](CHANGELOG.md), design [DECISIONS.md](DECISIONS.md) 2026-11-25 and 2026-11-26). The listener alone was restarted for 0.215 and a new Claude Code session started (the 0.94 descriptions loaded); FontLab and the CL font `Unnamed1` were left running. One font open. Prefix `ms1_`. The predictions were stated in chat before each call. No stage needed a save. Nothing was saved. One run each, one master, straight contours; components moved by an offset unless said.

| # | Step | Predicted | Result |
|---|---|---|---|
| (before 1857, unnumbered) | `fontlab_status` | 0.215 / 0.94 | as predicted; `changes_by_font` [] |
| 1857–1861 | `create_glyph ms1_src`, `ms1_a`, `ms1_b`, `ms1_k`, `ms1_c` | `layer_created` each; glyphs 51 → 56 | as predicted |
| 1862–1863 | `draw_polygon` a 50 square in `ms1_src`, a 100 square (0,0),(100,0),(100,100),(0,100) in `ms1_a` | `verified`, 4 nodes each | as predicted |
| 1864–1867 | `add_component` of `ms1_src`: `ms1_a` at (300, 0), `ms1_b` at (300, 0), `ms1_k` at (300, 0), `ms1_c` at (0, 0) (the control) | `temporary layer` with `existing_kept`, then `empty layer` three times; `verified` each | as predicted |
| 1868 | `get_glyph_outline ms1_a` | 2 elements, the square first, the component second; contour 1 (300,0)–(350,50); `verified`, `source_in_step` true | as predicted |
| 1869 | `move_nodes ms1_a`, contour 0 node 2 (100, 100) → (110, 80) | `moved`, `verified`; `edit_case` `several_shapes`; `other_shapes_unchanged`, `sources_unchanged` true | as predicted; FontLab's sidebearings current |
| 1870 | `move_nodes ms1_a`, contour 1 node 0 (the component's contour) | refused, nothing moved, the component of `ms1_src` named; "edit the source" | refused as predicted, naming `ms1_src` (shape 1); **wording finding**: the refusal opens "the request does not match the glyph as it is now" and ends "Read the glyph again", which cannot help here, and gives no "edit the source glyph instead" |
| 1871 | `add_contours ms1_a`, expected 2, the square (600,600)–(650,650), no `shape` | `added`, `verified`; `new_contour_indices` [1], the component's contour moves to 2; `shape` 0 | as predicted, **except no `shape` field in the reply (prediction failed)**: the field comes only when `shape` was passed (1885); FontLab's sidebearings lagged, `person_note` given |
| 1872 | `add_contours ms1_k` (a component only), expected 1, the same square | ONE new plain shape after the component; `new_contour_indices` [1]; `edit_case` `component`; `sources_unchanged` true | as predicted |
| 1873 | `get_glyph_outline ms1_k` | 2 elements, the component then a plain identity shape; `unverified` with `outline_lag_note` and `computed_from_nodes` (server 0.94) | as predicted: FontLab's ink width 50, `computed_from_nodes` 300 / −650 / 350; the top 650 agreed |
| 1874 | `add_contours ms1_b` (a component only), expected 1, a 100 square at (0, 0) | as 1872 | as predicted |
| 1875 | `move_nodes ms1_b`, contour 1 node 2 (100, 100) → (110, 80), a plain shape after a component | `moved`, `verified`, `several_shapes` | as predicted |
| 1876 | `remove_contours ms1_a`, expected 3, contour 2 (the component's contour) | refused before any question, nothing changed | as predicted; wording right ("the request names a contour of a component") |
| 1877 | `remove_contours ms1_k`, expected 2, contour 1 (the only contour of the plain shape) | after Yes: `removed`, `verified`; `shapes_emptied` [1]; the component kept, glyph not empty | call 1: `not_answered_in_time`, nothing changed (the person was not told in time that FontLab was asking); call 2, after the person's go-ahead and Yes: as predicted |
| 1878–1880 | `get_glyph_outline ms1_k`, `ms1_src`, `ms1_c` | the component alone; the source and the control unchanged; `verified` each | as predicted |
| 1881–1882 | `create_glyph ms1_t`; `draw_polygon` a 100 square | glyphs 56 → 57; `verified` | as predicted |
| (GUI) | the person: Element > New > Element in `ms1_t`, then one rectangle with the Rectangle tool | — | LAYERS & MASTERS "2 elements"; the ELEMENTS panel listed the new element first |
| 1883 | `get_glyph_outline ms1_t` | 2 plain identity elements, the square first | as predicted: the rectangle (70, 202)–(324, 404); `verified` |
| 1884 | `add_contours ms1_t`, expected 2, the square (600,600)–(650,650), no `shape` | refused, `shape` required, nothing changed | as predicted ("the glyph has 2 plain shapes (shapes 0, 1 …); name the one to add to with shape") |
| 1885 | the same with `shape` 1 | `added`, `verified`; `new_contour_indices` [2]; shape 0 unchanged | as predicted; the reply carries `shape` 1 |
| 1886 | `move_nodes ms1_t`, contour 0 node 2 (100, 100) → (110, 80) and contour 1 node 2 (324, 404) → (330, 410) in one call | `moved`, `verified` | as predicted |
| 1887 | `remove_contours ms1_t`, expected 3, contours 0 (all of shape 0) and 2 (in shape 1) | after Yes: `removed`, `verified`; `shapes_emptied` [0]; the rectangle left as contour 0 | as predicted; FontLab's sidebearings lagged |
| 1888–1890 | `create_glyph ms1_s`; `draw_polygon` a 100 square; `add_component` `ms1_src` at (300, 0) | glyphs 57 → 58; `verified`; `temporary layer`, `existing_kept` | as predicted |
| (GUI) | the person: in `ms1_s`, the component's horizontal scale set to 200% in the Transform bar | — | the bar read X 300, Y 0, 200 % / 100 % |
| 1891 | `get_glyph_outline ms1_s` | element 1 `m11` 2, offset (300, 0); contour 1 (300,0)–(400,50); `source_in_step` "unknown"; `verified` | as predicted |
| 1892–1894 | `move_nodes`, `add_contours`, `remove_contours` on `ms1_s` (contour 0, the plain square) | each refused, nothing changed, shape 1 named; `remove_contours` before any question | as predicted ("the glyph holds a component that is scaled, rotated or mirrored (shape 1: m11 2 …)"); `remove_contours` answered at once, no question seen |
| 1895 | `finish_changes` | 25 changes, `complete` | as predicted |

Reading (one run each): the three edit tools edit plain shapes beside components moved by an offset, before or after them, and either of two plain shapes, in one call across shapes too; `add_contours` adds last within the named or only plain shape, and on a glyph of components only makes one new plain shape; `remove_contours` may empty one plain shape, which FontLab then removes. A component's contour and a scaled component are refused with nothing changed. Every edit left the other shapes, the component offsets, the source `ms1_src` and the control `ms1_c` unchanged. Not tested: curves, open contours, a rotated or mirrored component, a scaled component in a glyph of components only, a Power Brush shape beside, a plain shape with an element transform, Edit > Undo, several fonts, other masters. The CL font `Unnamed1` (unsaved) now also holds `ms1_src` (a 50 square), `ms1_a` (a four-sided outline and a square in shape 0, a component), `ms1_b` (a component, then a four-sided outline), `ms1_k` (a component), `ms1_c` (a component), `ms1_t` (the moved rectangle), `ms1_s` (a square, a component scaled 200%); nothing to keep.

### MS2: the two findings of MS live (2026-11-26, listener 0.216 / server 0.95, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The live checks of the fix of MS 1870 and 1871 ([CHANGELOG.md](CHANGELOG.md)). `fontlab_status` read listener 0.216 and server 0.95, its change log empty since the listener's restart; a new Claude Code session held the 0.95 descriptions. FontLab and the CL font `Unnamed1` were left running. One font open. The glyphs of MS reused (`ms1_a`, `ms1_t`, `ms1_k`). The predictions were stated in chat before each call. No stage needed a save. Nothing was saved. One run each, one master, straight contours.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1896 | `fontlab_status` | 0.216 / 0.95; `changes_by_font` [] | as predicted |
| 1897 | `get_glyph_outline ms1_a` | shape 0 plain: contour 0 (the four-sided outline), contour 1 (the square (600,600)–(650,650)); shape 1 the component of `ms1_src`: contour 2 (300,0)–(350,50); `verified` | as predicted |
| 1898 | `move_nodes ms1_a`, contour 2 node 0 from (300, 0) (right) to (310, 0) | refused, nothing moved: "the request names a contour of a component", `ms1_src` named (shape 1), ending "edit the source glyph 'ms1_src' instead"; no stale-request opening, no "Read the glyph again" | as predicted (the fix of 1870 holds); "nothing was moved:" comes first |
| 1899 | the same move with a wrong `from` (999, 999) (the control: a stale request and a component's contour at once) | the refusal of 1898, not the stale-request one | as predicted, word for word |
| 1900 | `remove_contours ms1_a`, expected 3, contour 2 | refused before any question, the same ending | as predicted; the reply came at once |
| 1901 | `get_glyph_outline ms1_t` | 1 plain identity element, 1 contour: the rectangle with the corner (330, 410) of 1886; `verified` | nodes as predicted; **`unverified` (prediction failed)**: FontLab's ink width 254 and top 404, its values before the 1886 move; `outline_lag_note`, `computed_from_nodes` ink width 260 |
| 1902 | `add_contours ms1_t` (one plain shape), expected 1, the square (600,600)–(650,650), no `shape` | `added`, `verified`; `new_contour_indices` [1]; `shape` 0; no several-shapes fields | as predicted (the fix of 1871 holds); FontLab's sidebearings lagged, `person_note` given |
| 1903 | `add_contours ms1_t`, expected 2, `shape` 0, the square (700,700)–(750,750) | `added`, `verified`; [2]; `shape` 0 | as predicted |
| 1904 | `add_contours ms1_a` (a plain shape and a component), expected 3, the square (700,700)–(750,750), no `shape` | `added`, `verified`; `edit_case` `several_shapes`; [2], the component's contour moves to 3; `shape` 0; `other_shapes_unchanged`, `sources_unchanged` true | as predicted (`contours_now` 4) |
| 1905 | `add_contours ms1_k` (a component only), expected 1, the square (600,600)–(650,650) | `added`, `verified`; `edit_case` `component`; [1]; `shape` 1, the new plain shape; `sources_unchanged` true | as predicted |
| 1906 | `finish_changes` | 4 changes, `complete` | as predicted |

Reading (one run each): `move_nodes` refuses a component's contour before the stale-request checks, naming the source glyph to edit instead, and `remove_contours` gives the same sentence; `add_contours` names in `shape` the shape that received the contours on every confirmed add: one plain shape with and without `shape`, a plain shape beside a component, components only. FontLab's ink box of `ms1_t` was still stale at 1901, long after the 1886 move, with a listener restart in between; whether the person used FontLab meanwhile was not asked ([WATCH-POINTS.md](WATCH-POINTS.md)). Not tested: a refused `add_contours` keeping `shape` only as an echo (stub only), curves, a rotated or mirrored component. The CL font `Unnamed1` (unsaved) now holds `ms1_a` (shape 0: the four-sided outline and two squares; a component), `ms1_t` (the moved rectangle and two squares), `ms1_k` (a component, then a square); nothing to keep.

### 1907: `flPackage` names only, for replacing `font.glyphs` (2026-11-26, listener 0.216 / server 0.95, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Step 1 of "How a call is proven" ([FONTLAB-API-RULES.md](FONTLAB-API-RULES.md) §10) for the top candidate of the legacy-call audit of 2026-11-26: FontLab's Python documentation names `flPackage.glyphs`, but it covers FontLab 9 as well. `/debug/classdir` reads only `dir()` and `__doc__` of the class: nothing constructed or called, no font touched, no `len` (that needs a package, a gated step). `fontlab_status` before and after: listener 0.216, server 0.95, one font open (the CL font `Unnamed1`, unsaved), change count 4 both times. The predictions were stated in chat before the call. No stage needed a save. One run.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1907 | `/debug/classdir?name=flPackage&members=glyphs,glyphsCount,addGlyph,deleteGlyph,findName,findGlyph` | `addGlyph`, `findName`, `glyphsCount` present (test 137); `glyphs` absent (low confidence); `deleteGlyph` present (low confidence); `findGlyph` absent; no side effect | as predicted: `glyphs` and `findGlyph` "not a public member"; `glyphsCount` "int"; `addGlyph(fgGlyph / flGlyph )`; `bool deleteGlyph(fgGlyph / flGlyph )`; `flGlyph findName(string name)`; change count 4 → 4 |

Reading (one run, names only): FontLab 8.9.5's `flPackage` has no `glyphs`, so the documented candidate does not exist on this version. Names that may cover the jobs of `font.glyphs`, none called: `findName` (a glyph by name), `glyphsCount`, `findUnicode`, `hasName`; listing every name is open (`initItr`, `initItrGlyph`, docstrings not read). Creation and deletion have `addGlyph` and `deleteGlyph`.

### 1908: `flPackage` names only, continued (2026-11-26, listener 0.216 / server 0.95, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The docstrings of the names 1907 left open. The same probe and set-up as 1907: nothing constructed or called, no font touched. `fontlab_status` before and after: listener 0.216, server 0.95, one font open (the CL font `Unnamed1`, unsaved), change count 4 both times. The predictions were stated in chat before the call. No stage needed a save. One run.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1908 | `/debug/classdir?name=flPackage&members=findUnicode,hasName,initItr,initItrGlyph,findFgId,renameGlyph` | `findUnicode`: an int in, an `flGlyph` out; `bool hasName(string name)`; `initItr`, `initItrGlyph`: iteration over glyphs (low confidence); `findFgId`: an int id in, an `flGlyph` out; `renameGlyph`: a glyph and a new name, return unknown (low confidence); no side effect | `flGlyph findUnicode(uint uni)`; `bool hasName(string name[, bool relaxed=false])`; **`initItr(fgTTInterpreter itr)` and `initItrGlyph(fgTTInterpreter itr, flGlyph glyph)` (predictions failed: a TrueType interpreter, not glyph iteration)**; `flGlyph findFgId(uint id)`; **`bool renameGlyph(fgGlyph glyph, string name, bool rename)` (prediction failed: the legacy glyph and a third flag)**; change count 4 → 4 |

Reading (one run, names only): of the jobs of `font.glyphs`, a glyph by name (`findName`, `hasName`) and the count (`glyphsCount`) have modern names on 8.9.5; listing every name has none found, and the duplicate-Unicode scan cannot use `findUnicode`, which returns one glyph. `findName` returns an `flGlyph`, while the listener builds its wrappers from the legacy glyph (the bridge row of §10).

### 1909–1931 AG2: Antigravity's read-only tools (2026-11-26, listener 0.216 / server 0.95, FontLab 8.9.5 in Demo mode)

The set-up through Claude Code in Claude Desktop's Code tab (1909–1918); the reads through Antigravity IDE with Gemini 4 Hydrogen Medium, in a new conversation (1919–1929); two checks through Claude Code afterwards (1930–1931). One font open, made by the user with File > New Font after closing every other font, unsaved; prefix `agr1`. The predictions of 1909–1918 were stated in chat before each group of calls; those of 1919–1929 were written by Claude into Antigravity's prompt before its run; 1930 and 1931 had none. Antigravity was told to call only the ten read-only tools and to write nothing; whether each of its calls showed an approval card was not recorded (its permission preset was "Auto"). Its run met four "no capacity" errors (HTTP 503) from Google's servers, retried by Antigravity itself. No stage needed a save. One run.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1909 | `fontlab_status` (Claude Code) | 0.216 / 0.95, one font, a name beginning "Unnamed" | as predicted: `Unnamed Regular`, path null; `changes_by_font` one row, "Unnamed Regular" 3 (see 1931) |
| 1910 | `create_glyph agr1_a` | created, layer created, no Unicode | as predicted, 1 → 2 glyphs, layer `Regular` |
| 1911 | `draw_polygon agr1_a` (100,0)(500,0)(500,700)(100,700) | `verified`, left 100, ink width 400, width 0 | as predicted, `synced` |
| 1912 | `set_glyph_width agr1_a 600` | 0 → 600 | as predicted, modern route |
| 1913 | `create_glyph agr1_b` | created, 2 → 3 | as predicted |
| 1914 | `draw_polygon agr1_b` (50,0)(250,0)(250,300)(50,300) | `verified`, left 50, ink width 200 | as predicted |
| 1915 | `set_glyph_width agr1_b 300` | 0 → 300 | as predicted |
| 1916 | `set_glyph_unicode agr1_b 57344` | changed, no other holder | as predicted, `also_held_by` [] |
| 1917 | `set_kerning agr1_a agr1_b −40` | before none, after −40 | as predicted, glyph : glyph, `fontlab_panel_refresh` called |
| 1918 | `finish_changes` | 8 changes; probably the 3 earlier ones as `other_changes` | as predicted: 8, `complete`; `other_changes` 3 by `antigravity-client` in "Unnamed Regular", 16:37:49–16:46:47 (the AGY font, closed before AG2) |
| 1919 | `fontlab_status` (Antigravity) | 0.216 / 0.95, one font | as predicted |
| 1920 | `get_current_font` | a name beginning "Unnamed", no path, `fonts_open` 1 | as predicted, `glyph_count` 3 |
| 1921 | `list_glyphs` | `.notdef`, `agr1_a`, `agr1_b` | as predicted |
| 1922 | `get_glyph_outline agr1_a` | `verified`, 1 closed contour, 4 nodes, x 100–500, y 0–700, advance 600 | as predicted |
| 1923 | `get_glyph_sidebearings agr1_a` | 100 / 100 / 600 | as predicted, ink width 400 |
| 1924 | `get_glyph_width agr1_b` | 300 | as predicted, `width_source` modern |
| 1925 | `check_glyph_unicode agr1_b` | 57344 | as predicted (no hex field in the reply) |
| 1926 | `get_kerning agr1_a agr1_b` | −40, glyph : glyph | as predicted |
| 1927 | `get_kerning_groups glyphs=["agr1_a"]` | in no kerning group on either side | as predicted, `group_count` 0; also `cross_check` "failed: flPackage.getAllGroups() returned a NoneType, not a list" (not predicted) |
| 1928 | `check_notdef` | `empty` | as predicted, `font_mature` false |
| 1929 | `get_glyph_width agr1_zz` (no such glyph) | an error naming the glyph, nothing changed | as predicted: "No glyph named 'agr1_zz' was found." |
| 1930 | `get_kerning_groups glyphs=["agr1_a"]` (Claude Code) | — | the same reply as 1927, `cross_check` failure included |
| 1931 | `fontlab_status` (Claude Code) | — | `changes_by_font` two rows, both "Unnamed Regular": 3 and 8 |

Reading (one run): every prediction held. Antigravity called the ten read-only tools, eight of them for the first time in Antigravity (`get_current_font`, `list_glyphs`, `get_glyph_sidebearings`, `get_glyph_width`, `check_glyph_unicode`, `get_kerning`, `get_kerning_groups`, `check_notdef`), and wrote nothing: the counts stayed at 3 and 8 (1931). Two findings. (1) The change log keeps one row per font but labels it by name, so the closed AGY font (3 changes) and this font (8) show as two rows named "Unnamed Regular", and 1918's `other_changes` names the AGY font's changes "Unnamed Regular" as well. At 1909 Claude said in chat that the listener had filed the AGY font's changes under the new font by name; 1931 contradicts that. (2) In a font with no kerning group, `get_kerning_groups` gives the right answer but reports its cross-check as failed and tells the agent that no group is confirmed, because `getAllGroups()` returns `None` when no group exists (1531); the same through Claude Code (1930), so it does not depend on the client.

### 1932–1934 AG3: Antigravity's cached tool descriptions after a server update (2026-11-26, listener 0.217 / server 0.96, FontLab 8.9.5 in Demo mode)

Antigravity IDE with Gemini 4 Hydrogen Medium. Before the run, Antigravity was closed with the X, leaving no `agy.exe` process. Claude Code copied its 28 cached description files for comparison: all dated 17:02, none with the 0.96 wording. Server 0.96 was already in the repository. The predictions were stated in chat before each step. One run.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1932 | the user starts Antigravity, opens no conversation, makes no tool call; Claude Code compares the cache with the copy | all files rewritten; `fontlab_status.json` and `finish_changes.json` hold the 0.96 wording; `get_kerning.json` (unchanged in 0.96) rewritten with the same content | as predicted: all 28 dated 19:46, only those two changed, both with `same_name` and `in_front` |
| 1933 | a new conversation, only if 1932 showed no change | — | skipped |
| 1934 | Antigravity `fontlab_status`, in a new conversation | server 0.96, listener 0.216; `changes_by_font` one row "Unnamed Regular", no `same_name` | server 0.96 as predicted; **listener 0.217 and `changes_by_font` `[]` (predictions failed)**: the user had restarted the listener alone at 19:39:03, which Claude had not checked |

Reading (one run): a full restart of Antigravity refreshes its cached tool descriptions from the server, without a new conversation. Not tested: a server change while Antigravity runs. The failed predictions in 1934 come from an assumption Claude did not check, not from Antigravity.

### 1935–1944: the live checks of listener 0.217 / server 0.96 (2026-11-26, FontLab 8.9.5 in Demo mode)

Two clients, both on server 0.96: Claude Code, named `local-agent-mode` in FontLab's OUTPUT panel, and Antigravity IDE with Gemini 4 Hydrogen Medium, named `antigravity-client`. Listener 0.217 since 19:39:03; the listener alone was restarted, FontLab kept running. Start: the AG2 font alone (`agr1_a`, `agr1_b`, the pair −40). The predictions were stated in chat before the run. No stage needed a save. One run.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1935 | `fontlab_status` (Claude Code) | 0.217 / 0.96; `changes_by_font` `[]`; one font | as predicted |
| 1936 | `get_kerning_groups glyphs=["agr1_a"]` | `cross_check` "done", `group_count` 0 | as predicted (AG2 1927 gave "failed") |
| 1937 | `get_kerning agr1_a agr1_b` | −40, glyph : glyph | as predicted |
| 1938 | the user opens Arial; `get_kerning_groups glyphs=["o"]`; the user closes Arial | a confirmed group, "done" (the control) | as predicted: `o` in `e`, right, confirmed; 72 groups; matched by path |
| 1939 | `create_glyph agr2_a`, then `fontlab_status` | one row "Unnamed Regular", 1 change, no `same_name` | as predicted, 3 → 4 glyphs |
| 1940 | the user closes the AG2 font (X, Don't Save) and makes File > New Font; `fontlab_status` | FontLab asks about saving; one row, no `same_name` | as predicted |
| 1941 | Antigravity `create_glyph agr3_a` in the new font | created; OUTPUT names `antigravity-client` | as predicted, 1 → 2 glyphs. The OUTPUT line at 19:55:54 reads "create agr3_a: created (verified, glyphs 1 -> 2)", seen in the user's screenshot after the run. Approval was asked under the "Auto" preset. Two HTTP 503 errors, retried by Antigravity. |
| 1942 | Antigravity `finish_changes` | 1 change, `complete`; `other_changes` 1 by Claude Code, `same_name` true, `in_front` false | as predicted: by `local-agent-mode` at 19:53:01; approval asked; its summary named the time |
| 1943 | `fontlab_status` (Claude Code) | two rows "Unnamed Regular", both `same_name`; old `in_front` false, new true; different times | as predicted: 19:53:01 and 19:55:54 |
| 1944 | `finish_changes` (Claude Code) | 1 change, `complete`; `other_changes` 1 by `antigravity-client`, `same_name`, `in_front` true; `fonts_changed` the name once | as predicted |

Reading (one run): both findings of AG2 are fixed live. The cross-check runs in a font with no kerning group (1936) and still confirms a real group (1938). Same-named rows carry `same_name`, their times and `in_front`, in `changes_by_font` (1943) and in `other_changes` on both clients (1942, 1944). A new finding: `fonts_changed` lists a shared font name once although two fonts changed (1942, 1944; [WATCH-POINTS.md](WATCH-POINTS.md)). Not tested: a font not in front that is still open.

### 1945–1951: FC, the live checks of server 0.97 (2026-11-26, FontLab 8.9.5 in Demo mode)

One client, Claude Code (`local-agent-mode`), in a new session whose server process started on 0.97; listener 0.217 since 19:39:03, unchanged. Start: one font open, the unsaved "Unnamed Regular" of 1940 (`.notdef`, `agr3_a`); the listener's log held the two changes of 1939 (19:53:01, in the font closed at 1940) and 1941 (19:55:54). This server process had made no `finish_changes` call; `fontlab_status` does not move its bookmark (read in the code before the run). The predictions were stated in chat before each call. No stage needed a save. One run. Glyph prefix `fc97_`.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1945 | `finish_changes` | 0 in the package, `complete`, a reminder; `other_changes` two rows (19:53:01 `in_front` false, 19:55:54 true); `fonts_changed` two objects "Unnamed Regular", `same_name`, the same times and `in_front`; `fonts_changed_note` | as predicted |
| 1946 | `finish_changes` again (the control) | 0, `save_reminder` null, no `fonts_changed`, no `other_changes` | as predicted |
| 1947 | `create_font family="Unnamed"` | "Unnamed Regular", 2 fonts open, the new one in front; possibly a temporary tab name | as predicted: PostScript name `Unnamed-Regular`; FontLab's tab and FONTS panel showed "Unnamed1" (the user's screenshot) |
| 1948 | `create_glyph fc97_a` in the new font | created, 1 → 2 | as predicted, layer `Regular` |
| 1949 | the user clicks the older font's tab; `fontlab_status`, `list_glyphs` | 2 fonts; three rows "Unnamed Regular", all `same_name`; the new font's row `in_front` false, last change 21:01:50, first 21:01:46 only if `create_font` counts (less certain); `.notdef`, `agr3_a` | as predicted: the new font's row 2 changes, 21:01:46–21:01:50, so `create_font` counts as a change |
| 1950 | `create_glyph fc97_b` in the older font | created, 2 → 3 | as predicted, at 21:38:03 |
| 1951 | `finish_changes` | 3 changes, `complete`, no `other_changes`; `fonts_changed` two objects, `same_name`: the new font 21:01:46–21:01:50 `in_front` false, the older font `in_front` true; the note; the reminder | as predicted |

Reading (one run): server 0.97 lists each changed font once in `fonts_changed`, also when two share a name, with that package's times and `in_front`, whether the other font was closed (1945) or is still open (1951, the first live case of a same-named font not in front and still open). Not tested: a package across midnight (the times are compared as text), a log entry without a font key (stub only), Claude Desktop and Antigravity on 0.97, a save in between (Demo mode).

### 1952: the shape classes' transform and history names (2026-11-26, listener 0.217 / server 0.97, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

`/debug/classdir` on `flShape`, `flLayer`, `flShapeData`, `flContour`, `flNode` and `flGlyph`: the public names, then the docstrings of the transform and history members; nothing was called. A first docstring request with `doc=1` returned one character each (`doc` is a length limit); repeated with `doc=600`. No member is named "expand". Found: `flShape.applyTransform([QTransform transform])` (the argument optional), the same on `flLayer` and `flGlyph`; `flContour.applyTransform()`, no argument; `flNode.applyTransform(QTransform)` and `transformBy(QTransform tx[, QPointF origin])`; `flShape.ejectTo([bool clone=true[, bool apply_tx=true]])` returning `list(flShape)`, `eject(flShape)`, `decomposite()`; `getTransformationPermissions()` returning `(enbl_horz, enbl_vert, enbl_rotation)`; `prepareTransformationData()` and `resetTransformationData()` on the shape, layer and glyph; and on every class looked at, history members: `hasHistoryStates`, `currentHistoryState()` ("currentHistoryIx()"), `initialHistoryState()` ("initialHistoryIx()"), `historyStates(bool accepted_state)`, `restoreHistoryState(uint history_ix)`, `checkInitHistoryState(uint)`, `clearAboveHistory(uint)`, `hasHistoryState(uint)`. Facts: [topics/transforms-and-undo.md](topics/transforms-and-undo.md).

### 1953–1957 XT: FontLab's own Expand Transformation and its Undo (2026-11-26, listener 0.217 / server 0.97, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

The user closed both earlier test fonts and made a new font with File > New Font ("Unnamed Regular", one font open). The predictions were stated in chat before each call; the user made each GUI step alone. No stage needed a save. One run. Glyph prefix `xt`. The user's prediction before the run: Expand Transformation makes the modification permanent, with Edit > Undo, for GUI actions only, as the way back.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1953 | `create_glyph xt1_a`, `draw_polygon` the square (100, 0), (300, 0), (300, 200), (100, 200) | created with a layer; `verified`, left 100, ink width 200 | as predicted; advance width 0 (not predicted) |
| 1954 | `get_glyph_outline xt1_a` | `verified`, identity, the nodes as drawn, ink box x 100–300, y 0–200 | as predicted |
| 1955 | the user scales the element with the Element tool (asked for 150 % both ways; entered 150 % horizontally, 100 % vertically; the panel's sidebearings 150 / −450); read | m11 1.5, m22 1; drawn 150…450, raw 100…300; `verified`, left 150, ink width 300 | as predicted |
| 1956 | the user chooses Element > Expand Transformation; read | identity; raw 150…450; outline, left, ink width and ink box unchanged | as predicted; the Edit menu then offered "Undo Expand Transformation" |
| 1957 | the user chooses Edit > Undo Expand Transformation once; read | m11 1.5 again, raw 100…300, drawn 150…450, `verified` | as predicted |

Reading (one run): FontLab's own expansion moves the element transform into the nodes and leaves the identity; the outline does not move; Edit > Undo takes it back. Every result was a whole number, so rounding was not seen here (1981).

### 1958–1962 XT2: `applyTransform()` by probe, and Edit > Undo (2026-11-26, listener 0.218 / server 0.97, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Listener 0.218 restarted before 1958 (the server unchanged; FontLab and Claude Desktop left running, the font of XT kept); `xt1_a` as after 1957. The predictions were stated in chat before each call. One run.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1958 | `fontlab_status` | listener 0.218, server 0.97, no `compatibility_note`, `changes_by_font` `[]` | as predicted |
| 1959 | `/debug/tryexpand?name=xt1_a&shape=0&how=noarg&go=yes` | identity; raw (150, 0), (450, 0), (450, 200), (150, 200); outcome "expanded"; drawn outline, ink box and sidebearings kept; no side effect; synced and marked; the same after the sync; the return value not predicted | as predicted; it returned `None`; the bottom nodes' y read −0.0 |
| 1960 | `get_glyph_outline xt1_a` | `verified`, identity, nodes 150…450 without `raw_x`, left 150, ink width 300 | as predicted |
| 1961 | the user opens the Edit menu, no click | Undo does not name the expansion; Redo may still read "Redo Expand Transformation" | **wrong:** "Undo Glyphbridge Expand", Redo greyed: the entry is the change mark's title, as "Glyphbridge Move Nodes" in 1023; FontLab's transform panel still showed 150 % (stale) |
| 1962 | the user chooses Edit > Undo Glyphbridge Expand once; read | (from 1023) the identity stays, raw 150…450, `verified` | as predicted; the transform panel caught up to 100 %; the menu was not seen afterwards |

Reading (one run): the probe's expansion equals the GUI's (1956). FontLab's Undo entry for it is only the mark's label; undoing it changes no data, as in 1023.

### 1963: `flItems` names only (2026-11-26, listener 0.218 / server 0.97, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

`/debug/classdir?name=flItems`: 172 public names, then docstrings; nothing was called. History-related: `notifyChangesApplied([QString title, flObject object / list(flObject)[, bool recursive=false]])`, `notifyEditActionStarted()`, `notifyEditActionFinished()`, `notifyHistoryChanged()`, `notifyUpdateHistory()`, `requestCheckHistoryInitIndex(flGlyphInfo)`; also `notifyEditingFinished()`, `notifyGlyphUpdated(uint packageId, uint glyphId)`, `notifyTransformStarted()`, `notifyNodeChanged(flNodeInfo)`.

### 1964–1970 XT3: FontLab's history values by probe (2026-11-26, listener 0.219 / server 0.97, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Listener 0.219 restarted before 1964 (as before XT2). The predictions were stated in chat before each call. One run each. "Current" is `currentHistoryState()`; a list is `historyStates(True)`, equal to `historyStates(False)` unless said; the probe shows a list's first three items.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1964 | `fontlab_status`; `create_glyph` and `draw_polygon` `xt2_a`, `xt3_a`, `xt4_a` (the square of 1953) | 0.219, `changes_by_font` `[]`; three glyphs, `verified` | as predicted |
| 1965 | the user scales `xt2_a` (asked for 150 % / 100 %; entered 166 % / 177 %); `get_glyph_outline` | m11 1.66, m22 1.77; drawn x 166…498, y 0…354; raw 100…300; `verified` | as predicted |
| 1966 | `/debug/tryhistory?name=xt2_a&shape=0&go=yes` (a) | no crash; values as bools, numbers, lists or types; the glyph or layer `hasHistoryStates` true, current ≥ initial (low confidence); nothing changed | as predicted: glyph current 25, initial 22, [22, 25]; layer none (false, 0, []); shape current 29, initial 0, [0, 29, 28] |
| 1967 | the user chooses Element > Expand Transformation on `xt2_a`; `tryhistory` (b) | the glyph's or shape's current rises, one new number; layer none; identity | as predicted: shape current 30, 4 states ([0, 30, 29, …]); glyph 25 unchanged; layer none; identity; Expand Transformation then greyed |
| 1968 | the user scales `xt3_a` (222 % / 77 %); `/debug/tryexpand?name=xt3_a&shape=0&how=noarg&history=yes&go=yes` (c) | expanded (raw 222…666, 0…154), synced, marked; the shape's history unchanged before, after and after the sync; the glyph unchanged after the call, not predicted after the mark | as predicted: shape 32 throughout; glyph 26 → 33 after the sync and mark ([33, 23, 26]); layer none |
| 1969 | the user scales `xt4_a` (55 % / 144 %); the same with `&bracket=yes` (d) | both bracket calls without error; expanded (raw 55…165, 0…288); the glyph a new state after the mark; the shape none (low confidence) | as predicted: both calls returned `None`; shape 35 throughout; glyph 27 → 36 |
| 1970 | the user chooses Edit > Undo once ("Undo Glyphbridge Expand" before; "Undo Change Element Transform" and "Redo Glyphbridge Expand" after); `get_glyph_outline`, `tryhistory` | nothing reversed: identity, raw 55…165, `verified`; shape 35; the glyph perhaps 36 → 27 (low confidence) | as predicted: the data unchanged; glyph current 27, `historyStates(True)` [27, 24], `historyStates(False)` [27, 36, 24]; shape 35 |

Reading (one run each): a GUI edit records a state on the shape (1967); an API edit records none (1968), also inside the bracket (1969); the standard mark records one on the glyph only (1968, 1969), and Undo steps the glyph's history back without touching the shape, so the outline stays (1970). `historyStates(True)` holds the states up to the current one, `historyStates(False)` the undone ones too (1970). The lists are not in a fixed order ([22, 25] in 1966, [27, 24] in 1969). Before an API edit, the shape's current state is the one its last GUI edit recorded (1968, 1969).

### 1971–1981 XT4: the change mark's variants, Undo and Redo, rounding (2026-11-26, listener 0.220 / server 0.97, FontLab 8.9.5 in Demo mode, through Claude Code in Claude Desktop's Code tab)

Listener 0.220 restarted before 1971 (as before XT2). The predictions were stated in chat before each call, except where a row says otherwise. One run each.

| # | Step | Predicted | Result |
|---|---|---|---|
| 1971 | `fontlab_status`; `xt5_a` and `xt6_a` created and drawn (the square of 1953) | 0.220, `changes_by_font` `[]`; `verified` | as predicted |
| 1972 | the user transforms `xt5_a` (X 23, Y −20, 147 % / 88 %); `/debug/tryexpand?name=xt5_a&shape=0&how=noarg&history=yes&mark=recursive&go=yes` (variant A) | identity, raw (170, −20)…(464, 156); `variant_mark` called with the glyph and `True`, no error, `glyph_has_changes` true; the standard mark not called; the shape unchanged after the call; the glyph a new state after the mark; the shape too (moderate to low confidence) | as predicted: glyph 39 → 44, layer 43 → 44, shape 43 → 44 (5 states); the layer held states for the first time |
| 1973 | the user chooses Edit > Undo once ("Undo Glyphbridge Expand" before; "Undo Move Element" and "Redo Glyphbridge Expand" after); read, `tryhistory` | **the expansion reversed** (moderate confidence): transform (1.47, 0, 0, 0.88, 23, −20), raw 100…300 / 0…200, drawn unchanged, `verified`; shape 43; the panel 147 % / 88 % | as predicted, in single precision (m11 1.4700000286, drawn x 170.0000029 and 464.0000086; the panel's right sidebearing −465); glyph 39, layer 43, shape 43; 44 kept in `historyStates(False)` |
| 1974 | the user chooses Edit > Redo Glyphbridge Expand once (unsure of the clicks; the menu then "Undo Glyphbridge Expand", Redo greyed); read, `tryhistory` | the expansion back: identity, raw 170…464 / −20…156, `verified`; current 44 | as predicted, exact values |
| 1975 | the user transforms `xt6_a` (X 10, Y 20, 130 % / 140 %, slant 5°, rotation 15°; read: m11 1.255704, m12 0.336465, m21 −0.244036, m22 1.383997, `verified`); the same call with `&mark=shape` (variant B) | expanded without rounding: raw (135.570, 53.646), (386.711, 120.939), (337.904, 397.739), (86.763, 330.446); the mark on the shape | **wrong:** `applyTransform()` rounded the nodes to whole units, (136, 54), (387, 121), (338, 398), (87, 330), already before the sync; outcome "other", the drawn outline moved by up to 0.446, the ink box moved; so the probe made no mark, as designed; no history state anywhere; sidebearings 87 / −387 after the sync |
| 1976 | `xt7_a` created and drawn; the user transforms it (X 20, Y 30, 150 % / 50 %); `&mark=shape` | raw (170, 30)…(470, 130); `variant_mark` with the shape and `False`, no error; the shape a new state; the glyph and layer none (low confidence) | as predicted: shape 56 → 57; glyph 52, layer none; `glyph_has_changes` true |
| 1977 | the user chooses Edit > Undo once ("Undo Glyphbridge Expand" before; "Undo Change Element Transform" and "Redo Glyphbridge Expand" after); read, `tryhistory` | before the click: reversed as in 1973; revised after the user's screenshot, before the read: the transform restored, the nodes not | the revised prediction: transform (1.5, 0, 0, 0.5, 20, 30), raw 170…470 / 30…130, **drawn 275…725 / 45…95**, the outline moved and stretched; shape 56; `verified` |
| 1978 | `xt8_a` created and drawn; the user gives it 1975's transform; read | the matrix and drawn nodes of `xt6_a`, `verified` | as predicted, number for number |
| 1979 | the user chose Edit > Undo by mistake instead of Element > Expand Transformation; read (predicted after the screenshot, before the read) | scale, slant and offset kept, no rotation, raw 100…300 | as predicted: (1.3, 0, 0.122484, 1.4, 10, 20), in single precision (left 139.9999952) |
| 1980 | the user chooses Edit > Redo Change Element Transform; read | 1978's matrix again, raw 100…300, perhaps in single precision | as predicted, differences below 0.000001 |
| 1981 | the user chooses Element > Expand Transformation; read | the GUI rounds as in 1975 (moderate confidence): (136, 54), (387, 121), (338, 398), (87, 330), identity | as predicted, node for node; left 87; Expand and Remove Transformation then greyed |

Reading (one run each): with the recursive mark FontLab records a state on the glyph, the layer and the shape after the API change, and the shape's earlier state from the GUI stays (1972); Edit > Undo then reverses the API expansion and Redo restores it (1973, 1974), the first Glyphbridge edit that Undo reversed. A mark on the shape alone records the transform only: Undo then brings the old transform back over the expanded nodes and damages the outline (1977). FontLab rounds expanded nodes to whole units, through the API (1975) and in its GUI (1981) alike. Undo restores values in single precision (1973, 1979). Not tested: the recursive mark after any other write, curves, components, several shapes, a saved font (Demo mode).
