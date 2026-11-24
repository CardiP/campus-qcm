export const RELEASE = '20261124-5';
export const MEDIA_CACHE = 'campus-qcm-media-v1';

export function questionAssets(questions, baseURL) {
  return [...new Set(questions.flatMap(q => [...(q.images || []), ...(q.contextImages || []), ...(q.correctionImages || [])])
    .map(path => new URL(path, baseURL).href))];
}

// One queue for the whole library: the current session always goes first.
export class ImageDownloader {
  constructor({urls, cache, fetcher = (url, options) => fetch(url, options), onChange = () => {}, concurrency = 4}) {
    this.urls = [...new Set(urls)];
    this.cache = cache;
    this.fetcher = fetcher;
    this.onChange = onChange;
    this.concurrency = concurrency;
    this.cached = new Set();
    this.priority = [];
    this.running = false;
    this.paused = false;
    this.failures = 0;
    this.controllers = new Set();
  }
  async scan() {
    const keys = await this.cache.keys();
    this.cached = new Set(keys.map(key => key.url));
    this.onChange();
  }
  prioritize(urls) {
    this.priority = urls;
    this.queue = [...new Set([...urls, ...this.urls])].filter(url => !this.cached.has(url) && !this.inFlight?.has(url));
  }
  pause() {
    this.paused = true;
    for (const controller of this.controllers) controller.abort();
    this.onChange();
  }
  async resume() {
    if (this.running) return this.task;
    this.paused = false;
    this.failures = 0;
    this.inFlight = new Set();
    this.prioritize(this.priority);
    this.running = true;
    this.onChange();
    this.task = Promise.all(Array.from({length: this.concurrency}, () => this.work()))
      .finally(() => { this.running = false; this.onChange(); });
    return this.task;
  }
  async work() {
    while (this.queue.length && !this.paused) {
      const url = this.queue.shift();
      this.inFlight.add(url);
      const controller = new AbortController();
      this.controllers.add(controller);
      const timer = setTimeout(() => controller.abort(), 15000);
      try {
        const response = await this.fetcher(url, {signal: controller.signal});
        if (!response.ok || !response.headers.get('content-type')?.startsWith('image/')) throw new Error('Image unavailable');
        await this.cache.put(url, response);
        this.cached.add(url);
        this.failures = 0;
      } catch {
        if (++this.failures >= 3) this.paused = true;
      } finally {
        clearTimeout(timer);
        this.controllers.delete(controller);
        this.inFlight.delete(url);
        this.onChange();
      }
    }
  }
}

export async function prepareOffline(questions, onChange) {
  if (!('serviceWorker' in navigator) || !('caches' in window)) throw new Error('Offline storage unavailable');
  let registration;
  try {
    registration = await navigator.serviceWorker.register('./sw.js', {updateViaCache: 'none'});
  } catch (error) {
    // Reopening while offline must use the already installed worker.
    registration = await navigator.serviceWorker.getRegistration('./');
    if (!registration) throw error;
  }
  // A first visit must be controlled before we advertise offline readiness.
  await new Promise((resolve, reject) => {
    const done = () => {
      if (!navigator.serviceWorker.controller) return;
      clearTimeout(timer);
      navigator.serviceWorker.removeEventListener('controllerchange', done);
      resolve();
    };
    const timer = setTimeout(() => {
      navigator.serviceWorker.removeEventListener('controllerchange', done);
      reject(new Error('Offline setup interrupted'));
    }, 45000);
    navigator.serviceWorker.addEventListener('controllerchange', done);
    done();
  });
  const downloader = new ImageDownloader({
    urls: questionAssets(questions, document.baseURI),
    cache: await caches.open(MEDIA_CACHE),
    onChange
  });
  await downloader.scan();
  // Update checks also happen on subsequent visits; never reload an active quiz.
  registration.update().catch(() => {});
  return downloader;
}
