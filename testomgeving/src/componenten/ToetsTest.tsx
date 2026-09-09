/**
 * Ingebouwde toetstestpagina.
 *
 * Hier ziet de begeleider precies wat het mimiekhulpmiddel verstuurt:
 * per gebeurtenis `type`, `key`, `code`, `keyCode` en `isTrusted`, plus een
 * teller per toets. Is `code` leeg, dan wordt dat duidelijk gemarkeerd: dat
 * wijst op een hulpmiddel dat toetsen zonder hardware-scancode verstuurt.
 *
 * De tijd tussen keydown en keyup wordt gemeten, zodat de ingestelde
 * toetsduur van MimiControl (standaard 100 ms) te controleren is.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { InputManager, type RuweToetsInfo } from '../modules/InputManager';
import { omschrijfBinding } from '../modules/toetsnamen';
import { bindingUitEvent } from '../modules/toetsnamen';
import type { Instellingen } from '../types';

const MAX_REGELS = 120;

interface Props {
  instellingen: Instellingen;
}

interface Regel extends RuweToetsInfo {
  nummer: number;
}

export function ToetsTest({ instellingen }: Props) {
  const [regels, zetRegels] = useState<Regel[]>([]);
  const teller = useRef(0);

  useEffect(() => {
    // Eigen invoerbeheer in meetmodus: er worden geen acties uitgevoerd,
    // alleen gemeten. Standaardacties van de browser worden wel onderdrukt.
    const manager = new InputManager({
      opRuwEvent: (info) => {
        teller.current += 1;
        const regel: Regel = { ...info, nummer: teller.current };
        zetRegels((oud) => [regel, ...oud].slice(0, MAX_REGELS));
      },
    });
    manager.zetAlleenMeten(true);
    manager.start(window);
    return () => manager.stop();
  }, []);

  const cijfers = useMemo(() => {
    const perToets = new Map<string, { aantal: number; code: string; key: string; keyCode: number }>();
    let zonderCode = 0;
    let nietVertrouwd = 0;
    const duren: number[] = [];

    for (const regel of regels) {
      if (regel.type !== 'keydown') {
        if (typeof regel.toetsduurMs === 'number') duren.push(regel.toetsduurMs);
        continue;
      }
      const sleutel = `${regel.code}|${regel.key}|${regel.keyCode}`;
      const bestaand = perToets.get(sleutel);
      if (bestaand) bestaand.aantal += 1;
      else
        perToets.set(sleutel, {
          aantal: 1,
          code: regel.code,
          key: regel.key,
          keyCode: regel.keyCode,
        });
      if (regel.codeOntbreekt) zonderCode += 1;
      if (!regel.isTrusted) nietVertrouwd += 1;
    }

    const gemiddeldeDuur = duren.length
      ? Math.round(duren.reduce((a, b) => a + b, 0) / duren.length)
      : null;

    return {
      perToets: [...perToets.values()].sort((a, b) => b.aantal - a.aantal),
      zonderCode,
      nietVertrouwd,
      gemiddeldeDuur,
      kortsteDuur: duren.length ? Math.min(...duren) : null,
      langsteDuur: duren.length ? Math.max(...duren) : null,
      aantalDuren: duren.length,
    };
  }, [regels]);

  const toonKey = (key: string) => (key === ' ' ? '␣ (spatie)' : key || '(leeg)');

  return (
    <div>
      <section className="paneel">
        <h2>Toetstest</h2>
        <p>
          Laat het mimiekhulpmiddel een toets versturen. Elke gebeurtenis komt hieronder te staan.
          Klik eerst één keer in dit venster, zodat de toetsaanslagen hier aankomen.
        </p>

        <div className="samenvatting-instellingen">
          <div>
            <span>Ingestelde toets volgende</span>
            {omschrijfBinding(instellingen.keys.next)}
          </div>
          <div>
            <span>Ingestelde toets selecteren</span>
            {omschrijfBinding(instellingen.keys.select)}
          </div>
          <div>
            <span>Ingestelde toets terug</span>
            {omschrijfBinding(instellingen.keys.back)}
          </div>
        </div>

        {cijfers.zonderCode > 0 && (
          <div className="melding fout">
            <strong>Let op: {cijfers.zonderCode} aanslag(en) zonder scancode.</strong> Het veld{' '}
            <code>code</code> is leeg. Dat wijst op een hulpmiddel dat toetsen verstuurt zonder
            hardware-scancode. MimiControl Studio doet dat wél goed (SendInput met scancode). Deze
            app herkent de toets alsnog via <code>key</code> en <code>keyCode</code>, maar andere
            programma&apos;s kunnen hierdoor niet reageren.
          </div>
        )}

        {cijfers.nietVertrouwd > 0 && (
          <div className="melding waarschuwing">
            {cijfers.nietVertrouwd} aanslag(en) hadden <code>isTrusted = false</code>. Die komen niet
            van het besturingssysteem maar uit een script in de browser.
          </div>
        )}

        <h3>Gemeten toetsduur (keydown → keyup)</h3>
        {cijfers.aantalDuren === 0 ? (
          <p className="hulptekst">Nog geen volledige aanslag gemeten.</p>
        ) : (
          <div className="samenvatting-instellingen">
            <div>
              <span>Gemiddeld</span>
              {cijfers.gemiddeldeDuur} ms
            </div>
            <div>
              <span>Kortst</span>
              {cijfers.kortsteDuur} ms
            </div>
            <div>
              <span>Langst</span>
              {cijfers.langsteDuur} ms
            </div>
            <div>
              <span>Aantal metingen</span>
              {cijfers.aantalDuren}
            </div>
          </div>
        )}
        <p className="hulptekst">
          MimiControl Studio houdt de toets standaard 100 ms ingedrukt. Wijkt de meting hier sterk
          af, dan staat de toetsduur in MimiControl anders ingesteld.
        </p>
      </section>

      <section className="paneel">
        <h2>Teller per toets</h2>
        {cijfers.perToets.length === 0 ? (
          <p className="hulptekst">Nog geen toetsaanslagen ontvangen.</p>
        ) : (
          <div className="tabelomhulsel">
            <table className="tabel">
              <thead>
                <tr>
                  <th>Aantal</th>
                  <th>Herkend als</th>
                  <th>code</th>
                  <th>key</th>
                  <th>keyCode</th>
                </tr>
              </thead>
              <tbody>
                {cijfers.perToets.map((rij) => (
                  <tr key={`${rij.code}|${rij.key}|${rij.keyCode}`}>
                    <td>
                      <strong>{rij.aantal}</strong>
                    </td>
                    <td>{bindingUitEvent(rij).naam}</td>
                    <td className="eenregel">
                      {rij.code || <span className="merk fout">leeg</span>}
                    </td>
                    <td className="eenregel">{toonKey(rij.key)}</td>
                    <td className="eenregel">{rij.keyCode || '0'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="paneel">
        <h2>Alle gebeurtenissen</h2>
        <p>De nieuwste staat boven. Er worden maximaal {MAX_REGELS} regels bewaard.</p>
        <div className="knoppenrij">
          <button
            type="button"
            className="knop"
            onClick={() => {
              zetRegels([]);
              teller.current = 0;
            }}
          >
            Lijst wissen
          </button>
        </div>
        <div className="tabelomhulsel" style={{ marginTop: 14 }}>
          <table className="tabel">
            <thead>
              <tr>
                <th>#</th>
                <th>type</th>
                <th>code</th>
                <th>key</th>
                <th>keyCode</th>
                <th>isTrusted</th>
                <th>herhaling</th>
                <th>duur</th>
              </tr>
            </thead>
            <tbody>
              {regels.map((regel) => (
                <tr key={`${regel.nummer}-${regel.type}`}>
                  <td>{regel.nummer}</td>
                  <td>{regel.type}</td>
                  <td className="eenregel">
                    {regel.code || <span className="merk fout">leeg</span>}
                  </td>
                  <td className="eenregel">{toonKey(regel.key)}</td>
                  <td className="eenregel">{regel.keyCode || '0'}</td>
                  <td>
                    <span className={`merk ${regel.isTrusted ? 'goed' : 'let-op'}`}>
                      {regel.isTrusted ? 'true' : 'false'}
                    </span>
                  </td>
                  <td>{regel.repeat ? 'ja' : 'nee'}</td>
                  <td>{typeof regel.toetsduurMs === 'number' ? `${regel.toetsduurMs} ms` : ''}</td>
                </tr>
              ))}
              {regels.length === 0 && (
                <tr>
                  <td colSpan={8}>Nog geen gebeurtenissen.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
