// ইমেইল-পাসওয়ার্ড লগইন + Firestore-এ অটো ব্যাকআপ (Firebase REST, কোনো বাড়তি লাইব্রেরি ছাড়া)।
// নিয়ম: ফোনের ডাটাই আসল (offline-first); লগইন থাকলে বদলানোর ২ সেকেন্ড পরে ক্লাউডে যায়।
// দুই জায়গায় আলাদা বদল হলে প্রতিটা খাতার (হাজিরা/ক্যাশবুক/মিল) নতুনটাই থাকে।
(function () {
  var C = window.FIREBASE_CONFIG || {}, KEYS = ['hajira', 'cashbook', 'meal'], AK = 'hishab:auth', LS = localStorage, timer = null;
  var cfgOk = function () { return !!(C.apiKey && C.projectId); };
  var getAuth = function () { try { return JSON.parse(LS.getItem(AK)); } catch (e) { return null; } };
  var setAuth = function (a) { if (a) LS.setItem(AK, JSON.stringify(a)); else LS.removeItem(AK); };
  var ts = function (k) { return +LS.getItem('hishab:' + k + ':ts') || 0; };
  var fire = function () { try { window.dispatchEvent(new Event('hishab-sync')); } catch (e) {} };

  async function post(url, body, form) {
    var r = await fetch(url, {method: 'POST', headers: {'Content-Type': form ? 'application/x-www-form-urlencoded' : 'application/json'}, body: form ? body : JSON.stringify(body)});
    var j = await r.json().catch(function () { return {}; });
    if (!r.ok) throw new Error((j.error && (j.error.message || j.error)) || 'ERR');
    return j;
  }
  var idp = function (path, body) { return post('https://identitytoolkit.googleapis.com/v1/accounts:' + path + '?key=' + C.apiKey, body); };
  function keep(j) {
    var a = {email: j.email || (getAuth() || {}).email, uid: j.localId, idToken: j.idToken, refreshToken: j.refreshToken, exp: Date.now() + (+j.expiresIn) * 1000};
    setAuth(a); return a;
  }
  async function token() {
    var a = getAuth(); if (!a) return null;
    if (a.exp - Date.now() > 60000) return a;
    try {
      var j = await post('https://securetoken.googleapis.com/v1/token?key=' + C.apiKey, 'grant_type=refresh_token&refresh_token=' + encodeURIComponent(a.refreshToken), true);
      a = {email: a.email, uid: j.user_id, idToken: j.id_token, refreshToken: j.refresh_token, exp: Date.now() + (+j.expires_in) * 1000};
      setAuth(a); return a;
    } catch (e) {
      if (/TOKEN_EXPIRED|USER_NOT_FOUND|USER_DISABLED|INVALID_REFRESH_TOKEN/.test(String(e.message))) { setAuth(null); fire(); }
      throw e;
    }
  }

  var docUrl = function (a) { return 'https://firestore.googleapis.com/v1/projects/' + C.projectId + '/databases/(default)/documents/users/' + a.uid; };
  async function remoteGet(a) {
    var r = await fetch(docUrl(a), {headers: {Authorization: 'Bearer ' + a.idToken}});
    if (r.status === 404) return {};
    var j = await r.json().catch(function () { return {}; });
    if (!r.ok) throw new Error((j.error && j.error.message) || 'GET');
    return j.fields || {};
  }

  async function push() {
    if (!cfgOk() || !getAuth()) return;
    var dirty = KEYS.filter(function (k) { return LS.getItem('hishab:dirty:' + k); });
    if (!dirty.length) return;
    var fields = {}, mask = [], snap = {};
    dirty.forEach(function (k) {
      snap[k] = ts(k);
      fields[k] = {stringValue: LS.getItem('hishab:' + k) || ''}; fields[k + '_ts'] = {integerValue: String(snap[k])};
      mask.push('updateMask.fieldPaths=' + k, 'updateMask.fieldPaths=' + k + '_ts');
    });
    try {
      var a = await token(); if (!a) return;
      var r = await fetch(docUrl(a) + '?' + mask.join('&'), {method: 'PATCH', headers: {Authorization: 'Bearer ' + a.idToken, 'Content-Type': 'application/json'}, body: JSON.stringify({fields: fields})});
      if (!r.ok) throw new Error('PUT');
      dirty.forEach(function (k) { if (ts(k) === snap[k]) LS.removeItem('hishab:dirty:' + k); });
      LS.setItem('hishab:lastsync', Date.now());
    } catch (e) {}
    fire();
  }
  function schedule() { clearTimeout(timer); if (cfgOk() && getAuth()) timer = setTimeout(push, 2000); }
  function touch(k) { LS.setItem('hishab:' + k + ':ts', Date.now()); LS.setItem('hishab:dirty:' + k, '1'); schedule(); }

  // ক্লাউড ↔ ফোন মেলানো। ফোনের ডাটা বদলালে true ফেরত দেয় (পেজ রিলোড দরকার)।
  async function sync() {
    if (!cfgOk() || !getAuth()) return false;
    var a = await token(), f = await remoteGet(a), changed = false, toPush = false;
    KEYS.forEach(function (k) {
      var rts = f[k + '_ts'] ? +f[k + '_ts'].integerValue : 0, lts = ts(k);
      if (!lts && LS.getItem('hishab:' + k)) {  // লগইনের আগের ডাটা (টাইমস্ট্যাম্প নেই)
        if (!rts || !confirm('এই ফোনের "' + k + '" হিসাব আর ক্লাউডের হিসাব দুটোই আছে। ক্লাউডেরটা নেবেন?\n(বাতিল করলে ফোনেরটা ক্লাউডে যাবে)')) { LS.setItem('hishab:' + k + ':ts', Date.now()); lts = ts(k); }
      }
      if (rts > lts && f[k] && f[k].stringValue) {
        LS.setItem('hishab:' + k, f[k].stringValue); LS.setItem('hishab:' + k + ':ts', rts); LS.removeItem('hishab:dirty:' + k); changed = true;
      } else if (lts > rts) { LS.setItem('hishab:dirty:' + k, '1'); toPush = true; }
    });
    if (toPush) await push(); else { LS.setItem('hishab:lastsync', Date.now()); fire(); }
    return changed;
  }

  async function afterAuth(a) {
    var owner = LS.getItem('hishab:owner');
    if (owner && owner !== a.uid) {
      if (!confirm('এই ফোনে অন্য অ্যাকাউন্টের হিসাব আছে। সেটা মুছে এই অ্যাকাউন্টের হিসাব আনবেন?')) { setAuth(null); return false; }
      KEYS.forEach(function (k) { LS.removeItem('hishab:' + k); LS.removeItem('hishab:' + k + ':ts'); LS.removeItem('hishab:dirty:' + k); });
    }
    LS.setItem('hishab:owner', a.uid);
    return sync();
  }

  function errText(e) {
    var m = String((e && e.message) || e);
    if (/EMAIL_EXISTS/.test(m)) return 'এই ইমেইলে আগেই অ্যাকাউন্ট আছে — লগইন করুন';
    if (/WEAK_PASSWORD/.test(m)) return 'পাসওয়ার্ড কমপক্ষে ৬ অক্ষরের দিন';
    if (/INVALID_EMAIL|MISSING_EMAIL/.test(m)) return 'ইমেইলটা ঠিক নেই';
    if (/EMAIL_NOT_FOUND|INVALID_PASSWORD|INVALID_LOGIN_CREDENTIALS|MISSING_PASSWORD/.test(m)) return 'ইমেইল বা পাসওয়ার্ড ভুল';
    if (/TOO_MANY/.test(m)) return 'অনেকবার ভুল হয়েছে, একটু পরে চেষ্টা করুন';
    if (/OPERATION_NOT_ALLOWED/.test(m)) return 'Firebase-এ Email/Password লগইন চালু করা হয়নি';
    if (/permission|PERMISSION/i.test(m)) return 'Firestore-এর নিরাপত্তা নিয়ম (rules) বসানো হয়নি';
    if (/Failed to fetch|NetworkError|Load failed/.test(m)) return 'ইন্টারনেট নেই';
    return 'সমস্যা হয়েছে: ' + m;
  }

  window.HishabSync = {
    touch: touch, push: push, sync: sync, errText: errText,
    info: function () { var a = getAuth(); return {configured: cfgOk(), email: a && a.email, last: +LS.getItem('hishab:lastsync') || 0, pending: KEYS.some(function (k) { return LS.getItem('hishab:dirty:' + k); })}; },
    signIn: async function (email, pw) { return afterAuth(keep(await idp('signInWithPassword', {email: email, password: pw, returnSecureToken: true}))); },
    signUp: async function (email, pw) { return afterAuth(keep(await idp('signUp', {email: email, password: pw, returnSecureToken: true}))); },
    reset: function (email) { return idp('sendOobCode', {requestType: 'PASSWORD_RESET', email: email}); },
    signOut: function () { setAuth(null); fire(); }
  };
  window.addEventListener('online', push);
  schedule();
})();
