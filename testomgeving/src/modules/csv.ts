/**
 * CSV-export van sessiegegevens.
 *
 * We gebruiken een puntkomma als scheidingsteken; dat opent in de
 * Nederlandse instelling van Excel direct in kolommen. Waarden worden
 * altijd geciteerd wanneer ze een scheidingsteken, aanhalingsteken of
 * regeleinde bevatten, en een BOM zorgt dat accenten goed weergegeven worden.
 */

import type { Gebeurtenis, Sessie } from '../types';

export const CSV_SCHEIDING = ';';

export const CSV_KOLOMMEN = [
  'nummer',
  'tijdstempel',
  'ms_sinds_start',
  'gebeurtenis',
  'scherm',
  'tegel_id',
  'tegel_label',
  'positie',
  'reactietijd_ms',
  'toelichting',
] as const;

/** Citeer één veld volgens RFC 4180 wanneer dat nodig is. */
export function csvVeld(waarde: unknown): string {
  if (waarde === null || waarde === undefined) return '';
  const tekst = String(waarde);
  if (
    tekst.includes(CSV_SCHEIDING) ||
    tekst.includes('"') ||
    tekst.includes('\n') ||
    tekst.includes('\r')
  ) {
    return `"${tekst.replace(/"/g, '""')}"`;
  }
  return tekst;
}

function regel(velden: unknown[]): string {
  return velden.map(csvVeld).join(CSV_SCHEIDING);
}

/** Zet één gebeurtenis om naar een CSV-regel. */
function gebeurtenisRegel(gebeurtenis: Gebeurtenis): string {
  return regel([
    gebeurtenis.nummer,
    gebeurtenis.tijdstempel,
    gebeurtenis.msSindsStart,
    gebeurtenis.type,
    gebeurtenis.schermId ?? '',
    gebeurtenis.tegelId ?? '',
    gebeurtenis.tegelLabel ?? '',
    gebeurtenis.positie ?? '',
    gebeurtenis.reactietijdMs ?? '',
    gebeurtenis.toelichting ?? '',
  ]);
}

/**
 * Bouw het volledige CSV-bestand voor een sessie. De eerste regels bevatten
 * de sessiegegevens als commentaar-achtige kopregels, daarna volgt de tabel.
 */
export function sessieNaarCsv(sessie: Sessie): string {
  const kop = [
    regel(['sessiecode', sessie.sessiecode]),
    regel(['gestart_op', sessie.gestartOp]),
    regel(['gestopt_op', sessie.gestoptOp ?? '']),
    regel(['bedieningsmodus', sessie.modus]),
    regel(['scantijd_ms', sessie.scanIntervalMs]),
    regel(['observatienotities', sessie.notities]),
    '',
  ];
  const tabel = [
    CSV_KOLOMMEN.join(CSV_SCHEIDING),
    ...sessie.gebeurtenissen.map(gebeurtenisRegel),
  ];
  return [...kop, ...tabel].join('\r\n');
}

/** CSV met BOM, zodat Excel de tekens juist leest. */
export function csvMetBom(csv: string): string {
  return `\uFEFF${csv}`;
}

/** Bestandsnaam met sessiecode en datum. */
export function csvBestandsnaam(sessie: Sessie): string {
  const datum = sessie.gestartOp.slice(0, 19).replace(/[:T]/g, '-');
  return `sessie-${sessie.sessiecode}-${datum}.csv`;
}
