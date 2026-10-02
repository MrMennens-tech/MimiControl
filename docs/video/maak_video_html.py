"""
Bouwt docs/video/studio-uitleg/index.html (HyperFrames-compositie) uit de
scène-gegevens hieronder. Pas teksten of tijden hier aan en draai opnieuw:

    python docs\\video\\maak_video_html.py

De video heeft Nederlandse ondertitels en geen spraak. Het voorleesscript
staat in docs\\video\\voorleesscript.md.
"""

import os
import shutil
from PIL import Image

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HIER, "studio-uitleg")
ASSETS = os.path.join(PROJ, "assets")
os.makedirs(ASSETS, exist_ok=True)
LOGO = os.path.join(HIER, "..", "..", "app_v2", "assets", "Mennenstech_logo_wit.png")
if os.path.exists(LOGO):
    shutil.copy(LOGO, os.path.join(ASSETS, "logo.png"))

TEAL = "#4DB8BE"
DONKER = "#062D36"
GEEL = "#FFD400"

# Beeldvak links (px); tekstvak rechts
BEELD_X, BEELD_B, BEELD_H = 80, 1080, 780
TEKST_X, TEKST_B = 1230, 620


def maat(naam):
    with Image.open(os.path.join(ASSETS, naam)) as im:
        return im.size


def passend(naam):
    w, h = maat(naam)
    s = min(BEELD_B / w, BEELD_H / h)
    return int(w * s), int(h * s)


# Elke scène: id, begin, duur, titel, stappen (tekst), beeld(en), markeringen
# markering = (begin t.o.v. scène, einde, x1, y1, x2, y2) in fracties van het beeld
SCENES = [
    dict(id="s2", start=22, dur=20, nr="1", titel="Starten", beeld="01-dashboard.png",
         stappen=["Dubbelklik op “Start MimiControl Studio v2.bat”",
                  "Klik op Ja bij de Windows-melding",
                  "Controleer: Beheerder: ja"],
         marks=[(9.5, 19, 0.7175, 0.107, 0.9725, 0.269)]),
    dict(id="s3", start=42, dur=18, nr="2", titel="Kies je gezichtsbewegingen",
         beeld="02-kies-bewegingen.png",
         stappen=["Klik op “Mimiek verkennen”",
                  "Vink aan wat je wilt gebruiken",
                  "Snelle keuzes: bolle mond, tong uitsteken",
                  "Klik op Toepassen"],
         marks=[(7, 12, 0.085, 0.849, 0.463, 0.889), (12.5, 17.5, 0.514, 0.941, 0.633, 0.983)]),
    dict(id="s4", start=60, dur=20, nr="3", titel="Neem je beweging op",
         beeld="03-verkennen.png",
         stappen=["Klik op Opname starten",
                  "Maak je beweging een paar keer",
                  "Klik op Opname stoppen",
                  "Klik op Trigger maken"],
         marks=[(14, 19, 0.0, 0.85, 0.25, 1.0)]),
    dict(id="s5", start=80, dur=20, nr="4", titel="Toets en drempel instellen",
         beeld="05-trigger-editor.png",
         stappen=["Geef de trigger een naam",
                  "Kies de toets die Studio indrukt",
                  "Zet de drempel iets onder je gemeten waarde",
                  "Klik op Opslaan"],
         marks=[(5, 9.5, 0.025, 0.106, 0.43, 0.195), (10, 15.5, 0.69, 0.388, 0.875, 0.549),
                (16, 19.5, 0.694, 0.927, 0.828, 0.98)]),
    dict(id="s6", start=100, dur=22, nr="5", titel="Live gebruiken",
         beeld="06-live-camerabeeld.png", beeld2="07-live-toets-verstuurd.png", wissel=14,
         stappen=["Zet Communicator 5 op Vensterweergave",
                  "Klik op Communicator 5: dat is het actieve venster",
                  "Start Live en maak je beweging",
                  "Het label toont de verstuurde toets"],
         marks=[]),
    dict(id="s7", start=122, dur=16, nr="6", titel="Stoppen",
         beeld="06-live-camerabeeld.png", beeld2="08-live-stoppen.png", wissel=7,
         stappen=["Klik op de X rechtsboven",
                  "Klik nogmaals om te stoppen",
                  "Of gebruik Stop live of de toets Q"],
         marks=[(1.5, 6.5, 0.93, 0.0, 1.0, 0.13)]),
]


