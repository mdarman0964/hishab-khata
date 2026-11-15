#!/usr/bin/env python3
"""desktop/ এর পাইথন অ্যাপগুলোর HTML থেকে মোবাইল অ্যাপের www/ ফাইল বানায় (store.js ও meal-export.js হাতে লেখা, ছোঁয়া হয় না)।
চালান:  python tools/build_www.py"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop"))
import app, cashbook, meal, run  # noqa: E402

WWW = os.path.join(ROOT, "www")


def write(name, text):
    with open(os.path.join(WWW, name), "w", encoding="utf-8") as f:
        f.write(text)


def page(html, key, extra=""):
    tag = "<script>window.APP_KEY=%r</script><script src=\"firebase-config.js\"></script><script src=\"store.js\"></script><script src=\"sync.js\"></script>%s" % (key, extra)
    html = html.replace("<head>", "<head>" + tag, 1)
    html = html.replace("</body>", run.HOME_BTN + "</body>", 1)
    return html.replace('href="/"', 'href="index.html"')


write("hajira.html", page(app.HTML, "hajira"))
write("cashbook.html", page(cashbook.HTML, "cashbook"))

# মিল: Python সার্ভারের লিংক-বোতামের বদলে অ্যাপের শেয়ার/Excel বোতাম
m = meal.HTML
a = m.index("  const q = '?month=' + mkey();")
b = m.index("  box.appendChild(rep);")
m = m[:a] + """  const pdf = h('button', 'btn', 'হোয়াটসঅ্যাপে শেয়ার'); pdf.onclick = () => window.shareReport(data, mkey());
  const xl = h('button', 'btn ghost', 'Excel ফাইল'); xl.onclick = () => window.exportXlsx(data, mkey());
  rrow.append(pdf, xl); rep.appendChild(rrow);
  rep.appendChild(h('div', 'empty-msg', 'বাঁদিকের বোতামে লেখা আকারে হিসাব, ডানেরটায় Excel ফাইল শেয়ার হবে।'));
""" + m[b:]
write("meal.html", page(m, "meal", '<script src="meal-export.js"></script>'))

# হোম: লিংক ঠিক করা + ব্যাকআপ
home = run.HOME
for k in ("hajira", "cashbook", "meal"):
    home = home.replace('href="/%s"' % k, 'href="%s.html"' % k)
home = home.replace("<script>", '<script src="firebase-config.js"></script><script src="store.js"></script><script src="sync.js"></script>\n<script>', 1)
home = home.replace("\n</div>\n\n<script", """
  <section class="acct" id="acct"></section>
  <button class="bk" id="bkBtn">ব্যাকআপ ও ফিরিয়ে আনা</button>
</div>

<dialog id="bkDlg">
  <h3>ব্যাকআপ ও ফিরিয়ে আনা</h3>
  <p>নিচের লেখাটাই আপনার সব হিসাব। ফোন বদলালে বা অ্যাপ মুছলে এটা পেস্ট করে "ফিরিয়ে আনুন" চাপলেই সব ফিরে আসবে।</p>
  <textarea id="bkText" spellcheck="false"></textarea>
  <div class="bkrow"><button id="bkShare">শেয়ার/সেভ</button><button id="bkCopy">কপি</button><button id="bkRestore">ফিরিয়ে আনুন</button></div>
  <button class="bkclose" id="bkClose">বন্ধ করুন</button>
</dialog>

