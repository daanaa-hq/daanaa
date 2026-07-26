import { Link } from 'react-router-dom'
import type { ApiOrganization } from '../data/api'
import { getNteeLabel } from '../data/ntee'
import { CardPattern } from './ui/CardPattern'

interface CohortContextProps {
  org: ApiOrganization
}

// Shown ONLY for orgs we have no 990 financials for. It does not describe this
// organization. It describes the typical financial shape of its cause-cohort,
// drawn from organizations we do have data for. The wording keeps that wall
// explicit (Stewardship P3: no false precision; P4: small orgs still get
// useful, honest context instead of a blank section).
export default function CohortContext({ org }: CohortContextProps) {
  const cohort = org.cohort_context
  if (!cohort) return null

  const causeLabel = getNteeLabel(cohort.ntee_code)
  const median = Math.round(cohort.median_reserve)

  return (
    <CardPattern variant="subtle">
      <div className="space-y-4">
        <div>
          <h3 className="font-body text-xs tracking-widest uppercase font-semibold text-cool-grey">
            Financial Context
          </h3>
          <p className="font-body text-body-lg text-deep-navy mt-2 leading-relaxed">
            We do not have public financial filings for this organization yet, so
            we cannot show its own numbers.
          </p>
        </div>

        <CardPattern variant="nested" className="space-y-2">
          <p className="font-body text-small tracking-wide uppercase text-cool-grey">
            About {causeLabel.toLowerCase().startsWith('this') ? causeLabel : `its work in ${causeLabel}`}
          </p>
          <p className="font-body text-body-lg text-deep-navy leading-relaxed">
            Among the {cohort.n.toLocaleString()} organizations in this area we do
            have data for, the typical one keeps about{' '}
            <span className="font-semibold">{median} months</span> of operating
            costs in reserve.
          </p>
          <p className="font-body text-small text-cool-grey">
            This is background on the cause area, not a measure of this organization.
          </p>
        </CardPattern>

        <div className="pt-1">
          <p className="font-body text-body text-deep-navy">
            Run this organization?{' '}
            <Link
              to={`/for-nonprofits?ein=${org.EIN}`}
              className="font-semibold underline underline-offset-2 hover:opacity-80"
            >
              Claim your page
            </Link>{' '}
            to show its real numbers.
          </p>
        </div>
      </div>
    </CardPattern>
  )
}
