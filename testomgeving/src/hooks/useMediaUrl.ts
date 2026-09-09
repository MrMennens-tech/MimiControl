/**
 * Hook die een mediaverwijzing omzet naar een bruikbare URL.
 *
 * `media:<id>` komt uit de lokale opslag (IndexedDB) en krijgt een tijdelijke
 * object-URL die netjes weer wordt opgeruimd. Andere paden verwijzen naar
 * bestanden die met de app zijn meegeleverd. Ontbreekt het bestand, dan is
 * het resultaat `null` en toont de app het emoji-beeld als terugval.
 */

import { useEffect, useState } from 'react';
import { laadMedia } from '../modules/opslag';

export function useMediaUrl(verwijzing: string | undefined): string | null {
  const [url, zetUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!verwijzing) {
      zetUrl(null);
      return;
    }

    if (!verwijzing.startsWith('media:')) {
      zetUrl(verwijzing);
      return;
    }

    let geldig = true;
    let objectUrl: string | null = null;

    void laadMedia(verwijzing.slice('media:'.length)).then((bestand) => {
      if (!geldig) return;
      if (!bestand) {
        zetUrl(null);
        return;
      }
      objectUrl = URL.createObjectURL(bestand.blob);
      zetUrl(objectUrl);
    });

    return () => {
      geldig = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [verwijzing]);

  return url;
}
