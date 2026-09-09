/**
 * Informatietabblad: hoe de omgeving werkt, wat er wel en niet geregistreerd
 * wordt, en welke afspraken over privacy gelden.
 */

import type { AppData } from '../types';
import { isGeheugenopslag } from '../modules/opslag';

interface Props {
  appData: AppData;
}

export function Informatie({ appData }: Props) {
  const aantalTegels = appData.screens.reduce((som, scherm) => som + scherm.items.length, 0);

  return (
    <div>
      <section className="paneel">
        <h2>Waar is deze omgeving voor?</h2>
        <p>
          Deze omgeving is bedoeld om te observeren hoe iemand met één, twee of drie toetsen een
          computer bedient. Het is geen toets en geen meetinstrument voor kunnen of begrijpen.
        </p>
        <ul className="lijst-net">
          <li>Wat gebeurt er als een keuze gemaakt wordt?</li>
          <li>Wordt de bewegende markering gevolgd?</li>
          <li>Lukt het om te wachten tot de gewenste tegel actief is?</li>
          <li>Wordt er een volgende keuze gemaakt en een eerdere keuze herstelt?</li>
          <li>Welke scantijd is comfortabel en hoe betrouwbaar is iedere mimiek?</li>
        </ul>
        <p className="hulptekst">
          De app registreert alleen feitelijke gebeurtenissen met een tijdstempel. Er worden nooit
          conclusies getrokken over cognitie, emotie of intentie.
        </p>
      </section>

      <section className="paneel">
        <h2>Privacy</h2>
        <ul className="lijst-net">
          <li>Geen server, geen account, geen inlog.</li>
          <li>Geen trackers, geen statistiek naar buiten, geen reclame.</li>
          <li>Geen cameratoegang en geen microfoontoegang.</li>
          <li>Geen naam van de leerling: elke sessie krijgt een willekeurige code.</li>
          <li>Alles staat lokaal op dit apparaat en is met één knop te wissen.</li>
          <li>Externe links worden geblokkeerd; de app kan niet per ongeluk verlaten worden.</li>
        </ul>
        {isGeheugenopslag() && (
          <div className="melding waarschuwing">
            De lokale database is niet beschikbaar (bijvoorbeeld in een privévenster). De app werkt
            wel, maar instellingen en sessies worden niet bewaard.
          </div>
        )}
      </section>

      <section className="paneel">
        <h2>Bediening op een rij</h2>
        <div className="tabelomhulsel">
          <table className="tabel">
            <thead>
              <tr>
                <th>modus</th>
                <th>toets 1</th>
                <th>toets 2</th>
                <th>toets 3</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>1 toets</td>
                <td>—</td>
                <td>selecteren (de markering loopt automatisch)</td>
                <td>—</td>
              </tr>
              <tr>
                <td>2 toetsen</td>
                <td>volgende tegel</td>
                <td>selecteren</td>
                <td>—</td>
              </tr>
              <tr>
                <td>3 toetsen</td>
                <td>volgende tegel</td>
                <td>selecteren</td>
                <td>één scherm terug</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="hulptekst">
          Tijdens een eindactie stopt elke functietoets de actie. Op het beginscherm doet de
          terugtoets niets.
        </p>
      </section>

      <section className="paneel">
        <h2>Deze inhoud</h2>
        <div className="samenvatting-instellingen">
          <div>
            <span>Versie gegevensmodel</span>
            {appData.appVersion}
          </div>
          <div>
            <span>Aantal schermen</span>
            {appData.screens.length}
          </div>
          <div>
            <span>Aantal tegels</span>
            {aantalTegels}
          </div>
          <div>
            <span>Beginscherm</span>
            {appData.screens[0]?.title ?? '—'}
          </div>
        </div>
        <p className="hulptekst">
          Er wordt geen auteursrechtelijk beeld of geluid meegeleverd. Tegels gebruiken een emoji
          als beeld; eigen foto&apos;s en opnames kunnen per tegel toegevoegd worden.
        </p>
      </section>
    </div>
  );
}
