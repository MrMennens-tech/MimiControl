/**
 * SafetyLayer - houdt de omgeving veilig en gesloten.
 *
 * - Externe links worden geblokkeerd: er is geen enkele reden om deze app te
 *   verlaten, en de leerling kan niet per ongeluk op internet belanden.
 * - Geïmporteerde inhoud mag geen HTML, geen scripts en geen externe adressen
 *   bevatten. Alle tekst wordt als tekst weergegeven (React doet dat van
 *   zichzelf; we gebruiken nergens `innerHTML`).
 * - Uploads hebben een maximale bestandsgrootte.
 * - Sessiedata kan met één knop volledig gewist worden.
 */

/** Maximale grootte van een geüploade afbeelding (2 MB). */
export const MAX_AFBEELDING_BYTES = 2 * 1024 * 1024;
/** Maximale grootte van een geüpload audiobestand (5 MB). */
export const MAX_AUDIO_BYTES = 5 * 1024 * 1024;

export const TOEGESTANE_AFBEELDINGSTYPEN = [
  'image/png',
  'image/jpeg',
  'image/webp',
  'image/gif',
  'image/svg+xml',
];
export const TOEGESTANE_AUDIOTYPEN = [
  'audio/mpeg',
  'audio/mp3',
  'audio/wav',
  'audio/x-wav',
  'audio/ogg',
  'audio/webm',
  'audio/mp4',
  'audio/aac',
];

/** Leesbare weergave van een bestandsgrootte. */
export function formatteerBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} kB`;
  return `${(bytes / (1024 * 1024)).toFixed(1).replace('.', ',')} MB`;
}

export interface BestandControle {
  goed: boolean;
  fout?: string;
}

/** Controleer een geüploade afbeelding op type en grootte. */
export function controleerAfbeelding(bestand: { type: string; size: number }): BestandControle {
  if (!TOEGESTANE_AFBEELDINGSTYPEN.includes(bestand.type)) {
    return { goed: false, fout: `Dit bestandstype wordt niet ondersteund (${bestand.type || 'onbekend'}).` };
  }
  if (bestand.size > MAX_AFBEELDING_BYTES) {
    return {
      goed: false,
      fout: `De afbeelding is te groot (${formatteerBytes(bestand.size)}). Maximaal ${formatteerBytes(MAX_AFBEELDING_BYTES)}.`,
    };
  }
  return { goed: true };
}

/** Controleer een geüpload audiobestand op type en grootte. */
export function controleerAudio(bestand: { type: string; size: number }): BestandControle {
  if (!TOEGESTANE_AUDIOTYPEN.includes(bestand.type)) {
    return { goed: false, fout: `Dit bestandstype wordt niet ondersteund (${bestand.type || 'onbekend'}).` };
  }
  if (bestand.size > MAX_AUDIO_BYTES) {
    return {
      goed: false,
      fout: `Het geluidsbestand is te groot (${formatteerBytes(bestand.size)}). Maximaal ${formatteerBytes(MAX_AUDIO_BYTES)}.`,
    };
  }
  return { goed: true };
}

const VERDACHTE_PATRONEN = [
  /<\s*script/i,
  /<\s*iframe/i,
  /<\s*object/i,
  /<\s*embed/i,
  /javascript\s*:/i,
  /vbscript\s*:/i,
  /on[a-z]+\s*=/i,
  /data\s*:\s*text\/html/i,
];

/** Waar wanneer een tekst er uitziet als HTML, script of een gevaarlijke URL. */
export function bevatVerdachteInhoud(waarde: string): boolean {
  return VERDACHTE_PATRONEN.some((patroon) => patroon.test(waarde));
}

/**
 * Maak tekst uit een importbestand veilig: verwijder onzichtbare stuurtekens,
 * kort te lange teksten af en houd het bij platte tekst.
 */
export function veiligeTekst(waarde: unknown, maxLengte = 300): string {
  if (typeof waarde !== 'string') return '';
  return waarde
    .replace(/[\u0000-\u0008\u000b-\u001f\u007f]/g, '')
    .trim()
    .slice(0, maxLengte);
}

/**
 * Waar wanneer een verwijzing naar media toegestaan is. Toegestaan zijn
 * lokale uploads (`media:<id>`) en relatieve paden binnen de app.
 * Absolute adressen (http, https, //, data:) worden geweigerd.
 */
export function isVeiligeMediaVerwijzing(waarde: string): boolean {
  const pad = waarde.trim();
  if (pad === '') return true;
  if (pad.startsWith('media:')) return /^media:[A-Za-z0-9_-]{1,64}$/.test(pad);
  if (/^[a-z][a-z0-9+.-]*:/i.test(pad)) return false;
  if (pad.startsWith('//')) return false;
  if (pad.startsWith('/')) return false;
  if (pad.includes('..')) return false;
  return !bevatVerdachteInhoud(pad);
}

/** Waar wanneer een adres naar buiten de app wijst. */
export function isExterneLink(href: string): boolean {
  const waarde = href.trim();
  if (waarde === '' || waarde.startsWith('#')) return false;
  return /^(https?:|\/\/|mailto:|tel:|ftp:|file:)/i.test(waarde);
}

/**
 * Blokkeer klikken op externe links en het slepen van bestanden in het
 * venster. Geeft een functie terug om het weer uit te zetten.
 */
export function activeerLinkbescherming(document: Document): () => void {
  const opKlik = (event: MouseEvent) => {
    const doel = event.target as Element | null;
    const anker = doel?.closest?.('a');
    if (!anker) return;
    const href = anker.getAttribute('href') ?? '';
    if (isExterneLink(href)) {
      event.preventDefault();
      event.stopPropagation();
    }
  };
  const opSleep = (event: Event) => event.preventDefault();

  document.addEventListener('click', opKlik, true);
  document.addEventListener('dragover', opSleep);
  document.addEventListener('drop', opSleep);

  return () => {
    document.removeEventListener('click', opKlik, true);
    document.removeEventListener('dragover', opSleep);
    document.removeEventListener('drop', opSleep);
  };
}
