/**
 * SessionLogger - registreert feitelijke gebeurtenissen met tijdstempel.
 *
 * De logger legt alleen vast wat er gebeurd is: welke tegel actief werd,
 * wanneer er geselecteerd is, hoeveel tijd daartussen zat, welk scherm er
 * geopend werd en wanneer een scanronde zonder keuze afliep. Er worden geen
 * conclusies getrokken over cognitie, emotie of intentie.
 *
 * De sessie krijgt standaard een willekeurige code; er wordt nooit een naam
 * van de leerling gevraagd of opgeslagen.
 */

import type { Bedieningsmodus, Gebeurtenis, GebeurtenisType, Sessie } from '../types';
import { csvBestandsnaam, csvMetBom, sessieNaarCsv } from './csv';

export interface SessionLoggerOpties {
  nu?: () => number;
  /** Levert de sessiecode; instelbaar voor tests. */
  maakSessiecode?: () => string;
  /** Aangeroepen na elke wijziging, bijv. om op te slaan of te hertekenen. */
  opWijziging?: (sessie: Sessie) => void;
}

/** Gegevens die bij een gebeurtenis meegegeven kunnen worden. */
export interface GebeurtenisGegevens {
  schermId?: string;
  tegelId?: string;
  tegelLabel?: string;
  positie?: number;
  reactietijdMs?: number;
  toelichting?: string;
}

const LETTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

/** Willekeurige, niet-herleidbare sessiecode zoals "S-7FK2M". */
export function standaardSessiecode(willekeurig: () => number = Math.random): string {
  let code = '';
  for (let i = 0; i < 5; i += 1) {
    code += LETTERS[Math.floor(willekeurig() * LETTERS.length)];
  }
  return `S-${code}`;
}

export class SessionLogger {
  private nu: () => number;
  private maakSessiecode: () => string;
  private opWijziging?: (sessie: Sessie) => void;

  private sessie: Sessie | null = null;
  private startMs = 0;
  private teller = 0;
  /** Tijdstip waarop de huidige tegel actief werd (voor de reactietijd). */
  private focusSindsMs: number | null = null;

  constructor(opties: SessionLoggerOpties = {}) {
    this.nu = opties.nu ?? (() => Date.now());
    this.maakSessiecode = opties.maakSessiecode ?? (() => standaardSessiecode());
    this.opWijziging = opties.opWijziging;
  }

  /** Waar wanneer er een sessie loopt. */
  get isActief(): boolean {
    return this.sessie !== null && !this.sessie.gestoptOp;
  }

  /** De huidige of laatst afgesloten sessie. */
  get huidigeSessie(): Sessie | null {
    return this.sessie;
  }

  /** Start een nieuwe sessie en leg de gekozen instellingen vast. */
  start(modus: Bedieningsmodus, scanIntervalMs: number): Sessie {
    this.startMs = this.nu();
    this.teller = 0;
    this.focusSindsMs = null;
    this.sessie = {
      sessiecode: this.maakSessiecode(),
      gestartOp: new Date(this.startMs).toISOString(),
      modus,
      scanIntervalMs,
      gebeurtenissen: [],
      notities: '',
    };
    this.leg('sessieGestart', { toelichting: `sessiecode ${this.sessie.sessiecode}` });
    this.leg('modusGekozen', { toelichting: `${modus} toets(en)` });
    this.leg('scantijdIngesteld', { toelichting: `${scanIntervalMs} ms` });
    return this.sessie;
  }

  /** Stop de sessie. */
  stop(): Sessie | null {
    if (!this.sessie || this.sessie.gestoptOp) return this.sessie;
    this.leg('sessieGestopt');
    this.sessie.gestoptOp = new Date(this.nu()).toISOString();
    this.meld();
    return this.sessie;
  }

  /** Verwijder de sessie uit het geheugen. */
  reset(): void {
    this.sessie = null;
    this.teller = 0;
    this.focusSindsMs = null;
    this.meld();
  }

  /** Leg een gebeurtenis vast. Zonder actieve sessie gebeurt er niets. */
  leg(type: GebeurtenisType, gegevens: GebeurtenisGegevens = {}): Gebeurtenis | null {
    if (!this.sessie) return null;
    const tijd = this.nu();
    this.teller += 1;
    const gebeurtenis: Gebeurtenis = {
      nummer: this.teller,
      tijdstempel: new Date(tijd).toISOString(),
      msSindsStart: Math.max(0, tijd - this.startMs),
      type,
      ...gegevens,
    };
    this.sessie.gebeurtenissen.push(gebeurtenis);
    this.meld();
    return gebeurtenis;
  }

  /**
   * Leg vast dat een tegel actief (gemarkeerd) werd. Het tijdstip wordt
   * bewaard om de tijd tussen focus en selectie te kunnen berekenen.
   */
  legTegelActief(gegevens: GebeurtenisGegevens): void {
    this.focusSindsMs = this.nu();
    this.leg('tegelActief', gegevens);
  }

  /** Leg een selectie vast, inclusief de tijd sinds de tegel actief werd. */
  legSelectie(gegevens: GebeurtenisGegevens): void {
    const reactietijdMs =
      this.focusSindsMs === null ? undefined : Math.max(0, this.nu() - this.focusSindsMs);
    this.leg('selectie', { ...gegevens, reactietijdMs });
    this.focusSindsMs = null;
  }

  /** Sla de observatienotities van de begeleider op. */
  zetNotities(tekst: string): void {
    if (!this.sessie) return;
    this.sessie.notities = tekst;
    this.meld();
  }

