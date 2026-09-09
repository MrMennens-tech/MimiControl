/**
 * Gegevensmodel van de testomgeving.
 *
 * De sleutelnamen volgen het opgegeven uitgangspunt (`settings`, `screens`,
 * `items`, `action`) zodat bestaande voorbeeldbestanden blijven werken.
 * Alle waarden zijn gewone JSON: geen HTML, geen code, geen externe adressen.
 */

/** Bedieningsmodus: aantal toetsen dat de leerling gebruikt. */
export type Bedieningsmodus = 1 | 2 | 3;

/** Logische invoeracties waar toetsen naartoe worden vertaald. */
export type InvoerActie = 'next' | 'select' | 'back';

/** Soorten acties die een tegel kan uitvoeren. */
export type ActieType =
  /** Ga naar een ander scherm. */
  | 'navigate'
  /** Speel een lokaal audiobestand. */
  | 'audio'
  /** Spreek een korte boodschap uit via de spraakmodule van het systeem. */
  | 'speak'
  /** Toon het gekozen item groot in beeld. */
  | 'image'
  /** Laat een kleur rustig over het scherm bewegen. */
  | 'colorSweep'
  /** Confetti / lichtjes. */
  | 'confetti'
  /** Toon een dier groot in beeld met het bijbehorende geluid. */
  | 'animalSound'
  /** Eenvoudige animatie (rustig bewegend figuur). */
  | 'animation';

/** Beschrijving van wat er gebeurt als een tegel gekozen wordt. */
export interface Actie {
  type: ActieType;
  /** Doelscherm bij `navigate`. */
  target?: string;
  /** Verwijzing naar audio: `media:<id>` (lokale upload) of relatief pad. */
  audio?: string;
  /** Tekst die uitgesproken wordt bij `speak`. */
  tekst?: string;
  /** Hoofdkleur voor `colorSweep`, `confetti` en `animation`. */
  kleur?: string;
  /** Emoji die groot getoond wordt als er geen afbeelding is. */
  emoji?: string;
  /** Hoe lang de eindactie duurt in milliseconden. */
  duurMs?: number;
}

/** Eén tegel op een scherm. */
export interface Tegel {
  id: string;
  /** Kort label onder de afbeelding. */
  label: string;
  /** Emoji als beeld wanneer er geen afbeelding is toegevoegd. */
  emoji?: string;
  /** Verwijzing naar een afbeelding: `media:<id>` of relatief pad. */
  image?: string;
  /** Achtergrondkleur van de tegel (hex, bijv. `#2563eb`). */
  kleur?: string;
  /** Zichtbaar in de leerlingmodus. Standaard waar. */
  zichtbaar?: boolean;
  /** Afwijkende tekst voor gesproken benoeming; standaard het label. */
  spreekTekst?: string;
  action: Actie;
}

/** Eén scherm met maximaal vier tegels. */
export interface Scherm {
  id: string;
  title: string;
  /** Zichtbaar als thema in de leerlingmodus. Standaard waar. */
  zichtbaar?: boolean;
  items: Tegel[];
}

/**
 * Vastgelegde toets. We bewaren `code`, `key` én `keyCode` zodat de app ook
 * werkt met hulpmiddelen die toetsen zonder hardware-scancode versturen
 * (dan is `event.code` leeg, maar `key` en `keyCode` kloppen wel).
 */
export interface ToetsBinding {
  code: string;
  key: string;
  keyCode: number;
  /** Nederlandse weergavenaam, bijv. "Spatie". */
  naam: string;
}

/** Waar de scan begint op een nieuw scherm. */
export type Starttegel = 'eerste' | 'willekeurig';

/**
 * Waar de app naartoe gaat nadat een eindactie is afgelopen. In modus 1 en 2
 * is er geen terugtoets, dus moet de app zelf terugkeren om vastlopen te
 * voorkomen.
 */
export type TerugNaActie = 'beginscherm' | 'vorigeScherm' | 'blijven';

export interface Instellingen {
  controlMode: Bedieningsmodus;
  /** Scantijd per tegel in milliseconden (500 - 10000). */
  scanIntervalMs: number;
  /** Invoerblokkade na een selectie in milliseconden. */
  selectionCooldownMs: number;
  /** Gesproken benoeming bij het actief worden van een tegel. */
  speakLabels: boolean;
  /** Kort geluid bij een selectie. */
  selectionSound: boolean;
  keys: Record<InvoerActie, ToetsBinding>;
  /** Aantal scanrondes voordat de scanner stopt (0 = onbeperkt). */
  scanRondes: number;
  startTegel: Starttegel;
  /** Wat er gebeurt nadat een eindactie is afgelopen. */
  terugNaActie: TerugNaActie;
  /** Leerlingmodus meteen in volledig scherm openen. */
  volledigSchermStarten: boolean;
  /** Spreeksnelheid van de spraakmodule (0,5 - 1,5). */
  spraakSnelheid: number;
  /** Muis- en touchbediening toestaan (voor tests door de begeleider). */
  muisBediening: boolean;
  /** Pincode voor de begeleidersmodus. */
  pincode: string;
}

/** Volledige opslag van de app. */
export interface AppData {
  appVersion: string;
  settings: Instellingen;
  screens: Scherm[];
}

/** Soorten gebeurtenissen in het sessielogboek. */
export type GebeurtenisType =
  | 'sessieGestart'
  | 'sessieGestopt'
  | 'modusGekozen'
  | 'scantijdIngesteld'
  | 'schermGeopend'
  | 'tegelActief'
  | 'selectie'
  | 'terug'
  | 'terugGenegeerd'
  | 'scanrondeAfgebroken'
  | 'invoerGeblokkeerd'
  | 'actieGestart'
  | 'actieAfgelopen'
  | 'notitie';

/** Eén feitelijke gebeurtenis met tijdstempel. */
export interface Gebeurtenis {
  /** Doorlopend nummer binnen de sessie. */
  nummer: number;
  /** Tijdstempel in ISO-8601. */
  tijdstempel: string;
  /** Milliseconden sinds de start van de sessie. */
  msSindsStart: number;
  type: GebeurtenisType;
  schermId?: string;
  tegelId?: string;
  tegelLabel?: string;
  /** Positie van de tegel in de scanvolgorde (1-gebaseerd). */
  positie?: number;
  /** Tijd tussen het actief worden van de tegel en de selectie. */
  reactietijdMs?: number;
  /** Vrije, feitelijke toelichting (bijv. een observatienotitie). */
  toelichting?: string;
}

/** Opgeslagen sessie. */
export interface Sessie {
  sessiecode: string;
  gestartOp: string;
  gestoptOp?: string;
  modus: Bedieningsmodus;
  scanIntervalMs: number;
  gebeurtenissen: Gebeurtenis[];
  notities: string;
}
