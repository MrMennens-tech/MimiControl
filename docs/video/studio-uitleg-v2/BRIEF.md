---
workflow: general-video
flow: companion
storyboard: yes
message: "Met Studio bedien je Communicator 5 met een gezichtsbeweging, in vier stappen ingesteld."
audience: collega's en begeleiders, niet technisch
language: nl
aspect: 16:9
format: 1920x1080
fps: 30
length: ongeveer 2,5 tot 3 minuten
---

## Intent

Professionele uitlegvideo (Nederlands) over MimiControl Studio v2 voor collega's die het programma
zelf gaan gebruiken. Opvolger van `docs/video/Uitleg-MimiControl-Studio-v2.mp4` (te statisch, kleine
screenshots). Volledige opdracht: `docs/video/PROMPT-opus-video.md`.

Concept: de interface van Studio wordt in HTML/CSS nagebouwd (exacte teksten en kleuren uit `app_v2/`)
en leeft: cursor met klik-rimpel, zoom/pan naar het relevante deel, knoppen die indrukken, balkjes die
uitslaan, vinkjes, schuifbalken, "Verstuurd: Spatie". Één idee per scène, één regel ondertitel.

## Assets

- Logo Mennens.Tech: `app_v2/assets/Mennenstech_logo_wit.png`, `Mennenstech_logo.png`.
- Screenshots `docs/afbeeldingen/01..08` alleen als referentie.

## Customizations

- Voice-over: HeyGen-stem "Maarten de Vries" (Nederlands), gekozen door de gebruiker (2026-10-02).
- Naamgeving: "MimiControl" / "het programma", niet steeds "Studio" (gebruiker).
- Gezicht: geïllustreerde persoon, geen ei-vorm (gebruiker).
- Altijd Nederlandse ondertitels.
- Geluid: subtiel, rechtenvrij muziekbed en zachte klikgeluidjes.
- Muziek: HeyGen-bibliotheek, track eb9729536df94069a5c8313bff330626 (180 s), zacht onder de stem; klikgeluiden uit media-use (Pixabay-licentie).
- Huisstijl: donkerteal `#062D36`, accent `#4DB8BE`; lettertype Open Sans (OFL, meegeleverd; Segoe UI mag niet worden meegeleverd).

## Notes

- Feiten exact volgens `PROMPT-opus-video.md`; niets verzinnen. Communicator 5 werkt ook op volledig scherm.
- Gegenereerd door `maak_video.py` in deze map; teksten en tijden staan daar.
- Render: `docs/video/Uitleg-MimiControl-Studio-v2.mp4`, 1920x1080, 30 fps. Niet committen zonder vraag.
- Node 22 portable: `D:\nodejs22\node-v22.19.0-win-x64` (systeem-Node is 18).
