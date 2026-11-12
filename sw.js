// Offcourt: la web funciona como app y, sin conexión, muestra la última versión guardada.
// Siempre intenta primero la red (los datos cambian a menudo) y solo si falla usa la copia.
const CACHE = 'offcourt-v3';
self.addEventListener('install', e => { self.skipWaiting(); e.waitUntil(caches.open(CACHE).then(c => c.addAll(['./', 'manifest.webmanifest', 'icons/icon-192.png']))); });
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;   // los marcadores en directo van siempre a la red
  if (u.pathname.endsWith('/live.json')) return;                                  // directo: siempre a la red, sin guardar copias
  // fichas completas: se guarda solo la última de cada liga (sin la versión en la dirección)
  const key = u.pathname.includes('/box/') ? new Request(u.origin + u.pathname) : e.request;
  e.respondWith(fetch(e.request).then(r => { const c = r.clone(); if (r.ok) caches.open(CACHE).then(k => k.put(key, c)); return r; })
    .catch(() => caches.match(key).then(r => r || caches.match('./'))));
});

// avisos de Mi equipo: al tocar la notificación se abre (o enfoca) la web en el partido
self.addEventListener('notificationclick', e => {
  e.notification.close(); const url = (e.notification.data && e.notification.data.url) || './';
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(cs => {
    for (const c of cs) { if ('focus' in c) { c.navigate ? c.navigate(url) : 0; return c.focus() } }
    return self.clients.openWindow(url);
  }));
});
