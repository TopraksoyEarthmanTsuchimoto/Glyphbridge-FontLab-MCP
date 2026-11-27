# Mac session plan

> A plan for one visit to a Mac with a fully licensed FontLab 8 (written 2026-11-27, before the visit; listener 0.221 / server 0.99). **Scope: what is specific to macOS.** Every File > Save and save-question test is left out by the user's choice of 2026-11-27: they wait for a later computer ([DECISIONS.md](DECISIONS.md)). Reading the save reminder's Cmd+S (M21) stays: it is necessary, and it saves nothing. Results are recorded in [LIVE-TESTS.md](LIVE-TESTS.md) as they happen; this file stays unchanged during the visit and moves to `archive/` after it (section 9).

## 1. How to use this plan

**For the person.** Work through sections 3 to 7 in order. Each step says what to do, what to look at and what to report. One action at a time; when a step says *stop*, wait for the agent. If time runs short, follow the priority column in section 8. Nothing in this plan saves a font: when FontLab asks about saving, click **Don't Save**.

**For the agent on the Mac.** The `/s` skill does not exist on the Mac. Start Claude Code (or another agent) in the repository folder with: *"Follow the session start in AGENTS.md, then guide me through mental-model/MAC-SESSION-PLAN.md."* All of [AGENTS.md](../AGENTS.md) applies, in particular:
- The predictions below were written before the visit. **Repeat each one in chat before its call**, and record any that you change as changed.
- One variable per test; say what was and was NOT tested; FontLab is the oracle.
- Restart requests name each part, and say when and what not to touch.
- **Privacy:** the Mac's user name, computer name, IP address and serial number never go into a file. Write paths with `~`.

**Test numbers:** the series **MC**, numbers **3000 to 3099**, reserved for this visit so that Windows work in the meantime cannot collide. Record files: `~/3000_name.txt` and so on, as on Windows.

**Comparing like with like:** the Windows facts in this plan are from FontLab 8.9.5, Python 3.15.2, `mcp` 2.2.0. Use the same versions on the Mac where possible, so that macOS is the one variable. A different FontLab version is recorded, not avoided.

## 2. Before the trip (on Windows)

- **W1. Commit and push** the current state (the user, with GitHub Desktop). The Mac clones it.
- **W2. Windows controls** for the comparisons in section 6 (FontLab running with a new font open, listener 0.221 running; numbers from the normal sequence in [CURRENT-STATUS.md](CURRENT-STATUS.md)). The agent states the predictions first.
  - **W2a, reply times with FontLab in front** (curl is the same instrument as on the Mac):
    `1..12 | ForEach-Object { curl.exe -s -o NUL -w "%{time_total}`n" http://127.0.0.1:8765/health; Start-Sleep 5 } | Out-File $HOME\NNNN_win_front.txt`
  - **W2b, the same with FontLab minimized** (minimize it first, touch nothing until the command ends): the same line, file `NNNN_win_minimized.txt`.
  - **W2c, listener restart at once:** run W2a's line once more, then `curl.exe -s http://127.0.0.1:8765/shutdown`, then at once run the listener again from the Scripting panel. Report the OUTPUT lines. Expected on Windows: it starts.
  - **W2d, FontLab's own Python:** in the Scripting panel, run `import sys, platform; print(sys.version, sys.platform, platform.machine())`. This also settles an open item of [CURRENT-STATUS.md](CURRENT-STATUS.md).
- **W3. Ask the Mac's owner** (if it is not the user's): may we install Python 3.15.2, an AI app if missing, and Glyphbridge; edit the AI app's config; allow Terminal into the Documents folder; and remove it all afterwards (section 9)?
- **W4. Bring nothing else.** The Mac needs internet access for `git`, Python and `pip`.

## 3. The Mac and the install (MC, setup)

Each step tests the root [README](../README.md)'s macOS section. Note every place where that section was wrong, missing or unclear: the README is rewritten from these notes after the trip.

**M0. Facts about the Mac** (Terminal): `sw_vers; uname -m; sysctl -n machdep.cpu.brand_string`. Then FontLab > About FontLab 8: the version. In Activity Monitor, the **Kind** column of FontLab (Apple or Intel; Intel on an Apple chip means Rosetta). Report the AI apps installed and their versions. Record all in the first MC record.

**M1. Git.** `git --version`. *Predicted:* on a Mac without Apple's Command Line Tools a dialog offers to install them (several minutes). Allow it with the owner's OK.

**M2. The clone, outside Documents, Desktop and Downloads.** macOS asks before an app reads those folders; an AI app that starts the server could be stopped there without a visible question. `mkdir -p ~/Developer && cd ~/Developer && git clone https://github.com/TopraksoyEarthmanTsuchimoto/Glyphbridge-FontLab-MCP.git && cd Glyphbridge-FontLab-MCP`

