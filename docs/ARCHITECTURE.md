# ARGUS Architecture

```
                    +------------------+
                    |   AI Agent       |
                    | (Claude/Cursor/  |
                    |  Codex/...)       |
                    +--------+---------+
                             | MCP (JSON-RPC stdio)
                    +--------v---------+
                    |  mcp_server.py   |  tool registry + schemas
                    +--------+---------+
                             |
        +--------------------+--------------------+
        |                    |                    |
 +------v------+    +--------v-------+   +--------v-------+
 | web engine  |    | binary engine  |   | mobile engine  |   ...
 | (pure       |    | (radare2)      |   | (apktool/zip)  |
 |  Python)    |    |                |   |                |
 +-------------+    +----------------+   +----------------+
        +------v------+
        | dynamic     |  Frida — runtime inspection
        | engine      |  (REA does NOT wrap Frida or radare2)
        +-------------+
```

## Design principles
1. **Engines are dumb, agents are smart.** Engines return evidence-backed
   findings; the agent reasons over them (see `argus/workflows/`).
2. **Graceful degradation.** Every engine reports `available()`; missing
   backends produce a clear install hint, never a crash.
3. **Evidence or it didn't happen.** Every `Finding` carries the raw
   evidence string. Workflows must cite findings, never invent behavior.
4. **Local-first.** Analysis runs on the user's machine. Nothing is uploaded.

## Where ARGUS beats the viral REA (honest)
- **Dynamic analysis**: REA wraps static tools only; ARGUS wraps Frida —
  see what code *does* at runtime, not just what it *says*.
- **radare2**: REA doesn't wrap it; ARGUS does (free, scriptable).
- **Web depth**: dedicated JS/API/tracker pipeline instead of a thin
  Chrome wrapper.
- **Patch-diff workflow**: version-to-version deltas as a first-class
  investigation.

## Non-goals
- We do not build decompilers; we orchestrate the best free ones.
- No cracks, keygens, license bypasses, or DRM circumvention — analysis
  and clean-room reimplementation only.
