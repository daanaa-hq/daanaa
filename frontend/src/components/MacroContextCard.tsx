import { MacroContext } from '../data/api';

interface MacroContextCardProps {
  context: MacroContext | null;
  archetype: string | null;
  filingYear: number | null;
}

export default function MacroContextCard({ context, archetype, filingYear }: MacroContextCardProps) {
  if (!context) {
    return null;
  }

  const archetypeLabel = archetype === 'Donation-Funded' ? 'donation-funded'
    : archetype === 'Fee-for-Service' ? 'fee-for-service'
    : archetype === 'Endowment-Funded' ? 'endowment-funded'
    : 'nonprofit';

  // Build narrative based on archetype
  let narrative = '';
  if (archetype === 'Donation-Funded') {
    narrative = `In ${filingYear}, unemployment at ${context.unemployment_rate?.toFixed(1)}% and inflation at ~${context.cpi?.toFixed(1)}% affected donor capacity and operational costs. Labor market conditions and cost pressures are key factors for donation-funded orgs.`;
  } else if (archetype === 'Fee-for-Service') {
    narrative = `In ${filingYear}, GDP growth of ${context.gdp_growth?.toFixed(1)}% and unemployment at ${context.unemployment_rate?.toFixed(1)}% shaped service demand and ability to pay. Economic growth and employment affect the viability of fee-for-service models.`;
  } else if (archetype === 'Endowment-Funded') {
    narrative = `In ${filingYear}, Federal funds rate at ${context.interest_rate_federal?.toFixed(2)}% and broader market conditions affected investment returns. Interest rates and market performance are key drivers for endowment-funded operations.`;
  } else {
    narrative = `In ${filingYear}, macro economic indicators (unemployment: ${context.unemployment_rate?.toFixed(1)}%, inflation: ${context.cpi?.toFixed(1)}%) provide context for nonprofit operations.`;
  }

  return (
    <div className="mt-6 pt-6 border-t border-navy-light/20">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">📊</span>
        <h3 className="font-semibold text-cool-grey">Economic Context</h3>
      </div>

      <p className="text-body text-cool-grey mb-4">
        {narrative}
      </p>

      <div className="grid grid-cols-2 gap-3 text-sm">
        {context.unemployment_rate != null && (
          <div className="bg-navy-mid/5 px-3 py-2 rounded">
            <div className="text-cool-grey/70">Unemployment Rate</div>
            <div className="font-semibold text-cool-grey">{context.unemployment_rate.toFixed(1)}%</div>
          </div>
        )}

        {context.cpi != null && (
          <div className="bg-navy-mid/5 px-3 py-2 rounded">
            <div className="text-cool-grey/70">CPI (Inflation)</div>
            <div className="font-semibold text-cool-grey">{context.cpi.toFixed(1)}%</div>
          </div>
        )}

        {context.gdp_growth != null && (
          <div className="bg-navy-mid/5 px-3 py-2 rounded">
            <div className="text-cool-grey/70">GDP Growth</div>
            <div className="font-semibold text-cool-grey">{context.gdp_growth.toFixed(1)}%</div>
          </div>
        )}

        {context.interest_rate_federal != null && (
          <div className="bg-navy-mid/5 px-3 py-2 rounded">
            <div className="text-cool-grey/70">Fed Funds Rate</div>
            <div className="font-semibold text-cool-grey">{context.interest_rate_federal.toFixed(2)}%</div>
          </div>
        )}
      </div>

      <div className="mt-3 text-xs text-cool-grey/60 flex items-center gap-1">
        <span>📌</span>
        <span>Source: Federal Reserve (FRED) · {filingYear} tax year</span>
      </div>
    </div>
  );
}
