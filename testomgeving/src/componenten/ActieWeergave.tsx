/**
 * Weergave van een eindactie: groot beeld, rustige beweging, korte tekst.
 *
 * Het geluid en de timing komen van de ActionPlayer; hier wordt alleen
 * getekend. Er zijn geen felle flitsen en niets knippert.
 */

import { useMemo } from 'react';
import type { LopendeActie } from '../modules/ActionPlayer';
import { Beeld } from './Beeld';

interface Props {
  lopend: LopendeActie;
  /** Muis- of aanraakklik beëindigt de actie (voor de begeleider). */
  opKlik?: () => void;
}

/** Vaste posities voor de confettistukjes, zodat er niets willekeurig flikkert. */
function maakConfetti(kleur: string) {
  const kleuren = [kleur, '#fde047', '#38bdf8', '#f472b6', '#4ade80'];
  return Array.from({ length: 28 }, (_, i) => ({
    links: `${(i * 97) % 100}%`,
    vertraging: `${(i % 7) * 0.35}s`,
    duur: `${3.4 + (i % 5) * 0.45}s`,
    kleur: kleuren[i % kleuren.length],
  }));
}

export function ActieWeergave({ lopend, opKlik }: Props) {
  const { tegel, actie } = lopend;
  const kleur = actie.kleur ?? tegel.kleur ?? '#38bdf8';
  const confetti = useMemo(() => maakConfetti(kleur), [kleur]);
  const emoji = actie.emoji ?? tegel.emoji;
  const tekst = actie.tekst ?? tegel.label;

  return (
    <div
      className="actie-laag"
      style={{ ['--actiekleur' as string]: kleur }}
      onClick={opKlik}
      role="status"
      aria-live="polite"
    >
      {actie.type === 'colorSweep' && <div className="kleurgolf" />}
      {(actie.type === 'confetti' || actie.type === 'animation') && <div className="actie-gloed" />}
      {actie.type === 'confetti' &&
        confetti.map((stuk, i) => (
          <span
            key={i}
            className="confetti-stuk"
            style={{
              left: stuk.links,
              background: stuk.kleur,
              animationDelay: stuk.vertraging,
              animationDuration: stuk.duur,
            }}
          />
        ))}

      <div className={`actie-beeld${actie.type === 'animation' ? ' animatie-figuur' : ''}`}>
        <Beeld verwijzing={tegel.image} emoji={emoji} />
      </div>
      <div className="actie-tekst">{tekst}</div>
    </div>
  );
}
