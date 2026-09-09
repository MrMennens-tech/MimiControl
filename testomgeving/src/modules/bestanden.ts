/**
 * Hulpfuncties voor bestanden en volledig scherm.
 *
 * Downloads gebeuren met een tijdelijke object-URL: er komt geen server aan
 * te pas, het bestand wordt in de browser zelf gemaakt.
 */

/** Bied een tekstbestand aan als download. */
export function downloadTekst(naam: string, inhoud: string, mediatype: string): void {
  const blob = new Blob([inhoud], { type: `${mediatype};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const anker = document.createElement('a');
  anker.href = url;
  anker.download = naam;
  document.body.appendChild(anker);
  anker.click();
  anker.remove();
  // Even wachten zodat de download echt gestart is voordat we opruimen.
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

/** Lees een tekstbestand dat de begeleider heeft gekozen. */
export function leesTekstbestand(bestand: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const lezer = new FileReader();
    lezer.onload = () => resolve(String(lezer.result ?? ''));
    lezer.onerror = () => reject(lezer.error ?? new Error('Het bestand kon niet gelezen worden.'));
    lezer.readAsText(bestand, 'utf-8');
  });
}

/** Vraag volledig scherm aan. Lukt dat niet, dan gaat de app gewoon door. */
export async function naarVolledigScherm(element: HTMLElement = document.documentElement): Promise<boolean> {
  try {
    if (document.fullscreenElement) return true;
    if (!element.requestFullscreen) return false;
    await element.requestFullscreen();
    return true;
  } catch {
    return false;
  }
}

/** Verlaat volledig scherm. */
export async function verlaatVolledigScherm(): Promise<void> {
  try {
    if (document.fullscreenElement && document.exitFullscreen) await document.exitFullscreen();
  } catch {
    // niets te doen
  }
}

/** Waar wanneer de app nu in volledig scherm staat. */
export function isVolledigScherm(): boolean {
  return typeof document !== 'undefined' && document.fullscreenElement !== null;
}
