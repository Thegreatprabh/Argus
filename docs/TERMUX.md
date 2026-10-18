# ARGUS on Termux 📱

Run the full platform in your pocket. No root needed for static analysis.

## Install
```bash
pkg update && pkg install python radare2 binwalk
pip install git+https://github.com/Thegreatprabh/argus
```

## What works
| Feature | Termux | Notes |
|---|---|---|
| 🌐 web.analyze | ✅ | pure Python |
| 📦 apk.overview | ✅ | zip-parse, no apktool needed |
| ⚙️ binary.info | ✅ | via `pkg install radare2` |
| 🔍 firmware.scan | ✅ | via `pkg install binwalk` |
| 🔬 frida | ⚠️ | works for your own debuggable apps |
| 🖥️ dashboard | ✅ | `argus dashboard`, open in browser |

## Why ARGUS beats desktop-only tools here
Ghidra/IDA/Hopper need a desktop OS (and some are paid). ARGUS is
**radare2-first and dependency-light** — the whole platform runs on a phone.

## Agent setup on Termux
```bash
argus setup --agent gemini --dry-run   # preview
argus setup --agent gemini             # write config
```
Then restart Gemini CLI / your agent.
