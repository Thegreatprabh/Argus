# 👁️ ARGUS — Connect ANY AI Agent (Complete Setup Guide)

> One install. Every agent. If a connection fails, 99% of the time it's **the
> python path** — see [The Golden Rule](#-the-golden-rule-read-this-first).

## Step 0 — Install ARGUS (one command, every OS)

```bash
pip install git+https://github.com/Thegreatprabh/argus
```

Windows (if `pip` and `python` are different installs — very common):

```powershell
python -m pip install git+https://github.com/Thegreatprabh/argus
```

Verify the install:

```bash
python -m argus tools
# → should list 8 tools: web.analyze, binary.info, apk.overview,
#   frida.ps, firmware.peek, rebuild.scaffold, auto.rebuild, secrets.scan
```

---

## 🔑 The Golden Rule (read this first)

**GUI apps do NOT see your terminal's `python`.** Codex Desktop, ChatGPT Desktop,
Antigravity, Cursor — they launch with a minimal `PATH`, so a bare `python`
command fails silently and the server shows "Enabled" but never works in chat.

**Always use the FULL python path.** Find yours:

```bash
python -c "import sys; print(sys.executable)"
```

Examples of what it prints:

| OS      | Example full path                                              |
|---------|----------------------------------------------------------------|
| Windows | `C:\Users\YOU\AppData\Local\Programs\Python\Python314\python.exe` |
| macOS   | `/opt/homebrew/bin/python3`                                    |
| Linux   | `/usr/bin/python3`                                             |

Copy the **entire** line, `C:` to `python.exe`. That value goes in every
`command` field below.

> `argus setup` does this automatically — it writes `sys.executable` for you.

---

## ⚡ Automatic setup (recommended)

```bash
argus setup                # configure every agent it finds
argus setup --agent codex   # only one: claude | cursor | codex | gemini
argus setup --dry-run       # preview without writing anything
```

This writes the correct configs for **Claude Code** (`~/.claude.json`),
**Cursor** (`~/.cursor/mcp.json`), **Codex CLI** (`~/.codex/config.toml`) and
**Gemini CLI** (`~/.gemini/settings.json`).

**Then restart the agent app completely** (Quit, not just close window).
MCP servers load at startup.

---

## 🛠️ Manual setup — every famous agent

### 1. Codex Desktop (Windows / Mac)

1. Open **Settings → MCP servers → Add server**
2. Fill exactly:
   - **Name:** `argus`
   - **Type:** `STDIO` (not Streamable HTTP)
   - **Command:** your **full python path** from the Golden Rule above
   - **Arguments:** `-m argus.mcp_server`
3. **Save → Quit the app fully → reopen**
4. In the composer type `/mcp` → `argus` with 8 tools should appear

### 2. Codex CLI (terminal)

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.argus]
command = "<FULL PYTHON PATH>"
args = ["-m", "argus.mcp_server"]
```

Verify: `codex mcp list`, then `/mcp` inside a session.

### 3. ChatGPT Desktop App

Same flow as Codex Desktop — the ChatGPT desktop app shares the Codex MCP
config (`~/.codex/config.toml`):

1. **Settings → MCP servers → Add server → STDIO**
2. **Command:** full python path · **Arguments:** `-m argus.mcp_server`
3. Save → full restart → `/mcp`

> ⚠️ **chatgpt.com (web) cannot run local servers.** It only connects to
> *remote* MCP servers over HTTPS. The desktop app works because it launches
> the local process on your machine.

### 4. Claude Code

```bash
claude mcp add argus -- <FULL PYTHON PATH> -m argus.mcp_server
```

or manually in `~/.claude.json`:

```json
{
  "mcpServers": {
    "argus": {
      "command": "<FULL PYTHON PATH>",
      "args": ["-m", "argus.mcp_server"]
    }
  }
}
```

Restart Claude Code → `/mcp` to verify.

### 5. Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "argus": {
      "command": "<FULL PYTHON PATH>",
      "args": ["-m", "argus.mcp_server"]
    }
  }
}
```

Restart Cursor → Settings → MCP → `argus` enabled.

### 6. Gemini CLI

`~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "argus": {
      "command": "<FULL PYTHON PATH>",
      "args": ["-m", "argus.mcp_server"]
    }
  }
}
```

Restart your terminal session.

### 7. Antigravity (Google's AI IDE)

1. Open the **Agent panel** (right side) → click **`...`** → **MCP Servers**
2. Click **Manage MCP Servers → View raw config** (opens `mcp_config.json`)
3. Add:

```json
{
  "mcpServers": {
    "argus": {
      "command": "<FULL PYTHON PATH>",
      "args": ["-m", "argus.mcp_server"]
    }
  }
}
```

4. Save → back in **Manage MCP Servers** click **Refresh** → restart Antigravity

### 8. Claude Desktop

Edit `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "argus": {
      "command": "<FULL PYTHON PATH>",
      "args": ["-m", "argus.mcp_server"]
    }
  }
}
```

Save → restart Claude Desktop.

### 9. Termux (Android)

```bash
pkg install python git
pip install git+https://github.com/Thegreatprabh/argus
argus setup --agent gemini
```

Then use Gemini CLI in Termux — ARGUS is Termux-native (only needs `requests`).

---

## ✅ Verify (any agent)

Ask the agent: **"list all MCP tools"** — you should see the 8 ARGUS tools.
Or trigger one directly:

- *"Use argus to analyze https://example.com"* → `web.analyze`
- *"Scan this APK for secrets and risk"* → `secrets.scan` + `apk.overview`
- *"Rebuild this site with argus"* → `auto.rebuild`

---

## 🩺 Troubleshooting

| Problem | Fix |
|---|---|
| Server shows **Enabled** but tools missing in chat | Full python path in Command (not bare `python`); **Quit** app fully and reopen |
| `argus: command not found` (Windows) | Use `python -m argus ...` — the Scripts folder isn't in PATH |
| `pip` installed it but `python` can't find it | Install with the same interpreter: `python -m pip install ...` |
| Old version stuck after `--upgrade` | `python -m pip install --upgrade --force-reinstall git+https://github.com/Thegreatprabh/argus` |
| Diagnose everything at once | `python -m argus doctor` — checks python, install, MCP handshake, and prints the exact values to paste |

---

*ARGUS v0.2.1 · 8 engines · 8 MCP tools · MIT · by Prabhjot Singh*
