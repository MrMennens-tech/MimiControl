# Handleiding voor begeleiders en familie

Deze omgeving is bedoeld om samen te ontdekken hoe iemand met één, twee of drie
toetsen keuzes kan maken op de computer. Het is **geen toets** en **geen
beoordeling**. De app schrijft alleen op wat er gebeurt en op welk moment.
Wat dat betekent, bepaalt u samen — de app doet daar geen uitspraak over.

Er is geen internet nodig, er wordt niets verstuurd en er komt geen naam in de
app.

---

## 1. De app starten

1. Open de app (dubbelklik op `index.html` in de map `dist`, of gebruik de
   snelkoppeling die op de computer is gezet).
2. U ziet het startscherm met een korte samenvatting van de instellingen.
3. Klik op **Leerlingmodus starten**. De sessie begint en de tegels komen in
   beeld.

Wilt u de app als een gewoon programma op het bureaublad? In Chrome of Edge:
menu → *Installeren* / *App installeren*. De app opent dan in een eigen venster
en werkt daarna ook zonder internet.

---

## 2. De drie manieren van bedienen

| Aantal toetsen | Hoe het werkt |
| --- | --- |
| **1 toets** | De gele markering loopt zelf van tegel naar tegel. Op het juiste moment drukken kiest die tegel. |
| **2 toetsen** | Toets 1 zet de markering een tegel verder, toets 2 kiest. Geen haast: de markering blijft staan. |
| **3 toetsen** | Zoals bij twee toetsen, plus toets 3 om één scherm terug te gaan. |

Begin bij twijfel met **twee toetsen**: er is dan geen tijdsdruk, en het is goed
te zien of iemand het verschil tussen "verder" en "kiezen" gebruikt.

Bij één toets is de **scantijd** het belangrijkste. Begin ruim (bijvoorbeeld
3500 ms) en maak die alleen korter als kiezen duidelijk gemakkelijk gaat.

---

## 3. Begeleidersmodus openen

Er zijn drie manieren:

- Op het startscherm: knop **Begeleidersmodus**.
- Tijdens de leerlingmodus: **Ctrl + Shift + B**.
- Tijdens de leerlingmodus: **drie keer klikken in de linkerbovenhoek** van het
  scherm (die hoek is onzichtbaar, zodat er geen knop in beeld staat).

Daarna wordt de pincode gevraagd. Die is standaard **1234** en is bij
*Instellingen → Pincode* te wijzigen. De pincode is alleen bedoeld om te
voorkomen dat de instellingen per ongeluk opengaan.

---

## 4. Eerst controleren: komt de toets goed aan?

Ga naar het tabblad **Toetstest** en laat MimiControl (of het toetsenbord) een
toets versturen. In de tabel ziet u per aanslag:

- **type** – `keydown` (indrukken) of `keyup` (loslaten)
- **code** – de toets zoals de browser die uit de hardware-scancode afleidt
- **key** – het teken of de naam van de toets
- **keyCode** – de oude toetscode, als extra houvast
- **isTrusted** – `true` betekent: dit komt echt van het besturingssysteem
- **duur** – hoe lang de toets ingedrukt was

Waar u op moet letten:

- **Staat er "leeg" bij `code`?** Dan verstuurt het hulpmiddel de toets zonder
  hardware-scancode. Deze app werkt dan nog wél (hij kijkt ook naar `key` en
  `keyCode`), maar veel andere programma's reageren dan niet. MimiControl
  Studio doet het goed en vult `code` altijd.
- **Duur rond 100 ms?** Dat is de standaardinstelling van MimiControl. Wijkt
  het sterk af, dan staat de toetsduur in MimiControl anders ingesteld.
- **Meer aanslagen dan verwacht?** Kijk bij de teller per toets. Twee aanslagen
  bij één beweging betekent meestal dat de vasthoudtijd of cooldown in
  MimiControl hoger moet.

---

## 5. Instellingen die het meeste verschil maken

