# GEMINI.md

Notes for Gemini in Antigravity only. Everything else is in [AGENTS.md](AGENTS.md). Antigravity loads both files by itself before every turn, so this file never copies or imports AGENTS.md: it would then be loaded twice. Checked 2026-11-26, in a test folder and with this repository open as the workspace. Gemini CLI also reads this file; nothing here is tested there.

## Connection and restarts

- The Glyphbridge tools come from the `glyphbridge-fontlab` entry in `%USERPROFILE%\.gemini\config\mcp_config.json` ([mental-model/RUNBOOK.md](mental-model/RUNBOOK.md), step 4c). They are listed under ⋮ > Settings > Conversations > Customizations, after Show breakdown.
- Each tool asks "Allow using this MCP tool?" before it runs. A call that seems to hang is usually waiting for that answer. An "always allow in this conversation" grant ends with the conversation.
- After a server change, close Antigravity with the X and start it again, then read `fontlab_status` and check `server_version`. Antigravity had no tray icon and ended fully on 2026-11-26; an update may change that, so check that no `agy.exe` process remains before calling it a restart.
- Antigravity keeps one description file per tool in `%USERPROFILE%\.gemini\antigravity\mcp\glyphbridge-fontlab\`. Whether a server update refreshes them, and whether a new conversation is needed, is not tested: after a server change, compare one file with the server's new description before relying on it.
- A tool call ends after 180 s by default (Google's documentation, not run). A FontLab dialog that waits longer is cut off.
- FontLab's OUTPUT panel names this app `antigravity-client | AGY`.

## Live tests

- Record the model and its setting (for example "Gemini 4 Hydrogen Medium") with each live test, and change it only between tests.
- If `wc -w` is missing, count words with this line and say which tool you used:
  `.\venv\Scripts\python.exe -c "import sys,re;print(len(re.findall(rb'\S+',open(sys.argv[1],'rb').read())))" AGENTS.md`
