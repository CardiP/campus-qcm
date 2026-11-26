const RELEASE = '20261126-1';
const SHELL_CACHE = `campus-qcm-shell-${RELEASE}`;
const MEDIA_CACHE = 'campus-qcm-media-v1';
const ROOT = self.registration.scope;
const SHELL = [
  './', './index.html', './manifest.webmanifest', './assets/icon.svg',
  ...['app.js', 'core.js', 'offline.js', 'styles.css', 'data/annales.json', 'data/banques.json', 'data/anatomie.json', 'data/medicament.json', 'data/image-sizes.json']
    .map(path => `./${path}?v=${RELEASE}`)
].map(path => new URL(path, ROOT).href);

self.addEventListener('install', event => {
  // Atomic shell installation: never replace a working offline version with half a download.
  event.waitUntil(caches.open(SHELL_CACHE)
    .then(cache => cache.addAll(SHELL.map(url => new Request(url, {cache: 'reload'}))))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const old = (await caches.keys()).filter(name => name.startsWith('campus-qcm-shell-') && name !== SHELL_CACHE).sort().reverse();
    // Keep the previous shell for tabs that are already open during an update.
    await Promise.all(old.slice(1).map(name => caches.delete(name)));
    await self.clients.claim();
    const clients = await self.clients.matchAll({type: 'window'});
    clients.forEach(client => client.postMessage({type: 'CAMPUS_VERSION', version: RELEASE}));
  })());
});

self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || !url.href.startsWith(ROOT)) return;
  if (request.mode === 'navigate') {
    // Shell and JSON always belong to the same release, even during a network cut.
    event.respondWith(caches.open(SHELL_CACHE).then(async cache => (await cache.match(ROOT)) || fetch(request)));
    return;
  }
  if (url.pathname.endsWith('.webp')) {
    event.respondWith((async () => {
      const cache = await caches.open(MEDIA_CACHE);
      const cached = await cache.match(request);
      if (cached) return cached;
      const response = await fetch(request);
      if (response.ok && response.headers.get('content-type')?.startsWith('image/')) {
        // A quota error must not prevent an online image from being displayed.
        await cache.put(request, response.clone()).catch(() => {});
      }
      return response;
    })());
    return;
  }
  event.respondWith((async () => {
    const cache = await caches.open(SHELL_CACHE);
    return (await cache.match(request)) || (await caches.match(request)) || fetch(request);
  })());
});
