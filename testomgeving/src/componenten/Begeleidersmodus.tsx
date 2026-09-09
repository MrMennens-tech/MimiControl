/**
 * Begeleidersmodus met tabbladen: instellingen, inhoud, toetstest, sessie en
 * informatie. Deze modus is alleen bereikbaar via de pincode of de verborgen
 * toetscombinatie en is nooit zichtbaar in de leerlingmodus.
 */

import { useState } from 'react';
import type { AppData, Instellingen, Scherm, Sessie } from '../types';
import { InhoudEditor } from './InhoudEditor';
import { InstellingenPaneel } from './InstellingenPaneel';
import { SessieOverzicht } from './SessieOverzicht';
import { ToetsTest } from './ToetsTest';
import { Informatie } from './Informatie';

type Tab = 'instellingen' | 'inhoud' | 'toetstest' | 'sessie' | 'over';

const TABBLADEN: { id: Tab; naam: string }[] = [
  { id: 'instellingen', naam: 'Instellingen' },
  { id: 'inhoud', naam: 'Inhoud' },
  { id: 'toetstest', naam: 'Toetstest' },
  { id: 'sessie', naam: 'Sessie' },
  { id: 'over', naam: 'Informatie' },
];

interface Props {
  appData: AppData;
  huidigeSessie: Sessie | null;
  eerdereSessies: Sessie[];
  sessieActief: boolean;
  opslagWaarschuwing: string | null;
  mediaMeldingen: string[];
  opInstellingen: (instellingen: Instellingen) => void;
  opSchermen: (schermen: Scherm[]) => void;
  opVolledigeData: (data: AppData) => void;
  opSessieStart: () => void;
  opSessieStop: () => void;
  opSessieReset: () => void;
  opNotities: (tekst: string) => void;
  opWisSessies: () => void;
  opVolledigScherm: () => void;
  opVoorbeeld: (schermId: string) => void;
  opSluiten: () => void;
}

export function Begeleidersmodus(props: Props) {
  const [tab, zetTab] = useState<Tab>('instellingen');
  const { appData } = props;

  return (
    <div className="begeleider">
      <header className="begeleider-kop">
        <h1>Begeleidersmodus</h1>
        <span className="merk">
          modus {appData.settings.controlMode} · scantijd {appData.settings.scanIntervalMs} ms
        </span>
        <button type="button" className="knop primair" onClick={props.opSessieStart}>
          Leerlingmodus openen
        </button>
        <button type="button" className="knop" onClick={props.opSluiten}>
          Naar het startscherm
        </button>
      </header>

      <div className="tabbladen" role="tablist">
        {TABBLADEN.map((blad) => (
          <button
            key={blad.id}
            type="button"
            role="tab"
            className="tabblad"
            aria-selected={tab === blad.id}
            onClick={() => zetTab(blad.id)}
          >
            {blad.naam}
          </button>
        ))}
      </div>

      <div className="tabinhoud" role="tabpanel">
        {props.opslagWaarschuwing && (
          <div className="melding waarschuwing">{props.opslagWaarschuwing}</div>
        )}
        {props.mediaMeldingen.length > 0 && (
          <div className="melding waarschuwing">
            <strong>Meldingen over media in de laatste sessie:</strong>
            <ul>
              {props.mediaMeldingen.map((melding, i) => (
                <li key={i}>{melding}</li>
              ))}
            </ul>
          </div>
        )}

        {tab === 'instellingen' && (
          <InstellingenPaneel
            instellingen={appData.settings}
            schermen={appData.screens}
            startSchermId={appData.screens[0]?.id ?? ''}
            opInstellingen={props.opInstellingen}
            opSchermen={props.opSchermen}
            sessieActief={props.sessieActief}
            opSessieStart={props.opSessieStart}
            opSessieStop={props.opSessieStop}
            opSessieReset={props.opSessieReset}
            opVolledigScherm={props.opVolledigScherm}
          />
        )}
        {tab === 'inhoud' && (
          <InhoudEditor
            appData={appData}
            opSchermen={props.opSchermen}
            opVolledigeData={props.opVolledigeData}
            opVoorbeeld={props.opVoorbeeld}
          />
        )}
        {tab === 'toetstest' && <ToetsTest instellingen={appData.settings} />}
        {tab === 'sessie' && (
          <SessieOverzicht
            huidigeSessie={props.huidigeSessie}
            eerdereSessies={props.eerdereSessies}
            opNotities={props.opNotities}
            opWisSessies={props.opWisSessies}
          />
        )}
        {tab === 'over' && <Informatie appData={appData} />}
      </div>
    </div>
  );
}
