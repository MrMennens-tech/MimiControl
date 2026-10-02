/* Gedeelde regie-helpers voor de scènes. Alles wordt bij het opbouwen van de tijdlijn
   vastgelegd met fromTo/set (seek-veilig, deterministisch). Coördinaten zijn
   "schermcoördinaten" (1920x1080) binnen .cam. */
(function () {
  var E_IN = "power3.out", E_BEW = "power2.inOut", E_UIT = "power2.in";

  function h(html) {
    var t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstChild;
  }

  var PIJL = '<svg viewBox="0 0 24 24"><path d="M3 2 L3 19.5 L7.7 15.2 L10.8 22 L13.9 20.6 L10.9 13.9 L17.3 13.9 Z" ' +
    'fill="#FFFFFF" stroke="#111" stroke-width="1.3" stroke-linejoin="round"/></svg>';

  /* Regie: houdt camera- en cursorstand bij, zodat elke tween expliciete begin- en eindwaarden heeft. */
  function Regie(tl, root, opties) {
    opties = opties || {};
    this.tl = tl;
    this.root = root;
    this.camEl = root.querySelector(".cam");
    this.cam = { x: 0, y: 0, s: 1 };
    this.cur = null;
    if (this.camEl) tl.set(this.camEl, { x: 0, y: 0, scale: 1 }, 0);
    if (opties.cursor) this.maakCursor(opties.cursor[0], opties.cursor[1]);
  }

  Regie.prototype.maakCursor = function (x, y) {
    var c = h('<div class="cursor"><div class="cs">' + PIJL + '<div class="rimpel"></div><div class="rimpel"></div></div></div>');
    this.camEl.appendChild(c);
    this.cur = { el: c, s: c.querySelector(".cs"), r: c.querySelectorAll(".rimpel"), x: x, y: y, ri: 0, zicht: 0 };
    this.tl.set(c, { x: x, y: y, opacity: 0 }, 0);
    this.tl.set(this.cur.s, { scale: 1 }, 0);
    return this;
  };

  /* Camera naar een stand {x,y,s} of naar een rechthoek [x,y,b,h] (gecentreerd boven de ondertitelband). */
  Regie.prototype.camStand = function (doel) {
    if (!Array.isArray(doel)) return doel;
    var x = doel[0], y = doel[1], b = doel[2], hh = doel[3];
    var mx = doel[4] || 1720, my = doel[5] || 760;
    var s = Math.min(mx / b, my / hh);
    var cx = x + b / 2, cy = y + hh / 2;
    return { x: 960 - cx * s, y: 470 - cy * s, s: s };
  };

  Regie.prototype.camera = function (doel, t, dur, ease) {
    var n = this.camStand(doel);
    dur = dur == null ? 1.1 : dur;
    var o = this.cam;
    this.tl.fromTo(this.camEl, { x: o.x, y: o.y, scale: o.s },
      { x: n.x, y: n.y, scale: n.s, duration: dur, ease: ease || E_BEW, immediateRender: false }, t);
    if (this.cur) {
      this.tl.fromTo(this.cur.s, { scale: 1 / o.s }, { scale: 1 / n.s, duration: dur, ease: ease || E_BEW, immediateRender: false }, t);
    }
    this.cam = n;
    return this;
  };

  Regie.prototype.camDirect = function (doel, t) {
    var n = this.camStand(doel);
    this.tl.set(this.camEl, { x: n.x, y: n.y, scale: n.s }, t);
    if (this.cur) this.tl.set(this.cur.s, { scale: 1 / n.s }, t);
    this.cam = n;
    return this;
  };

  Regie.prototype.toonCursor = function (t, aan) {
    var c = this.cur;
    var van = c.zicht, naar = aan === false ? 0 : 1;
    this.tl.fromTo(c.el, { opacity: van }, { opacity: naar, duration: 0.3, ease: "none", immediateRender: false }, t);
    c.zicht = naar;
    return this;
  };

  /* Cursor beweegt naar (x,y) en komt aan op tijdstip t. */
  Regie.prototype.naar = function (x, y, t, dur) {
    var c = this.cur;
    dur = dur == null ? 0.7 : dur;
    if (c.zicht === 0) this.toonCursor(Math.max(0, t - dur - 0.1));
    this.tl.fromTo(c.el, { x: c.x, y: c.y }, { x: x, y: y, duration: dur, ease: E_BEW, immediateRender: false }, t - dur);
    c.x = x; c.y = y;
    return this;
  };

  /* Klik op tijdstip t: cursor duikt, rimpel; optioneel knop-element dat indrukt. */
  Regie.prototype.klik = function (t, knop) {
    var c = this.cur, tl = this.tl;
    var r = c.r[c.ri++ % c.r.length];
    tl.fromTo(r, { scale: 0.25, opacity: 0.95 }, { scale: 1.25, opacity: 0, duration: 0.5, ease: "power2.out", immediateRender: false }, t);
    tl.fromTo(c.el.querySelector("svg"), { scale: 1 }, { scale: 0.86, duration: 0.08, ease: "power1.out", immediateRender: false, transformOrigin: "3px 2px" }, t - 0.04);
    tl.fromTo(c.el.querySelector("svg"), { scale: 0.86 }, { scale: 1, duration: 0.16, ease: "power2.out", immediateRender: false, transformOrigin: "3px 2px" }, t + 0.04);
    if (knop) this.druk(knop, t);
    return this;
  };

  Regie.prototype.druk = function (el, t) {
    this.tl.fromTo(el, { scale: 1 }, { scale: 0.95, duration: 0.08, ease: "power1.out", immediateRender: false }, t - 0.03);
    this.tl.fromTo(el, { scale: 0.95 }, { scale: 1, duration: 0.22, ease: "back.out(2)", immediateRender: false }, t + 0.05);
    return this;
  };

  /* Element verschijnt (fade + kleine schuif). */
  Regie.prototype.in = function (el, t, opt) {
    opt = opt || {};
    var van = { opacity: 0, y: opt.y == null ? 24 : opt.y, scale: opt.s == null ? 1 : opt.s };
    if (opt.vooraf !== false) this.tl.set(el, van, 0);
    this.tl.fromTo(el, van, { opacity: 1, y: 0, scale: 1, duration: opt.dur || 0.6, ease: E_IN, immediateRender: false }, t);
    return this;
  };

  Regie.prototype.uit = function (el, t, opt) {
    opt = opt || {};
    this.tl.fromTo(el, { opacity: 1, y: 0 }, { opacity: 0, y: opt.y == null ? -16 : opt.y, duration: opt.dur || 0.4, ease: E_UIT, immediateRender: false }, t);
    return this;
  };

  Regie.prototype.zet = function (el, props, t) { this.tl.set(el, props, t); return this; };

  /* Hoofdstuktitel: groot in beeld, dan weg; klein label linksboven verschijnt. */
  Regie.prototype.hoofdstuk = function (groot, klein, tIn, tWissel) {
    var tl = this.tl;
    boven(groot); boven(klein);
    var kick = groot.querySelector(".kick"), tit = groot.querySelector(".tit");
    tl.set([kick, tit], { opacity: 0, y: 30 }, 0);
    tl.fromTo(kick, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.6, ease: E_IN, immediateRender: false }, tIn);
    tl.fromTo(tit, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.7, ease: E_IN, immediateRender: false }, tIn + 0.12);
    tl.fromTo(groot, { opacity: 1, y: 0 }, { opacity: 0, y: -40, duration: 0.45, ease: E_UIT, immediateRender: false }, tWissel);
    tl.set(klein, { opacity: 0, x: -20 }, 0);
    tl.fromTo(klein, { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.5, ease: E_IN, immediateRender: false }, tWissel + 0.3);
    return this;
  };

  /* Scène in- en uitfaden (de achtergrond in index.html loopt door). */
  Regie.prototype.fade = function (el, duur) {
    this.tl.set(el, { opacity: 0 }, 0);
    this.tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.4, ease: "none", immediateRender: false }, 0);
    this.tl.fromTo(el, { opacity: 1 }, { opacity: 0, duration: 0.45, ease: "none", immediateRender: false }, duur - 0.45);
    return this;
  };

  /* Wisselt tussen kinderen (bijv. getallen of knoppenrijen): toont nr i vanaf t. */
  function wissel(tl, lijst, stappen) {
    lijst = Array.prototype.slice.call(lijst);
    tl.set(lijst, { opacity: 0 }, 0);
    tl.set(lijst[stappen[0][1]], { opacity: 1 }, 0);
    for (var k = 1; k < stappen.length; k++) {
      tl.set(lijst, { opacity: 0 }, stappen[k][0]);
      tl.set(lijst[stappen[k][1]], { opacity: 1 }, stappen[k][0]);
    }
  }

  /* Tijden: woordmomenten uit de voice-over. */
  function tijden(id) {
    var T = (window.TIJDEN || {})[id] || { woorden: [], cues: {}, duur: 10 };
    return {
      duur: T.duur, voor: T.voor,
      w: function (woord, n) {
        n = n || 1;
        for (var i = 0; i < T.woorden.length; i++) {
          if (T.woorden[i].w === woord && --n === 0) return T.woorden[i].t;
        }
        throw new Error("woord niet gevonden in " + id + ": " + woord);
      },
      e: function (woord, n) {
        n = n || 1;
        for (var i = 0; i < T.woorden.length; i++) {
          if (T.woorden[i].w === woord && --n === 0) return T.woorden[i].e;
        }
        throw new Error("woord niet gevonden in " + id + ": " + woord);
      },
      c: function (naam) {
        if (!(naam in T.cues)) throw new Error("cue ontbreekt in " + id + ": " + naam);
        return T.cues[naam];
      }
    };
  }

  /* Gepauzeerde tijdlijn waarvan set(..., 0) ook meteen wordt toegepast: een set op exact 0
     wordt anders pas getekend als de afspeelkop voorbij 0 komt (frame 0 zou de eindstand tonen). */
  function tijdlijn() {
    var tl = gsap.timeline({ paused: true });
    var set = tl.set.bind(tl);
    tl.set = function (doel, waarden, pos) {
      if (pos === 0) gsap.set(doel, waarden);
      return set(doel, waarden, pos);
    };
    return tl;
  }

  /* Bovenste laag (dialoog, label, paneel): tekst mag bewust over andere tekst liggen. */
  function boven(el) {
    if (!el) return el;
    el.setAttribute("data-layout-allow-overlap", "");
    el.querySelectorAll("*").forEach(function (k) { k.setAttribute("data-layout-allow-overlap", ""); });
    return el;
  }

  window.UI = { boven: boven, tijdlijn: tijdlijn, Regie: Regie, h: h, wissel: wissel, tijden: tijden, E_IN: E_IN, E_BEW: E_BEW, E_UIT: E_UIT };
})();
