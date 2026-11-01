# Runbook

> Moved from milestone summary v11 (operational part of §1, §13, Appendix A) on 2026-11-01, edited only where the chat-era workflow or a personal path no longer applies. The original section numbers are kept, so older cross-references such as "section 8p" still resolve: [MARKDOWN-MAP.md](MARKDOWN-MAP.md) lists which file holds each section. Snapshot: [archive/milestone-summary-v11.md](archive/milestone-summary-v11.md).

## Setting up a machine (developer setup, Windows; first done this way on 2026-11-01)

1. Clone the repository. The two scripts stay in the repository root: `tests/run_all.py` reads them from the parent of `tests/`.
2. Create the server's private Python in the repository: `py -m venv venv`, then `.\venv\Scripts\python.exe -m pip install mcp==2.2.0`. `venv\` is ignored by git. Never copy a venv from another machine: its `pyvenv.cfg` points at that machine's Python. Verified with Python 3.15.2; the old machine used 3.14.7.
3. Copy `glyphbridge_fontlab_mcp_listener.py` into `~\Documents\FontLab\FontLab 8\Scripts\`. FontLab runs the listener from there and `run_all.py` warns when that copy differs from the repository copy.
4. **Claude Desktop:** add a `glyphbridge-fontlab` entry under `mcpServers` with `command` = the venv's `python.exe`, `args` = the full path of `glyphbridge_mcp_server.py`, and `cwd` = the repository folder (all absolute paths). Open the file from **Settings > Developer > Edit Config**: the Store (MSIX) build does not read `%APPDATA%\Claude\claude_desktop_config.json`. It reads a file inside its own data folder, and Claude Desktop's `main.log` names that file on startup. Claude Desktop also writes its own preferences into the same file, so add the `mcpServers` key and never replace the file.
5. **Claude Code:** the repository's [`.mcp.json`](../.mcp.json) starts the same server with repository-relative paths. Claude Code asks once to approve it.
6. Start the listener (next section), fully restart Claude Desktop, and check: `Invoke-RestMethod "http://127.0.0.1:8765/version"` should give the listener version, `.\venv\Scripts\python.exe glyphbridge_mcp_server.py --check` should print four `[OK]` lines, and `fontlab_status` should report the versions in [CURRENT-STATUS.md](CURRENT-STATUS.md). Stop the listener with `Invoke-RestMethod "http://127.0.0.1:8765/shutdown"`; FontLab keeps running.

## Operating rules (from §1)

**Restart rules:** after changing the server, fully quit Claude Desktop (tray too) and reopen; **then call `fontlab_status` and READ `server_version` / `listener_version`**
(a tool call that times out with no answer after a restart usually means an unanswered Claude Desktop approval prompt: allow it, then retry; check the font's state with a
read-only call before repeating a write). After changing the listener, restart it
from the Scripting panel; the Output panel prints its version (and "Connected at HH:MM:SS" on the first request). FontLab itself need not be restarted for either. Never run setup
from an elevated terminal. FontLab modern object ids (`flGlyph.id`) change between sessions: never store them.

**PowerShell (user's shell):** ONE line per command; loops as `"a","b" | ForEach-Object { ... }` (a `foreach` statement cannot be
piped); numbers may print with a decimal comma, depending on the Windows locale (the JSON is fine). Read: `Invoke-RestMethod "<url>"`. POST:
`Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8765/glyph/create" -Body '{"name":"x"}' -ContentType "application/json"`.

