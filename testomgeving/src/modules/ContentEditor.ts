/**
 * ContentEditor - inhoud bewerken, valideren, importeren en exporteren.
 *
 * De validatie is streng: alleen bekende velden, alleen platte tekst, geen
 * HTML of scripts en geen externe adressen. Wat niet klopt wordt gemeld
 * (fout) of stilzwijgend gecorrigeerd met een melding (waarschuwing), zodat
 * de begeleider altijd ziet wat er met een importbestand is gebeurd.
 */

import type {
  Actie,
  ActieType,
  AppData,
  Bedieningsmodus,
  Instellingen,
  InvoerActie,
  Scherm,
  Starttegel,
  Tegel,
  TerugNaActie,
  ToetsBinding,
} from '../types';
import {
  APP_VERSIE,
  BLOKKADE_MAX_MS,
  BLOKKADE_MIN_MS,
  MAX_TEGELS_PER_SCHERM,
  SCANTIJD_MAX_MS,
  SCANTIJD_MIN_MS,
  STANDAARD_INSTELLINGEN,
} from '../inhoud/standaardInstellingen';
import { STANDAARD_SCHERMEN } from '../inhoud/standaardInhoud';
import { bindingUitNaam } from './toetsnamen';
import { bevatVerdachteInhoud, isVeiligeMediaVerwijzing, veiligeTekst } from './SafetyLayer';

const ACTIE_TYPEN: ActieType[] = [
  'navigate',
  'audio',
  'speak',
  'image',
  'colorSweep',
  'confetti',
  'animalSound',
  'animation',
];

/** Nederlandse aliassen voor actietypen, zodat handmatig gemaakte bestanden werken. */
const ACTIE_ALIASSEN: Record<string, ActieType> = {
  navigeren: 'navigate',
  scherm: 'navigate',
  geluid: 'audio',
  spraak: 'speak',
  spreken: 'speak',
  afbeelding: 'image',
  groot: 'image',
  kleurgolf: 'colorSweep',
  kleur: 'colorSweep',
  lichtjes: 'confetti',
  dier: 'animalSound',
  diergeluid: 'animalSound',
  animatie: 'animation',
};

/** Nederlandse omschrijving van een actietype voor de begeleidersmodus. */
export const ACTIE_OMSCHRIJVING: Record<ActieType, string> = {
  navigate: 'Naar een ander scherm',
  audio: 'Geluidsfragment spelen',
  speak: 'Korte gesproken boodschap',
  image: 'Keuze groot in beeld',
  colorSweep: 'Kleur over het scherm',
  confetti: 'Confetti en lichtjes',
  animalSound: 'Dier met geluid',
  animation: 'Eenvoudige animatie',
};

export interface ValidatieResultaat {
  geldig: boolean;
  fouten: string[];
  waarschuwingen: string[];
  /** De opgeschoonde gegevens; alleen bruikbaar wanneer `geldig` waar is. */
  data: AppData | null;
}

/** Volledige standaardinhoud met standaardinstellingen. */
export function standaardAppData(): AppData {
  return {
    appVersion: APP_VERSIE,
    settings: structuredKopie(STANDAARD_INSTELLINGEN),
    screens: structuredKopie(STANDAARD_SCHERMEN),
  };
}

/** Diepe kopie zonder verwijzingen naar het origineel. */
export function structuredKopie<T>(waarde: T): T {
  return JSON.parse(JSON.stringify(waarde)) as T;
}

function isObject(waarde: unknown): waarde is Record<string, unknown> {
  return typeof waarde === 'object' && waarde !== null && !Array.isArray(waarde);
}

function getal(waarde: unknown, standaard: number, min: number, max: number): number {
  const nummer = typeof waarde === 'number' ? waarde : Number(waarde);
  if (!Number.isFinite(nummer)) return standaard;
  return Math.min(max, Math.max(min, Math.round(nummer)));
}

function booleaans(waarde: unknown, standaard: boolean): boolean {
  return typeof waarde === 'boolean' ? waarde : standaard;
}

/** Zet een id om naar een veilige, korte sleutel. */
export function veiligId(waarde: unknown, terugval: string): string {
  const tekst = typeof waarde === 'string' ? waarde.trim() : '';
  const opgeschoond = tekst
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48);
  return opgeschoond || terugval;
}

/** Controleer of een kleur een geldige hexwaarde is. */
export function veiligeKleur(waarde: unknown): string | undefined {
  if (typeof waarde !== 'string') return undefined;
  const kleur = waarde.trim();
  return /^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$/.test(kleur) ? kleur : undefined;
}

