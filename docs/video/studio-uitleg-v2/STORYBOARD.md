---
format: 1920x1080
duration: 164s
message: "Met Studio bedien je Communicator 5 met een gezichtsbeweging; instellen doe je in vier stappen."
arc: Belofte → Hoe het werkt → Starten → Vier stappen → Live → Stoppen → Hulp → Logo
audience: collega's en begeleiders, niet technisch
mode: collaborative
---

# Storyboard: Uitleg MimiControl Studio v2 (v2, gebouwd)

## Beslissingen

- **Boodschap:** met een gezichtsbeweging druk je een toets in Communicator 5; instellen kost vier stappen.
- **Publiek en boog:** collega's en begeleiders. Belofte → concept → starten → 4 stappen → live → stoppen → hulp → logo.
- **Formaat:** 16:9, 1920x1080, 30 fps, circa 3:05. Voice-over: Nederlands (stem nog te bevestigen),
  altijd ondertitels. Muziekbed zacht, klikgeluidjes bij elke klik. Ondertitels in de onderste band
  (y 900–1010); belangrijke inhoud blijft in de bovenste 83 %.
- **Rode draad (spine):** de toets **Spatie**. Hij verschijnt in het concept (F02), wordt gekozen in de
  trigger (F06), staat als label op de kaart (F07) en komt terug als "Verstuurd: Spatie" in live (F08)
  waarna het bord reageert, net als in F02 (callback).
- **Camera:** één virtuele camera over een nagebouwde Studio. Elke zoom eindigt zo dat tekst ≥ 40 px is.
- **Huisstijl:** podium donkerteal `#062D36`, accent `#4DB8BE`, licht teal `#68CCD1`; Studio-vlakken
  `#F2F2F7` / `#FFFFFF` / rood `#E05A50`; trigger-geel `#FFD60A`. Eén familie: Segoe UI (zoals Studio)
  in 400/600/700. Radius 12 (Studio). Easing: `power3.out` voor binnenkomen, `power2.inOut` voor
  camera en cursor, `power2.in` voor uitgaan. Klik = knop 0,96 schaal + rimpel 0,45 s.
- **Verboden:** geen screenshots in een kader, geen gloed of neon, geen flitsen, geen merklogo's van
  Tobii/Windows nabootsen, geen echt gezicht, geen gradient-tekst, geen twee regels ondertitel.
  Bewegingsfouten om te vermijden: de diashow (elke scène een nieuwe kaart zonder verband) en de
  screensaver (beweging die niets uitlegt).
- **Rustmoment:** F07, de triggerkaart landt en alles staat 1,5 s stil.
- **Waarheid:** de schermen zijn nagebouwd uit `app_v2/` met exacte teksten; het gezicht is een
  illustratie; "Communicator 5" is een gestileerd communicatiebord zonder logo; de Windows-melding is
  een neutrale kaart zonder Windows-huisstijl.


## Gebouwd (definitieve tijden)

Gegenereerd uit `lib/tijden.js` na de build; de composities zijn leidend.

| Scène | Start | Duur |
|---|---|---|
| f01-intro | 0:00.0 | 7.0 s |
| f02-concept | 0:07.0 | 16.6 s |
| f03-starten | 0:23.6 | 20.1 s |
| f04-kiezen | 0:43.7 | 16.4 s |
| f05-opnemen | 1:00.0 | 15.1 s |
| f06-trigger | 1:15.1 | 15.3 s |
| f07-kaart | 1:30.5 | 7.4 s |
| f08-live | 1:37.9 | 24.4 s |
| f09-stoppen | 2:02.3 | 16.6 s |
| f10-hulp | 2:18.8 | 17.8 s |
| f11-outro | 2:36.6 | 7.3 s |

Totaal: 2:43,9. Voice-over: HeyGen "Maarten de Vries". Muziek: HeyGen-bibliotheek (eb9729536df94069a5c8313bff330626).

## Wijzigingen ten opzichte van v1

