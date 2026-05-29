# PWA Implementation Notes — Daanaa

## What's implemented (Phase 1)

| Asset | Path | Purpose |
|-------|------|---------|
| Web App Manifest | `frontend/public/manifest.json` | Install metadata, icons, theme |
| Service Worker | `frontend/public/sw.js` | Offline app shell + asset caching |
| SW registration | `frontend/src/main.tsx` | PROD-only registration (`import.meta.env.PROD` guard) |
| Meta tags | `frontend/index.html` | Apple mobile, theme-color, mobile-web-app-capable |

## Caching strategy

| Request type | Strategy |
|---|---|
| HTML navigation (`mode: navigate`) | Cache-first (offline shell), network fallback |
| Vite static assets (JS/CSS/images) | Stale-while-revalidate |
| Google Fonts (googleapis/gstatic) | Network-first, cached on success |
| `/api/*` (live data) | **Never cached** — always network-only |

Cache version key: `daanaa-shell-v1`. Increment to force eviction on deploy.

## iOS Safari limitations

iOS Safari (as of iOS 17) has these PWA restrictions that we cannot work around:

1. **No Web Push Notifications** — `PushManager` is available on iOS 16.4+ but requires the user to explicitly add the app to Home Screen first. Prompting for push permission inside the browser has no effect.
2. **No Background Sync** — `BackgroundSyncManager` is not available on iOS WebKit. Deferred giving-list writes must be done at foreground resume.
3. **Storage eviction** — iOS may evict PWA storage after ~7 days of non-use. Giving list is already in localStorage; no additional risk.
4. **Install prompt** — the `beforeinstallprompt` event is not fired on iOS. Users must add manually via the Share sheet → "Add to Home Screen". We should add a banner on iOS Safari that explains this.
5. **Service Worker scope** — iOS caches the SW registration per origin, not per path. The `scope: '/'` in `sw.js` registration is correct.

## Android Chrome — no known blockers

Android Chrome supports: install prompt, Web Push, Background Sync, full PWA APIs. Gate 2 will test installability and the install prompt UX.

## Gate 1 checklist for PWA

- [ ] Lighthouse PWA audit: installable + offline-ready (run in PROD build)
- [ ] iOS Safari: add to home screen → open offline → directory loads from cache
- [ ] Android Chrome: install prompt appears after 2 visits → installed app opens standalone
- [ ] `/api/*` requests are never served from cache (open Network tab → confirm)
- [ ] Cache version bumped after each deploy that changes JS/CSS hashes

## Future (Phase 3 / Capacitor)

If a native Capacitor wrapper is chosen, `frontend/src/lib/platform.ts` is the swap point:
- `apiUrl()` → native: point to `https://api.daanaa.org`; web: keep relative
- `openExternalUrl()` → native: `CapacitorBrowser.open()`; web: `window.open()`
- `isNative()` → uses `window.Capacitor.isNative`

The service worker is NOT registered in Capacitor mode (the native shell handles caching).
