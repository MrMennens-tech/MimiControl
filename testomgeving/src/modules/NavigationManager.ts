/**
 * NavigationManager - opent schermen en bewaart de geschiedenis.
 *
 * Bij het openen van een nieuw scherm wordt de tegel die op het vorige scherm
 * gekozen was onthouden. Gaat de leerling een scherm terug, dan wordt die
 * tegel opnieuw gemarkeerd, zodat de omgeving voorspelbaar blijft.
 * Op het beginscherm doet terug niets.
 */

import type { Scherm } from '../types';

export interface GeschiedenisItem {
  schermId: string;
  /** Index van de tegel die op dat scherm gemarkeerd was. */
  focusIndex: number;
}

export class NavigationManager {
  private schermen: Scherm[];
  private startId: string;
  private huidig: string;
  private geschiedenis: GeschiedenisItem[] = [];

  constructor(schermen: Scherm[], startId?: string) {
    this.schermen = schermen;
    this.startId = startId ?? schermen[0]?.id ?? '';
    this.huidig = this.startId;
  }

  /** Id van het scherm dat nu open staat. */
  get huidigSchermId(): string {
    return this.huidig;
  }

  /** Het scherm dat nu open staat, of `undefined` bij ontbrekende inhoud. */
  get huidigScherm(): Scherm | undefined {
    return this.schermen.find((scherm) => scherm.id === this.huidig);
  }

  /** Waar wanneer er een scherm is om naar terug te gaan. */
  get kanTerug(): boolean {
    return this.geschiedenis.length > 0;
  }

  /** Aantal schermen in de geschiedenis (diepte in het menu). */
  get diepte(): number {
    return this.geschiedenis.length;
  }

  /** Vervang de inhoud, bijvoorbeeld na een import. */
  zetSchermen(schermen: Scherm[], startId?: string): void {
    this.schermen = schermen;
    this.startId = startId ?? schermen[0]?.id ?? '';
    this.huidig = this.startId;
    this.geschiedenis = [];
  }

  /**
   * Open een scherm. `huidigeFocus` is de tegel die op het huidige scherm
   * gemarkeerd stond; die wordt bewaard voor het teruggaan.
   * Geeft `false` bij een onbekend doelscherm (inhoud kan onvolledig zijn).
   */
  ga(schermId: string, huidigeFocus: number): boolean {
    const bestaat = this.schermen.some((scherm) => scherm.id === schermId);
    if (!bestaat) return false;
    if (schermId === this.huidig) return false;
    this.geschiedenis.push({ schermId: this.huidig, focusIndex: huidigeFocus });
    this.huidig = schermId;
    return true;
  }

  /**
   * Ga één scherm terug. Geeft het herstelde scherm met de eerder gekozen
   * tegel terug, of `null` op het beginscherm.
   */
  terug(): GeschiedenisItem | null {
    const vorige = this.geschiedenis.pop();
    if (!vorige) return null;
    this.huidig = vorige.schermId;
    return vorige;
  }

  /** Terug naar het beginscherm en de geschiedenis wissen. */
  naarBegin(): void {
    this.huidig = this.startId;
    this.geschiedenis = [];
  }
}
