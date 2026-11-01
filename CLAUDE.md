@AGENTS.md

## Claude-specific notes

- The Glyphbridge tools appear as `mcp__glyphbridge-fontlab__<tool>`, both in Claude Code (from [.mcp.json](.mcp.json)) and in the Claude Desktop chat (from its config). They may be deferred: load them with ToolSearch `select:` before calling them.
- Do not call `get_current_font` first: it can open the `.notdef` dialog in FontLab. Start with `fontlab_status`.
- After a server change, fully quit Claude Desktop (tray too) and reopen it. Tool descriptions can stay stale until a second restart. A call that hangs right after a restart usually means an approval prompt is waiting.
- Restarting Claude Desktop also ends the running Claude Code session. Reopen it from the sidebar.
