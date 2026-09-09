/**
 * Tests voor de invoerbeheerder: toetsherkenning (ook zonder scancode),
 * invoerblokkade tegen dubbele activatie en het onderdrukken van
 * standaardacties van de browser.
 */

import { describe, expect, it, vi } from 'vitest';
import { InputManager, type ToetsEventGegevens } from './InputManager';
import { bindingUitNaam } from './toetsnamen';
import type { InvoerActie, ToetsBinding } from '../types';

const TOETSEN: Record<InvoerActie, ToetsBinding> = {
  next: bindingUitNaam('Space'),
  select: bindingUitNaam('Enter'),
  back: bindingUitNaam('Escape'),
};

interface Opzet {
  manager: InputManager;
  acties: InvoerActie[];
  geblokkeerd: { actie: InvoerActie | null; reden: string }[];
  klok: { waarde: number };
}

function maakManager(aantalToetsen: 1 | 2 | 3 = 3): Opzet {
  const klok = { waarde: 1000 };
  const acties: InvoerActie[] = [];
  const geblokkeerd: { actie: InvoerActie | null; reden: string }[] = [];
  const manager = new InputManager({
    nu: () => klok.waarde,
    opActie: (actie) => acties.push(actie),
    opGeblokkeerd: (actie, reden) => geblokkeerd.push({ actie, reden }),
  });
  manager.zetBindings(TOETSEN, aantalToetsen);
  manager.zetActief(true);
  return { manager, acties, geblokkeerd, klok };
}

/** Volledige aanslag: keydown gevolgd door keyup. */
function drukEnLaatLos(opzet: Opzet, event: Partial<ToetsEventGegevens>): void {
  opzet.manager.verwerk({ type: 'keydown', ...event });
  opzet.manager.verwerk({ type: 'keyup', ...event });
}

describe('toetsherkenning', () => {
  it('herkent een toets op code', () => {
    const opzet = maakManager();
    drukEnLaatLos(opzet, { code: 'Enter', key: 'Enter', keyCode: 13 });
    expect(opzet.acties).toEqual(['select']);
  });

  it('herkent spatie als "volgende"', () => {
    const opzet = maakManager();
    drukEnLaatLos(opzet, { code: 'Space', key: ' ', keyCode: 32 });
    expect(opzet.acties).toEqual(['next']);
  });

  it('herkent de toets ook wanneer code leeg is (hulpmiddel zonder scancode)', () => {
    const opzet = maakManager();
    drukEnLaatLos(opzet, { code: '', key: 'Enter', keyCode: 13 });
    expect(opzet.acties).toEqual(['select']);
  });

  it('herkent de toets als alleen keyCode klopt', () => {
    const opzet = maakManager();
    drukEnLaatLos(opzet, { code: '', key: '', keyCode: 32 });
    expect(opzet.acties).toEqual(['next']);
  });

  it('negeert toetsen zonder functie', () => {
    const opzet = maakManager();
    drukEnLaatLos(opzet, { code: 'KeyQ', key: 'q', keyCode: 81 });
    expect(opzet.acties).toEqual([]);
  });

  it('kiest bij overlap de match op code boven die op keyCode', () => {
    const klok = { waarde: 0 };
    const acties: InvoerActie[] = [];
    const manager = new InputManager({ nu: () => klok.waarde, opActie: (a) => acties.push(a) });
    // "next" matcht alleen op keyCode 13, "select" op code Enter.
    manager.zetBindings(
      {
        next: { code: 'Onbekend', key: '', keyCode: 13, naam: 'Vreemd' },
        select: bindingUitNaam('Enter'),
        back: bindingUitNaam('Escape'),
      },
      3,
    );
    manager.zetActief(true);
    manager.verwerk({ type: 'keydown', code: 'Enter', key: 'Enter', keyCode: 13 });
    expect(acties).toEqual(['select']);
  });
});

