# Acceptatiecriteria

Stand van zaken bij oplevering. Alle 133 geautomatiseerde tests slagen
(`npm test`), de typecontrole is schoon (`npm run typecheck`) en de
productiebuild komt zonder fouten door (`npm run build`). De ontwikkelserver
(`npm run dev`) en de gebouwde app zijn beide gecontroleerd.

Legenda: **Gehaald** / **Deels** / **Niet gehaald**.

---

## Bediening

| # | Criterium | Stand | Waar / hoe aangetoond |
| --- | --- | --- | --- |
| 1 | Iedere functie is bedienbaar met de gekozen toetsen | **Gehaald** | Navigeren, kiezen, teruggaan, een eindactie afbreken en de gestopte scanner opnieuw starten gaan allemaal met de ingestelde toetsen. `Besturing.test.ts` |
| 2 | 1 toets: automatisch scannen + selecteren | **Gehaald** | `ScanEngine` scant lineair op de ingestelde scantijd; de selectietoets kiest de gemarkeerde tegel. Tests "modus 1 - één toets" |
| 3 | 2 toetsen: volgende + selecteren | **Gehaald** | Toets 1 stapt door, na de laatste tegel weer naar de eerste; geen tijdsdruk. Tests "modus 2 - twee toetsen" |
| 4 | 3 toetsen: volgende + selecteren + terug | **Gehaald** | Terug gaat één scherm omhoog; op het beginscherm gebeurt niets. Tests "modus 3 - drie toetsen" |
| 5 | Onbedoelde dubbele toetsaanslag voert niet direct twee acties uit | **Gehaald** | Drie beschermingen tegelijk: invoerblokkade (`selectionCooldownMs`), negeren van automatische herhaling (`event.repeat`) en negeren van een tweede keydown zolang de toets niet is losgelaten. Tests "bescherming tegen dubbele activatie" in `InputManager.test.ts` en `Besturing.test.ts` |
| 6 | Markering altijd duidelijk zichtbaar, scanvolgorde voorspelbaar | **Gehaald** | Dikke gele rand, zachte gloed en lichte vergroting op een effen donkere achtergrond; niets knippert. De scanvolgorde is altijd de vaste tegelvolgorde van het scherm en identiek op elk scherm. `globaal.css` (`.tegel.actief`), `ScanEngine` |
| 7 | Teruggaan werkt | **Gehaald** | Inclusief het opnieuw markeren van de eerder gekozen tegel, ook meerdere niveaus diep. `NavigationManager.test.ts`, tests "modus 3" |

## Inhoud

| # | Criterium | Stand | Waar / hoe aangetoond |
| --- | --- | --- | --- |
| 8 | Afbeeldingen en geluiden zijn lokaal toevoegbaar | **Gehaald** | Per tegel te uploaden via de inhoudseditor; opslag in IndexedDB als `media:<id>`. Ook een relatief pad in `public/assets/` werkt. Ontbrekende media wordt netjes opgevangen: emoji als beeld, spraak in plaats van geluid |
| 9 | Begeleider kan inhoud zonder code aanpassen | **Gehaald** | Tabblad Inhoud: schermen en tegels toevoegen, wijzigen, verwijderen en ordenen; label, emoji, kleur, gesproken benoeming, actietype, doelscherm, media en voorbeeldweergave |
| 10 | JSON export/import werkt | **Gehaald** | Export levert JSON die zonder fouten weer te importeren is; import valideert eerst en wijzigt bij fouten niets. `ContentEditor.test.ts` (26 tests), inclusief het gegevensmodel uit de opdracht en `voorbeeld/voorbeeld-inhoud.json` |
| 11 | Voorbeeldinhoud: vier thema's met vervolgkeuzes en eindacties | **Gehaald** | Muziek, Kapsalon, Shoppen en stijl, Dieren — 19 schermen, elk met maximaal vier tegels. Eindacties: geluidsfragment, kleur over het scherm, dier met geluid, confetti, keuze groot in beeld, eenvoudige animatie en een korte gesproken boodschap |

## Sessie en observatie

