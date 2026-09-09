# Toetsentestomgeving (MimiControl)

Een lokaal werkende webapp (PWA) om te observeren hoe iemand een computer
bedient met **1, 2 of 3 toetsaanslagen**. De toetsen komen bijvoorbeeld uit
[MimiControl Studio](../README.md), dat gezichtsmimiek omzet naar
toetsaanslagen.

De omgeving is bedoeld om te **observeren**, niet om te toetsen. De app
registreert uitsluitend feitelijke gebeurtenissen met een tijdstempel en trekt
geen enkele conclusie over cognitie, emotie of intentie.

> Dit project staat volledig los van de Python-app in de hoofdmap. Er is niets
> in `app/`, `scripts/` of de hoofd-`README.md` gewijzigd.

---

## Snel starten

Vereisten: **Node.js 18 of nieuwer** (getest met Node 18.16 en npm 9.5).

```powershell
cd testomgeving
npm install
npm run dev
```

Open daarna het adres dat Vite laat zien (standaard <http://localhost:5173>).

### Productiebuild

```powershell
npm run build      # typecheck + build naar dist/
npm run preview    # de gebouwde versie lokaal bekijken
```

De map `dist/` bevat een volledig zelfstandige app met relatieve paden. Die map
kan op een USB-stick, in een lokale map of achter een eenvoudige webserver
gezet worden. Na één keer laden werkt de app **offline**, dankzij de service
worker (`public/sw.js`).

### Tests

```powershell
npm test           # 133 tests, eenmalig
npm run test:watch # meelopend tijdens ontwikkelen
npm run typecheck  # alleen de TypeScript-controle
```

---

## Wat kan de app?

### Drie bedieningsmodi

| Modus | Toets 1 | Toets 2 | Toets 3 |
| --- | --- | --- | --- |
| **1 toets** | — | selecteren (de markering loopt automatisch) | — |
| **2 toetsen** | volgende tegel | selecteren | — |
| **3 toetsen** | volgende tegel | selecteren | één scherm terug |

- **Modus 1**: automatische lineaire scan langs de tegels. Scantijd instelbaar
  van 500 tot 10000 ms, instelbaar aantal scanrondes voordat de scanner stopt,
  en starten bij de eerste of bij een willekeurige tegel. Stopt de scanner, dan
  zet de selectietoets hem weer aan.
- **Modus 2**: geen tijdsdruk. Na de laatste tegel gaat de markering terug naar
  de eerste.
- **Modus 3**: terug gaat één scherm omhoog en markeert de eerder gekozen tegel
  opnieuw. Op het beginscherm doet terug niets.

Na elke keuze geldt een instelbare **invoerblokkade** (standaard 700 ms), zodat
een spasme niet meteen een tweede keuze maakt.

### Leerlingmodus

Volledig scherm, rustige effen achtergrond, maximaal vier zeer grote tegels per
scherm, groot beeld met een kort label, en een scanmarkering met hoog contrast:
dikke gele rand, zachte gloed en een lichte vergroting. Niets knippert, er zijn
geen beheerknoppen, geen externe links en geen reclame. De scanvolgorde is op
elk scherm identiek en voorspelbaar.

Optioneel: gesproken benoeming zodra een tegel actief wordt (spraakmodule van
het systeem, werkt offline) en een kort selectiegeluid.

### Begeleidersmodus

Te openen met een pincode (standaard `1234`) via de knop op het startscherm,
of in de leerlingmodus met **Ctrl + Shift + B** of drie klikken in de
linkerbovenhoek. Tabbladen:

- **Instellingen** – modus, toetsen vastleggen door de gewenste toets in te
  drukken, scantijd, invoerblokkade, scanrondes, starttegel, gesproken labels,
  selectiegeluid, spreeksnelheid, volledig scherm, muisbediening, welke
  thema's zichtbaar zijn, pincode, en sessie starten/stoppen/resetten.
- **Inhoud** – schermen en tegels toevoegen, wijzigen, verwijderen en ordenen;
  titel, label, emoji, kleur, gesproken benoeming, actietype, doelscherm,
  afbeelding uploaden, geluid uploaden, voorbeeld bekijken, en JSON
  export/import met validatie.
- **Toetstest** – zie hieronder.
- **Sessie** – alle geregistreerde gebeurtenissen, observatienotities,
  CSV-export en een korte feitelijke tekstsamenvatting.
- **Informatie** – waar de omgeving voor is, privacy en de bediening op een rij.

### Ingebouwde toetstestpagina

Speciaal om invoerproblemen te herkennen. Per gebeurtenis worden `type`, `key`,
`code`, `keyCode`, `isTrusted`, herhaling en de gemeten toetsduur getoond, plus
een teller per toets.

- Is `code` **leeg**, dan wordt dat duidelijk gemarkeerd. Dat wijst op een
  hulpmiddel dat toetsen verstuurt **zonder hardware-scancode**. MimiControl
  Studio doet dat wél goed: het gebruikt Windows `SendInput` met scancode (zie
  `app/toets_actie.py`), dus daar zijn `code`, `key` en `keyCode` allemaal
  gevuld.
- De tijd tussen `keydown` en `keyup` wordt gemeten, zodat de **toetsduur** van
  MimiControl (standaard 100 ms) te controleren is.

Om zeker te zijn dat een toets altijd herkend wordt, matcht de app op
**code, key én keyCode** tegelijk, met code als sterkste aanwijzing.

---

## Mappenstructuur

```
testomgeving/
├── index.html                 App-shell met een strikt Content-Security-Policy
├── package.json               Scripts en de (weinige) dependencies
├── vite.config.ts             Vite + Vitest, relatieve base voor offline gebruik
├── tsconfig.json
├── HANDLEIDING.md             Korte handleiding voor begeleiders en familie
├── ACCEPTATIECRITERIA.md      Alle criteria met de stand van zaken
├── voorbeeld/
│   └── voorbeeld-inhoud.json  Voorbeeldconfiguratie om te importeren
├── public/
│   ├── manifest.webmanifest   PWA-manifest (volledig scherm)
│   ├── sw.js                  Service worker: offline na één keer laden
│   ├── icoon.svg              App-icoon
│   └── assets/LEESMIJ.txt     Waar eigen geluiden en beelden kunnen staan
└── src/
    ├── main.tsx               Startpunt, registratie service worker
    ├── App.tsx                Weergavekeuze, laden/bewaren, startscherm
    ├── types.ts               Gegevensmodel
    ├── modules/               Alle logica, los van de interface
    │   ├── InputManager.ts    Toetsen → next/select/back, dubbele invoer
    │   ├── ScanEngine.ts      Automatische scan en handmatige stapscan
    │   ├── NavigationManager.ts Schermen, geschiedenis, focusherstel
    │   ├── ActionPlayer.ts    Audio, spraak, selectiegeluid, timing
    │   ├── ContentEditor.ts   Validatie, import/export, bewerkingen
    │   ├── SessionLogger.ts   Gebeurtenissen, cijfers, samenvatting
    │   ├── SafetyLayer.ts     Links, bestandsgrenzen, geen HTML/scripts
    │   ├── Besturing.ts       Verbindt alle modules; alle toestand
    │   ├── opslag.ts          IndexedDB (inhoud, media, sessies)
    │   ├── toetsnamen.ts      MimiControl-namen ↔ browserwaarden
    │   ├── csv.ts             CSV-export
    │   └── bestanden.ts       Downloads, bestand lezen, volledig scherm
    ├── componenten/           React-componenten (alleen weergave)
    ├── inhoud/                Standaardinstellingen en voorbeeldinhoud
    ├── hooks/                 useMediaUrl
    └── stijl/globaal.css      Stijl van leerling- en begeleidersmodus
```

De logica in `src/modules/` is volledig los te gebruiken en te testen; de
React-componenten tekenen alleen wat daar gebeurt.

---

## Gegevensmodel

Instellingen en inhoud staan samen in één JSON-bestand, te exporteren en te
importeren via de begeleidersmodus. Het opgegeven uitgangspunt uit de opdracht
wordt ongewijzigd aanvaard; de app vult ontbrekende velden aan met
standaardwaarden.

```json
{
  "appVersion": "1.0",
  "settings": {
    "controlMode": 1,
    "scanIntervalMs": 2500,
    "selectionCooldownMs": 700,
    "speakLabels": true,
    "selectionSound": true,
    "keys": { "next": "Space", "select": "Enter", "back": "Escape" }
  },
  "screens": [
    { "id": "home", "title": "Wat wil je doen?", "items": [
      { "id": "music", "label": "Muziek", "image": "assets/music.jpg",
        "action": { "type": "navigate", "target": "music-menu" } }
    ]}
  ]
}
```

### Uitbreidingen op het uitgangspunt

| Veld | Betekenis |
| --- | --- |
| `settings.scanRondes` | Aantal scanrondes voordat de scanner stopt (0 = onbeperkt) |
| `settings.startTegel` | `eerste` of `willekeurig` |
| `settings.terugNaActie` | `beginscherm`, `vorigeScherm` of `blijven` |
| `settings.volledigSchermStarten` | Leerlingmodus meteen in volledig scherm |
| `settings.spraakSnelheid` | 0,5 – 1,5 |
| `settings.muisBediening` | Muis/touch toestaan voor tests door de begeleider |
| `settings.pincode` | Pincode van de begeleidersmodus |
| `settings.keys.*` | Mag een naam zijn (`"Space"`, `"space"`) of een object met `code`, `key` en `keyCode` |
| `screens[].zichtbaar` | Scherm in gebruik |
| `items[].emoji` | Beeld zolang er geen afbeelding is |
| `items[].kleur` | Hexkleur van de tegel |
| `items[].zichtbaar` | Tegel zichtbaar voor de leerling |
| `items[].spreekTekst` | Afwijkende tekst voor de gesproken benoeming |
| `action.tekst` | Tekst in beeld / gesproken boodschap |
| `action.kleur`, `action.emoji`, `action.duurMs` | Vormgeving en duur van de eindactie |

### Actietypen

| `action.type` | Wat er gebeurt | Nederlandse alias |
| --- | --- | --- |
| `navigate` | Naar een ander scherm (`target`) | `navigeren` |
| `audio` | Lokaal geluidsfragment spelen | `geluid` |
| `speak` | Korte gesproken boodschap | `spraak` |
| `image` | Keuze groot in beeld | `afbeelding` |
| `colorSweep` | Kleur beweegt rustig over het scherm | `kleurgolf` |
| `confetti` | Confetti en lichtjes | `lichtjes` |
| `animalSound` | Dier groot in beeld met geluid | `dier` |
| `animation` | Eenvoudige, rustige animatie | `animatie` |

Media wordt aangeduid met `media:<id>` (lokale upload in IndexedDB) of met een
relatief pad zoals `assets/hond.mp3`. Absolute adressen (`http://`, `https://`,
`javascript:`) worden bij import geweigerd.

---

## Sessieobservatie

Geregistreerd worden, met tijdstempel en oplopend nummer: sessie
gestart/gestopt, gekozen modus, ingestelde scantijd, geopend scherm, tegel
actief geworden, selectie (met de tijd tussen focus en selectie), terugactie,
genegeerde terugactie op het beginscherm, afgelopen scanrondes zonder keuze,
door de invoerblokkade genegeerde aanslagen, en gestarte/afgelopen eindacties.
Daarnaast is er een vrij veld voor observatienotities.

Export als **CSV** (puntkomma als scheidingsteken en een BOM, dus direct
bruikbaar in Excel) en als korte **feitelijke tekstsamenvatting**. Elke sessie
krijgt een willekeurige code zoals `S-7FK2M`; er wordt nooit een naam van de
leerling gevraagd of opgeslagen.

---

## Privacy en veiligheid

- Geen server, geen account, geen inlog, geen trackers, geen reclame.
- Geen cameratoegang en geen microfoontoegang.
- Alles staat lokaal in IndexedDB en is met één knop te wissen.
- Externe links en het slepen van bestanden in het venster worden geblokkeerd.
- Geïmporteerde inhoud mag geen HTML, scripts of externe adressen bevatten;
  alle tekst wordt als tekst gerenderd (nergens `innerHTML`).
- Uploads: afbeeldingen maximaal 2 MB, geluid maximaal 5 MB.
- Er wordt geen auteursrechtelijk beeld of geluid meegeleverd; tegels gebruiken
  een emoji als beeld en de familie voegt zelf opnames toe.

---

## Verder lezen

- [`HANDLEIDING.md`](HANDLEIDING.md) – korte handleiding voor begeleiders en familie.
- [`ACCEPTATIECRITERIA.md`](ACCEPTATIECRITERIA.md) – alle criteria met de stand van zaken.
