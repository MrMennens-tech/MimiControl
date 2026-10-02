---
workflow: general-video
flow: automation
storyboard: no
---

## Intent

Uitlegvideo (circa 2,5 minuten, 1920x1080, Nederlands) voor collega's: hoe gebruik je MimiControl
Studio v2 om met je gezicht toetsen in te drukken, vooral in Communicator 5. Stappen: starten,
bewegingen kiezen, opnemen, trigger instellen, live gebruiken, stoppen, probleemoplossing.

## Assets

- Schermafbeeldingen uit `docs/afbeeldingen` (gemaakt met `docs/maak_screenshots.py`; demo-gegevens en
  een neutraal silhouet, geen echt gezicht).
- Logo Mennens.Tech (`app_v2/assets/Mennenstech_logo_wit.png`).

## Customizations

- Nederlandse ondertitels, geen spraak (er is lokaal geen Nederlandse stem). Voorleesscript staat in
  `docs/video/voorleesscript.md` voor wie zelf wil inspreken.
- Huisstijl Studio: donkerteal `#062D36`, accent `#4DB8BE`, markeringen geel.

## Notes

- De compositie wordt gegenereerd door `docs/video/maak_video_html.py`; pas teksten en tijden daar aan.
- Render met Node.js 22 of nieuwer. Uitvoer: `docs/video/Uitleg-MimiControl-Studio-v2.mp4`
  (`*.mp4` staat in `.gitignore`).
