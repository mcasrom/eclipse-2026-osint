const CACHE = 'eclipse-2026-v26';
const ASSETS = [
  '/', '/index.html', '/manifest.json', '/icon.svg',
  '/vendor/leaflet.js', '/vendor/leaflet.css',
  '/data/2026/cities.json', '/data/2026/franja.geojson',
  '/data/2027/cities.json', '/data/2027/franja.geojson', '/data/events.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) =>
    Promise.all(ASSETS.map((a) =>
      fetch(a, { cache: 'reload' }).then((r) => { if (r && r.ok) return c.put(a, r); }).catch(() => {})
    ))
  ));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
  ));
  self.clients.claim();
  self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(cls){
    cls.forEach(function(c){ c.postMessage({ type: 'NEW_VERSION' }); });
  });
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;
  if (url.pathname.startsWith('/api/')) return; // previsión siempre en red
  // index: network-first; resto: cache con revalidación en red
  e.respondWith(
    fetch(e.request, { cache: 'no-cache' })
      .then((res) => {
        if (res && res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); }
        return res;
      })
      .catch(() => caches.match(e.request).then((cached) => cached || caches.match('/')))
  );
});
