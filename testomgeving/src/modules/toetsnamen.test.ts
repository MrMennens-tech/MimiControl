/**
 * Tests voor de toetsentabel: de namen die MimiControl gebruikt moeten
 * omgezet worden naar de juiste browserwaarden, en een event zonder
 * scancode moet alsnog een volledige binding opleveren.
 */

import { describe, expect, it } from 'vitest';
import {
  bindingUitEvent,
  bindingUitNaam,
  heeftBrowserActie,
  omschrijfBinding,
} from './toetsnamen';

describe('bindingUitNaam', () => {
  it('zet MimiControl-namen om naar browserwaarden', () => {
    expect(bindingUitNaam('space')).toEqual({
      code: 'Space',
      key: ' ',
      keyCode: 32,
      naam: 'Spatie',
    });
    expect(bindingUitNaam('esc')).toEqual({
      code: 'Escape',
      key: 'Escape',
      keyCode: 27,
      naam: 'Escape',
    });
    expect(bindingUitNaam('left').code).toBe('ArrowLeft');
    expect(bindingUitNaam('pagedown').keyCode).toBe(34);
  });

  it('kent de cijfers 0 tot 9', () => {
    expect(bindingUitNaam('0')).toEqual({
      code: 'Digit0',
      key: '0',
      keyCode: 48,
      naam: 'Cijfer 0',
    });
    expect(bindingUitNaam('9').keyCode).toBe(57);
  });

  it('aanvaardt ook browsernamen', () => {
    expect(bindingUitNaam('Space').keyCode).toBe(32);
    expect(bindingUitNaam('ArrowUp').keyCode).toBe(38);
    expect(bindingUitNaam('Escape').code).toBe('Escape');
  });

  it('levert een bruikbare binding bij een onbekende naam', () => {
    const binding = bindingUitNaam('F13');
    expect(binding.code).toBe('F13');
    expect(binding.keyCode).toBe(0);
  });
});

describe('bindingUitEvent', () => {
  it('gebruikt de waarden uit het event', () => {
    expect(bindingUitEvent({ code: 'Enter', key: 'Enter', keyCode: 13 })).toEqual({
      code: 'Enter',
      key: 'Enter',
      keyCode: 13,
      naam: 'Enter',
    });
  });

  it('vult een ontbrekende code aan uit de tabel (hulpmiddel zonder scancode)', () => {
    const binding = bindingUitEvent({ code: '', key: 'Enter', keyCode: 13 });
    expect(binding.code).toBe('Enter');
    expect(binding.key).toBe('Enter');
    expect(binding.keyCode).toBe(13);
  });

  it('vult een ontbrekende key aan wanneer alleen de keyCode bekend is', () => {
    const binding = bindingUitEvent({ code: '', key: '', keyCode: 32 });
    expect(binding.code).toBe('Space');
    expect(binding.key).toBe(' ');
    expect(binding.naam).toBe('Spatie');
  });

  it('beschrijft een volstrekt onbekende toets zonder te bezwijken', () => {
    const binding = bindingUitEvent({ code: '', key: '', keyCode: 0 });
    expect(binding.naam).toBe('Onbekende toets');
  });
});

describe('standaardacties van de browser', () => {
  it('herkent toetsen die scrollen of terugnavigeren', () => {
    expect(heeftBrowserActie({ code: 'Space' })).toBe(true);
    expect(heeftBrowserActie({ code: 'ArrowDown' })).toBe(true);
    expect(heeftBrowserActie({ code: 'Backspace' })).toBe(true);
    expect(heeftBrowserActie({ code: 'Tab' })).toBe(true);
  });

  it('herkent ze ook zonder code, via key of keyCode', () => {
    expect(heeftBrowserActie({ key: ' ' })).toBe(true);
    expect(heeftBrowserActie({ keyCode: 40 })).toBe(true);
  });

  it('meldt gewone toetsen als onschuldig', () => {
    expect(heeftBrowserActie({ code: 'Enter' })).toBe(false);
    expect(heeftBrowserActie({ code: 'KeyA' })).toBe(false);
  });
});

describe('omschrijfBinding', () => {
  it('toont naam, code, key en keyCode voor de begeleider', () => {
    const tekst = omschrijfBinding(bindingUitNaam('space'));
    expect(tekst).toContain('Spatie');
    expect(tekst).toContain('code: Space');
    expect(tekst).toContain('keyCode: 32');
  });
});
