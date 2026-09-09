/** Tests voor navigeren en teruggaan, inclusief het herstellen van de focus. */

import { describe, expect, it } from 'vitest';
import { NavigationManager } from './NavigationManager';
import { TEST_SCHERMEN } from '../test/voorbeeldInhoud';

function maakNavigatie(): NavigationManager {
  return new NavigationManager(JSON.parse(JSON.stringify(TEST_SCHERMEN)), 'home');
}

describe('NavigationManager', () => {
  it('begint op het beginscherm en kan dan niet terug', () => {
    const navigatie = maakNavigatie();
    expect(navigatie.huidigSchermId).toBe('home');
    expect(navigatie.kanTerug).toBe(false);
    expect(navigatie.terug()).toBeNull();
    expect(navigatie.huidigSchermId).toBe('home');
  });

  it('opent een scherm en onthoudt de eerder gemarkeerde tegel', () => {
    const navigatie = maakNavigatie();
    expect(navigatie.ga('tweede', 2)).toBe(true);
    expect(navigatie.huidigSchermId).toBe('tweede');

    const vorige = navigatie.terug();
    expect(vorige).toEqual({ schermId: 'home', focusIndex: 2 });
    expect(navigatie.huidigSchermId).toBe('home');
  });

  it('herstelt bij meerdere niveaus telkens de juiste tegel', () => {
    const navigatie = maakNavigatie();
    navigatie.ga('tweede', 0);
    navigatie.ga('derde', 1);
    expect(navigatie.diepte).toBe(2);

    expect(navigatie.terug()).toEqual({ schermId: 'tweede', focusIndex: 1 });
    expect(navigatie.terug()).toEqual({ schermId: 'home', focusIndex: 0 });
    expect(navigatie.terug()).toBeNull();
  });

  it('weigert een onbekend doelscherm', () => {
    const navigatie = maakNavigatie();
    expect(navigatie.ga('bestaat-niet', 0)).toBe(false);
    expect(navigatie.huidigSchermId).toBe('home');
    expect(navigatie.kanTerug).toBe(false);
  });

  it('gaat met naarBegin() terug naar het beginscherm en wist de geschiedenis', () => {
    const navigatie = maakNavigatie();
    navigatie.ga('tweede', 1);
    navigatie.ga('derde', 0);
    navigatie.naarBegin();
    expect(navigatie.huidigSchermId).toBe('home');
    expect(navigatie.kanTerug).toBe(false);
  });
});
