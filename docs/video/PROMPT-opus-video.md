# Prompt voor Opus 5.5: professionele uitlegvideo MimiControl Studio v2

**Zo gebruik je dit**
1. Open een nieuwe sessie in de map `D:\_MimiControl\mimicontrol` en kies in de modelkiezer **Opus 5.5**.
2. Plak alles onder de streep (vanaf "Je maakt...") als eerste bericht.
3. Antwoord op de vragen die hij mogelijk stelt (voice-over, muziek). Hij vraagt toestemming voor
   downloads; dat is de bedoeling.

Er is niets extra aan te zetten: de HyperFrames-skills staan in `~\.claude\skills`. Alleen Node.js 22
of nieuwer is nodig (jouw pc heeft Node 18; Opus vraagt dan om een portable Node 22 te downloaden).

---

Je maakt een **professionele, verzorgde uitlegvideo (Nederlands)** over MimiControl Studio v2, voor
collega's die het programma zelf moeten gaan gebruiken. Een eerste versie bestaat al
(`docs/video/Uitleg-MimiControl-Studio-v2.mp4`, gemaakt met `docs/video/maak_video_html.py`). Die is
**te matig**: kleine, statische screenshots met een tekst die ernaast inschuift, nauwelijks beweging,
de interface is onleesbaar klein, geen sfeer of ritme. Maak er een echt goed product van. Begin niet
bij die versie; gebruik alleen de inhoud en de feiten hieronder.

## Wat is MimiControl Studio?
Windows-programma van Mennens.Tech. Het kijkt via de webcam naar je gezicht (MediaPipe) en drukt een
toets in (SendInput) als je een bepaalde gezichtsbeweging maakt. Doel: iemand met beperkte
motoriek (bijvoorbeeld een leerling met spasmen) bedient een programma, vooral **Communicator 5**
(Tobii Dynavox). Doelgroep van de video: collega's en begeleiders, niet technisch.

## Harde feiten (klopt exact; verzin niets erbij)
- **Starten:** dubbelklik op **`MimiControl Studio v2.exe`** in de map van Studio. Er is **geen** `.bat`
  nodig. Studio vraagt zelf: "Studio werkt met Communicator 5 alleen als het als beheerder draait. Nu
  opnieuw starten als beheerder?" Klik **Ja**; daarna volgt de Windows-melding, ook **Ja**.
- Controle: in het dashboard staat bovenaan de kaart **Communicator 5** met **"Beheerder: ja"**.
- **Communicator 5 werkt ook op volledig scherm.** Zeg dus *niet* dat Vensterweergave nodig is.
  Hooguit: "staat het beeld stil? probeer Vensterweergave".
- Toetsen gaan altijd naar het **actieve venster** (waar je het laatst op klikte). Klik dus op
  Communicator 5 voordat je begint.
- **Trigger maken, in 4 stappen:**
  1. Dashboard, knop **Mimiek verkennen**. Scherm "Kies je gezichtsbewegingen" met groepen (Mond, Ogen,
     Wenkbrauwen, Kaak, Wangen, Neus); knoppen **Alles aanvinken**, **Alles uitvinken**, snelle keuzes
     **Bolle mond / tuiten** en **Tong uitsteken (benadering)**, dan **Toepassen**. De tong kan niet los
     gemeten worden; de benadering is "Kaak open" + "Lip-trechter".
  2. Verkenvenster met camerabeeld en balkjes. Knoppen onderaan: **Opname starten [spatie]** →
     (beweging maken) → **Opname stoppen** → **Trigger maken [enter]**. Verder **Opnieuw opnemen**,
     **Beweging kiezen [f]** (bewegingen toevoegen/weghalen) en **Sluiten [q]**. Bovenin staat
     "Stap 1: klik Opname starten" / "Stap 2: klik Trigger maken". De sterkste beweging krijgt een gele balk.
  3. Scherm **Nieuwe trigger**: Naam, **Actie** (toets uit lijst of **Toets opnemen**), kolommen
     Beweging / Gemeten / Drempel / Waarde. Drempel = hoe sterk je de beweging moet maken; zet hem iets
     onder de gemeten waarde. **Opslaan**.
  4. De trigger staat als kaart op het dashboard (naam, toets-label, bewegingen met drempel).
