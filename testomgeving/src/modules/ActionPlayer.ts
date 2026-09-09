/**
 * ActionPlayer - speelt geluid, spraak en de timing van eindacties.
 *
 * Het beeld (grote afbeelding, kleurgolf, confetti, animatie) wordt door de
 * leerlingmodus getekend; deze module bepaalt hoe lang een actie duurt,
 * speelt geluid en spreekt labels uit. Ontbreekt een geluidsbestand, dan
 * wordt dat netjes overgeslagen en - als spraak aan staat - vervangen door
 * een gesproken benoeming.
 */

import type { Actie, Tegel } from '../types';
import { laadMedia } from './opslag';

export interface ActionPlayerOpties {
  /** Gesproken benoeming aan of uit. */
  spraakAan?: boolean;
  spraakSnelheid?: number;
  /** Selectiegeluid aan of uit. */
  selectiegeluidAan?: boolean;
  /** Basispad voor bestanden die met de app zijn meegeleverd. */
  basisPad?: string;
  /** Aangeroepen wanneer een geluidsbestand niet gespeeld kon worden. */
  opMediaFout?: (verwijzing: string, melding: string) => void;
}

/** Wat er nu op het scherm gebeurt; de leerlingmodus tekent dit. */
export interface LopendeActie {
  tegel: Tegel;
  actie: Actie;
  /** Tijdstip waarop de actie gestart is. */
  gestartOp: number;
  duurMs: number;
}

export class ActionPlayer {
  private spraakAan: boolean;
  private spraakSnelheid: number;
  private selectiegeluidAan: boolean;
  private basisPad: string;
  private opMediaFout?: (verwijzing: string, melding: string) => void;

  private audio: HTMLAudioElement | null = null;
  private objectUrl: string | null = null;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private audioContext: AudioContext | null = null;
  private lopend: LopendeActie | null = null;

  constructor(opties: ActionPlayerOpties = {}) {
    this.spraakAan = opties.spraakAan ?? true;
    this.spraakSnelheid = opties.spraakSnelheid ?? 0.9;
    this.selectiegeluidAan = opties.selectiegeluidAan ?? true;
    this.basisPad = opties.basisPad ?? '';
    this.opMediaFout = opties.opMediaFout;
  }

  /** Werk de instellingen bij zonder de speler opnieuw te maken. */
  zetInstellingen(opties: ActionPlayerOpties): void {
    if (opties.spraakAan !== undefined) this.spraakAan = opties.spraakAan;
    if (opties.spraakSnelheid !== undefined) this.spraakSnelheid = opties.spraakSnelheid;
    if (opties.selectiegeluidAan !== undefined) this.selectiegeluidAan = opties.selectiegeluidAan;
    if (opties.basisPad !== undefined) this.basisPad = opties.basisPad;
  }

  /** De actie die nu loopt, of `null`. */
  get huidigeActie(): LopendeActie | null {
    return this.lopend;
  }

  // --- Spraak -------------------------------------------------------------

  /**
   * Spreek een korte tekst uit. Gebruikt de spraakmodule van het systeem;
   * die werkt offline en heeft geen internetverbinding nodig.
   */
  spreek(tekst: string): void {
    if (!this.spraakAan) return;
    const schoon = tekst.trim();
    if (!schoon) return;
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    try {
      window.speechSynthesis.cancel();
      const uiting = new SpeechSynthesisUtterance(schoon);
      uiting.lang = 'nl-NL';
      uiting.rate = this.spraakSnelheid;
      window.speechSynthesis.speak(uiting);
    } catch {
      // Spraak is een extraatje: mislukt hij, dan gaat de app gewoon door.
    }
  }

  /** Benoem de tegel die net actief geworden is. */
  benoem(tegel: Tegel): void {
    this.spreek(tegel.spreekTekst ?? tegel.label);
  }

  /** Stop de spraak onmiddellijk. */
  stopSpraak(): void {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    try {
      window.speechSynthesis.cancel();
    } catch {
      // niets te doen
    }
  }

  // --- Selectiegeluid -----------------------------------------------------