def beeld_html(sc):
    w, h = passend(sc["beeld"])
    x = BEELD_X + (BEELD_B - w) // 2
    y = (1080 - h) // 2
    kader = (f'<div class="beeld" id="{sc["id"]}-beeld" '
             f'style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">'
             f'<img src="assets/{sc["beeld"]}" alt="">')
    if sc.get("beeld2"):
        kader += f'<img class="tweede" id="{sc["id"]}-beeld2" src="assets/{sc["beeld2"]}" alt="">'
    for i, (t0, t1, x1, y1, x2, y2) in enumerate(sc["marks"]):
        kader += (f'<div class="mark" id="{sc["id"]}-m{i}" style="left:{x1*100:.2f}%;top:{y1*100:.2f}%;'
                  f'width:{(x2-x1)*100:.2f}%;height:{(y2-y1)*100:.2f}%"></div>')
    kader += "</div>"
    return kader


def scene_html(sc):
    stappen = "".join(
        f'<li id="{sc["id"]}-st{i}"><span class="num">{i+1}</span><span class="tx">{t}</span></li>'
        for i, t in enumerate(sc["stappen"]))
    return f'''
    <div class="clip scene" id="{sc["id"]}" data-start="{sc["start"]}" data-duration="{sc["dur"]}" data-track-index="1">
      {beeld_html(sc)}
      <div class="tekst" style="left:{TEKST_X}px;width:{TEKST_B}px">
        <div class="badge" id="{sc["id"]}-badge">Stap {sc["nr"]} van 6</div>
        <h2 id="{sc["id"]}-titel">{sc["titel"]}</h2>
        <ol>{stappen}</ol>
      </div>
    </div>'''


def animaties():
    r = []
    for sc in SCENES:
        s, d, i = sc["start"], sc["dur"], sc["id"]
        r.append(f'tl.fromTo("#{i}-beeld", {{opacity:0, x:-50}}, {{opacity:1, x:0, duration:0.7, ease:"power2.out"}}, {s}+0.2);')
        r.append(f'tl.fromTo("#{i}-badge", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.5}}, {s}+0.5);')
        r.append(f'tl.fromTo("#{i}-titel", {{opacity:0, y:24}}, {{opacity:1, y:0, duration:0.6, ease:"power2.out"}}, {s}+0.7);')
        n = len(sc["stappen"])
        # stappen verdeeld over de scène; laatste blijft tot het einde in beeld
        gap = (d - 3.5) / max(n, 1) * 0.85
        for k in range(n):
            t = s + 1.8 + k * gap
            r.append(f'tl.fromTo("#{i}-st{k}", {{opacity:0, x:40}}, {{opacity:1, x:0, duration:0.5, ease:"power2.out"}}, {t:.2f});')
        if sc.get("beeld2"):
            r.append(f'tl.fromTo("#{i}-beeld2", {{opacity:0}}, {{opacity:1, duration:0.6}}, {s + sc["wissel"]});')
        for m, (t0, t1, *_rest) in enumerate(sc["marks"]):
            r.append(f'tl.fromTo("#{i}-m{m}", {{opacity:0, scale:1.08}}, {{opacity:1, scale:1, duration:0.4, ease:"back.out(2)"}}, {s + t0});')
            r.append(f'tl.to("#{i}-m{m}", {{opacity:0, duration:0.35}}, {s + t1});')
        r.append(f'tl.to("#{i}", {{opacity:0, duration:0.5}}, {s + d - 0.5});')
    return "\n      ".join(r)