| # | Criterium | Stand | Waar / hoe aangetoond |
| --- | --- | --- | --- |
| 12 | Sessie als CSV downloadbaar | **Gehaald** | Puntkomma als scheidingsteken plus BOM, dus direct bruikbaar in Excel; velden worden correct geciteerd. `SessionLogger.test.ts` |
| 13 | Feitelijke tekstsamenvatting | **Gehaald** | `maakSamenvatting()` geeft uitsluitend getelde gebeurtenissen en gemeten tijden, met de expliciete vermelding dat er geen conclusies in staan |
| 14 | Alle gevraagde gebeurtenissen worden geregistreerd | **Gehaald** | Sessie gestart/gestopt, modus, scantijd, geopend scherm, tegel actief, selectie, terug, genegeerde terug, afgelopen scanrondes zonder keuze, door de blokkade genegeerde aanslagen, gestarte/afgelopen eindactie, plus de tijd tussen focus en selectie |
| 15 | Veld voor handmatige observatienotities | **Gehaald** | Tabblad Sessie; de notities gaan mee in de CSV-kop en in de samenvatting |
| 16 | Standaard een willekeurige sessiecode, geen leerlingnaam | **Gehaald** | Code als `S-7FK2M`; er is nergens een veld voor een naam |
| 17 | Geen conclusies over cognitie, emotie of intentie | **Gehaald** | Er is geen enkele score, beoordeling of interpretatie in de app; alleen tellingen en tijden |

## Leerlingmodus

| # | Criterium | Stand | Waar / hoe aangetoond |
| --- | --- | --- | --- |
| 18 | Leerlingmodus toont geen beheerknoppen | **Gehaald** | Alleen titel, tegels en één regel rusttekst. De ingang naar de begeleidersmodus is een onzichtbare hoek (drie klikken) of Ctrl + Shift + B, achter een pincode |
| 19 | Volledig scherm, rustige effen achtergrond, maximaal 4 grote tegels | **Gehaald** | 2 × 2 rooster op volledige hoogte, effen achtergrond, geen versieringen; de inhoudseditor staat geen vijfde tegel toe en import waarschuwt daarover |
| 20 | Geen knipperende onderdelen, geen externe links, geen reclame | **Gehaald** | Geen knipperanimaties; alleen de door de leerling gekozen eindactie beweegt, rustig. `prefers-reduced-motion` zet ook die beweging uit. Externe links worden onderschept |
| 21 | Optionele gesproken benoeming en optioneel selectiegeluid | **Gehaald** | Beide aan/uit te zetten; spraak via de spraakmodule van het systeem (offline), selectiegeluid via de audio-engine van de browser (geen bestand nodig) |
| 22 | Invoer wordt geblokkeerd tijdens de overgang na een keuze | **Gehaald** | Tijdens de fase `overgang` staat de invoer uit en loopt bovendien de invoerblokkade |
| 23 | Muis/touch mag werken maar mag toetsbediening niet verstoren | **Gehaald** | Uit te zetten met één instelling; een klik gebruikt exact hetzelfde selectiepad, inclusief blokkade en logboek |

## Begeleidersmodus

| # | Criterium | Stand | Waar / hoe aangetoond |
| --- | --- | --- | --- |
| 24 | Achter een pincode of verborgen toetscombinatie | **Gehaald** | Pincode (standaard 1234) plus Ctrl + Shift + B en drie klikken in de linkerbovenhoek |
| 25 | Alle gevraagde instellingen aanwezig | **Gehaald** | Modus, toetsen vastleggen door indrukken, scantijd, invoerblokkade, gesproken labels, selectiegeluid, starttegel, thema's zichtbaar/verborgen, volledig scherm starten, en sessie starten/stoppen/resetten |
| 26 | Ingebouwde toetstestpagina met `type`, `key`, `code`, `keyCode`, `isTrusted` en een teller | **Gehaald** | Tabblad Toetstest; teller per toets en een lijst van de laatste 120 gebeurtenissen |
| 27 | Duidelijke markering wanneer `code` leeg is | **Gehaald** | Rood gemarkeerd in de tabel plus een uitleg bovenaan over hulpmiddelen zonder hardware-scancode |
| 28 | Tijd tussen keydown en keyup wordt getoond | **Gehaald** | Per gebeurtenis en als gemiddelde/kortste/langste, met de opmerking dat MimiControl standaard 100 ms gebruikt |

