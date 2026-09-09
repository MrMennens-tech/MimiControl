/**
 * Beeld met terugval.
 *
 * Is er een afbeelding ingesteld, dan wordt die getoond. Ontbreekt het
 * bestand of is het onleesbaar, dan valt de app netjes terug op de emoji.
 * Zo blijft de omgeving werken ook als de familie een bestand verplaatst.
 */

import { useEffect, useState } from 'react';
import { useMediaUrl } from '../hooks/useMediaUrl';

interface Props {
  verwijzing?: string;
  emoji?: string;
  /** Alternatieve tekst; leeg laten wanneer het label er al naast staat. */
  alt?: string;
  className?: string;
}

export function Beeld({ verwijzing, emoji, alt = '', className }: Props) {
  const url = useMediaUrl(verwijzing);
  const [fout, zetFout] = useState(false);

  useEffect(() => {
    zetFout(false);
  }, [url]);

  if (url && !fout) {
    return <img className={className} src={url} alt={alt} onError={() => zetFout(true)} />;
  }
  return (
    <span className={className} aria-hidden={alt === '' ? 'true' : undefined}>
      {emoji ?? '⬜'}
    </span>
  );
}
