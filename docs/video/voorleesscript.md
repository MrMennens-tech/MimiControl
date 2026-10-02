# Voorleesscript: uitlegvideo MimiControl Studio v2

De video heeft een Nederlandse voice-over (HeyGen-stem "Maarten de Vries") en Nederlandse
ondertitels. Wil je zelf inspreken? Hieronder de tekst per scène met het tijdstip waarop de scène
begint. De gesproken tekst begint telkens kort na dat tijdstip.

| Tijd | Scène | Tekst |
|---|---|---|
| 0:00 | Intro | MimiControl: toetsen indrukken met je gezicht. |
| 0:07 | Zo werkt het | MimiControl kijkt via de webcam naar je gezicht. Maak je een bepaalde beweging, bijvoorbeeld je mond open, dan drukt het programma een toets in, zoals de spatiebalk. Zo bedien je Communicator 5 zonder toetsenbord. |
| 0:23 | Starten | Start het programma met een dubbelklik op het bestand MimiControl Studio v2.exe. Het programma vraagt of het opnieuw mag starten als beheerder. Klik op Ja, en daarna ook op Ja bij de melding van Windows. Bovenaan het dashboard staat dan: Beheerder: ja. |
| 0:43 | Stap 1: Kies je gezichtsbewegingen | Stap één: klik op Mimiek verkennen en kies je gezichtsbewegingen. Vink aan wat je wilt gebruiken, bijvoorbeeld de kaak. Klik op Toepassen. |
| 0:56 | Stap 2: Neem je beweging op | Stap twee: klik op Opname starten en maak je beweging een paar keer. De sterkste beweging krijgt een gele balk. Klik op Opname stoppen, en daarna op Trigger maken. |
| 1:11 | Stap 3: Toets en drempel | Stap drie: geef de trigger een naam en kies de toets, bijvoorbeeld Spatie. De drempel is hoe sterk je de beweging moet maken. Zet hem iets onder de gemeten waarde. Klik op Opslaan. |
| 1:26 | Stap 4: Klaar | Stap vier: je trigger staat nu als kaart op het dashboard. |
| 1:33 | Live gebruiken | Klik op Live modus starten. Rechtsboven verschijnt een klein camerabeeld. Dat blijft boven je andere programma's staan. Klik nu op Communicator 5: toetsen gaan altijd naar het actieve venster. Volledig scherm mag gewoon. Maak je beweging. Linksonder in het camerabeeld zie je welke toets is verstuurd. |
| 1:58 | Stoppen | Stoppen? Klik op de X rechtsboven in het camerabeeld. De knop wordt rood: klik nog een keer. Zo stopt het programma niet per ongeluk. Je kunt ook op Stop live klikken, of op Q drukken. |
| 2:14 | Werkt het niet? | Komt de toets niet aan? Start opnieuw en kies Ja. Camera werkt niet? Sluit andere camera-apps of een oude MimiControl. Draait het al? Sluit de andere. Beeld stil? Probeer Vensterweergave. |
| 2:32 | Einde | Meer uitleg vind je in de handleiding. |

## Opnieuw maken

Teksten staan in `docs/video/studio-uitleg-v2/maak_video.py`. Daarna, in die map:

```
python maak_video.py stem
python maak_video.py
npx hyperframes render -o ../Uitleg-MimiControl-Studio-v2.mp4
```

Voor `stem` is de HeyGen-CLI nodig (`D:\heygen-cli\heygen.exe`, ingelogd met `heygen auth login --oauth`). Het gratis stemtegoed van HeyGen is beperkt per maand; `stem` maakt alleen scènes opnieuw waarvan de tekst veranderd is. Voor `npx hyperframes` is Node.js 22 of nieuwer nodig.