- Gezicht: verzorgde illustratie (geen ei-vorm), op verzoek van de gebruiker.
- Naamgeving in de voice-over: "MimiControl" / "het programma" in plaats van steeds "Studio".
- Stap 1: het stuk over Tong uitsteken is eruit (gaf een verkeerd beeld: het is maar een benadering). De twee zinnen zijn uit de bestaande opname geknipt.
- Scène 10 is ingekort omdat het gratis HeyGen-stemtegoed op was.
- Live: het drempelpaneel verdwijnt achter Communicator 5 op volledig scherm (alleen het camerabeeld blijft vooraan, zoals in Studio).

## Frame 1 — Intro

- scene: Logo bouwt op, titel "MimiControl Studio v2", regel "Toetsen indrukken met je gezicht"
- duration: 6s
- transition_in: cut
- status: animated
- voiceover: "MimiControl Studio: toetsen indrukken met je gezicht."
- src: compositions/f01-intro.html

Logo-cirkel tekent zich (stroke-draw), "MENNENS.TECH" vervaagt in, titel schuift 24 px omhoog. Zeer
zachte ademende radiale gloed. Seam: titel schuift naar links weg, gezicht komt van rechts.

## Frame 2 — Zo werkt het

- scene: Gezicht → meter → toets Spatie → bord springt een vakje verder
- duration: 18s
- transition_in: push-left
- status: animated
- voiceover: "Studio kijkt via de webcam naar je gezicht. Maak je een bepaalde beweging, bijvoorbeeld je mond open, dan drukt Studio een toets in, zoals de spatiebalk. Zo bedien je Communicator 5 zonder toetsenbord."
- src: compositions/f02-concept.html

Drie stations op één rij: geïllustreerd gezicht (links), meter "Kaak open" met drempelstreep (midden),
toets "Spatie" (rechts), daaronder het bord. Kaak opent → balk stijgt over streep → toets duikt in →
gemarkeerd vakje springt door. Herhaalt één keer sneller.

## Frame 3 — Starten

- scene: Map met MimiControl Studio v2.exe → vraag beheerder → Ja → Windows-melding → Ja → "✓ Beheerder: ja"
- duration: 22s
- transition_in: crossfade
- status: animated
- voiceover: "Start Studio met een dubbelklik op MimiControl Studio v2 punt exe. Studio vraagt of het opnieuw mag starten als beheerder. Klik op Ja, en daarna ook op Ja bij de melding van Windows. Bovenaan het dashboard staat dan: Beheerder: ja."
- src: compositions/f03-starten.html

Hoofdstuktitel "Starten". Map-venster met bestand, cursor dubbelklikt (twee rimpels). Dialoog met
exacte tekst, zoom zodat tekst leesbaar is; cursor klikt Ja. Neutrale kaart "Windows-melding:
Wil je toestaan…" → Ja. Dashboard schuift in, camera zoomt op kaart Communicator 5.

## Frame 4 — Stap 1: Kies je gezichtsbewegingen

- scene: Mimiek verkennen → scherm "Kies je gezichtsbewegingen" → Alles uitvinken → Kaak aanvinken → Toepassen
- duration: 22s
- transition_in: zoom-through
- status: animated
- voiceover: "Stap één: klik op Mimiek verkennen en kies je gezichtsbewegingen. Vink aan wat je wilt gebruiken, bijvoorbeeld de kaak. Klik op Toepassen."
- src: compositions/f04-kiezen.html

Op het dashboard drukt de cursor "Mimiek verkennen"; camera duikt door de knop het keuzescherm in.
"Alles uitvinken" → vinkjes verdwijnen; lijst schuift naar groep Kaak; cursor klikt "Alles" → vier
vinkjes tikken aan. Toepassen.

## Frame 5 — Stap 2: Neem je beweging op

- scene: Verkenvenster: Opname starten → gezicht beweegt, balkjes slaan uit, Kaak open geel → Opname stoppen → Trigger maken
- duration: 22s
- transition_in: crossfade
- status: animated
- voiceover: "Stap twee: klik op Opname starten en maak je beweging een paar keer. De sterkste beweging krijgt een gele balk. Klik op Opname stoppen, en daarna op Trigger maken."
- src: compositions/f05-opnemen.html

