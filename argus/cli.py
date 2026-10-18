"""ARGUS CLI: team-grade command line interface."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .engines.binary import BinaryEngine
from .engines.dynamic import DynamicEngine
from .engines.firmware import FirmwareEngine
from .engines.mobile import MobileEngine
from .engines.rebuild import RebuildEngine
from .engines.web import WebEngine
from .mcp_server import _REGISTRY


def _emit(obj: dict) -> None:
    json.dump(obj, sys.stdout, indent=2)
    sys.stdout.write("\n")


def cmd_scan_web(args: argparse.Namespace) -> int:
    _emit(WebEngine().analyze(args.url, deep=args.deep).to_dict())
    return 0


def cmd_binary(args: argparse.Namespace) -> int:
    eng = BinaryEngine()
    if not eng.available():
        print(eng.missing_hint(), file=sys.stderr)
        return 2
    _emit(eng.analyze(args.path).to_dict())
    return 0


def cmd_apk(args: argparse.Namespace) -> int:
    _emit(MobileEngine().analyze(args.path).to_dict())
    return 0


def cmd_ps(_: argparse.Namespace) -> int:
    eng = DynamicEngine()
    if not eng.available():
        print(eng.missing_hint(), file=sys.stderr)
        return 2
    _emit(eng.analyze("local", mode="ps").to_dict())
    return 0


def cmd_firmware(args: argparse.Namespace) -> int:
    eng = FirmwareEngine()
    if not eng.available():
        print(eng.missing_hint(), file=sys.stderr)
        return 2
    _emit(eng.analyze(args.path).to_dict())
    return 0


def cmd_rebuild(args: argparse.Namespace) -> int:
    eng = RebuildEngine()
    bp = (eng.blueprint_apk(args.target)
          if args.target.lower().endswith(".apk")
          else eng.blueprint_web(args.target))
    files = eng.generate(bp, args.outdir, args.project)
    _emit({"project": args.project, "outdir": args.outdir,
           "files": files, "blueprint_kind": bp.get("kind")})
    print(f"\n[{len(files)} files] scaffold ready in {args.outdir}/", file=sys.stderr)
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    from .setup_agents import apply, plan
    items = plan(args.agent)
    for line in apply(items, dry_run=args.dry_run):
        print(line)
    if not args.dry_run:
        print("\nRestart your agent to load the argus MCP server.", file=sys.stderr)
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    from .dashboard import run
    run(port=args.port, open_browser=not args.no_browser)
    return 0


def cmd_tools(_: argparse.Namespace) -> int:
    for name, t in _REGISTRY.items():
        print(f"{name:18s} {t['description']}")
    return 0


def cmd_serve(_: argparse.Namespace) -> int:
    from .mcp_server import serve
    serve()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="argus",
        description="ARGUS — AI-agent reverse engineering platform.")
    p.add_argument("--version", action="version", version=f"argus {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan-web", help="X-ray a website")
    s.add_argument("url")
    s.add_argument("--deep", action="store_true",
                   help="also fetch first-party JS and extract API endpoints")
    s.set_defaults(fn=cmd_scan_web)

    b = sub.add_parser("binary", help="static analysis of an executable")
    b.add_argument("path")
    b.set_defaults(fn=cmd_binary)

    a = sub.add_parser("apk", help="Android APK overview")
    a.add_argument("path")
    a.set_defaults(fn=cmd_apk)

    ps = sub.add_parser("ps", help="list processes (Frida targets)")
    ps.set_defaults(fn=cmd_ps)

    fw = sub.add_parser("firmware", help="firmware image analysis (Binwalk)")
    fw.add_argument("path")
    fw.set_defaults(fn=cmd_firmware)

    rb = sub.add_parser("rebuild", help="blueprint -> starter codebase")
    rb.add_argument("target", help="URL or APK path")
    rb.add_argument("-o", "--outdir", default="rebuild-out")
    rb.add_argument("--project", default="my-rebuild")
    rb.set_defaults(fn=cmd_rebuild)

    su = sub.add_parser("setup", help="connect AI agents (MCP) in one command")
    su.add_argument("--agent", choices=["claude", "cursor", "codex", "gemini"])
    su.add_argument("--dry-run", action="store_true")
    su.set_defaults(fn=cmd_setup)

    db = sub.add_parser("dashboard", help="launch web dashboard UI")
    db.add_argument("--port", type=int, default=8765)
    db.add_argument("--no-browser", action="store_true")
    db.set_defaults(fn=cmd_dashboard)

    t = sub.add_parser("tools", help="list MCP tools")
    t.set_defaults(fn=cmd_tools)

    sv = sub.add_parser("serve", help="run MCP server on stdio")
    sv.set_defaults(fn=cmd_serve)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
