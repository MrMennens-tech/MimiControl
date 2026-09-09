/**
 * Tests voor de importvalidatie, de export en de bewerkingen op de inhoud.
 */

import { describe, expect, it } from 'vitest';
import voorbeeldInhoud from '../../voorbeeld/voorbeeld-inhoud.json';
import {
  exportBestandsnaam,
  exporteerJson,
  nieuweTegel,
  standaardAppData,
  uniekId,
  valideerAppData,
  valideerJsonTekst,
  veiligeKleur,
  veiligId,
  verplaats,
} from './ContentEditor';
import { STANDAARD_INSTELLINGEN } from '../inhoud/standaardInstellingen';

/** Het gegevensmodel uit de opdracht, precies zoals opgegeven. */
const OPDRACHT_VOORBEELD = {
  appVersion: '1.0',
  settings: {
    controlMode: 1,
    scanIntervalMs: 2500,
    selectionCooldownMs: 700,
    speakLabels: true,
    selectionSound: true,
    keys: { next: 'Space', select: 'Enter', back: 'Escape' },
  },
  screens: [
    {
      id: 'home',
      title: 'Wat wil je doen?',
      items: [
        {
          id: 'music',
          label: 'Muziek',
          image: 'assets/music.jpg',
          action: { type: 'navigate', target: 'music-menu' },
        },
      ],
    },
    {
      id: 'music-menu',
      title: 'Welke muziek?',
      items: [{ id: 'rustig', label: 'Rustig', action: { type: 'audio' } }],
    },
  ],
};