/** Beperk een emoji tot enkele tekens platte tekst. */
function veiligeEmoji(waarde: unknown): string | undefined {
  const tekst = veiligeTekst(waarde, 8);
  return tekst || undefined;
}

// ---------------------------------------------------------------------------
// Instellingen
// ---------------------------------------------------------------------------

function leesBinding(waarde: unknown, standaard: ToetsBinding): ToetsBinding {
  if (typeof waarde === 'string' && waarde.trim()) return bindingUitNaam(waarde.trim());
  if (isObject(waarde)) {
    const code = veiligeTekst(waarde.code, 32);
    const key = typeof waarde.key === 'string' ? waarde.key.slice(0, 32) : '';
    const keyCode = getal(waarde.keyCode, 0, 0, 1024);
    if (code || key || keyCode) {
      const basis = bindingUitNaam(code || key);
      return {
        code: code || basis.code,
        key: key || basis.key,
        keyCode: keyCode || basis.keyCode,
        naam: veiligeTekst(waarde.naam, 40) || basis.naam,
      };
    }
  }
  return { ...standaard };
}

/** Lees en corrigeer de instellingen. */
export function leesInstellingen(
  onbekend: unknown,
  waarschuwingen: string[] = [],
): Instellingen {
  const bron = isObject(onbekend) ? onbekend : {};
  const s = STANDAARD_INSTELLINGEN;

  const modusRuw = getal(bron.controlMode, s.controlMode, 1, 3);
  const controlMode = modusRuw as Bedieningsmodus;

  const scanIntervalRuw = getal(bron.scanIntervalMs, s.scanIntervalMs, SCANTIJD_MIN_MS, SCANTIJD_MAX_MS);
  if (
    typeof bron.scanIntervalMs === 'number' &&
    (bron.scanIntervalMs < SCANTIJD_MIN_MS || bron.scanIntervalMs > SCANTIJD_MAX_MS)
  ) {
    waarschuwingen.push(
      `Scantijd aangepast naar ${scanIntervalRuw} ms (toegestaan: ${SCANTIJD_MIN_MS}-${SCANTIJD_MAX_MS} ms).`,
    );
  }

  const keysBron = isObject(bron.keys) ? bron.keys : {};
  const keys = {
    next: leesBinding(keysBron.next, s.keys.next),
    select: leesBinding(keysBron.select, s.keys.select),
    back: leesBinding(keysBron.back, s.keys.back),
  } as Record<InvoerActie, ToetsBinding>;

  const startTegel: Starttegel = bron.startTegel === 'willekeurig' ? 'willekeurig' : 'eerste';
  const terugNaActie: TerugNaActie =
    bron.terugNaActie === 'vorigeScherm' || bron.terugNaActie === 'blijven'
      ? bron.terugNaActie
      : s.terugNaActie;

  const pincodeRuw = veiligeTekst(bron.pincode, 8).replace(/\D/g, '');

  return {
    controlMode,
    scanIntervalMs: scanIntervalRuw,
    selectionCooldownMs: getal(bron.selectionCooldownMs, s.selectionCooldownMs, BLOKKADE_MIN_MS, BLOKKADE_MAX_MS),
    speakLabels: booleaans(bron.speakLabels, s.speakLabels),
    selectionSound: booleaans(bron.selectionSound, s.selectionSound),
    keys,
    scanRondes: getal(bron.scanRondes, s.scanRondes, 0, 99),
    startTegel,
    terugNaActie,
    volledigSchermStarten: booleaans(bron.volledigSchermStarten, s.volledigSchermStarten),
    spraakSnelheid: Math.min(1.5, Math.max(0.5, Number(bron.spraakSnelheid) || s.spraakSnelheid)),
    muisBediening: booleaans(bron.muisBediening, s.muisBediening),
    pincode: pincodeRuw.length >= 3 ? pincodeRuw : s.pincode,
  };
}

// ---------------------------------------------------------------------------
// Schermen en tegels
// ---------------------------------------------------------------------------

