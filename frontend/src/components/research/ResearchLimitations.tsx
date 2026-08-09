export default function ResearchLimitations() {
  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-6">
        Limitations & Future Directions
      </h2>

      <div className="prose prose-sm max-w-none text-cool-grey space-y-8">
        <div>
          <h3 className="text-xl font-semibold text-deep-navy mb-4">
            What Daanaa Doesn't Measure
          </h3>
          <p>
            Our methodology is intentionally narrow. We measure operating reserves and data
            completeness—not these important factors:
          </p>
          <ul className="list-disc pl-5 space-y-2 mt-3">
            <li>
              <strong>Impact:</strong> We cannot measure outcomes, beneficiary satisfaction,
              or social return. Only the organization itself knows its impact.
            </li>
            <li>
              <strong>Leadership quality:</strong> Board composition, staff retention, and
              founder vision are invisible to public data.
            </li>
            <li>
              <strong>Sustainability:</strong> Revenue volatility, funder concentration, and
              runway cannot be inferred from a single year's 990.
            </li>
            <li>
              <strong>Culture & values:</strong> Organizational health, diversity initiatives,
              and mission alignment are not captured in financial data.
            </li>
            <li>
              <strong>Emerging opportunities:</strong> New organizations and pivoting teams
              lack historical data, creating a bias toward established entities.
            </li>
          </ul>
        </div>

        <div className="bg-destructive/5 border border-destructive/20 rounded-lg p-6">
          <h4 className="font-semibold text-deep-navy mb-3">⚠️ Critical limitations</h4>
          <ul className="space-y-2 text-sm">
            <li>
              <strong>Data lag:</strong> Form 990 filings lag by 6-18 months. Real-time
              financial state may differ significantly from published records.
            </li>
            <li>
                <strong>Sampling bias:</strong> Organizations without recent filings are
                underrepresented in this analysis. A missing filing reflects the limits of
                our data coverage, not evidence that an organization is inactive or
                struggling — smaller and newer nonprofits routinely file less often.
            </li>
            <li>
              <strong>Accounting variation:</strong> Nonprofits apply GAAP differently.
              Revenue recognition, depreciation, and allocation methods vary widely.
            </li>
            <li>
              <strong>Geographic blindness:</strong> Our funding model and sector categories reflect
              national patterns, not local context. A human services org in rural
              Montana may operate nothing like its urban peer.
            </li>
          </ul>
        </div>

        <div>
          <h3 className="text-xl font-semibold text-deep-navy mb-4">Roadmap</h3>
          <p>
            Over the next 2-3 years, we plan to extend Daanaa's capabilities:
          </p>
          <ul className="list-disc pl-5 space-y-2 mt-3">
            <li>
              <strong>Outcome research partnerships:</strong> Collaborate with academic
              research teams to link nonprofit outcomes to financial patterns.
            </li>
            <li>
              <strong>Real-time data integration:</strong> Incorporate 10-Q filings, grant
              registries, and nonprofit-submitted updates.
            </li>
            <li>
              <strong>Sector-specific deep dives:</strong> Build industry-specific peer groups
              (e.g., pediatric health, environmental conservation) with custom metrics.
            </li>
            <li>
              <strong>Community feedback mechanism:</strong> Enable organizations to submit
              context, dispute findings, and update contact information in real time.
            </li>
            <li>
              <strong>Sustainability scoring:</strong> Predict financial resilience using
              machine learning on historical 990 patterns (with human audit and transparency).
            </li>
          </ul>
        </div>

        <div>
          <h3 className="text-xl font-semibold text-deep-navy mb-4">
            Principles for Future Expansion
          </h3>
          <p>
            Any new feature or data source must meet these criteria:
          </p>
          <div className="space-y-3 mt-3">
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">Explainability</p>
              <p className="text-sm">
                Any metric must be traceable to public records or simple, auditable rules.
              </p>
            </div>
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">Privacy</p>
              <p className="text-sm">
                Individuals' identities and giving patterns must never be exposed or inferred.
              </p>
            </div>
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">Equity</p>
              <p className="text-sm">
                Small organizations must be treated with equal dignity. No feature should bias
                discovery toward large or wealthy entities.
              </p>
            </div>
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">Humility</p>
              <p className="text-sm">
                We will publicly document what we get wrong and correct errors immediately.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-soft-gold/10 rounded-lg p-6">
          <p className="text-sm font-semibold text-deep-navy mb-2">
            👋 Closing thought
          </p>
          <p className="text-sm">
            Daanaa is a transparency tool, not a replacement for human judgment. We encourage
            you to use this data as a starting point, then dig deeper: talk to the
            organization, visit the work, meet the team. Data informs; people decide.
          </p>
        </div>
      </div>
    </div>
  )
}