## Techniek en privacy

| # | Criterium | Stand | Waar / hoe aangetoond |
| --- | --- | --- | --- |
| 29 | React + TypeScript, PWA, offline werkend na laden | **Gehaald** | React 18 + TypeScript 5, manifest met volledig scherm, service worker met cache-first en app-shell-terugval |
| 30 | Zo min mogelijk externe dependencies | **Gehaald** | Runtime: alleen `react` en `react-dom`. Ontwikkeltijd: Vite, TypeScript, Vitest en de React-plug-in. Geen UI-bibliotheek, geen datumbibliotheek, geen router |
| 31 | Lokale opslag via IndexedDB | **Gehaald** | `opslag.ts` met drie winkels (inhoud/instellingen, media, sessies) en een geheugenterugval wanneer IndexedDB niet beschikbaar is |
| 32 | JSON voor inhoud/instellingen, CSV voor sessielogs | **Gehaald** | `ContentEditor.ts` en `csv.ts` |
| 33 | Geen server, geen account, geen tracking, geen cameratoegang | **Gehaald** | Er staat geen enkel netwerkverzoek naar buiten in de code; het Content-Security-Policy in `index.html` staat alleen `self` toe en de service worker negeert alles buiten de eigen oorsprong |
| 34 | Volledig scherm ondersteunen | **Gehaald** | Knop in de begeleidersmodus, optie om de leerlingmodus meteen in volledig scherm te starten, en `display: fullscreen` in het manifest |
| 35 | Vite als build tool | **Gehaald** | Vite 5 met de React-plug-in; relatieve `base` zodat de build ook vanaf een map of USB-stick werkt |
| 36 | Losse modules, state gescheiden van UI | **Gehaald** | Alle logica in `src/modules/`; `Besturing.ts` houdt de toestand bij en publiceert die, de React-componenten tekenen alleen. Alle modules zijn zonder browser te testen |
| 37 | SafetyLayer: geen externe links, bestandsgrenzen, geen scripts, tekst als tekst, wisknop | **Gehaald** | `SafetyLayer.ts` + `SafetyLayer.test.ts`; nergens `innerHTML` of `dangerouslySetInnerHTML` |
| 38 | Geen externe trackers | **Gehaald** | Geen analytics, geen externe fonts, geen CDN-verwijzingen; het CSP verbiedt externe bronnen |
| 39 | Netjes omgaan met ontbrekende mediabestanden | **Gehaald** | Ontbrekende afbeelding → emoji; ontbrekend geluid → gesproken benoeming plus een melding voor de begeleider in de begeleidersmodus |
| 40 | Geen auteursrechtelijk materiaal, geen externe muziekdiensten | **Gehaald** | Alleen emoji, CSS-effecten en zelfgemaakte SVG-iconen; audio voegt de familie zelf toe |

## Testen

| # | Criterium | Stand | Waar / hoe aangetoond |
| --- | --- | --- | --- |
| 41 | Automatische test: scanvolgorde | **Gehaald** | `ScanEngine.test.ts` — vaste volgorde, omslag na de laatste tegel, willekeurige start, automatisch scannen op tijd, stoppen na N rondes |
| 42 | Automatische test: selectie in alle drie de modi | **Gehaald** | `Besturing.test.ts` |
| 43 | Automatische test: terugnavigatie | **Gehaald** | `NavigationManager.test.ts` en `Besturing.test.ts` |
| 44 | Automatische test: invoerblokkade tegen dubbele activatie | **Gehaald** | `InputManager.test.ts` en `Besturing.test.ts` |
| 45 | Automatische test: herstel van vorige focus | **Gehaald** | `NavigationManager.test.ts` ("herstelt bij meerdere niveaus") en `Besturing.test.ts` ("herstelt de focus ook diep in het menu") |
| 46 | Automatische test: importvalidatie | **Gehaald** | `ContentEditor.test.ts` — opdrachtvoorbeeld, geen JSON, ontbrekende schermen, onbekend doelscherm, dubbele ids, HTML/script, externe URL, scantijd buiten de grenzen, te veel tegels |
| 47 | Automatische test: CSV-export | **Gehaald** | `SessionLogger.test.ts` — kopregels, één regel per gebeurtenis, juiste kolom voor de reactietijd, citeren van bijzondere tekens, BOM en bestandsnaam |
| 48 | Automatische test: toetsen die standaardacties van de browser veroorzaken | **Gehaald** | `InputManager.test.ts` — spatie (ook zonder functie), alle pijltjes, Page up/down, Home, End, Tab en Backspace worden onderdrukt; gewone letters niet |
| 49 | Automatische test: toets zonder scancode | **Gehaald** | `InputManager.test.ts` en `toetsnamen.test.ts` — herkenning via `key` en `keyCode` bij een lege `code`, en het aanvullen van de binding |
| 50 | Automatische test: weergave | **Gehaald** | `componenten/weergave.test.tsx` — alle schermen tekenen zonder fouten, precies één tegel is gemarkeerd, de leerlingmodus bevat geen beheerknoppen en geen link, en de samenvatting bevat geen woorden die een conclusie suggereren |

