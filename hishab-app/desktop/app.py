#!/usr/bin/env python3
"""
হিসাব খাতা — কাজের দিন ও বেতনের হিসাব
চালানো:   python app.py
ফোন থেকে (একই ওয়াইফাই): python app.py --lan
ডাটা সেভ হয় app.py-র পাশের data.json ফাইলে।
"""
import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
PORT = 8000
LOCK = threading.Lock()

DEFAULT_DATA = {
    "workers": [
        {
            "id": "w1",
            "name": "জিকু",
            "rate": 0,
            "days": {"2026-11": [4, 5, 6, 7, 9, 10, 11, 12, 13, 14]},
            "payments": [
                {"id": "p1", "date": "2026-11-12", "amount": 400, "note": "বেতন নেওয়া হয়েছে"}
            ],
        }
    ]
}


def load_data():
    with LOCK:
        if not os.path.exists(DATA_FILE):
            save_raw(DEFAULT_DATA)
            return DEFAULT_DATA
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return DEFAULT_DATA


def save_raw(data):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


def save_data(data):
    with LOCK:
        save_raw(data)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif self.path == "/api/data":
            body = json.dumps(load_data(), ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
        else:
            self._send(404, b"Not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/data":
            return self._send(404, b"Not found", "text/plain")
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("workers"), list):
                raise ValueError("bad shape")
            save_data(data)
            self._send(200, b'{"ok":true}', "application/json")
        except Exception:
            self._send(400, b'{"ok":false}', "application/json")

    def log_message(self, *args):
        pass


HTML = r"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>হিসাব খাতা</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0d1520; --bg2:#12202f; --surface:#172a3d; --surface2:#1d3349;
  --line:rgba(255,255,255,.08); --text:#eaf0f6; --muted:#8fa3b8;
  --gold:#e9bd6b; --gold2:#c99a45; --mint:#4fd1a5; --rose:#f08a8a;
  --r:20px;
}
*{box-sizing:border-box;margin:0;-webkit-tap-highlight-color:transparent}
html,body{background:var(--bg);color:var(--text);font-family:'Hind Siliguri','Noto Sans Bengali','Kalpurush',system-ui,sans-serif;line-height:1.5}
body{min-height:100vh;background:
  radial-gradient(900px 500px at 85% -10%,rgba(233,189,107,.10),transparent 60%),
  radial-gradient(700px 500px at -10% 10%,rgba(79,209,165,.07),transparent 60%),var(--bg)}
.wrap{max-width:640px;margin:0 auto;padding:max(18px,env(safe-area-inset-top)) 16px 90px}
button,input,select{font:inherit;color:inherit}
button{cursor:pointer;border:0;background:none}
:focus-visible{outline:2px solid var(--gold);outline-offset:2px}

