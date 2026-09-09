/**
 * InputManager - vertaalt toetsaanslagen naar de logische acties
 * `next`, `select` en `back`.
 *
 * Belangrijke eigenschappen:
 * - Matcht op `code`, `key` én `keyCode`. Een hulpmiddel dat toetsen zonder
 *   hardware-scancode verstuurt levert een leeg `event.code`; de toets wordt
 *   dan alsnog herkend via `key` of `keyCode`.
 * - Voorkomt onbedoelde dubbele activatie met een instelbare invoerblokkade,
 *   negeert automatische herhaling en negeert een tweede keydown zolang de
 *   toets nog niet is losgelaten.
 * - Onderdrukt standaardacties van de browser (spatie scrollt, pijltjes
 *   scrollen, backspace gaat terug) zonder de toetsfunctie te verstoren.
 * - Levert daarnaast elk ruw event door voor de ingebouwde toetstestpagina.
 */

import type { InvoerActie, ToetsBinding } from '../types';
import { heeftBrowserActie } from './toetsnamen';

/** Minimale vorm van een toetsevent; zo is de module los te testen. */
export interface ToetsEventGegevens {
  type: 'keydown' | 'keyup';
  code?: string;
  key?: string;
  keyCode?: number;
  repeat?: boolean;
  isTrusted?: boolean;
  /** Tijdstip in milliseconden; standaard de klok van de manager. */
  tijd?: number;
  preventDefault?: () => void;
}

/** Ruwe eventinformatie voor de toetstestpagina. */
export interface RuweToetsInfo {
  type: 'keydown' | 'keyup';
  code: string;
  key: string;
  keyCode: number;
  isTrusted: boolean;
  repeat: boolean;
  tijd: number;
  /** Bij keyup: tijd tussen keydown en keyup van dezelfde toets. */
  toetsduurMs?: number;
  /** Waar wanneer `code` leeg is: dat wijst op een hulpmiddel zonder scancode. */
  codeOntbreekt: boolean;
}

/** Reden waarom een aanslag niet is uitgevoerd. */
export type BlokkadeReden = 'invoerblokkade' | 'herhaling' | 'nogIngedrukt' | 'inactief';

export interface InputManagerOpties {
  /** Klok; instelbaar voor tests. */
  nu?: () => number;
  /** Actie uitvoeren. */
  opActie?: (actie: InvoerActie, tijd: number) => void;
  /** Elke aanslag die genegeerd is, met reden. */
  opGeblokkeerd?: (actie: InvoerActie | null, reden: BlokkadeReden, tijd: number) => void;
  /** Elk ruw event, ook toetsen zonder functie (voor de toetstestpagina). */
  opRuwEvent?: (info: RuweToetsInfo) => void;
}

/** Hoe zeker een binding bij een event past; hoger is beter. */
const SCORE_CODE = 4;
const SCORE_KEY = 2;
const SCORE_KEYCODE = 1;

const ACTIE_VOLGORDE: InvoerActie[] = ['select', 'next', 'back'];

export class InputManager {
  private nu: () => number;
  private opActie?: (actie: InvoerActie, tijd: number) => void;
  private opGeblokkeerd?: (actie: InvoerActie | null, reden: BlokkadeReden, tijd: number) => void;
  private opRuwEvent?: (info: RuweToetsInfo) => void;

  private bindings: Partial<Record<InvoerActie, ToetsBinding>> = {};
  /** Acties die in de huidige modus bestaan. */
  private toegestaneActies: InvoerActie[] = [];
  private blokkadeTotMs = 0;
  private ingedrukt = new Map<string, number>();
  /** Waar wanneer toetsen acties mogen uitvoeren. */
  private actief = false;
  /** In testmodus worden events wel gemeld maar geen acties uitgevoerd. */
  private alleenMeten = false;

  private doel: EventTarget | null = null;
  private keydownLuisteraar = (event: Event) => this.verwerkDomEvent(event as KeyboardEvent, 'keydown');
  private keyupLuisteraar = (event: Event) => this.verwerkDomEvent(event as KeyboardEvent, 'keyup');