**M3. Python.** `which python3 python3.15; python3 --version`. *Predicted:* `python3` is Apple's 3.9 (from the Command Line Tools), too old: `mcp` 2.2.0 needs 3.10 and the README asks for 3.14 or newer. Install Python 3.15.2 from python.org, then `python3.15 --version`. *Predicted:* `Python 3.15.2`, at `/usr/local/bin/python3.15`.

**M4. The server's Python.** `python3.15 -m venv venv && venv/bin/python -m pip install mcp==2.2.0`. *Predicted:* ends with `Successfully installed … mcp-2.2.0`.

**M5. The tests, before FontLab.** `venv/bin/python -B tests/run_all.py`. *Predicted:* four PASS lines at **6125 + 58 + 121 + 2057**, and a warning that the deployed listener copy is missing (not yet copied). The expected files hold no Windows paths and the repository stores LF line endings, so nothing should differ. A diff is a macOS finding: record it, never `--update`.

**M6. Identity.** `md5 -q glyphbridge_fontlab_mcp_listener.py glyphbridge_mcp_server.py`. *Predicted:* `4b90d48c09b180d207ba0c99fb3df8c5` and `34cb6a388a8aa632308d4128b72b8a88`, as on Windows (LF on both).

**M7. FontLab's Scripts folder.** `ls ~/Documents/FontLab/"FontLab 8"/Scripts`. *Predicted:* the folder exists once FontLab has run, as on Windows; Terminal may ask for access to Documents (allow, with the owner's OK; record whether it asked). If it does not exist, find the folder FontLab's Scripting panel offers and record it. Then `cp glyphbridge_fontlab_mcp_listener.py ~/Documents/FontLab/"FontLab 8"/Scripts/` and run M5 again. *Predicted:* four PASS and "deployed listener copy is identical". If the folder differs, `GLYPHBRIDGE_FONTLAB_SCRIPTS=<folder> venv/bin/python -B tests/run_all.py` points the runner at it.

## 4. The listener on macOS, with no AI app yet

The person starts FontLab and makes a new font (File > New Font). One GUI action at a time.

**M8. Start the listener:** Scripting panel, open the copied file, run it. *Predicted:* OUTPUT shows `glyphbridge_fontlab_mcp_listener.py v0.221` and `Listener started on http://127.0.0.1:8765 (main-thread polling)`; **no firewall question**, because the listener binds to 127.0.0.1 only. If macOS asks whether FontLab may accept incoming connections: click **Deny** and record it; local calls should still work.

**M9. FontLab's own Python** (the Mac side of W2d): the same line in the Scripting panel. *Predicted:* `sys.platform` `darwin`; `platform.machine()` `arm64` on an Apple chip unless FontLab runs under Rosetta (compare M0).

**M10. First calls from Terminal.** `curl -s http://127.0.0.1:8765/version`. *Predicted:* listener version `0.221`. Then `venv/bin/python glyphbridge_mcp_server.py --check`. *Predicted:* four `[OK]` lines, and FontLab's OUTPUT shows the connection from `"glyphbridge --check"` with the launcher **`ZSH`**. This is the first real run of the macOS launcher code (`_mac_process_info`, libproc); Terminal's shell is the known control. No launcher at all means libproc failed: record it.

**M11. Not reachable from the network.** `curl -s -m 3 http://$(ipconfig getifaddr en0):8765/health; echo "exit $?"`. *Predicted:* no answer (exit 7, connection refused). Do not record the address.

**M12. The first dialog, without an AI app:** `venv/bin/python glyphbridge_mcp_server.py --check --with-write-test`. It creates `glyphbridge_probe_…`, then asks Yes/No in FontLab to delete it. The person clicks **Yes**. Observe and report:
- where the question appears (a window of its own or a sheet on the font window), and whether it comes to the front while Terminal is in front;
- the order of the buttons, which one is the default (*predicted:* **No**, with the countdown "No (44)" ticking down);
- whether the dialog's text reads correctly.
*Predicted:* `[OK] delete_glyph`, and the width round trip `[OK]`.

## 5. AI apps on macOS

**Claude Code first, if it is installed** (or installed with the owner's OK, as Anthropic's documentation says). Then Claude Desktop. The other apps get one check each (M17).

**M13. The repository's `.mcp.json` on a Mac.** It names `venv/Scripts/python.exe`, a Windows path. *Predicted:* Claude Code lists `glyphbridge-fontlab` as failed. Record it: a macOS finding to fix after the trip. Workaround for the visit (local scope wins over the project file; check the syntax with `claude mcp add --help` first): `claude mcp add --scope local glyphbridge-fontlab -- "$PWD/venv/bin/python" "$PWD/glyphbridge_mcp_server.py"`, then `claude mcp list`. Restart: quit Claude Code and start it again in the repository folder; leave FontLab and the listener running.

