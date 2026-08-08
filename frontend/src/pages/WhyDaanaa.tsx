import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function WhyDaanaa() {
  usePageMeta('Why Daanaa Exists', 'The story behind Daanaa and our commitment to help people discover nonprofits with confidence.')

  return (
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy pt-nav">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-caption text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-caption text-muted-cream">Why Daanaa</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-10 md:gap-16">
            <div className="max-w-[720px]">
              <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(48px, 6vw, 72px)' }}>
                Why Daanaa Exists
              </h1>
            </div>
            <div className="shrink-0 hidden md:flex justify-end">
              <img src="/logo.png" alt="Daanaa" className="w-48 h-48 lg:w-56 lg:h-56 object-contain drop-shadow-[0_12px_48px_rgba(201,169,110,0.22)]" />
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[720px] mx-auto px-6 lg:px-12">

          {/* Founder's message */}
          <div className="space-y-6 font-body text-title-sm leading-[1.8] text-cool-grey">

            <p>
              Daanaa began with a simple observation.
            </p>

            <p>
              People want to help.
            </p>

            <p>
              Every day, someone looks for a way to support a cause they care about. They may be searching for a local food bank, a scholarship fund, a place of worship, a community organization, or a nonprofit serving people they will never meet.
            </p>

            <p>
              At the same time, thousands of organizations are doing meaningful work without the visibility, resources, or recognition enjoyed by larger institutions.
            </p>

            <p>
              The information needed to connect the two often exists, but it is scattered across reports, filings, websites, and databases that were never designed to be easily understood.
            </p>

            <p>
              Daanaa was created to help bridge that gap.
            </p>

            <hr className="border-light-grey my-8" />

            <p className="font-semibold text-deep-navy">
              Our goal is not to tell people where to give.
            </p>

            <p>
              Our goal is to help people discover organizations, understand the public information available about them, and make their own informed decisions.
            </p>

            <p>
              We believe people deserve clear information, honest context, and the freedom to choose for themselves.
            </p>

            <p>
              We believe small organizations deserve to be seen.
            </p>

            <p>
              We believe trust is earned through transparency, fairness, and humility.
            </p>

            <hr className="border-light-grey my-8" />

            <p>
              Technology will change. Data sources will improve. Methods will evolve.
            </p>

            <p>
              What should remain constant is our commitment to stewardship and service.
            </p>

            <p>
              If Daanaa succeeds, it will not be because of technology alone. It will be because it earns trust over time.
            </p>

            <p className="font-semibold text-deep-navy">
              That trust matters more than growth.
            </p>

            <p>
              Welcome to Daanaa.
            </p>

          </div>

          {/* Story links */}
          <div className="mt-20 pt-12 border-t border-light-grey">
            <p className="font-body text-label font-semibold tracking-[0.08em] text-cool-grey uppercase mb-6">
              The full story
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

              <Link
                to="/methodology"
                className="group p-6 border border-light-grey rounded-lg hover:border-soft-gold/50 hover:bg-white/60 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-display text-deep-navy text-title-sm group-hover:text-soft-gold transition-colors">
                      How we score
                    </h3>
                    <p className="mt-2 font-body text-body text-cool-grey">
                      Our methodology for peer financial context and peer group analysis
                    </p>
                  </div>
                  <svg className="w-5 h-5 text-soft-gold mt-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </div>
              </Link>

              <Link
                to="/methodology#financial-context"
                className="group p-6 border border-light-grey rounded-lg hover:border-soft-gold/50 hover:bg-white/60 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-display text-deep-navy text-title-sm group-hover:text-soft-gold transition-colors">
                      Visibility levels
                    </h3>
                    <p className="mt-2 font-body text-body text-cool-grey">
                      What each tier means and how public data completeness varies
                    </p>
                  </div>
                  <svg className="w-5 h-5 text-soft-gold mt-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </div>
              </Link>

              <Link
                to="/governance"
                className="group p-6 border border-light-grey rounded-lg hover:border-soft-gold/50 hover:bg-white/60 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-display text-deep-navy text-title-sm group-hover:text-soft-gold transition-colors">
                      Governance
                    </h3>
                    <p className="mt-2 font-body text-body text-cool-grey">
                      How we make decisions and remain accountable to the mission
                    </p>
                  </div>
                  <svg className="w-5 h-5 text-soft-gold mt-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </div>
              </Link>

              <Link
                to="/the-invisible-97"
                className="group p-6 border border-light-grey rounded-lg hover:border-soft-gold/50 hover:bg-white/60 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-display text-deep-navy text-title-sm group-hover:text-soft-gold transition-colors">
                      The invisible 97%
                    </h3>
                    <p className="mt-2 font-body text-body text-cool-grey">
                      The nonprofits you've never heard of, and why they matter
                    </p>
                  </div>
                  <svg className="w-5 h-5 text-soft-gold mt-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </div>
              </Link>

              <Link
                to="/directory"
                className="group p-6 border border-light-grey rounded-lg hover:border-soft-gold/50 hover:bg-white/60 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-display text-deep-navy text-title-sm group-hover:text-soft-gold transition-colors">
                      The directory
                    </h3>
                    <p className="mt-2 font-body text-body text-cool-grey">
                      Search 1.7M nonprofits and discover organizations in your community
                    </p>
                  </div>
                  <svg className="w-5 h-5 text-soft-gold mt-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </div>
              </Link>

              <Link
                to="/wallet"
                className="group p-6 border border-light-grey rounded-lg hover:border-soft-gold/50 hover:bg-white/60 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-display text-deep-navy text-title-sm group-hover:text-soft-gold transition-colors">
                      Your wallet
                    </h3>
                    <p className="mt-2 font-body text-body text-cool-grey">
                      Keep a private record of your giving, right on your device
                    </p>
                  </div>
                  <svg className="w-5 h-5 text-soft-gold mt-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </div>
              </Link>

            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
