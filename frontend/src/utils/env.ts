/**
 * Centralizes import.meta.env access so tests can mock this module.
 */
export function getApiBase(): string {
  return (import.meta.env.VITE_API_URL as string) || 'http://localhost:5000'
}
