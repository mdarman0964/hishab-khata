#!/usr/bin/env python3
"""
একটাই লোকালহোস্ট — হোম পেজ থেকে বেছে নিন:
  • দৈনন্দিন হাজিরা  → /hajira   (app.py-র হাজিরা খাতা)
  • মিলের হিসাব      → /meal     (meal.py-র মেস/বাসার মিলের খাতা, PDF ও Excel রিপোর্টসহ)
  • ক্যাশবুক         → /cashbook (cashbook.py-র মাসের খরচের খাতা)

চালানো:              python run.py
ফোন থেকে (ওয়াইফাই): python run.py --lan
ব্রাউজার খুলবে না:     python run.py --no-browser

app.py, cashbook.py আর meal.py এই ফাইলের পাশেই থাকতে হবে।
ডাটা আগের মতোই data.json (হাজিরা) আর cashbook.json (ক্যাশবুক) ফাইলে সেভ হবে।
"""
import json
import re
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import app
import cashbook
import meal

PORT = 8000

HOME_BTN = r"""
<style>
.homebtn{position:fixed;left:max(16px,calc(50% - 320px));bottom:max(22px,env(safe-area-inset-bottom));z-index:60;
display:flex;align-items:center;gap:6px;height:46px;padding:0 16px;border-radius:16px;text-decoration:none;
background:rgba(29,51,73,.92);color:#eaf0f6;border:1px solid rgba(255,255,255,.12);font:600 15px 'Hind Siliguri','Noto Sans Bengali',system-ui,sans-serif;
backdrop-filter:blur(8px);box-shadow:0 8px 24px rgba(0,0,0,.4)}
.homebtn:active{transform:scale(.95)}
</style>
<a class="homebtn" href="/" aria-label="হোমে ফিরুন">← হোম</a>
"""


def page(module, prefix):
    """মডিউলের HTML-এর API পথ বদলে আর হোম বোতাম বসিয়ে দেয়।"""
    html = module.HTML.replace("'/api/data'", "'%s/api/data'" % prefix)
    return html.replace("</body>", HOME_BTN + "</body>").encode("utf-8")


APPS = {
    "/hajira": {"module": app, "key": "workers", "html": page(app, "/hajira")},
    "/cashbook": {"module": cashbook, "key": "entries", "html": page(cashbook, "/cashbook")},
    "/meal": {"module": meal, "key": "members", "html": page(meal, "/meal"), "extra": True},
}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype, headers=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _route(self):
        path = self.path.split("?")[0].rstrip("/") or "/"
        if path == "/":
            return "home", None, None
        for prefix, cfg in APPS.items():
            if path == prefix:
                return "page", prefix, cfg
            if path == prefix + "/api/data":
                return "api", prefix, cfg
            if cfg.get("extra") and path in (prefix + "/report", prefix + "/export.xlsx"):
                return "extra", prefix, cfg
        return None, None, None

    def do_GET(self):
        kind, _, cfg = self._route()
        if kind == "home":
            self._send(200, HOME.encode("utf-8"), "text/html; charset=utf-8")
        elif kind == "page":
            self._send(200, cfg["html"], "text/html; charset=utf-8")
        elif kind == "extra":
            mk = (parse_qs(urlparse(self.path).query).get("month") or [""])[0]
            if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", mk):
                return self._send(400, b"bad month", "text/plain")
            mod, data = cfg["module"], cfg["module"].load_data()
            if self.path.split("?")[0].rstrip("/").endswith("/report"):
                self._send(200, mod.report_html(data, mk).encode("utf-8"), "text/html; charset=utf-8")
            else:
                self._send(200, mod.make_xlsx(mod.build_sheets(data, mk)),
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           {"Content-Disposition": 'attachment; filename="meal-%s.xlsx"' % mk})
        elif kind == "api":
            body = json.dumps(cfg["module"].load_data(), ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
        else:
            self._send(404, b"Not found", "text/plain")

    def do_POST(self):
        kind, _, cfg = self._route()
        if kind != "api":
            return self._send(404, b"Not found", "text/plain")
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get(cfg["key"]), list):
                raise ValueError("bad shape")
            cfg["module"].save_data(data)
            self._send(200, b'{"ok":true}', "application/json")
        except Exception:
            self._send(400, b'{"ok":false}', "application/json")

    def log_message(self, *args):
        pass