  constructor(opties: InputManagerOpties = {}) {
    this.nu = opties.nu ?? (() => Date.now());
    this.opActie = opties.opActie;
    this.opGeblokkeerd = opties.opGeblokkeerd;
    this.opRuwEvent = opties.opRuwEvent;
  }

  /** Begin met luisteren op een DOM-doel (standaard `window`). */
  start(doel: EventTarget): void {
    this.stop();
    this.doel = doel;
    doel.addEventListener('keydown', this.keydownLuisteraar);
    doel.addEventListener('keyup', this.keyupLuisteraar);
  }

  /** Stop met luisteren en vergeet ingedrukte toetsen. */
  stop(): void {
    if (this.doel) {
      this.doel.removeEventListener('keydown', this.keydownLuisteraar);
      this.doel.removeEventListener('keyup', this.keyupLuisteraar);
      this.doel = null;
    }
    this.ingedrukt.clear();
  }

  /**
   * Stel de toetsen in. `aantalToetsen` bepaalt welke acties beschikbaar zijn:
   * 1 = alleen selecteren, 2 = volgende + selecteren, 3 = ook terug.
   */
  zetBindings(bindings: Record<InvoerActie, ToetsBinding>, aantalToetsen: 1 | 2 | 3): void {
    this.bindings = { ...bindings };
    if (aantalToetsen === 1) this.toegestaneActies = ['select'];
    else if (aantalToetsen === 2) this.toegestaneActies = ['next', 'select'];
    else this.toegestaneActies = ['next', 'select', 'back'];
  }

  /** Acties toestaan of tegenhouden (bijv. tijdens een schermovergang). */
  zetActief(actief: boolean): void {
    this.actief = actief;
    if (!actief) this.ingedrukt.clear();
  }

  /** In meetmodus worden events alleen gerapporteerd (toetstestpagina). */
  zetAlleenMeten(alleenMeten: boolean): void {
    this.alleenMeten = alleenMeten;
  }

  /** Blokkeer invoer voor het opgegeven aantal milliseconden. */
  blokkeer(ms: number): void {
    if (ms <= 0) return;
    this.blokkadeTotMs = Math.max(this.blokkadeTotMs, this.nu() + ms);
  }

  /** Hef een lopende blokkade direct op. */
  hefBlokkadeOp(): void {
    this.blokkadeTotMs = 0;
  }

  /** Waar wanneer invoer op dit moment geblokkeerd is. */
  isGeblokkeerd(tijd: number = this.nu()): boolean {
    return tijd < this.blokkadeTotMs;
  }

  /** Resterende blokkadetijd in milliseconden. */
  restBlokkadeMs(tijd: number = this.nu()): number {
    return Math.max(0, this.blokkadeTotMs - tijd);
  }

