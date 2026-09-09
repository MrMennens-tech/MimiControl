/**
 * Toetsentabel.
 *
 * MimiControl verstuurt toetsen met de PyAutoGUI-namen (`space`, `enter`,
 * `esc`, `left`, `0`-`9`, ...). De browser ziet die als een KeyboardEvent met
 * `code`, `key` en `keyCode`. Deze tabel legt die drie waarden naast elkaar,
 * zodat een toets ook herkend wordt wanneer één van de drie ontbreekt.
 */

import type { ToetsBinding } from '../types';

interface ToetsRegel {
  /** Naam zoals MimiControl / PyAutoGUI die gebruikt. */
  pyautogui: string;
  /** `KeyboardEvent.code` (afgeleid van de hardware-scancode). */
  code: string;
  /** `KeyboardEvent.key`. */
  key: string;
  /** Verouderde `KeyboardEvent.keyCode`, nog altijd handig als terugval. */
  keyCode: number;
  /** Nederlandse weergavenaam. */
  naam: string;
  /** Deze toets veroorzaakt een standaardactie in de browser (scrollen e.d.). */
  browserActie?: boolean;
}

const REGELS: ToetsRegel[] = [
  { pyautogui: 'space', code: 'Space', key: ' ', keyCode: 32, naam: 'Spatie', browserActie: true },
  { pyautogui: 'enter', code: 'Enter', key: 'Enter', keyCode: 13, naam: 'Enter' },
  { pyautogui: 'esc', code: 'Escape', key: 'Escape', keyCode: 27, naam: 'Escape' },
  { pyautogui: 'tab', code: 'Tab', key: 'Tab', keyCode: 9, naam: 'Tab', browserActie: true },
  { pyautogui: 'backspace', code: 'Backspace', key: 'Backspace', keyCode: 8, naam: 'Backspace', browserActie: true },
  { pyautogui: 'delete', code: 'Delete', key: 'Delete', keyCode: 46, naam: 'Delete' },
  { pyautogui: 'left', code: 'ArrowLeft', key: 'ArrowLeft', keyCode: 37, naam: 'Pijl links', browserActie: true },
  { pyautogui: 'right', code: 'ArrowRight', key: 'ArrowRight', keyCode: 39, naam: 'Pijl rechts', browserActie: true },
  { pyautogui: 'up', code: 'ArrowUp', key: 'ArrowUp', keyCode: 38, naam: 'Pijl omhoog', browserActie: true },
  { pyautogui: 'down', code: 'ArrowDown', key: 'ArrowDown', keyCode: 40, naam: 'Pijl omlaag', browserActie: true },
  { pyautogui: 'pageup', code: 'PageUp', key: 'PageUp', keyCode: 33, naam: 'Page up', browserActie: true },
  { pyautogui: 'pagedown', code: 'PageDown', key: 'PageDown', keyCode: 34, naam: 'Page down', browserActie: true },
  { pyautogui: 'home', code: 'Home', key: 'Home', keyCode: 36, naam: 'Home', browserActie: true },
  { pyautogui: 'end', code: 'End', key: 'End', keyCode: 35, naam: 'End', browserActie: true },
];

// Cijfers 0-9 zoals MimiControl ze kan versturen.
for (let cijfer = 0; cijfer <= 9; cijfer += 1) {
  REGELS.push({
    pyautogui: String(cijfer),
    code: `Digit${cijfer}`,
    key: String(cijfer),
    keyCode: 48 + cijfer,
    naam: `Cijfer ${cijfer}`,
  });
}

// Letters a-z, handig voor tests met een gewoon toetsenbord.
const LETTERS = 'abcdefghijklmnopqrstuvwxyz';
for (const letter of LETTERS) {
  REGELS.push({
    pyautogui: letter,
    code: `Key${letter.toUpperCase()}`,
    key: letter,
    keyCode: letter.toUpperCase().charCodeAt(0),
    naam: `Letter ${letter.toUpperCase()}`,
  });
}

/** Alle toetsen die de app kent, in vaste volgorde. */
export const TOETSEN: readonly ToetsRegel[] = REGELS;

