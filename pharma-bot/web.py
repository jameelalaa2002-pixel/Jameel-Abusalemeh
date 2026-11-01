"""Web UI (standard library only):  python web.py  ->  http://localhost:8000"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from bot.engine import PharmaBot

bot = PharmaBot()

PAGE = """<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>مساعد الصيدلية</title>
<style>
body{font-family:system-ui,Tahoma,sans-serif;max-width:640px;margin:0 auto;padding:16px;background:#f3f8f6;color:#1c1c1e}
h1{font-size:20px}#log{display:flex;flex-direction:column;gap:10px;margin-bottom:12px}
.m{padding:10px 14px;border-radius:14px;max-width:88%;line-height:1.7;white-space:pre-wrap}
.u{background:#0f9d73;color:#fff;align-self:flex-start}.b{background:#fff;border:1px solid #d5e4de;align-self:flex-end}
form{display:flex;gap:8px;position:sticky;bottom:12px}
input{flex:1;padding:12px;border:1px solid #bcd;border-radius:12px;font-size:16px}
button{padding:0 18px;border:0;border-radius:12px;background:#0f9d73;color:#fff;font-size:16px;cursor:pointer}
.chips button{background:#dff3ec;color:#0b7a59;font-size:13px;padding:6px 10px;margin:2px}
</style></head><body><h1>💊 مساعد الصيدلية</h1>
<div class="chips" id="chips"></div><div id="log"></div>
<form id="f"><input id="q" placeholder="اكتب سؤالك..." autocomplete="off" autofocus><button>إرسال</button></form>
<script>
const log=document.getElementById('log'),q=document.getElementById('q');
function add(t,c){const d=document.createElement('div');d.className='m '+c;d.textContent=t;log.appendChild(d);d.scrollIntoView()}
async function ask(t){add(t,'u');const r=await fetch('/ask',{method:'POST',body:JSON.stringify({q:t})});add((await r.json()).text,'b')}
document.getElementById('f').onsubmit=e=>{e.preventDefault();if(q.value.trim()){ask(q.value);q.value=''}};
['هل بانادول متوفر؟','أي صيدلية مفتوحة هلأ؟','في دكتور أطفال اليوم؟','فنتولين']
 .forEach(t=>{const b=document.createElement('button');b.textContent=t;b.onclick=()=>ask(t);chips.appendChild(b)});
add('أهلين! 👋 اسألني عن توفر الأدوية، الصيدليات المفتوحة، أو مواعيد الدكاتره.','b');
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
            q = str(json.loads(self.rfile.read(n))["q"])[:300]
            r = bot.ask(q)
            self._send(200, json.dumps({"text": r.text, "intent": r.intent}, ensure_ascii=False),
                       "application/json; charset=utf-8")
        except Exception:
            self._send(400, '{"text":"صار خطأ، جرّب مرة ثانية"}', "application/json; charset=utf-8")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("http://localhost:8000")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
