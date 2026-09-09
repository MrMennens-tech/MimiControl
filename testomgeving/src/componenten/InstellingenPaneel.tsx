/**
 * Instellingen in de begeleidersmodus.
 *
 * Alles is zonder programmeerkennis in te stellen: bedieningsmodus, toetsen,
 * scantijd, invoerblokkade, spraak, geluid, starttegel en welke thema's de
 * leerling ziet.
 */

import type { Bedieningsmodus, Instellingen, Scherm, Starttegel, TerugNaActie } from '../types';
import {
  BLOKKADE_MAX_MS,
  BLOKKADE_MIN_MS,
  SCANTIJD_MAX_MS,
  SCANTIJD_MIN_MS,
} from '../inhoud/standaardInstellingen';
import { ToetsVastleggen } from './ToetsVastleggen';

interface Props {
  instellingen: Instellingen;
  schermen: Scherm[];
  startSchermId: string;
  opInstellingen: (nieuw: Instellingen) => void;
  opSchermen: (nieuw: Scherm[]) => void;
  sessieActief: boolean;
  opSessieStart: () => void;
  opSessieStop: () => void;
  opSessieReset: () => void;
  opVolledigScherm: () => void;
}

const MODUS_UITLEG: Record<Bedieningsmodus, string> = {
  1: 'Eén toets: de markering loopt automatisch langs de tegels, de toets selecteert.',
  2: 'Twee toetsen: toets 1 zet de markering een tegel verder, toets 2 selecteert.',
  3: 'Drie toetsen: toets 1 volgende, toets 2 selecteren, toets 3 één scherm terug.',
};

