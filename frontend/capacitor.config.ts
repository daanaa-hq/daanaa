import type { CapacitorConfig } from '@capacitor/cli'

// Native wrapper config for the Daanaa app (WhatsApp-style: wallet data rides the
// device's own iCloud/Google backup once wrapped). The web build in `dist/` is the
// app's web layer; Capacitor wraps it into iOS/Android shells.
//
// Privacy note: no server account, no push tokens, no analytics SDKs. The wallet
// stays in the app's local storage, which the OS includes in device backups.
const config: CapacitorConfig = {
  appId: 'org.daanaa.app',
  appName: 'Daanaa',
  webDir: 'dist',
  // App talks to the same public API over HTTPS in production.
  server: { androidScheme: 'https' },
  ios: { contentInset: 'always' },
}

export default config