| Instelling | Wat het doet | Tip |
| --- | --- | --- |
| **Bedieningsmodus** | 1, 2 of 3 toetsen | Begin met 2 |
| **Toetsen** | Klik op *Toets vastleggen* en laat de mimiek de toets versturen | Doe dit per mimiek opnieuw na een wijziging in MimiControl |
| **Scantijd** | Hoe lang een tegel gemarkeerd blijft (modus 1) | Ruim beginnen; 2500–4000 ms is vaak een goed begin |
| **Invoerblokkade** | Hoe lang toetsen genegeerd worden na een keuze | Bij veel spasmen hoger zetten, bijvoorbeeld 1200 ms |
| **Scanrondes** | Na hoeveel rondes de scanner stopt | 2 of 3; daarna zet de selectietoets de scan weer aan |
| **Beginnen bij** | Eerste of willekeurige tegel | *Willekeurig* laat zien of er echt gekeken wordt |
| **Tegel benoemen** | Spreekt het label uit zodra een tegel actief wordt | Aan laten bij weinig zicht of veel afleiding |
| **Na een eindactie** | Terug naar het begin, terug naar het vorige scherm, of blijven staan | Bij 1 of 2 toetsen is *terug naar het beginscherm* het rustigst |
| **Thema's** | Welke van de vier thema's zichtbaar zijn | Begin met één of twee thema's |

Alles wat u wijzigt wordt meteen op het apparaat opgeslagen.

---

## 6. Eigen foto's en geluiden toevoegen

Op het tabblad **Inhoud**:

1. Kies links het scherm dat u wilt aanpassen.
2. Zoek de tegel en klik op **Afbeelding kiezen** of **Geluid kiezen**.
3. Kies een bestand van de computer. Het bestand wordt in de app zelf
   opgeslagen en verlaat het apparaat niet.

Grenzen: afbeeldingen tot 2 MB, geluiden tot 5 MB. Ontbreekt een bestand, dan
laat de app de emoji zien en spreekt hij het label uit — de app loopt daar dus
nooit op vast.

**Gebruik alleen eigen opnames of materiaal waarvan het gebruik is toegestaan.**
Er zit met opzet geen muziek of beeld van anderen in de app.

Handige geluiden om zelf te maken: de stem van een bekende, een lievelingsliedje
dat de familie zelf mag gebruiken, echte dierengeluiden, of het geluid van een
haardroger.

---

## 7. Tegels en schermen aanpassen

Op hetzelfde tabblad **Inhoud** kunt u zonder programmeerkennis:

- Schermen toevoegen, verwijderen, omhoog en omlaag zetten (het bovenste scherm
  is het beginscherm).
- Per scherm de titel aanpassen: dat is de vraag boven de tegels.
- Tegels toevoegen (maximaal vier per scherm), verwijderen en ordenen.
- Per tegel het label, de emoji, de kleur en de gesproken benoeming instellen.
- Kiezen wat er bij een keuze gebeurt: naar een ander scherm, geluid spelen,
  een korte gesproken boodschap, de keuze groot in beeld, een kleur over het
  scherm, confetti, een dier met geluid, of een eenvoudige animatie.
- Met **Voorbeeld bekijken** direct zien hoe het scherm er voor de leerling
  uitziet.

Een scherm kan niet verwijderd worden zolang er nog tegels naar verwijzen; de
app laat dan zien welke dat zijn.

### Alles bewaren of overzetten

- **Exporteren naar JSON** maakt één bestand met alle instellingen en inhoud.
  Bewaar dat als reservekopie of zet het over naar een andere computer.
- **Importeren uit JSON** leest zo'n bestand weer in. De app controleert het
  eerst en laat zien wat er niet klopt; bij fouten wordt er niets gewijzigd.
- **Voorbeeldinhoud terugzetten** brengt de vier oorspronkelijke thema's terug.
  De instellingen blijven daarbij staan.

---

## 8. Een sessie observeren en bewaren

