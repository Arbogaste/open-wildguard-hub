/* open-wildguard-hub — offline-first service worker.
   Caches the demo shell + all self-hosted vendor assets so the command center
   loads with zero network. Map tiles are cached opportunistically (online);
   when offline, Leaflet falls back to vendor/leaflet/tile-offline.png. */

const CACHE = 'wildguard-shell-v2';

const PRECACHE = [
  './',
  './index.html',
  './i18n/en.json',
  './i18n/it.json',
  './assets/brand/favicon-32.png',
  './assets/brand/favicon-180.png',
  './assets/brand/favicon-256.png',
  './vendor/fonts/fonts.css',
  './vendor/leaflet/leaflet.css',
  './vendor/leaflet/leaflet.js',
  './vendor/leaflet/images/marker-icon.png',
  './vendor/leaflet/images/marker-icon-2x.png',
  './vendor/leaflet/images/marker-shadow.png',
  './vendor/leaflet/images/layers.png',
  './vendor/leaflet/images/layers-2x.png',
  './vendor/leaflet/tile-offline.png',
  './vendor/fontawesome/css/all.min.css',
  './vendor/fontawesome/webfonts/fa-solid-900.woff2',
  './vendor/fontawesome/webfonts/fa-regular-400.woff2',
  './vendor/fontawesome/webfonts/fa-brands-400.woff2'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then(async (cache) => {
      // Precache the shell. Also pull in every font woff2 referenced by fonts.css.
      await cache.addAll(PRECACHE);
      try {
        const css = await (await fetch('./vendor/fonts/fonts.css')).text();
        const fonts = [...css.matchAll(/url\(\.\/([^)]+\.woff2)\)/g)]
          .map((m) => './vendor/fonts/' + m[1]);
        await cache.addAll([...new Set(fonts)]);
      } catch (_) { /* fonts are optional for offline boot */ }
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  const isTile = /basemaps\.cartocdn\.com/.test(url.hostname);

  if (isTile) {
    // Tiles: network-first, cache successes, fall back to cache offline.
    e.respondWith(
      fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
        return res;
      }).catch(() => caches.match(req))
    );
    return;
  }

  // Shell/vendor: cache-first.
  e.respondWith(
    caches.match(req).then((cached) => cached || fetch(req).then((res) => {
      if (url.origin === location.origin) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
      }
      return res;
    }).catch(() => cached))
  );
});