header{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
h1{font-size:22px;font-weight:700;letter-spacing:.2px}
.sync{font-size:13px;color:var(--muted);transition:color .3s}
.sync.ok{color:var(--mint)}

.workers{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;margin-bottom:14px;scrollbar-width:none}
.workers::-webkit-scrollbar{display:none}
.chip{padding:8px 16px;border-radius:999px;background:var(--surface);border:1px solid var(--line);white-space:nowrap;font-weight:500;color:var(--muted);transition:.2s}
.chip.active{background:linear-gradient(135deg,var(--gold),var(--gold2));color:#1a1405;border-color:transparent;font-weight:600}
.chip.add{border-style:dashed;background:transparent}

.hero{background:linear-gradient(160deg,var(--surface2),var(--surface));border:1px solid var(--line);border-radius:28px;padding:22px 22px 18px;position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;right:-50px;top:-50px;width:180px;height:180px;border-radius:50%;background:radial-gradient(circle,rgba(233,189,107,.22),transparent 70%)}
.monthnav{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;position:relative;z-index:1}
.monthnav b{font-size:18px;font-weight:600}
.navbtn{width:38px;height:38px;border-radius:12px;background:rgba(255,255,255,.06);font-size:20px;line-height:1;transition:.15s}
.navbtn:active{transform:scale(.92)}
.due-label{color:var(--muted);font-size:14px;position:relative;z-index:1}
.due{font-size:46px;font-weight:700;line-height:1.15;position:relative;z-index:1;font-variant-numeric:tabular-nums}
.due.pos{color:var(--gold)} .due.neg{color:var(--mint)} .due.zero{color:var(--text)}
.due-note{font-size:13px;color:var(--muted);margin-top:2px;position:relative;z-index:1;min-height:20px}
.hdates{position:relative;z-index:1;margin-top:14px;padding-top:14px;border-top:1px solid var(--line)}
.hdates .hl{font-size:13px;color:var(--muted)}
.hdates .hr{font-size:19px;font-weight:700;color:var(--mint);margin:2px 0 10px}
.hdates .hc{display:flex;flex-wrap:wrap;gap:6px}
.hdates .hc span{min-width:34px;text-align:center;padding:4px 8px;border-radius:10px;background:rgba(79,209,165,.15);border:1px solid rgba(79,209,165,.25);font-size:15px;font-weight:600}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:18px;position:relative;z-index:1}
.stat{background:rgba(0,0,0,.18);border-radius:14px;padding:10px 12px}
.stat span{display:block;font-size:12px;color:var(--muted)}
.stat b{font-size:18px;font-weight:600}

.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:16px;margin-top:14px}
.card h2{font-size:16px;font-weight:600;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center}
.card h2 small{font-weight:400;color:var(--muted);font-size:13px}

.rate{display:flex;align-items:center;gap:10px}
.rate label{color:var(--muted);font-size:14px;flex:1}
input[type=number],input[type=text],input[type=date]{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:10px 12px;width:100%;min-width:0;color-scheme:dark}
.rate input{width:110px;text-align:right}