HOME = r"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>আমার খাতা</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#0d1520;--surface:#172a3d;--surface2:#1d3349;--line:rgba(255,255,255,.08);--text:#eaf0f6;--muted:#8fa3b8;--gold:#e9bd6b;--gold2:#c99a45;--mint:#4fd1a5;--rose:#f08a8a}
*{box-sizing:border-box;margin:0;-webkit-tap-highlight-color:transparent}
html,body{background:var(--bg);color:var(--text);font-family:'Hind Siliguri','Noto Sans Bengali','Kalpurush',system-ui,sans-serif;line-height:1.5}
body{min-height:100vh;background:
  radial-gradient(800px 500px at 100% -10%,rgba(233,189,107,.13),transparent 60%),
  radial-gradient(700px 500px at -10% 100%,rgba(240,138,138,.10),transparent 60%),var(--bg)}
.wrap{max-width:560px;margin:0 auto;padding:max(34px,env(safe-area-inset-top)) 18px 40px}
.date{color:var(--muted);font-size:14px}
h1{font-size:32px;font-weight:700;margin:2px 0 26px;letter-spacing:.2px}
.tile{display:block;text-decoration:none;color:inherit;border-radius:28px;padding:24px;margin-bottom:16px;border:1px solid var(--line);position:relative;overflow:hidden;transition:transform .15s,border-color .2s}
.tile:active{transform:scale(.98)}
.tile:hover{border-color:rgba(255,255,255,.2)}
.tile.h{background:linear-gradient(160deg,#1f3a3a,var(--surface))}
.tile.c{background:linear-gradient(160deg,#3a2530,var(--surface))}
.tile.m{background:linear-gradient(160deg,#2a3250,var(--surface))}
.tile::after{content:"";position:absolute;right:-40px;top:-40px;width:170px;height:170px;border-radius:50%}
.tile.h::after{background:radial-gradient(circle,rgba(79,209,165,.25),transparent 70%)}
.tile.m::after{background:radial-gradient(circle,rgba(127,179,245,.25),transparent 70%)}
.tile.c::after{background:radial-gradient(circle,rgba(240,138,138,.25),transparent 70%)}
.tile>*{position:relative;z-index:1}
.ic{width:52px;height:52px;border-radius:16px;display:grid;place-items:center;font-size:26px;margin-bottom:16px;color:#10161e}
.h .ic{background:linear-gradient(145deg,#59dcae,#2fa87e)}
.m .ic{background:linear-gradient(145deg,#a5caf8,#6a9fe0)}
.c .ic{background:linear-gradient(145deg,#f4a3a3,#e27474)}
.tile h2{font-size:23px;font-weight:700}
.tile p{color:var(--muted);font-size:15px;margin-top:2px}
.sum{margin-top:16px;padding-top:14px;border-top:1px solid var(--line);font-size:15px;font-weight:600;min-height:40px}
.h .sum{color:var(--mint)} .c .sum{color:var(--rose)} .m .sum{color:#7fb3f5}
.go{position:absolute!important;right:22px;bottom:22px;width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,.08);display:grid;place-items:center;font-size:20px}
</style>
</head>
<body>
<div class="wrap">
  <div class="date" id="date"></div>
  <h1>আমার খাতা</h1>

  <a class="tile h" href="/hajira">
    <div class="ic">✓</div>
    <h2>দৈনন্দিন হাজিরা</h2>
    <p>কাজের দিন, বেতন নেওয়া আর বাকির হিসাব</p>
    <div class="sum" id="hSum">&nbsp;</div>
    <span class="go">›</span>
  </a>

  <a class="tile m" href="/meal">
    <div class="ic">🍽</div>
    <h2>মিলের হিসাব</h2>
    <p>মেস বা বাসার মিল, বাজার আর কে কত পাবে</p>
    <div class="sum" id="mSum">&nbsp;</div>
    <span class="go">›</span>
  </a>

  <a class="tile c" href="/cashbook">
    <div class="ic">৳</div>
    <h2>ক্যাশবুক</h2>
    <p>মাসের খরচ — কোথায় কত টাকা গেল</p>
    <div class="sum" id="cSum">&nbsp;</div>
    <span class="go">›</span>
  </a>
</div>

<script>
const $ = id => document.getElementById(id);
const NF = new Intl.NumberFormat('en-US', {maximumFractionDigits: 2});
const money = n => '৳' + NF.format(n);
const MONTHS = ['জানুয়ারি','ফেব্রুয়ারি','মার্চ','এপ্রিল','মে','জুন','জুলাই','আগস্ট','সেপ্টেম্বর','অক্টোবর','নভেম্বর','ডিসেম্বর'];
const WEEK = ['রবিবার','সোমবার','মঙ্গলবার','বুধবার','বৃহস্পতিবার','শুক্রবার','শনিবার'];
const now = new Date();
const mk = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0');
$('date').textContent = now.getDate() + ' ' + MONTHS[now.getMonth()] + ' ' + now.getFullYear() + ', ' + WEEK[now.getDay()];

fetch('/hajira/api/data').then(r => r.json()).then(d => {
  let days = 0, due = 0;
  (d.workers || []).forEach(w => {
    const n = ((w.days || {})[mk] || []).length; days += n;
    const paid = (w.payments || []).filter(p => p.date.startsWith(mk)).reduce((a, p) => a + (+p.amount || 0), 0);
    due += n * (+w.rate || 0) - paid;
  });
  $('hSum').textContent = 'এই মাসে ' + days + ' দিন কাজ · বাকি ' + money(due);
}).catch(() => {});

fetch('/meal/api/data').then(r => r.json()).then(d => {
  const m = (d.months || {})[mk]; const n = (d.members || []).length;
  const exp = m ? (m.expenses || []).reduce((a, e) => a + (+e.amount || 0), 0) : 0;
  $('mSum').textContent = n ? n + ' জন সদস্য · এই মাসে বাজার ' + money(exp) : 'শুরু করতে ট্যাপ করুন';
}).catch(() => {});

fetch('/cashbook/api/data').then(r => r.json()).then(d => {
  const out = (d.entries || []).filter(e => e.type === 'out' && e.date.startsWith(mk)).reduce((a, e) => a + (+e.amount || 0), 0);
  $('cSum').textContent = 'এই মাসে মোট খরচ ' + money(out);
}).catch(() => {});
</script>
</body>
</html>
"""


def main():
    lan = "--lan" in sys.argv
    host = "0.0.0.0" if lan else "127.0.0.1"

    app.load_data()        # data.json না থাকলে তৈরি হবে
    cashbook.load_data()   # cashbook.json না থাকলে তৈরি হবে

    try:
        server = ThreadingHTTPServer((host, PORT), Handler)
    except OSError:
        print("পোর্ট %d আগে থেকেই ব্যবহার হচ্ছে।" % PORT)
        print("অন্য টার্মিনালে আগের app.py / cashbook.py / run.py চালু থাকলে সেটা বন্ধ করে আবার চেষ্টা করুন।")
        sys.exit(1)

    url = "http://localhost:%d" % PORT
    print("আমার খাতা চালু হয়েছে →", url)
    print("  দৈনন্দিন হাজিরা →", url + "/hajira")
    print("  মিলের হিসাব     →", url + "/meal")
    print("  ক্যাশবুক        →", url + "/cashbook")
    if lan:
        print("ফোন থেকে খুলতে: http://<এই কম্পিউটারের IP>:%d" % PORT)
    print("বন্ধ করতে Ctrl+C চাপুন")

    if "--no-browser" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nবন্ধ হলো।")


if __name__ == "__main__":
    main()
