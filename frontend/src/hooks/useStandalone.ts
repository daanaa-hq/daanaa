import { useSyncExternalStore } from 'react'

// True when running as an installed app (home-screen PWA) rather than in a
// browser tab. Drives the focused "app posture": donor tools front and
// center, website chrome tucked away.
const QUERY = '(display-mode: standalone)'

function subscribe(cb: () => void) {
  const mq = window.matchMedia(QUERY)
  mq.addEventListener('change', cb)
  return () => mq.removeEventListener('change', cb)
}

function getSnapshot(): boolean {
  // iOS Safari legacy flag, then the standard display-mode media query
  return (navigator as unknown as { standalone?: boolean }).standalone === true
    || window.matchMedia(QUERY).matches
}

export function useStandalone(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, () => false)
}
