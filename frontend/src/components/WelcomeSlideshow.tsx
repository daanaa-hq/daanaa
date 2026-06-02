import { useState } from 'react'
import { Link } from 'react-router-dom'

// First-visit onboarding. Shows once (localStorage), dismissable, skippable.
// Calm card-by-card intro to who we are + the features that matter.

const SEEN_KEY = 'daanaa-welcome-seen'

interface Slide {
  tag: string
  title: string
  body: string
  accent?: string
}

const SLIDES: Slide[] = [
  {
    tag: 'Welcome',
    title: 'Daanaa means wise',
    body: `A wise person doesn't hold on to kindness. They pass it on. That is what Daanaa is here to help you do, with giving that is as thoughtful as it is generous.`,
  },
  {
    tag: 'Discover',
    title: 'Find the invisible 97%',
    body: `There are 1.8 million nonprofits in America, and almost none are ones you have heard of. Search by cause, by place, or in plain words, like 'after school reading help in Austin', and meet the small ones doing real good.`,
  },
  {
    tag: 'How it works',
    title: 'Every nonprofit gets a voice',
    body: `Most of these had no description anywhere, so we use public records and AI to write a clear mission for each one, just so it can be found. When a nonprofit claims its page, it makes those words its own.`,
  },
  {
    tag: 'Give',
    title: 'From finding to giving, in a few clicks',
    body: `When you are ready, we send you straight to the nonprofit's own donation page. Daanaa never touches your money. We just keep the path short and the destination trustworthy.`,
  },
  {
    tag: 'Yours',
    title: 'Your giving stays with you',
    body: `Keep a private record of everything you give, ready for when it is time to itemize deductions. It lives on your device, never on our servers. No accounts, no tracking, no one watching where your generosity goes.`,
  },
]

export default function WelcomeSlideshow() {
  const [dismissed, setDismissed] = useState(() => {
    try { return localStorage.getItem(SEEN_KEY) === '1' } catch { return true }
  })
  const [i, setI] = useState(0)

  if (dismissed) return null

  const close = () => {
    try { localStorage.setItem(SEEN_KEY, '1') } catch { /* private mode */ }
    setDismissed(true)
  }

  const slide = SLIDES[i]
  const isLast = i === SLIDES.length - 1

  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center p-4"
      style={{ background: 'rgba(10,22,40,0.72)', backdropFilter: 'blur(6px)' }}
      role="dialog"
      aria-modal="true"
    >
      <div className="relative w-full max-w-[460px] bg-merit-cream rounded-2xl shadow-2xl overflow-hidden">
        {/* gold top rule */}
        <div className="h-[3px] w-full" style={{ background: 'linear-gradient(90deg, transparent, #C9A96E 30%, #D4B87A 50%, #C9A96E 70%, transparent)' }} />

        <button
          onClick={close}
          aria-label="Skip intro"
          className="absolute top-4 right-4 p-1.5 text-cool-grey/60 hover:text-deep-navy transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="4" y1="4" x2="20" y2="20" /><line x1="20" y1="4" x2="4" y2="20" />
          </svg>
        </button>

        <div className="px-8 pt-10 pb-7 min-h-[300px] flex flex-col">
          <span className="inline-flex self-start items-center px-2.5 py-0.5 rounded-full bg-soft-gold/12 border border-soft-gold/25 font-body text-[10px] font-semibold tracking-[0.1em] uppercase text-soft-gold mb-5">
            {slide.tag}
          </span>
          <h2 className="font-display italic text-deep-navy text-[28px] leading-[1.15] tracking-[-0.01em] mb-4">
            {slide.title}
          </h2>
          <p className="font-body text-[15px] text-cool-grey leading-[1.65] flex-1">
            {slide.body}
          </p>

          {/* dots */}
          <div className="flex items-center gap-1.5 mt-7 mb-5">
            {SLIDES.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setI(idx)}
                aria-label={`Slide ${idx + 1}`}
                className="h-1.5 rounded-full transition-all"
                style={{
                  width: idx === i ? 20 : 6,
                  background: idx === i ? '#C9A96E' : 'rgba(10,22,40,0.18)',
                }}
              />
            ))}
          </div>

          <div className="flex items-center justify-between">
            <button
              onClick={close}
              className="font-body text-[13px] text-cool-grey hover:text-deep-navy transition-colors"
            >
              Skip
            </button>
            {isLast ? (
              <Link
                to="/directory"
                onClick={close}
                className="inline-flex items-center gap-1.5 px-6 py-2.5 rounded-full bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors"
              >
                Explore the directory
              </Link>
            ) : (
              <button
                onClick={() => setI(i + 1)}
                className="inline-flex items-center gap-1.5 px-6 py-2.5 rounded-full bg-deep-navy text-warm-cream font-body text-[14px] font-semibold hover:bg-navy-mid transition-colors"
              >
                Next
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
