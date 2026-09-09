/**
 * Tests voor het sessielogboek, de CSV-export en de feitelijke samenvatting.
 */

import { describe, expect, it } from 'vitest';
import { berekenCijfers, maakCsvBestand, maakSamenvatting, SessionLogger } from './SessionLogger';
import { CSV_KOLOMMEN, CSV_SCHEIDING, csvVeld, sessieNaarCsv } from './csv';
import type { Sessie } from '../types';

function maakLogger() {
  const klok = { waarde: Date.parse('2026-03-04T10:00:00.000Z') };
  const logger = new SessionLogger({
    nu: () => klok.waarde,
    maakSessiecode: () => 'S-TEST1',
  });
  return { logger, klok };
}

function maakVolledigeSessie(): Sessie {
  const { logger, klok } = maakLogger();
  logger.start(2, 2500);
  logger.legTegelActief({ schermId: 'home', tegelId: 'a', tegelLabel: 'Muziek', positie: 1 });
  klok.waarde += 1200;
  logger.legSelectie({ schermId: 'home', tegelId: 'a', tegelLabel: 'Muziek', positie: 1 });
  logger.leg('schermGeopend', { schermId: 'muziek-menu' });
  logger.legTegelActief({ schermId: 'muziek-menu', tegelId: 'r', tegelLabel: 'Rustig', positie: 1 });
  klok.waarde += 800;
  logger.legSelectie({ schermId: 'muziek-menu', tegelId: 'r', tegelLabel: 'Rustig', positie: 1 });
  logger.leg('terugGenegeerd', { schermId: 'home' });
  logger.leg('invoerGeblokkeerd', { schermId: 'home', toelichting: 'select genegeerd' });
  logger.zetNotities('Om 10:00 rustig gestart.');
  klok.waarde += 5000;
  logger.stop();
  return logger.huidigeSessie as Sessie;
}

describe('SessionLogger', () => {
  it('start met een willekeurige sessiecode en zonder naam', () => {
    const { logger } = maakLogger();
    const sessie = logger.start(1, 2500);
    expect(sessie.sessiecode).toBe('S-TEST1');
    expect(Object.keys(sessie)).not.toContain('naam');
  });

  it('legt de modus en de scantijd vast bij de start', () => {
    const { logger } = maakLogger();
    logger.start(3, 4000);
    const typen = logger.huidigeSessie?.gebeurtenissen.map((g) => g.type);
    expect(typen).toEqual(['sessieGestart', 'modusGekozen', 'scantijdIngesteld']);
    expect(logger.huidigeSessie?.gebeurtenissen[2].toelichting).toBe('4000 ms');
  });

  it('meet de tijd tussen het actief worden van een tegel en de selectie', () => {
    const { logger, klok } = maakLogger();
    logger.start(1, 2500);
    logger.legTegelActief({ tegelId: 'a', tegelLabel: 'A', positie: 1 });
    klok.waarde += 1450;
    logger.legSelectie({ tegelId: 'a', tegelLabel: 'A', positie: 1 });
    const selectie = logger.huidigeSessie?.gebeurtenissen.find((g) => g.type === 'selectie');
    expect(selectie?.reactietijdMs).toBe(1450);
  });

  it('nummert gebeurtenissen doorlopend en rekent de tijd vanaf de start', () => {
    const { logger, klok } = maakLogger();
    logger.start(1, 2500);
    klok.waarde += 2000;
    const gebeurtenis = logger.leg('notitie', { toelichting: 'test' });
    expect(gebeurtenis?.nummer).toBe(4);
    expect(gebeurtenis?.msSindsStart).toBe(2000);
  });

  it('legt niets vast zonder actieve sessie', () => {
    const { logger } = maakLogger();
    expect(logger.leg('selectie')).toBeNull();
    expect(logger.isActief).toBe(false);
  });

  it('kan een sessie resetten', () => {
    const { logger } = maakLogger();
    logger.start(1, 2500);
    logger.reset();
    expect(logger.huidigeSessie).toBeNull();
  });
});

