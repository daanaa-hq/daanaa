import { ApiFinancialRecord } from '../data/api'
import { formatCurrency } from '../data/organizations'

/**
 * FinancialHistoryTable — multi-year Form 990 filing history.
 *
 * Extracted from OrganizationDetail.tsx (2026-08-18) per a design ask: org
 * page sections should be modular and adapt to window/device size rather
 * than assuming a fixed desktop layout. The previous inline table used
 * `overflow-x-auto` on a 6-column table — technically "responsive" (it
 * scrolls) but not easy to read on a narrow screen, since the whole point
 * of a horizontal-scroll table is that you can't see all the data at once.
 *
 * Below the `md` breakpoint (768px) this renders each year as a stacked
 * card (label/value pairs) instead. Above it, the original table layout.
 * Self-contained: takes only `financials` + `showAll` as props, makes no
 * assumption about parent width or sibling layout.
 */
export default function FinancialHistoryTable({
  financials,
  showAll,
}: {
  financials: ApiFinancialRecord[]
  showAll: boolean
}) {
  if (!showAll || financials.length === 0) return null

  const rows = [...financials].reverse()

  return (
    <div className="mt-4">
      {/* Mobile: stacked cards, one per year, no horizontal scroll */}
      <div className="md:hidden space-y-3">
        {rows.map((f) => (
          <div key={f.tax_prd_yr} className="rounded-lg border border-light-grey p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="font-body text-small font-semibold text-deep-navy">{f.tax_prd_yr}</span>
              {f.pdf_url ? (
                <a
                  href={f.pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 font-body text-label text-link-gold hover:text-deep-gold transition-colors"
                >
                  PDF
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                </a>
              ) : null}
            </div>
            <div className="grid grid-cols-2 gap-y-2 gap-x-4">
              <div>
                <div className="font-body text-label tracking-[0.06em] text-cool-grey uppercase">Revenue</div>
                <div className="font-body text-small text-deep-navy">{f.totrevenue != null ? formatCurrency(f.totrevenue) : '--'}</div>
              </div>
              <div>
                <div className="font-body text-label tracking-[0.06em] text-cool-grey uppercase">Expenses</div>
                <div className="font-body text-small text-cool-grey">{f.totfuncexpns != null ? formatCurrency(f.totfuncexpns) : '--'}</div>
              </div>
              <div>
                <div className="font-body text-label tracking-[0.06em] text-cool-grey uppercase">Net Assets</div>
                <div className={`font-body text-small ${(f.totnetassetend ?? 0) < 0 ? 'text-amber-600' : 'text-cool-grey'}`}>
                  {f.totnetassetend != null ? formatCurrency(f.totnetassetend) : '--'}
                </div>
              </div>
              <div>
                <div className="font-body text-label tracking-[0.06em] text-cool-grey uppercase">Contributions</div>
                <div className="font-body text-small text-cool-grey">{f.totcntrbgfts != null ? formatCurrency(f.totcntrbgfts) : '--'}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Tablet/desktop: full table, no scroll needed at these widths */}
      <div className="hidden md:block overflow-x-auto max-w-[820px]">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-light-grey">
              <th className="font-body text-label tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Year</th>
              <th className="font-body text-label tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Revenue</th>
              <th className="font-body text-label tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Expenses</th>
              <th className="font-body text-label tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Net Assets</th>
              <th className="font-body text-label tracking-[0.06em] text-cool-grey uppercase pb-2 pr-4">Contributions</th>
              <th className="font-body text-label tracking-[0.06em] text-cool-grey uppercase pb-2">Report</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((f) => (
              <tr key={f.tax_prd_yr} className="border-b border-light-grey/50 hover:bg-white/50 transition-colors">
                <td className="font-body text-small font-medium text-deep-navy py-3 pr-4">{f.tax_prd_yr}</td>
                <td className="font-body text-small text-deep-navy py-3 pr-4">{f.totrevenue != null ? formatCurrency(f.totrevenue) : '--'}</td>
                <td className="font-body text-small text-cool-grey py-3 pr-4">{f.totfuncexpns != null ? formatCurrency(f.totfuncexpns) : '--'}</td>
                <td className={`font-body text-small py-3 pr-4 ${(f.totnetassetend ?? 0) < 0 ? 'text-amber-600' : 'text-cool-grey'}`}>
                  {f.totnetassetend != null ? formatCurrency(f.totnetassetend) : '--'}
                </td>
                <td className="font-body text-small text-cool-grey py-3 pr-4">{f.totcntrbgfts != null ? formatCurrency(f.totcntrbgfts) : '--'}</td>
                <td className="py-3">
                  {f.pdf_url ? (
                    <a
                      href={f.pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 font-body text-label text-link-gold hover:text-deep-gold transition-colors"
                    >
                      PDF
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                    </a>
                  ) : '--'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-4 font-body text-caption text-cool-grey">
        Source: IRS Form 990 filings, via GuideStar/ProPublica indexes and direct IRS data · Government annual financial reports
      </p>
    </div>
  )
}
