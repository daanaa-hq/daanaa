# Daanaa Giving Wallet — Mobile App Setup

Build and deploy the Daanaa Giving Wallet as native iOS and Android apps using Capacitor.

## Prerequisites

```bash
# Node.js + npm (already have)
# Xcode (macOS) — needed for iOS build
# Android Studio + SDK — needed for Android build
```

## Quick Start

```bash
# 1. Install Capacitor CLI + dependencies
npm install -g @capacitor/cli
npm install @capacitor/core @capacitor/ios @capacitor/android

# 2. Build frontend (creates dist/)
cd frontend && npm run build

# 3. Add Capacitor platforms
npx cap add ios
npx cap add android

# 4. Build & sync native projects
npx cap build
```

## Build for iOS

```bash
# Open Xcode project
npx cap open ios

# In Xcode:
# 1. Select "Daanaa Wallet" scheme
# 2. Select simulator or device
# 3. Click ▶️ Run
# 4. When ready to ship: Product → Archive → Upload to App Store

# Or build from CLI:
cd ios/App
xcodebuild -workspace App.xcworkspace -scheme App -configuration Release -derivedDataPath build
```

## Build for Android

```bash
# Open Android Studio
npx cap open android

# In Android Studio:
# 1. Select "App" module
# 2. Build → Generate Signed Bundle / APK
# 3. Follow wizard (need keystore for signing)
# 4. When ready to ship: Play Console → Create release

# Or build from CLI:
cd android
./gradlew build
./gradlew bundleRelease
```

## Key Features in Mobile App

✅ **Full Wallet Functionality**
- View bookmarked organizations
- Log donations + volunteer hours
- E2E encrypted wallet (passphrase-protected)
- Offline support (reads from device storage)
- Sync to server when online (JWT token auth)

✅ **Native Integrations**
- File picker for backup import
- Share menu for exporting wallet backup
- Device permissions (camera for QR codes, etc.)
- Biometric unlock (fingerprint/Face ID) — future

✅ **App-Store Ready**
- Privacy Policy + Terms bundled
- Push notifications (future: donation receipts, cause updates)
- Crash reporting (Sentry)
- Analytics (Plausible — privacy-respecting)

## Development Workflow

```bash
# After code changes:

# 1. Rebuild frontend
cd frontend && npm run build

# 2. Sync to native projects
npx cap sync

# 3. If you changed native code, rebuild:
npx cap build

# 4. Test on device/simulator
npx cap open ios  # or android
```

## App Store Submission

### iOS
- App ID: `org.daanaa.wallet`
- Minimum iOS: 14.0
- Requires: App Privacy Policy + Terms of Service
- Screenshot + metadata via App Store Connect
- Testflight beta testing before release

### Android
- Package ID: `org.daanaa.wallet`
- Minimum Android: 7.0 (API 24)
- Signed APK + Bundle via Play Console
- Privacy Policy + Terms required
- Beta release via Play Console

## Offline Capability

The wallet works fully offline:
- All data stored in device's encrypted localStorage
- No live API calls required for core features
- Sync happens automatically when connection returns
- User never loses access to their bookmarks/history

## Troubleshooting

**App won't build:**
```bash
# Clean all build artifacts
rm -rf ios/App/Pods android/build node_modules
npm install && npm rebuild
npx cap build
```

**Wallet data not syncing:**
- Check network connection
- Verify JWT token hasn't expired (5-min expiry)
- Check browser console for sync errors
- Force sync by editing wallet (triggers debounced sync)

**App crashes on launch:**
- Check console logs: `npx cap open <platform>` → View logs
- Verify frontend build succeeded: `ls frontend/dist/index.html`
- Clear app cache: Settings → App → Clear Cache

## Publishing Checklist

- [ ] All tests passing
- [ ] Privacy Policy updated for mobile
- [ ] Terms of Service reviewed by attorney
- [ ] App Store screenshots (5x) + description
- [ ] Android: signed keystore generated
- [ ] iOS: development + distribution certificates
- [ ] Testflight beta feedback collected
- [ ] App version bumped (package.json + xcode + gradle)
- [ ] Release notes written
- [ ] Crash reporting configured (Sentry)
- [ ] Analytics working (Plausible)

## Future Mobile-Only Features

- Biometric unlock (faster than typing passphrase)
- QR code scanner (add orgs by QR)
- Push notifications (donation receipts, cause alerts)
- Widget (show favorite orgs on home screen)
- Siri shortcuts (voice-controlled giving)
- Watch app (notification sync)

---

**Status:** Ready for first release
**Estimated size:** ~5-8 MB (iOS), ~15-20 MB (Android)
**App stores:** iOS App Store, Google Play Store
