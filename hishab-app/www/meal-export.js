// মিলের হিসাব: Excel (.xlsx) ফাইল বানানো ও লেখা-আকারে রিপোর্ট শেয়ার
(function () {
  var MN = ['জানুয়ারি','ফেব্রুয়ারি','মার্চ','এপ্রিল','মে','জুন','জুলাই','আগস্ট','সেপ্টেম্বর','অক্টোবর','নভেম্বর','ডিসেম্বর'];
  var WK = ['সোম','মঙ্গল','বুধ','বৃহ','শুক্র','শনি','রবি'];
  var sum = function (a) { return a.reduce(function (x, y) { return x + y; }, 0); };
  var fnum = function (n) { n = Math.round(n * 100) / 100; if (n === 0) n = 0; return n.toLocaleString('en-US', {maximumFractionDigits: 2}); };
  var money = function (n) { return (n < -0.004 ? '−' : '') + '৳' + fnum(Math.abs(n)); };

  function settle(rows) {
    var cr = rows.filter(function (r) { return r.bal > 0.005; }).map(function (r) { return {n: r.name, b: r.bal}; }).sort(function (a, b) { return b.b - a.b; });
    var dr = rows.filter(function (r) { return r.bal < -0.005; }).map(function (r) { return {n: r.name, b: -r.bal}; }).sort(function (a, b) { return b.b - a.b; });
    var out = [], i = 0, j = 0;
    while (i < dr.length && j < cr.length) {
      var a = Math.min(dr[i].b, cr[j].b);
      out.push([dr[i].n, cr[j].n, a]); dr[i].b -= a; cr[j].b -= a;
      if (dr[i].b < 0.005) i++; if (cr[j].b < 0.005) j++;
    }
    return out;
  }

  function compute(data, mk) {
    var members = data.members || [], ids = members.map(function (m) { return m.id; });
    var month = (data.months || {})[mk] || {}, counts = month.counts || {}, expenses = month.expenses || [];
    var ym = mk.split('-').map(Number), y = ym[0], mo = ym[1], kinds = {};
    ['meal', 'snack'].forEach(function (kind) {
      var kc = counts[kind] || {}, daily = {}, totals = {}, paid = {};
      ids.forEach(function (i) { daily[i] = kc[i] || {}; totals[i] = sum(Object.keys(daily[i]).map(function (d) { return +daily[i][d] || 0; })); });
      var exps = expenses.filter(function (e) { return e.kind === kind && ids.indexOf(e.by) >= 0; }).sort(function (a, b) { return (a.date || '').localeCompare(b.date || ''); });
      ids.forEach(function (i) { paid[i] = sum(exps.filter(function (e) { return e.by === i; }).map(function (e) { return +e.amount || 0; })); });
      var tm = sum(ids.map(function (i) { return totals[i]; })), te = sum(ids.map(function (i) { return paid[i]; }));
      kinds[kind] = {daily: daily, totals: totals, paid: paid, exps: exps, tm: tm, te: te, rate: tm ? te / tm : 0};
    });
    var rows = members.map(function (m) {
      var i = m.id, km = kinds.meal, ks = kinds.snack;
      var mc = km.totals[i] * km.rate, sc = ks.totals[i] * ks.rate, paid = km.paid[i] + ks.paid[i];
      return {id: i, name: m.name, meals: km.totals[i], snacks: ks.totals[i], mc: mc, sc: sc, cost: mc + sc, paid: paid, bal: paid - (mc + sc)};
    });
    return {y: y, mo: mo, title: MN[mo - 1] + ' ' + y, nd: new Date(y, mo, 0).getDate(), kinds: kinds, rows: rows, settle: settle(rows)};
  }

  // ---------- Excel ----------
  var colL = function (n) { var s = ''; while (n) { var r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = Math.floor((n - 1) / 26); } return s; };
  var esc = function (s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };

  function sheetXml(rows, widths) {
    var o = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">';
    if (widths && widths.length) o += '<cols>' + widths.map(function (w, i) { return '<col min="' + (i + 1) + '" max="' + (i + 1) + '" width="' + w + '" customWidth="1"/>'; }).join('') + '</cols>';
    o += '<sheetData>';
    rows.forEach(function (row, r) {
      o += '<row r="' + (r + 1) + '">';
      row.forEach(function (cell, c) {
        if (cell == null) return;
        var v = Array.isArray(cell) ? cell[0] : cell, st = Array.isArray(cell) ? cell[1] : 0, ref = colL(c + 1) + (r + 1);
        if (typeof v === 'number') o += '<c r="' + ref + '" s="' + st + '"><v>' + (Math.round(v * 1e6) / 1e6) + '</v></c>';
        else o += '<c r="' + ref + '" s="' + st + '" t="inlineStr"><is><t xml:space="preserve">' + esc(v) + '</t></is></c>';
      });
      o += '</row>';
    });
    return o + '</sheetData></worksheet>';
  }

  var STYLES = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
    '<numFmts count="1"><numFmt numFmtId="164" formatCode="#,##0.00"/></numFmts>' +
    '<fonts count="3"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="15"/><name val="Calibri"/></font></fonts>' +
    '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFF3E3BD"/><bgColor indexed="64"/></patternFill></fill></fills>' +
    '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>' +
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>' +
    '<cellXfs count="7"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>' +
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>' +
    '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center"/></xf>' +
    '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>' +
    '<xf numFmtId="164" fontId="1" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1"/>' +
    '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>' +
    '<xf numFmtId="164" fontId="1" fillId="2" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1"/></cellXfs>' +
    '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>';

  function buildSheets(data, mk) {
    var c = compute(data, mk), names = c.rows.map(function (r) { return r.name; }), km = c.kinds.meal, ks = c.kinds.snack;
    var H = function (arr) { return arr.map(function (h) { return [h, 2]; }); };
    var s = [[['মিলের হিসাব — ' + c.title, 5]], [], H(['সদস্য', 'মিল', 'স্ন্যাক', 'মিল খরচ', 'স্ন্যাক খরচ', 'মোট খরচ', 'দিয়েছেন', 'পাবেন (+) / দিতে হবে (−)'])];
    c.rows.forEach(function (r) { s.push([r.name, r.meals, r.snacks, [r.mc, 3], [r.sc, 3], [r.cost, 3], [r.paid, 3], [r.bal, 3]]); });
    var T = function (k) { return [sum(c.rows.map(function (r) { return r[k]; })), 6]; };
    s.push([['মোট', 2], [sum(c.rows.map(function (r) { return r.meals; })), 1], [sum(c.rows.map(function (r) { return r.snacks; })), 1], T('mc'), T('sc'), T('cost'), T('paid'), T('bal')]);
    s.push([], [['মোট বাজার খরচ', 1], [km.te, 3]], [['মোট মিল', 1], km.tm], [['প্রতি মিলের রেট', 1], [km.rate, 3]],
      [['মোট স্ন্যাক খরচ', 1], [ks.te, 3]], [['মোট স্ন্যাক', 1], ks.tm], [['প্রতি স্ন্যাকের রেট', 1], [ks.rate, 3]], [], [['হিসাব মেটানোর উপায়', 1]]);
    if (c.settle.length) c.settle.forEach(function (x) { s.push([x[0], '→', x[1], [x[2], 3]]); }); else s.push(['সবার হিসাব মিলে গেছে']);
    var sheets = [['সারাংশ', s, [24, 12, 12, 14, 14, 14, 14, 26]]];
    [['meal', 'মিল'], ['snack', 'স্ন্যাক']].forEach(function (kk) {
      var k = c.kinds[kk[0]], u = kk[1];
      var rows = [[[u + ' — ' + c.title, 5]], [], [['তারিখ', 2]].concat(H(names))];
      for (var d = 1; d <= c.nd; d++) {
        var wd = WK[(new Date(c.y, c.mo - 1, d).getDay() + 6) % 7];
        rows.push([d + ' ' + wd].concat(c.rows.map(function (r) { return +(k.daily[r.id][d]) || 0; })));
      }
      rows.push([['মোট', 2]].concat(c.rows.map(function (r) { return [k.totals[r.id], 1]; })));
      rows.push([], [['মোট খরচ', 1], [k.te, 3]], [['মোট ' + u, 1], k.tm], [['প্রতি ' + u + '-এর রেট', 1], [k.rate, 3]], [], H(['সদস্য', u, 'খরচ', 'দিয়েছেন']));
      c.rows.forEach(function (r) { rows.push([r.name, k.totals[r.id], [k.totals[r.id] * k.rate, 3], [k.paid[r.id], 3]]); });
      rows.push([], H(['তারিখ', 'কে দিয়েছেন', 'বিবরণ', 'টাকা']));
      var by = {}; c.rows.forEach(function (r) { by[r.id] = r.name; });
      k.exps.forEach(function (e) {
        var ds = ''; if (e.date) { var p = e.date.split('-'); ds = (+p[2]) + ' ' + MN[+p[1] - 1]; }
        rows.push([ds, by[e.by] || '', e.note || '', [+e.amount || 0, 3]]);
      });
      rows.push([['মোট', 2], null, null, [k.te, 6]]);
      sheets.push([u, rows, [24].concat([14, 14, 14, 14, 14, 14, 14])]);
    });
    return sheets;
  }

  function crc32(b) { var crc = 0xFFFFFFFF; for (var i = 0; i < b.length; i++) { crc ^= b[i]; for (var k = 0; k < 8; k++) crc = (crc & 1) ? (crc >>> 1) ^ 0xEDB88320 : (crc >>> 1); } return (crc ^ 0xFFFFFFFF) >>> 0; }
  var u16 = function (n) { return [n & 255, (n >> 8) & 255]; };
  var u32 = function (n) { return [n & 255, (n >> 8) & 255, (n >> 16) & 255, (n >>> 24) & 255]; };

  function zip(files) {
    var enc = new TextEncoder(), parts = [], central = [], off = 0;
    files.forEach(function (f) {
      var name = enc.encode(f.name), data = enc.encode(f.text), crc = crc32(data);
      var lh = [0x50, 0x4b, 3, 4].concat(u16(20), u16(0x0800), u16(0), u16(0), u16(0x21), u32(crc), u32(data.length), u32(data.length), u16(name.length), u16(0));
      parts.push(new Uint8Array(lh), name, data);
      central.push(new Uint8Array([0x50, 0x4b, 1, 2].concat(u16(20), u16(20), u16(0x0800), u16(0), u16(0), u16(0x21), u32(crc), u32(data.length), u32(data.length), u16(name.length), u16(0), u16(0), u16(0), u16(0), u32(0), u32(off))), name);
      off += lh.length + name.length + data.length;
    });
    var csize = central.reduce(function (a, p) { return a + p.length; }, 0);
    var end = new Uint8Array([0x50, 0x4b, 5, 6].concat(u16(0), u16(0), u16(files.length), u16(files.length), u32(csize), u32(off), u16(0)));
    var all = parts.concat(central, [end]), total = all.reduce(function (a, p) { return a + p.length; }, 0), out = new Uint8Array(total), pos = 0;
    all.forEach(function (p) { out.set(p, pos); pos += p.length; });
    return out;
  }

  function makeXlsx(sheets) {
    var n = sheets.length, ct = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>';
    var wb = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>';
    var rel = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">';
    var files = [];
    sheets.forEach(function (s, i) {
      var id = i + 1;
      ct += '<Override PartName="/xl/worksheets/sheet' + id + '.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>';
      wb += '<sheet name="' + esc(s[0]) + '" sheetId="' + id + '" r:id="rId' + id + '"/>';
      rel += '<Relationship Id="rId' + id + '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet' + id + '.xml"/>';
      files.push({name: 'xl/worksheets/sheet' + id + '.xml', text: sheetXml(s[1], s[2])});
    });
    ct += '</Types>'; wb += '</sheets></workbook>';
    rel += '<Relationship Id="rId' + (n + 1) + '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>';
    var root = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>';
    return zip([{name: '[Content_Types].xml', text: ct}, {name: '_rels/.rels', text: root}, {name: 'xl/workbook.xml', text: wb}, {name: 'xl/_rels/workbook.xml.rels', text: rel}, {name: 'xl/styles.xml', text: STYLES}].concat(files));
  }

  function b64(u8) { var s = '', ch = 0x8000; for (var i = 0; i < u8.length; i += ch) s += String.fromCharCode.apply(null, u8.subarray(i, i + ch)); return btoa(s); }
  var plugins = function () { return (window.Capacitor && window.Capacitor.Plugins) || {}; };
  var cancelled = function (e) { return /cancel|abort/i.test(String(e && (e.message || e))); };

  async function shareText(text, title) {
    var P = plugins();
    try {
      if (P.Share) { await P.Share.share({title: title, text: text, dialogTitle: title}); return; }
      if (navigator.share) { await navigator.share({title: title, text: text}); return; }
      await navigator.clipboard.writeText(text); alert('হিসাব কপি হয়েছে — এখন যেকোনো জায়গায় পেস্ট করুন।');
    } catch (e) { if (!cancelled(e)) alert('শেয়ার করা যায়নি।'); }
  }

  window.exportXlsx = async function (data, mk) {
    var c = compute(data, mk);
    if (!c.rows.length) { alert('আগে সদস্য যোগ করুন।'); return; }
    var name = 'meal-' + mk + '.xlsx', mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
    var data64 = b64(makeXlsx(buildSheets(data, mk))), P = plugins();
    try {
      if (P.Filesystem && P.Share) {
        var r = await P.Filesystem.writeFile({path: name, data: data64, directory: 'CACHE'});
        await P.Share.share({title: 'মিলের হিসাব — ' + c.title, url: r.uri, dialogTitle: 'Excel ফাইল পাঠান'});
      } else { var a = document.createElement('a'); a.href = 'data:' + mime + ';base64,' + data64; a.download = name; document.body.appendChild(a); a.click(); a.remove(); }
    } catch (e) { if (!cancelled(e)) alert('ফাইল তৈরি করা যায়নি।'); }
  };

  window.shareReport = function (data, mk) {
    var c = compute(data, mk);
    if (!c.rows.length) { alert('আগে সদস্য যোগ করুন।'); return; }
    var km = c.kinds.meal, ks = c.kinds.snack, L = ['🍽 মিলের হিসাব — ' + c.title, ''];
    L.push('মোট বাজার ' + money(km.te) + ' · মোট মিল ' + fnum(km.tm) + ' · প্রতি মিল ' + money(km.rate));
    if (ks.te || ks.tm) L.push('স্ন্যাক ' + money(ks.te) + ' · মোট ' + fnum(ks.tm) + ' · প্রতি স্ন্যাক ' + money(ks.rate));
    L.push('');
    c.rows.forEach(function (r) {
      var res = Math.abs(r.bal) < 0.005 ? 'মিলে গেছে' : r.bal > 0 ? 'পাবেন ' + money(r.bal) : 'দিতে হবে ' + money(-r.bal);
      L.push('• ' + r.name + ': মিল ' + fnum(r.meals) + (ks.tm ? ', স্ন্যাক ' + fnum(r.snacks) : '') + ' → খরচ ' + money(r.cost) + ', দিয়েছেন ' + money(r.paid) + ' → ' + res);
    });
    if (c.settle.length) { L.push('', 'মেটানোর উপায়:'); c.settle.forEach(function (x) { L.push(x[0] + ' → ' + x[1] + ': ' + money(x[2])); }); }
    shareText(L.join('\n'), 'মিলের হিসাব — ' + c.title);
  };
  window.__mealExport = {compute: compute, buildSheets: buildSheets, makeXlsx: makeXlsx};
})();