- **Live:** knop **Live modus starten**. Rechtsboven verschijnt een klein camerabeeld (blijft boven andere
  programma's), naast een drempelpaneel met schakelaars per trigger. Bij elke trigger toont het beeld
  linksonder een label **"Verstuurd: Spatie"** (twee seconden, in de kleur van de trigger). Het
  drempelpaneel toont **"Actief venster: <naam>"**.
- **Stoppen:** kleine **X** rechtsboven in het camerabeeld. Eerste klik: rode knop **"Stoppen? Klik
  nogmaals"**; tweede klik (binnen 3 seconden) stopt. Zo stopt het niet per ongeluk. Ook: knop **Stop
  live** in het drempelpaneel of toets **Q**.
- **Werkt het niet?** Toets komt niet aan: Studio opnieuw starten en Ja kiezen (beheerder).
  Camera werkt niet: andere camera-apps of een oude Studio sluiten. Melding "draait al": de andere Studio
  sluiten.
- Merk: Mennens.Tech; donkerteal `#062D36`, accent `#4DB8BE`; logo
  `app_v2/assets/Mennenstech_logo_wit.png` en `Mennenstech_logo.png`.

## Beeldmateriaal dat al bestaat (alleen als bron of referentie)
- `docs/afbeeldingen/01…08*.png`: echte screenshots (demo-gegevens, geen echt gezicht). Gemaakt met
  `docs/maak_screenshots.py` (opnieuw te maken, ook in andere formaten of scherper).
- `docs/Handleiding-MimiControl-Studio-v2.docx`/`.pdf`: inhoud en volgorde (lees `docs/video/voorleesscript.md`).
- Broncode van de schermen: `app_v2/` (CustomTkinter-interface en OpenCV-vensters), voor exacte teksten.

## Kwaliteitslat (dit moet het verschil maken)
- **Geen losse screenshots in een kader met tekst ernaast.** Bouw de interface van Studio **na in HTML/CSS**
  (scherp op 1080p en 4K, exacte Nederlandse teksten en kleuren uit de screenshots) en laat hem leven:
  een **geanimeerde muiscursor** die klikt (klik-rimpel), **zoom/pan naar het relevante deel**, knoppen
  die indrukken, balkjes die uitslaan, vinkjes die aanvinken, schuifbalken die bewegen, het label
  "Verstuurd: Spatie" dat verschijnt. Gebruik zoom-ins zodat tekst altijd goed leesbaar is.
- **Rustig, professioneel ritme**: ongeveer 2 tot 3 minuten; één idee per scène; maximaal één korte regel
  ondertitel tegelijk (groot, hoog contrast, binnen de veilige zone); hoofdstuktitels met subtiele
  motion; consequente easing; vloeiende, doelgerichte overgangen (geen willekeurige effecten).
- **Visuele identiteit**: Mennens.Tech-huisstijl, één lettertype-familie, ruime witruimte, zachte schaduw
  en diepte. Een korte, verzorgde intro en outro met logo.
- **Het concept uitleggen met beeld**, niet met tekst: gezicht (neutraal silhouet of illustratie, **geen
  echt gezicht**) maakt een beweging, een meter slaat uit, een toets verschijnt, Communicator 5 reageert
  (een gestileerde mock-up van een communicatieboek is prima; geen merklogo's nabootsen).
- **Geluid**: kies ofwel een subtiele muziekbed en zachte klik-geluidjes (via de media-use skill, licht
  en rechtenvrij), ofwel stilte. Er is geen Nederlandse TTS-stem lokaal (Kokoro kent geen Nederlands).
  Vraag de gebruiker of er voice-over komt: dan maak je eerst een voorleesscript met tijdstippen en laat
  je de video daarop timen. Altijd Nederlandse ondertitels.
- **Toegankelijk**: contrast minimaal WCAG AA, tekst nooit kleiner dan circa 40 px op 1080p, geen flitsende
  beelden.

## Werkwijze
1. Lees `docs/video/PROMPT-opus-video.md` (dit bestand), `docs/video/voorleesscript.md` en kijk naar de
   screenshots. Start met `/hyperframes` (intent-laag) en volg de workflow `general-video` in
   **companion-modus met storyboard**: eerst een plan en een storyboard (scènes, tijden, motion per scène,
   zoom-doelen) laten goedkeuren, dan bouwen. Kondig het plan aan; stel maximaal drie vragen.
2. Gebruik de HyperFrames-skills (`hyperframes`, `-core`, `-animation`, `-keyframes`, `-creative`,
   `-audio`, `-registry`, `media-use`). Zoek in de catalogus (`npx hyperframes catalog --query ...`) naar
   bestaande blokken voor cursor/klik-effecten, zoom en onderschriften vóór je iets zelf bouwt.
3. Node.js **22 of nieuwer** is nodig voor `npx hyperframes`; de pc heeft Node 18. Vraag toestemming voor
   een **portable Node 22** (zip van nodejs.org, controleer de SHA256, uitpakken in een tijdelijke map
   buiten de repo, alleen daarvoor gebruiken, daarna opruimen). Wijzig niets aan de systeem-Node.
4. Bouw in `docs/video/studio-uitleg-v2/` (nieuwe map; laat de oude staan). Maak het genereerbaar (een
   script met scène-gegevens, zoals `maak_video_html.py`) zodat teksten later makkelijk te wijzigen zijn.
5. Controleer: `npx hyperframes check` (0 fouten), `snapshot` op sleutelmomenten en bekijk de beelden
   echt; fix leesbaarheid, uitlijning en timing. Render dan naar
   `docs/video/Uitleg-MimiControl-Studio-v2.mp4` (1920x1080, 30 fps) en controleer enkele frames uit het MP4.
6. **Commit niet en push niet** zonder dat de gebruiker erom vraagt. `*.mp4` staat in `.gitignore`.

## Opleveren
- De MP4, de bronbestanden, een bijgewerkt `voorleesscript.md` en een korte samenvatting (wat je
  gekozen hebt en waarom). Vermeld eerlijk wat je niet kon controleren.
