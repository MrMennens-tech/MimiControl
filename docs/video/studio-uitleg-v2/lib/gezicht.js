/* Geïllustreerd gezicht (geen echt persoon) met bestuurbare mimiek.
   Gezicht.maak(container) tekent het; Gezicht.zet(el, {open, tuit, knip, lach})
   zet de stand (0..1). Deterministisch: alleen afhankelijk van de waarden. */
(function () {
  var NS = "http://www.w3.org/2000/svg";
  var HUID = "#E9B48F", HUID_D = "#D69A74", HAAR = "#3A2A22", LIP = "#B4575C",
      MOND = "#4A1C24", TONG = "#D7737A", OOG = "#3C2C24", SHIRT = "#4DB8BE";

  function el(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  function maak(container, opties) {
    opties = opties || {};
    var svg = el("svg", { viewBox: "0 0 400 470", width: "100%", height: "100%",
      preserveAspectRatio: "xMidYMid meet" });
    var defs = el("defs", {}, svg);
    var uid = "g" + Math.round((container.id || "x").length * 997 + (window.__gezichtTeller = (window.__gezichtTeller || 0) + 1));
    var clip = el("clipPath", { id: uid + "-mond" }, defs);
    var clipEl = el("ellipse", { cx: 200, cy: 330, rx: 30, ry: 4 }, clip);

    // romp en hals
    el("path", { d: "M70 470 C80 410 130 392 200 392 C270 392 320 410 330 470 Z", fill: opties.shirt || SHIRT }, svg);
    el("path", { d: "M165 330 L165 400 C180 412 220 412 235 400 L235 330 Z", fill: HUID_D }, svg);
    // oren
    el("ellipse", { cx: 112, cy: 240, rx: 16, ry: 26, fill: HUID_D }, svg);
    el("ellipse", { cx: 288, cy: 240, rx: 16, ry: 26, fill: HUID_D }, svg);
    // hoofd (kin beweegt mee met kaak)
    var hoofd = el("path", { fill: HUID }, svg);
    // haar
    el("path", { d: "M104 236 C88 150 128 66 204 64 C276 62 318 128 298 236 C294 206 288 184 278 168 C262 174 246 170 236 160 C212 176 168 178 136 162 C122 178 110 204 104 236 Z", fill: HAAR }, svg);
    el("path", { d: "M136 162 C160 120 214 104 252 120 C230 122 206 134 190 150 C176 160 156 164 136 162 Z", fill: "#4E3A2E" }, svg);
    el("path", { d: "M236 160 C246 140 262 132 280 136 C284 148 282 160 278 168 C262 174 246 170 236 160 Z", fill: "#4E3A2E" }, svg);
    // wangen
    var wangL = el("ellipse", { cx: 150, cy: 292, rx: 22, ry: 13, fill: "#F09A86", opacity: 0.35 }, svg);
    var wangR = el("ellipse", { cx: 250, cy: 292, rx: 22, ry: 13, fill: "#F09A86", opacity: 0.35 }, svg);
    // wenkbrauwen
    var wbL = el("path", { fill: "none", stroke: HAAR, "stroke-width": 7, "stroke-linecap": "round" }, svg);
    var wbR = el("path", { fill: "none", stroke: HAAR, "stroke-width": 7, "stroke-linecap": "round" }, svg);
    // ogen
    function oog(cx) {
      var g = el("g", {}, svg);
      var wit = el("ellipse", { cx: cx, cy: 238, rx: 19, ry: 11, fill: "#FFFFFF" }, g);
      var iris = el("circle", { cx: cx, cy: 238, r: 8.5, fill: OOG }, g);
      var glim = el("circle", { cx: cx + 3, cy: 235, r: 2.4, fill: "#FFFFFF" }, g);
      var lid = el("path", { fill: HUID }, g);
      var lijn = el("path", { fill: "none", stroke: "#5A3E30", "stroke-width": 3, "stroke-linecap": "round" }, g);
      return { cx: cx, wit: wit, iris: iris, glim: glim, lid: lid, lijn: lijn };
    }
    var oL = oog(160), oR = oog(240);
    // neus
    el("path", { d: "M200 250 C196 272 188 284 190 292 C194 298 206 298 212 292", fill: "none", stroke: "#C2856A", "stroke-width": 4, "stroke-linecap": "round" }, svg);
    // mond
    var mondG = el("g", {}, svg);
    var lippen = el("ellipse", { fill: LIP }, mondG);
    var binnen = el("ellipse", { fill: MOND }, mondG);
    var inG = el("g", { "clip-path": "url(#" + uid + "-mond)" }, mondG);
    var tanden = el("rect", { fill: "#FBF7F2", rx: 3 }, inG);
    var tong = el("ellipse", { fill: TONG }, inG);
    var lachLijn = el("path", { fill: "none", stroke: "#8E3A40", "stroke-width": 3.5, "stroke-linecap": "round" }, mondG);

    container.innerHTML = "";
    container.appendChild(svg);
    var deel = { hoofd: hoofd, wbL: wbL, wbR: wbR, oL: oL, oR: oR, lippen: lippen, binnen: binnen,
      tanden: tanden, tong: tong, clipEl: clipEl, lachLijn: lachLijn, wangL: wangL, wangR: wangR };
    container.__gezicht = deel;
    zet(container, { open: 0, tuit: 0, knip: 0, lach: 0.3 });
    return container;
  }

  /* Berekent alle attributen voor een stand; geeft [[element, attrs], ...]. */
  function staat(container, s) {
    var d = container.__gezicht, uit = [];
    var open = s.open || 0, tuit = s.tuit || 0, knip = s.knip || 0, lach = s.lach == null ? 0.3 : s.lach;
    var kin = 392 + 30 * open;
    uit.push([d.hoofd, { d: "M112 220 C112 130 160 92 200 92 C240 92 288 130 288 220 L288 262 C288 " + (330 + 14 * open) +
      " 250 " + (kin - 6) + " 200 " + kin + " C150 " + (kin - 6) + " 112 " + (330 + 14 * open) + " 112 262 Z" }]);
    var wb = 6 * open;
    uit.push([d.wbL, { d: "M136 " + (206 - wb) + " C148 " + (198 - wb) + " 168 " + (198 - wb) + " 182 " + (204 - wb) }]);
    uit.push([d.wbR, { d: "M218 " + (204 - wb) + " C232 " + (198 - wb) + " 252 " + (198 - wb) + " 264 " + (206 - wb) }]);
    var dichtOog = Math.min(1, Math.max(0, knip));
    [d.oL, d.oR].forEach(function (o) {
      var ry = 11 + 2 * open;
      var bovenY = 238 - ry + 2 * ry * dichtOog;
      uit.push([o.wit, { ry: ry }]);
      uit.push([o.lid, { d: "M" + (o.cx - 24) + " " + (238 - ry - 6) + " L" + (o.cx + 24) + " " + (238 - ry - 6) +
        " L" + (o.cx + 24) + " " + bovenY + " Q" + o.cx + " " + (bovenY - 6 + 6 * dichtOog) + " " + (o.cx - 24) + " " + bovenY + " Z" }]);
      uit.push([o.lijn, { d: "M" + (o.cx - 20) + " " + bovenY + " Q" + o.cx + " " + (bovenY - 7 + 7 * dichtOog) + " " + (o.cx + 20) + " " + bovenY }]);
      var zicht = dichtOog > 0.85 ? 0 : 1;
      uit.push([o.iris, { opacity: zicht }]);
      uit.push([o.glim, { opacity: zicht }]);
    });
    var cy = 330 + 12 * open;
    var bw = 34 * (1 - 0.42 * tuit) + 4 * lach * (1 - open);
    var bh = 2 + 30 * open + 8 * tuit;
    var dicht = open < 0.06 && tuit < 0.3;
    var zachtDicht = Math.max(0, Math.min(1, (0.1 - Math.max(open, tuit / 3)) / 0.1)); /* 1 = dicht */
    var mondZicht = 1 - zachtDicht;
    uit.push([d.lippen, { cx: 200, cy: cy, rx: bw + 6 + 3 * tuit - 2 * zachtDicht, ry: (bh + 7 + 3 * tuit) * mondZicht + 10 * zachtDicht }]);
    uit.push([d.binnen, { cx: 200, cy: cy, rx: Math.max(0.01, bw), ry: Math.max(0.01, bh), opacity: mondZicht }]);
    uit.push([d.clipEl, { cx: 200, cy: cy, rx: Math.max(0.01, bw), ry: Math.max(0.01, bh) }]);
    uit.push([d.tanden, { x: 200 - bw, y: cy - bh - 2, width: 2 * bw, height: 9, opacity: mondZicht }]);
    uit.push([d.tong, { cx: 200, cy: cy + bh * 0.8, rx: bw * 0.7, ry: Math.max(0.01, bh * 0.55), opacity: mondZicht }]);
    uit.push([d.lachLijn, { opacity: zachtDicht,
      d: "M" + (200 - bw - 4) + " " + (cy - 2 * lach) + " Q200 " + (cy + 3 + 9 * lach) + " " + (200 + bw + 4) + " " + (cy - 2 * lach) }]);
    return uit;
  }

  function zet(container, s) {
    staat(container, s).forEach(function (p) {
      for (var k in p[1]) p[0].setAttribute(k, p[1][k]);
    });
  }

  /* Tween van stand s0 naar s1 (seek-veilig: expliciete begin- en eindwaarden). */
  function anim(tl, container, s0, s1, t, dur, ease) {
    var a = staat(container, s0), b = staat(container, s1);
    for (var i = 0; i < a.length; i++) {
      tl.fromTo(a[i][0], { attr: a[i][1] }, { attr: b[i][1], duration: dur, ease: ease || "power2.inOut", immediateRender: false }, t);
    }
  }

  /* Beginstand op t=0 vastleggen. */
  function start(tl, container, s) {
    staat(container, s).forEach(function (p) { tl.set(p[0], { attr: p[1] }, 0); });
  }

  /* Reeks standen: [[t, stand, dur], ...] vanaf beginstand s0. */
  function reeks(tl, container, s0, stappen) {
    start(tl, container, s0);
    var huidig = s0;
    stappen.forEach(function (st) {
      anim(tl, container, huidig, st[1], st[0], st[2] || 0.35, st[3]);
      huidig = st[1];
    });
    return huidig;
  }

  window.Gezicht = { maak: maak, zet: zet, staat: staat, anim: anim, start: start, reeks: reeks };
})();
