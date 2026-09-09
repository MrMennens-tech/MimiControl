/*
 * Service worker voor offline gebruik.
 *
 * Strategie: cache-first met netwerk als terugval. Bij de eerste keer laden
 * worden alle bestanden die de app opvraagt in de cache gezet; daarna werkt de
 * app volledig zonder internet. Er wordt niets naar buiten gestuurd: alleen
 * verzoeken naar de eigen oorsprong worden behandeld.
 */

const CACHE_NAAM = 'toetstest-v1';
const KERNBESTANDEN = ['./', './index.html', './manifest.webmanifest', './icoon.svg'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAAM)
      .then((cache) => cache.addAll(KERNBESTANDEN))
      .catch(() => undefined)
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((namen) =>
        Promise.all(namen.filter((naam) => naam !== CACHE_NAAM).map((naam) => caches.delete(naam))),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const verzoek = event.request;
  if (verzoek.method !== 'GET') return;

  const url = new URL(verzoek.url);
  // Alleen eigen bestanden: nooit externe adressen ophalen of cachen.
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.match(verzoek).then((gecachet) => {
      if (gecachet) return gecachet;
      return fetch(verzoek)
        .then((antwoord) => {
          if (antwoord && antwoord.ok && antwoord.type === 'basic') {
            const kopie = antwoord.clone();
            caches.open(CACHE_NAAM).then((cache) => cache.put(verzoek, kopie));
          }
          return antwoord;
        })
        .catch(() =>
          // Bij navigatie zonder netwerk: geef de app-shell terug.
          verzoek.mode === 'navigate'
            ? caches.match('./index.html').then((shell) => shell ?? Response.error())
            : Response.error(),
        );
    }),
  );
});
