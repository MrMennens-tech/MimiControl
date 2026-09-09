/**
 * Sessieoverzicht: geregistreerde gebeurtenissen, observatienotities, export
 * naar CSV en een korte feitelijke samenvatting.
 *
 * Er staan bewust geen conclusies in over begrip, bedoeling of gevoel; er
 * worden alleen gebeurtenissen en gemeten tijden weergegeven.
 */

import { useMemo, useState } from 'react';
import type { Sessie } from '../types';
import { berekenCijfers, maakCsvBestand, maakSamenvatting } from '../modules/SessionLogger';
import { downloadTekst } from '../modules/bestanden';

interface Props {
  huidigeSessie: Sessie | null;
  eerdereSessies: Sessie[];
  opNotities: (tekst: string) => void;
  opWisSessies: () => void;
}

const GEBEURTENIS_TEKST: Record<string, string> = {
  sessieGestart: 'sessie gestart',
  sessieGestopt: 'sessie gestopt',
  modusGekozen: 'bedieningsmodus gekozen',
  scantijdIngesteld: 'scantijd ingesteld',
  schermGeopend: 'scherm geopend',
  tegelActief: 'tegel actief',
  selectie: 'selectie',
  terug: 'terug',
  terugGenegeerd: 'terug genegeerd',
  scanrondeAfgebroken: 'scanrondes afgelopen zonder keuze',
  invoerGeblokkeerd: 'aanslag genegeerd (invoerblokkade)',
  actieGestart: 'eindactie gestart',
  actieAfgelopen: 'eindactie afgelopen',
  notitie: 'notitie',
};

function tijdKort(tijdstempel: string): string {
  return tijdstempel.slice(11, 23).replace('T', '');
}

