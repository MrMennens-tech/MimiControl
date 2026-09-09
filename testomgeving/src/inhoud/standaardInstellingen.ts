/** Standaardinstellingen van de testomgeving. */

import type { Instellingen } from '../types';
import { bindingUitNaam } from '../modules/toetsnamen';

export const APP_VERSIE = '1.0';

/** Grenzen voor de scantijd, zoals in de opdracht vastgelegd. */
export const SCANTIJD_MIN_MS = 500;
export const SCANTIJD_MAX_MS = 10000;

/** Grenzen voor de invoerblokkade na een selectie. */
export const BLOKKADE_MIN_MS = 0;
export const BLOKKADE_MAX_MS = 5000;

/** Maximaal aantal tegels per scherm in de leerlingmodus. */
export const MAX_TEGELS_PER_SCHERM = 4;

export const STANDAARD_INSTELLINGEN: Instellingen = {
  controlMode: 1,
  scanIntervalMs: 2500,
  selectionCooldownMs: 700,
  speakLabels: true,
  selectionSound: true,
  keys: {
    next: bindingUitNaam('Space'),
    select: bindingUitNaam('Enter'),
    back: bindingUitNaam('Escape'),
  },
  scanRondes: 3,
  startTegel: 'eerste',
  terugNaActie: 'beginscherm',
  volledigSchermStarten: false,
  spraakSnelheid: 0.9,
  muisBediening: true,
  pincode: '1234',
};
