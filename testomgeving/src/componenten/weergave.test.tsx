/**
 * Smoketest voor de weergave: alle schermen moeten zonder fouten te tekenen
 * zijn en de leerlingmodus mag geen beheerknoppen bevatten.
 *
 * Er wordt met `renderToString` gerenderd, zodat er geen browseromgeving en
 * geen extra testbibliotheek nodig is.
 */

import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { Begeleidersmodus } from './Begeleidersmodus';
import { Leerlingmodus } from './Leerlingmodus';
import { Pincode } from './Pincode';
import { App } from '../App';
import { Besturing } from '../modules/Besturing';
import { SessionLogger } from '../modules/SessionLogger';
import { standaardAppData } from '../modules/ContentEditor';
import { maakSamenvatting } from '../modules/SessionLogger';
import type { BesturingStatus } from '../modules/Besturing';
import type { Sessie } from '../types';

function maakStatus(): BesturingStatus {
  const logger = new SessionLogger({ maakSessiecode: () => 'S-TEST' });
  const besturing = new Besturing({
    appData: standaardAppData(),
    logger,
    opStatus: () => undefined,
  });
  besturing.start();
  const status = besturing.status();
  besturing.pauzeer();
  return status;
}

function maakSessie(): Sessie {
  const logger = new SessionLogger({ maakSessiecode: () => 'S-TEST' });
  logger.start(2, 2500);
  logger.legTegelActief({ schermId: 'home', tegelId: 'muziek', tegelLabel: 'Muziek', positie: 1 });
  logger.legSelectie({ schermId: 'home', tegelId: 'muziek', tegelLabel: 'Muziek', positie: 1 });
  logger.stop();
  return logger.huidigeSessie as Sessie;
}

describe('leerlingmodus', () => {
  it('tekent de titel en alle tegels van het beginscherm', () => {
    const appData = standaardAppData();
    const html = renderToString(
      <Leerlingmodus
        status={maakStatus()}
        instellingen={appData.settings}
        opTegelKlik={() => undefined}
        opActieKlik={() => undefined}
        opVerborgenHoek={() => undefined}
      />,
    );
    expect(html).toContain('Wat wil je doen?');
    for (const tegel of appData.screens[0].items) {
      expect(html).toContain(tegel.label);
    }
  });

  it('markeert precies één tegel als actief', () => {
    const appData = standaardAppData();
    const html = renderToString(
      <Leerlingmodus
        status={maakStatus()}
        instellingen={appData.settings}
        opTegelKlik={() => undefined}
        opActieKlik={() => undefined}
        opVerborgenHoek={() => undefined}
      />,
    );
    expect(html.match(/tegel actief/g)).toHaveLength(1);
  });

  it('bevat geen beheerknoppen of externe links', () => {
    const appData = standaardAppData();
    const html = renderToString(
      <Leerlingmodus
        status={maakStatus()}
        instellingen={appData.settings}
        opTegelKlik={() => undefined}
        opActieKlik={() => undefined}
        opVerborgenHoek={() => undefined}
      />,
    );
    // De enige knop in de leerlingmodus is de onzichtbare hoek; die staat
    // buiten de beeldopbouw en is niet met tab te bereiken.
    expect(html.match(/<button/g)).toHaveLength(1);
    expect(html).toContain('class="hoekknop"');
    expect(html).toContain('tabindex="-1"');

    for (const verboden of ['Instellingen', 'Inhoud beheren', 'Exporteren', 'http', '<a ', '<iframe']) {
      expect(html, verboden).not.toContain(verboden);
    }
  });
});

describe('begeleidersmodus', () => {
  it('tekent de instellingen zonder fouten', () => {
    const html = renderToString(
      <Begeleidersmodus
        appData={standaardAppData()}
        huidigeSessie={maakSessie()}
        eerdereSessies={[maakSessie()]}
        sessieActief={false}
        opslagWaarschuwing={null}
        mediaMeldingen={[]}
        opInstellingen={() => undefined}
        opSchermen={() => undefined}
        opVolledigeData={() => undefined}
        opSessieStart={() => undefined}
        opSessieStop={() => undefined}
        opSessieReset={() => undefined}
        opNotities={() => undefined}
        opWisSessies={() => undefined}
        opVolledigScherm={() => undefined}
        opVoorbeeld={() => undefined}
        opSluiten={() => undefined}
      />,
    );
    expect(html).toContain('Begeleidersmodus');
    expect(html).toContain('Scantijd per tegel');
    expect(html).toContain('Invoerblokkade na een keuze');
    expect(html).toContain('Toets vastleggen');
  });
});

describe('overige weergaven', () => {
  it('tekent het pincodevenster', () => {
    const html = renderToString(
      <Pincode verwachtePincode="1234" opGoed={() => undefined} opAfbreken={() => undefined} />,
    );
    expect(html).toContain('Pincode');
  });

  it('tekent het laadscherm van de app', () => {
    const html = renderToString(<App />);
    expect(html).toContain('Bezig met laden');
  });
});

describe('samenvatting', () => {
  it('bevat geen woorden die een conclusie suggereren', () => {
    const tekst = maakSamenvatting(maakSessie()).toLowerCase();
    for (const woord of ['begrijpt', 'kan niet', 'wil ', 'vindt ', 'score', 'niveau', 'goed gedaan']) {
      expect(tekst, woord).not.toContain(woord);
    }
  });
});
