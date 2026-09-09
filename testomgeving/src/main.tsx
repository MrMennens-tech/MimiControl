/**
 * Startpunt van de app.
 *
 * De service worker wordt alleen in de gebouwde versie geregistreerd, zodat
 * de app na één keer laden ook zonder internet blijft werken.
 */

import { createRoot } from 'react-dom/client';
import { App } from './App';
import './stijl/globaal.css';

const wortel = document.getElementById('root');
if (!wortel) throw new Error('Het element met id "root" ontbreekt in index.html.');

// Bewust geen StrictMode: die start effecten twee keer, waardoor timers van
// de scanner dubbel zouden lopen.
createRoot(wortel).render(<App />);

if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register(`${import.meta.env.BASE_URL}sw.js`).catch(() => {
      // Zonder service worker werkt de app ook, alleen niet offline.
    });
  });
}
