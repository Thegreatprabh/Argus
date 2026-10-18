"""ARGUS dashboard: `argus dashboard` -> http://localhost:8765

Self-contained web UI (zero dependencies, stdlib http.server).
Dark hacker theme. Scan a target, watch the blueprint build live.
"""

from __future__ import annotations

import html
import json
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from .engines.rebuild import RebuildEngine

PORT = 8765

PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<title>ARGUS // dashboard</title>
<style>
:root{--bg:#0a0e14;--panel:#11161f;--grn:#00ff41;--pur:#b366ff;--txt:#c9d4e3;--dim:#5b6b82}
*{box-sizing:border-box}body{background:var(--bg);color:var(--txt);font-family:ui-monospace,Menlo,Consolas,monospace;margin:0;padding:0}
header{border-bottom:1px solid #1d2635;padding:18px 28px;display:flex;align-items:center;gap:14px}
header .eye{font-size:28px}header h1{margin:0;font-size:20px;letter-spacing:3px;color:var(--grn);text-shadow:0 0 12px #00ff4133}
header small{color:var(--dim);letter-spacing:1px}
main{max-width:980px;margin:0 auto;padding:28px}
.scan{display:flex;gap:10px;margin-bottom:8px}
.scan input{flex:1;background:var(--panel);border:1px solid #1d2635;color:var(--txt);padding:12px 14px;border-radius:6px;font:inherit}
.scan input:focus{outline:none;border-color:var(--grn)}
.scan button{background:var(--grn);color:#04140a;border:none;padding:12px 26px;border-radius:6px;font:inherit;font-weight:700;cursor:pointer}
.scan button:hover{filter:brightness(1.1)}
.hint{color:var(--dim);font-size:12px;margin-bottom:26px}
#out .card{background:var(--panel);border:1px solid #1d2635;border-radius:8px;padding:16px 18px;margin-bottom:14px}
#out .card h3{margin:0 0 8px;color:var(--pur);font-size:14px;letter-spacing:1px}
#out .sev{float:right;font-size:11px;padding:2px 8px;border-radius:10px;background:#1d2635;color:var(--dim)}
#out pre{white-space:pre-wrap;font-size:12px;color:var(--txt);margin:8px 0 0}
#out .ev{color:var(--dim);font-size:12px}
.log{color:var(--grn);font-size:13px;min-height:24px;margin-bottom:14px}
.log .blink{animation:bl 1s steps(1) infinite}@keyframes bl{50%{opacity:0}}
.badge{display:inline-block;background:#1d2635;border:1px solid #2a3a52;border-radius:4px;padding:2px 8px;font-size:11px;margin:2px 4px 2px 0;color:var(--txt)}
footer{text-align:center;color:var(--dim);font-size:11px;padding:30px;letter-spacing:2px}
</style></head><body>
<header><span class="eye">👁️</span><h1>ARGUS</h1><small>REVERSE-ENGINEER ANYTHING → REBUILD EVERYTHING</small></header>
<main>
<div class="scan"><input id="t" placeholder="https://example.com  or  /path/app.apk"><button onclick="go()">X-RAY ▸</button></div>
<div class="hint">web • apk • binary • firmware &nbsp;—&nbsp; evidence-backed findings, zero uploads, runs local</div>
<div class="log" id="log"></div>
<div id="out"></div>
</main>
<footer>A R G U S &nbsp;//&nbsp; MIT &nbsp;//&nbsp; LOCAL-FIRST</footer>
<script>
const log=document.getElementById('log'),out=document.getElementById('out');
function go(){
 const t=document.getElementById('t').value.trim();if(!t)return;
 out.innerHTML='';log.innerHTML='[●] scanning <b>'+t+'</b> <span class="blink">▊</span>';
 fetch('/api/scan?target='+encodeURIComponent(t)).then(r=>r.json()).then(d=>{
  log.innerHTML='[✓] scan complete — '+d.findings.length+' findings';
  out.innerHTML=d.findings.map(f=>
   '<div class="card"><span class="sev">'+f.severity+'</span><h3>'+esc(f.title)+'</h3>'+
   '<div class="ev">'+esc(f.evidence).slice(0,900)+'</div></div>').join('')
   ||'<div class="card"><h3>no findings</h3><div class="ev">target unreachable or engine unavailable — see warnings</div></div>';
 }).catch(e=>{log.innerHTML='[✗] '+e});
}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
</script></body></html>
"""


class _Handler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, ctype: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/scan":
            target = urllib.parse.parse_qs(parsed.query).get("target", [""])[0]
            eng = RebuildEngine()
            try:
                if target.lower().endswith(".apk"):
                    bp = eng.blueprint_apk(target)
                else:
                    bp = eng.blueprint_web(target)
                findings = bp.get("findings", [])
            except Exception as exc:  # dashboard never crashes on a bad target
                findings = [{"title": "scan failed", "evidence": str(exc),
                             "severity": "high", "meta": {}}]
            self._send(json.dumps({"findings": findings}).encode(),
                       "application/json")
            return
        self._send(PAGE.encode(), "text/html; charset=utf-8")

    def log_message(self, *args: object) -> None:  # quiet
        pass


def run(port: int = PORT, open_browser: bool = True) -> None:
    srv = HTTPServer(("127.0.0.1", port), _Handler)
    url = f"http://localhost:{port}"
    print(f"ARGUS dashboard -> {url}")
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
