/**
 * Eén tegel in de leerlingmodus: groot beeld, kort label.
 *
 * Labels zijn altijd platte tekst; er wordt nooit HTML uit de inhoud
 * gerenderd. Ontbreekt de afbeelding, dan valt de tegel terug op de emoji.
 */

import type { Tegel } from '../types';
import { Beeld } from './Beeld';

interface Props {
  tegel: Tegel;
  actief: boolean;
  gekozen: boolean;
  /** Muis- en aanraakbediening voor tests door de begeleider. */
  bedienbaar: boolean;
  opKlik: () => void;
}

export function TegelWeergave({ tegel, actief, gekozen, bedienbaar, opKlik }: Props) {
  const klassen = ['tegel'];
  if (actief) klassen.push('actief');
  if (gekozen) klassen.push('gekozen');
  if (bedienbaar) klassen.push('bedienbaar');

  return (
    <div
      className={klassen.join(' ')}
      style={{ background: tegel.kleur ?? '#1e293b' }}
      onClick={bedienbaar ? opKlik : undefined}
      role="img"
      aria-label={tegel.label}
      aria-current={actief ? 'true' : undefined}
    >
      <div className="tegel-beeld">
        <Beeld verwijzing={tegel.image} emoji={tegel.emoji} />
      </div>
      <div className="tegel-label">{tegel.label}</div>
    </div>
  );
}
