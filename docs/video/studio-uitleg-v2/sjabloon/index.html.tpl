<!doctype html>
<html lang="nl">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <!-- Sjabloon voor index.html: maak_video.py vult de {{...}}-velden in. -->
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <link rel="stylesheet" href="lib/ui.css" />
    <script src="lib/tijden.js"></script>
    <script src="lib/gezicht.js"></script>
    <script src="lib/ui.js"></script>
    <script src="lib/studio.js"></script>
    <style>
      @font-face { font-family: "Mimi Sans"; src: url("assets/fonts/open-sans-400.woff2") format("woff2"); font-weight: 400; }
      @font-face { font-family: "Mimi Sans"; src: url("assets/fonts/open-sans-600.woff2") format("woff2"); font-weight: 600; }
      @font-face { font-family: "Mimi Sans"; src: url("assets/fonts/open-sans-700.woff2") format("woff2"); font-weight: 700; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #062D36; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Mimi Sans", sans-serif;
        background: #062D36; }
      #root > div[data-composition-src] { position: absolute; inset: 0; }
      #achter { position: absolute; inset: 0; overflow: hidden; }
      #achter .gloed { position: absolute; left: -400px; top: -500px; width: 2000px; height: 1700px; border-radius: 50%;
        background: radial-gradient(closest-side, rgba(77, 184, 190, 0.20), rgba(77, 184, 190, 0.05) 60%, rgba(6, 45, 54, 0) 100%); }
      #achter .gloed2 { position: absolute; right: -500px; bottom: -700px; width: 1600px; height: 1400px; border-radius: 50%;
        background: radial-gradient(closest-side, rgba(10, 64, 80, 0.9), rgba(6, 45, 54, 0) 100%); }
      #achter .raster { position: absolute; inset: -60px; opacity: 0.07;
        background-image: radial-gradient(circle, #68CCD1 1.6px, rgba(0, 0, 0, 0) 2px); background-size: 44px 44px; }
      #achter .merk { position: absolute; right: -160px; bottom: -200px; width: 900px; height: 858px; opacity: 0.045; }
      .cap { position: absolute; left: 0; right: 0; bottom: 58px; display: flex; justify-content: center; z-index: 90; }
      .cap-tekst { display: block; max-width: 1760px; font-size: 48px; font-weight: 600; line-height: 1.25; color: #FFFFFF;
        background: rgba(2, 22, 28, 0.88); padding: 12px 34px 14px; border-radius: 16px; white-space: nowrap;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="{{DUUR}}">
      <div id="achter">
        <div class="gloed"></div>
        <div class="gloed2"></div>
        <div class="raster"></div>
        <img class="merk" src="assets/Mennenstech_logo_wit.png" alt="" />
      </div>

{{SLOTS}}

{{ONDERTITELS}}

{{AUDIO}}
    </div>

    <script>
      (function () {
        var tl = gsap.timeline({ paused: true });
        var duur = {{DUUR}};
        // achtergrond: trage, eindige drift (geen oneindige herhaling)
        tl.fromTo("#achter .gloed", { x: 0, y: 0, scale: 1 }, { x: 260, y: 120, scale: 1.12, duration: duur, ease: "sine.inOut" }, 0);
        tl.fromTo("#achter .raster", { x: 0, y: 0 }, { x: -44, y: -44, duration: duur, ease: "none" }, 0);
        tl.fromTo("#achter .merk", { rotation: -4, y: 0 }, { rotation: 4, y: -40, duration: duur, ease: "sine.inOut" }, 0);
        // ondertitels: zachte in/uit-fade binnen het eigen tijdvenster
        document.querySelectorAll(".cap").forEach(function (cap) {
          var s = parseFloat(cap.getAttribute("data-start")), d = parseFloat(cap.getAttribute("data-duration"));
          var tx = cap.querySelector(".cap-tekst");
          tl.fromTo(tx, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.22, ease: "power2.out", immediateRender: false }, s);
          tl.fromTo(tx, { opacity: 1 }, { opacity: 0, duration: 0.18, ease: "power1.in", immediateRender: false }, s + d - 0.18);
        });
        window.__timelines["main"] = tl;
      })();
    </script>
  </body>
</html>
