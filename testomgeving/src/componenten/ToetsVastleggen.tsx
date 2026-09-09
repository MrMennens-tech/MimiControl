/**
 * Toets vastleggen door de gewenste toets in te drukken.
 *
 * De begeleider klikt op "Toets vastleggen" en laat het mimiekhulpmiddel de
 * toets versturen. Alle drie de kenmerken worden bewaard (`code`, `key` en
 * `keyCode`), zodat de toets later ook herkend wordt wanneer één van die
 * kenmerken ontbreekt.
 */

import { useEffect, useState } from 'react';
import type { ToetsBinding } from '../types';
import { bindingUitEvent, omschrijfBinding } from '../modules/toetsnamen';

interface Props {
  naam: string;
  uitleg: string;
  binding: ToetsBinding;
  opNieuweBinding: (binding: ToetsBinding) => void;
  uitgeschakeld?: boolean;
}

export function ToetsVastleggen({ naam, uitleg, binding, opNieuweBinding, uitgeschakeld }: Props) {
  const [wacht, zetWacht] = useState(false);

  useEffect(() => {
    if (!wacht) return;

    const opKeydown = (event: KeyboardEvent) => {
      // Voorkom dat spatie of pijltjes de pagina laten scrollen.
      event.preventDefault();
      event.stopPropagation();
      if (event.key === 'Escape' && event.code === 'Escape') {
        // Escape blijft bruikbaar om het vastleggen af te breken.
        zetWacht(false);
        return;
      }
      opNieuweBinding(bindingUitEvent(event));
      zetWacht(false);
    };

    window.addEventListener('keydown', opKeydown, true);
    return () => window.removeEventListener('keydown', opKeydown, true);
  }, [wacht, opNieuweBinding]);

  return (
    <div className="veld">
      <span className="veldnaam">{naam}</span>
      <div className={`toetsvak${wacht ? ' wacht' : ''}`}>
        {wacht ? 'Druk nu de gewenste toets in… (Escape breekt af)' : omschrijfBinding(binding)}
      </div>
      <div className="knoppenrij" style={{ marginTop: 0 }}>
        <button
          type="button"
          className="knop klein"
          onClick={() => zetWacht(true)}
          disabled={uitgeschakeld || wacht}
        >
          Toets vastleggen
        </button>
      </div>
      <small>{uitleg}</small>
    </div>
  );
}
