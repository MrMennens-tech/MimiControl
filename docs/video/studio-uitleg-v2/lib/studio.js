/* Nagebouwde schermen van MimiControl Studio v2 (teksten en kleuren uit app_v2/).
   Elke bouwer geeft { el, r } terug: el = DOM-element (absoluut in schermcoördinaten),
   r = rechthoeken [x, y, b, h] van belangrijke onderdelen in schermcoördinaten
   (vaste maten, niets wordt gemeten). */
(function () {
  var h = function (s) { var t = document.createElement("template"); t.innerHTML = s.trim(); return t.content.firstChild; };
  function abs(o, r) { return [o[0] + r[0], o[1] + r[1], r[2], r[3]]; }
  function st(r, extra) {
    return 'left:' + r[0] + 'px;top:' + r[1] + 'px;width:' + r[2] + 'px;height:' + r[3] + 'px;' + (extra || "");
  }
  function vink(x, y, aan, id) {
    return '<div class="vink" ' + (id ? 'id="' + id + '" ' : '') + 'style="left:' + x + 'px;top:' + y + 'px">' +
      '<div class="aan" style="opacity:' + (aan ? 1 : 0) + '"></div></div>';
  }
  function titelbalk(tekst) {
    return '<div class="titelbalk">' + tekst + '<div class="ctl"><i></i><i class="v"></i><i class="x"></i></div></div>';
  }

  /* ---------------- Dashboard ---------------- */
  var DASH = [210, 110, 1500, 800];
  function dashboard(p, opt) {
    opt = opt || {};
    var o = DASH;
    var R = {
      venster: o,
      comm: abs(o, [1060, 120, 416, 196]),
      beheerder: abs(o, [1080, 160, 240, 34]),
      acties: abs(o, [1060, 498, 416, 296]),
      verkennen: abs(o, [1080, 542, 376, 52]),
      live: abs(o, [1080, 666, 376, 52]),
      kaart: abs(o, [28, 176, 600, 236]),
      welkom: abs(o, [28, 176, 640, 300])
    };
    var kaart = opt.kaart ?
      '<div class="kaart" id="' + p + '-tkaart" style="' + st([28, 176, 600, 236], "border-radius:14px;") + '">' +
      '<div id="' + p + '-kaartbalk" style="position:absolute;left:18px;right:18px;top:16px;height:6px;background:#FFDC00;transform-origin:0 50%"></div>' +
      '<div class="lbl" style="left:24px;top:42px;font-size:26px;font-weight:700">1. Spatie met kaak</div>' +
      '<div class="knop" style="' + st([452, 38, 124, 42], "background:#FFDC00;color:#1C1C1E;border-radius:12px;font-size:21px") + '">Spatie</div>' +
      '<div style="position:absolute;left:22px;right:22px;top:100px;height:56px;background:#F2F2F7;border-radius:10px"></div>' +
      '<div class="lbl" style="left:40px;top:113px;font-size:21px">▸ Kaak open</div>' +
      '<div class="lbl" style="right:40px;top:113px;font-size:21px;font-weight:700;color:#5A5A5E">&gt; ' + (opt.drempel || "0.60") + '</div>' +
      '<div class="knop zacht" style="' + st([22, 174, 136, 44], "border-radius:22px;font-size:19px") + '">Bewerken</div>' +
      '<div class="knop rood zacht" style="' + st([170, 174, 150, 44], "border-radius:22px;font-size:19px") + '">Verwijderen</div>' +
      '</div>' : '';
    var welkom = opt.welkom ?
      '<div class="kaart" id="' + p + '-welkom" style="' + st([28, 176, 640, 300], "border-radius:14px;") + '">' +
      '<div class="lbl" style="left:30px;top:26px;font-size:24px;font-weight:700">Welkom bij MimiControl Studio v2!</div>' +
      '<div class="lbl" style="left:30px;top:66px;font-size:19px;color:#5A5A5E">Je hebt nog geen triggers ingesteld. Volg deze stappen:</div>' +
      [["1", "Klik op “Mimiek verkennen” in de balk rechts"], ["2", "Maak het gebaar dat je wilt gebruiken voor de webcam"],
       ["3", "Stel de trigger in met de gewenste toets"], ["4", "Klik op “Live modus starten” om te beginnen"]].map(function (s, i) {
        var y = 112 + i * 44;
        return '<div class="knop" style="' + st([30, y, 32, 32], "border-radius:16px;font-size:17px") + '">' + s[0] + '</div>' +
          '<div class="lbl" style="left:76px;top:' + (y + 3) + 'px;font-size:19px">' + s[1] + '</div>';
      }).join("") + '</div>' : '';
    var el = h(
      '<div class="venster" id="' + p + '-dash" style="' + st(o) + '">' +
      '<div class="kop" style="top:0;height:96px;justify-content:flex-start;padding-left:24px">' +
      '<img src="assets/Mennenstech_logo_wit.png" style="width:64px;height:61px" alt="">' +
      '<div style="margin-left:18px"><div style="font-size:34px;font-weight:700;line-height:1.15">MimiControl Studio v2</div>' +
      '<div style="font-size:20px;font-weight:400;color:#68CCD1">Mimiek omzetten naar toetsen  ·  Mennens.Tech</div></div></div>' +
      '<div class="lbl" style="left:28px;top:122px;font-size:28px;font-weight:700"><span style="color:#4DB8BE">•</span> Geconfigureerde triggers</div>' +
      welkom + kaart +
      // rechterbalk
      '<div class="kaart" style="' + st([1060, 120, 416, 196], "border-radius:14px") + '">' +
      '<div class="lbl" style="left:20px;top:14px;font-size:22px;font-weight:700">Communicator 5</div>' +
      '<div class="lbl" id="' + p + '-beheerder" style="left:20px;top:50px;font-size:21px;font-weight:700;color:#2E9E5B">✓  Beheerder: ja</div>' +
      '<div style="position:absolute;left:20px;top:88px;width:376px;font-size:16.5px;line-height:1.38;color:#5A5A5E">Toetsen kunnen in Communicator 5 aankomen, ook op volledig scherm. Je toetsen gaan altijd naar het actieve venster: klik dus op Communicator 5 voordat je begint.</div>' +
      '</div>' +
      '<div class="kaart" style="' + st([1060, 332, 416, 150], "border-radius:14px") + '">' +
      '<div class="lbl" style="left:20px;top:14px;font-size:22px;font-weight:700">Camera</div>' +
      '<div class="knop zacht" style="' + st([20, 50, 330, 44], "justify-content:flex-start;padding-left:16px;font-size:18px") + '">Integrated Camera (Camera 0)</div>' +
      '<div class="lbl" style="left:366px;top:56px;font-size:24px;color:#5A5A5E">↻</div>' +
      '<div class="knop donker zacht" style="' + st([20, 102, 376, 36], "font-size:17px") + '">Camera preview</div>' +
      '</div>' +
      '<div class="kaart" style="' + st([1060, 498, 416, 296], "border-radius:14px") + '">' +
      '<div class="lbl" style="left:20px;top:12px;font-size:22px;font-weight:700">Acties</div>' +
      '<div class="knop" id="' + p + '-verkenknop" style="' + st([20, 44, 376, 52], "font-size:22px") + '">Mimiek verkennen</div>' +
      '<div style="position:absolute;left:20px;top:102px;width:376px;font-size:15.5px;line-height:1.35;color:#5A5A5E">Neem een gezichtsbeweging op en maak er een trigger van</div>' +
      '<div class="knop donker" id="' + p + '-liveknop" style="' + st([20, 168, 376, 52], "font-size:22px") + '">Live modus starten</div>' +
      '<div style="position:absolute;left:20px;top:228px;width:384px;font-size:13.5px;line-height:1.3;color:#5A5A5E">Je mimiek stuurt toetsen naar het actieve venster (waar je het laatst op klikte). Stoppen: de X rechtsboven in het camerabeeld (twee keer klikken), ‘Stop live’ of Q.</div>' +
      '</div>' +
      '</div>');
    return { el: el, r: R };
  }

  /* ---------------- Keuzescherm: Kies je gezichtsbewegingen ---------------- */
  var KIES = [210, 100, 1500, 820];
  var GROEPEN = [
    ["Mond", ["Lippen tuiten", "Lip-trechter", "Lipdruk L", "Lipdruk R", "Bovenlip rollen", "Onderlip rollen", "Mond dicht",
      "Lach links", "Lach rechts", "Mondhoek omlaag L", "Mondhoek omlaag R", "Mond naar links", "Mond naar rechts",
      "Bovenlip omhoog", "Onderlip omhoog", "Mondkuiltje L", "Mondkuiltje R", "Mond strekken L", "Mond strekken R",
      "Bovenlip op L", "Bovenlip op R", "Onderlip omlaag L", "Onderlip omlaag R"]],
    ["Ogen", ["Oogknip L", "Oogknip R", "Oog wijd L", "Oog wijd R", "Oog knijp L", "Oog knijp R", "Blik omhoog L", "Blik omhoog R",
      "Blik omlaag L", "Blik omlaag R", "Blik naar binnen L", "Blik naar binnen R", "Blik naar buiten L", "Blik naar buiten R"]],
    ["Wenkbrauwen", ["Wenkbrauw omlaag L", "Wenkbrauw omlaag R", "Wenkbrauwen omhoog (binnen)", "Wenkbrauw omhoog L", "Wenkbrauw omhoog R"]],
    ["Kaak", ["Kaak open", "Kaak vooruit", "Kaak links", "Kaak rechts"]],
    ["Wangen", ["Wangen bol", "Wang knijp L", "Wang knijp R"]],
    ["Neus", ["Neus optrekken L", "Neus optrekken R"]]
  ];
  var STANDAARD = { "Lippen tuiten": 1, "Lip-trechter": 1, "Mond dicht": 1, "Lach links": 1, "Lach rechts": 1,
    "Mondhoek omlaag L": 1, "Mondhoek omlaag R": 1, "Oogknip L": 1, "Oogknip R": 1, "Oog wijd L": 1, "Oog wijd R": 1,
    "Oog knijp L": 1, "Oog knijp R": 1, "Wenkbrauw omlaag L": 1, "Wenkbrauw omlaag R": 1, "Wenkbrauwen omhoog (binnen)": 1,
    "Wenkbrauw omhoog L": 1, "Wenkbrauw omhoog R": 1, "Kaak open": 1, "Neus optrekken L": 1, "Neus optrekken R": 1 };

  function kiezer(p) {
    var o = KIES;
    var VIEW = [24, 196, 1452, 460];   // zichtbare lijst binnen het venster
    var KOLB = 710, RIJ = 40, KOP = 62;
    // groepen in twee kolommen, per rij even hoog
    var html = "", y = 0, vinkjes = [], groepPos = {};
    for (var g = 0; g < GROEPEN.length; g += 2) {
      var hoogte = 0;
      for (var k = 0; k < 2; k++) {
        var gr = GROEPEN[g + k]; if (!gr) continue;
        hoogte = Math.max(hoogte, KOP + gr[1].length * RIJ + 18);
      }
      for (k = 0; k < 2; k++) {
        gr = GROEPEN[g + k]; if (!gr) continue;
        var x = k * (KOLB + 16);
        groepPos[gr[0]] = [x, y, KOLB, hoogte];
        html += '<div class="kaart" style="' + st([x, y, KOLB, hoogte], "border-radius:14px") + '">' +
          '<div class="lbl" style="left:18px;top:14px;font-size:24px;font-weight:700">' + gr[0] + '</div>' +
          '<div class="knop zacht" id="' + p + '-alles-' + gr[0] + '" style="' + st([KOLB - 190, 14, 84, 36], "border-radius:9px;font-size:18px") + '">Alles</div>' +
          '<div class="knop grijs" style="' + st([KOLB - 96, 14, 80, 36], "border-radius:9px;font-size:18px") + '">Geen</div>';
        gr[1].forEach(function (naam, i) {
          var id = p + "-v-" + naam.replace(/[^A-Za-z0-9]/g, "");
          vinkjes.push({ id: id, naam: naam, groep: gr[0], aan: !!STANDAARD[naam] });
          html += vink(26, KOP + i * RIJ + 6, STANDAARD[naam], id) +
            '<div class="lbl" style="left:68px;top:' + (KOP + i * RIJ + 4) + 'px;font-size:21px">' + naam + '</div>';
        });
        html += '</div>';
      }
      y += hoogte + 16;
    }
    var el = h(
      '<div class="venster" id="' + p + '-kies" style="' + st(o) + '">' +
      '<div class="kop" style="top:0;height:76px;font-size:30px">Kies je gezichtsbewegingen</div>' +
      '<div class="lbl" style="left:0;right:0;top:92px;text-align:center;font-size:19px;color:#5A5A5E">Alleen de bewegingen die je aanvinkt worden getoond, gemeten en voorgesteld voor triggers.</div>' +
      '<div style="position:absolute;left:150px;right:150px;top:126px;text-align:center;font-size:18px;line-height:1.4;color:#8A5A2A">Tip: de tong kan niet los gemeten worden. Wil je op de tong reageren? Combineer dan ‘Kaak open’ met ‘Lip-trechter’. Wangen staan er ook bij, maar geven vaak 0,00.</div>' +
      '<div style="position:absolute;' + st(VIEW, "overflow:hidden") + '"><div id="' + p + '-lijst" style="position:absolute;left:0;top:0;width:1452px">' + html + '</div></div>' +
      '<div class="lbl" style="left:28px;top:686px;font-size:19px;color:#5A5A5E">Snelle keuze:</div>' +
      '<div class="knop zacht" id="' + p + '-bolle" style="' + st([156, 674, 236, 46], "background:#FFE8A3;color:#1C1C1E;border-radius:10px;font-size:19px") + '">Bolle mond / tuiten</div>' +
      '<div class="knop zacht" id="' + p + '-tong" style="' + st([404, 674, 300, 46], "background:#FFE8A3;color:#1C1C1E;border-radius:10px;font-size:19px") + '">Tong uitsteken (benadering)</div>' +
      '<div class="knop grijs" id="' + p + '-aanvinken" style="' + st([354, 744, 180, 52], "border-radius:10px;font-size:19px") + '">Alles aanvinken</div>' +
      '<div class="knop grijs" id="' + p + '-uitvinken" style="' + st([548, 744, 180, 52], "border-radius:10px;font-size:19px") + '">Alles uitvinken</div>' +
      '<div class="knop" id="' + p + '-toepassen" style="' + st([742, 744, 200, 52], "border-radius:10px;font-size:23px") + '">Toepassen</div>' +
      '<div class="knop rood zacht" id="' + p + '-annuleren" style="' + st([956, 744, 170, 52], "border-radius:10px;font-size:19px") + '">Annuleren</div>' +
      '</div>');
    var gp = function (naam, scroll) { var g = groepPos[naam]; return [o[0] + VIEW[0] + g[0], o[1] + VIEW[1] + g[1] - (scroll || 0), g[2], g[3]]; };
    return {
      el: el, vinkjes: vinkjes, groep: gp, view: abs(o, VIEW), groepPos: groepPos,
      r: {
        venster: o,
        uitvinken: abs(o, [548, 744, 180, 52]), toepassen: abs(o, [742, 744, 200, 52]),
        tong: abs(o, [404, 674, 300, 46]), snel: abs(o, [20, 664, 720, 66]), tip: abs(o, [150, 120, 1200, 60])
      }
    };
  }

  /* ---------------- Verkenvenster (OpenCV) ---------------- */
  var VERK = [160, 140, 1600, 676];
  var BALKEN = ["Kaak open", "Kaak vooruit", "Kaak links", "Kaak rechts"];
  function verken(p) {
    var o = VERK;
    var knoppen = function (id, defs, b) {
      var tot = defs.length * b + (defs.length - 1) * 12, x = (1600 - tot) / 2;
      return '<div id="' + p + '-' + id + '" style="position:absolute;left:0;top:556px;width:1600px;height:80px">' +
        defs.map(function (d, i) {
          return '<div class="knop zacht" style="' + st([x + i * (b + 12), 8, b, 64], "border-radius:2px;font-size:23px;background:" + d[1]) + '">' + d[0] + '</div>';
        }).join("") + '</div>';
    };
    var TEAL = "#4DB8BE", ROOD = "#E05A50", GRIJS = "#6E6C69";
    var bars = BALKEN.map(function (n, i) {
      var y = 84 + i * 52;
      return '<div class="lbl" id="' + p + '-bl' + i + '" style="left:24px;top:' + y + 'px;font-size:23px;color:#9A9A9A">' + n + '</div>' +
        '<div style="position:absolute;left:214px;top:' + (y + 6) + 'px;width:300px;height:22px;background:#2E2E2E">' +
        '<div id="' + p + '-bf' + i + '" style="position:absolute;left:0;top:0;width:300px;height:22px;background:#777;transform-origin:0 50%"></div></div>' +
        '<div id="' + p + '-bw' + i + '" style="position:absolute;left:530px;top:' + y + 'px;width:90px;height:32px;font-size:23px;color:#BDBDBD"></div>';
    }).join("");
    var el = h(
      '<div class="venster" id="' + p + '-verk" style="' + st(o, "background:#1E1C1B;border-radius:10px") + '">' +
      titelbalk("MimiExplorer (Q=sluiten)") +
      '<div style="position:absolute;left:0;top:40px;width:960px;height:540px;background:#3C4246"><div id="' + p + '-gezicht" style="position:absolute;left:290px;top:30px;width:380px;height:446px"></div></div>' +
      '<div style="position:absolute;left:960px;top:40px;width:3px;height:540px;background:#3C3C3C"></div>' +
      '<div style="position:absolute;left:963px;top:40px;width:637px;height:516px">' +
      '<div id="' + p + '-s1" class="lbl" style="left:24px;top:22px;font-size:26px;color:#C8C8C8">Stap 1: klik Opname starten</div>' +
      '<div id="' + p + '-s2" class="lbl" style="left:24px;top:22px;font-size:26px;color:#FF4040;font-weight:700">Opname loopt: maak je beweging</div>' +
      '<div id="' + p + '-s3" class="lbl" style="left:24px;top:22px;font-size:26px;color:#FFFF00">Stap 2: klik Trigger maken</div>' +
      bars + '</div>' +
      '<div style="position:absolute;left:0;top:580px;width:1600px;height:96px;background:#2A2826"></div>' +
      '<div style="position:absolute;left:0;top:24px;width:1600px;height:676px">' +
      knoppen("k1", [["Opname starten  [spatie]", TEAL], ["Beweging kiezen  [f]", GRIJS], ["Sluiten  [q]", GRIJS]], 430) +
      knoppen("k2", [["Opname stoppen  [spatie]", ROOD]], 430) +
      knoppen("k3", [["Trigger maken  [enter]", TEAL], ["Opnieuw opnemen  [spatie]", GRIJS], ["Beweging kiezen  [f]", GRIJS], ["Sluiten  [q]", GRIJS]], 385) +
      '</div></div>');
    var k = function (n, b, i) { var tot = n * b + (n - 1) * 12, x = (1600 - tot) / 2; return abs(o, [x + i * (b + 12), 588, b, 64]); };
    return {
      el: el, r: {
        venster: o, start: k(3, 430, 0), stop: k(1, 430, 0), maken: k(4, 385, 0), paneel: abs(o, [963, 40, 637, 300]),
        knoppen: abs(o, [0, 580, 1600, 96]), cam: abs(o, [0, 40, 960, 540])
      }
    };
  }

  /* ---------------- Trigger-editor: Nieuwe trigger ---------------- */
  var ED = [260, 96, 1400, 830];
  var SL = [760, 470];  // schuifbalk x-begin en breedte (binnen een rij)
  function editor(p) {
    var o = ED;
    var rijen = [["Kaak open", "0.71", 0.50, 1], ["Kaak vooruit", "0.02", 0.01, 0], ["Kaak links", "0.05", 0.04, 0], ["Kaak rechts", "0.04", 0.03, 0]];
    var rh = rijen.map(function (r, i) {
      var y = 444 + i * 54, x0 = SL[0], b = SL[1], kx = x0 + r[2] * b;
      return '<div style="position:absolute;left:30px;top:' + y + 'px;width:1340px;height:46px;background:#fff;border:1px solid #E5E5EA;border-radius:12px">' +
        vink(16, 9, r[3], p + "-ev" + i) +
        '<div class="lbl" style="left:64px;top:8px;font-size:21px">' + r[0] + '</div>' +
        '<div class="lbl" style="left:370px;top:10px;font-size:19px;color:#5A5A5E">piek ' + r[1] + '</div>' +
        '<div style="position:absolute;left:' + (x0 - 30) + 'px;top:19px;width:' + b + 'px;height:8px;border-radius:4px;background:#9AA3A8"></div>' +
        '<div id="' + p + '-sp' + i + '" style="position:absolute;left:' + (x0 - 30) + 'px;top:19px;width:' + b + 'px;height:8px;border-radius:4px;background:#4DB8BE;transform-origin:0 50%;transform:scaleX(' + r[2] + ')"></div>' +
        '<div id="' + p + '-sk' + i + '" style="position:absolute;left:' + (kx - 30 - 14) + 'px;top:9px;width:28px;height:28px;border-radius:14px;background:#4DB8BE"></div>' +
        '<div id="' + p + '-sw' + i + '" style="position:absolute;left:1240px;top:6px;width:84px;height:34px;text-align:right;font-size:22px;font-weight:700">' + r[2].toFixed(2) + '</div>' +
        '</div>';
    }).join("");
    var el = h(
      '<div class="venster" id="' + p + '-ed" style="' + st(o) + '">' +
      '<div class="kop" style="top:0;height:90px;font-size:32px">Nieuwe trigger</div>' +
      '<div class="lbl" style="left:36px;top:126px;font-size:21px">Naam:</div>' +
      '<div style="position:absolute;left:126px;top:114px;width:440px;height:52px;background:#FAFAFA;border:1px solid #E5E5EA;border-radius:12px"></div>' +
      '<div id="' + p + '-naam1" class="lbl" style="left:144px;top:124px;font-size:24px">Trigger 1</div>' +
      '<div id="' + p + '-naamsel" style="position:absolute;left:140px;top:122px;width:106px;height:36px;background:#BFE6E8;opacity:0"></div>' +
      '<div id="' + p + '-naam2" class="lbl" style="left:144px;top:124px;font-size:24px"></div>' +
      '<div class="lbl" style="left:36px;top:194px;font-size:21px">Actie:</div>' +
      '<div id="' + p + '-actie" style="position:absolute;left:126px;top:180px;width:300px;height:52px;background:#fff;border-radius:12px">' +
      '<div class="lbl" style="left:18px;top:9px;font-size:24px">Spatie</div>' +
      '<div class="knop" style="left:248px;top:0;width:52px;height:52px;border-radius:0 12px 12px 0;font-size:20px">▾</div></div>' +
      '<div class="knop" style="' + st([440, 180, 210, 52], "font-size:21px") + '">Toets opnemen</div>' +
      '<div class="lbl" style="left:36px;top:262px;font-size:18px;color:#5A5A5E">Kies de gezichtsbewegingen en stel in hoe sterk je ze moet maken (drempel):</div>' +
      '<div style="position:absolute;left:36px;top:296px;width:1120px;font-size:17px;line-height:1.4;color:#8A5A2A">Tip: de tong kan niet los gemeten worden. Wil je op de tong reageren? Combineer dan ‘Kaak open’ met ‘Lip-trechter’. Wangen staan er ook bij, maar geven vaak 0,00.</div>' +
      '<div class="lbl" style="left:96px;top:364px;font-size:17px;color:#5A5A5E">Beweging</div>' +
      '<div class="lbl" style="left:396px;top:364px;font-size:17px;color:#5A5A5E">Gemeten</div>' +
      '<div class="lbl" style="left:960px;top:364px;font-size:17px;color:#5A5A5E">Drempel</div>' +
      '<div class="lbl" style="left:1296px;top:364px;font-size:17px;color:#5A5A5E">Waarde</div>' +
      '<div class="lbl" style="left:40px;top:404px;font-size:22px;font-weight:700;color:#062D36">Kaak</div>' +
      rh +
      '<div class="knop" id="' + p + '-opslaan" style="' + st([990, 750, 190, 58], "border-radius:29px;font-size:24px") + '">Opslaan</div>' +
      '<div class="knop grijs" style="' + st([1194, 750, 180, 58], "border-radius:29px;font-size:24px;font-weight:700") + '">Annuleren</div>' +
      // uitklaplijst
      '<div id="' + p + '-lijst" style="position:absolute;left:126px;top:238px;width:300px;height:282px;background:#fff;border-radius:12px;box-shadow:0 16px 40px rgba(0,0,0,.22);overflow:hidden">' +
      ["Spatie", "Enter", "Tab", "Pijl links", "Pijl rechts", "Pijl omhoog"].map(function (t, i) {
        return '<div style="position:absolute;left:0;top:' + (i * 47) + 'px;width:300px;height:47px;' + (i === 0 ? "background:#E3F4F5;" : "") + 'font-size:22px;padding:9px 18px">' + t + '</div>';
      }).join("") + '</div>' +
      '</div>');
    var rij0 = abs(o, [30, 444, 1340, 46]);
    return {
      el: el, SL: SL, r: {
        venster: o, naam: abs(o, [126, 114, 440, 52]), actie: abs(o, [126, 180, 300, 52]), spatie: abs(o, [126, 238, 300, 47]),
        rij: rij0, opslaan: abs(o, [990, 750, 190, 58]),
        knop: function (v) { return [rij0[0] + SL[0] - 30 + v * SL[1], rij0[1] + 23]; },
        bovenkant: abs(o, [20, 100, 660, 150])
      }
    };
  }

  /* ---------------- Verkenner (map met het programma) ---------------- */
  var MAP = [360, 180, 1200, 600];
  function verkenner(p) {
    var o = MAP;
    var rij = function (i, ico, naam, datum, type, id) {
      var y = 156 + i * 58;
      return '<div id="' + (id || "") + '" style="position:absolute;left:12px;top:' + y + 'px;width:1176px;height:52px;border-radius:8px"></div>' +
        '<div style="position:absolute;left:30px;top:' + (y + 10) + 'px;width:32px;height:32px">' + ico + '</div>' +
        '<div class="lbl" style="left:78px;top:' + (y + 11) + 'px;font-size:22px">' + naam + '</div>' +
        '<div class="lbl" style="left:640px;top:' + (y + 13) + 'px;font-size:19px;color:#5A5A5E">' + datum + '</div>' +
        '<div class="lbl" style="left:900px;top:' + (y + 13) + 'px;font-size:19px;color:#5A5A5E">' + type + '</div>';
    };
    var map = '<svg viewBox="0 0 32 32" width="32" height="32"><path d="M2 8 L12 8 L15 11 L30 11 L30 27 L2 27 Z" fill="#E8B43C"/><path d="M2 13 L30 13 L30 27 L2 27 Z" fill="#F5C84C"/></svg>';
    var app = '<div style="width:32px;height:32px;border-radius:8px;background:#062D36;display:flex;align-items:center;justify-content:center"><img src="assets/Mennenstech_logo_wit.png" style="width:24px;height:23px" alt=""></div>';
    var el = h(
      '<div class="venster" id="' + p + '-map" style="' + st(o, "background:#FFFFFF") + '">' +
      titelbalk("MimiControl Studio v2") +
      '<div style="position:absolute;left:0;top:40px;width:1200px;height:58px;background:#F7F8F9;border-bottom:1px solid #E5E5EA"></div>' +
      '<div class="lbl" style="left:24px;top:56px;font-size:19px;color:#5A5A5E">…  ›  MimiControl Studio v2</div>' +
      '<div class="lbl" style="left:78px;top:116px;font-size:17px;color:#5A5A5E">Naam</div>' +
            '<div class="lbl" style="left:900px;top:116px;font-size:17px;color:#5A5A5E">Type</div>' +
      rij(0, map, "_internal", "", "Bestandsmap") +
      rij(1, app, "MimiControl Studio v2.exe", "", "Toepassing", p + "-exe") +
      '</div>');
    return { el: el, r: { venster: o, exe: abs(o, [12, 214, 1176, 52]), exeNaam: abs(o, [78, 225, 330, 30]) } };
  }

  /* ---------------- Vraag: opnieuw starten als beheerder ---------------- */
  function vraag(p) {
    var o = [460, 250, 1000, 430];
    var el = h(
      '<div class="venster" id="' + p + '-vraag" style="' + st(o, "background:#FFFFFF") + '">' +
      titelbalk("MimiControl Studio — beheerdersrechten") +
      '<div style="position:absolute;left:40px;top:72px;width:920px;font-size:28px;line-height:1.4">Studio werkt met Communicator 5 alleen als het als beheerder draait.</div>' +
      '<div class="lbl" style="left:40px;top:168px;font-size:28px;font-weight:700">Nu opnieuw starten als beheerder?</div>' +
      '<div style="position:absolute;left:40px;top:228px;width:900px;font-size:20px;line-height:1.4;color:#5A5A5E">Kies ‘Nee’ om toch door te gaan; toetsen komen dan mogelijk niet aan in Communicator 5.</div>' +
      '<div style="position:absolute;left:0;top:322px;width:1000px;height:108px;background:#F2F2F7;border-top:1px solid #E5E5EA"></div>' +
      '<div class="knop" id="' + p + '-ja" style="' + st([628, 348, 160, 56], "font-size:24px") + '">Ja</div>' +
      '<div class="knop grijs" style="' + st([804, 348, 160, 56], "font-size:24px") + '">Nee</div>' +
      '</div>');
    return { el: el, r: { venster: o, ja: abs(o, [628, 348, 160, 56]), tekst: abs(o, [20, 50, 960, 230]) } };
  }

  /* ---------------- Windows-melding (neutrale kaart) ---------------- */
  function melding(p) {
    var o = [560, 280, 800, 360];
    var schild = '<svg viewBox="0 0 40 40" width="56" height="56"><path d="M20 3 L35 9 L35 20 C35 29 28 35 20 38 C12 35 5 29 5 20 L5 9 Z" fill="#4DB8BE"/><path d="M13 20 L18 25 L28 14" stroke="#fff" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    var el = h(
      '<div class="venster" id="' + p + '-melding" style="' + st(o, "background:#FFFFFF") + '">' +
      '<div style="position:absolute;left:0;top:0;width:800px;height:96px;background:#062D36"></div>' +
      '<div style="position:absolute;left:36px;top:20px">' + schild + '</div>' +
      '<div class="lbl" style="left:112px;top:28px;font-size:30px;font-weight:700;color:#fff">Windows-melding</div>' +
      '<div class="lbl" style="left:40px;top:132px;font-size:22px;color:#5A5A5E">Programma</div>' +
      '<div class="lbl" style="left:40px;top:166px;font-size:30px;font-weight:700">MimiControl Studio v2</div>' +
      '<div class="knop" id="' + p + '-mja" style="' + st([424, 268, 170, 58], "font-size:24px") + '">Ja</div>' +
      '<div class="knop grijs" style="' + st([606, 268, 170, 58], "font-size:24px") + '">Nee</div>' +
      '</div>');
    return { el: el, r: { venster: o, ja: abs(o, [424, 268, 170, 58]) } };
  }

  /* ---------------- Communicatiebord (gestileerd, geen merk) ---------------- */
  var ICO = {
    ja: '<path d="M14 34 L28 48 L52 20" stroke="#2E9E5B" stroke-width="8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    nee: '<path d="M18 18 L46 46 M46 18 L18 46" stroke="#D9473D" stroke-width="8" stroke-linecap="round"/>',
    meer: '<path d="M32 12 V52 M12 32 H52" stroke="#2C7FB8" stroke-width="8" stroke-linecap="round"/>',
    stop: '<path d="M22 8 H42 L56 22 V42 L42 56 H22 L8 42 V22 Z" fill="#D9473D"/><rect x="18" y="29" width="28" height="6" fill="#fff"/>',
    help: '<circle cx="32" cy="32" r="24" fill="#F29C38"/><path d="M24 25 C24 16 40 16 40 25 C40 32 32 31 32 39" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round"/><circle cx="32" cy="47" r="3.5" fill="#fff"/>',
    eten: '<circle cx="32" cy="34" r="20" fill="none" stroke="#8C6A4A" stroke-width="5"/><circle cx="32" cy="34" r="11" fill="#F2D2A8"/><path d="M8 10 V26 M4 10 V20 M12 10 V20 M8 26 V58" stroke="#5A5A5E" stroke-width="3.5" stroke-linecap="round"/>',
    drinken: '<path d="M16 12 H48 L44 56 H20 Z" fill="#CFE9F7" stroke="#2C7FB8" stroke-width="4" stroke-linejoin="round"/><path d="M19 28 H45 L43 54 H21 Z" fill="#6FB6E3"/>',
    spelen: '<circle cx="32" cy="32" r="24" fill="#F5C84C"/><path d="M8 32 C20 24 44 24 56 32 M32 8 C24 20 24 44 32 56" stroke="#D9473D" stroke-width="4" fill="none"/>',
    buiten: '<circle cx="32" cy="32" r="12" fill="#F5C84C"/><path d="M32 6 V14 M32 50 V58 M6 32 H14 M50 32 H58 M13 13 L19 19 M45 45 L51 51 M51 13 L45 19 M19 45 L13 51" stroke="#F29C38" stroke-width="4" stroke-linecap="round"/>',
    muziek: '<path d="M24 46 V14 L50 9 V40" stroke="#7A4FB8" stroke-width="5" fill="none"/><ellipse cx="18" cy="46" rx="8" ry="6" fill="#7A4FB8"/><ellipse cx="44" cy="40" rx="8" ry="6" fill="#7A4FB8"/>',
    ik: '<circle cx="32" cy="20" r="11" fill="#F2B48A"/><path d="M12 58 C12 40 52 40 52 58 Z" fill="#4DB8BE"/>',
    jij: '<circle cx="32" cy="20" r="11" fill="#C98E6E"/><path d="M12 58 C12 40 52 40 52 58 Z" fill="#F29C38"/>',
    wil: '<path d="M32 54 C10 38 8 22 20 16 C27 13 31 18 32 22 C33 18 37 13 44 16 C56 22 54 38 32 54 Z" fill="#E86A8A"/>',
    niet: '<circle cx="32" cy="32" r="22" fill="none" stroke="#D9473D" stroke-width="6"/><path d="M17 47 L47 17" stroke="#D9473D" stroke-width="6"/>',
    klaar: '<path d="M16 8 V58" stroke="#5A5A5E" stroke-width="4" stroke-linecap="round"/><path d="M18 10 H50 L42 22 L50 34 H18 Z" fill="#2E9E5B"/>'
  };
  var WOORDEN = [["ja", "#DFF3E4"], ["nee", "#FBE2DF"], ["meer", "#E1EEF8"], ["stop", "#FBE2DF"], ["help", "#FDEBD6"],
    ["eten", "#FFF3D6"], ["drinken", "#E1EEF8"], ["spelen", "#FFF3D6"], ["buiten", "#FFF3D6"], ["muziek", "#EEE5F8"],
    ["ik", "#E3F4F5"], ["jij", "#FDEBD6"], ["wil", "#FBE5EC"], ["niet", "#FBE2DF"], ["klaar", "#DFF3E4"]];
  var CEL = function (i) { var c = i % 5, r = Math.floor(i / 5); return [40 + c * 372, 124 + r * 316, 352, 300]; };
  function bord(p) {
    var cellen = WOORDEN.map(function (w, i) {
      var c = CEL(i);
      return '<div style="position:absolute;' + st(c, "background:#fff;border-radius:22px;box-shadow:0 2px 6px rgba(0,0,0,.08)") + '">' +
        '<div style="position:absolute;left:0;top:0;width:352px;height:200px;border-radius:22px 22px 0 0;background:' + w[1] + '"></div>' +
        '<svg viewBox="0 0 64 64" style="position:absolute;left:106px;top:30px;width:140px;height:140px">' + ICO[w[0]] + '</svg>' +
        '<div style="position:absolute;left:0;right:0;top:214px;text-align:center;font-size:52px;font-weight:700;color:#1C1C1E">' + w[0] + '</div></div>';
    }).join("");
    var el = h(
      '<div id="' + p + '-bord" style="position:absolute;left:0;top:0;width:1920px;height:1080px;background:#E8EEF0;overflow:hidden">' +
      '<div style="position:absolute;left:0;top:0;width:1920px;height:100px;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.08)"></div>' +
      '<div class="lbl" style="left:40px;top:22px;font-size:40px;font-weight:700;color:#1C1C1E">Begin</div>' +
      '<div class="knop grijs" style="' + st([220, 20, 180, 60], "font-size:28px") + '">Terug</div>' +
      '<div class="knop grijs" style="' + st([416, 20, 180, 60], "font-size:28px") + '">Home</div>' +
      cellen +
      '<div id="' + p + '-scan" style="position:absolute;left:0;top:0;width:376px;height:324px;border:12px solid #FFD60A;border-radius:30px;box-shadow:0 0 0 4px rgba(0,0,0,.15)"></div>' +
      '</div>');
    return { el: el, cel: function (i) { var c = CEL(i); return [c[0] - 12, c[1] - 12]; }, CEL: CEL };
  }

  /* ---------------- Live: klein camerabeeld (overlay) ---------------- */
  var OV = [1416, 24, 480, 270];
  function overlay(p) {
    var o = OV;
    var el = h(
      '<div id="' + p + '-ov" style="position:absolute;' + st(o, "background:#3C4246;box-shadow:0 12px 30px rgba(0,0,0,.35)") + '">' +
      '<div id="' + p + '-ovgez" style="position:absolute;left:130px;top:22px;width:220px;height:258px"></div>' +
      '<div id="' + p + '-ovrand" style="position:absolute;inset:0;border:4px solid #FFDC00;opacity:0"></div>' +
      '<div id="' + p + '-ovx" style="position:absolute;right:6px;top:6px;width:28px;height:24px;background:#464646;border:1px solid #fff;color:#fff;font-size:15px;line-height:22px;text-align:center">X</div>' +
      '<div id="' + p + '-ovstop" style="position:absolute;right:6px;top:6px;width:196px;height:24px;background:#DC3C3C;border:1px solid #fff;color:#fff;font-size:13.5px;line-height:22px;text-align:center;opacity:0">Stoppen? Klik nogmaals</div>' +
      '<div id="' + p + '-ovtel" style="position:absolute;right:6px;top:31px;width:196px;height:3px;background:#fff;opacity:0;transform-origin:0 50%"></div>' +
      '<div id="' + p + '-ovbadge" style="position:absolute;left:8px;top:196px;height:40px;padding:0 10px;background:#FFDC00;border:1px solid #fff;color:#141414;font-size:17px;font-weight:700;line-height:38px;opacity:0;white-space:nowrap">Verstuurd: Spatie</div>' +
      '</div>');
    return {
      el: el, r: {
        venster: o, x: [o[0] + 480 - 34, o[1] + 6, 28, 24], stop: [o[0] + 480 - 202, o[1] + 6, 196, 24],
        badge: [o[0] + 8, o[1] + 196, 180, 40]
      }
    };
  }

  /* ---------------- Live: drempelpaneel ---------------- */
  var PN = [996, 24, 404, 580];
  function paneel(p) {
    var o = PN;
    var el = h(
      '<div class="venster" id="' + p + '-pn" style="' + st(o, "border-radius:10px") + '">' +
      titelbalk("Drempels — MimiControl Studio v2") +
      '<div class="kop" style="top:40px;height:56px;font-size:19px">Live Drempels &amp; Filter</div>' +
      '<div class="lbl" style="left:0;right:0;top:102px;text-align:center;font-size:11.5px;color:#5A5A5E">Schakelaar: trigger aan/uit  ·  Schuifbalk: hoe sterk de beweging moet zijn</div>' +
      '<div style="position:absolute;left:12px;top:126px;width:380px;height:118px;background:#E8F6F7;border-radius:8px"></div>' +
      '<div id="' + p + '-ban1" style="position:absolute;left:24px;top:134px;width:356px;font-size:14.5px;line-height:1.38;color:#062D36"><div>Actief venster: het camerabeeld van Studio</div><div>Let op: je toetsen komen nu hier terecht. Klik op Communicator 5 (of je eigen programma) om dat het actieve venster te maken.</div></div>' +
      '<div id="' + p + '-ban2" style="position:absolute;left:24px;top:134px;width:356px;font-size:14.5px;line-height:1.38;color:#062D36;opacity:0"><div>Actief venster: Communicator 5</div><div>Je mimiek-toetsen gaan naar dit venster.</div></div>' +
      '<div class="kaart" style="' + st([12, 258, 380, 142], "border-radius:12px") + '">' +
      '<div style="position:absolute;left:12px;right:12px;top:10px;height:4px;background:#FFDC00"></div>' +
      '<div class="lbl" style="left:14px;top:26px;font-size:16px;font-weight:700">1. Spatie met kaak</div>' +
      '<div style="position:absolute;left:316px;top:26px;width:46px;height:24px;border-radius:12px;background:#4DB8BE"><div style="position:absolute;left:25px;top:3px;width:18px;height:18px;border-radius:9px;background:#fff"></div></div>' +
      '<div class="lbl" style="left:14px;top:72px;font-size:14px">Kaak open</div>' +
      '<div style="position:absolute;left:110px;top:80px;width:200px;height:6px;border-radius:3px;background:#9AA3A8"><div style="width:120px;height:6px;border-radius:3px;background:#4DB8BE"></div></div>' +
      '<div style="position:absolute;left:222px;top:73px;width:20px;height:20px;border-radius:10px;background:#4DB8BE"></div>' +
      '<div class="lbl" style="left:324px;top:71px;font-size:15px;font-weight:700">0.60</div>' +
      '</div>' +
      '<div class="knop rood" id="' + p + '-stoplive" style="' + st([12, 470, 186, 38], "font-size:15px;border-radius:12px") + '">Stop live</div>' +
      '<div class="knop" style="' + st([206, 470, 186, 38], "font-size:15px;border-radius:12px") + '">Opslaan en sluiten</div>' +
      '<div class="knop donker" style="' + st([12, 516, 380, 38], "font-size:15px;border-radius:12px") + '">Camerabeeld naar voren</div>' +
      '</div>');
    return { el: el, r: { venster: o, banner: abs(o, [12, 120, 380, 130]), stoplive: abs(o, [12, 470, 186, 38]) } };
  }

  window.Studio = { dashboard: dashboard, kiezer: kiezer, verken: verken, editor: editor, verkenner: verkenner,
    vraag: vraag, melding: melding, bord: bord, overlay: overlay, paneel: paneel, BALKEN: BALKEN };
})();
