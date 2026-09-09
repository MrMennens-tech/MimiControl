/** Kleine, overzichtelijke inhoud voor de tests. */

import type { AppData, Scherm } from '../types';
import { standaardAppData } from '../modules/ContentEditor';

export const TEST_SCHERMEN: Scherm[] = [
  {
    id: 'home',
    title: 'Wat wil je doen?',
    items: [
      { id: 'a', label: 'A', action: { type: 'navigate', target: 'tweede' } },
      { id: 'b', label: 'B', action: { type: 'image', duurMs: 1000 } },
      { id: 'c', label: 'C', action: { type: 'image', duurMs: 1000 } },
      { id: 'd', label: 'D', action: { type: 'image', duurMs: 1000 } },
    ],
  },
  {
    id: 'tweede',
    title: 'Tweede scherm',
    items: [
      { id: 'e', label: 'E', action: { type: 'image', duurMs: 1000 } },
      { id: 'f', label: 'F', action: { type: 'navigate', target: 'derde' } },
    ],
  },
  {
    id: 'derde',
    title: 'Derde scherm',
    items: [{ id: 'g', label: 'G', action: { type: 'image', duurMs: 1000 } }],
  },
];

/** Testgegevens met aanpasbare instellingen. */
export function testAppData(instellingen: Partial<AppData['settings']> = {}): AppData {
  const basis = standaardAppData();
  return {
    appVersion: basis.appVersion,
    settings: { ...basis.settings, ...instellingen },
    screens: JSON.parse(JSON.stringify(TEST_SCHERMEN)) as Scherm[],
  };
}