export function SessieOverzicht({
  huidigeSessie,
  eerdereSessies,
  opNotities,
  opWisSessies,
}: Props) {
  const [bevestigWissen, zetBevestigWissen] = useState(false);
  const cijfers = useMemo(
    () => (huidigeSessie ? berekenCijfers(huidigeSessie) : null),
    [huidigeSessie],
  );

  const downloadCsv = (sessie: Sessie) => {
    const bestand = maakCsvBestand(sessie);
    downloadTekst(bestand.naam, bestand.inhoud, 'text/csv');
  };

  const downloadSamenvatting = (sessie: Sessie) => {
    downloadTekst(
      `samenvatting-${sessie.sessiecode}.txt`,
      maakSamenvatting(sessie),
      'text/plain',
    );
  };

  return (
    <div>
      <section className="paneel">
        <h2>Huidige sessie</h2>
        {!huidigeSessie ? (
          <p className="hulptekst">
            Er is nog geen sessie gestart. Start een sessie op het tabblad Instellingen.
          </p>
        ) : (
          <>
            <div className="samenvatting-instellingen">
              <div>
                <span>Sessiecode</span>
                {huidigeSessie.sessiecode}
              </div>
              <div>
                <span>Gestart</span>
                {tijdKort(huidigeSessie.gestartOp)}
              </div>
              <div>
                <span>Status</span>
                {huidigeSessie.gestoptOp ? 'gestopt' : 'loopt'}
              </div>
              <div>
                <span>Bedieningsmodus</span>
                {huidigeSessie.modus} toets(en)
              </div>
              <div>
                <span>Scantijd</span>
                {huidigeSessie.scanIntervalMs} ms
              </div>
              <div>
                <span>Gebeurtenissen</span>
                {huidigeSessie.gebeurtenissen.length}
              </div>
            </div>

            {cijfers && (
              <>
                <h3>Cijfers (alleen geteld en gemeten)</h3>
                <div className="samenvatting-instellingen">
                  <div>
                    <span>Selecties</span>
                    {cijfers.aantalSelecties}
                  </div>
                  <div>
                    <span>Tegels actief geworden</span>
                    {cijfers.aantalTegelActief}
                  </div>
                  <div>
                    <span>Keer terug</span>
                    {cijfers.aantalTerug} (genegeerd: {cijfers.aantalTerugGenegeerd})
                  </div>
                  <div>
                    <span>Scanrondes zonder keuze</span>
                    {cijfers.aantalAfgebrokenRondes}
                  </div>
                  <div>
                    <span>Aanslagen genegeerd</span>
                    {cijfers.aantalGeblokkeerdeAanslagen}
                  </div>
                  <div>
                    <span>Tijd focus → selectie (gem.)</span>
                    {cijfers.gemiddeldeReactietijdMs === null
                      ? 'nog niets gemeten'
                      : `${cijfers.gemiddeldeReactietijdMs} ms`}
                  </div>
                </div>
              </>
            )}

            <h3>Observatienotities</h3>
            <div className="veld">
              <label htmlFor="notities">Feitelijke aantekeningen van de begeleider</label>
              <textarea
                id="notities"
                value={huidigeSessie.notities}
                placeholder="Bijvoorbeeld: om 10:14 hoofd naar links gedraaid; scantijd van 2500 naar 3500 ms gezet."
                onChange={(event) => opNotities(event.target.value)}
              />
            </div>

            <div className="knoppenrij">
              <button
                type="button"
                className="knop primair"
                onClick={() => downloadCsv(huidigeSessie)}
              >
                Sessie downloaden als CSV
              </button>
              <button
                type="button"
                className="knop"
                onClick={() => downloadSamenvatting(huidigeSessie)}
              >
                Samenvatting downloaden (tekst)
              </button>
            </div>

            <h3>Gebeurtenissen</h3>
            <div className="tabelomhulsel">
              <table className="tabel">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>tijd</th>
                    <th>ms</th>
                    <th>gebeurtenis</th>
                    <th>scherm</th>
                    <th>tegel</th>
                    <th>pos.</th>
                    <th>reactietijd</th>
                    <th>toelichting</th>
                  </tr>
                </thead>
                <tbody>
                  {[...huidigeSessie.gebeurtenissen]
                    .reverse()
                    .slice(0, 300)
                    .map((gebeurtenis) => (
                      <tr key={gebeurtenis.nummer}>
                        <td>{gebeurtenis.nummer}</td>
                        <td className="eenregel">{tijdKort(gebeurtenis.tijdstempel)}</td>
                        <td>{gebeurtenis.msSindsStart}</td>
                        <td>{GEBEURTENIS_TEKST[gebeurtenis.type] ?? gebeurtenis.type}</td>
                        <td>{gebeurtenis.schermId ?? ''}</td>
                        <td>{gebeurtenis.tegelLabel ?? ''}</td>
                        <td>{gebeurtenis.positie ?? ''}</td>
                        <td>
                          {typeof gebeurtenis.reactietijdMs === 'number'
                            ? `${gebeurtenis.reactietijdMs} ms`
                            : ''}
                        </td>
                        <td>{gebeurtenis.toelichting ?? ''}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
            <p className="hulptekst">
              De nieuwste gebeurtenis staat boven; er worden maximaal 300 regels weergegeven. De
              CSV-export bevat alles.
            </p>
          </>
        )}
      </section>

      <section className="paneel">
        <h2>Eerdere sessies op dit apparaat</h2>
        {eerdereSessies.length === 0 ? (
          <p className="hulptekst">Er zijn nog geen eerdere sessies bewaard.</p>
        ) : (
          <div className="tabelomhulsel">
            <table className="tabel">
              <thead>
                <tr>
                  <th>sessiecode</th>
                  <th>gestart</th>
                  <th>modus</th>
                  <th>scantijd</th>
                  <th>gebeurtenissen</th>
                  <th>export</th>
                </tr>
              </thead>
              <tbody>
                {eerdereSessies.map((sessie) => (
                  <tr key={sessie.sessiecode}>
                    <td>{sessie.sessiecode}</td>
                    <td className="eenregel">{sessie.gestartOp.slice(0, 19).replace('T', ' ')}</td>
                    <td>{sessie.modus}</td>
                    <td>{sessie.scanIntervalMs} ms</td>
                    <td>{sessie.gebeurtenissen.length}</td>
                    <td>
                      <button
                        type="button"
                        className="knop klein"
                        onClick={() => downloadCsv(sessie)}
                      >
                        CSV
                      </button>{' '}
                      <button
                        type="button"
                        className="knop klein"
                        onClick={() => downloadSamenvatting(sessie)}
                      >
                        Tekst
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="knoppenrij">
          {bevestigWissen ? (
            <>
              <button
                type="button"
                className="knop gevaar"
                onClick={() => {
                  opWisSessies();
                  zetBevestigWissen(false);
                }}
              >
                Ja, alle sessiedata wissen
              </button>
              <button type="button" className="knop" onClick={() => zetBevestigWissen(false)}>
                Annuleren
              </button>
            </>
          ) : (
            <button type="button" className="knop gevaar" onClick={() => zetBevestigWissen(true)}>
              Alle sessiedata wissen
            </button>
          )}
        </div>
        <p className="hulptekst">
          Wissen verwijdert alle sessielogboeken van dit apparaat. Instellingen en inhoud blijven
          staan.
        </p>
      </section>
    </div>
  );
}
