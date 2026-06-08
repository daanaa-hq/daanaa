export default function ResearchAbout() {
  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-6">About Daanaa</h2>

      <div className="prose prose-sm max-w-none text-cool-grey space-y-6">
        <div>
          <h3 className="text-xl font-semibold text-deep-navy mb-3">Our Mission</h3>
          <p>
            Daanaa means "wise" in Somali. We help you discover the invisible 97%—the
            thousands of effective nonprofits doing world-changing work in quiet corners,
            far from major donors and foundation awareness.
          </p>
        </div>

        <div>
          <h3 className="text-xl font-semibold text-deep-navy mb-3">Our Approach</h3>
          <p>
            We index public data from the IRS, ProPublica, and verified nonprofit disclosures.
            We don't rank "better" or "worse." We provide peer financial context—how an
            organization's revenue and reserve strength compares to similar nonprofits in
            its field.
          </p>
        </div>

        <div>
          <h3 className="text-xl font-semibold text-deep-navy mb-3">Stewardship Principles</h3>
          <ul className="list-disc pl-5 space-y-2">
            <li>Trust signals reflect real, evidence-based data only</li>
            <li>Donor privacy is non-negotiable—no tracking, no social pressure</li>
            <li>Small organizations have equal dignity to large ones</li>
            <li>All findings must be explainable and traceable</li>
            <li>We never handle funds—we hand off to organizations' own processors</li>
          </ul>
        </div>

        <div className="bg-soft-gold/10 rounded-lg p-4 mt-6">
          <p className="text-sm">
            <strong>Privacy commitment:</strong> Daanaa uses no accounts, no tracking, and
            stores your giving record only on your device. We believe in discovery, not
            exposure.
          </p>
        </div>
      </div>
    </div>
  )
}
