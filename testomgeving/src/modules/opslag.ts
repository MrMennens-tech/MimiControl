/**
 * Lokale opslag via IndexedDB.
 *
 * Alles blijft op het apparaat: instellingen en inhoud, geüploade
 * afbeeldingen en geluiden, en de sessielogboeken. Er is geen server, geen
 * account en geen enkele verbinding naar buiten.
 *
 * Werkt IndexedDB niet (bijvoorbeeld in een privévenster), dan valt de app
 * terug op geheugenopslag: de app blijft werken, maar bewaart niets.
 */

import type { AppData, Sessie } from '../types';

const DB_NAAM = 'toetsentestomgeving';
const DB_VERSIE = 1;

export const WINKEL_APP = 'app';
export const WINKEL_MEDIA = 'media';
export const WINKEL_SESSIES = 'sessies';

const SLEUTEL_APPDATA = 'appdata';

/** Eén opgeslagen mediabestand (afbeelding of geluid). */
export interface MediaBestand {
  id: string;
  naam: string;
  type: string;
  grootte: number;
  soort: 'afbeelding' | 'audio';
  blob: Blob;
  toegevoegdOp: string;
}

let dbBelofte: Promise<IDBDatabase> | null = null;
/** Terugval wanneer IndexedDB niet beschikbaar is. */
const geheugen = {
  app: new Map<string, unknown>(),
  media: new Map<string, MediaBestand>(),
  sessies: new Map<string, Sessie>(),
};
let gebruiktGeheugen = false;

function openDb(): Promise<IDBDatabase> {
  if (dbBelofte) return dbBelofte;
  dbBelofte = new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('IndexedDB is niet beschikbaar'));
      return;
    }
    const verzoek = indexedDB.open(DB_NAAM, DB_VERSIE);
    verzoek.onupgradeneeded = () => {
      const db = verzoek.result;
      if (!db.objectStoreNames.contains(WINKEL_APP)) db.createObjectStore(WINKEL_APP);
      if (!db.objectStoreNames.contains(WINKEL_MEDIA)) {
        db.createObjectStore(WINKEL_MEDIA, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(WINKEL_SESSIES)) {
        db.createObjectStore(WINKEL_SESSIES, { keyPath: 'sessiecode' });
      }
    };
    verzoek.onsuccess = () => resolve(verzoek.result);
    verzoek.onerror = () => reject(verzoek.error ?? new Error('Kon de database niet openen'));
  });
  return dbBelofte;
}

/** Waar wanneer de app op geheugenopslag is teruggevallen. */
export function isGeheugenopslag(): boolean {
  return gebruiktGeheugen;
}

function transactie<T>(
  winkel: string,
  modus: IDBTransactionMode,
  actie: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  return openDb().then(
    (db) =>
      new Promise<T>((resolve, reject) => {
        const tx = db.transaction(winkel, modus);
        const verzoek = actie(tx.objectStore(winkel));
        verzoek.onsuccess = () => resolve(verzoek.result);
        verzoek.onerror = () => reject(verzoek.error ?? new Error('Opslagfout'));
      }),
  );
}

// --- Instellingen en inhoud ------------------------------------------------

/** Bewaar instellingen en inhoud. */
export async function bewaarAppData(data: AppData): Promise<void> {
  try {
    await transactie(WINKEL_APP, 'readwrite', (store) => store.put(data, SLEUTEL_APPDATA));
  } catch {
    gebruiktGeheugen = true;
    geheugen.app.set(SLEUTEL_APPDATA, data);
  }
}

/** Laad instellingen en inhoud; `null` wanneer er nog niets bewaard is. */
export async function laadAppData(): Promise<AppData | null> {
  try {
    const resultaat = await transactie<AppData | undefined>(WINKEL_APP, 'readonly', (store) =>
      store.get(SLEUTEL_APPDATA),
    );
    return resultaat ?? null;
  } catch {
    gebruiktGeheugen = true;
    return (geheugen.app.get(SLEUTEL_APPDATA) as AppData | undefined) ?? null;
  }
}

