# Glyphbridge-FontLab-MCP

Lets AI agents such as Claude read and edit fonts open in **FontLab 8** through the Model Context Protocol (MCP). Two parts work together: a **listener** that runs inside FontLab, and an **MCP server** that your AI app starts.

What an agent can do today: read glyph outlines, widths, sidebearings, Unicode values and kerning pairs; create and delete glyphs; set widths, sidebearings, codepoints and kerning between two glyphs; draw closed straight and cubic outlines. **Glyphbridge never saves your font.** You save it yourself (File menu or Ctrl+S).

## Requirements

- FontLab 8
- Python 3.14 or newer (3.15 tested)
- Claude Desktop, or another MCP client that can start a local (stdio) server

## Install on Windows (tested)

1. Download or clone this repository, for example to `Documents\GitHub\Glyphbridge-FontLab-MCP`.
2. Open PowerShell in that folder and create the server's own Python environment:
   ```
   py -m venv venv
   .\venv\Scripts\python.exe -m pip install mcp==2.2.0
   ```
3. Copy `glyphbridge_fontlab_mcp_listener.py` to `Documents\FontLab\FontLab 8\Scripts\`.
4. In Claude Desktop open **Settings > Developer > Edit Config** and add this inside the file's top-level braces, using your own folder path. Keep everything else that is already in the file:
   ```json
   "mcpServers": {
     "glyphbridge-fontlab": {
       "command": "C:\\path\\to\\Glyphbridge-FontLab-MCP\\venv\\Scripts\\python.exe",
       "args": ["C:\\path\\to\\Glyphbridge-FontLab-MCP\\glyphbridge_mcp_server.py"],
       "cwd": "C:\\path\\to\\Glyphbridge-FontLab-MCP"
     }
   }
   ```
5. Fully quit Claude Desktop (including the tray icon) and start it again.

## Install on macOS (not tested yet)

The same steps should apply, with these differences:
- Step 2: `python3 -m venv venv` and `venv/bin/python -m pip install mcp==2.2.0`.
- Step 3: FontLab's user Scripts folder in your Documents folder.
- Step 4: `command` is `.../venv/bin/python`. Claude Desktop's config is `~/Library/Application Support/Claude/claude_desktop_config.json`.

Please report what works.

## Linux

FontLab 8 has no Linux version and would need Wine. This setup is not supported or tested.

## Do not forget to start the listener: necessary in every session!

1. Start FontLab with or without a font.
2. Open the **Scripting** panel, open `glyphbridge_fontlab_mcp_listener.py` and run it. The Output panel shows the listener's version.
3. In Claude, ask for example: *"Check the FontLab connection"* or *"What is the kerning between A and V?"*

The listener has to be started again every time FontLab starts. It only accepts connections from your own computer (`127.0.0.1:8765`).

## Trouble?

- "Cannot reach the Glyphbridge listener": start the listener (step 2 above).
- Tools missing in Claude: check the config path and restart Claude Desktop fully, sometimes twice.

Developer documentation: [mental-model/README.md](mental-model/README.md).