function leesActie(
  onbekend: unknown,
  pad: string,
  fouten: string[],
  waarschuwingen: string[],
): Actie {
  const bron = isObject(onbekend) ? onbekend : {};
  const ruwType = typeof bron.type === 'string' ? bron.type.trim() : '';
  let type = ACTIE_TYPEN.find((t) => t === ruwType);
  if (!type) {
    const alias = ACTIE_ALIASSEN[ruwType.toLowerCase()];
    if (alias) type = alias;
  }
  if (!type) {
    fouten.push(`${pad}: onbekend actietype "${ruwType || '(leeg)'}".`);
    type = 'image';
  }

  const actie: Actie = { type };

  if (type === 'navigate') {
    const target = veiligId(bron.target, '');
    if (!target) fouten.push(`${pad}: actietype "navigate" heeft een doelscherm nodig.`);
    else actie.target = target;
  }

  if (typeof bron.audio === 'string' && bron.audio.trim()) {
    const audio = bron.audio.trim();
    if (!isVeiligeMediaVerwijzing(audio)) {
      waarschuwingen.push(`${pad}: geluidsverwijzing "${audio}" is niet toegestaan en is verwijderd.`);
    } else {
      actie.audio = audio;
    }
  }

  const tekst = veiligeTekst(bron.tekst, 200);
  if (tekst) {
    if (bevatVerdachteInhoud(tekst)) {
      fouten.push(`${pad}: de tekst bevat code of HTML en is geweigerd.`);
    } else {
      actie.tekst = tekst;
    }
  }
  if (type === 'speak' && !actie.tekst) {
    fouten.push(`${pad}: actietype "speak" heeft een tekst nodig.`);
  }

  const kleur = veiligeKleur(bron.kleur);
  if (kleur) actie.kleur = kleur;
  const emoji = veiligeEmoji(bron.emoji);
  if (emoji) actie.emoji = emoji;
  actie.duurMs = getal(bron.duurMs, 6000, 500, 60000);

  return actie;
}

function leesTegel(
  onbekend: unknown,
  pad: string,
  index: number,
  fouten: string[],
  waarschuwingen: string[],
): Tegel {
  const bron = isObject(onbekend) ? onbekend : {};
  const id = veiligId(bron.id, `tegel-${index + 1}`);
  const label = veiligeTekst(bron.label, 60);
  if (!label) fouten.push(`${pad}: de tegel heeft een label nodig.`);
  if (label && bevatVerdachteInhoud(label)) fouten.push(`${pad}: het label bevat code of HTML.`);

  const tegel: Tegel = {
    id,
    label: label || `Tegel ${index + 1}`,
    action: leesActie(bron.action, `${pad} > actie`, fouten, waarschuwingen),
  };

  const emoji = veiligeEmoji(bron.emoji);
  if (emoji) tegel.emoji = emoji;
  const kleur = veiligeKleur(bron.kleur);
  if (kleur) tegel.kleur = kleur;

  if (typeof bron.image === 'string' && bron.image.trim()) {
    const image = bron.image.trim();
    if (!isVeiligeMediaVerwijzing(image)) {
      waarschuwingen.push(`${pad}: afbeeldingsverwijzing "${image}" is niet toegestaan en is verwijderd.`);
    } else {
      tegel.image = image;
    }
  }

  if (bron.zichtbaar === false) tegel.zichtbaar = false;
  const spreekTekst = veiligeTekst(bron.spreekTekst, 120);
  if (spreekTekst) tegel.spreekTekst = spreekTekst;

  return tegel;
}

function leesScherm(
  onbekend: unknown,
  index: number,
  fouten: string[],
  waarschuwingen: string[],
): Scherm {
  const bron = isObject(onbekend) ? onbekend : {};
  const id = veiligId(bron.id, `scherm-${index + 1}`);
  const title = veiligeTekst(bron.title, 80) || `Scherm ${index + 1}`;
  const pad = `Scherm "${id}"`;

  if (bevatVerdachteInhoud(title)) fouten.push(`${pad}: de titel bevat code of HTML.`);

  const ruweItems = Array.isArray(bron.items) ? bron.items : [];
  if (ruweItems.length === 0) fouten.push(`${pad}: het scherm heeft minstens één tegel nodig.`);
  if (ruweItems.length > MAX_TEGELS_PER_SCHERM) {
    waarschuwingen.push(
      `${pad}: ${ruweItems.length} tegels. Voor de leerlingmodus zijn maximaal ${MAX_TEGELS_PER_SCHERM} tegels per scherm bedoeld.`,
    );
  }

  const items = ruweItems.map((item, i) =>
    leesTegel(item, `${pad} > tegel ${i + 1}`, i, fouten, waarschuwingen),
  );

  const scherm: Scherm = { id, title, items };
  if (bron.zichtbaar === false) scherm.zichtbaar = false;
  return scherm;
}

/**
 * Valideer een volledig gegevensbestand. Levert opgeschoonde gegevens,
 * fouten (import wordt geweigerd) en waarschuwingen (import gaat door).
 */
