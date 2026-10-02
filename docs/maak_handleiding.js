// Maakt docs/Handleiding-MimiControl-Studio-v2.docx
// Gebruik: eerst `python docs\maak_screenshots.py`, daarna `node docs\maak_handleiding.js`
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, LevelFormat, WidthType, ShadingType, BorderStyle,
  Footer, PageNumber, PageBreak,
} = require("docx");

const AFB = path.join(__dirname, "afbeeldingen");
const TEAL = "2A8F96";
const DONKER = "062D36";
const FONT = "Calibri";

// ---- hulpfuncties ----------------------------------------------------------
const t = (tekst, o = {}) => new TextRun({ text: tekst, font: FONT, ...o });
const p = (kinderen, o = {}) =>
  new Paragraph({
    spacing: { after: 120, line: 288 },
    children: typeof kinderen === "string" ? [t(kinderen)] : kinderen,
    ...o,
  });
const h1 = (tekst) =>
  new Paragraph({ heading: HeadingLevel.HEADING_1, keepNext: true, spacing: { before: 360, after: 160 }, children: [t(tekst)] });
const h2 = (tekst) =>
  new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, spacing: { before: 240, after: 100 }, children: [t(tekst)] });
let huidigeLijst = 0;
const lijstStart = () => { huidigeLijst += 1; return []; }; // elke lijst telt vanaf 1
const stap = (kinderen) =>
  new Paragraph({
    numbering: { reference: "stappen", level: 0, instance: huidigeLijst },
    spacing: { after: 100, line: 288 },
    children: typeof kinderen === "string" ? [t(kinderen)] : kinderen,
  });
const punt = (kinderen) =>
  new Paragraph({
    numbering: { reference: "punten", level: 0 },
    spacing: { after: 80, line: 288 },
    children: typeof kinderen === "string" ? [t(kinderen)] : kinderen,
  });
const vet = (tekst) => t(tekst, { bold: true });

