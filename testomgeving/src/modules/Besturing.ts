/**
 * Besturing - knoopt de losse modules aan elkaar.
 *
 * Deze module bevat alle toestand van de leerlingmodus en staat volledig los
 * van de gebruikersinterface: de UI vraagt de toestand op en tekent die.
 * Zo is het gedrag (scannen, kiezen, teruggaan, blokkeren) los te testen.
 *
 * Fasen:
 * - `klaar`     : er loopt geen sessie
 * - `kiezen`    : de leerling kan een keuze maken
 * - `overgang`  : net gekozen; invoer is geblokkeerd
 * - `actie`     : een eindactie is in beeld
 */

import type { AppData, Bedieningsmodus, InvoerActie, Scherm, Tegel } from '../types';
import { ActionPlayer, type LopendeActie } from './ActionPlayer';
import { InputManager, type BlokkadeReden, type RuweToetsInfo } from './InputManager';
import { NavigationManager } from './NavigationManager';
import { ScanEngine } from './ScanEngine';
import { SessionLogger } from './SessionLogger';
import { zichtbareItems } from './ContentEditor';

export type Fase = 'klaar' | 'kiezen' | 'overgang' | 'actie';

/** Alles wat de leerlingmodus nodig heeft om te tekenen. */
export interface BesturingStatus {
  fase: Fase;
  schermId: string;
  schermTitel: string;
  tegels: Tegel[];
  focusIndex: number;
  lopendeActie: LopendeActie | null;
  kanTerug: boolean;
  /** Waar wanneer de automatische scan gestopt is zonder keuze. */
  scanGestopt: boolean;
  /** Meldingen over ontbrekende media, voor de begeleider. */
  mediaMeldingen: string[];
}

export interface BesturingOpties {
  appData: AppData;
  logger: SessionLogger;
  /** Aangeroepen bij elke wijziging van de toestand. */
  opStatus: (status: BesturingStatus) => void;
  /** Timerfuncties; instelbaar voor tests. */
  zetTimer?: (callback: () => void, ms: number) => unknown;
  wisTimer?: (handle: unknown) => void;
  nu?: () => number;
  willekeurig?: () => number;
  /** Ruwe toetsevents doorgeven aan de toetstestpagina. */
  opRuwEvent?: (info: RuweToetsInfo) => void;
}

export class Besturing {
  private appData: AppData;
  private logger: SessionLogger;
  private opStatus: (status: BesturingStatus) => void;
  private zetTimer: (callback: () => void, ms: number) => unknown;
  private wisTimer: (handle: unknown) => void;
  private nu: () => number;

  readonly input: InputManager;
  readonly scan: ScanEngine;
  readonly speler: ActionPlayer;
  private navigatie: NavigationManager;

  private fase: Fase = 'klaar';
  private focusIndex = 0;
  private scanGestopt = false;
  private mediaMeldingen: string[] = [];
  private overgangTimer: unknown = null;
  private opRuwEventExtern?: (info: RuweToetsInfo) => void;

  constructor(opties: BesturingOpties) {
    this.appData = opties.appData;
    this.logger = opties.logger;
    this.opStatus = opties.opStatus;
    this.nu = opties.nu ?? (() => Date.now());
    this.zetTimer =
      opties.zetTimer ?? ((callback, ms) => setTimeout(callback, ms) as unknown as number);
    this.wisTimer = opties.wisTimer ?? ((handle) => clearTimeout(handle as number));
    this.opRuwEventExtern = opties.opRuwEvent;

    this.input = new InputManager({
      nu: this.nu,
      opActie: (actie) => this.verwerkActie(actie),
      opGeblokkeerd: (actie, reden) => this.verwerkGeblokkeerd(actie, reden),
      opRuwEvent: (info) => this.opRuwEventExtern?.(info),
    });

    this.scan = new ScanEngine({
      zetTimer: opties.zetTimer,
      wisTimer: opties.wisTimer,
      willekeurig: opties.willekeurig,
      opFocus: (index) => this.verwerkFocus(index),
      opGestopt: (rondes) => this.verwerkScanGestopt(rondes),
    });

    this.speler = new ActionPlayer({
      spraakAan: this.appData.settings.speakLabels,
      spraakSnelheid: this.appData.settings.spraakSnelheid,
      selectiegeluidAan: this.appData.settings.selectionSound,
      opMediaFout: (verwijzing, melding) => this.meldMedia(`${verwijzing}: ${melding}`),
    });

    this.navigatie = new NavigationManager(this.appData.screens, this.startSchermId());
    this.input.zetBindings(this.appData.settings.keys, this.appData.settings.controlMode);
  }

