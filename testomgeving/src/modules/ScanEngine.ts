/**
 * ScanEngine - beheert welke tegel actief (gemarkeerd) is.
 *
 * Modus 1: automatische lineaire scan met een instelbare scantijd. Na een
 * instelbaar aantal rondes stopt de scanner (er is dan geen keuze gemaakt).
 * Modus 2 en 3: handmatige stapscan; iedere `volgende()` zet de markering één
 * tegel verder en na de laatste tegel weer op de eerste. Geen tijdsdruk.
 *
 * De scanvolgorde is altijd de vaste volgorde van de tegels op het scherm:
 * voorspelbaar en identiek op elk scherm.
 */

export type ScanModus = 'automatisch' | 'handmatig';

export interface ScanEngineOpties {
  /** Timerfuncties; instelbaar zodat tests met een nepklok kunnen werken. */
  zetTimer?: (callback: () => void, ms: number) => unknown;
  wisTimer?: (handle: unknown) => void;
  /** Willekeurige startpositie; instelbaar voor voorspelbare tests. */
  willekeurig?: () => number;
  /** Aangeroepen zodra een andere tegel actief wordt. */
  opFocus?: (index: number) => void;
  /** Aangeroepen als een volledige scanronde afgerond is (modus 1). */
  opRondeAf?: (rondeNummer: number) => void;
  /** Aangeroepen als de scanner stopt zonder selectie (rondes verbruikt). */
  opGestopt?: (afgerondeRondes: number) => void;
}

export interface ScanConfiguratie {
  /** Aantal tegels op het scherm. */
  aantal: number;
  modus: ScanModus;
  /** Scantijd per tegel in milliseconden (alleen bij automatisch). */
  intervalMs: number;
  /** Aantal rondes voordat de scanner stopt; 0 = onbeperkt. */
  rondes: number;
  /** Beginpositie: eerste tegel of een willekeurige tegel. */
  startTegel: 'eerste' | 'willekeurig';
  /** Vaste beginindex (bijv. bij teruggaan naar een eerder scherm). */
  startIndex?: number;
}

export class ScanEngine {
  private zetTimer: (callback: () => void, ms: number) => unknown;
  private wisTimer: (handle: unknown) => void;
  private willekeurig: () => number;
  private opFocus?: (index: number) => void;
  private opRondeAf?: (rondeNummer: number) => void;
  private opGestopt?: (afgerondeRondes: number) => void;

  private config: ScanConfiguratie = {
    aantal: 0,
    modus: 'handmatig',
    intervalMs: 2500,
    rondes: 0,
    startTegel: 'eerste',
  };

  private index = 0;
  private rondesGedaan = 0;
  private timer: unknown = null;
  private loopt = false;
  /**
   * Positie waarop een ronde als afgerond geldt: terug bij de beginpositie.
   * Bij een willekeurige start is dat dus de willekeurig gekozen tegel.
   */
  private rondeGrens = 0;

  constructor(opties: ScanEngineOpties = {}) {
    this.zetTimer =
      opties.zetTimer ?? ((callback, ms) => setTimeout(callback, ms) as unknown as number);
    this.wisTimer = opties.wisTimer ?? ((handle) => clearTimeout(handle as number));
    this.willekeurig = opties.willekeurig ?? Math.random;
    this.opFocus = opties.opFocus;
    this.opRondeAf = opties.opRondeAf;
    this.opGestopt = opties.opGestopt;
  }

  /** Huidige actieve tegel; -1 wanneer er geen tegels zijn. */
  get huidigeIndex(): number {
    return this.config.aantal === 0 ? -1 : this.index;
  }

  /** Aantal volledig afgeronde scanrondes sinds de start. */
  get afgerondeRondes(): number {
    return this.rondesGedaan;
  }

  /** Waar wanneer de automatische scan loopt. */
  get isActief(): boolean {
    return this.loopt;
  }

  /**
   * Stel het scherm in en zet de markering op de beginpositie.
   * Roept `opFocus` aan voor de eerste tegel.
   */
  configureer(config: ScanConfiguratie): void {
    this.stop();
    this.config = { ...config };
    this.rondesGedaan = 0;
    this.index = this.bepaalStartIndex();
    this.rondeGrens = this.index;
    if (this.config.aantal > 0) this.opFocus?.(this.index);
  }

  private bepaalStartIndex(): number {
    const { aantal, startIndex, startTegel } = this.config;
    if (aantal <= 0) return 0;
    if (typeof startIndex === 'number' && startIndex >= 0 && startIndex < aantal) {
      return startIndex;
    }
    if (startTegel === 'willekeurig') {
      return Math.min(aantal - 1, Math.max(0, Math.floor(this.willekeurig() * aantal)));
    }
    return 0;
  }

  /** Start de automatische scan (alleen zinvol in modus 1). */
  start(): void {
    if (this.config.modus !== 'automatisch') return;
    if (this.config.aantal <= 0) return;
    if (this.loopt) return;
    this.loopt = true;
    this.planVolgendeStap();
  }

  /** Stop de automatische scan zonder de markering te verplaatsen. */
  stop(): void {
    this.loopt = false;
    if (this.timer !== null) {
      this.wisTimer(this.timer);
      this.timer = null;
    }
  }

  /** Herstart de scan vanaf de beginpositie. */
  herstart(): void {
    this.stop();
    this.rondesGedaan = 0;
    this.index = this.bepaalStartIndex();
    this.rondeGrens = this.index;
    if (this.config.aantal > 0) this.opFocus?.(this.index);
    this.start();
  }

  /**
   * Zet de markering één tegel verder. Wordt gebruikt door de automatische
   * timer en door de "volgende"-toets in modus 2 en 3.
   * Geeft de nieuwe index terug.
   */
  volgende(): number {
    const { aantal } = this.config;
    if (aantal <= 0) return -1;
    const nieuw = (this.index + 1) % aantal;
    const rondeAf = nieuw === this.rondeGrens;
    this.index = nieuw;
    this.opFocus?.(this.index);
    if (rondeAf) {
      this.rondesGedaan += 1;
      this.opRondeAf?.(this.rondesGedaan);
    }
    return this.index;
  }

  /** Zet de markering op een vaste tegel (bijv. na teruggaan). */
  zetIndex(index: number): void {
    const { aantal } = this.config;
    if (aantal <= 0) return;
    const veilig = Math.min(aantal - 1, Math.max(0, index));
    this.index = veilig;
    this.opFocus?.(veilig);
  }

  private planVolgendeStap(): void {
    if (!this.loopt) return;
    this.timer = this.zetTimer(() => {
      this.timer = null;
      if (!this.loopt) return;
      this.volgende();
      const limiet = this.config.rondes;
      if (limiet > 0 && this.rondesGedaan >= limiet) {
        const gedaan = this.rondesGedaan;
        this.stop();
        this.opGestopt?.(gedaan);
        return;
      }
      this.planVolgendeStap();
    }, this.config.intervalMs);
  }
}
