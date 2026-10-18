# Contributing to ARGUS 👁️

## Setup
```bash
git clone https://github.com/Thegreatprabh/argus
cd argus
pip install -e ".[dev]"
```

Termux:
```bash
pkg install python radare2 binwalk
pip install argus
```

## Adding an engine
1. Create `argus/engines/<name>.py` subclassing `Engine` (see `base.py`).
2. Implement `available()` (backend check) and `analyze()`.
3. Wire it: `cli.py` subcommand + `mcp_server.py` `@tool` + README table.
4. Add offline tests under `tests/`.

## Rules
- Core stays dependency-light (Termux-first).
- Every finding carries evidence. No invented behavior.
- No cracking / DRM / paywall bypass features — PRs adding them are rejected.
- Update `docs/ARCHITECTURE.md` if you change the design.

## Release checklist
- [ ] `pytest tests/` green
- [ ] `python -m argus tools` lists new tools
- [ ] README comparison table still honest
- [ ] version bump in `pyproject.toml` + `argus/__init__.py`