  // --- Toestand -----------------------------------------------------------

  /** Huidige toestand als losse, meegeefbare waarde. */
  status(): BesturingStatus {
    const scherm = this.navigatie.huidigScherm;
    return {
      fase: this.fase,
      schermId: this.navigatie.huidigSchermId,
      schermTitel: scherm?.title ?? 'Geen inhoud gevonden',
      tegels: scherm ? zichtbareItems(scherm) : [],
      focusIndex: this.focusIndex,
      lopendeActie: this.speler.huidigeActie,
      kanTerug: this.navigatie.kanTerug,
      scanGestopt: this.scanGestopt,
      mediaMeldingen: [...this.mediaMeldingen],
    };
  }

  private publiceer(): void {
    this.opStatus(this.status());
  }

  private get instellingen() {
    return this.appData.settings;
  }

  private startSchermId(): string {
    const eerste = this.appData.screens.find((scherm) => scherm.zichtbaar !== false);
    return eerste?.id ?? this.appData.screens[0]?.id ?? '';
  }

  /** Zichtbare tegels van het huidige scherm. */
  private huidigeTegels(): Tegel[] {
    const scherm: Scherm | undefined = this.navigatie.huidigScherm;
    return scherm ? zichtbareItems(scherm) : [];
  }

  // --- Instellingen en inhoud --------------------------------------------

  /** Nieuwe instellingen of inhoud doorvoeren (buiten een sessie). */
  zetAppData(data: AppData): void {
    this.appData = data;
    this.input.zetBindings(data.settings.keys, data.settings.controlMode);
    this.speler.zetInstellingen({
      spraakAan: data.settings.speakLabels,
      spraakSnelheid: data.settings.spraakSnelheid,
      selectiegeluidAan: data.settings.selectionSound,
    });
    this.navigatie.zetSchermen(data.screens, this.startSchermId());
    if (this.fase !== 'klaar') this.configureerScherm();
    this.publiceer();
  }

  // --- Sessie -------------------------------------------------------------

  /** Start de leerlingmodus en het sessielogboek. */
  start(doel?: EventTarget): void {
    this.stopTimers();
    this.speler.stop();
    this.navigatie.naarBegin();
    this.scanGestopt = false;
    this.mediaMeldingen = [];
    this.fase = 'kiezen';

    if (!this.logger.isActief) {
      this.logger.start(this.instellingen.controlMode, this.instellingen.scanIntervalMs);
    }
    if (doel) this.input.start(doel);
    this.input.zetAlleenMeten(false);
    this.input.hefBlokkadeOp();
    this.input.zetActief(true);

    this.logger.leg('schermGeopend', { schermId: this.navigatie.huidigSchermId });
    this.configureerScherm();
    this.publiceer();
  }

  /**
   * Start de leerlingmodus bij een bepaald scherm (functie "voorbeeld
   * bekijken" in de inhoudseditor).
   */
  startVoorbeeld(schermId: string, doel?: EventTarget): void {
    this.start(doel);
    if (!schermId || schermId === this.navigatie.huidigSchermId) return;
    if (!this.navigatie.ga(schermId, 0)) return;
    this.logger.leg('schermGeopend', { schermId });
    this.configureerScherm();
    this.publiceer();
  }

  /**
   * Verlaat de leerlingmodus zonder de sessie af te sluiten, bijvoorbeeld om
   * even in de begeleidersmodus te kijken.
   */
  pauzeer(): void {
    this.stopTimers();
    this.scan.stop();
    this.speler.stop();
    this.input.zetActief(false);
    this.input.stop();
    this.fase = 'klaar';
    this.publiceer();
  }

  /** Stop de leerlingmodus en sluit het sessielogboek. */
  stop(): void {
    this.pauzeer();
    this.logger.stop();
    this.publiceer();
  }

  /** Stel de scanner in voor het huidige scherm. */
  private configureerScherm(startIndex?: number): void {
    const tegels = this.huidigeTegels();
    this.scanGestopt = false;
    this.scan.configureer({
      aantal: tegels.length,
      modus: this.instellingen.controlMode === 1 ? 'automatisch' : 'handmatig',
      intervalMs: this.instellingen.scanIntervalMs,
      rondes: this.instellingen.scanRondes,
      startTegel: this.instellingen.startTegel,
      startIndex,
    });
    if (this.instellingen.controlMode === 1) this.scan.start();
  }

  // --- Reacties op de modules --------------------------------------------

