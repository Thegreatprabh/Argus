"""`argus doctor` — diagnose MCP connection problems.

Checks, in order:
  1. python executable + version
  2. argus importable + version
  3. MCP server handshake (initialize -> tools/list) via subprocess
  4. prints the EXACT command/args to paste into Codex/Claude/Cursor settings

Run on the machine where the AI agent lives:
    argus doctor
"""

from __future__ import annotations

import json
import subprocess
import sys


def _check_handshake() -> tuple[bool, str]:
    """Spawn the MCP server exactly like an agent would, run handshake."""
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "argus.mcp_server"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True)
    except Exception as exc:
        return False, f"could not spawn server: {exc}"
    try:
        init = json.dumps({"jsonrpc": "2.0", "id": 1,
                           "method": "initialize", "params": {}})
        proc.stdin.write(init + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        resp = json.loads(line)
        assert resp.get("result", {}).get("serverInfo", {}).get("name") == "argus"

        lst = json.dumps({"jsonrpc": "2.0", "id": 2,
                          "method": "tools/list", "params": {}})
        proc.stdin.write(lst + "\n")
        proc.stdin.flush()
        tools = json.loads(proc.stdout.readline())
        names = [t["name"] for t in tools["result"]["tools"]]
    except Exception as exc:
        err = proc.stderr.read()[:500] if proc.stderr else ""
        proc.kill()
        return False, f"handshake failed: {exc}\nstderr: {err}"
    proc.kill()
    return True, f"{len(names)} tools OK ({', '.join(names[:4])}...)"


def run() -> int:
    print("== ARGUS doctor ==\n")
    print(f"[1] python : {sys.executable}")
    print(f"    version: {sys.version.split()[0]}")

    try:
        import argus  # noqa
        from argus import __version__
        print(f"[2] argus  : import OK (v{__version__})")
    except Exception as exc:
        print(f"[2] argus  : IMPORT FAILED: {exc}")
        print("    fix: pip install git+https://github.com/Thegreatprabh/argus")
        return 1

    ok, msg = _check_handshake()
    print(f"[3] MCP handshake: {'OK' if ok else 'FAILED'}")
    print(f"    {msg}")
    if not ok:
        return 1

    print("\n== paste this into your agent's MCP settings (STDIO) ==")
    print(f"    command: {sys.executable}")
    print('    args   : ["-m", "argus.mcp_server"]')
    print("\nor this TOML (~/.codex/config.toml):")
    print('    [mcp_servers.argus]')
    print(f'    command = "{sys.executable}"')
    print('    args = ["-m", "argus.mcp_server"]')
    print("\nThen RESTART the agent app completely and type /mcp in the composer.")
    return 0