  /**
   * Kort, zacht selectiegeluid. Wordt met de audio-engine van de browser
   * gemaakt, zodat er geen geluidsbestand nodig is.
   */
  selectiegeluid(): void {
    if (!this.selectiegeluidAan) return;
    if (typeof window === 'undefined' || typeof AudioContext === 'undefined') return;
    try {
      if (!this.audioContext) this.audioContext = new AudioContext();
      const context = this.audioContext;
      if (context.state === 'suspended') void context.resume();
      const nu = context.currentTime;
      const oscillator = context.createOscillator();
      const volume = context.createGain();
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(660, nu);
      oscillator.frequency.linearRampToValueAtTime(880, nu + 0.12);
      volume.gain.setValueAtTime(0.0001, nu);
      volume.gain.linearRampToValueAtTime(0.14, nu + 0.02);
      volume.gain.exponentialRampToValueAtTime(0.0001, nu + 0.22);
      oscillator.connect(volume).connect(context.destination);
      oscillator.start(nu);
      oscillator.stop(nu + 0.24);
    } catch {
      // Geluid is een extraatje.
    }
  }

  // --- Eindacties ---------------------------------------------------------

  /**
   * Start een eindactie. `opKlaar` wordt aangeroepen zodra de actie afgelopen
   * is (of meteen afgebroken wordt).
   */
  async speel(tegel: Tegel, opKlaar: () => void): Promise<void> {
    this.stop();
    const actie = tegel.action;
    const duurMs = actie.duurMs ?? 6000;
    this.lopend = { tegel, actie, gestartOp: Date.now(), duurMs };

    // Gesproken toelichting bij de actie, of anders het label.
    const teVertellen = actie.tekst ?? tegel.spreekTekst ?? tegel.label;
    const heeftGeluidsbestand = Boolean(actie.audio);

    if (heeftGeluidsbestand) {
      const gelukt = await this.speelAudio(actie.audio as string);
      if (!gelukt) this.spreek(teVertellen);
    } else if (actie.type === 'speak' || actie.type === 'animalSound') {
      this.spreek(teVertellen);
    } else if (actie.tekst) {
      this.spreek(actie.tekst);
    }

    this.timer = setTimeout(() => {
      this.timer = null;
      this.opruimenAudio();
      this.lopend = null;
      opKlaar();
    }, duurMs);
  }

  /** Breek een lopende actie af en maak alles schoon. */
  stop(): void {
    if (this.timer !== null) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    this.opruimenAudio();
    this.stopSpraak();
    this.lopend = null;
  }

  /** Start de lopende actie opnieuw vanaf het begin. */
  herstart(opKlaar: () => void): void {
    const lopend = this.lopend;
    if (!lopend) return;
    void this.speel(lopend.tegel, opKlaar);
  }

  /**
   * Zet een mediaverwijzing om naar een URL die de browser kan gebruiken.
   * `media:<id>` komt uit de lokale opslag, andere paden zijn meegeleverde
   * bestanden. Geeft `null` wanneer het bestand ontbreekt.
   */
  async maakMediaUrl(verwijzing: string): Promise<{ url: string; tijdelijk: boolean } | null> {
    if (!verwijzing) return null;
    if (verwijzing.startsWith('media:')) {
      const id = verwijzing.slice('media:'.length);
      const bestand = await laadMedia(id);
      if (!bestand) return null;
      return { url: URL.createObjectURL(bestand.blob), tijdelijk: true };
    }
    return { url: `${this.basisPad}${verwijzing}`, tijdelijk: false };
  }

  /** Speel een geluidsbestand. Geeft `false` als dat niet gelukt is. */
  private async speelAudio(verwijzing: string): Promise<boolean> {
    const bron = await this.maakMediaUrl(verwijzing);
    if (!bron) {
      this.opMediaFout?.(verwijzing, 'Geluidsbestand niet gevonden.');
      return false;
    }
    if (typeof Audio === 'undefined') return false;

    return new Promise<boolean>((resolve) => {
      const audio = new Audio(bron.url);
      this.audio = audio;
      if (bron.tijdelijk) this.objectUrl = bron.url;

      let beantwoord = false;
      const antwoord = (gelukt: boolean, melding?: string) => {
        if (beantwoord) return;
        beantwoord = true;
        if (!gelukt) this.opMediaFout?.(verwijzing, melding ?? 'Geluid kon niet gespeeld worden.');
        resolve(gelukt);
      };

      audio.addEventListener('error', () => antwoord(false, 'Geluidsbestand ontbreekt of is onleesbaar.'));
      audio.addEventListener('playing', () => antwoord(true));
      audio.play().then(
        () => antwoord(true),
        (fout: Error) => antwoord(false, fout.message),
      );
    });
  }

  private opruimenAudio(): void {
    if (this.audio) {
      try {
        this.audio.pause();
        this.audio.src = '';
      } catch {
        // niets te doen
      }
      this.audio = null;
    }
    if (this.objectUrl) {
      URL.revokeObjectURL(this.objectUrl);
      this.objectUrl = null;
    }
  }
}