// --- Media ----------------------------------------------------------------

/** Bewaar een geüpload bestand en geef het bijbehorende id terug. */
export async function bewaarMedia(bestand: MediaBestand): Promise<string> {
  try {
    await transactie(WINKEL_MEDIA, 'readwrite', (store) => store.put(bestand));
  } catch {
    gebruiktGeheugen = true;
    geheugen.media.set(bestand.id, bestand);
  }
  return bestand.id;
}

/** Haal een mediabestand op; `null` wanneer het ontbreekt. */
export async function laadMedia(id: string): Promise<MediaBestand | null> {
  try {
    const resultaat = await transactie<MediaBestand | undefined>(WINKEL_MEDIA, 'readonly', (store) =>
      store.get(id),
    );
    return resultaat ?? null;
  } catch {
    gebruiktGeheugen = true;
    return geheugen.media.get(id) ?? null;
  }
}

/** Alle mediabestanden, nieuwste eerst. */
export async function laadAlleMedia(): Promise<MediaBestand[]> {
  try {
    const resultaat = await transactie<MediaBestand[]>(WINKEL_MEDIA, 'readonly', (store) =>
      store.getAll(),
    );
    return [...resultaat].sort((a, b) => b.toegevoegdOp.localeCompare(a.toegevoegdOp));
  } catch {
    gebruiktGeheugen = true;
    return [...geheugen.media.values()];
  }
}

/** Verwijder een mediabestand. */
export async function verwijderMedia(id: string): Promise<void> {
  try {
    await transactie(WINKEL_MEDIA, 'readwrite', (store) => store.delete(id));
  } catch {
    gebruiktGeheugen = true;
    geheugen.media.delete(id);
  }
}

// --- Sessies --------------------------------------------------------------

/** Bewaar (of werk bij) een sessie. */
export async function bewaarSessie(sessie: Sessie): Promise<void> {
  try {
    await transactie(WINKEL_SESSIES, 'readwrite', (store) => store.put(sessie));
  } catch {
    gebruiktGeheugen = true;
    geheugen.sessies.set(sessie.sessiecode, sessie);
  }
}

/** Alle bewaarde sessies, nieuwste eerst. */
export async function laadSessies(): Promise<Sessie[]> {
  try {
    const resultaat = await transactie<Sessie[]>(WINKEL_SESSIES, 'readonly', (store) =>
      store.getAll(),
    );
    return [...resultaat].sort((a, b) => b.gestartOp.localeCompare(a.gestartOp));
  } catch {
    gebruiktGeheugen = true;
    return [...geheugen.sessies.values()].sort((a, b) => b.gestartOp.localeCompare(a.gestartOp));
  }
}

/** Verwijder alle sessiegegevens (wisknop in de begeleidersmodus). */
export async function wisAlleSessies(): Promise<void> {
  try {
    await transactie(WINKEL_SESSIES, 'readwrite', (store) => store.clear());
  } catch {
    gebruiktGeheugen = true;
  }
  geheugen.sessies.clear();
}

/** Verwijder alle lokale gegevens: inhoud, media én sessies. */
export async function wisAlles(): Promise<void> {
  try {
    await transactie(WINKEL_APP, 'readwrite', (store) => store.clear());
    await transactie(WINKEL_MEDIA, 'readwrite', (store) => store.clear());
    await transactie(WINKEL_SESSIES, 'readwrite', (store) => store.clear());
  } catch {
    gebruiktGeheugen = true;
  }
  geheugen.app.clear();
  geheugen.media.clear();
  geheugen.sessies.clear();
}

/** Kort, willekeurig id voor een mediabestand. */
export function nieuwMediaId(): string {
  const tekens = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let id = '';
  for (let i = 0; i < 12; i += 1) id += tekens[Math.floor(Math.random() * tekens.length)];
  return id;
}