  /** Laad een eerder opgeslagen sessie terug in de logger. */
  herstel(sessie: Sessie): void {
    this.sessie = sessie;
    this.teller = sessie.gebeurtenissen.reduce((hoogste, g) => Math.max(hoogste, g.nummer), 0);
    this.startMs = Date.parse(sessie.gestartOp);
    this.focusSindsMs = null;
  }

  private meld(): void {
    if (this.sessie) this.opWijziging?.(this.sessie);
  }
}

/** Cijfers over een sessie; puur geteld, zonder interpretatie. */
export interface SessieCijfers {
  aantalSelecties: number;
  aantalTerug: number;
  aantalTerugGenegeerd: number;
  aantalSchermen: number;
  aantalTegelActief: number;
  aantalAfgebrokenRondes: number;
  aantalGeblokkeerdeAanslagen: number;
  reactietijdenMs: number[];
  gemiddeldeReactietijdMs: number | null;
  snelsteReactietijdMs: number | null;
  langsteReactietijdMs: number | null;
  duurMs: number | null;
  /** Aantal selecties per tegel, gesorteerd van veel naar weinig. */
  perTegel: { label: string; aantal: number }[];
}

/** Bereken de cijfers van een sessie. */
export function berekenCijfers(sessie: Sessie): SessieCijfers {
  const tel = (type: GebeurtenisType) =>
    sessie.gebeurtenissen.filter((g) => g.type === type).length;

  const reactietijden = sessie.gebeurtenissen
    .filter((g) => g.type === 'selectie' && typeof g.reactietijdMs === 'number')
    .map((g) => g.reactietijdMs as number);

  const perTegelMap = new Map<string, number>();
  for (const g of sessie.gebeurtenissen) {
    if (g.type !== 'selectie') continue;
    const label = g.tegelLabel ?? g.tegelId ?? 'onbekend';
    perTegelMap.set(label, (perTegelMap.get(label) ?? 0) + 1);
  }

  const som = reactietijden.reduce((a, b) => a + b, 0);
  const duurMs = sessie.gestoptOp
    ? Math.max(0, Date.parse(sessie.gestoptOp) - Date.parse(sessie.gestartOp))
    : null;

  return {
    aantalSelecties: tel('selectie'),
    aantalTerug: tel('terug'),
    aantalTerugGenegeerd: tel('terugGenegeerd'),
    aantalSchermen: tel('schermGeopend'),
    aantalTegelActief: tel('tegelActief'),
    aantalAfgebrokenRondes: tel('scanrondeAfgebroken'),
    aantalGeblokkeerdeAanslagen: tel('invoerGeblokkeerd'),
    reactietijdenMs: reactietijden,
    gemiddeldeReactietijdMs: reactietijden.length ? Math.round(som / reactietijden.length) : null,
    snelsteReactietijdMs: reactietijden.length ? Math.min(...reactietijden) : null,
    langsteReactietijdMs: reactietijden.length ? Math.max(...reactietijden) : null,
    duurMs,
    perTegel: [...perTegelMap.entries()]
      .map(([label, aantal]) => ({ label, aantal }))
      .sort((a, b) => b.aantal - a.aantal || a.label.localeCompare(b.label, 'nl')),
  };
}

function seconden(ms: number | null): string {
  if (ms === null) return 'onbekend';
  return `${(ms / 1000).toFixed(1).replace('.', ',')} s`;
}

/**
 * Korte, feitelijke tekstsamenvatting. Bevat uitsluitend getelde
 * gebeurtenissen en gemeten tijden - geen uitspraken over de leerling.
 */
export function maakSamenvatting(sessie: Sessie): string {
  const c = berekenCijfers(sessie);
  const regels: string[] = [
    `Sessiecode: ${sessie.sessiecode}`,
    `Gestart: ${sessie.gestartOp}`,
    `Gestopt: ${sessie.gestoptOp ?? 'nog niet gestopt'}`,
    `Duur: ${seconden(c.duurMs)}`,
    `Bedieningsmodus: ${sessie.modus} toets(en)`,
    `Ingestelde scantijd: ${sessie.scanIntervalMs} ms`,
    '',
    `Aantal keer dat een tegel actief werd: ${c.aantalTegelActief}`,
    `Aantal selecties: ${c.aantalSelecties}`,
    `Aantal keer terug: ${c.aantalTerug} (genegeerd op beginscherm: ${c.aantalTerugGenegeerd})`,
    `Aantal geopende schermen: ${c.aantalSchermen}`,
    `Aantal scanrondes afgelopen zonder selectie: ${c.aantalAfgebrokenRondes}`,
    `Aantal aanslagen genegeerd door de invoerblokkade: ${c.aantalGeblokkeerdeAanslagen}`,
    '',
    `Tijd tussen actief worden en selecteren - gemiddeld: ${seconden(c.gemiddeldeReactietijdMs)}, ` +
      `snelst: ${seconden(c.snelsteReactietijdMs)}, langst: ${seconden(c.langsteReactietijdMs)}`,
  ];

  if (c.perTegel.length) {
    regels.push('', 'Selecties per tegel:');
    for (const { label, aantal } of c.perTegel) {
      regels.push(`- ${label}: ${aantal}`);
    }
  }

  if (sessie.notities.trim()) {
    regels.push('', 'Observatienotities van de begeleider:', sessie.notities.trim());
  }

  regels.push(
    '',
    'Deze samenvatting bevat alleen geregistreerde gebeurtenissen en gemeten tijden.',
    'Er zijn geen conclusies verwerkt over begrip, bedoeling of gevoel.',
  );

  return regels.join('\n');
}

/** Naam en inhoud van het CSV-bestand voor deze sessie. */
export function maakCsvBestand(sessie: Sessie): { naam: string; inhoud: string } {
  return { naam: csvBestandsnaam(sessie), inhoud: csvMetBom(sessieNaarCsv(sessie)) };
}