## Oplevering

| # | Criterium | Stand | Waar |
| --- | --- | --- | --- |
| 51 | Volledige broncode met duidelijke mappenstructuur | **Gehaald** | `testomgeving/src/` met `modules`, `componenten`, `inhoud`, `hooks`, `stijl`, `test` |
| 52 | `README.md` met installatie, lokaal starten en productiebuild | **Gehaald** | `testomgeving/README.md` |
| 53 | Voorbeeldconfiguratie (JSON) | **Gehaald** | `testomgeving/voorbeeld/voorbeeld-inhoud.json`, met een test die aantoont dat het bestand zonder fouten importeert |
| 54 | Korte handleiding voor begeleiders en familie | **Gehaald** | `testomgeving/HANDLEIDING.md` |
| 55 | Lijst met acceptatiecriteria en of eraan voldaan is | **Gehaald** | Dit bestand |
| 56 | Geen onafgemaakte placeholders voor kernfuncties | **Gehaald** | Geen `TODO`, `FIXME` of niet-werkende knop in de broncode; de enige bewuste "lege" plek is de map `public/assets/` waar de familie zelf geluiden neerzet, met uitleg in `LEESMIJ.txt` |
| 57 | Bestaande MimiControl-code ongewijzigd | **Gehaald** | Er is niets aangepast in `app/`, `scripts/` of de hoofd-`README.md`; alleen `.gitignore` is aangevuld met `node_modules/` |

---

## Bewuste keuzes en aandachtspunten

Geen enkel criterium is onafgemaakt. Wel een paar keuzes die het waard zijn om
te weten:

1. **Beeld is emoji, geen foto's.** De opdracht vraagt om geen auteursrechtelijk
   materiaal. Elke tegel heeft daarom een grote emoji en een eigen kleur. Per
   tegel is een eigen foto te uploaden.
2. **Automatisch terugkeren na een eindactie.** In de modus met één of twee
   toetsen is er geen terugtoets. Daarom keert de app na een eindactie zelf
   terug naar het beginscherm (instelbaar). Zonder die keuze zou de leerling in
   een submenu kunnen vastlopen.
3. **Tijdens een eindactie stopt elke functietoets de actie.** De eerste
   honderden milliseconden zijn wel geblokkeerd, zodat een spasme de actie niet
   meteen afbreekt.
4. **Scherm-ids zijn niet te wijzigen in de editor.** Andere tegels verwijzen
   ernaar; een id wijzigen zou die verwijzingen stilletjes kunnen breken. Nieuwe
   schermen krijgen automatisch een uniek id.
5. **De pincode is een drempel, geen beveiliging.** Dat is expliciet zo
   gevraagd; de code staat leesbaar in de lokale opslag.
6. **Spraak gebruikt de stemmen van het besturingssysteem.** Dat werkt offline
   en zonder externe dienst, maar de kwaliteit hangt af van de stemmen die op
   de computer staan.
7. **Geen React StrictMode.** Die start effecten twee keer, waardoor de timers
   van de scanner dubbel zouden lopen.