**Test-result numbering:** a live-test command writes its output to `$HOME\N_name.txt`, N first. Either the user or the agent runs it; in Claude Code the agent can read the file itself. Use DISTINCT numbers that do not resemble earlier ones (the last used was **154b** (kerning probes 146 to 154b); **135** (File > Save) stays DEFERRED; v9's **136a / 136b** are superseded by 139a / 139b and 142; the commands **144a / 144b / 145** (T3 / T4, Appendix A2 / A3) were prepared in v10 but NEVER run; continue from **155**).

**FontLab GUI facts for testing:** only the *Element* selection tool shows the transform bar (X/Y, horizontal/vertical %, rotation,
slant). The X/Y box at the bottom shows the selected node in the *displayed* (transformed) space, one decimal. The Glyph panel's
width/LSB/RSB are **truncated integers**: compare exact values through the API. Fonts opened from the system get pseudo paths such
as `:/Arial: Normal`.

## 13. Re-verify after any change

1. Tests (`python tests\run_all.py` from the project folder: four PASS lines, **1489 + 58 + 90 + 668 lines** at v0.95 / v0.31 (v0.89 / v0.29: 1117 + 58 + 90 + 530; v0.88 / v0.28: 1092 + 58 + 90 + 511; v0.87 / v0.27: 983 + 58 + 90 + 490), plus its report of which files were tested and whether the Scripts copy of the listener is identical). 2. Restart the listener; check its version in FontLab's Output panel against [CURRENT-STATUS.md](CURRENT-STATUS.md). 3. Fully restart Claude Desktop after a server change, then call `fontlab_status`: `server_version` and `listener_version` as in CURRENT-STATUS.md, no `compatibility_note`.

3b. Geometry smoke test (disposable glyphs only; names that start with a NEW prefix): `create_glyph`, `draw_polygon` with a rectangle, `draw_path` with one curved edge (expect ink width 475 for handles at x = 500), a SECOND draw into the same glyph (expect a refusal "layer not KNOWN to be empty" and an unchanged outline), `set_glyph_sidebearings`, `get_glyph_outline` (expect `source: "modern layer"`, `verified`), then open the glyph in an editor tab and compare FontLab's numbers; quit FontLab WITHOUT saving afterwards.
3c. Stale-legacy-view smoke test (v0.25 / v0.26): on a glyph that the person has OPENED in an editor tab: read the outline (expect `verified` and `modern_margins_check: agrees`), `set_glyph_sidebearings(20, 30)`, read the outline at once (expect `unverified`, `stale_legacy_view: true`, legacy 0 / 50 against modern 20 / 30 for the bulging rectangle), ask the person to CLOSE the editor tab and double-click the thumbnail, read again (expect `verified`, nodes moved by +20, `agrees`).
3e. Auto-sync smoke test (v0.89 / v0.29, disposable font open, nothing saved): Appendix A (142 as written there): every write reply must say `synced_with_fontlab: true` with `fontlab_sync.synced: true`, the outline reads must show `margins_agree: true`, the creates must not skip their refresh, nothing may be lost; quit FontLab WITHOUT saving afterwards.
3f. Kerning smoke test (v0.95 / v0.31; Arial open, listener v0.95, pure reads): K1, K2 and K4 of section 14 (A4 in Appendix A): the 13 proven pairs answer the values of section 8p with `errors` 0, `table_size` 1370, `side_effect_detected` false; through Claude Desktop the agent reads only the pairs asked for. A request for more than 250 pairs must be refused and the agent must ask the person (K8).
4. For reference glyphs of the local test font: `.\venv\Scripts\python.exe glyphbridge_mcp_server.py --check --outline NAME`; expect `verified` and "read directly". 5. After one outline call: `1..3 | ForEach-Object { (Invoke-RestMethod "http://127.0.0.1:8765/glyph/outline?name=NAME").elements.wrapper }` prints `cached` x3. 6. `Invoke-RestMethod "http://127.0.0.1:8765/font/notdef" | ConvertTo-Json -Compress`. 7. Ask Claude about a glyph's shape. 8. For name/Unicode changes: create a standard-named glyph (expect `assigned`), create a name with an unsafe character (expect a refusal and an unchanged glyph count), `create_glyph('uni00e8')` (expect the lowercase-hex hint), then quit FontLab without saving. 9. For the save policy: ask Claude for several changes in ONE request (e.g. create three glyphs, set a width, delete one) and check that the chat ends with ONE bold "You must save..." line, none per step, and that FontLab shows no extra dialog (and that a pure read request produces no reminder).

## Appendix A. Ready PowerShell commands (all single-line; helper `Gb`; output `N_name.txt`, read by the agent or shared by the user; a screenshot only if the GUI shows something odd)

**A1. Regression smoke test of the auto sync (test 142; stage: FontLab started, the disposable font `savedtestfont.vfc` open, no other font, listener v0.89 running; quit FontLab WITHOUT saving afterwards; the names `stl88`, `stl89`, `stl90` must not exist):**
```
$o='142_real_font.txt'; $h='http://127.0.0.1:8765'; function Gb($m,$p,$b){ "== $(Get-Date -Format HH:mm:ss) $m $p $b" | Out-File $o -Append -Encoding utf8; try { if($m -eq 'GET'){ $r=Invoke-RestMethod "$h$p" } else { $r=Invoke-RestMethod "$h$p" -Method Post -Body $b -ContentType 'application/json' }; ($r | ConvertTo-Json -Depth 10 -Compress) | Out-File $o -Append -Encoding utf8 } catch { "ERR $_" | Out-File $o -Append -Encoding utf8 } }; Gb GET '/version'; Gb GET '/font/current'; Gb POST '/glyph/create' '{"name":"stl88"}'; Gb POST '/glyph/polygon' '{"name":"stl88","points":[[0,0],[400,0],[400,300],[0,300]]}'; Gb GET '/debug/trymodern?stage=state&name=stl88'; Gb GET '/glyph/outline?name=stl88'; Gb POST '/glyph/sidebearings' '{"name":"stl88","left":20,"right":30}'; Gb GET '/debug/trymodern?stage=state&name=stl88'; Gb GET '/glyph/outline?name=stl88'; Gb GET '/glyph/sidebearings?name=stl88'; Gb POST '/glyph/width' '{"name":"stl88","width":520}'; Gb GET '/glyph/outline?name=stl88'; Gb POST '/glyph/create' '{"name":"stl89"}'; Gb POST '/glyph/polygon' '{"name":"stl89","points":[[0,0],[300,0],[300,200],[0,200]]}'; Gb POST '/glyph/create' '{"name":"stl90"}'; Gb GET '/debug/trymodern?stage=state&name=stl88'; Gb GET '/debug/trymodern?stage=state&name=stl89'; Gb GET '/glyph/outline?name=stl88'; Gb GET '/glyph/outline?name=stl89'; Gb GET '/glyph/sidebearings?name=stl88'; Gb GET '/glyph/sidebearings?name=stl89'
```
Expected (seen live): every write reply `synced_with_fontlab: true` and `fontlab_sync.synced: true`; the state reads `synced`; stl88 ends with x 20..420, margins 20 / 100 / 520; stl89 keeps its outline (0 / -300 / advance 0); no `display_refresh_skipped_to_protect` anywhere.

**A2. T3 (the original stale scenario with the sync; stage as A1; names with a NEW prefix).** Run 144a:
```
$o='144a_open.txt'; $h='http://127.0.0.1:8765'; function Gb($m,$p,$b){ "== $(Get-Date -Format HH:mm:ss) $m $p $b" | Out-File $o -Append -Encoding utf8; try { if($m -eq 'GET'){ $r=Invoke-RestMethod "$h$p" } else { $r=Invoke-RestMethod "$h$p" -Method Post -Body $b -ContentType 'application/json' }; ($r | ConvertTo-Json -Depth 10 -Compress) | Out-File $o -Append -Encoding utf8 } catch { "ERR $_" | Out-File $o -Append -Encoding utf8 } }; Gb GET '/version'; Gb POST '/glyph/create' '{"name":"opn91a"}'; Gb POST '/glyph/polygon' '{"name":"opn91a","points":[[0,0],[400,0],[400,300],[0,300]]}'; Gb GET '/glyph/outline?name=opn91a'
```
Then ONE GUI action: double-click `opn91a` in the grid to open it in an editor tab and LEAVE it open (touch nothing else). Then 144b:
```
$o='144b_open.txt'; $h='http://127.0.0.1:8765'; function Gb($m,$p,$b){ "== $(Get-Date -Format HH:mm:ss) $m $p $b" | Out-File $o -Append -Encoding utf8; try { if($m -eq 'GET'){ $r=Invoke-RestMethod "$h$p" } else { $r=Invoke-RestMethod "$h$p" -Method Post -Body $b -ContentType 'application/json' }; ($r | ConvertTo-Json -Depth 10 -Compress) | Out-File $o -Append -Encoding utf8 } catch { "ERR $_" | Out-File $o -Append -Encoding utf8 } }; Gb GET '/glyph/outline?name=opn91a'; Gb POST '/glyph/sidebearings' '{"name":"opn91a","left":20,"right":30}'; Gb GET '/glyph/outline?name=opn91a'; Gb GET '/glyph/sidebearings?name=opn91a'; Gb GET '/debug/trymodern?stage=state&name=opn91a'
```
Expected: the sidebearings reply `synced_with_fontlab: true`, `fontlab_sync.synced: true`; the outline right after: x 20..420, `margins_agree: true`, no `modern_outline`. The editor panel numbers may still show the old values (8f). If `margins_agree` is false the fallback answers from the modern layer: record which, do not guess.

**A3. T4 (existing glyph of a real font; stage as A1; nothing saved).** Predicted from test 143: `testglyph2` has lsb 102.15479625533814, rsb 117, advance 500, ink 280.84520374466183. After width 560: advance 560, rsb 177, outline unchanged. After sidebearings 50 / 60: lsb 50, rsb 60, advance 390.845, every node moved by -52.1548 in x (the first node 128 -> 75.845).
```
$o='145_existing.txt'; $h='http://127.0.0.1:8765'; function Gb($m,$p,$b){ "== $(Get-Date -Format HH:mm:ss) $m $p $b" | Out-File $o -Append -Encoding utf8; try { if($m -eq 'GET'){ $r=Invoke-RestMethod "$h$p" } else { $r=Invoke-RestMethod "$h$p" -Method Post -Body $b -ContentType 'application/json' }; ($r | ConvertTo-Json -Depth 10 -Compress) | Out-File $o -Append -Encoding utf8 } catch { "ERR $_" | Out-File $o -Append -Encoding utf8 } }; Gb GET '/glyph/outline?name=testglyph2'; Gb GET '/glyph/sidebearings?name=testglyph2'; Gb POST '/glyph/width' '{"name":"testglyph2","width":560}'; Gb GET '/glyph/outline?name=testglyph2'; Gb POST '/glyph/sidebearings' '{"name":"testglyph2","left":50,"right":60}'; Gb GET '/glyph/outline?name=testglyph2'; Gb GET '/glyph/sidebearings?name=testglyph2'; Gb GET '/debug/trymodern?stage=state&name=testglyph2'
```
Test 135 (File > Save) and everything like it stays DEFERRED. Tests 136a / 136b of v9 are superseded by 139a / 139b and 142 (the guard was verified live).

**Appendix A, v11 additions (kerning; stage: Arial open from the system, listener v0.95; pure reads, nothing is written; the helper `Gb` is the one of A1, here with the error BODY added so a 400 shows its message; output files 155 to 158).**

**A4. K2 (test 155): the 13 proven pairs and one word, GET.**
```
$o='155_kern_get.txt'; $h='http://127.0.0.1:8765'; function Gb($m,$p,$b){ "== $(Get-Date -Format HH:mm:ss) $m $p $b" | Out-File $o -Append -Encoding utf8; try { if($m -eq 'GET'){ $r=Invoke-RestMethod "$h$p" } else { $r=Invoke-RestMethod "$h$p" -Method Post -Body $b -ContentType 'application/json' }; ($r | ConvertTo-Json -Depth 10 -Compress) | Out-File $o -Append -Encoding utf8 } catch { "ERR $_ $($_.ErrorDetails.Message)" | Out-File $o -Append -Encoding utf8 } }; Gb GET '/version'; Gb GET '/kerning/pairs?pairs=A:V,V:A,T:o,A:B,Aacute:V,Adieresis:V,T:oacute,T:odieresis,A:Wgrave.c2sc,Aacute:Wgrave.c2sc,Atilde:Ydieresis.c2sc,A:Tbar.c2sc,Aacute:Tbar.c2sc'; Gb GET '/kerning/pairs?text=AVATAR'
```
Expected: see K2 (the values of probes 150 / 151 / 154b; `errors` 0; `table_size` 1370; `side_effect_detected` false). Compare the `AVATAR` row with the KERNING panel (K5).

**A5. K3 (test 156): the same pairs by POST (the form the server uses).**
```
$o='156_kern_post.txt'; $h='http://127.0.0.1:8765'; function Gb($m,$p,$b){ "== $(Get-Date -Format HH:mm:ss) $m $p $b" | Out-File $o -Append -Encoding utf8; try { if($m -eq 'GET'){ $r=Invoke-RestMethod "$h$p" } else { $r=Invoke-RestMethod "$h$p" -Method Post -Body $b -ContentType 'application/json' }; ($r | ConvertTo-Json -Depth 10 -Compress) | Out-File $o -Append -Encoding utf8 } catch { "ERR $_ $($_.ErrorDetails.Message)" | Out-File $o -Append -Encoding utf8 } }; Gb POST '/kerning/pairs' '{"pairs":[["A","V"],["V","A"],["T","o"],["A","B"],["Aacute","V"],["Adieresis","V"],["T","oacute"],["T","odieresis"],["A","Wgrave.c2sc"],["Aacute","Wgrave.c2sc"],["Atilde","Ydieresis.c2sc"],["A","Tbar.c2sc"],["Aacute","Tbar.c2sc"]]}'; Gb POST '/kerning/pairs' '{"text":"AVATAR"}'
```
Expected: the same `results` as A4.

**A6. K7 (test 157): refusals and one per-pair error.**
```
$o='157_kern_errors.txt'; $h='http://127.0.0.1:8765'; function Gb($m,$p,$b){ "== $(Get-Date -Format HH:mm:ss) $m $p $b" | Out-File $o -Append -Encoding utf8; try { if($m -eq 'GET'){ $r=Invoke-RestMethod "$h$p" } else { $r=Invoke-RestMethod "$h$p" -Method Post -Body $b -ContentType 'application/json' }; ($r | ConvertTo-Json -Depth 10 -Compress) | Out-File $o -Append -Encoding utf8 } catch { "ERR $_ $($_.ErrorDetails.Message)" | Out-File $o -Append -Encoding utf8 } }; Gb GET '/kerning/pairs'; Gb GET '/kerning/pairs?pairs=A:V&text=AV'; Gb GET '/kerning/pairs?pairs=A:Qzq,A:V'; Gb GET '/kerning/pairs?pairs=A:V:B'; Gb GET '/kerning/pairs?text=A'; Gb POST '/kerning/pairs' '{"pairs":[["A","V"]],"go":"yes"}'; Gb POST '/kerning/pairs' '{"pairs":[]}'; Gb POST '/kerning/pairs' '{"text":5}'
```
Expected: every answer except the third is HTTP 400 with a specific message (`ERR` lines with the message body); the third is HTTP 200 with `errors` 1: the pair `A:Qzq` has `error` "no glyph named 'Qzq'" and `A:V` still reads -152.

**A7. K11 (test 158): names only, the OpenType features object of the font (nothing is called).**
```
$o='158_features.txt'; $h='http://127.0.0.1:8765'; function Gb($m,$p,$b){ "== $(Get-Date -Format HH:mm:ss) $m $p $b" | Out-File $o -Append -Encoding utf8; try { $r=Invoke-RestMethod "$h$p"; ($r | ConvertTo-Json -Depth 10 -Compress) | Out-File $o -Append -Encoding utf8 } catch { "ERR $_ $($_.ErrorDetails.Message)" | Out-File $o -Append -Encoding utf8 } }; Gb GET '/debug/fontdir?stage=sub&attr=features'
```
Expected: the type, `len`, docstring and public names of `font.features` (and nothing else). Then PROPOSE (do not build) what a feature read would need.

A1 to A3 above were written for v0.89 and still work with v0.95 (the listener banner then says v0.95). Test 135 (File > Save) and everything like it stays DEFERRED.