  /**
   * Verwerk een toetsevent. Geeft de uitgevoerde actie terug, of `null`
   * wanneer er niets is gebeurd.
   */
  verwerk(event: ToetsEventGegevens): InvoerActie | null {
    const tijd = event.tijd ?? this.nu();
    const code = event.code ?? '';
    const key = event.key ?? '';
    const keyCode = event.keyCode ?? 0;
    const sleutel = code || key || `kc${keyCode}`;

    const gekoppeld = this.zoekActie({ code, key, keyCode });

    // Standaardacties van de browser onderdrukken: alle toetsen met een
    // functie, plus toetsen die van zichzelf scrollen of terugnavigeren.
    if (gekoppeld || heeftBrowserActie({ code, key, keyCode })) {
      event.preventDefault?.();
    }

    if (event.type === 'keyup') {
      const startTijd = this.ingedrukt.get(sleutel);
      this.ingedrukt.delete(sleutel);
      this.opRuwEvent?.({
        type: 'keyup',
        code,
        key,
        keyCode,
        isTrusted: event.isTrusted ?? false,
        repeat: event.repeat ?? false,
        tijd,
        toetsduurMs: startTijd === undefined ? undefined : Math.max(0, tijd - startTijd),
        codeOntbreekt: code === '',
      });
      return null;
    }

    const alIngedrukt = this.ingedrukt.has(sleutel);
    if (!alIngedrukt) this.ingedrukt.set(sleutel, tijd);

    this.opRuwEvent?.({
      type: 'keydown',
      code,
      key,
      keyCode,
      isTrusted: event.isTrusted ?? false,
      repeat: event.repeat ?? false,
      tijd,
      codeOntbreekt: code === '',
    });

    if (!gekoppeld) return null;
    if (this.alleenMeten) return null;
    if (!this.actief) {
      this.opGeblokkeerd?.(gekoppeld, 'inactief', tijd);
      return null;
    }
    if (event.repeat) {
      this.opGeblokkeerd?.(gekoppeld, 'herhaling', tijd);
      return null;
    }
    if (alIngedrukt) {
      this.opGeblokkeerd?.(gekoppeld, 'nogIngedrukt', tijd);
      return null;
    }
    if (this.isGeblokkeerd(tijd)) {
      this.opGeblokkeerd?.(gekoppeld, 'invoerblokkade', tijd);
      return null;
    }

    this.opActie?.(gekoppeld, tijd);
    return gekoppeld;
  }

  /** Zet een echt DOM-event om naar de eenvoudige vorm die we verwerken. */
  private verwerkDomEvent(event: KeyboardEvent, type: 'keydown' | 'keyup'): void {
    this.verwerk({
      type,
      code: event.code,
      key: event.key,
      keyCode: event.keyCode,
      repeat: event.repeat,
      isTrusted: event.isTrusted,
      preventDefault: () => event.preventDefault(),
    });
  }

  /**
   * Zoek de actie die het beste bij het event past. Een match op `code` weegt
   * zwaarder dan op `key`, en die weer zwaarder dan op `keyCode`. Zo wint bij
   * overlappende instellingen altijd de meest specifieke overeenkomst.
   */
  private zoekActie(event: { code: string; key: string; keyCode: number }): InvoerActie | null {
    let beste: InvoerActie | null = null;
    let besteScore = 0;

    for (const actie of ACTIE_VOLGORDE) {
      if (!this.toegestaneActies.includes(actie)) continue;
      const binding = this.bindings[actie];
      if (!binding) continue;
      const score = vergelijk(binding, event);
      if (score > besteScore) {
        besteScore = score;
        beste = actie;
      }
    }
    return beste;
  }
}

/** Bereken hoe goed een binding bij een event past. 0 = geen match. */
export function vergelijk(
  binding: ToetsBinding,
  event: { code?: string; key?: string; keyCode?: number },
): number {
  let score = 0;
  if (binding.code && event.code && binding.code === event.code) score += SCORE_CODE;
  if (binding.key && event.key && gelijkeKey(binding.key, event.key)) score += SCORE_KEY;
  if (binding.keyCode && event.keyCode && binding.keyCode === event.keyCode) score += SCORE_KEYCODE;
  return score;
}

/** Vergelijk `key`-waarden ongeacht hoofdletters; spatie kan ' ' of 'Space' zijn. */
function gelijkeKey(a: string, b: string): boolean {
  const links = normaliseerKey(a);
  const rechts = normaliseerKey(b);
  return links !== '' && links === rechts;
}

function normaliseerKey(waarde: string): string {
  if (waarde === ' ') return 'space';
  const laag = waarde.toLowerCase();
  if (laag === 'spacebar') return 'space';
  if (laag === 'esc') return 'escape';
  if (laag === 'return') return 'enter';
  if (laag === 'del') return 'delete';
  if (laag === 'left') return 'arrowleft';
  if (laag === 'right') return 'arrowright';
  if (laag === 'up') return 'arrowup';
  if (laag === 'down') return 'arrowdown';
  return laag;
}
