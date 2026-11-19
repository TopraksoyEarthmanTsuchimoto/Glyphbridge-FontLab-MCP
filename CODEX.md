# CODEX.md

Notes for Codex only (including Codex and Work mode in ChatGPT Desktop). Everything else is in [AGENTS.md](AGENTS.md), which Codex loads by itself; this file is read because AGENTS.md says so. To check what was loaded, ask: "List the instruction sources you loaded."

## Connection and restarts

- The Glyphbridge tools come from the `[mcp_servers.glyphbridge-fontlab]` table in `%USERPROFILE%\.codex\config.toml`, which ChatGPT Desktop shares with Codex ([mental-model/RUNBOOK.md](mental-model/RUNBOOK.md), step 4b). A plain ChatGPT chat has no Glyphbridge tools; use Work or Codex mode.
- Each tool asks for approval on first use. A call that seems to hang is usually waiting for that approval.
- After a server change, fully quit ChatGPT Desktop (tray icon too), start it again, and start a new session: config and instructions are read when a session starts. Then read `fontlab_status` and check `server_version`.

## Shell

- On Windows the shell is PowerShell. If `wc -w` is missing, count words with this line; it can differ slightly from `wc -w` on files with dashes or arrows, so say which tool you used:
  `.\venv\Scripts\python.exe -c "import sys,re;print(len(re.findall(rb'\S+',open(sys.argv[1],'rb').read())))" AGENTS.md`
- Copying the listener to FontLab's Scripts folder writes outside the repository and may be refused by the approval prompt. If it is refused, give the user the copy command as one PowerShell line instead, and say the copy was not made.

## What the user sees

- A shared Codex session shows your messages, not your reasoning. Predictions, the Demo-mode statement and the plan you ask approval for must be written in a message before the call or edit they belong to.