Verkenvenster met camerabeeld (illustratie) en balkpaneel. Boven: "Stap 1: klik Opname starten" →
"Opname loopt: maak je beweging" (rood) → "Stap 2: klik Trigger maken" (geel). Knoppen wisselen exact
zoals in Studio.

## Frame 6 — Stap 3: Toets en drempel

- scene: Nieuwe trigger: naam typt, Actie Spatie, zoom op rij Kaak open (piek 0.62), schuif naar 0.50, Opslaan
- duration: 22s
- transition_in: crossfade
- status: animated
- voiceover: "Stap drie: geef de trigger een naam en kies de toets, bijvoorbeeld Spatie. De drempel is hoe sterk je de beweging moet maken. Zet hem iets onder de gemeten waarde. Klik op Opslaan."
- src: compositions/f06-trigger.html

Naamveld typt "Spatie met kaak". Actie-lijst klapt open, "Spatie" gekozen. Camera schuift naar de
rij Kaak open; een stippellijn markeert "piek 0.62", schuif zakt naar 0.50; waarde telt mee. Opslaan.

## Frame 7 — Stap 4: Klaar

- scene: De triggerkaart "Spatie met kaak" landt op het dashboard
- duration: 8s
- transition_in: crossfade
- status: animated
- voiceover: "Stap vier: je trigger staat nu als kaart op het dashboard."
- src: compositions/f07-kaart.html

Kaart zakt in de lege plek, gele bovenrand tekent zich, label "Spatie", rij "Kaak open > 0.50".
Rustmoment.

## Frame 8 — Live gebruiken

- scene: Live modus starten → bord op volledig scherm, camerabeeld + drempelpaneel rechtsboven → klik op bord → "Actief venster: Communicator 5" → beweging → "Verstuurd: Spatie" → bord springt
- duration: 26s
- transition_in: zoom-out
- status: animated
- voiceover: "Klik op Live modus starten. Rechtsboven verschijnt een klein camerabeeld; dat blijft boven je andere programma's. Klik nu op Communicator 5, want toetsen gaan altijd naar het actieve venster. Volledig scherm mag gewoon. Maak je beweging: linksonder in het camerabeeld zie je welke toets is verstuurd."
- src: compositions/f08-live.html

Callback op F02: hetzelfde bord, nu echt. Klik op bord → panel-banner wisselt naar "Actief venster:
Communicator 5". Zoom op camerabeeld: label "Verstuurd: Spatie" in geel, 2 s; bord springt verder.

## Frame 9 — Stoppen

- scene: X rechtsboven → rood "Stoppen? Klik nogmaals" → tweede klik → beeld sluit; daarna "Stop live" of Q
- duration: 15s
- transition_in: push-up
- status: animated
- voiceover: "Stoppen? Klik op de X rechtsboven in het camerabeeld. De knop wordt rood: klik nog een keer. Zo stopt Studio niet per ongeluk. Je kunt ook op Stop live klikken, of op Q drukken."
- src: compositions/f09-stoppen.html

Grote zoom op het camerabeeld. X → rode knop met teller (3 s), tweede klik, beeld klapt dicht.
Dan kort: knop "Stop live" en toetskap "Q" naast elkaar.

## Frame 10 — Werkt het niet?

- scene: Vier korte regels na elkaar, elk met icoon
- duration: 18s
- transition_in: crossfade
- status: animated
- voiceover: "Komt de toets niet aan? Start Studio opnieuw en kies Ja. Werkt de camera niet? Sluit andere camera-apps of een oude Studio. Zegt Studio dat hij al draait? Sluit dan de andere Studio. Staat het beeld stil? Probeer Vensterweergave."
- src: compositions/f10-hulp.html

Vier rijen vraag → oplossing; elke rij licht op terwijl hij besproken wordt, de vorige dimt.

## Frame 11 — Outro

- scene: Logo, "MimiControl Studio v2", "Meer uitleg: de handleiding"
- duration: 7s
- transition_in: crossfade
- status: animated
- voiceover: "Meer uitleg vind je in de handleiding."
- src: compositions/f11-outro.html

Spiegel van de intro; logo blijft staan, muziek dooft uit.
