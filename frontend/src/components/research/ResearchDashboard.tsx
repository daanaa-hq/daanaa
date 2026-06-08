import { useEffect, useState } from 'react'
import {
  Treemap,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface ResearchDashboardProps {
  sessionToken: string
}

interface TreemapData {
  name: string
  value: number
  model?: string
  band?: string
  count?: number
}

export default function ResearchDashboard({
  sessionToken,
}: ResearchDashboardProps) {
  const [data, setData] = useState<TreemapData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/research/summary/revenue-bands', {
          headers: { 'X-Research-Session': sessionToken },
        })
        if (response.ok) {
          const result = await response.json()
          // Transform flat data into treemap structure
          const treemapData = result.data.map((item: any) => ({
            name: `${item.operating_model} - Band ${item.revenue_band_number}`,
            value: item.count,
            model: item.operating_model,
            band: item.revenue_band_number,
            count: item.count,
          }))
          setData(treemapData)
        }
      } catch (error) {
        console.error('Failed to load data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [sessionToken])

  const CustomTooltip = (props: any) => {
    if (props.active && props.payload && props.payload[0]) {
      const data = props.payload[0].payload
      return (
        <div className="bg-deep-navy text-warm-cream p-3 rounded shadow-lg text-sm">
          <p className="font-semibold">{data.model}</p>
          <p>Revenue Band: {data.band}</p>
          <p>{data.count?.toLocaleString()} organizations</p>
        </div>
      )
    }
    return null
  }

  const COLORS = [
    '#B8902F', '#D4B968', '#E8C896', '#8B7355', '#A0826D',
    '#B8936F', '#C9A876', '#7A6B5A', '#9E8B6F',
  ]

  const getColor = (model: string) => {
    const models = [
      'Direct_Delivery', 'Activity_Programming', 'Community_Human_Services',
      'Clinical_Reimbursement', 'Cause_Advocacy_Research', 'Intermediary_Public_Benefit',
      'Faith_Community', 'Emergency_Logistics', 'Membership_Mutual_Benefit',
    ]
    const index = models.indexOf(model)
    return COLORS[index] || '#B8902F'
  }

  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-6">
        Operating Models & Revenue Bands
      </h2>

      <p className="text-cool-grey mb-8 max-w-2xl">
        Hover over any section to see the operating model, revenue band, and organization count.
        Larger sections represent more organizations in that peer group.
      </p>

      {loading ? (
        <div className="h-96 flex items-center justify-center text-cool-grey">
          Loading...
        </div>
      ) : (
        <div className="bg-white rounded-lg p-6 border border-light-grey mb-8">
          <ResponsiveContainer width="100%" height={500}>
            <Treemap
              data={data}
              dataKey="value"
              stroke="#fff"
              fill="#8884d8"
              content={
                <g>
                  {data.map((entry, index) => (
                    <g key={`rect-${index}`}>
                      <rect
                        x={0}
                        y={0}
                        width={100}
                        height={100}
                        fill={getColor(entry.model || '')}
                        stroke="#fff"
                        strokeWidth={2}
                      />
                    </g>
                  ))}
                </g>
              }
            >
              <Tooltip content={<CustomTooltip />} />
            </Treemap>
          </ResponsiveContainer>
        </div>
      )}

      {/* Operating Models Legend */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[
          { name: 'Activity_Programming', desc: 'Schools, museums, theaters, sports leagues, YMCAs, libraries, and cultural venues.' },
          { name: 'Direct_Delivery', desc: 'Legal aid, employment training, housing providers, and social service agencies.' },
          { name: 'Community_Human_Services', desc: 'Youth development, family services, community improvement organizations.' },
          { name: 'Clinical_Reimbursement', desc: 'Hospitals, clinics, mental health centers, disease organizations, medical research.' },
          { name: 'Emergency_Logistics', desc: 'Food banks, food pantries, disaster relief, and public safety nonprofits.' },
          { name: 'Cause_Advocacy_Research', desc: 'Environmental, animal welfare, international development, civil rights, research.' },
          { name: 'Intermediary_Public_Benefit', desc: 'Community foundations, United Way affiliates, grantmaking bodies.' },
          { name: 'Faith_Community', desc: 'Congregations, parishes, religious ministries, faith-based organizations.' },
          { name: 'Membership_Mutual_Benefit', desc: 'Fraternal orders, mutual benefit societies, civic membership organizations.' },
        ].map((model, i) => (
          <div
            key={model.name}
            className="p-4 rounded-lg border-l-4 bg-white"
            style={{ borderLeftColor: COLORS[i] }}
          >
            <div className="flex items-center gap-2 mb-2">
              <div
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: COLORS[i] }}
              />
              <h4 className="font-semibold text-deep-navy text-sm">
                {model.name.replace(/_/g, ' ')}
              </h4>
            </div>
            <p className="text-xs text-cool-grey">{model.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