1. Start de sessie via *Instellingen → Sessie starten* of via de knop
   **Leerlingmodus openen**.
2. Kijk samen. Alles wordt automatisch opgeschreven.
3. Ga tussendoor of achteraf naar het tabblad **Sessie**.

Daar staan:

- De sessiecode, de starttijd, de gekozen modus en de scantijd.
- Getelde gebeurtenissen: hoeveel selecties, hoe vaak terug, hoeveel
  scanrondes zonder keuze, hoeveel aanslagen door de invoerblokkade genegeerd
  zijn, en de gemiddelde tijd tussen "tegel wordt actief" en "keuze".
- Een tabel met alle gebeurtenissen op de seconde.
- Een tekstveld voor **observatienotities**. Schrijf daar feitelijke dingen op,
  bijvoorbeeld: *"10:14 hoofd naar links gedraaid"* of *"scantijd van 2500 naar
  3500 ms gezet"*.

Met **Sessie downloaden als CSV** krijgt u een bestand dat direct in Excel
opent. **Samenvatting downloaden** geeft een korte tekst met dezelfde cijfers.

Met **Alle sessiedata wissen** verdwijnen alle logboeken van het apparaat.
Instellingen en inhoud blijven dan staan.

---

## 9. Waar u naar kunt kijken

Deze omgeving helpt bij vragen als:

- Gebeurt er iets zichtbaars na een aanslag, en wordt daarop gereageerd?
- Wordt de bewegende markering met de ogen gevolgd?
- Lukt het om te wachten tot de gewenste tegel actief is?
- Wordt er na een keuze een volgende keuze gemaakt?
- Wordt de terugtoets gebruikt om een eerdere keuze te herstellen?
- Bij welke scantijd gaat kiezen het rustigst?
- Hoe betrouwbaar is iedere mimiek: komt er één aanslag of meteen twee?

Schrijf op wat u ziet, niet wat u denkt dat het betekent. De app doet dat ook
zo: de samenvatting bevat uitsluitend getelde gebeurtenissen en gemeten tijden.

---

## 10. Als iets niet werkt

| Probleem | Wat te doen |
| --- | --- |
| De toets doet niets | Klik één keer in het venster van de app, zodat het de toetsen ontvangt. Controleer daarna op het tabblad Toetstest of er iets aankomt. |
| De toets komt aan maar er gebeurt niets | Staat de toets in *Instellingen* bij de juiste functie? In de modus met één toets werkt alleen de **selecteertoets**. |
| Er worden meteen twee keuzes gemaakt | Zet de invoerblokkade hoger, bijvoorbeeld 1200 ms, en verhoog eventueel de cooldown in MimiControl. |
| Bij `code` staat "leeg" | Het hulpmiddel verstuurt geen scancode. Deze app werkt nog wel; gebruik voor andere programma's MimiControl Studio. |
| Er komt geen geluid | Zit het bestand in de map `public/assets`, of is het via *Geluid kiezen* toegevoegd? Staat het geluid van de computer aan? |
| Er wordt niets uitgesproken | Zet *Tegel benoemen* aan en controleer of Windows een Nederlandse stem heeft. |
| De scan stopt na een tijdje | Dat is de instelling **scanrondes**. De selectietoets zet de scan weer aan; zet de instelling op 0 om te blijven doorscannen. |
| Instellingen worden niet bewaard | De app staat in een privévenster. Open hem in een normaal venster. |
| Volledig scherm gaat niet aan | Gebruik de knop *Volledig scherm aan/uit*, of de toets **F11**. |

---

## 11. Afspraken over privacy

- Er is geen server, geen account en geen internetverbinding nodig.
- Er worden geen statistieken naar buiten gestuurd en er zijn geen trackers.
- De app gebruikt geen camera en geen microfoon.
- Er wordt geen naam opgeslagen: elke sessie krijgt een willekeurige code.
- Alle gegevens staan op dit apparaat en kunnen met één knop gewist worden.
- Externe links werken niet: de app kan niet per ongeluk verlaten worden.