export function valideerAppData(onbekend: unknown): ValidatieResultaat {
  const fouten: string[] = [];
  const waarschuwingen: string[] = [];

  if (!isObject(onbekend)) {
    return {
      geldig: false,
      fouten: ['Het bestand bevat geen JSON-object.'],
      waarschuwingen,
      data: null,
    };
  }

  const versie = veiligeTekst(onbekend.appVersion, 16) || APP_VERSIE;
  if (versie !== APP_VERSIE) {
    waarschuwingen.push(`Het bestand is van versie ${versie}; deze app gebruikt versie ${APP_VERSIE}.`);
  }

  const settings = leesInstellingen(onbekend.settings, waarschuwingen);

  const ruweSchermen = Array.isArray(onbekend.screens) ? onbekend.screens : null;
  if (!ruweSchermen) fouten.push('Het bestand bevat geen lijst "screens".');
  const screens = (ruweSchermen ?? []).map((scherm, i) =>
    leesScherm(scherm, i, fouten, waarschuwingen),
  );

  if (ruweSchermen && screens.length === 0) fouten.push('Er is geen enkel scherm gevonden.');

  // Dubbele ids opsporen: die maken navigeren onvoorspelbaar.
  const gezien = new Set<string>();
  for (const scherm of screens) {
    if (gezien.has(scherm.id)) fouten.push(`Scherm-id "${scherm.id}" komt meer dan één keer voor.`);
    gezien.add(scherm.id);
  }

  // Navigatiedoelen controleren.
  for (const scherm of screens) {
    for (const item of scherm.items) {
      if (item.action.type !== 'navigate') continue;
      const doel = item.action.target;
      if (doel && !gezien.has(doel)) {
        fouten.push(`Scherm "${scherm.id}" > tegel "${item.id}" verwijst naar onbekend scherm "${doel}".`);
      }
    }
  }

  const geldig = fouten.length === 0;
  return {
    geldig,
    fouten,
    waarschuwingen,
    data: geldig ? { appVersion: APP_VERSIE, settings, screens } : null,
  };
}

/** Lees en valideer een JSON-tekst. */
export function valideerJsonTekst(tekst: string): ValidatieResultaat {
  let ontleed: unknown;
  try {
    ontleed = JSON.parse(tekst);
  } catch (fout) {
    return {
      geldig: false,
      fouten: [`Het bestand is geen geldige JSON: ${(fout as Error).message}`],
      waarschuwingen: [],
      data: null,
    };
  }
  return valideerAppData(ontleed);
}

/** Zet de gegevens om naar leesbare JSON voor export. */
export function exporteerJson(data: AppData): string {
  return `${JSON.stringify(data, null, 2)}\n`;
}

/** Bestandsnaam voor een export, met datum. */
export function exportBestandsnaam(nu: Date = new Date()): string {
  const datum = nu.toISOString().slice(0, 10);
  return `toetstest-inhoud-${datum}.json`;
}

// ---------------------------------------------------------------------------
// Bewerkingen op de inhoud (gebruikt door de inhoudseditor)
// ---------------------------------------------------------------------------

/** Verplaats een element in een lijst; buiten de grenzen verandert niets. */
export function verplaats<T>(lijst: T[], van: number, naar: number): T[] {
  if (van < 0 || van >= lijst.length || naar < 0 || naar >= lijst.length || van === naar) {
    return [...lijst];
  }
  const kopie = [...lijst];
  const [element] = kopie.splice(van, 1);
  kopie.splice(naar, 0, element);
  return kopie;
}

/** Maak een id dat nog niet voorkomt. */
export function uniekId(basis: string, bestaande: string[]): string {
  const schoon = veiligId(basis, 'nieuw');
  if (!bestaande.includes(schoon)) return schoon;
  let nummer = 2;
  while (bestaande.includes(`${schoon}-${nummer}`)) nummer += 1;
  return `${schoon}-${nummer}`;
}

/** Nieuw, leeg scherm. */
export function nieuwScherm(bestaandeIds: string[]): Scherm {
  const id = uniekId('nieuw-scherm', bestaandeIds);
  return {
    id,
    title: 'Nieuw scherm',
    items: [nieuweTegel([])],
  };
}

/** Nieuwe tegel met een veilige standaardactie. */
export function nieuweTegel(bestaandeIds: string[]): Tegel {
  const id = uniekId('nieuwe-tegel', bestaandeIds);
  return {
    id,
    label: 'Nieuwe keuze',
    emoji: '⭐',
    kleur: '#2563eb',
    action: { type: 'image', emoji: '⭐', tekst: 'Nieuwe keuze', duurMs: 6000 },
  };
}

/** Alle schermen die als thema zichtbaar zijn in de leerlingmodus. */
export function zichtbareItems(scherm: Scherm): Tegel[] {
  return scherm.items.filter((item) => item.zichtbaar !== false);
}
