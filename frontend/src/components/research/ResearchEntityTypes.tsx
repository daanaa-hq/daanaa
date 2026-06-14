import { useEffect, useState } from 'react'
import { loadResearchSnapshot } from '../../data/researchSnapshot'

interface ResearchEntityTypesProps {
  sessionToken: string
  metadata: any
}

type EntityTypes = NonNullable<
  Awaited<ReturnType<typeof loadResearchSnapshot>>['entity_types']
>

const fmt = (n: number) => n.toLocaleString()

export default function ResearchEntityTypes(_props: ResearchEntityTypesProps) {
  const [data, setData] = useState<EntityTypes | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadResearchSnapshot()
      .then((snap) => setData(snap.entity_types ?? null))
      .catch((error) => console.error('Failed to load entity-type data:', error))
      .finally(() => setLoading(false))
  }, [])

  const rows = data
    ? [
        {
          key: 'public_charity',
          label: 'Public charities',
          pct: data.pct_public_charity,
          count: data.public_charity,
          color: '#B8902F',
          blurb:
            'Publicly supported, operating organizations: food banks, clinics, schools, shelters. They run programs directly and rely on donations from many sources.',
        },
        {
          key: 'private_foundation',
          label: 'Private foundations',
          pct: data.pct_private_foundation,
          count: data.private_foundation,
          color: '#8B7355',
          blurb:
            'Endowment-funded grantmakers, usually started by one donor or family. They fund other organizations rather than take public donations, and must pay out a share of their assets each year.',
        },
        {
          key: 'unclassified',
          label: 'Not yet classified',
          pct: data.pct_unclassified,
          count: data.unclassified,
          color: '#C9BBA3',
          blurb:
            'Organizations whose IRS foundation determination is not on the public record we hold. They are still recognized 501(c)(3)s; we simply do not assert a sub-type we cannot verify.',
        },
      ]
    : []

  return (
    <div>
      <h1 className="text-4xl font-display text-deep-navy mb-4">
        Organization Types
      </h1>
      <p className="text-lg text-cool-grey mb-6 max-w-2xl">
        "Nonprofit," "charity," and "foundation" are often used interchangeably, but
        they are not the same thing. Every organization in our directory is a
        tax-deductible 501(c)(3), and within that the IRS classifies each as either a
        public charity or a private foundation. The distinction matters when you give.
      </p>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-5 mb-8 max-w-2xl">
        <p className="text-sm text-deep-navy leading-relaxed">
          A <strong>public charity</strong> is a publicly supported organization that
          runs programs directly. A <strong>private foundation</strong> is usually an
          endowment that funds other organizations through grants rather than taking
          public donations. Both are tax-deductible, but giving to an operating charity
          and giving to a grantmaking foundation are different acts.
        </p>
      </div>

      {loading && <p className="text-sm text-cool-grey">Loading…</p>}

      {!loading && !data && (
        <p className="text-sm text-cool-grey">Composition data is not available right now.</p>
      )}

      {data && (
        <div className="max-w-2xl">
          {/* Composition bar */}
          <div className="flex h-3 w-full overflow-hidden rounded-full mb-6">
            {rows.map((r) => (
              <div
                key={r.key}
                style={{ width: `${r.pct}%`, backgroundColor: r.color }}
                title={`${r.label}: ${r.pct}%`}
              />
            ))}
          </div>

          <div className="space-y-5">
            {rows.map((r) => (
              <div key={r.key} className="flex gap-4">
                <div className="shrink-0 w-1.5 rounded-full" style={{ backgroundColor: r.color }} />
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="font-display text-2xl text-deep-navy">{r.pct}%</span>
                    <span className="text-sm font-medium text-deep-navy">{r.label}</span>
                    <span className="text-xs text-cool-grey">({fmt(r.count)})</span>
                  </div>
                  <p className="text-sm text-slate mt-1 leading-relaxed">{r.blurb}</p>
                </div>
              </div>
            ))}
          </div>

          <p className="mt-8 text-xs text-cool-grey leading-relaxed max-w-2xl">
            Source: IRS Business Master File foundation code, joined to the{' '}
            {fmt(data.total)} active, tax-deductible 501(c)(3) organizations in our
            index. Codes 02–04 are private foundations; 10–18 are public charities
            (509(a)(1)–(4)). Where the IRS determination is not on record, we leave the
            organization unclassified rather than guess.
          </p>
        </div>
      )}
    </div>
  )
}
