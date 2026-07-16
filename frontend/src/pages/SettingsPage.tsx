import { useTheme } from '../contexts/ThemeContext'
import { usePageMeta } from '../hooks/usePageMeta'

// Mini preview of each theme: a tiny mock page (header bar, text lines, gold
// accent) rendered in that theme's actual colors, so the user sees what they
// are choosing before they click.
function ThemePreview({ mode, active, onSelect }: {
  mode: 'dark' | 'light'
  active: boolean
  onSelect: () => void
}) {
  const c = mode === 'dark'
    ? { page: '#0A1628', card: '#111D2E', line: '#F5F0EB', sub: '#D4CCBF', accent: '#C9A96E' }
    : { page: '#F8F7F5', card: '#FFFFFF', line: '#1E2530', sub: '#6B6257', accent: '#8B6F47' }

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={active}
      aria-label={`Use ${mode} theme`}
      className={`group flex-1 rounded-xl border-2 p-3 text-left transition-all duration-150 ${
        active
          ? 'border-soft-gold shadow-[0_0_0_3px_rgb(var(--soft-gold-rgb)/0.15)]'
          : 'border-navy-mid hover:border-soft-gold/50'
      }`}
    >
      {/* Mock page */}
      <div className="rounded-lg overflow-hidden border" style={{ background: c.page, borderColor: mode === 'dark' ? '#1A2744' : '#E5E0D8' }}>
        <div className="h-5 flex items-center gap-1 px-2" style={{ background: c.card }}>
          <span className="w-8 h-1.5 rounded-full" style={{ background: c.accent }} />
          <span className="ml-auto w-4 h-1.5 rounded-full opacity-40" style={{ background: c.line }} />
        </div>
        <div className="p-2.5 space-y-1.5">
          <span className="block w-3/4 h-2 rounded-full" style={{ background: c.line }} />
          <span className="block w-full h-1.5 rounded-full opacity-70" style={{ background: c.sub }} />
          <span className="block w-2/3 h-1.5 rounded-full opacity-70" style={{ background: c.sub }} />
          <div className="flex gap-1.5 pt-1">
            <span className="w-10 h-3 rounded-full" style={{ background: c.accent }} />
            <span className="w-10 h-3 rounded-full border" style={{ borderColor: c.sub, opacity: 0.6 }} />
          </div>
        </div>
      </div>

      {/* Label row */}
      <div className="mt-3 flex items-center justify-between px-0.5">
        <span className="font-body text-[14px] font-medium text-warm-cream capitalize">{mode}</span>
        <span
          className={`inline-flex items-center justify-center w-[18px] h-[18px] rounded-full border-2 transition-colors ${
            active ? 'border-soft-gold bg-soft-gold' : 'border-muted-cream/50'
          }`}
        >
          {active && (
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#0A1628" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          )}
        </span>
      </div>
    </button>
  )
}

export default function SettingsPage() {
  const { theme, toggleTheme } = useTheme()

  usePageMeta(
    'Settings | Daanaa',
    'Customize your Daanaa experience'
  )

  const select = (mode: 'dark' | 'light') => {
    if (mode !== theme) toggleTheme()
  }

  return (
    <div className="min-h-screen bg-deep-navy">
      <div className="max-w-2xl mx-auto px-6 pt-20 pb-16 lg:px-8">
        {/* Header */}
        <div className="mb-10">
          <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">
            Your preferences
          </span>
          <h1 className="mt-2 font-display italic text-warm-cream leading-[1.05]" style={{ fontSize: 'clamp(32px, 4vw, 44px)' }}>
            Settings
          </h1>
          <p className="mt-3 font-body text-[15px] text-muted-cream leading-[1.6]">
            Everything here stays on this device. Nothing is sent to our servers.
          </p>
        </div>

        {/* Appearance */}
        <section className="bg-dark-surface rounded-2xl border border-navy-mid p-6 md:p-8">
          <h2 className="font-body text-[16px] font-semibold text-warm-cream">Appearance</h2>
          <p className="mt-1 font-body text-[13px] text-muted-cream leading-[1.5]">
            Choose the theme that reads best for you. Every trust signal and
            disclosure is checked for readability in both.
          </p>

          <div className="mt-5 flex flex-col sm:flex-row gap-4">
            <ThemePreview mode="dark" active={theme === 'dark'} onSelect={() => select('dark')} />
            <ThemePreview mode="light" active={theme === 'light'} onSelect={() => select('light')} />
          </div>
        </section>

        {/* Privacy note */}
        <div className="mt-6 flex items-start gap-3 p-4 rounded-xl border border-navy-mid bg-dark-surface/60">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-soft-gold shrink-0 mt-0.5">
            <rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <p className="font-body text-[13px] text-muted-cream leading-[1.55]">
            Your preference is saved in this browser only — the same way your
            Giving Wallet works. No account, no tracking, deletable any time by
            clearing your browser data.
          </p>
        </div>
      </div>
    </div>
  )
}