describe('cijfers', () => {
  it('telt gebeurtenissen en berekent de reactietijden', () => {
    const cijfers = berekenCijfers(maakVolledigeSessie());
    expect(cijfers.aantalSelecties).toBe(2);
    expect(cijfers.aantalTegelActief).toBe(2);
    expect(cijfers.aantalTerugGenegeerd).toBe(1);
    expect(cijfers.aantalGeblokkeerdeAanslagen).toBe(1);
    expect(cijfers.reactietijdenMs).toEqual([1200, 800]);
    expect(cijfers.gemiddeldeReactietijdMs).toBe(1000);
    expect(cijfers.snelsteReactietijdMs).toBe(800);
    expect(cijfers.langsteReactietijdMs).toBe(1200);
    expect(cijfers.duurMs).toBe(7000);
  });

  it('telt de selecties per tegel', () => {
    const cijfers = berekenCijfers(maakVolledigeSessie());
    expect(cijfers.perTegel).toEqual([
      { label: 'Muziek', aantal: 1 },
      { label: 'Rustig', aantal: 1 },
    ]);
  });
});

describe('samenvatting', () => {
  it('bevat de feitelijke cijfers en de notities', () => {
    const tekst = maakSamenvatting(maakVolledigeSessie());
    expect(tekst).toContain('Sessiecode: S-TEST1');
    expect(tekst).toContain('Aantal selecties: 2');
    expect(tekst).toContain('Om 10:00 rustig gestart.');
  });

  it('vermeldt expliciet dat er geen conclusies in staan', () => {
    const tekst = maakSamenvatting(maakVolledigeSessie());
    expect(tekst).toContain('geen conclusies');
  });
});

describe('CSV-export', () => {
  it('begint met de sessiegegevens en daarna de kolomkoppen', () => {
    const csv = sessieNaarCsv(maakVolledigeSessie());
    const regels = csv.split('\r\n');
    expect(regels[0]).toBe(`sessiecode${CSV_SCHEIDING}S-TEST1`);
    expect(regels).toContain(CSV_KOLOMMEN.join(CSV_SCHEIDING));
  });

  it('bevat een regel per gebeurtenis', () => {
    const sessie = maakVolledigeSessie();
    const csv = sessieNaarCsv(sessie);
    const kopIndex = csv.split('\r\n').indexOf(CSV_KOLOMMEN.join(CSV_SCHEIDING));
    const dataregels = csv.split('\r\n').slice(kopIndex + 1);
    expect(dataregels).toHaveLength(sessie.gebeurtenissen.length);
  });

  it('zet de reactietijd in de juiste kolom', () => {
    const csv = sessieNaarCsv(maakVolledigeSessie());
    const selectieregel = csv
      .split('\r\n')
      .find((regel) => regel.includes('selectie') && regel.includes('Muziek'));
    expect(selectieregel?.split(CSV_SCHEIDING)[8]).toBe('1200');
  });

  it('citeert velden met een scheidingsteken, aanhalingsteken of regeleinde', () => {
    expect(csvVeld('gewoon')).toBe('gewoon');
    expect(csvVeld('met;punt')).toBe('"met;punt"');
    expect(csvVeld('met "quote"')).toBe('"met ""quote"""');
    expect(csvVeld('regel\nnieuw')).toBe('"regel\nnieuw"');
    expect(csvVeld(undefined)).toBe('');
  });

  it('levert een bestandsnaam met sessiecode en een BOM voor Excel', () => {
    const bestand = maakCsvBestand(maakVolledigeSessie());
    expect(bestand.naam).toBe('sessie-S-TEST1-2026-03-04-10-00-00.csv');
    expect(bestand.inhoud.startsWith('\uFEFF')).toBe(true);
  });
});