export function InstellingenPaneel({
  instellingen,
  schermen,
  startSchermId,
  opInstellingen,
  opSchermen,
  sessieActief,
  opSessieStart,
  opSessieStop,
  opSessieReset,
  opVolledigScherm,
}: Props) {
  const wijzig = <K extends keyof Instellingen>(veld: K, waarde: Instellingen[K]) => {
    opInstellingen({ ...instellingen, [veld]: waarde });
  };

  const startScherm = schermen.find((scherm) => scherm.id === startSchermId);

  const wijzigThemaZichtbaar = (tegelId: string, zichtbaar: boolean) => {
    opSchermen(
      schermen.map((scherm) =>
        scherm.id !== startSchermId
          ? scherm
          : {
              ...scherm,
              items: scherm.items.map((item) =>
                item.id === tegelId ? { ...item, zichtbaar } : item,
              ),
            },
      ),
    );
  };

  return (
    <div>
      <section className="paneel">
        <h2>Sessie</h2>
        <p>
          Een sessie legt vast wat er gebeurt. De sessie krijgt een willekeurige code; er wordt geen
          naam van de leerling gevraagd of opgeslagen.
        </p>
        <div className="knoppenrij" style={{ marginTop: 0 }}>
          <button type="button" className="knop primair" onClick={opSessieStart}>
            {sessieActief ? 'Leerlingmodus openen' : 'Sessie starten en leerlingmodus openen'}
          </button>
          <button type="button" className="knop" onClick={opSessieStop} disabled={!sessieActief}>
            Sessie stoppen
          </button>
          <button type="button" className="knop gevaar" onClick={opSessieReset}>
            Sessie resetten
          </button>
          <button type="button" className="knop" onClick={opVolledigScherm}>
            Volledig scherm aan/uit
          </button>
        </div>
      </section>

      <section className="paneel">
        <h2>Bedieningsmodus</h2>
        <p>{MODUS_UITLEG[instellingen.controlMode]}</p>
        <div className="veldenrij">
          <div className="veld">
            <label htmlFor="modus">Aantal toetsen</label>
            <select
              id="modus"
              value={instellingen.controlMode}
              onChange={(event) =>
                wijzig('controlMode', Number(event.target.value) as Bedieningsmodus)
              }
            >
              <option value={1}>1 - automatisch scannen en selecteren</option>
              <option value={2}>2 - volgende en selecteren</option>
              <option value={3}>3 - volgende, selecteren en terug</option>
            </select>
          </div>
        </div>

        <h3>Toetsen</h3>
        <div className="veldenrij">
          <ToetsVastleggen
            naam="Volgende tegel"
            uitleg={
              instellingen.controlMode === 1
                ? 'Niet in gebruik in de modus met één toets.'
                : 'Zet de markering één tegel verder.'
            }
            binding={instellingen.keys.next}
            opNieuweBinding={(binding) => wijzig('keys', { ...instellingen.keys, next: binding })}
          />
          <ToetsVastleggen
            naam="Selecteren"
            uitleg="Kiest de tegel die op dat moment gemarkeerd is."
            binding={instellingen.keys.select}
            opNieuweBinding={(binding) => wijzig('keys', { ...instellingen.keys, select: binding })}
          />
          <ToetsVastleggen
            naam="Eén scherm terug"
            uitleg={
              instellingen.controlMode === 3
                ? 'Gaat één scherm terug en markeert de eerder gekozen tegel opnieuw.'
                : 'Alleen in gebruik in de modus met drie toetsen.'
            }
            binding={instellingen.keys.back}
            opNieuweBinding={(binding) => wijzig('keys', { ...instellingen.keys, back: binding })}
          />
        </div>
        <p className="hulptekst">
          Van elke toets worden <code>code</code>, <code>key</code> en <code>keyCode</code> bewaard.
          Verstuurt een hulpmiddel de toets zonder scancode (leeg <code>code</code>), dan wordt de
          toets alsnog herkend. Controleer dit op het tabblad Toetstest.
        </p>
      </section>

      <section className="paneel">
        <h2>Scannen en timing</h2>
        <div className="veldenrij">
          <div className="veld">
            <label htmlFor="scantijd">
              Scantijd per tegel: {instellingen.scanIntervalMs} ms
            </label>
            <input
              id="scantijd"
              type="range"
              min={SCANTIJD_MIN_MS}
              max={SCANTIJD_MAX_MS}
              step={100}
              value={instellingen.scanIntervalMs}
              onChange={(event) => wijzig('scanIntervalMs', Number(event.target.value))}
            />
            <small>
              Hoe lang een tegel gemarkeerd blijft in de modus met één toets ({SCANTIJD_MIN_MS} -{' '}
              {SCANTIJD_MAX_MS} ms).
            </small>
          </div>

          <div className="veld">
            <label htmlFor="blokkade">
              Invoerblokkade na een keuze: {instellingen.selectionCooldownMs} ms
            </label>
            <input
              id="blokkade"
              type="range"
              min={BLOKKADE_MIN_MS}
              max={BLOKKADE_MAX_MS}
              step={50}
              value={instellingen.selectionCooldownMs}
              onChange={(event) => wijzig('selectionCooldownMs', Number(event.target.value))}
            />
            <small>
              Zolang deze tijd loopt worden toetsaanslagen genegeerd. Dit voorkomt dat een spasme
              meteen een tweede keuze maakt.
            </small>
          </div>

          <div className="veld">
            <label htmlFor="rondes">Aantal scanrondes voordat de scanner stopt</label>
            <input
              id="rondes"
              type="number"
              min={0}
              max={99}
              value={instellingen.scanRondes}
              onChange={(event) => wijzig('scanRondes', Math.max(0, Number(event.target.value)))}
            />
            <small>0 betekent: blijf doorscannen. Stopt de scanner, dan zet de selectietoets hem weer aan.</small>
          </div>

          <div className="veld">
            <label htmlFor="starttegel">Beginnen bij</label>
            <select
              id="starttegel"
              value={instellingen.startTegel}
              onChange={(event) => wijzig('startTegel', event.target.value as Starttegel)}
            >
              <option value="eerste">de eerste tegel</option>
              <option value="willekeurig">een willekeurige tegel</option>
            </select>
            <small>Bepaalt waar de markering op een nieuw scherm begint.</small>
          </div>

          <div className="veld">
            <label htmlFor="terugnaactie">Na een eindactie</label>
            <select
              id="terugnaactie"
              value={instellingen.terugNaActie}
              onChange={(event) => wijzig('terugNaActie', event.target.value as TerugNaActie)}
            >
              <option value="beginscherm">terug naar het beginscherm</option>
              <option value="vorigeScherm">terug naar het vorige scherm</option>
              <option value="blijven">op hetzelfde scherm blijven</option>
            </select>
            <small>
              In de modus met één of twee toetsen is er geen terugtoets; de app keert daarom zelf
              terug.
            </small>
          </div>
        </div>
      </section>

      <section className="paneel">
        <h2>Geluid en spraak</h2>
        <div className="aanvinken">
          <input
            id="spreeklabels"
            type="checkbox"
            checked={instellingen.speakLabels}
            onChange={(event) => wijzig('speakLabels', event.target.checked)}
          />
          <label htmlFor="spreeklabels">
            Tegel benoemen zodra hij actief wordt (spraakmodule van het systeem)
          </label>
        </div>
        <div className="aanvinken">
          <input
            id="selectiegeluid"
            type="checkbox"
            checked={instellingen.selectionSound}
            onChange={(event) => wijzig('selectionSound', event.target.checked)}
          />
          <label htmlFor="selectiegeluid">Kort geluid bij een selectie</label>
        </div>
        <div className="veldenrij">
          <div className="veld">
            <label htmlFor="spraaksnelheid">
              Spreeksnelheid: {instellingen.spraakSnelheid.toFixed(2).replace('.', ',')}
            </label>
            <input
              id="spraaksnelheid"
              type="range"
              min={0.5}
              max={1.5}
              step={0.05}
              value={instellingen.spraakSnelheid}
              onChange={(event) => wijzig('spraakSnelheid', Number(event.target.value))}
            />
          </div>
        </div>
      </section>

      <section className="paneel">
        <h2>Leerlingmodus</h2>
        <div className="aanvinken">
          <input
            id="volledigscherm"
            type="checkbox"
            checked={instellingen.volledigSchermStarten}
            onChange={(event) => wijzig('volledigSchermStarten', event.target.checked)}
          />
          <label htmlFor="volledigscherm">Leerlingmodus in volledig scherm starten</label>
        </div>
        <div className="aanvinken">
          <input
            id="muisbediening"
            type="checkbox"
            checked={instellingen.muisBediening}
            onChange={(event) => wijzig('muisBediening', event.target.checked)}
          />
          <label htmlFor="muisbediening">
            Muis en aanraking laten werken (voor tests door de begeleider)
          </label>
        </div>

        <h3>Welke thema&apos;s ziet de leerling?</h3>
        {startScherm ? (
          startScherm.items.map((item) => (
            <div className="aanvinken" key={item.id}>
              <input
                id={`thema-${item.id}`}
                type="checkbox"
                checked={item.zichtbaar !== false}
                onChange={(event) => wijzigThemaZichtbaar(item.id, event.target.checked)}
              />
              <label htmlFor={`thema-${item.id}`}>
                {item.emoji} {item.label}
              </label>
            </div>
          ))
        ) : (
          <p className="hulptekst">Er is nog geen beginscherm ingericht.</p>
        )}
        <p className="hulptekst">
          Verberg thema&apos;s om het aantal keuzes klein te houden. Op het beginscherm blijven
          maximaal vier tegels staan.
        </p>
      </section>

      <section className="paneel">
        <h2>Pincode</h2>
        <div className="veldenrij">
          <div className="veld">
            <label htmlFor="pincode">Pincode voor de begeleidersmodus</label>
            <input
              id="pincode"
              type="text"
              inputMode="numeric"
              value={instellingen.pincode}
              onChange={(event) =>
                wijzig('pincode', event.target.value.replace(/\D/g, '').slice(0, 8))
              }
            />
            <small>
              Minstens drie cijfers. Dit is een drempel tegen onbedoeld openen, geen zware
              beveiliging.
            </small>
          </div>
        </div>
        <p className="hulptekst">
          In de leerlingmodus opent de begeleidersmodus met <strong>Ctrl + Shift + B</strong> of met
          drie klikken in de linkerbovenhoek van het scherm.
        </p>
      </section>
    </div>
  );
}