**M14. Claude Desktop.** Settings > Developer > Edit Config. *Predicted:* it opens `~/Library/Application Support/Claude/claude_desktop_config.json`. Add the entry with `command` `…/venv/bin/python`, `args` the server's full path, `cwd` the folder (from `pwd`; not recorded). Restart: quit Claude Desktop with Cmd+Q (check the menu bar for its icon too) and open it again; leave FontLab and the listener running.

**M15. `fontlab_status` from each app** (one call). *Predicted:* `server_version` 0.99, `listener_version` 0.221, no `compatibility_note`. In FontLab's OUTPUT, the launcher after `|`. *Predicted, Claude Code:* **`CLAUDE`** (with a native install; `NODE` if installed through npm). *Claude Desktop:* **`CLAUDE`**; other names seen are data, not a failure (for example a helper process or a shell): record exactly.

**M16. A quit leaves no server behind.** After Cmd+Q of Claude Desktop: `pgrep -fl glyphbridge_mcp_server; echo "exit $?"`. *Predicted:* nothing listed (exit 1), apart from the server of Claude Code if it runs.

**M17. Other apps, if installed** (one `fontlab_status` each; their config files are unconfirmed on macOS):
- **ChatGPT Desktop:** *predicted* `~/.codex/config.toml`, the table of README step 4 with `venv/bin/python`; Work mode.
- **Antigravity:** `~/.gemini/config/mcp_config.json` (Google's documentation). *Predicted* OUTPUT name `antigravity-client`; the launcher is open (on Windows `AGY`).
Record the config path that worked, the launcher, and whether quitting the app leaves a server (M16's line).

## 6. Glyphbridge's work on macOS

Same steps as on Windows, so that a difference is a macOS difference. All writes go to the new font, names with the prefix **`mc1_`** (a new prefix for each repeat: `mc2_`, …). Before each call the agent states the prediction; the person reports FontLab's numbers when asked.

**M18. Reads and writes** (through the AI app):
- `get_current_font`: *predicted* an unsaved font, path empty, `fonts_open` 1.
- `create_glyph mc1_a`, then `draw_polygon` with `[[0,0],[400,0],[400,300],[0,300]]`, `set_glyph_sidebearings` 20 / 30, `set_glyph_width` 520, `get_glyph_outline`. *Predicted:* each write verified and synced; the outline `verified` from the modern layer, x 20..420; LSB 20, RSB 100, width 520. The person compares FontLab's Glyph panel (it rounds down).
- `draw_path` into the same glyph: *predicted* refused, the outline unchanged.
- `move_nodes` on `mc1_a` (the agent reads first and gives `from` and `to`): *predicted* verified.

**M19. Kerning on macOS.** `create_glyph mc1_k1` and `mc1_k2`, `set_kerning` −50, `get_kerning`, then `remove_kerning`. *Predicted:* −50 read back; the pair shows in the KERNING panel at once (the person checks); removed, a re-read shows no entry.

**M20. The OUTPUT panel:** the person reads the lines of M18–M19. *Predicted:* one short line per change and a "reads:" summary, with the client name and the launcher once per client; every character readable.

**M21. The save reminder, read only.** `finish_changes`. *Predicted:* the bold reminder names **Cmd+S**, not Ctrl+S (`SAVE_SHORTCUT`, never run on a Mac). The agent also quotes the sentence naming the shortcut in `set_glyph_width`'s description. **Do not press it**: this checks the text only, and is not a save test.

**M22. Dialogs from the AI app,** named by the button (DECISIONS.md, 2026-11-25). The agent states the plan and waits for "go". `create_glyph mc1_yes`, `mc1_no`, `mc1_noanswer`; then `delete_glyph` each: Yes, No, and no click for `mc1_noanswer`. **Keep the AI app in front** during these calls. Observe: does the question come to the front, does FontLab's Dock icon bounce, can the person reach it? *Predicted:* `mc1_yes` gone; `mc1_no` kept; `mc1_noanswer` kept with `not_answered_in_time` after about 45 s, the call still answered within the app's limit. If the dialog stayed hidden behind the AI app, that is the finding of this step.

**M23. Undo, optional** (only if time allows): the person makes a scaled shape in a glyph `mc1_x` (Element tool, horizontal 110 %); `expand_transformation`, preview and the person's yes in chat; then Edit > Undo and Edit > Redo (Cmd+Z, Cmd+Shift+Z). *Predicted,* as on Windows (XT5 1990, 1991): Undo restores the transform, Redo the expansion.

## 7. What only a Mac can show

**M24. FontLab in the background (App Nap).** macOS may slow down an app that is hidden or covered, and the listener depends on a 25 ms timer. One state per run; touch nothing while a run lasts (one minute):
- in front: `for i in $(seq 1 12); do curl -s -o /dev/null -w "%{time_total}\n" http://127.0.0.1:8765/health; sleep 5; done | tee ~/30NN_mac_front.txt`
- hidden (FontLab in front, then Cmd+H): the same line, file `30NN_mac_hidden.txt`;
- minimized (Cmd+M): file `30NN_mac_minimized.txt`.
*Predicted:* in front, every reply under 0.05 s. Hidden and minimized: **open**. Under the App Nap hypothesis the first replies are fast and later ones slower (0.1 s or more). Compare W2a and W2b. If slowed: one write (`set_glyph_width mc1_a 530`) with FontLab hidden, to see whether a slow reply reaches the 5 s limit. Changing App Nap settings is the owner's decision and not part of this visit.

**M25. Restarting the listener at once.** The listener does not set `SO_REUSEADDR`; on macOS a port with recent connections can stay busy for about 30 s. Run M24's front line, then `curl -s http://127.0.0.1:8765/shutdown`, then **at once** run the listener again. *Predicted:* `Could not bind 127.0.0.1:8765 -> [Errno 48] Address already in use` and the advice to reopen FontLab. Then wait 60 s and run it again: *predicted* it starts. Compare W2c. If confirmed, the advice "close and reopen FontLab" is wrong on a Mac: a finding for after the trip.

**M26. Running the listener a second time** while it runs (Scripting panel, run again). *Predicted:* "Listener already running", as the code says when the panel keeps the script's state. If it reports a bind error instead, the panel starts the script afresh: record which.

**M27. A path with a space and an accent.** `mkdir -p ~/Developer/"gb test é" && cp /System/Library/Fonts/Supplemental/Arial.ttf ~/Developer/"gb test é"/`. The person opens that file with File > Open Fonts… so that two fonts are open, with Arial in front. Then `get_current_font` and `get_kerning A:V`. *Predicted:* the path under `~/Developer/gb test é/` (written with `~` in records); the kerning read works, since it compares the font's path with itself; the value is the Mac Arial's own, compared with FontLab's KERNING panel, not with Windows. A refusal over the path is a macOS finding (Finder and Python may write `é` differently).

**M28. Two fonts, switching windows.** With M27's two fonts: the person brings the new font to the front through the Window menu; `fontlab_status`. *Predicted:* the reply names the font in front each time, as on Windows (T5).

## 8. Priority and time

| Priority | Steps | Estimate |
|---|---|---|
| Must | M0–M12, M13 or M14, M15, M18, M21, M22, M24, M25 | about 3 hours |
| Should | M16, M19, M20, M26, M27, M28 | about 1 hour |
| Could | M17, M23 | about 45 minutes |

**If FontLab crashes:** stop, record the last call and its reply, reopen FontLab, start the listener, and continue with a new prefix. **If a step fails:** record it with its prediction, and go on with the next step that does not depend on it.

## 9. Ending the visit and after it

**On the Mac:**
- Close every test font: **Don't Save**.
- Records: each MC result goes into [LIVE-TESTS.md](LIVE-TESTS.md) during the visit, under "MC, the Mac visit", with the step (M-number), the predicted and the seen values. Take them home by a push (if the user's GitHub login is wanted on that Mac), or with `git diff > ~/Desktop/mc-results.patch`, carried home and applied with `git apply`.
- If the Mac is not the user's: remove the Glyphbridge entries from each AI app's config, the listener from FontLab's Scripts folder, `~/Developer/Glyphbridge-FontLab-MCP` and `~/Developer/gb test é`, the `~/30NN_*.txt` files, and any Claude Code local entry (`claude mcp remove --scope local glyphbridge-fontlab`); sign out of GitHub and the AI apps. Python and Claude Code stay or go as the owner says.

**Back on Windows** (each as a proposal first, per AGENTS.md):
- [WHAT-WORKS.md](WHAT-WORKS.md), [CURRENT-STATUS.md](CURRENT-STATUS.md) (Environment), [PROJECT.md](PROJECT.md) (Scope) and [DECISIONS.md](DECISIONS.md) (2026-11-04, macOS compatibility): what is now proven on macOS.
- The root README's macOS section and a macOS part of [RUNBOOK.md](RUNBOOK.md), from M1–M17.
- Fixes found, one proposal each (candidates, if the predictions hold: `.mcp.json` that works on both systems; the listener's port on restart; App Nap).
- [refusals.md](topics/refusals.md) and [WATCH-POINTS.md](WATCH-POINTS.md) for anything open.
- Move this file to `archive/` with a dated suffix, and update [MARKDOWN-MAP.md](MARKDOWN-MAP.md).
