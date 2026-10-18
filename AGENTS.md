# AGENTS.md — how AI agents work in this repo

> Read this before modifying ARGUS. It keeps every agent's changes consistent.

## What ARGUS is
An AI-agent reverse engineering platform: engines produce **evidence-backed
findings**, agents reason over them. See `docs/ARCHITECTURE.md`.

## Layout
- `argus/engines/` — analysis backends. Each engine subclasses
  `engines/base.py::Engine` (`available()`, `analyze()` -> `EngineResult`).
  New engine? Add file + wire into `cli.py`, `mcp_server.py`, README table.
- `argus/mcp_server.py` — tool registry. New tool = `@tool("name.desc", "...")`
  on a function. Keep the JSON-RPC stdio loop untouched.
- `argus/cli.py` — argparse subcommands. One function per command.
- `argus/workflows/*.md` — investigation playbooks agents follow.
- `argus/dashboard.py` — self-contained web UI (stdlib only, no new deps).
- `tests/` — offline unit tests (no network). Run: `python -m pytest tests/`

## Rules
1. **Evidence or it didn't happen.** Every `Finding` needs the `evidence`
   string. Never invent endpoints/functions/behavior.
2. **Graceful degradation.** Missing backends -> `warnings` + install hint,
   never a crash.
3. **Stdlib + requests only** in core. Termux must stay `pip install`-able.
   Heavy/optional deps go in `[project.optional-dependencies]`.
4. **No cracks/keygens/DRM bypasses.** Analysis + clean-room rebuild only.
5. Keep the hacker README theme (dark + neon). Update the REA comparison
   table honestly when features change.

## Quick checks
```bash
python -m pytest tests/ -q
python -m argus tools
python - <<'EOF'
from argus.engines.web import analyze_website
print(analyze_website("https://example.com")["findings"][0]["title"])
EOF
```