<script""", 1)
home = home.replace("</head>", """<style>
.acct{background:var(--surface);border:1px solid var(--line);border-radius:22px;padding:16px;margin:4px 0 12px}
.acct .at{font-weight:600;margin-bottom:4px} .acct .am{color:var(--muted);font-size:14px;margin-bottom:8px;word-break:break-word}
.acct input{width:100%;background:var(--bg);color:var(--text);border:1px solid var(--line);border-radius:12px;padding:11px 12px;margin-bottom:8px;font:inherit}
.acct .arow{display:flex;gap:8px} .acct button{flex:1;padding:11px 8px;border-radius:12px;border:0;background:linear-gradient(135deg,var(--gold),var(--gold2));color:#1a1405;font:600 14px inherit;font-family:inherit;cursor:pointer}
.acct button.g{background:rgba(255,255,255,.08);color:var(--text)} .acct button.alink{background:none;color:var(--muted);flex:none;width:auto;padding:8px 0 0;font-weight:400;text-decoration:underline}
.bk{display:block;margin:6px auto 0;padding:10px 18px;border-radius:999px;background:rgba(255,255,255,.07);border:1px solid var(--line);color:var(--muted);font:500 14px inherit;font-family:inherit;cursor:pointer}
dialog{border:1px solid var(--line);background:var(--surface);color:var(--text);border-radius:22px;padding:18px;width:min(94vw,520px)}
dialog::backdrop{background:rgba(5,10,16,.7)}
dialog h3{margin-bottom:6px} dialog p{color:var(--muted);font-size:14px;margin-bottom:10px}
textarea{width:100%;height:150px;background:var(--bg);color:var(--text);border:1px solid var(--line);border-radius:12px;padding:10px;font:12px monospace}
.bkrow{display:flex;gap:8px;margin:10px 0}
.bkrow button{flex:1;padding:11px 6px;border-radius:12px;background:linear-gradient(135deg,var(--gold),var(--gold2));color:#1a1405;font:600 14px inherit;font-family:inherit;border:0;cursor:pointer}
.bkclose{width:100%;padding:11px;border-radius:12px;background:rgba(255,255,255,.07);color:var(--text);border:0;font:500 14px inherit;font-family:inherit;cursor:pointer}
</style></head>""", 1)
home = home.replace("</body>", """<script>
const KEYS = ['hajira', 'cashbook', 'meal'];
$('bkBtn').onclick = () => {
  const o = {}; KEYS.forEach(k => { const r = localStorage.getItem('hishab:' + k); if (r) o[k] = JSON.parse(r); });
  $('bkText').value = JSON.stringify(o); $('bkDlg').showModal();
};
$('bkClose').onclick = () => $('bkDlg').close();
$('bkCopy').onclick = async () => {
  $('bkText').select();
  try { await navigator.clipboard.writeText($('bkText').value); } catch (e) { document.execCommand('copy'); }
  alert('কপি হয়েছে');
};
$('bkShare').onclick = async () => {
  const P = (window.Capacitor && window.Capacitor.Plugins) || {}, t = $('bkText').value;
  try { if (P.Share) await P.Share.share({title: 'আমার খাতা ব্যাকআপ', text: t}); else if (navigator.share) await navigator.share({title: 'আমার খাতা ব্যাকআপ', text: t}); else alert('"কপি" বোতাম ব্যবহার করুন'); } catch (e) {}
};
$('bkRestore').onclick = () => {
  try {
    const o = JSON.parse($('bkText').value), ks = KEYS.filter(k => o[k]);
    if (!ks.length) throw 0;
    if (!confirm('বর্তমান হিসাব মুছে এই ব্যাকআপ থেকে ফিরিয়ে আনবেন?')) return;
    ks.forEach(k => { localStorage.setItem('hishab:' + k, JSON.stringify(o[k])); if (window.HishabSync) HishabSync.touch(k); });
    alert('ফিরিয়ে আনা হয়েছে'); location.reload();
  } catch (e) { alert('ব্যাকআপের লেখাটা ঠিক নেই'); }
};
const S = window.HishabSync;
function renderAcct() {
  const i = S.info(), box = $('acct');
  if (!i.configured) { box.innerHTML = '<div class="at">☁ ক্লাউড ব্যাকআপ</div><div class="am">এখনো চালু করা হয়নি — www/firebase-config.js-এ Firebase-এর দুটো মান বসাতে হবে।</div>'; return; }
  if (i.email) {
    box.innerHTML = '<div class="at">☁ অটো ব্যাকআপ চালু</div><div class="am" id="aE"></div><div class="am" id="aS"></div><div class="arow"><button id="aSync">এখনই সিঙ্ক</button><button class="g" id="aOut">লগআউট</button></div>';
    $('aE').textContent = i.email;
    $('aS').textContent = i.pending ? 'সিঙ্ক বাকি আছে (ইন্টারনেট এলে নিজে হবে)' : (i.last ? 'শেষ সিঙ্ক: ' + new Date(i.last).toLocaleString('en-GB') : 'এখনো সিঙ্ক হয়নি');
    $('aSync').onclick = async () => { $('aS').textContent = 'অপেক্ষা করুন…'; try { if (await S.sync()) location.reload(); else renderAcct(); } catch (e) { $('aS').textContent = S.errText(e); } };
    $('aOut').onclick = () => { if (confirm('লগআউট করবেন? ফোনের হিসাব ফোনেই থাকবে, শুধু অটো ব্যাকআপ বন্ধ হবে।')) { S.signOut(); renderAcct(); } };
    return;
  }
  box.innerHTML = '<div class="at">☁ লগইন করে অটো ব্যাকআপ</div><div class="am">লগইন করলে হিসাব আপনার অ্যাকাউন্টে নিজে নিজে জমা হবে, ফোন বদলালেও ফিরে পাবেন।</div><input id="aMail" type="email" placeholder="ইমেইল" autocomplete="email"><input id="aPass" type="password" placeholder="পাসওয়ার্ড (কমপক্ষে ৬ অক্ষর)" autocomplete="current-password"><div class="arow"><button id="aIn">লগইন</button><button class="g" id="aUp">নতুন অ্যাকাউন্ট</button></div><button class="alink" id="aForgot">পাসওয়ার্ড ভুলে গেছেন?</button><div class="am" id="aMsg"></div>';
  const run = async fn => {
    $('aMsg').textContent = 'অপেক্ষা করুন…';
    try { if (await fn($('aMail').value.trim(), $('aPass').value)) location.reload(); else renderAcct(); } catch (e) { $('aMsg').textContent = S.errText(e); }
  };
  $('aIn').onclick = () => run(S.signIn); $('aUp').onclick = () => run(S.signUp);
  $('aForgot').onclick = async () => {
    const m = $('aMail').value.trim(); if (!m) { $('aMsg').textContent = 'আগে ইমেইল লিখুন'; return; }
    try { await S.reset(m); $('aMsg').textContent = 'পাসওয়ার্ড রিসেটের লিংক ইমেইলে পাঠানো হয়েছে'; } catch (e) { $('aMsg').textContent = S.errText(e); }
  };
}
renderAcct();
window.addEventListener('hishab-sync', () => { if (S.info().email) renderAcct(); });
if (S.info().email) S.sync().then(ch => { if (ch) location.reload(); }).catch(() => {});
</script></body>""", 1)
write("index.html", home)
print("www তৈরি হয়েছে:", sorted(os.listdir(WWW)))