describe('importvalidatie', () => {
  it('aanvaardt het gegevensmodel uit de opdracht', () => {
    const resultaat = valideerAppData(OPDRACHT_VOORBEELD);
    expect(resultaat.fouten).toEqual([]);
    expect(resultaat.geldig).toBe(true);
    expect(resultaat.data?.screens).toHaveLength(2);
    expect(resultaat.data?.screens[0].items[0].image).toBe('assets/music.jpg');
  });

  it('zet toetsnamen om naar volledige bindingen met code, key en keyCode', () => {
    const resultaat = valideerAppData(OPDRACHT_VOORBEELD);
    expect(resultaat.data?.settings.keys.next).toEqual({
      code: 'Space',
      key: ' ',
      keyCode: 32,
      naam: 'Spatie',
    });
    expect(resultaat.data?.settings.keys.select.keyCode).toBe(13);
    expect(resultaat.data?.settings.keys.back.code).toBe('Escape');
  });

  it('vult ontbrekende instellingen aan met de standaardwaarden', () => {
    const resultaat = valideerAppData(OPDRACHT_VOORBEELD);
    expect(resultaat.data?.settings.scanRondes).toBe(STANDAARD_INSTELLINGEN.scanRondes);
    expect(resultaat.data?.settings.startTegel).toBe(STANDAARD_INSTELLINGEN.startTegel);
  });

  it('weigert geen JSON', () => {
    const resultaat = valideerJsonTekst('dit is geen json');
    expect(resultaat.geldig).toBe(false);
    expect(resultaat.fouten[0]).toContain('geen geldige JSON');
  });

  it('weigert een bestand zonder schermen', () => {
    const resultaat = valideerAppData({ appVersion: '1.0', settings: {} });
    expect(resultaat.geldig).toBe(false);
    expect(resultaat.fouten.join(' ')).toContain('screens');
  });

  it('weigert een verwijzing naar een onbekend scherm', () => {
    const resultaat = valideerAppData({
      appVersion: '1.0',
      screens: [
        {
          id: 'home',
          title: 'Start',
          items: [{ id: 'x', label: 'X', action: { type: 'navigate', target: 'nergens' } }],
        },
      ],
    });
    expect(resultaat.geldig).toBe(false);
    expect(resultaat.fouten.join(' ')).toContain('nergens');
  });

  it('weigert dubbele scherm-ids', () => {
    const resultaat = valideerAppData({
      appVersion: '1.0',
      screens: [
        { id: 'home', title: 'Een', items: [{ id: 'a', label: 'A', action: { type: 'image' } }] },
        { id: 'home', title: 'Twee', items: [{ id: 'b', label: 'B', action: { type: 'image' } }] },
      ],
    });
    expect(resultaat.geldig).toBe(false);
    expect(resultaat.fouten.join(' ')).toContain('meer dan één keer');
  });

  it('weigert HTML of script in een label', () => {
    const resultaat = valideerAppData({
      appVersion: '1.0',
      screens: [
        {
          id: 'home',
          title: 'Start',
          items: [
            {
              id: 'a',
              label: '<script>alert(1)</script>',
              action: { type: 'image' },
            },
          ],
        },
      ],
    });
    expect(resultaat.geldig).toBe(false);
    expect(resultaat.fouten.join(' ')).toContain('code of HTML');
  });

  it('verwijdert een externe afbeeldingsverwijzing en waarschuwt daarover', () => {
    const resultaat = valideerAppData({
      appVersion: '1.0',
      screens: [
        {
          id: 'home',
          title: 'Start',
          items: [
            {
              id: 'a',
              label: 'A',
              image: 'https://voorbeeld.nl/plaatje.jpg',
              action: { type: 'image' },
            },
          ],
        },
      ],
    });
    expect(resultaat.geldig).toBe(true);
    expect(resultaat.data?.screens[0].items[0].image).toBeUndefined();
    expect(resultaat.waarschuwingen.join(' ')).toContain('niet toegestaan');
  });

  it('verwijdert een javascript-verwijzing in het geluidsveld', () => {
    const resultaat = valideerAppData({
      appVersion: '1.0',
      screens: [
        {
          id: 'home',
          title: 'Start',
          items: [
            {
              id: 'a',
              label: 'A',
              action: { type: 'audio', audio: 'javascript:alert(1)' },
            },
          ],
        },
      ],
    });
    expect(resultaat.data?.screens[0].items[0].action.audio).toBeUndefined();
    expect(resultaat.waarschuwingen.join(' ')).toContain('niet toegestaan');
  });

  it('corrigeert een scantijd buiten de toegestane grenzen', () => {
    const resultaat = valideerAppData({
      appVersion: '1.0',
      settings: { scanIntervalMs: 99999 },
      screens: [
        { id: 'home', title: 'Start', items: [{ id: 'a', label: 'A', action: { type: 'image' } }] },
      ],
    });
    expect(resultaat.data?.settings.scanIntervalMs).toBe(10000);
    expect(resultaat.waarschuwingen.join(' ')).toContain('Scantijd aangepast');
  });

  it('waarschuwt bij meer dan vier tegels op één scherm', () => {
    const items = Array.from({ length: 6 }, (_, i) => ({
      id: `t${i}`,
      label: `T${i}`,
      action: { type: 'image' },
    }));
    const resultaat = valideerAppData({
      appVersion: '1.0',
      screens: [{ id: 'home', title: 'Start', items }],
    });
    expect(resultaat.geldig).toBe(true);
    expect(resultaat.waarschuwingen.join(' ')).toContain('maximaal 4 tegels');
  });

  it('aanvaardt Nederlandse namen voor actietypen', () => {
    const resultaat = valideerAppData({
      appVersion: '1.0',
      screens: [
        {
          id: 'home',
          title: 'Start',
          items: [{ id: 'a', label: 'A', action: { type: 'kleurgolf' } }],
        },
      ],
    });
    expect(resultaat.geldig).toBe(true);
    expect(resultaat.data?.screens[0].items[0].action.type).toBe('colorSweep');
  });

  it('weigert een onbekend actietype', () => {
    const resultaat = valideerAppData({
      appVersion: '1.0',
      screens: [
        {
          id: 'home',
          title: 'Start',
          items: [{ id: 'a', label: 'A', action: { type: 'raketlanceren' } }],
        },
      ],
    });
    expect(resultaat.geldig).toBe(false);
    expect(resultaat.fouten.join(' ')).toContain('onbekend actietype');
  });
});

