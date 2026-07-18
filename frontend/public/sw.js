// Daanaa Service Worker — offline app shell + donor data cache
// Cache strategy:
//   - HTML navigations: NETWORK-FIRST so new deploys reach users immediately,
//     fall back to the cached shell only when offline
//   - Static Vite assets (content-hashed JS/CSS): stale-while-revalidate
//   - Org detail (/api/organizations/<ein>): network-first with cache
//     fallback — a donor's saved orgs keep working offline (name, mission,
//     EIN, mailing address for checks). Fresh data wins whenever online, so
//     donate links are never served stale when a network is available.
//   - Directory lists (/api/organizations?...): network-first, cache
//     fallback — recent searches survive going offline.
//   - Every other /api/* request: network-only (stats, wallet sync,
//     admin — never cached).
//   - Google Fonts: network-first with long-TTL cache
// Bump CACHE_NAME on any caching-behavior change so the activate handler
// purges the stale shell from previous versions.

const CACHE_NAME = 'daanaa-shell-v4';
const API_CACHE = 'daanaa-api-v1';
const API_MAX_ENTRIES = 400; // roughly: a full wallet + weeks of searches

// Trim oldest entries once the API cache exceeds its budget (FIFO by
// insertion order, which cache.keys() preserves).
async function trimApiCache() {
  const cache = await caches.open(API_CACHE);
  const keys = await cache.keys();
  if (keys.length <= API_MAX_ENTRIES) return;
  for (const key of keys.slice(0, keys.length - API_MAX_ENTRIES)) {
    await cache.delete(key);
  }
}

// Network-first with cache fallback for donor-visible API data.
async function apiNetworkFirst(request) {
  const cache = await caches.open(API_CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
      trimApiCache(); // fire-and-forget
    }
    return response;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return cached;
    throw err;
  }
}

// Minimal static shell — Vite hashes the JS/CSS filenames so we can't
// pre-cache them by name here. Instead we intercept navigations and
// serve the cached index.html (populated on first visit).
const SHELL_URLS = ['/'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS))
  );
  // Take over immediately (don't wait for old SW to retire)
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Delete old cache versions (keep the current shell + API caches)
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME && key !== API_CACHE)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API routing: cache only donor-visible directory data (GET), never
  // anything else (stats, wallet sync, impact log, admin).
  if (url.pathname.startsWith('/api/')) {
    const isOrgData =
      request.method === 'GET' &&
      /^\/api\/organizations(\/\d{9}(\/(similar|financials))?)?$/.test(url.pathname);
    if (isOrgData) {
      event.respondWith(apiNetworkFirst(request));
    }
    return; // everything else: network-only, untouched
  }

  // Never intercept cross-origin requests other than fonts
  const isGoogleFont =
    url.hostname === 'fonts.googleapis.com' ||
    url.hostname === 'fonts.gstatic.com';

  if (!isGoogleFont && url.origin !== self.location.origin) {
    return;
  }

  if (isGoogleFont) {
    // Network-first, cache fonts for 1 year
    event.respondWith(
      caches.open(CACHE_NAME).then(async (cache) => {
        const cached = await cache.match(request);
        if (cached) return cached;
        const response = await fetch(request);
        if (response.ok) cache.put(request, response.clone());
        return response;
      })
    );
    return;
  }

  // HTML navigations: network-first. Always try to fetch the freshest
  // index.html (which references the current hashed bundle), and refresh the
  // cached shell for offline use. Fall back to cache only when the network
  // fails. This is what lets new deploys reach returning visitors immediately.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put('/', copy));
          return response;
        })
        .catch(() => caches.match('/'))
    );
    return;
  }

  // Static assets (JS, CSS, images, fonts): stale-while-revalidate
  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cached = await cache.match(request);
      const networkFetch = fetch(request).then((response) => {
        if (response.ok) cache.put(request, response.clone());
        return response;
      });
      return cached || networkFetch;
    })
  );
});
