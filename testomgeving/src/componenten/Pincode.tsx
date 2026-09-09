/**
 * Pincodevenster voor de begeleidersmodus.
 *
 * Dit is geen beveiliging tegen kwaadwillenden, maar een drempel tegen
 * onbedoeld openen tijdens het werken met de leerling.
 */

import { useEffect, useRef, useState } from 'react';

interface Props {
  verwachtePincode: string;
  opGoed: () => void;
  opAfbreken: () => void;
}

export function Pincode({ verwachtePincode, opGoed, opAfbreken }: Props) {
  const [waarde, zetWaarde] = useState('');
  const [fout, zetFout] = useState(false);
  const veld = useRef<HTMLInputElement>(null);

  useEffect(() => {
    veld.current?.focus();
  }, []);

  const controleer = (event: React.FormEvent) => {
    event.preventDefault();
    if (waarde === verwachtePincode) {
      opGoed();
      return;
    }
    zetFout(true);
    zetWaarde('');
  };

  return (
    <div className="pin-overlay" role="dialog" aria-modal="true" aria-label="Pincode invoeren">
      <form className="pin-kaart" onSubmit={controleer}>
        <h2>Begeleidersmodus</h2>
        <p>Voer de pincode in om de instellingen te openen.</p>
        <div className="veld">
          <label htmlFor="pincodeveld">Pincode</label>
          <input
            id="pincodeveld"
            ref={veld}
            type="password"
            inputMode="numeric"
            autoComplete="off"
            value={waarde}
            onChange={(event) => {
              zetWaarde(event.target.value.replace(/\D/g, '').slice(0, 8));
              zetFout(false);
            }}
          />
        </div>
        {fout && <div className="melding fout">De pincode is niet juist.</div>}
        <div className="knoppenrij">
          <button type="submit" className="knop primair">
            Openen
          </button>
          <button type="button" className="knop" onClick={opAfbreken}>
            Annuleren
          </button>
        </div>
      </form>
    </div>
  );
}