HTML = f'''<!doctype html>
<html lang="nl">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: {DONKER}; }}
      #root {{ position: relative; width: 1920px; height: 1080px; overflow: hidden;
        background: radial-gradient(1200px 800px at 25% 20%, #0B4551 0%, {DONKER} 70%);
        font-family: "Segoe UI", Inter, ui-sans-serif, system-ui, sans-serif; color: #fff; }}
      .scene {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }}
      .beeld {{ position: absolute; border-radius: 18px; overflow: hidden;
        box-shadow: 0 30px 80px rgba(0,0,0,.55); border: 2px solid rgba(255,255,255,.18); background:#fff; }}
      .beeld img {{ position: absolute; left: 0; top: 0; width: 100%; height: 100%; display: block; }}
      .beeld .tweede {{ opacity: 0; }}
      .mark {{ position: absolute; border: 6px solid {GEEL}; border-radius: 12px; opacity: 0;
        box-shadow: 0 0 0 4px rgba(255,212,0,.25), 0 0 40px rgba(255,212,0,.7); }}
      .tekst {{ position: absolute; top: 50%; transform: translateY(-50%); }}
      .badge {{ display: inline-block; background: {TEAL}; color: {DONKER}; font-weight: 700;
        font-size: 26px; padding: 8px 22px; border-radius: 999px; margin-bottom: 22px; }}
      h2 {{ font-size: 62px; line-height: 1.08; font-weight: 700; margin-bottom: 40px; letter-spacing: -0.01em; }}
      ol {{ list-style: none; }}
      li {{ display: flex; gap: 20px; align-items: flex-start; font-size: 38px; line-height: 1.28;
        margin-bottom: 26px; }}
      .num {{ flex: 0 0 52px; height: 52px; border-radius: 50%; background: #fff; color: {DONKER};
        font-weight: 700; font-size: 30px; display: flex; align-items: center; justify-content: center; margin-top: 2px; }}
      .tx {{ flex: 1; }}
      .vol {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }}
      .logo {{ width: 220px; margin-bottom: 40px; }}
      .groot {{ font-size: 112px; font-weight: 800; letter-spacing: -0.02em; }}
      .sub {{ font-size: 46px; color: {TEAL}; margin-top: 18px; }}
      .rij {{ display: flex; align-items: center; gap: 40px; margin-top: 60px; }}
      .kaart {{ width: 440px; height: 360px; border-radius: 24px; background: rgba(255,255,255,.08);
        border: 2px solid rgba(255,255,255,.2); display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 30px; }}
      .kaart .k1 {{ font-size: 40px; font-weight: 700; margin-bottom: 14px; }}
      .kaart .k2 {{ font-size: 34px; color: #BFE7EA; line-height: 1.25; }}
      .pijl {{ font-size: 90px; color: {TEAL}; }}
      .toets {{ font-size: 60px; font-weight: 800; background: #fff; color: {DONKER}; padding: 14px 44px;
        border-radius: 18px; border-bottom: 10px solid #9fc9cd; margin-bottom: 14px; }}
      .tips {{ display: flex; gap: 40px; margin-top: 54px; }}
      .tip {{ width: 520px; min-height: 360px; border-radius: 24px; background: rgba(255,255,255,.09);
        border: 2px solid rgba(255,255,255,.2); padding: 36px; text-align: left; }}
      .tip .t1 {{ font-size: 38px; font-weight: 700; color: {GEEL}; margin-bottom: 18px; line-height: 1.2; }}
      .tip .t2 {{ font-size: 34px; line-height: 1.3; color: #E7F6F7; }}
      h1.kop {{ font-size: 76px; font-weight: 800; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="158" data-width="1920" data-height="1080">

      <!-- 0. titel -->
      <div class="clip scene" id="s0" data-start="0" data-duration="6" data-track-index="1">
        <div class="vol">
          <img class="logo" id="s0-logo" src="assets/logo.png" alt="">
          <div class="groot" id="s0-titel">MimiControl Studio</div>
          <div class="sub" id="s0-sub">Met je gezicht toetsen indrukken</div>
        </div>
      </div>

      <!-- 1. wat is het -->
      <div class="clip scene" id="s1" data-start="6" data-duration="16" data-track-index="1">
        <div class="vol">
          <h1 class="kop" id="s1-kop">Zo werkt het</h1>
          <div class="rij">
            <div class="kaart" id="s1-k1"><div class="k1">Jij</div><div class="k2">Studio kijkt via de webcam naar je gezicht</div></div>
            <div class="pijl" id="s1-p1">&rarr;</div>
            <div class="kaart" id="s1-k2"><div class="k1">Je beweging</div><div class="k2">bijvoorbeeld: kaak open</div></div>
            <div class="pijl" id="s1-p2">&rarr;</div>
            <div class="kaart" id="s1-k3"><div class="toets">Spatie</div><div class="k2">Studio drukt de toets in, bijvoorbeeld in Communicator 5</div></div>
          </div>
        </div>
      </div>
{"".join(scene_html(sc) for sc in SCENES)}

      <!-- 8. werkt het niet -->
      <div class="clip scene" id="s8" data-start="138" data-duration="14" data-track-index="1">
        <div class="vol">
          <h1 class="kop" id="s8-kop">Werkt het niet?</h1>
          <div class="tips">
            <div class="tip" id="s8-t1"><div class="t1">De toets komt niet aan</div><div class="t2">Start Studio opnieuw en klik Ja bij de Windows-melding. Controleer: Beheerder: ja.</div></div>
            <div class="tip" id="s8-t2"><div class="t1">De camera werkt niet</div><div class="t2">Sluit andere camera-apps en een oude Studio. Start Studio daarna opnieuw.</div></div>
            <div class="tip" id="s8-t3"><div class="t1">Het beeld staat stil</div><div class="t2">Zet Communicator 5 op Vensterweergave in plaats van volledig scherm.</div></div>
          </div>
        </div>
      </div>

      <!-- 9. einde -->
      <div class="clip scene" id="s9" data-start="152" data-duration="6" data-track-index="1">
        <div class="vol">
          <img class="logo" id="s9-logo" src="assets/logo.png" alt="">
          <div class="groot" id="s9-t1" style="font-size:80px">Meer uitleg in de handleiding</div>
          <div class="sub" id="s9-t2">Handleiding-MimiControl-Studio-v2.pdf</div>
        </div>
      </div>
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});

      // 0 titel
      tl.fromTo("#s0-logo", {{opacity:0, y:-20}}, {{opacity:1, y:0, duration:0.7}}, 0.2);
      tl.fromTo("#s0-titel", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.8, ease:"power2.out"}}, 0.7);
      tl.fromTo("#s0-sub", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.7}}, 1.5);
      tl.to("#s0", {{opacity:0, duration:0.5}}, 5.5);

      // 1 concept
      tl.fromTo("#s1-kop", {{opacity:0, y:-20}}, {{opacity:1, y:0, duration:0.6}}, 6.3);
      tl.fromTo("#s1-k1", {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.7, ease:"power2.out"}}, 7.5);
      tl.fromTo("#s1-p1", {{opacity:0}}, {{opacity:1, duration:0.4}}, 9.2);
      tl.fromTo("#s1-k2", {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.7, ease:"power2.out"}}, 10);
      tl.fromTo("#s1-p2", {{opacity:0}}, {{opacity:1, duration:0.4}}, 12);
      tl.fromTo("#s1-k3", {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.7, ease:"power2.out"}}, 12.8);
      tl.to("#s1", {{opacity:0, duration:0.5}}, 21.5);

      {animaties()}

      // 8 tips
      tl.fromTo("#s8-kop", {{opacity:0, y:-20}}, {{opacity:1, y:0, duration:0.6}}, 138.3);
      tl.fromTo("#s8-t1", {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.7}}, 139.5);
      tl.fromTo("#s8-t2", {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.7}}, 142.5);
      tl.fromTo("#s8-t3", {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.7}}, 145.5);
      tl.to("#s8", {{opacity:0, duration:0.5}}, 151.5);

      // 9 einde
      tl.fromTo("#s9-logo", {{opacity:0, y:-20}}, {{opacity:1, y:0, duration:0.7}}, 152.3);
      tl.fromTo("#s9-t1", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.8}}, 152.9);
      tl.fromTo("#s9-t2", {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.7}}, 153.8);

      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
'''

with open(os.path.join(PROJ, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML)
print("index.html geschreven")