describe('export', () => {
  it('exporteert geldige JSON die weer te importeren is', () => {
    const data = standaardAppData();
    const tekst = exporteerJson(data);
    const opnieuw = valideerJsonTekst(tekst);
    expect(opnieuw.fouten).toEqual([]);
    expect(opnieuw.geldig).toBe(true);
    expect(opnieuw.data?.screens).toHaveLength(data.screens.length);
  });

  it('gebruikt een bestandsnaam met datum', () => {
    expect(exportBestandsnaam(new Date('2026-03-04T10:00:00Z'))).toBe(
      'toetstest-inhoud-2026-03-04.json',
    );
  });
});

describe('bewerkingen op de inhoud', () => {
  it('verplaatst een element in een lijst', () => {
    expect(verplaats(['a', 'b', 'c'], 0, 2)).toEqual(['b', 'c', 'a']);
    expect(verplaats(['a', 'b', 'c'], 2, 1)).toEqual(['a', 'c', 'b']);
  });

  it('laat de lijst ongemoeid bij een verplaatsing buiten de grenzen', () => {
    expect(verplaats(['a', 'b'], 0, -1)).toEqual(['a', 'b']);
    expect(verplaats(['a', 'b'], 1, 5)).toEqual(['a', 'b']);
  });

  it('maakt unieke ids', () => {
    expect(uniekId('muziek', [])).toBe('muziek');
    expect(uniekId('muziek', ['muziek'])).toBe('muziek-2');
    expect(uniekId('muziek', ['muziek', 'muziek-2'])).toBe('muziek-3');
  });

  it('schoont ids op', () => {
    expect(veiligId('Mijn Nieuwe Scherm!', 'terugval')).toBe('mijn-nieuwe-scherm');
    expect(veiligId('', 'terugval')).toBe('terugval');
  });

  it('aanvaardt alleen hexkleuren', () => {
    expect(veiligeKleur('#2563eb')).toBe('#2563eb');
    expect(veiligeKleur('#abc')).toBe('#abc');
    expect(veiligeKleur('rood')).toBeUndefined();
    expect(veiligeKleur('url(javascript:alert(1))')).toBeUndefined();
  });

  it('maakt een nieuwe tegel met een werkende actie', () => {
    const tegel = nieuweTegel([]);
    expect(tegel.label).toBeTruthy();
    expect(tegel.action.type).toBe('image');
  });
});

describe('meegeleverde voorbeeldinhoud', () => {
  it('bevat vier thema\'s en is geldig', () => {
    const data = standaardAppData();
    const resultaat = valideerAppData(data);
    expect(resultaat.fouten).toEqual([]);
    expect(data.screens[0].items).toHaveLength(4);
  });

  it('heeft nergens meer dan vier tegels per scherm', () => {
    for (const scherm of standaardAppData().screens) {
      expect(scherm.items.length, scherm.id).toBeLessThanOrEqual(4);
    }
  });

  it('bevat op elk scherm minstens één keuze', () => {
    for (const scherm of standaardAppData().screens) {
      expect(scherm.items.length, scherm.id).toBeGreaterThan(0);
    }
  });

  it('kan de meegeleverde voorbeeldconfiguratie importeren', () => {
    const resultaat = valideerJsonTekst(JSON.stringify(voorbeeldInhoud));
    expect(resultaat.fouten).toEqual([]);
    expect(resultaat.waarschuwingen).toEqual([]);
    expect(resultaat.geldig).toBe(true);
    expect(resultaat.data?.screens[0].items).toHaveLength(4);
  });

  it('heeft in elk thema minstens één eindactie te bereiken', () => {
    const data = standaardAppData();
    const eindacties = data.screens.filter((scherm) =>
      scherm.items.some((item) => item.action.type !== 'navigate'),
    );
    // Elk vervolgscherm van een thema eindigt in een eindactie.
    expect(eindacties.length).toBeGreaterThanOrEqual(4);
  });
});