function pngMaat(bestand) {
  const b = fs.readFileSync(bestand);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function afbeelding(naam, maxB, onderschrift, maxH = 420) {
  const bestand = path.join(AFB, naam);
  const { w, h } = pngMaat(bestand);
  let breedte = maxB;
  let hoogte = Math.round((h * breedte) / w);
  if (hoogte > maxH) {
    hoogte = maxH;
    breedte = Math.round((w * hoogte) / h);
  }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      keepNext: true,
      spacing: { before: 120, after: 60 },
      children: [new ImageRun({
        type: "png", data: fs.readFileSync(bestand),
        transformation: { width: breedte, height: hoogte },
        altText: { title: onderschrift, description: onderschrift, name: naam },
      })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [t(onderschrift, { italics: true, size: 20, color: "595959" })],
    }),
  ];
}
function kader(titel, regels, kleur = "E6F4F5") {
  const rand = { style: BorderStyle.SINGLE, size: 4, color: "B8D9DC" };
  return new Table({
    width: { size: 9026, type: WidthType.DXA },
    columnWidths: [9026],
    rows: [new TableRow({ children: [new TableCell({
      width: { size: 9026, type: WidthType.DXA },
      shading: { fill: kleur, type: ShadingType.CLEAR },
      borders: { top: rand, bottom: rand, left: rand, right: rand },
      margins: { top: 100, bottom: 100, left: 160, right: 160 },
      children: [
        new Paragraph({ spacing: { after: 60 }, children: [t(titel, { bold: true, color: DONKER })] }),
        ...regels.map((r) => new Paragraph({ spacing: { after: 60, line: 276 }, children: typeof r === "string" ? [t(r)] : r })),
      ],
    })] })],
  });
}
function tabel(kolommen, breedtes, rijen) {
  const rand = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
  const randen = { top: rand, bottom: rand, left: rand, right: rand };
  const cel = (tekst, w, kop) => new TableCell({
    width: { size: w, type: WidthType.DXA },
    borders: randen,
    shading: kop ? { fill: DONKER, type: ShadingType.CLEAR } : undefined,
    margins: { top: 70, bottom: 70, left: 110, right: 110 },
    children: [new Paragraph({ spacing: { after: 0 }, children: [t(tekst, kop ? { bold: true, color: "FFFFFF" } : { size: 21 })] })],
  });
  return new Table({
    width: { size: breedtes.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: breedtes,
    rows: [
      new TableRow({ tableHeader: true, children: kolommen.map((k, i) => cel(k, breedtes[i], true)) }),
      ...rijen.map((r) => new TableRow({ cantSplit: true, children: r.map((c, i) => cel(c, breedtes[i], false)) })),
    ],
  });
}

// ---- inhoud ---------------------------------------------------------------
const inhoud = [
  new Paragraph({ spacing: { before: 600, after: 120 }, children: [t("MimiControl Studio", { bold: true, size: 64, color: DONKER })] }),
  new Paragraph({ spacing: { after: 120 }, children: [t("Handleiding", { size: 40, color: TEAL })] }),
  p([t("Met je gezicht toetsen indrukken, bijvoorbeeld om Communicator 5 te bedienen.", { size: 26 })]),
  p([t("Mennens.Tech  ·  versie 2.2  ·  oktober 2026", { color: "595959" })]),

  h1("1. Wat is MimiControl Studio?"),
  p("MimiControl Studio kijkt via de webcam naar je gezicht. Maak je een bepaalde beweging, bijvoorbeeld je kaak open, dan drukt Studio een toets voor je in, bijvoorbeeld de spatiebalk. Zo bedien je een programma zonder toetsenbord of muis."),
  kader("Vier woorden die je vaker leest", [
    [vet("Gezichtsbeweging: "), t("iets wat je met je gezicht doet en wat Studio meet, zoals kaak open of een lach.")],
    [vet("Trigger: "), t("een koppeling tussen een beweging en een toets. Voorbeeld: kaak open geeft Spatie.")],
    [vet("Drempel: "), t("hoe sterk je de beweging moet maken. Een lage drempel reageert snel, een hoge drempel pas bij een grote beweging.")],
    [vet("Actief venster: "), t("het venster waar je het laatst op klikte. Daar komen je toetsen binnen.")],
  ]),

  h1("2. Starten"),
  ...lijstStart(),
  stap([vet("Dubbelklik "), t("op "), vet("Start MimiControl Studio v2.bat"), t(" in de map van Studio (niet alleen op het .exe-bestand).")]),
  stap([t("Windows vraagt of Studio wijzigingen mag aanbrengen. Klik op "), vet("Ja"), t(". Dat is nodig: Communicator 5 draait met extra rechten, en alleen dan komen de toetsen van Studio daar binnen.")]),
  stap([t("Studio opent. Rechtsboven, onder "), vet("Communicator 5"), t(", moet staan: "), vet("✓ Beheerder: ja"), t(".")]),
  stap([t("Kies bij "), vet("Camera"), t(" de juiste webcam en klik op "), vet("Camera preview"), t(" om te controleren dat je jezelf ziet.")]),
  ...afbeelding("01-dashboard.png", 600, "Het hoofdscherm. Links staan je triggers, rechts de instellingen.", 400),
  kader("Lukt het starten niet?", [
    "•  Staat er ✗ Beheerder: nee? Sluit Studio en start opnieuw. Kies bij de Windows-melding Ja.",
    "•  Meldt Studio dat het al draait? Sluit de andere Studio af (Taakbeheer, zoek MimiControl of pythonw) en start opnieuw.",
  ], "FFF4E0"),

  h1("3. Een trigger maken"),
  p("Je maakt een trigger in drie stappen: kies de bewegingen, neem je beweging op en kies de toets."),
  h2("Stap 1: kies je gezichtsbewegingen"),
  ...lijstStart(),
  stap([t("Klik op "), vet("Mimiek verkennen"), t(".")]),
  stap([t("Vink de bewegingen aan die je wilt gebruiken. Hoe minder je aanvinkt, hoe overzichtelijker het wordt: alleen deze bewegingen worden getoond en voorgesteld."), ]),
  stap([t("Handig: de knoppen "), vet("Alles aanvinken"), t(" en "), vet("Alles uitvinken"), t(", en de snelle keuzes "), vet("Bolle mond / tuiten"), t(" en "), vet("Tong uitsteken (benadering)"), t(".")]),
  stap([t("Klik op "), vet("Toepassen"), t(".")]),
  ...afbeelding("02-kies-bewegingen.png", 520, "Kies welke gezichtsbewegingen je wilt gebruiken.", 400),
  kader("Tong uitsteken", [
    "Het systeem kan de tong niet los meten. De snelle keuze 'Tong uitsteken (benadering)' vinkt daarom 'Kaak open' en 'Lip-trechter' aan: een combinatie die lijkt op tong uitsteken. Stel de drempels van beide goed in en test het even.",
  ]),
  h2("Stap 2: neem je beweging op"),
  ...lijstStart(),
  stap([t("Er opent een venster met je camerabeeld en balkjes voor elke beweging. Klik op "), vet("Opname starten"), t(" en maak je beweging een paar keer.")]),
  stap([t("Klik op "), vet("Opname stoppen"), t(". De sterkste beweging krijgt een gele balk.")]),
  stap([t("Mis je een beweging? Klik op "), vet("Beweging kiezen"), t(" en vink er een aan. Heb je de beweging niet gemaakt tijdens de opname, kies dan "), vet("Opnieuw opnemen"), t(".")]),
  stap([t("Klik op "), vet("Trigger maken"), t(".")]),
  ...afbeelding("03-verkennen.png", 520, "Opnemen: eerst Opname starten, daarna Trigger maken.", 300),
  h2("Stap 3: kies de toets en stel de drempel in"),
  ...lijstStart(),
  stap([t("Geef de trigger een naam.")]),
  stap([t("Kies bij "), vet("Actie"), t(" de toets die Studio moet indrukken (kies uit de lijst of klik op "), vet("Toets opnemen"), t(" en druk de toets in).")]),
  stap([t("Zet bij elke beweging de schuifbalk op de juiste drempel. De kolom "), vet("Gemeten"), t(" laat zien hoe sterk je de beweging maakte. Zet de drempel iets lager dan dat. Dan lukt het ook als je de beweging iets zwakker maakt.")]),
  stap([t("Klik op "), vet("Opslaan"), t(". Je trigger staat nu op het hoofdscherm.")]),
  ...afbeelding("05-trigger-editor.png", 480, "Naam, toets en drempel instellen.", 400),

  h1("4. Live gebruiken met Communicator 5"),
  ...lijstStart(),
  stap([t("Zet Communicator 5 op "), vet("Vensterweergave"), t(" (niet op volledig scherm). Dat voorkomt dat het camerabeeld blijft hangen.")]),
  stap([t("Klik in Studio op "), vet("Live modus starten"), t(".")]),
  stap([t("Klik op Communicator 5, zodat dat het "), vet("actieve venster"), t(" is. Studio drukt de toetsen altijd in het actieve venster in.")]),
  stap([t("Maak je beweging. Studio drukt de toets in en toont dat linksonder in het camerabeeld.")]),
  ...afbeelding("07-live-toets-verstuurd.png", 380, "Het label laat zien welke toets Studio net heeft verstuurd.", 260),
  p([t("Staat het label op grijs en zegt het "), vet("Niet verstuurd"), t(", dan is de toets niet aangekomen. Zie hoofdstuk 6.")]),
  h2("Instellingen aanpassen"),
  p("Alles wat je in het hoofdscherm instelt, wordt bewaard in je profiel."),
  punt([vet("Camerabeeld tonen, Grootte, Hoek: "), t("waar en hoe groot het camerabeeld staat.")]),
  punt([vet("Triggerbalken tonen: "), t("een balk naast het camerabeeld met de status van je triggers.")]),
  punt([vet("Toetsen sturen: "), t("zet je dit uit, dan kun je oefenen zonder dat er toetsen worden ingedrukt.")]),
  punt([vet("Toets-melding tonen: "), t("het label met de verstuurde toets aan of uit.")]),
  punt([vet("Cooldown: "), t("hoe lang Studio wacht voordat dezelfde trigger opnieuw mag.")]),
  punt([vet("Vasthoudtijd: "), t("hoe lang je de beweging moet vasthouden voordat de toets wordt ingedrukt. Handig tegen ongewilde bewegingen.")]),
  punt([vet("Toetsduur: "), t("hoe lang de toets ingedrukt blijft.")]),

  h1("5. Stoppen"),
  p([t("Klik "), vet("twee keer"), t(" op de kleine "), vet("X"), t(" rechtsboven in het camerabeeld. Bij de eerste klik wordt de knop rood en staat er 'Stoppen? Klik nogmaals'. Zo stopt Studio niet per ongeluk. Klik je niet nog een keer, dan gaat de knop na drie seconden terug naar de X.")]),
  ...afbeelding("08-live-stoppen.png", 380, "Na de eerste klik vraagt de knop om bevestiging.", 260),
  p([t("Andere manieren: de knop "), vet("Stop live"), t(" in het drempelpaneel, of de toets "), vet("Q"), t(" als het camerabeeld is aangeklikt.")]),

  h1("6. Werkt het niet?"),
  tabel(
    ["Wat zie je?", "Mogelijke oorzaak", "Wat doe je?"],
    [2500, 3100, 3426],
    [
      ["De toets komt niet aan in Communicator 5", "Studio draait niet met beheerdersrechten.", "Sluit Studio en start opnieuw. Klik Ja bij de Windows-melding. Controleer ✓ Beheerder: ja."],
      ["Het label zegt 'Niet verstuurd'", "'Toetsen sturen' staat uit, of Windows blokkeert de toets.", "Zet 'Toetsen sturen' aan en controleer de beheerdersrechten."],
      ["De toets gaat naar het verkeerde programma", "Het actieve venster is een ander venster.", "Klik eerst op Communicator 5. De toets gaat altijd naar het actieve venster."],
      ["De camera werkt niet of het beeld is zwart", "Een andere Studio of app gebruikt de camera.", "Sluit andere camera-apps en oude Studio's (Taakbeheer: MimiControl of pythonw) en start opnieuw."],
      ["Melding dat Studio al draait", "Er loopt al een Studio.", "Sluit de andere Studio of start de pc opnieuw."],
      ["Het camerabeeld staat stil boven Communicator", "Communicator staat op volledig scherm.", "Zet Communicator 5 op Vensterweergave."],
      ["Het rode label 'Geen gezicht'", "Studio ziet je gezicht niet.", "Zorg voor goed licht en ga recht voor de camera zitten."],
      ["De trigger gaat te snel of per ongeluk af", "De drempel is te laag of de vasthoudtijd te kort.", "Verhoog de drempel van de trigger of de vasthoudtijd."],
      ["De trigger gaat niet af", "De drempel is te hoog.", "Verlaag de drempel, of neem de beweging opnieuw op."],
    ],
  ),

  h1("7. Sneltoetsen in het camerabeeld"),
  p("Klik eerst op het camerabeeld. Daarna werken deze toetsen:"),
  tabel(
    ["Toets", "Wat doet het?", "Toets", "Wat doet het?"],
    [900, 3613, 900, 3613],
    [
      ["Q", "Live stoppen", "K", "Toets-melding aan/uit"],
      ["P", "Beeld pauzeren", "A", "Altijd bovenop aan/uit"],
      ["1 2 3", "Grootte van het beeld", "M", "Volledig gezichtsnet aan/uit"],
      ["T", "Triggerbalken aan/uit", "F", "Beeld spiegelen"],
      ["S", "Toetsen sturen aan/uit", "O", "Volgende hoek"],
      ["C", "Alleen camerabeeld", "", ""],
    ],
  ),
  new Paragraph({ spacing: { before: 360 }, children: [t("Vragen of problemen? Neem contact op met Mennens.Tech.", { italics: true, color: "595959" })] }),
];

const doc = new Document({
  creator: "Mennens.Tech",
  title: "Handleiding MimiControl Studio v2",
  styles: {
    default: { document: { run: { font: FONT, size: 23 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 34, bold: true, font: FONT, color: DONKER }, paragraph: { outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 27, bold: true, font: FONT, color: TEAL }, paragraph: { outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      // elke lijst met stappen telt opnieuw vanaf 1
      ...Array.from({ length: 1 }, () => ({
        reference: "stappen",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 540, hanging: 360 } } } }],
      })),
      { reference: "punten", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 540, hanging: 280 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, right: 1440, bottom: 1134, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      t("MimiControl Studio · handleiding · pagina ", { size: 18, color: "808080" }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "808080" }),
    ] })] }) },
    children: inhoud,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const uit = path.join(__dirname, "Handleiding-MimiControl-Studio-v2.docx");
  fs.writeFileSync(uit, buf);
  console.log("Geschreven:", uit);
});
