import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

const PROMISES = [
  {
    title: 'We will never take a cut of a donation.',
    body: 'Money moves directly from a donor to an organization, through the organization’s own channels. Daanaa is never in the middle, never the merchant of record, never a percentage. Not now, not at scale, not ever.',
  },
  {
    title: 'We will never sell you anything inside Daanaa.',
    body: 'The platform carries no ads, no sponsored results, no paid placement, no upsells, and no pitches, including for services offered by our own operating company. If you ever want professional help, there is a door you can open in your own settings. We will never knock on it.',
  },
  {
    title: 'We will never use what you give us to sell to you.',
    body: 'Information you entrust to Daanaa, your contact details, your custom mission, your notes, your activity on the platform, is used to operate Daanaa for you and for nothing else. It is never a lead, never a marketing signal, never shared with or used by any commercial arm, partner, or vendor. This is enforced in our code, not just in this sentence.',
  },
  {
    title: 'We will never sell or share your data.',
    body: 'Not to vendors, not to foundations, not to researchers without your explicit consent, not in aggregate forms that could identify you. Donor giving activity is never exposed, period.',
  },
  {
    title: 'We will never charge for the platform.',
    body: 'Discovery, your profile, your dashboard, your peer context, and every core tool we build for nonprofits is free, for the smallest organization on the same terms as the largest. If that ever has to change, it happens in public, with notice, with this charter revised in daylight, and with the change explained, never slipped into fine print.',
  },
  {
    title: 'We will never let money shape the truth.',
    body: 'No payment, partnership, sponsorship, or relationship, including our own consulting clients, can influence any organization’s score, visibility, ranking, or how it is described. The methodology is published; the same math runs for everyone.',
  },
  {
    title: 'We will never shame the organizations we describe.',
    body: 'Our job is context, not verdicts. We show evidence, label uncertainty, and treat a small or struggling organization with the same dignity as a thriving one. Where our data is thin, we say “we don’t know enough,” never “they failed.”',
  },
  {
    title: 'We will never hide our mistakes.',
    body: 'Every organization page carries a visible way to challenge what we say. Corrections happen promptly and are documented, not overwritten.',
  },
  {
    title: 'We will never lock you in.',
    body: 'You can export everything you have given us, and you can delete it, entirely and at any time. The public record remains public, because it was never ours, but what you entrusted to us leaves when you say so.',
  },
  {
    title: 'We will never weaken this charter quietly.',
    body: 'Changes to this document are logged, dated, explained, and announced. Silent dilution of any promise here is a violation of the platform’s founding commitments, and anyone, inside or outside the organization, is entitled to call it out.',
  },
]

export default function Charter() {
  usePageMeta(
    'The Daanaa Charter',
    'Ten promises Daanaa makes to the nonprofits and donors it serves, written down so anyone can hold us to them.'
  )

  return (
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy pt-nav">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-caption text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-caption text-muted-cream">Charter</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-10 md:gap-16">
            <div className="max-w-[720px]">
              <span className="font-body text-label font-medium tracking-[0.08em] text-soft-gold uppercase">Our Promises, In Writing</span>
              <h1 className="font-display italic text-warm-cream mt-3 leading-[1.05] tracking-[-0.01em]">
                The Daanaa Charter
              </h1>
              <p className="mt-5 font-body text-title-sm leading-[1.65] text-muted-cream">
                Ten things we will never do. Published because promises kept in
                private are just intentions &mdash; a promise published is a debt.
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

          <section className="mb-14">
            <div className="space-y-4 font-body text-lead text-cool-grey leading-[1.7]">
              <p>
                Daanaa exists to help people give well and to help nonprofit
                organizations, especially small ones, be known truthfully and
                supported practically. This charter is the list of things we
                will never do, written down so that anyone, at any time, can
                hold us to it.
              </p>
            </div>
          </section>

          {/* The ten promises */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em]">
              What Daanaa will never do
            </h2>
            <ol className="mt-8 space-y-10">
              {PROMISES.map((p, i) => (
                <li key={i} className="flex gap-5">
                  <span className="font-display italic text-soft-gold text-headline leading-none shrink-0 w-10 text-right">{i + 1}</span>
                  <div>
                    <h3 className="font-body text-title-sm font-semibold text-deep-navy leading-[1.4]">{p.title}</h3>
                    <p className="mt-2 font-body text-body-lg text-cool-grey leading-[1.7]">{p.body}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          <hr className="border-light-grey my-12" />

          {/* What holds this up */}
          <section className="mb-16">
            <h2 className="font-display italic text-deep-navy leading-[1.1] text-headline-lg md:text-display tracking-[-0.01em]">
              What holds this up
            </h2>
            <div className="mt-5 space-y-4 font-body text-lead text-cool-grey leading-[1.7]">
              <p>
                Daanaa operates under a Founding Stewardship Commitment, a
                governing constitution, and a data classification policy that
                separates, in code, what is public from what you have entrusted
                to us. Our operating company, EcoMargins Consulting LLC, does
                professional consulting under its own name; a structural
                firewall, audited quarterly and enforced at the code level,
                keeps that business from ever reaching into what Daanaa holds
                in trust. When Daanaa becomes its own legal entity, this
                charter transfers with it, unchanged.
              </p>
              <p>
                If you believe we have broken any promise on this page, write
                to <a href="mailto:hello@daanaa.org" className="text-deep-navy underline underline-offset-2 hover:text-navy-mid">hello@daanaa.org</a>.
                You will get an answer from a human, and if you are right, you
                will see the correction happen in public.
              </p>
              <p className="text-body text-cool-grey/80">
                Charter version 1.0, adopted 2026-07-13. Revisions are listed
                here with date, author, and reason. There are none yet. May it
                stay a short list. See also our{' '}
                <Link to="/about" className="text-deep-navy underline underline-offset-2 hover:text-navy-mid">About Daanaa</Link> page.
              </p>
            </div>
          </section>

        </div>
      </div>
    </div>
  )
}
