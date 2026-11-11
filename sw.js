// Offcourt: la web funciona como app y, sin conexión, muestra la última versión guardada.
// Siempre intenta primero la red (los datos cambian a menudo) y solo si falla usa la copia.
const CACHE = 'offcourt-v1';
self.addEventListener('install', e => { self.skipWaiting(); e.waitUntil(caches.open(CACHE).then(c => c.addAll(['./', 'manifest.webmanifest', 'icons/icon-192.png']))); });
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;   // los marcadores en directo van siempre a la red
  // fichas completas: se guarda solo la última de cada liga (sin la versión en la dirección)
  const key = u.pathname.includes('/box/') ? new Request(u.origin + u.pathname) : e.request;
  e.respondWith(fetch(e.request).then(r => { const c = r.clone(); if (r.ok) caches.open(CACHE).then(k => k.put(key, c)); return r; })
    .catch(() => caches.match(key).then(r => r || caches.match('./'))));
});
