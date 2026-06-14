import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  isChunkError: boolean
}

// A failed lazy() chunk load usually means the user has an old tab open after a
// fresh deploy. A reload fetches the new assets and recovers cleanly.
function looksLikeChunkError(error: Error): boolean {
  const msg = `${error?.name ?? ''} ${error?.message ?? ''}`.toLowerCase()
  return (
    msg.includes('dynamically imported module') ||
    msg.includes('failed to fetch') ||
    msg.includes('loading chunk') ||
    msg.includes('importing a module script failed')
  )
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, isChunkError: false }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, isChunkError: looksLikeChunkError(error) }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Keep this lightweight: log for debugging, never send user data anywhere.
    console.error('Something broke while rendering:', error, info.componentStack)
  }

  render() {
    if (!this.state.hasError) return this.props.children

    const { isChunkError } = this.state

    return (
      <div className="min-h-[100dvh] bg-warm-cream flex items-center justify-center px-6">
        <div className="max-w-[440px] text-center">
          <p className="font-display italic text-deep-navy mb-3"
            style={{ fontSize: 'clamp(26px, 4vw, 36px)' }}>
            {isChunkError ? 'A fresh version is ready' : 'Something went sideways'}
          </p>
          <p className="font-body text-[15px] text-cool-grey leading-[1.6] mb-7">
            {isChunkError
              ? 'We just updated the site while you were here. Reload to pick up the latest version.'
              : 'This page ran into a problem on our end, not yours. A reload usually clears it. If it keeps happening, let us know and we will look into it.'}
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <button
              onClick={() => window.location.reload()}
              className="px-5 py-2.5 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors"
            >
              Reload the page
            </button>
            <a
              href="/"
              className="px-5 py-2.5 rounded-xl border border-light-grey text-deep-navy font-body text-[14px] font-medium hover:border-soft-gold/40 transition-colors"
            >
              Back to home
            </a>
          </div>
        </div>
      </div>
    )
  }
}