describe('beschikbare acties per modus', () => {
  it('gebruikt in modus 1 alleen de selectietoets', () => {
    const opzet = maakManager(1);
    drukEnLaatLos(opzet, { code: 'Space', key: ' ', keyCode: 32 });
    drukEnLaatLos(opzet, { code: 'Escape', key: 'Escape', keyCode: 27 });
    drukEnLaatLos(opzet, { code: 'Enter', key: 'Enter', keyCode: 13 });
    expect(opzet.acties).toEqual(['select']);
  });

  it('gebruikt in modus 2 volgende en selecteren, maar niet terug', () => {
    const opzet = maakManager(2);
    drukEnLaatLos(opzet, { code: 'Space', key: ' ', keyCode: 32 });
    drukEnLaatLos(opzet, { code: 'Escape', key: 'Escape', keyCode: 27 });
    drukEnLaatLos(opzet, { code: 'Enter', key: 'Enter', keyCode: 13 });
    expect(opzet.acties).toEqual(['next', 'select']);
  });

  it('gebruikt in modus 3 alle drie de toetsen', () => {
    const opzet = maakManager(3);
    drukEnLaatLos(opzet, { code: 'Space', key: ' ', keyCode: 32 });
    drukEnLaatLos(opzet, { code: 'Enter', key: 'Enter', keyCode: 13 });
    drukEnLaatLos(opzet, { code: 'Escape', key: 'Escape', keyCode: 27 });
    expect(opzet.acties).toEqual(['next', 'select', 'back']);
  });
});

describe('bescherming tegen dubbele activatie', () => {
  it('negeert een tweede aanslag binnen de invoerblokkade', () => {
    const opzet = maakManager();
    drukEnLaatLos(opzet, { code: 'Enter', key: 'Enter', keyCode: 13 });
    opzet.manager.blokkeer(700);

    opzet.klok.waarde += 120; // spasme kort na de eerste aanslag
    drukEnLaatLos(opzet, { code: 'Enter', key: 'Enter', keyCode: 13 });

    expect(opzet.acties).toEqual(['select']);
    expect(opzet.geblokkeerd.map((g) => g.reden)).toEqual(['invoerblokkade']);
  });

  it('laat een aanslag na de invoerblokkade weer door', () => {
    const opzet = maakManager();
    drukEnLaatLos(opzet, { code: 'Enter', key: 'Enter', keyCode: 13 });
    opzet.manager.blokkeer(700);

    opzet.klok.waarde += 701;
    drukEnLaatLos(opzet, { code: 'Enter', key: 'Enter', keyCode: 13 });

    expect(opzet.acties).toEqual(['select', 'select']);
  });

  it('negeert automatische toetsherhaling', () => {
    const opzet = maakManager();
    opzet.manager.verwerk({ type: 'keydown', code: 'Enter', key: 'Enter', keyCode: 13 });
    opzet.manager.verwerk({
      type: 'keydown',
      code: 'Enter',
      key: 'Enter',
      keyCode: 13,
      repeat: true,
    });
    expect(opzet.acties).toEqual(['select']);
    expect(opzet.geblokkeerd.map((g) => g.reden)).toContain('herhaling');
  });

  it('negeert een tweede keydown zolang de toets niet is losgelaten', () => {
    const opzet = maakManager();
    opzet.manager.verwerk({ type: 'keydown', code: 'Enter', key: 'Enter', keyCode: 13 });
    opzet.klok.waarde += 50;
    opzet.manager.verwerk({ type: 'keydown', code: 'Enter', key: 'Enter', keyCode: 13 });
    expect(opzet.acties).toEqual(['select']);
    expect(opzet.geblokkeerd.map((g) => g.reden)).toContain('nogIngedrukt');
  });

  it('voert niets uit wanneer de invoer niet actief is', () => {
    const opzet = maakManager();
    opzet.manager.zetActief(false);
    drukEnLaatLos(opzet, { code: 'Enter', key: 'Enter', keyCode: 13 });
    expect(opzet.acties).toEqual([]);
    expect(opzet.geblokkeerd.map((g) => g.reden)).toEqual(['inactief']);
  });
});

