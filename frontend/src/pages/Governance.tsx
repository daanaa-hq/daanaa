import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function Governance() {
  usePageMeta('Governance & Accountability', 'Learn how Daanaa makes decisions, protects independence, and remains accountable to the nonprofits and donors we serve.')

  return (
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy pt-nav">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-caption text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-caption text-muted-cream">Governance</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-10 md:gap-16">
            <div className="max-w-[720px]">
              <span className="font-body text-label font-medium tracking-[0.08em] text-soft-gold uppercase">Trust & Accountability</span>
              <h1 className="font-display italic text-warm-cream mt-3 leading-[1.05] tracking-[-0.01em]">
                Governance & Accountability
              </h1>
              <p className="mt-5 font-body text-title-sm leading-[1.65] text-muted-cream">
                How we make decisions, protect independence, and remain accountable.
              </p>
            </div>
            <div className="shrink-0 hidden md:flex justify-end">
              <img src="/logo.png" alt="Daanaa" className="w-48 h-48 lg:w-56 lg:h-56 object-contain drop-shadow-[0_12px_48px_rgba(201,169,110,0.22)]" />
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[960px] mx-auto px-6 lg:px-12">

          {/* Our Purpose */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em]">
              Our Purpose
            </h2>
            <div className="mt-5 space-y-4 font-body text-lead text-cool-grey leading-[1.7]">
              <p>
                Daanaa exists to help people discover causes they care about and support them with confidence.
              </p>
              <p>
                Every decision we make is measured against that purpose.
              </p>
              <p>
                If a feature, partnership, or opportunity does not help people make informed giving decisions, it does not belong on the platform.
              </p>
            </div>
          </section>

          <hr className="border-light-grey my-12" />

          {/* Our Commitments */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em]">
              Our Commitments
            </h2>
            <div className="mt-8 space-y-8">
              <div>
                <h3 className="font-display text-deep-navy text-title md:text-title-lg">We do not accept paid placement</h3>
                <p className="mt-3 font-body text-lead text-cool-grey leading-[1.7]">
                  Organizations cannot pay to appear higher in search results.
                </p>
                <p className="mt-2 font-body text-lead text-cool-grey leading-[1.7]">
                  Visibility is based on publicly available information and transparent methodologies, not advertising budgets.
                </p>
              </div>

              <div>
                <h3 className="font-display text-deep-navy text-title md:text-title-lg">We do not control donor funds</h3>
                <p className="mt-3 font-body text-lead text-cool-grey leading-[1.7]">
                  Donations do not pass through Daanaa.
                </p>
                <p className="mt-2 font-body text-lead text-cool-grey leading-[1.7]">
                  Daanaa links to an organization's own official website. Anyone who chooses to give deals with the nonprofit directly.
                </p>
                <p className="mt-2 font-body text-lead text-cool-grey leading-[1.7]">
                  Daanaa does not hold, process, or transfer charitable funds.
                </p>
              </div>

              <div>
                <h3 className="font-display text-deep-navy text-title md:text-title-lg">We do not sell donor activity</h3>
                <p className="mt-3 font-body text-lead text-cool-grey leading-[1.7]">
                  We do not build profiles based on giving behavior.
                </p>
                <p className="mt-2 font-body text-lead text-cool-grey leading-[1.7]">
                  We do not encourage public displays of generosity.
                </p>
                <p className="mt-2 font-body text-lead text-cool-grey leading-[1.7]">
                  Giving is personal and should remain in the hands of the giver.
                </p>
              </div>

              <div>
                <h3 className="font-display text-deep-navy text-title md:text-title-lg">We strive to treat organizations fairly</h3>
                <p className="mt-3 font-body text-lead text-cool-grey leading-[1.7]">
                  Large and small organizations deserve equal consideration.
                </p>
                <p className="mt-2 font-body text-lead text-cool-grey leading-[1.7]">
                  We seek to provide context, not judgment.
                </p>
                <p className="mt-2 font-body text-lead text-cool-grey leading-[1.7]">
                  Our goal is to help people understand public information, not to tell them what conclusions they must reach.
                </p>
              </div>
            </div>
          </section>

          <hr className="border-light-grey my-12" />

          {/* How Decisions Are Made */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em]">
              How Decisions Are Made
            </h2>
            <div className="mt-5 space-y-4 font-body text-lead text-cool-grey leading-[1.7]">
              <p>
                Most day to day decisions involve maintaining data, improving search results, verifying public information, and correcting errors.
              </p>
              <p>
                Significant decisions, including methodology changes, new data sources, partnerships, and governance updates, are documented and reviewed before implementation.
              </p>
              <p>
                When a decision could affect fairness, transparency, privacy, or independence, additional review is required.
              </p>
            </div>
          </section>

          <hr className="border-light-grey my-12" />

          {/* Human Responsibility */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em]">
              Human Responsibility
            </h2>
            <div className="mt-5 space-y-4 font-body text-lead text-cool-grey leading-[1.7]">
              <p>
                Technology helps us organize information and improve the experience of using Daanaa.
              </p>
              <p>
                Technology does not replace accountability.
              </p>
              <p>
                People remain responsible for the principles, policies, and decisions that shape the platform.
              </p>
              <p>
                When mistakes occur, our responsibility is to acknowledge them, correct them, and learn from them.
              </p>
            </div>
          </section>

          <hr className="border-light-grey my-12" />

          {/* Stewardship Principles */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em]">
              Stewardship Principles
            </h2>
            <p className="mt-5 font-body text-lead text-cool-grey leading-[1.7]">
              Daanaa operates according to eleven stewardship principles:
            </p>
            <ol className="mt-6 space-y-3 font-body text-lead text-cool-grey leading-[1.7]">
              <li><span className="font-semibold">1. Mission before growth</span></li>
              <li><span className="font-semibold">2. Privacy is core</span></li>
              <li><span className="font-semibold">3. Trust signals must be evidence based</span></li>
              <li><span className="font-semibold">4. Fairness to small organizations</span></li>
              <li><span className="font-semibold">5. We do not weaponize transparency</span></li>
              <li><span className="font-semibold">6. Mistakes must be corrected quickly</span></li>
              <li><span className="font-semibold">7. Independence must be protected</span></li>
              <li><span className="font-semibold">8. We do not control donor funds</span></li>
              <li><span className="font-semibold">9. Decisions should be explainable later</span></li>
              <li><span className="font-semibold">10. AI is a tool, not a substitute for responsibility</span></li>
              <li><span className="font-semibold">11. Principles are strengthened, not quietly weakened</span></li>
            </ol>
            <p className="mt-6 font-body text-lead text-cool-grey leading-[1.7]">
              These principles guide our work today and are intended to outlast any individual leader, technology, or methodology.
            </p>
          </section>

          <hr className="border-light-grey my-12" />

          {/* Transparency */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em]">
              Transparency
            </h2>
            <p className="mt-5 font-body text-lead text-cool-grey leading-[1.7]">
              We believe people should be able to understand how Daanaa operates.
            </p>
            <p className="mt-4 font-body text-lead text-cool-grey leading-[1.7]">
              For that reason we publish:
            </p>
            <ul className="mt-4 space-y-2 ml-6 font-body text-lead text-cool-grey leading-[1.7]">
              <li>• Our methodology</li>
              <li>• Our stewardship principles</li>
              <li>• Major governance updates</li>
              <li>• Material corrections</li>
              <li>• Data source information</li>
            </ul>
            <p className="mt-6 font-body text-lead text-cool-grey leading-[1.7]">
              Transparency is not a feature of the platform.
            </p>
            <p className="mt-2 font-body text-lead text-cool-grey leading-[1.7]">
              It is part of the responsibility that comes with building it.
            </p>
          </section>

          <hr className="border-light-grey my-12" />

          {/* Looking Ahead */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em]">
              Looking Ahead
            </h2>
            <div className="mt-5 space-y-4 font-body text-lead text-cool-grey leading-[1.7]">
              <p>
                Governance is not something that is finished.
              </p>
              <p>
                As Daanaa grows, we expect our processes, advisory structures, and oversight mechanisms to evolve.
              </p>
              <p>
                What should not change is our commitment to stewardship, independence, fairness, and service.
              </p>
              <p>
                These are the standards we hold ourselves to, and the standards by which we invite others to judge our work.
              </p>
            </div>
          </section>

          {/* Related links */}
          <div className="mt-16 pt-12 border-t border-light-grey">
            <p className="font-body text-label font-semibold tracking-[0.08em] text-cool-grey uppercase mb-4">
              Related
            </p>
            <div className="flex flex-wrap gap-4">
              <Link
                to="/methodology"
                className="inline-flex items-center gap-2 font-body text-body text-soft-gold hover:text-bright-gold transition-colors"
              >
                Our methodology →
              </Link>
              <Link
                to="/methodology#financial-context"
                className="inline-flex items-center gap-2 font-body text-body text-soft-gold hover:text-bright-gold transition-colors"
              >
                Financial context →
              </Link>
              <a
                href="mailto:hello@daanaa.org"
                className="inline-flex items-center gap-2 font-body text-body text-soft-gold hover:text-bright-gold transition-colors"
              >
                Send feedback →
              </a>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
