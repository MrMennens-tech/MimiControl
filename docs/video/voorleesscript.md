# Voorleesscript: uitlegvideo MimiControl Studio v2

De video heeft Nederlandse ondertitels en geen spraak. Wil je zelf inspreken? Dit is de tekst per
scène, met het tijdstip waarop de scène begint. Spreek rustig; elke scène heeft ruimte voor de tekst.

| Tijd | Scène | Tekst |
|---|---|---|
| 0:00 | Titel | MimiControl Studio. Met je gezicht toetsen indrukken. |
| 0:06 | Zo werkt het | Studio kijkt via de webcam naar je gezicht. Maak je een bepaalde beweging, bijvoorbeeld je kaak open, dan drukt Studio een toets in, zoals de spatiebalk. Zo bedien je bijvoorbeeld Communicator 5 zonder toetsenbord. |
| 0:22 | Stap 1: Starten | Dubbelklik op Start MimiControl Studio v2 punt bat. Klik op Ja bij de Windows-melding: dat is nodig, omdat Communicator 5 met extra rechten draait. Controleer dat er Beheerder: ja staat. |
| 0:42 | Stap 2: Kies je gezichtsbewegingen | Klik op Mimiek verkennen. Vink de bewegingen aan die je wilt gebruiken. Met de snelle keuzes kies je bijvoorbeeld bolle mond of tong uitsteken. Klik dan op Toepassen. |
| 1:00 | Stap 3: Neem je beweging op | Klik op Opname starten en maak je beweging een paar keer. Klik op Opname stoppen en daarna op Trigger maken. |
| 1:20 | Stap 4: Toets en drempel | Geef de trigger een naam en kies de toets die Studio moet indrukken. Zet de drempel iets onder de waarde die je hebt gemeten. Klik op Opslaan. |
| 1:40 | Stap 5: Live gebruiken | Zet Communicator 5 op Vensterweergave en klik erop: dat is het actieve venster, daar komen je toetsen binnen. Start Live en maak je beweging. Linksonder zie je welke toets er is verstuurd. |
| 2:02 | Stap 6: Stoppen | Klik op de X rechtsboven in het camerabeeld. De knop wordt rood: klik nogmaals om te stoppen. Zo stopt Studio niet per ongeluk. |
| 2:18 | Werkt het niet? | Komt de toets niet aan? Start Studio opnieuw en klik Ja bij de Windows-melding. Werkt de camera niet? Sluit andere camera-apps en een oude Studio. Staat het beeld stil? Zet Communicator 5 op Vensterweergave. |
| 2:32 | Einde | Meer uitleg vind je in de handleiding. |

De video maak je opnieuw met `python docs\video\maak_video_html.py` en daarna
`npx hyperframes render` in `docs\video\studio-uitleg` (Node.js 22 of nieuwer nodig).
