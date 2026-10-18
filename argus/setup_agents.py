"""`argus setup` — connect every AI agent in one command.

Writes/updates MCP server configs so agents can call ARGUS tools:
  - Claude Code  -> ~/.claude.json            (mcpServers)
  - Cursor       -> ~/.cursor/mcp.json         (mcpServers)
  - Codex CLI    -> ~/.codex/config.toml       (mcp_servers)
  - Gemini CLI   -> ~/.gemini/settings.json   (mcpServers)

Usage:
    argus setup                 # configure all detected agents
    argus setup --agent cursor  # only Cursor
    argus setup --dry-run       # preview without writing
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

SERVER_COMMAND = [sys.executable, "-m", "argus.mcp_server"]


def _json_target(path: Path) -> Tuple[Path, Dict[str, Any]]:
    data: Dict[str, Any] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except Exception:
            data = {}
    servers = data.setdefault("mcpServers", {})
    servers["argus"] = {"command": SERVER_COMMAND[0], "args": SERVER_COMMAND[1:]}
    return path, data


def _toml_target(path: Path) -> Tuple[Path, str]:
    block = ('\n[mcp_servers.argus]\n'
             f'command = "{SERVER_COMMAND[0]}"\n'
             f'args = {json.dumps(SERVER_COMMAND[1:])}\n')
    existing = path.read_text() if path.exists() else ""
    if "[mcp_servers.argus]" in existing:
        return path, existing  # already configured
    return path, existing.rstrip("\n") + "\n" + block


AGENTS: Dict[str, Any] = {
    "claude": ("Claude Code", lambda: _json_target(
        Path.home() / ".claude.json")),
    "cursor": ("Cursor", lambda: _json_target(
        Path.home() / ".cursor" / "mcp.json")),
    "gemini": ("Gemini CLI", lambda: _json_target(
        Path.home() / ".gemini" / "settings.json")),
    "codex": ("Codex CLI", lambda: _toml_target(
        Path.home() / ".codex" / "config.toml")),
}


def plan(agent: str | None = None) -> List[Tuple[str, str, Path, Any]]:
    """Return [(agent_key, label, path, new_content)] without writing."""
    out = []
    for key, (label, fn) in AGENTS.items():
        if agent and key != agent:
            continue
        path, content = fn()
        out.append((key, label, path, content))
    return out


def apply(items: List[Tuple[str, str, Path, Any]], dry_run: bool = False
          ) -> List[str]:
    done = []
    for key, label, path, content in items:
        if isinstance(content, dict):
            text = json.dumps(content, indent=2)
        else:
            text = content
        if dry_run:
            done.append(f"[dry-run] {label}: would write {path}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + ("\n" if not text.endswith("\n") else ""))
        done.append(f"{label}: configured -> {path}")
    return done