/**
 * Toetsen die in de browser een standaardactie hebben (scrollen, focus
 * verplaatsen, vorige pagina). Die actie moet in de leerlingmodus altijd
 * onderdrukt worden, ook als de toets niet aan een functie is toegewezen.
 */
export const BROWSERACTIE_CODES: readonly string[] = REGELS.filter((r) => r.browserActie).map(
  (r) => r.code,
);

export const BROWSERACTIE_KEYCODES: readonly number[] = REGELS.filter((r) => r.browserActie).map(
  (r) => r.keyCode,
);

/** Waar of de toets in de browser een standaardactie zou uitvoeren. */
export function heeftBrowserActie(gegevens: {
  code?: string;
  key?: string;
  keyCode?: number;
}): boolean {
  const regel = zoekRegel(gegevens);
  return regel?.browserActie === true;
}

function normaliseer(waarde: string): string {
  return waarde.trim().toLowerCase();
}

/** Zoek de tabelregel op basis van (een deel van) de eventgegevens. */
function zoekRegel(gegevens: {
  code?: string;
  key?: string;
  keyCode?: number;
}): ToetsRegel | undefined {
  const { code, key, keyCode } = gegevens;
  if (code) {
    const opCode = REGELS.find((r) => r.code === code);
    if (opCode) return opCode;
  }
  if (key) {
    const genormaliseerd = normaliseer(key) || ' ';
    const opKey = REGELS.find((r) => normaliseer(r.key) === genormaliseerd || r.key === key);
    if (opKey) return opKey;
    const opNaam = REGELS.find(
      (r) => normaliseer(r.pyautogui) === genormaliseerd || normaliseer(r.naam) === genormaliseerd,
    );
    if (opNaam) return opNaam;
  }
  if (typeof keyCode === 'number' && keyCode > 0) {
    const opKeyCode = REGELS.find((r) => r.keyCode === keyCode);
    if (opKeyCode) return opKeyCode;
  }
  return undefined;
}

/**
 * Maak een toetsbinding uit een naam. Aanvaardt zowel MimiControl-namen
 * (`space`, `esc`, `left`) als browsercodes (`Space`, `Escape`, `ArrowLeft`).
 * Onbekende namen leveren een binding die alleen op `code` matcht.
 */
export function bindingUitNaam(naam: string): ToetsBinding {
  const regel = zoekRegel({ code: naam, key: naam });
  if (regel) {
    return { code: regel.code, key: regel.key, keyCode: regel.keyCode, naam: regel.naam };
  }
  return { code: naam, key: naam, keyCode: 0, naam: naam || 'Onbekende toets' };
}

/**
 * Maak een toetsbinding uit een echt toetsevent (functie "toets vastleggen").
 * Ontbrekende velden worden aangevuld uit de tabel, zodat een hulpmiddel
 * zonder scancode alsnog een volledige binding oplevert.
 */
export function bindingUitEvent(event: {
  code?: string;
  key?: string;
  keyCode?: number;
}): ToetsBinding {
  const regel = zoekRegel(event);
  return {
    code: event.code || regel?.code || '',
    key: event.key || regel?.key || '',
    keyCode: event.keyCode || regel?.keyCode || 0,
    naam: regel?.naam || beschrijfOnbekend(event),
  };
}

function beschrijfOnbekend(event: { code?: string; key?: string; keyCode?: number }): string {
  if (event.key && event.key.trim()) return event.key;
  if (event.code) return event.code;
  if (event.keyCode) return `Toetscode ${event.keyCode}`;
  return 'Onbekende toets';
}

/** Korte, leesbare omschrijving van een binding voor de begeleider. */
export function omschrijfBinding(binding: ToetsBinding): string {
  const delen = [binding.naam];
  const technisch: string[] = [];
  if (binding.code) technisch.push(`code: ${binding.code}`);
  if (binding.key) technisch.push(`key: ${binding.key === ' ' ? '␣' : binding.key}`);
  if (binding.keyCode) technisch.push(`keyCode: ${binding.keyCode}`);
  if (technisch.length) delen.push(`(${technisch.join(', ')})`);
  return delen.join(' ');
}
