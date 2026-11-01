"""Web UI (standard library only):  python web.py  ->  http://localhost:8000"""
import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer

from rag.agent import Assistant

bot = Assistant()

PAGE = """<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>مساعد دليل الطالب</title>
<style>
body{font-family:system-ui,Tahoma,sans-serif;max-width:640px;margin:0 auto;padding:16px;background:#f6f7f9;color:#1c1c1e}
h1{font-size:20px}#log{display:flex;flex-direction:column;gap:10px;margin-bottom:12px}
.m{padding:10px 14px;border-radius:14px;max-width:85%;line-height:1.6;white-space:pre-wrap}
.u{background:#1f6feb;color:#fff;align-self:flex-start}.b{background:#fff;border:1px solid #dde;align-self:flex-end}
.s{font-size:12px;color:#667;margin-top:6px}form{display:flex;gap:8px;position:sticky;bottom:12px}
input{flex:1;padding:12px;border:1px solid #ccd;border-radius:12px;font-size:16px}
button{padding:0 18px;border:0;border-radius:12px;background:#1f6feb;color:#fff;font-size:16px;cursor:pointer}
.chips button{background:#e8eefc;color:#1f6feb;font-size:13px;padding:6px 10px;margin:2px}
</style></head><body><h1>🎓 مساعد دليل الطالب</h1>
<div class="chips" id="chips"></div><div id="log"></div>
<form id="f"><input id="q" placeholder="اكتب سؤالك..." autocomplete="off" autofocus><button>إرسال</button></form>
<script>
const log=document.getElementById('log'),q=document.getElementById('q');
function add(t,c,s){const d=document.createElement('div');d.className='m '+c;d.textContent=t;
 if(s){const e=document.createElement('div');e.className='s';e.textContent='📚 '+s;d.appendChild(e)}
 log.appendChild(d);d.scrollIntoView()}
async function ask(t){add(t,'u');const r=await fetch('/ask',{method:'POST',body:JSON.stringify({q:t})});
 const a=await r.json();add(a.text,'b',a.sources.join(' | '))}
document.getElementById('f').onsubmit=e=>{e.preventDefault();if(q.value.trim()){ask(q.value);q.value=''}};
['كم نسبة الغياب المسموحة؟','كم سعر الساعة؟','احسب معدلي A:3, B+:3, C:2','رسوم 15 ساعة كم؟']
 .forEach(t=>{const b=document.createElement('button');b.textContent=t;b.onclick=()=>ask(t);chips.appendChild(b)});
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200, PAGE, "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/ask":
            return self._send(404, "{}", "application/json")
        try:
            n = int(self.headers.get("Content-Length", 0))
            q = json.loads(self.rfile.read(n))["q"]
            a = bot.ask(str(q)[:500])
            body = json.dumps(asdict(a), ensure_ascii=False)
            self._send(200, body, "application/json; charset=utf-8")
        except Exception:
            self._send(400, '{"error":"bad request"}', "application/json")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("http://localhost:8000")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
