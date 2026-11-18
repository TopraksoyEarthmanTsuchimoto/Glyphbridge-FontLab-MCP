# Glyphbridge-FontLab-MCP

Lets AI agents read and edit fonts open in **FontLab 8** through the Model Context Protocol (MCP). Two parts work together: a **listener** that runs inside FontLab, and an **MCP server** that your AI app starts.

What an agent can do today: read glyph outlines, widths, sidebearings, Unicode values and kerning pairs; create and delete glyphs; set widths, sidebearings, codepoints and kerning between two glyphs; draw straight and cubic outlines, closed or open; move nodes of an existing outline; place components; create a new font. **Glyphbridge never saves your font.** You save it yourself (File menu or Ctrl+S).

## Requirements

Make sure you have these installed on your computer:
- FontLab 8
- Python 3.14 or newer (3.15 tested)
- An AI app that can start a local (stdio) MCP server. Tested: Claude Desktop, ChatGPT Desktop

## Install on Windows (tested)

**Option 1:** open the AI agent of your choice and type *"Tell me how to install and use https://github.com/TopraksoyEarthmanTsuchimoto/Glyphbridge-FontLab-MCP on this computer"*.

**Option 2:** do these steps by hand:

1. Download or clone this repository, for example to `Documents\GitHub\Glyphbridge-FontLab-MCP` (You can use the green "< > Code" button and Download ZIP).
2. Open PowerShell in that folder and create the server's own Python environment:
   ```
   py -m venv venv
   .\venv\Scripts\python.exe -m pip install mcp==2.2.0
   ```
3. Copy `glyphbridge_fontlab_mcp_listener.py` to `Documents\FontLab\FontLab 8\Scripts\`.
4. Register the server in your AI app, with your own folder path, as described for your app below.
5. Fully quit your AI app (**including its tray icon**) and start it again.

Every app needs the same three values: `command` (the venv's `python.exe`), `args` (the full path of `glyphbridge_mcp_server.py`) and `cwd` (the repository folder).

### Claude Desktop

Open **Settings > Developer > Edit Config** and add this inside the file's top-level braces. Keep everything else that is already in the file:

```json
"mcpServers": {
  "glyphbridge-fontlab": {
    "command": "C:\\path\\to\\Glyphbridge-FontLab-MCP\\venv\\Scripts\\python.exe",
    "args": ["C:\\path\\to\\Glyphbridge-FontLab-MCP\\glyphbridge_mcp_server.py"],
    "cwd": "C:\\path\\to\\Glyphbridge-FontLab-MCP"
  }
}
```

### ChatGPT Desktop

Open `%USERPROFILE%\.codex\config.toml` in a text editor, keep a backup, and add this block at the end of the file, outside any other section:

```toml
[mcp_servers.glyphbridge-fontlab]
command = "C:\\path\\to\\Glyphbridge-FontLab-MCP\\venv\\Scripts\\python.exe"
args = ["C:\\path\\to\\Glyphbridge-FontLab-MCP\\glyphbridge_mcp_server.py"]
cwd = "C:\\path\\to\\Glyphbridge-FontLab-MCP"
```

Use **Work** or **Codex** mode: a plain chat has no Glyphbridge tools and offers to continue in Work mode. Approve each tool when asked. ChatGPT's Settings > Add-ons > MCP servers route is not tested.

### Other AI apps

Any app that starts a local (stdio) MCP server should work with the same three values. Not tested yet: please report what works.

## Install on macOS (not tested yet)

The same steps should apply, with these differences:
- Step 2: `python3 -m venv venv` and `venv/bin/python -m pip install mcp==2.2.0`.
- Step 3: FontLab's user Scripts folder in your Documents folder.
- Step 4: `command` is `.../venv/bin/python`. Claude Desktop's config is `~/Library/Application Support/Claude/claude_desktop_config.json`; ChatGPT Desktop's is not confirmed on macOS yet.

Please report what works.

## Linux

FontLab 8 has no Linux version and would need Wine. This setup is not supported or tested.

## Do not forget to start the listener: necessary in every session!

1. Start FontLab with or without a font.
2. Open the **Scripting** panel, open `glyphbridge_fontlab_mcp_listener.py` and run it. The Output panel shows the listener's version.
3. In your AI app, ask for example: *"Check the FontLab connection"* or *"What is the kerning between A and V?"*

The listener has to be started again every time FontLab starts. It only accepts connections from your own computer (`127.0.0.1:8765`).

## Trouble?

- "Cannot reach the Glyphbridge listener": start the listener (step 2 above).
- Tools missing: check the config file and its path, then fully quit your AI app (**including its tray icon**) and start it again. If tools are still missing or show old descriptions after that, quit and start it a second time. In ChatGPT Desktop, check that the chat is in Work or Codex mode.

Developer documentation: [mental-model/README.md](mental-model/README.md).
