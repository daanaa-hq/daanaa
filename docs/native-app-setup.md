# Native App Setup (Capacitor)

Goal: wrap the existing React web app so wallet data rides the phone's own
iCloud / Google backup (true WhatsApp-style backup) and Daanaa is installable from
the app stores. No server account, no push tokens, no analytics SDKs.

`frontend/capacitor.config.ts` is already in place. The steps below need a Mac (for
iOS) and your developer accounts, so they can't be run on the Linux build server.

## Founder prerequisites (these gate publishing)
- **Apple Developer Program** — $99/yr (iOS build + App Store).
- **Google Play Developer** — $25 one-time (Android build + Play Store).
- A **Mac with Xcode** for iOS builds. Android can build on Linux with Android Studio / SDK.

## One-time setup
```bash
cd frontend
npm install @capacitor/core @capacitor/cli @capacitor/ios @capacitor/android
npx cap init Daanaa org.daanaa.app --web-dir dist   # config already committed; this confirms it
npm run build                                        # produce dist/
npx cap add ios        # Mac only
npx cap add android
npx cap sync
```

## Each release
```bash
cd frontend && npm run build && npx cap sync
npx cap open ios       # archive + upload in Xcode
npx cap open android   # build signed bundle in Android Studio
```

## Why this gives WhatsApp-style backup
The wallet lives in the app's local storage (localStorage / IndexedDB inside the
native WebView). iOS includes the app container in iCloud device backups; Android
includes it in Auto Backup. So when the user backs up or migrates their phone, their
giving record comes along — with zero server storage on our side. Until the wrapper
ships, the web app's "Text it to myself" + encrypted backup file cover durability.

## Privacy guardrails to keep in the native build
- No push notification tokens unless we add a feature that needs them (and only opt-in).
- No analytics/crash SDKs (Firebase, etc.) — keep `PRIVACY-INVARIANTS.md` true in native too.
- The app talks to the same public HTTPS API; no new endpoints that store giving data.