  /** Een andere tegel is actief geworden. */
  private verwerkFocus(index: number): void {
    this.focusIndex = index;
    const tegel = this.huidigeTegels()[index];
    if (tegel) {
      this.logger.legTegelActief({
        schermId: this.navigatie.huidigSchermId,
        tegelId: tegel.id,
        tegelLabel: tegel.label,
        positie: index + 1,
      });
      if (this.instellingen.speakLabels) this.speler.benoem(tegel);
    }
    this.publiceer();
  }

  /** De automatische scan is gestopt zonder dat er gekozen is. */
  private verwerkScanGestopt(rondes: number): void {
    this.scanGestopt = true;
    this.logger.leg('scanrondeAfgebroken', {
      schermId: this.navigatie.huidigSchermId,
      toelichting: `${rondes} scanronde(s) afgelopen zonder selectie`,
    });
    this.publiceer();
  }

  /** Een aanslag is genegeerd; alleen de invoerblokkade wordt gelogd. */
  private verwerkGeblokkeerd(actie: InvoerActie | null, reden: BlokkadeReden): void {
    if (reden !== 'invoerblokkade') return;
    this.logger.leg('invoerGeblokkeerd', {
      schermId: this.navigatie.huidigSchermId,
      toelichting: `${actie ?? 'toets'} genegeerd door de invoerblokkade (${this.instellingen.selectionCooldownMs} ms)`,
    });
    this.publiceer();
  }

  /** Een toets met functie is ingedrukt. */
  private verwerkActie(actie: InvoerActie): void {
    if (this.fase === 'actie') {
      // Tijdens een eindactie beëindigt elke functietoets de actie.
      this.beeindigActie();
      return;
    }
    if (this.fase !== 'kiezen') return;

    if (actie === 'next') {
      this.volgende();
      return;
    }
    if (actie === 'back') {
      this.terug();
      return;
    }
    this.selecteer(this.focusIndex, 'toets');
  }

  /** Zet de markering één tegel verder (modus 2 en 3). */
  private volgende(): void {
    if (this.instellingen.controlMode === 1) return;
    this.scan.volgende();
  }

  /**
   * Selecteer een tegel. `bron` is `toets`, `muis` of `herstart`; alleen voor
   * de logboekregel.
   */
  selecteer(index: number, bron: 'toets' | 'muis'): void {
    if (this.fase !== 'kiezen') return;

    // Is de scanner gestopt, dan zet de selectietoets hem weer aan.
    if (this.scanGestopt && this.instellingen.controlMode === 1 && bron === 'toets') {
      this.logger.leg('notitie', {
        schermId: this.navigatie.huidigSchermId,
        toelichting: 'scan opnieuw gestart na afgelopen scanrondes',
      });
      this.scan.herstart();
      this.scanGestopt = false;
      this.publiceer();
      return;
    }

    const tegels = this.huidigeTegels();
    const tegel = tegels[index];
    if (!tegel) return;

    this.scan.stop();
    this.speler.stopSpraak();
    this.speler.selectiegeluid();
    this.logger.legSelectie({
      schermId: this.navigatie.huidigSchermId,
      tegelId: tegel.id,
      tegelLabel: tegel.label,
      positie: index + 1,
      toelichting: bron === 'muis' ? 'gekozen met muis of aanraking' : 'gekozen met toets',
    });

    if (tegel.action.type === 'navigate' && tegel.action.target) {
      this.overgangNaarScherm(tegel.action.target, index);
      return;
    }
    this.startEindactie(tegel);
  }

  /** Ga naar een ander scherm met een rustige overgang. */
  private overgangNaarScherm(doelId: string, huidigeFocus: number): void {
    const gelukt = this.navigatie.ga(doelId, huidigeFocus);
    if (!gelukt) {
      this.meldMedia(`Scherm "${doelId}" bestaat niet; de keuze is overgeslagen.`);
      this.fase = 'kiezen';
      this.configureerScherm(huidigeFocus);
      this.publiceer();
      return;
    }
    this.fase = 'overgang';
    this.publiceer();
    this.planOvergang(() => {
      this.fase = 'kiezen';
      this.logger.leg('schermGeopend', { schermId: this.navigatie.huidigSchermId });
      this.configureerScherm();
    });
  }

  /** Start de eindactie van een tegel. */
  private startEindactie(tegel: Tegel): void {
    this.fase = 'actie';
    this.logger.leg('actieGestart', {
      schermId: this.navigatie.huidigSchermId,
      tegelId: tegel.id,
      tegelLabel: tegel.label,
      toelichting: tegel.action.type,
    });
    // Tijdens de eerste milliseconden van de actie blijft invoer geblokkeerd,
    // zodat een spasme de actie niet meteen weer afbreekt.
    this.input.blokkeer(Math.max(this.instellingen.selectionCooldownMs, 400));
    void this.speler.speel(tegel, () => this.beeindigActie());
    this.publiceer();
  }