.week,.grid{display:grid;grid-template-columns:repeat(7,1fr);gap:6px}
.week span{text-align:center;font-size:12px;color:var(--muted);padding-bottom:4px}
.day{aspect-ratio:1;border-radius:14px;background:var(--bg2);border:1px solid var(--line);font-size:19px;font-weight:600;font-variant-numeric:lining-nums tabular-nums;color:var(--text);position:relative;transition:transform .12s,background .2s}
.day:active{transform:scale(.9)}
.day.empty{visibility:hidden}
.day.today{border-color:var(--gold)}
.day.on{background:linear-gradient(145deg,#59dcae,#2fa87e);color:#06231a;font-weight:700;border-color:transparent;animation:pop .22s ease}
.day.on::after{content:"✓";position:absolute;right:5px;top:1px;font-size:9px;opacity:.7}
.mdates span{font-size:15px!important;font-weight:600!important}
@keyframes pop{0%{transform:scale(.8)}60%{transform:scale(1.08)}100%{transform:scale(1)}}

.pay{display:flex;align-items:center;gap:12px;padding:11px 0;border-top:1px solid var(--line)}
.pay:first-of-type{border-top:0}
.pay .amt{font-weight:600;font-size:17px;color:var(--gold);min-width:70px;font-variant-numeric:tabular-nums}
.pay .meta{flex:1;min-width:0}
.pay .meta div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pay .meta small{color:var(--muted);font-size:12px}
.del{width:34px;height:34px;border-radius:10px;color:var(--rose);background:rgba(240,138,138,.1)}
.empty-msg{color:var(--muted);font-size:14px;padding:4px 0 10px}

.addpay{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
.addpay .full{grid-column:1/-1}
.btn{padding:12px 16px;border-radius:14px;font-weight:600;background:linear-gradient(135deg,var(--gold),var(--gold2));color:#1a1405;transition:.15s}
.btn:active{transform:scale(.97)}
.btn.ghost{background:rgba(255,255,255,.06);color:var(--text)}
.btn.danger{background:rgba(240,138,138,.12);color:var(--rose)}
.row{display:flex;gap:8px;margin-top:12px}
.row .btn{flex:1}

.mrow{padding:12px 0;border-top:1px solid var(--line);cursor:pointer}
.mrow:first-child{border-top:0;padding-top:0}
.mrow.cur .mname{color:var(--gold)}
.mhead{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;gap:8px}
.mname{font-weight:600}
.mlabel{font-size:12px;color:var(--muted);margin-bottom:2px}
.mrange{font-size:17px;font-weight:600;color:var(--mint);margin-bottom:10px}
.mdates2{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}
.dchip{background:rgba(79,209,165,.12);border:1px solid rgba(79,209,165,.25);border-radius:12px;padding:6px 0;text-align:center}
.dchip b{display:block;font-size:19px;font-weight:700;line-height:1.2;color:var(--text)}
.dchip small{display:block;font-size:11px;color:var(--mint)}
.mcount{font-size:14px;font-weight:600;color:#06231a;background:var(--mint);padding:2px 12px;border-radius:999px}
.mstats{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px}
.mst{background:rgba(0,0,0,.18);border-radius:12px;padding:7px 8px;min-width:0}
.mst span{display:block;font-size:11px;color:var(--muted)}
.mst b{font-size:14px;font-weight:600;display:block;white-space:nowrap}
.mst.days b{color:var(--mint)}
.mst.due b{color:var(--gold)}
.mdates{display:flex;flex-wrap:wrap;gap:5px}
.mdates span{min-width:30px;text-align:center;padding:3px 8px;border-radius:9px;background:rgba(79,209,165,.14);color:var(--mint);font-size:13px;font-weight:500}
.mdue{font-size:12px;color:var(--muted);margin-top:7px}
.alltime{display:flex;justify-content:space-between;color:var(--muted);font-size:14px}
.alltime b{color:var(--text)}

dialog{border:1px solid var(--line);border-radius:22px;background:var(--surface);color:var(--text);padding:20px;width:min(92vw,360px);margin:auto}
dialog::backdrop{background:rgba(5,10,16,.7);backdrop-filter:blur(4px)}
dialog h3{margin-bottom:12px;font-size:17px}

.toast{position:fixed;left:50%;bottom:24px;transform:translate(-50%,30px);background:var(--surface2);border:1px solid var(--line);padding:10px 18px;border-radius:999px;font-size:14px;opacity:0;pointer-events:none;transition:.25s}
.toast.show{opacity:1;transform:translate(-50%,0)}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>হিসাব খাতা</h1>
    <span class="sync" id="sync">লোড হচ্ছে…</span>
  </header>

  <div class="workers" id="workers"></div>

  <section class="hero">
    <div class="monthnav">
      <button class="navbtn" id="prev" aria-label="আগের মাস">‹</button>
      <b id="monthTitle"></b>
      <button class="navbtn" id="next" aria-label="পরের মাস">›</button>
    </div>
    <div class="due-label" id="dueLabel">বাকি আছে</div>
    <div class="due" id="due">0</div>
    <div class="due-note" id="dueNote"></div>
    <div class="hdates" id="hDates"></div>
    <div class="stats">
      <div class="stat"><span>কাজের দিন</span><b id="sDays">0</b></div>
      <div class="stat"><span>মোট পাওনা</span><b id="sEarn">0</b></div>
      <div class="stat"><span>নেওয়া হয়েছে</span><b id="sPaid">0</b></div>
    </div>
  </section>

  <section class="card">
    <div class="rate">
      <label for="rate">দৈনিক মজুরি (টাকা)</label>
      <input type="number" id="rate" inputmode="decimal" min="0" placeholder="0">
    </div>
  </section>

  <section class="card">
    <h2>কাজের দিন <small>দিনে ট্যাপ করে টিক দিন</small></h2>
    <div class="week" id="week"></div>
    <div class="grid" id="grid"></div>
  </section>

  <section class="card">
    <h2>বেতন নেওয়া <small id="payTotal"></small></h2>
    <div id="payList"></div>
    <div class="addpay">
      <input type="number" id="pAmt" inputmode="decimal" min="0" placeholder="টাকার পরিমাণ">
      <input type="date" id="pDate">
      <input type="text" id="pNote" class="full" placeholder="নোট (ঐচ্ছিক)">
      <button class="btn full" id="addPay">বেতন যোগ করুন</button>
    </div>
  </section>

  <section class="card">
    <h2>সব মাস মিলিয়ে</h2>
    <div id="aMonths"></div>
    <div class="row">
      <button class="btn ghost" id="rename">নাম বদলান</button>
      <button class="btn danger" id="delWorker">মুছে ফেলুন</button>
    </div>
  </section>
</div>

<dialog id="dlg">
  <h3 id="dlgTitle"></h3>
  <input type="text" id="dlgInput" autocomplete="off">
  <div class="row">
    <button class="btn ghost" id="dlgCancel">বাতিল</button>
    <button class="btn" id="dlgOk">ঠিক আছে</button>
  </div>
</dialog>
<div class="toast" id="toast"></div>

<script>
const $ = id => document.getElementById(id);
const BN = new Intl.NumberFormat('en-US', {maximumFractionDigits: 2});
const fmt = n => BN.format(n);
const money = n => '৳' + fmt(n);
const MONTHS = ['জানুয়ারি','ফেব্রুয়ারি','মার্চ','এপ্রিল','মে','জুন','জুলাই','আগস্ট','সেপ্টেম্বর','অক্টোবর','নভেম্বর','ডিসেম্বর'];
const WEEK = ['রবি','সোম','মঙ্গল','বুধ','বৃহ','শুক্র','শনি'];

let data = {workers: []};
let current = null;
let view = new Date(); view.setDate(1);
let saveTimer = null;

const key = () => view.getFullYear() + '-' + String(view.getMonth() + 1).padStart(2, '0');
const worker = () => data.workers.find(w => w.id === current);
const uid = () => Math.random().toString(36).slice(2, 9);
const todayStr = () => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0'); };

async function load() {
  try {
    const r = await fetch('/api/data');
    data = await r.json();
    setSync('সেভ আছে', true);
  } catch (e) { setSync('সার্ভার পাওয়া যাচ্ছে না', false); }
  if (!data.workers.length) data.workers.push({id: uid(), name: 'নতুন', rate: 0, days: {}, payments: []});
  current = data.workers[0].id;
  render();
}

function setSync(t, ok) { const s = $('sync'); s.textContent = t; s.classList.toggle('ok', !!ok); }

function save() {
  setSync('সেভ হচ্ছে…', false);
  clearTimeout(saveTimer);
  saveTimer = setTimeout(async () => {
    try {
      const r = await fetch('/api/data', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});
      if (!r.ok) throw 0;
      setSync('সেভ হয়েছে ✓', true);
    } catch (e) { setSync('সেভ হয়নি!', false); toast('সেভ করা যায়নি — সার্ভার চালু আছে কি?'); }
  }, 250);
}

function toast(t) { const el = $('toast'); el.textContent = t; el.classList.add('show'); setTimeout(() => el.classList.remove('show'), 2200); }

function monthPayments(w) { return w.payments.filter(p => p.date.startsWith(key())); }
const sum = arr => arr.reduce((a, p) => a + (+p.amount || 0), 0);

function render() {
  const w = worker();

  // workers chips
  const box = $('workers'); box.innerHTML = '';
  data.workers.forEach(x => {
    const b = document.createElement('button');
    b.className = 'chip' + (x.id === current ? ' active' : '');
    b.textContent = x.name;
    b.onclick = () => { current = x.id; render(); };
    box.appendChild(b);
  });
  const add = document.createElement('button');
  add.className = 'chip add'; add.textContent = '+ নতুন';
  add.onclick = () => ask('নতুন জনের নাম', '', name => {
    const nw = {id: uid(), name, rate: 0, days: {}, payments: []};
    data.workers.push(nw); current = nw.id; save(); render();
  });
  box.appendChild(add);

  $('monthTitle').textContent = MONTHS[view.getMonth()] + ' ' + fmt(view.getFullYear()).replace(/,/g, '');

  const days = w.days[key()] || [];
  const earned = days.length * (+w.rate || 0);
  const paid = sum(monthPayments(w));
  const due = earned - paid;

  $('sDays').textContent = fmt(days.length);
  $('sEarn').textContent = money(earned);
  $('sPaid').textContent = money(paid);

  const dueEl = $('due');
  dueEl.className = 'due ' + (due > 0 ? 'pos' : due < 0 ? 'neg' : 'zero');
  dueEl.textContent = money(Math.abs(due));
  $('dueLabel').textContent = due < 0 ? 'বেশি নেওয়া হয়েছে' : (due === 0 ? 'হিসাব মিলে গেছে' : 'এই মাসে বাকি আছে');
  $('dueNote').textContent = (+w.rate || 0) === 0 ? 'দৈনিক মজুরি দিলে পাওনা হিসাব হবে' : '';

  $('rate').value = w.rate || '';

  // worked dates in hero card
  const hd = $('hDates'); hd.innerHTML = '';
  const hl = document.createElement('div'); hl.className = 'hl';
  if (!days.length) {
    hl.textContent = 'এই মাসে এখনো কোনো দিন টিক দেওয়া হয়নি';
    hd.appendChild(hl);
  } else {
    const sd = days.slice().sort((a, b) => a - b);
    const rs = []; sd.forEach(d => { const l = rs[rs.length - 1]; if (l && d === l[1] + 1) l[1] = d; else rs.push([d, d]); });
    const txt = rs.map(([a, b]) => a === b ? fmt(a) : (b === a + 1 ? fmt(a) + ', ' + fmt(b) : fmt(a) + '–' + fmt(b))).join(', ') + ' ' + MONTHS[view.getMonth()];
    hl.textContent = 'কাজ করেছেন যে তারিখে (' + fmt(sd.length) + ' দিন)';
    const hr = document.createElement('div'); hr.className = 'hr'; hr.textContent = txt;
    const hc = document.createElement('div'); hc.className = 'hc';
    sd.forEach(d => { const s = document.createElement('span'); s.textContent = fmt(d); hc.appendChild(s); });
    hd.append(hl, hr, hc);
  }

  // calendar
  const wk = $('week'); wk.innerHTML = WEEK.map(d => '<span>' + d + '</span>').join('');
  const grid = $('grid'); grid.innerHTML = '';
  const first = new Date(view.getFullYear(), view.getMonth(), 1).getDay();
  const total = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
  for (let i = 0; i < first; i++) { const e = document.createElement('div'); e.className = 'day empty'; grid.appendChild(e); }
  const t = new Date();
  for (let d = 1; d <= total; d++) {
    const b = document.createElement('button');
    const isToday = t.getFullYear() === view.getFullYear() && t.getMonth() === view.getMonth() && t.getDate() === d;
    b.className = 'day' + (days.includes(d) ? ' on' : '') + (isToday ? ' today' : '');
    b.textContent = fmt(d);
    b.setAttribute('aria-pressed', days.includes(d));
    b.onclick = () => toggleDay(d);
    grid.appendChild(b);
  }

  // payments
  const list = $('payList'); list.innerHTML = '';
  const mp = monthPayments(w).sort((a, b) => a.date.localeCompare(b.date));
  $('payTotal').textContent = mp.length ? 'মোট ' + money(sum(mp)) : '';
  if (!mp.length) { const m = document.createElement('div'); m.className = 'empty-msg'; m.textContent = 'এই মাসে এখনো কোনো বেতন নেওয়া হয়নি।'; list.appendChild(m); }
  mp.forEach(p => {
    const row = document.createElement('div'); row.className = 'pay';
    const a = document.createElement('div'); a.className = 'amt'; a.textContent = money(p.amount);
    const meta = document.createElement('div'); meta.className = 'meta';
    const n = document.createElement('div'); n.textContent = p.note || 'বেতন';
    const s = document.createElement('small'); const dt = new Date(p.date + 'T00:00:00'); s.textContent = fmt(dt.getDate()) + ' ' + MONTHS[dt.getMonth()];
    meta.append(n, s);
    const del = document.createElement('button'); del.className = 'del'; del.textContent = '✕'; del.setAttribute('aria-label', 'মুছুন');
    del.onclick = () => { if (confirm('এই এন্ট্রি মুছে ফেলবেন?')) { w.payments = w.payments.filter(x => x.id !== p.id); save(); render(); } };
    row.append(a, meta, del); list.appendChild(row);
  });
  $('pDate').value = todayStr();

  // all time
  const mBox = $('aMonths'); mBox.innerHTML = '';
  const keys = Object.keys(w.days).filter(k => w.days[k].length).sort().reverse();
  if (!keys.length) { const m = document.createElement('div'); m.className = 'empty-msg'; m.textContent = 'এখনো কোনো কাজের দিন টিক দেওয়া হয়নি।'; mBox.appendChild(m); }
  keys.forEach(k => {
    const [yy, mm] = k.split('-').map(Number);
    const ds = w.days[k].slice().sort((a, b) => a - b);
    const row = document.createElement('div'); row.className = 'mrow' + (k === key() ? ' cur' : '');
    const head = document.createElement('div'); head.className = 'mhead';
    const nm = document.createElement('span'); nm.className = 'mname'; nm.textContent = MONTHS[mm - 1] + ' ' + fmt(yy).replace(/,/g, '');
    const ct = document.createElement('span'); ct.className = 'mcount'; ct.textContent = fmt(ds.length) + ' দিন';
    head.append(nm, ct);
    const ranges = []; ds.forEach(d => { const l = ranges[ranges.length - 1]; if (l && d === l[1] + 1) l[1] = d; else ranges.push([d, d]); });
    const rangeTxt = ranges.map(([a, b]) => a === b ? fmt(a) : (b === a + 1 ? fmt(a) + ', ' + fmt(b) : fmt(a) + '–' + fmt(b))).join(', ') + ' ' + MONTHS[mm - 1];
    const lab = document.createElement('div'); lab.className = 'mlabel'; lab.textContent = 'কাজ করেছেন যে তারিখে';
    const rg = document.createElement('div'); rg.className = 'mrange'; rg.textContent = rangeTxt;
    const dates = document.createElement('div'); dates.className = 'mdates2';
    ds.forEach(d => {
      const c = document.createElement('div'); c.className = 'dchip';
      const n = document.createElement('b'); n.textContent = fmt(d);
      const wd = document.createElement('small'); wd.textContent = WEEK[new Date(yy, mm - 1, d).getDay()];
      c.append(n, wd); dates.appendChild(c);
    });
    row.append(head, lab, rg, dates);
    const mPaid = sum(w.payments.filter(p => p.date.startsWith(k)));
    const mEarn = ds.length * (+w.rate || 0);
    const grid4 = document.createElement('div'); grid4.className = 'mstats';
    [['কাজের দিন', fmt(ds.length) + ' দিন', 'days'], ['পাওনা', money(mEarn), ''], ['নেওয়া', money(mPaid), ''], ['বাকি', money(mEarn - mPaid), 'due']].forEach(([l, v, c]) => {
      const box = document.createElement('div'); box.className = 'mst ' + c;
      const s1 = document.createElement('span'); s1.textContent = l;
      const b1 = document.createElement('b'); b1.textContent = v;
      box.append(s1, b1); grid4.appendChild(box);
    });
    row.appendChild(grid4);
    row.onclick = () => { view = new Date(yy, mm - 1, 1); render(); window.scrollTo({top: 0, behavior: 'smooth'}); };
    mBox.appendChild(row);
  });
}

function toggleDay(d) {
  const w = worker(); const k = key();
  const arr = w.days[k] || (w.days[k] = []);
  const i = arr.indexOf(d);
  if (i >= 0) arr.splice(i, 1); else { arr.push(d); arr.sort((a, b) => a - b); }
  save(); render();
}

$('prev').onclick = () => { view.setMonth(view.getMonth() - 1); render(); };
$('next').onclick = () => { view.setMonth(view.getMonth() + 1); render(); };
$('rate').oninput = e => { worker().rate = Math.max(0, +e.target.value || 0); save();
  // refresh numbers without re-rendering the input (keeps keyboard open)
  const w = worker(); const days = w.days[key()] || []; const earned = days.length * w.rate; const paid = sum(monthPayments(w)); const due = earned - paid;
  $('sEarn').textContent = money(earned);
  $('due').textContent = money(Math.abs(due));
  $('due').className = 'due ' + (due > 0 ? 'pos' : due < 0 ? 'neg' : 'zero');
  $('dueNote').textContent = w.rate === 0 ? 'দৈনিক মজুরি দিলে পাওনা হিসাব হবে' : '';
  $('dueLabel').textContent = due < 0 ? 'বেশি নেওয়া হয়েছে' : (due === 0 ? 'হিসাব মিলে গেছে' : 'এই মাসে বাকি আছে');
};
$('rate').onchange = render;

$('addPay').onclick = () => {
  const amt = +$('pAmt').value;
  if (!(amt > 0)) { toast('টাকার পরিমাণ লিখুন'); $('pAmt').focus(); return; }
  const date = $('pDate').value || todayStr();
  worker().payments.push({id: uid(), date, amount: amt, note: $('pNote').value.trim()});
  $('pAmt').value = ''; $('pNote').value = '';
  const d = new Date(date + 'T00:00:00'); view = new Date(d.getFullYear(), d.getMonth(), 1);
  save(); render(); toast('বেতন যোগ হয়েছে');
};

$('rename').onclick = () => ask('নতুন নাম', worker().name, name => { worker().name = name; save(); render(); });
$('delWorker').onclick = () => {
  const w = worker();
  if (!confirm('"' + w.name + '" এর সব হিসাব মুছে যাবে। নিশ্চিত?')) return;
  data.workers = data.workers.filter(x => x.id !== w.id);
  if (!data.workers.length) data.workers.push({id: uid(), name: 'নতুন', rate: 0, days: {}, payments: []});
  current = data.workers[0].id; save(); render();
};

// small prompt dialog
let dlgCb = null;
function ask(title, value, cb) { $('dlgTitle').textContent = title; $('dlgInput').value = value; dlgCb = cb; $('dlg').showModal(); $('dlgInput').focus(); }
$('dlgCancel').onclick = () => $('dlg').close();
$('dlgOk').onclick = () => { const v = $('dlgInput').value.trim(); if (v && dlgCb) dlgCb(v); $('dlg').close(); };
$('dlgInput').onkeydown = e => { if (e.key === 'Enter') $('dlgOk').click(); };

load();
</script>
</body>
</html>
"""


def main():
    lan = "--lan" in sys.argv
    host = "0.0.0.0" if lan else "127.0.0.1"
    load_data()  # creates data.json on first run
    server = ThreadingHTTPServer((host, PORT), Handler)
    url = "http://localhost:%d" % PORT
    print("হিসাব খাতা চালু হয়েছে →", url)
    if lan:
        print("ফোন থেকে খুলতে: http://<এই কম্পিউটারের IP>:%d" % PORT)
    print("বন্ধ করতে Ctrl+C চাপুন")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nবন্ধ হলো।")


if __name__ == "__main__":
    main()
