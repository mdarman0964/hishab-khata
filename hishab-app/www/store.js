// ডাটা সেভ হয় ফোনের localStorage-এ। আগের পাইথন সার্ভারের '/api/data' কলগুলো এখানে ধরা হয়,
// তাই পেজগুলোর কোড বদলাতে হয়নি।
(function () {
  var DEF = {
    hajira: {workers: []},
    cashbook: {categories: ['খাবার', 'বাজার', 'যাতায়াত', 'মোবাইল/নেট', 'বিল', 'চিকিৎসা', 'কেনাকাটা', 'অন্যান্য'], entries: []},
    meal: {members: [], months: {}}
  };
  var real = window.fetch.bind(window);
  function keyOf(u) {
    try {
      var p = new URL(u, location.href).pathname;
      var m = p.match(/\/(?:(hajira|cashbook|meal)\/)?api\/data$/);
      return m ? (m[1] || window.APP_KEY) : null;
    } catch (e) { return null; }
  }
  window.fetch = async function (u, o) {
    var k = typeof u === 'string' ? keyOf(u) : null;
    if (!k || !DEF[k]) return real(u, o);
    var sk = 'hishab:' + k;
    if (o && o.method === 'POST') {
      try { JSON.parse(o.body); localStorage.setItem(sk, o.body); return new Response('{"ok":true}', {status: 200}); }
      catch (e) { return new Response('{"ok":false}', {status: 400}); }
    }
    return new Response(localStorage.getItem(sk) || JSON.stringify(DEF[k]), {status: 200, headers: {'Content-Type': 'application/json'}});
  };
})();
