"""ARGUS dashboard v2: `argus dashboard` -> http://localhost:8765

Self-contained web UI (zero dependencies, stdlib http.server).
Animated hacker theme: risk gauge, secrets cards, one-click rebuild.
"""

from __future__ import annotations

import json
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from .engines.mobile import MobileEngine
from .engines.rebuild import RebuildEngine
from .engines.secrets import SecretsEngine
from .engines.web import WebEngine

PORT = 8765


def _scan(target: str) -> dict:
    eng = RebuildEngine()
    try:
        if target.lower().endswith(".apk"):
            bp = eng.blueprint_apk(target)
            findings = bp.get("findings", [])
            risk = next((f["meta"].get("risk_score")
                         for f in findings if "risk_score" in f.get("meta", {})),
                        None)
            label = next((f["meta"].get("risk_label", "")
                          for f in findings if "risk_label" in f.get("meta", {})),
                         "")
        else:
            bp = eng.blueprint_web(target)
            findings = bp.get("findings", [])
            risk, label = None, ""
        sec = SecretsEngine().analyze(target).to_dict()
        secrets = [f for f in sec["findings"] if f["title"].startswith("⚠️")]
        tech = bp.get("tech", [])
        return {"ok": True, "findings": findings, "secrets": secrets,
                "tech": tech, "risk": risk, "risk_label": label,
                "kind": bp.get("kind")}
    except Exception as exc:  # dashboard never crashes on a bad target
        return {"ok": False, "error": str(exc)}


def _rebuild(target: str) -> dict:
    eng = RebuildEngine()
    bp = (eng.blueprint_apk(target) if target.lower().endswith(".apk")
          else eng.blueprint_web(target))
    files = eng.generate(bp, "rebuild-out", "dashboard-rebuild")
    return {"ok": True, "files": files, "outdir": "rebuild-out"}


PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<title>ARGUS // dashboard</title>
<style>
:root{--bg:#0a0e14;--panel:#11161f;--grn:#00ff41;--pur:#b366ff;--red:#ff3b5c;--txt:#c9d4e3;--dim:#5b6b82;--amber:#ffb020}
*{box-sizing:border-box}body{background:var(--bg);color:var(--txt);font-family:ui-monospace,Menlo,Consolas,monospace;margin:0}
header{border-bottom:1px solid #1d2635;padding:16px 28px;display:flex;align-items:center;gap:14px;position:relative;overflow:hidden}
header::after{content:"";position:absolute;left:0;right:0;height:40px;top:-40px;background:linear-gradient(#00ff4122,transparent);animation:scan 4s linear infinite}
@keyframes scan{to{transform:translateY(160px)}}
header .eye{font-size:30px;animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{50%{transform:scale(1.12)}}
header h1{margin:0;font-size:22px;letter-spacing:4px;color:var(--grn);text-shadow:0 0 14px #00ff4144}
header small{color:var(--dim);letter-spacing:1px}
main{max-width:1020px;margin:0 auto;padding:26px}
.scan{display:flex;gap:10px}
.scan input{flex:1;background:var(--panel);border:1px solid #1d2635;color:var(--txt);padding:13px 15px;border-radius:6px;font:inherit}
.scan input:focus{outline:none;border-color:var(--grn);box-shadow:0 0 0 2px #00ff4133}
.btn{background:var(--grn);color:#04140a;border:none;padding:13px 26px;border-radius:6px;font:inherit;font-weight:700;cursor:pointer}
.btn:hover{filter:brightness(1.12)}
.btn.pur{background:var(--pur);color:#12041f}
.btn:disabled{opacity:.5;cursor:wait}
.hint{color:var(--dim);font-size:12px;margin:8px 0 24px}
.log{color:var(--grn);font-size:13px;min-height:26px;margin-bottom:14px}
.log .blink{animation:bl 1s steps(1) infinite}@keyframes bl{50%{opacity:0}}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:700px){.grid{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid #1d2635;border-radius:8px;padding:16px 18px;margin-bottom:14px;animation:rise .35s ease-out}
@keyframes rise{from{opacity:0;transform:translateY(8px)}}
.card h3{margin:0 0 8px;color:var(--pur);font-size:14px;letter-spacing:1px}
.card.danger{border-color:#ff3b5c66}.card.danger h3{color:var(--red)}
.sev{float:right;font-size:11px;padding:2px 9px;border-radius:10px;background:#1d2635;color:var(--dim)}
.sev.high{background:#ff3b5c22;color:var(--red)}.sev.medium{background:#ffb02022;color:var(--amber)}
.ev{color:var(--dim);font-size:12px;white-space:pre-wrap}
.badge{display:inline-block;background:#1d2635;border:1px solid #2a3a52;border-radius:4px;padding:3px 9px;font-size:11px;margin:2px 4px 2px 0}
.gauge{text-align:center;padding:8px}
.gauge .num{font-size:34px;font-weight:700}
.rebuildbox{margin-top:6px}
footer{text-align:center;color:var(--dim);font-size:11px;padding:30px;letter-spacing:2px}
</style></head><body>
<header><span class="eye">👁️</span><h1>ARGUS</h1><small>REVERSE-ENGINEER ANYTHING → REBUILD EVERYTHING</small></header>
<main>
<div class="scan"><input id="t" placeholder="https://example.com  or  /path/app.apk"><button class="btn" id="go" onclick="go()">X-RAY ▸</button></div>
<div class="hint">🌐 web &nbsp; 📦 apk &nbsp; ⚙️ binary &nbsp; 🔍 firmware &nbsp; 🔬 frida &nbsp;—&nbsp; local-first, nothing uploaded</div>
<div class="log" id="log"></div>
<div id="out"></div>
</main>
<footer>A R G U S &nbsp;//&nbsp; MIT &nbsp;//&nbsp; v0.2</footer>
<script>
const log=document.getElementById('log'),out=document.getElementById('out'),goBtn=document.getElementById('go');
let lastTarget='';
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function go(){
 const t=document.getElementById('t').value.trim();if(!t)return;lastTarget=t;
 goBtn.disabled=true;out.innerHTML='';
 log.innerHTML='[●] x-raying <b>'+esc(t)+'</b> <span class="blink">▊</span>';
 fetch('/api/scan?target='+encodeURIComponent(t)).then(r=>r.json()).then(d=>{
  goBtn.disabled=false;
  if(!d.ok){log.innerHTML='[✗] '+esc(d.error);return}
  log.innerHTML='[✓] scan complete — '+d.findings.length+' findings'+(d.secrets.length?', <b style="color:#ff3b5c">'+d.secrets.length+' secrets exposed</b>':'');
  let h='';
  if(d.risk!==null&&d.risk!==undefined){
   const col=d.risk>60?'#ff3b5c':d.risk>30?'#ffb020':'#00ff41';
   const arc=(d.risk/100*180).toFixed(1);
   h+='<div class="card"><h3>RISK SCORE</h3><div class="gauge"><svg width="220" height="120" viewBox="0 0 220 120"><path d="M20 105 A90 90 0 0 1 200 105" fill="none" stroke="#1d2635" stroke-width="14" stroke-linecap="round"/><path d="M20 105 A90 90 0 0 1 200 105" fill="none" stroke="'+col+'" stroke-width="14" stroke-linecap="round" stroke-dasharray="'+(d.risk*2.82).toFixed(0)+' 300"><animate attributeName="stroke-dasharray" from="0 300" to="'+(d.risk*2.82).toFixed(0)+' 300" dur="1s" fill="freeze"/></path></svg><div class="num" style="color:'+col+'">'+d.risk+'<span style="font-size:16px;color:#5b6b82">/100</span></div><div style="color:'+col+';letter-spacing:2px">'+esc(d.risk_label.toUpperCase())+'</div></div></div>';
  }
  if(d.tech&&d.tech.length)h+='<div class="card"><h3>TECH STACK</h3>'+d.tech.map(x=>'<span class="badge">'+esc(x)+'</span>').join('')+'</div>';
  h+=d.secrets.map(f=>'<div class="card danger"><span class="sev high">'+f.severity+'</span><h3>'+esc(f.title)+'</h3><div class="ev">'+esc(f.evidence).slice(0,300)+'</div></div>').join('');
  h+=d.findings.filter(f=>!f.meta||!f.meta.risk_score).map(f=>'<div class="card"><span class="sev '+f.severity+'">'+f.severity+'</span><h3>'+esc(f.title)+'</h3><div class="ev">'+esc(f.evidence).slice(0,700)+'</div></div>').join('');
  h+='<div class="card rebuildbox"><h3>🏗️ REBUILD</h3><div class="ev">Generate a clean-room starter codebase from this blueprint.</div><br><button class="btn pur" onclick="rebuild()">GENERATE REBUILD ▸</button><div id="rbout" style="margin-top:10px"></div></div>';
  out.innerHTML=h;
 }).catch(e=>{goBtn.disabled=false;log.innerHTML='[✗] '+e});
}
function rebuild(){
 const o=document.getElementById('rbout');o.innerHTML='<span class="blink" style="color:#b366ff">building…</span>';
 fetch('/api/rebuild?target='+encodeURIComponent(lastTarget)).then(r=>r.json()).then(d=>{
  o.innerHTML=d.ok?'<div class="ev">[✓] '+d.files.length+' files → <b>'+esc(d.outdir)+'/</b><br>'+d.files.slice(0,8).map(esc).join('<br>')+(d.files.length>8?'<br>…':'')+'</div>':'[✗] '+esc(d.error);
 });
}
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
        qs = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/api/scan":
            self._send(json.dumps(_scan(qs.get("target", [""])[0])).encode(),
                       "application/json")
            return
        if parsed.path == "/api/rebuild":
            try:
                self._send(json.dumps(
                    _rebuild(qs.get("target", [""])[0])).encode(),
                    "application/json")
            except Exception as exc:
                self._send(json.dumps({"ok": False,
                                       "error": str(exc)}).encode(),
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