  /** Rond de eindactie af en ga terug volgens de instelling. */
  private beeindigActie(): void {
    if (this.fase !== 'actie') return;
    const lopend = this.speler.huidigeActie;
    this.speler.stop();
    this.logger.leg('actieAfgelopen', {
      schermId: this.navigatie.huidigSchermId,
      tegelId: lopend?.tegel.id,
      tegelLabel: lopend?.tegel.label,
    });

    const terugNaActie = this.instellingen.terugNaActie;
    if (terugNaActie === 'blijven') {
      this.fase = 'kiezen';
      this.configureerScherm(this.focusIndex);
      this.publiceer();
      return;
    }

    this.fase = 'overgang';
    this.publiceer();
    this.planOvergang(() => {
      if (terugNaActie === 'beginscherm') {
        this.navigatie.naarBegin();
      } else {
        const vorige = this.navigatie.terug();
        if (vorige) {
          this.fase = 'kiezen';
          this.logger.leg('schermGeopend', { schermId: this.navigatie.huidigSchermId });
          this.configureerScherm(vorige.focusIndex);
          return;
        }
        this.navigatie.naarBegin();
      }
      this.fase = 'kiezen';
      this.logger.leg('schermGeopend', { schermId: this.navigatie.huidigSchermId });
      this.configureerScherm();
    });
  }

  /** Eén scherm terug (modus 3). Op het beginscherm gebeurt er niets. */
  terug(): void {
    if (this.fase !== 'kiezen') return;
    if (this.instellingen.controlMode !== 3) return;

    const vorige = this.navigatie.terug();
    if (!vorige) {
      this.logger.leg('terugGenegeerd', {
        schermId: this.navigatie.huidigSchermId,
        toelichting: 'terug op het beginscherm doet niets',
      });
      this.publiceer();
      return;
    }

    this.logger.leg('terug', {
      schermId: vorige.schermId,
      positie: vorige.focusIndex + 1,
      toelichting: 'eerder gekozen tegel wordt opnieuw gemarkeerd',
    });
    this.scan.stop();
    this.speler.stopSpraak();
    this.fase = 'overgang';
    this.publiceer();
    this.planOvergang(() => {
      this.fase = 'kiezen';
      this.logger.leg('schermGeopend', { schermId: this.navigatie.huidigSchermId });
      this.configureerScherm(vorige.focusIndex);
    });
  }

  /** Muis- of aanraakselectie (voor tests door de begeleider). */
  klikTegel(index: number): void {
    if (!this.instellingen.muisBediening) return;
    if (this.fase === 'actie') {
      this.beeindigActie();
      return;
    }
    if (this.fase !== 'kiezen') return;
    this.scan.zetIndex(index);
    this.selecteer(index, 'muis');
  }

  /** Zet de scanner weer aan nadat de rondes afgelopen waren. */
  herstartScan(): void {
    if (this.fase !== 'kiezen') return;
    this.scanGestopt = false;
    this.scan.herstart();
    this.publiceer();
  }

  /** Zet de toetsentestmodus aan of uit (geen acties, alleen meten). */
  zetAlleenMeten(alleenMeten: boolean): void {
    this.input.zetAlleenMeten(alleenMeten);
  }

  /** Begin met luisteren naar toetsen zonder een sessie te starten. */
  luister(doel: EventTarget): void {
    this.input.start(doel);
  }

  /** Stop met luisteren naar toetsen. */
  stopLuisteren(): void {
    this.input.stop();
  }

  /** Toon de ruwe toetsevents ergens anders (toetstestpagina). */
  zetRuweEventLuisteraar(luisteraar?: (info: RuweToetsInfo) => void): void {
    this.opRuwEventExtern = luisteraar;
  }

  /** Huidige bedieningsmodus. */
  get modus(): Bedieningsmodus {
    return this.instellingen.controlMode;
  }

  private planOvergang(fn: () => void): void {
    const ms = Math.max(250, this.instellingen.selectionCooldownMs);
    this.input.blokkeer(ms);
    this.input.zetActief(false);
    this.stopTimers();
    this.overgangTimer = this.zetTimer(() => {
      this.overgangTimer = null;
      fn();
      this.input.zetActief(true);
      this.publiceer();
    }, ms);
  }

  private stopTimers(): void {
    if (this.overgangTimer !== null) {
      this.wisTimer(this.overgangTimer);
      this.overgangTimer = null;
    }
  }

  private meldMedia(melding: string): void {
    this.mediaMeldingen = [melding, ...this.mediaMeldingen].slice(0, 20);
  }
}
