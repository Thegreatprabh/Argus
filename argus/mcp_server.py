"""ARGUS MCP server: exposes every engine as tools over JSON-RPC stdio.

Speaks the MCP stdio transport (JSON-RPC 2.0):
  initialize -> { protocolVersion, serverInfo }
  tools/list -> every registered engine tool + schema
  tools/call -> run a tool, get evidence-backed findings

Wire it into any MCP-capable agent (Claude Code, Cursor, ...):

    { "mcpServers": { "argus": {
        "command": "python", "args": ["-m", "argus.mcp_server"] } } }
"""

from __future__ import annotations

import inspect
import json
import sys
from typing import Any, Callable, Dict, List

from . import __version__
from .engines.binary import BinaryEngine
from .engines.dynamic import DynamicEngine
from .engines.firmware import FirmwareEngine
from .engines.mobile import MobileEngine
from .engines.rebuild import RebuildEngine
from .engines.web import WebEngine

ToolFn = Callable[..., Dict[str, Any]]
_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: str, description: str):
    def deco(fn: ToolFn) -> ToolFn:
        sig = inspect.signature(fn)
        props: Dict[str, Any] = {}
        required: List[str] = []
        for pname, param in sig.parameters.items():
            props[pname] = {"type": "string",
                            "description": f"argument `{pname}`"}
            if param.default is inspect.Parameter.empty:
                required.append(pname)
        _REGISTRY[name] = {
            "fn": fn,
            "description": description,
            "inputSchema": {"type": "object", "properties": props,
                            "required": required},
        }
        return fn
    return deco


@tool("web.analyze", "X-ray a website: tech stack, JS bundles, API endpoints, trackers, forms.")
def t_web_analyze(url: str) -> Dict[str, Any]:
    return WebEngine().analyze(url, deep=True).to_dict()


@tool("binary.info", "Static analysis of an executable (radare2): headers, strings, symbols.")
def t_binary_info(path: str) -> Dict[str, Any]:
    return BinaryEngine().analyze(path).to_dict()


@tool("apk.overview", "Android APK overview: permissions, embedded SDKs, hardcoded URLs.")
def t_apk_overview(path: str) -> Dict[str, Any]:
    return MobileEngine().analyze(path).to_dict()


@tool("frida.ps", "List local processes for dynamic instrumentation targets.")
def t_frida_ps() -> Dict[str, Any]:
    return DynamicEngine().analyze("local", mode="ps").to_dict()


@tool("firmware.scan", "Firmware image analysis (Binwalk): embedded filesystems, kernels, bootloaders.")
def t_firmware_scan(path: str) -> Dict[str, Any]:
    return FirmwareEngine().analyze(path).to_dict()


@tool("rebuild.scaffold", "Blueprint -> starter codebase: generate a clean-room rebuild scaffold from a URL or APK.")
def t_rebuild_scaffold(target: str) -> Dict[str, Any]:
    return RebuildEngine().analyze(
        target, outdir="rebuild-out", project="my-rebuild").to_dict()


@tool("auto.rebuild", "ONE-SHOT: give a website URL or APK path, get the full reverse-engineer + rebuild pipeline in a single call. Returns blueprint summary + generated scaffold file list.")
def t_auto_rebuild(target: str) -> Dict[str, Any]:
    eng = RebuildEngine()
    bp = (eng.blueprint_apk(target) if target.lower().endswith(".apk")
          else eng.blueprint_web(target))
    files = eng.generate(bp, "rebuild-out", "my-rebuild")
    return {"target": target,
            "blueprint_kind": bp.get("kind"),
            "tech": bp.get("tech", []),
            "pages": len(bp.get("pages", [])),
            "endpoints": len(bp.get("endpoints", [])) or len(bp.get("urls", [])),
            "files_generated": files,
            "outdir": "rebuild-out"}


def _handle(msg: Dict[str, Any]) -> Dict[str, Any] | None:
    method = msg.get("method", "")
    mid = msg.get("id")
    params = msg.get("params", {}) or {}

    def ok(result: Any) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    if method == "initialize":
        return ok({"protocolVersion": "2024-11-05",
                   "serverInfo": {"name": "argus", "version": __version__},
                   "capabilities": {"tools": {}}})
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return ok({"tools": [
            {"name": n, "description": t["description"],
             "inputSchema": t["inputSchema"]}
            for n, t in _REGISTRY.items()]})
    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {}) or {}
        entry = _REGISTRY.get(name)
        if not entry:
            return ok({"content": [{"type": "text",
                                    "text": f"unknown tool: {name}"}],
                       "isError": True})
        try:
            out = entry["fn"](**args)
            text = json.dumps(out, indent=2)[:20000]
        except Exception as exc:  # never crash the agent loop
            text = json.dumps({"error": str(exc)})
            return ok({"content": [{"type": "text", "text": text}],
                       "isError": True})
        return ok({"content": [{"type": "text", "text": text}]})
    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"unknown method {method}"}}


def serve() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    serve()
