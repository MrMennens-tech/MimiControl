/**
 * Tests voor de volledige besturing: selecteren in alle drie de modi,
 * terugnavigatie met herstel van de eerdere focus, en de invoerblokkade die
 * een onbedoelde dubbele toetsaanslag tegenhoudt.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Besturing } from './Besturing';
import { SessionLogger } from './SessionLogger';
import { testAppData } from '../test/voorbeeldInhoud';
import type { GebeurtenisType, Instellingen, InvoerActie } from '../types';

const EVENTS: Record<InvoerActie, { code: string; key: string; keyCode: number }> = {
  next: { code: 'Space', key: ' ', keyCode: 32 },
  select: { code: 'Enter', key: 'Enter', keyCode: 13 },
  back: { code: 'Escape', key: 'Escape', keyCode: 27 },
};

function maakBesturing(instellingen: Partial<Instellingen> = {}) {
  const logger = new SessionLogger({ maakSessiecode: () => 'S-TEST' });
  const besturing = new Besturing({
    appData: testAppData(instellingen),
    logger,
    opStatus: () => undefined,
  });
  besturing.start();

  const druk = (actie: InvoerActie) => {
    besturing.input.verwerk({ type: 'keydown', ...EVENTS[actie] });
    besturing.input.verwerk({ type: 'keyup', ...EVENTS[actie] });
  };

  const typen = (): GebeurtenisType[] =>
    (logger.huidigeSessie?.gebeurtenissen ?? []).map((g) => g.type);

  const van = (type: GebeurtenisType) =>
    (logger.huidigeSessie?.gebeurtenissen ?? []).filter((g) => g.type === type);

  return { besturing, logger, druk, typen, van };
}

beforeEach(() => {
  vi.useFakeTimers();
  return () => vi.useRealTimers();
});

describe('modus 1 - één toets', () => {
  it('scant automatisch en selecteert met de selectietoets', () => {
    const { besturing, druk, van } = maakBesturing({
      controlMode: 1,
      scanIntervalMs: 2000,
      selectionCooldownMs: 500,
      scanRondes: 0,
    });

    expect(besturing.status().focusIndex).toBe(0);
    vi.advanceTimersByTime(2000);
    expect(besturing.status().focusIndex).toBe(1);
    vi.advanceTimersByTime(2000);
    expect(besturing.status().focusIndex).toBe(2);

    druk('select');
    const selecties = van('selectie');
    expect(selecties).toHaveLength(1);
    expect(selecties[0].tegelId).toBe('c');
    expect(selecties[0].positie).toBe(3);
  });

  it('meet de tijd tussen het actief worden van de tegel en de selectie', () => {
    const { druk, van } = maakBesturing({
      controlMode: 1,
      scanIntervalMs: 2000,
      scanRondes: 0,
    });
    vi.advanceTimersByTime(2000); // tegel 2 wordt actief
    vi.advanceTimersByTime(750); // leerling wacht
    druk('select');
    expect(van('selectie')[0].reactietijdMs).toBe(750);
  });

  it('doet niets met de volgende- en terugtoets', () => {
    const { besturing, druk } = maakBesturing({ controlMode: 1, scanIntervalMs: 5000 });
    druk('next');
    druk('back');
    expect(besturing.status().focusIndex).toBe(0);
    expect(besturing.status().schermId).toBe('home');
  });

  it('stopt na het ingestelde aantal scanrondes en meldt dat', () => {
    const { besturing, van } = maakBesturing({
      controlMode: 1,
      scanIntervalMs: 1000,
      scanRondes: 1,
    });
    vi.advanceTimersByTime(4000); // vier tegels, één volledige ronde
    expect(van('scanrondeAfgebroken')).toHaveLength(1);
    expect(besturing.status().scanGestopt).toBe(true);
  });

  it('start de scan opnieuw wanneer er na het stoppen gedrukt wordt', () => {
    const { besturing, druk, van } = maakBesturing({
      controlMode: 1,
      scanIntervalMs: 1000,
      scanRondes: 1,
      selectionCooldownMs: 0,
    });
    vi.advanceTimersByTime(4000);
    expect(besturing.status().scanGestopt).toBe(true);

    druk('select');
    expect(besturing.status().scanGestopt).toBe(false);
    expect(van('selectie')).toHaveLength(0);
    vi.advanceTimersByTime(1000);
    expect(besturing.status().focusIndex).toBe(1);
  });
});

describe('modus 2 - twee toetsen', () => {
  it('zet met toets 1 de markering verder en kiest met toets 2', () => {
    const { besturing, druk, van } = maakBesturing({
      controlMode: 2,
      selectionCooldownMs: 300,
    });
    expect(besturing.status().focusIndex).toBe(0);
    druk('next');
    expect(besturing.status().focusIndex).toBe(1);
    druk('select');
    expect(van('selectie')[0].tegelId).toBe('b');
  });

  it('gaat na de laatste tegel terug naar de eerste', () => {
    const { besturing, druk } = maakBesturing({ controlMode: 2 });
    druk('next');
    druk('next');
    druk('next');
    expect(besturing.status().focusIndex).toBe(3);
    druk('next');
    expect(besturing.status().focusIndex).toBe(0);
  });

  it('scant niet op tijd; er is geen tijdsdruk', () => {
    const { besturing } = maakBesturing({ controlMode: 2, scanIntervalMs: 500 });
    vi.advanceTimersByTime(30000);
    expect(besturing.status().focusIndex).toBe(0);
  });

  it('opent een nieuw scherm na de invoerblokkade', () => {
    const { besturing, druk } = maakBesturing({
      controlMode: 2,
      selectionCooldownMs: 600,
    });
    druk('select'); // tegel A verwijst naar scherm "tweede"
    expect(besturing.status().fase).toBe('overgang');
    expect(besturing.status().schermId).toBe('tweede');

    vi.advanceTimersByTime(600);
    expect(besturing.status().fase).toBe('kiezen');
    expect(besturing.status().tegels.map((t) => t.id)).toEqual(['e', 'f']);
    expect(besturing.status().focusIndex).toBe(0);
  });

  it('doet niets met de terugtoets', () => {
    const { besturing, druk, van } = maakBesturing({ controlMode: 2, selectionCooldownMs: 0 });
    druk('select');
    vi.advanceTimersByTime(300);
    expect(besturing.status().schermId).toBe('tweede');
    druk('back');
    expect(besturing.status().schermId).toBe('tweede');
    expect(van('terug')).toHaveLength(0);
  });
});

describe('modus 3 - drie toetsen', () => {
  it('gaat een scherm terug en markeert de eerder gekozen tegel opnieuw', () => {
    const { besturing, druk, van } = maakBesturing({
      controlMode: 3,
      selectionCooldownMs: 400,
    });

    druk('next'); // tegel B
    druk('next'); // tegel C
    druk('next'); // tegel D
    druk('next'); // terug bij tegel A
    expect(besturing.status().focusIndex).toBe(0);

    druk('select'); // A opent scherm "tweede"
    vi.advanceTimersByTime(400);
    expect(besturing.status().schermId).toBe('tweede');

    druk('next'); // tegel F op het tweede scherm
    expect(besturing.status().focusIndex).toBe(1);

    druk('back');
    vi.advanceTimersByTime(400);
    expect(besturing.status().schermId).toBe('home');
    // De eerder gekozen tegel A staat weer gemarkeerd.
    expect(besturing.status().focusIndex).toBe(0);
    expect(van('terug')).toHaveLength(1);
  });

  it('herstelt de focus ook diep in het menu', () => {
    const { besturing, druk } = maakBesturing({ controlMode: 3, selectionCooldownMs: 0 });

    druk('select'); // A -> tweede
    vi.advanceTimersByTime(300);
    druk('next'); // F
    druk('select'); // F -> derde
    vi.advanceTimersByTime(300);
    expect(besturing.status().schermId).toBe('derde');

    druk('back');
    vi.advanceTimersByTime(300);
    expect(besturing.status().schermId).toBe('tweede');
    expect(besturing.status().focusIndex).toBe(1);

    druk('back');
    vi.advanceTimersByTime(300);
    expect(besturing.status().schermId).toBe('home');
    expect(besturing.status().focusIndex).toBe(0);
  });

  it('doet niets bij terug op het beginscherm', () => {
    const { besturing, druk, van } = maakBesturing({ controlMode: 3 });
    druk('back');
    expect(besturing.status().schermId).toBe('home');
    expect(van('terug')).toHaveLength(0);
    expect(van('terugGenegeerd')).toHaveLength(1);
  });
});

describe('bescherming tegen onbedoelde dubbele activatie', () => {
  it('voert bij twee snelle aanslagen niet direct twee acties uit', () => {
    const { besturing, druk, van } = maakBesturing({
      controlMode: 2,
      selectionCooldownMs: 800,
    });

    druk('select');
    druk('select'); // spasme: meteen nog een aanslag
    druk('select');

    expect(van('selectie')).toHaveLength(1);
    expect(besturing.status().schermId).toBe('tweede');
  });

  it('blokkeert de invoer ook aan het begin van een eindactie en legt dat vast', () => {
    const { besturing, druk, van } = maakBesturing({
      controlMode: 2,
      selectionCooldownMs: 700,
    });

    druk('next'); // tegel B: eindactie
    druk('select');
    expect(besturing.status().fase).toBe('actie');

    vi.advanceTimersByTime(100);
    druk('select'); // valt binnen de invoerblokkade
    expect(besturing.status().fase).toBe('actie');
    expect(van('invoerGeblokkeerd').length).toBeGreaterThan(0);
  });

  it('laat een aanslag na de invoerblokkade wel weer door', () => {
    const { besturing, druk } = maakBesturing({
      controlMode: 2,
      selectionCooldownMs: 400,
    });
    druk('next');
    druk('select'); // eindactie van 1000 ms
    vi.advanceTimersByTime(500);
    druk('select'); // buiten de blokkade: beëindigt de actie
    expect(besturing.status().fase).toBe('overgang');
  });
});

describe('eindacties', () => {
  it('speelt een eindactie en keert daarna terug naar het beginscherm', () => {
    const { besturing, druk, van } = maakBesturing({
      controlMode: 2,
      selectionCooldownMs: 300,
      terugNaActie: 'beginscherm',
    });

    druk('select'); // A -> tweede
    vi.advanceTimersByTime(300);
    druk('select'); // E: eindactie van 1000 ms
    expect(besturing.status().fase).toBe('actie');
    expect(besturing.status().lopendeActie?.tegel.id).toBe('e');

    vi.advanceTimersByTime(1000); // actie loopt af
    vi.advanceTimersByTime(300); // overgang
    expect(besturing.status().fase).toBe('kiezen');
    expect(besturing.status().schermId).toBe('home');
    expect(van('actieGestart')).toHaveLength(1);
    expect(van('actieAfgelopen')).toHaveLength(1);
  });

  it('kan na een eindactie ook op hetzelfde scherm blijven', () => {
    const { besturing, druk } = maakBesturing({
      controlMode: 2,
      selectionCooldownMs: 0,
      terugNaActie: 'blijven',
    });
    druk('next');
    druk('select');
    vi.advanceTimersByTime(1000);
    expect(besturing.status().schermId).toBe('home');
    expect(besturing.status().fase).toBe('kiezen');
  });
});

describe('logboek', () => {
  it('legt de sessiestart, modus, scantijd en geopende schermen vast', () => {
    const { typen } = maakBesturing({ controlMode: 2 });
    expect(typen().slice(0, 4)).toEqual([
      'sessieGestart',
      'modusGekozen',
      'scantijdIngesteld',
      'schermGeopend',
    ]);
  });

  it('legt elke actief geworden tegel vast met positie en label', () => {
    const { druk, van } = maakBesturing({ controlMode: 2 });
    druk('next');
    const actief = van('tegelActief');
    expect(actief[0].positie).toBe(1);
    expect(actief[1].positie).toBe(2);
    expect(actief[1].tegelLabel).toBe('B');
  });

  it('stopt de sessie met een eindtijd', () => {
    const { besturing, logger } = maakBesturing({ controlMode: 2 });
    besturing.stop();
    expect(logger.huidigeSessie?.gestoptOp).toBeTruthy();
    expect(logger.isActief).toBe(false);
  });
});

describe('muis- en aanraakbediening', () => {
  it('kiest een tegel bij een klik wanneer dat is toegestaan', () => {
    const { besturing, van } = maakBesturing({
      controlMode: 2,
      muisBediening: true,
      selectionCooldownMs: 0,
    });
    besturing.klikTegel(2);
    expect(van('selectie')[0].tegelId).toBe('c');
  });

  it('doet niets bij een klik wanneer muisbediening uit staat', () => {
    const { besturing, van } = maakBesturing({ controlMode: 2, muisBediening: false });
    besturing.klikTegel(2);
    expect(van('selectie')).toHaveLength(0);
  });
});
