export function getApiBase(): string {
  return 'http://localhost:5000'
}

export function getFeatureFlag(name: string): boolean {
  return name === 'VITE_ENABLE_PROFILE_CONTEXTS'
}
