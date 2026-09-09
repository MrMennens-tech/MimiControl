/**
 * Leerlingmodus - volledig scherm, rustige achtergrond, maximaal vier zeer
 * grote tegels. Geen beheerknoppen, geen externe links, geen reclame.
 *
 * De begeleidersmodus is alleen te openen met de verborgen toetscombinatie
 * (Ctrl + Shift + B) of door drie keer in de linkerbovenhoek te klikken; die
 * hoek is onzichtbaar en levert geen zichtbare knop op.
 */

import { useRef } from 'react';
import type { BesturingStatus } from '../modules/Besturing';
import type { Instellingen } from '../types';
import { ActieWeergave } from './ActieWeergave';
import { TegelWeergave } from './TegelWeergave';

interface Props {
  status: BesturingStatus;
  instellingen: Instellingen;
  opTegelKlik: (index: number) => void;
  opActieKlik: () => void;
  /** Wordt aangeroepen na drie klikken in de verborgen hoek. */
  opVerborgenHoek: () => void;
}

/** Klasse voor het rooster; vier tegels worden 2 x 2. */
function roosterKlasse(aantal: number): string {
  if (aantal <= 0) return 'tegelrooster aantal-1';
  if (aantal > 4) return 'tegelrooster aantal-veel';
  return `tegelrooster aantal-${aantal}`;
}

export function Leerlingmodus({
  status,
  instellingen,
  opTegelKlik,
  opActieKlik,
  opVerborgenHoek,
}: Props) {
  const hoekKlikken = useRef<number[]>([]);

  const verborgenHoek = () => {
    const nu = Date.now();
    hoekKlikken.current = [...hoekKlikken.current, nu].filter((tijd) => nu - tijd < 2500);
    if (hoekKlikken.current.length >= 3) {
      hoekKlikken.current = [];
      opVerborgenHoek();
    }
  };

  const bedienbaar = instellingen.muisBediening && status.fase === 'kiezen';

  return (
    <div className="leerling">
      {/* Onzichtbare hoek: geen knop in beeld, alleen voor de begeleider. */}
      <button
        type="button"
        className="hoekknop"
        onClick={verborgenHoek}
        aria-label="Begeleidersmodus openen"
        tabIndex={-1}
      />

      <h1 className="leerling-titel">{status.schermTitel}</h1>

      <div className={roosterKlasse(status.tegels.length)}>
        {status.tegels.map((tegel, index) => (
          <TegelWeergave
            key={tegel.id}
            tegel={tegel}
            actief={status.fase === 'kiezen' && index === status.focusIndex}
            gekozen={status.fase === 'overgang' && index === status.focusIndex}
            bedienbaar={bedienbaar}
            opKlik={() => opTegelKlik(index)}
          />
        ))}
        {status.tegels.length === 0 && (
          <div className="tegel">
            <div className="tegel-label">Er staan nog geen tegels op dit scherm.</div>
          </div>
        )}
      </div>

      <div className="leerling-voet">
        {status.scanGestopt && instellingen.controlMode === 1
          ? 'Druk op de toets om verder te gaan.'
          : ''}
      </div>

      {status.lopendeActie && (
        <ActieWeergave
          lopend={status.lopendeActie}
          opKlik={instellingen.muisBediening ? opActieKlik : undefined}
        />
      )}
    </div>
  );
}
