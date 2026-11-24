import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import {ImageDownloader, questionAssets, RELEASE, MEDIA_CACHE} from '../public/offline.js';

const root = 'https://example.test/campus-qcm/';
const image = () => new Response('image bytes', {headers: {'Content-Type': 'image/webp'}});
function memoryCache() {
  const entries = new Map();
  const key = value => typeof value === 'string' ? value : value.url;
  return {
    keys: async () => [...entries.keys()].map(url => ({url})),
    match: async url => entries.get(key(url))?.clone(),
    put: async (url, response) => { entries.set(key(url), response.clone()); },
    addAll: async requests => { for (const request of requests) entries.set(key(request), new Response(key(request))); }
  };
}

test('session assets include unseen questions and corrections, with GitHub Pages base paths', () => {
  assert.deepEqual(questionAssets([
    {images: ['assets/q.webp'], correctionImages: ['assets/c.webp']},
    {images: ['assets/next.webp', 'assets/q.webp']}
  ], root), ['assets/q.webp', 'assets/c.webp', 'assets/next.webp'].map(path => root + path));
});

test('prefetch prioritizes a session, persists images, and skips already saved files on a new visit', async () => {
  const cache = memoryCache();
  await cache.put(root+'cached.webp', image());
  const urls = ['cached', 'later', 'question', 'correction'].map(name => root+name+'.webp');
  const fetched = [];
  const downloader = new ImageDownloader({urls, cache, concurrency: 1, fetcher: async url => {fetched.push(url); return image();}});
  await downloader.scan();
  downloader.prioritize(urls.slice(2));
  await downloader.resume();
  assert.deepEqual(fetched, [urls[2], urls[3], urls[1]]);
  assert.equal(downloader.cached.size, 4);
  const reopened = new ImageDownloader({urls, cache, fetcher: () => {throw Error('network should not be needed');}});
  await reopened.scan();
  await reopened.resume();
  assert.equal(reopened.cached.size, 4);
});

test('network loss pauses downloads without discarding saved images; reconnection downloads the rest', async () => {
  const urls = Array.from({length: 12}, (_, i) => root+i+'.webp');
  const cache = memoryCache();
  let online = false, requests = 0;
  const downloader = new ImageDownloader({urls, cache, concurrency: 1, fetcher: async url => {
    requests++;
    if (url === urls[0] || online) return image();
    throw Error('network disconnected');
  }});
  await downloader.scan();
  await downloader.resume();
  assert.equal(downloader.cached.size, 1);
  assert.equal(downloader.paused, true);
  assert.equal(requests, 4);
  online = true;
  await downloader.resume();
  assert.equal(downloader.cached.size, 12);
  assert.equal(requests, 15);
});

test('HTTP errors, HTML error pages and storage failures never count as ready', async () => {
  for (const failure of ['http', 'html', 'quota']) {
    const cache = memoryCache();
    if (failure === 'quota') cache.put = async () => {throw Error('QuotaExceededError');};
    const downloader = new ImageDownloader({urls: [root+'q.webp'], cache, fetcher: async () =>
      failure === 'http' ? new Response('', {status: 404}) : failure === 'html' ? new Response('<html>error</html>') : image()});
    await downloader.scan();
    await downloader.resume();
    assert.equal(downloader.cached.size, 0, failure);
  }
});

test('worker serves the shell, question data, unseen images and correction images with no server', async () => {
  const handlers = {}, stores = new Map();
  let fetchCalls = 0;
  const caches = {
    open: async name => {if (!stores.has(name)) stores.set(name, memoryCache()); return stores.get(name);},
    keys: async () => [...stores.keys()],
    delete: async name => stores.delete(name),
    match: async request => {for (const store of stores.values()) {const response = await store.match(request); if (response) return response;}}
  };
  const self = {registration: {scope: root}, addEventListener: (name, handler) => handlers[name] = handler,
    skipWaiting: async () => {}, clients: {claim: async () => {}, matchAll: async () => []}};
  vm.runInNewContext(await readFile(new URL('../public/sw.js', import.meta.url), 'utf8'), {
    self, caches, Request, URL, fetch: async () => {fetchCalls++; throw Error('server stopped');}
  });
  const dispatchLifecycle = name => new Promise((resolve, reject) => handlers[name]({waitUntil: task => task.then(resolve,reject)}));
  await dispatchLifecycle('install');
  await dispatchLifecycle('activate');
  const media = await caches.open(MEDIA_CACHE);
  await media.put(root+'assets/unseen.webp', image());
  await media.put(root+'assets/correction.webp', image());
  for (const [path, mode] of [['?reopen=1', 'navigate'], [`data/annales.json?v=${RELEASE}`, 'cors'], [`app.js?v=${RELEASE}`, 'cors'], ['assets/unseen.webp', 'cors'], ['assets/correction.webp', 'cors']]) {
    let result;
    handlers.fetch({request: {url: root+path, method:'GET', mode}, respondWith: task => result = task});
    assert.equal((await result).status, 200, path);
  }
  assert.equal(fetchCalls, 0);
});

test('every published question and correction image reserves its real dimensions', async () => {
  const data = async name => JSON.parse(await readFile(new URL(`../public/data/${name}.json`, import.meta.url), 'utf8'));
  const [annales, banques, sizes] = await Promise.all(['annales', 'banques', 'image-sizes'].map(data));
  for (const q of [...annales,...banques]) for (const path of [...q.images,...q.correctionImages]) {
    assert.ok(sizes[path]?.every(n => Number.isInteger(n) && n>0), path);
  }
  const html = await readFile(new URL('../public/index.html', import.meta.url), 'utf8');
  const app = await readFile(new URL('../public/app.js', import.meta.url), 'utf8');
  assert.ok(html.includes(`app.js?v=${RELEASE}`));
  assert.ok(app.includes(`offline.js?v=${RELEASE}`));
});