describe('standaardacties van de browser', () => {
  it('onderdrukt spatie, ook als die geen functie heeft', () => {
    const opzet = maakManager(1); // in modus 1 heeft spatie geen functie
    const preventDefault = vi.fn();
    opzet.manager.verwerk({ type: 'keydown', code: 'Space', key: ' ', keyCode: 32, preventDefault });
    expect(preventDefault).toHaveBeenCalledTimes(1);
  });

  it('onderdrukt de pijltjestoetsen', () => {
    const opzet = maakManager();
    for (const code of ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']) {
      const preventDefault = vi.fn();
      opzet.manager.verwerk({ type: 'keydown', code, key: code, preventDefault });
      expect(preventDefault, code).toHaveBeenCalledTimes(1);
    }
  });

  it('onderdrukt page up, page down, home, end, tab en backspace', () => {
    const opzet = maakManager();
    for (const code of ['PageUp', 'PageDown', 'Home', 'End', 'Tab', 'Backspace']) {
      const preventDefault = vi.fn();
      opzet.manager.verwerk({ type: 'keydown', code, key: code, preventDefault });
      expect(preventDefault, code).toHaveBeenCalledTimes(1);
    }
  });

  it('onderdrukt een toets met functie ook als de browser er niets mee doet', () => {
    const opzet = maakManager();
    const preventDefault = vi.fn();
    opzet.manager.verwerk({
      type: 'keydown',
      code: 'Enter',
      key: 'Enter',
      keyCode: 13,
      preventDefault,
    });
    expect(preventDefault).toHaveBeenCalledTimes(1);
  });

  it('laat gewone letters ongemoeid', () => {
    const opzet = maakManager();
    const preventDefault = vi.fn();
    opzet.manager.verwerk({ type: 'keydown', code: 'KeyQ', key: 'q', keyCode: 81, preventDefault });
    expect(preventDefault).not.toHaveBeenCalled();
  });
});

describe('meetmodus voor de toetstestpagina', () => {
  it('meldt alle events met code, key, keyCode en isTrusted', () => {
    const events: { code: string; key: string; keyCode: number; isTrusted: boolean }[] = [];
    const manager = new InputManager({
      nu: () => 0,
      opRuwEvent: (info) =>
        events.push({
          code: info.code,
          key: info.key,
          keyCode: info.keyCode,
          isTrusted: info.isTrusted,
        }),
    });
    manager.zetAlleenMeten(true);
    manager.verwerk({ type: 'keydown', code: 'Space', key: ' ', keyCode: 32, isTrusted: true });
    expect(events).toEqual([{ code: 'Space', key: ' ', keyCode: 32, isTrusted: true }]);
  });

  it('markeert een lege code en meet de toetsduur', () => {
    const klok = { waarde: 500 };
    const infos: { codeOntbreekt: boolean; duur?: number }[] = [];
    const manager = new InputManager({
      nu: () => klok.waarde,
      opRuwEvent: (info) => infos.push({ codeOntbreekt: info.codeOntbreekt, duur: info.toetsduurMs }),
    });
    manager.zetAlleenMeten(true);

    manager.verwerk({ type: 'keydown', code: '', key: 'Enter', keyCode: 13 });
    klok.waarde += 100; // MimiControl houdt de toets standaard 100 ms vast
    manager.verwerk({ type: 'keyup', code: '', key: 'Enter', keyCode: 13 });

    expect(infos[0].codeOntbreekt).toBe(true);
    expect(infos[1].duur).toBe(100);
  });

  it('voert in meetmodus geen acties uit', () => {
    const opzet = maakManager();
    opzet.manager.zetAlleenMeten(true);
    drukEnLaatLos(opzet, { code: 'Enter', key: 'Enter', keyCode: 13 });
    expect(opzet.acties).toEqual([]);
  });
});
