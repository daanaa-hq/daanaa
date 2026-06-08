import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { loadResearchSnapshot } from '../../data/researchSnapshot'

interface ResearchSpendingProps {
  sessionToken: string
  metadata: any
}

const MODEL_COLORS: Record<string, string> = {
  'Activity_Programming': '#D4B968',
  'Direct_Delivery': '#B8902F',
  'Community_Human_Services': '#E8C896',
  'Clinical_Reimbursement': '#8B7355',
  'Emergency_Logistics': '#7A6B5A',
  'Cause_Advocacy_Research': '#A0826D',
  'Intermediary_Public_Benefit': '#B8936F',
  'Faith_Community': '#C9A876',
  'Membership_Mutual_Benefit': '#9E8B6F',
}

export default function ResearchSpending({
  sessionToken,
  metadata,
}: ResearchSpendingProps) {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadResearchSnapshot()
      .then((snap) => {
        setData(
          snap.spending.map((item) => ({
            name: item.operating_model.replace(/_/g, ' '),
            model: item.operating_model,
            median: item.median_program_spend || 0,
            p25: item.p25_program_spend || 0,
            p75: item.p75_program_spend || 0,
            count: item.count,
          }))
        )
      })
      .catch((error) => console.error('Failed to load spending data:', error))
      .finally(() => setLoading(false))
  }, [])

  const CustomTooltip = (props: any) => {
    if (props.active && props.payload && props.payload[0]) {
      const item = props.payload[0].payload
      return (
        <div className="bg-deep-navy text-warm-cream p-3 rounded shadow-lg text-sm border border-soft-gold">
          <p className="font-semibold">{item.name}</p>
          <p className="text-xs text-cool-grey mt-1">Median spending: <span className="text-soft-gold font-bold">{item.median.toFixed(1)}%</span></p>
          <p className="text-xs text-cool-grey">Middle 50%: {item.p25.toFixed(1)}% – {item.p75.toFixed(1)}%</p>
          <p className="text-xs text-cool-grey mt-1">{item.count.toLocaleString()} orgs</p>
        </div>
      )
    }
    return null
  }

  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-6">
        Program Spending by Operating Model
      </h2>

      <p className="text-cool-grey mb-8 max-w-2xl">
        Median percentage of revenue spent directly on programs (vs. admin/overhead) for each operating model.
        The middle-50% range shows how organizations within each model spread out around that median.
      </p>

      {loading ? (
        <div className="h-96 flex items-center justify-center text-cool-grey">
          Loading...
        </div>
      ) : (
        <div className="bg-white rounded-lg p-6 border border-light-grey mb-8">
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={data}
              margin={{ top: 20, right: 30, left: 0, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={100}
                tick={{ fontSize: 12 }}
              />
              <YAxis
                label={{ value: 'Program Spending %', angle: -90, position: 'insideLeft' }}
                domain={[0, 100]}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar
                dataKey="median"
                name="Median Program Spending"
                fill="#D4B968"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.map((item) => (
          <div
            key={item.model}
            className="p-4 rounded-lg border-l-4 bg-white"
            style={{ borderLeftColor: MODEL_COLORS[item.model] }}
          >
            <div className="flex items-center gap-2 mb-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: MODEL_COLORS[item.model] }}
              />
              <h4 className="font-semibold text-deep-navy text-sm">{item.name}</h4>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-cool-grey">
                <span className="font-semibold text-soft-gold">{item.median.toFixed(1)}%</span> median spending
              </p>
              <p className="text-xs text-cool-grey/70">
                Middle 50%: {item.p25.toFixed(1)}% – {item.p75.toFixed(1)}%
              </p>
              <p className="text-xs text-cool-grey/70">
                {item.count.toLocaleString()} organizations
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
