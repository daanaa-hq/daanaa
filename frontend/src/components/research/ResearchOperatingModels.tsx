import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { loadResearchSnapshot } from '../../data/researchSnapshot'

interface ResearchOperatingModelsProps {
  sessionToken: string
  metadata: any
}

interface ModelData {
  model: string
  data: Array<{
    revenue_band_number: number
    count: number
  }>
}

// 9 operating models with colors, descriptions, and revenue band thresholds
const OPERATING_MODELS: Record<string, {color: string; desc: string; ntee: string; orgs: number; bands: number[]}> = {
  'Activity_Programming': {
    color: '#D4B968',
    desc: 'Schools, museums, theaters, sports leagues, YMCAs, libraries, and cultural venues.',
    ntee: 'NTEE: A · B · N',
    orgs: 120508,
    bands: [27249, 52819, 76834, 110281, 165472, 284527, 828352]
  },
  'Direct_Delivery': {
    color: '#B8902F',
    desc: 'Legal aid, employment training, housing providers, and social service agencies.',
    ntee: 'NTEE: I · J · L',
    orgs: 34235,
    bands: [46941, 83998, 134978, 228936, 416113, 903911, 2255466]
  },
  'Community_Human_Services': {
    color: '#E8C896',
    desc: 'Youth development, family services, community improvement organizations.',
    ntee: 'NTEE: O · P · S',
    orgs: 78812,
    bands: [31190, 61908, 100883, 162333, 271640, 514120, 1382545]
  },
  'Clinical_Reimbursement': {
    color: '#8B7355',
    desc: 'Hospitals, clinics, mental health centers, disease organizations, medical research.',
    ntee: 'NTEE: E · F · G · H',
    orgs: 37932,
    bands: [57574, 137822, 356219, 1859828]
  },
  'Emergency_Logistics': {
    color: '#7A6B5A',
    desc: 'Food banks, food pantries, disaster relief, and public safety nonprofits.',
    ntee: 'NTEE: K · M',
    orgs: 15828,
    bands: [60297, 106948, 187162, 459258]
  },
  'Cause_Advocacy_Research': {
    color: '#A0826D',
    desc: 'Environmental, animal welfare, international development, civil rights, research.',
    ntee: 'NTEE: C · D · Q · R · U · V',
    orgs: 28745,
    bands: [42742, 91647, 173159, 460190]
  },
  'Intermediary_Public_Benefit': {
    color: '#B8936F',
    desc: 'Community foundations, United Way affiliates, grantmaking bodies.',
    ntee: 'NTEE: T · W',
    orgs: 25822,
    bands: [50310, 117090, 278734, 1335713]
  },
  'Faith_Community': {
    color: '#C9A876',
    desc: 'Congregations, parishes, religious ministries, faith-based organizations.',
    ntee: 'NTEE: X',
    orgs: 16691,
    bands: [47539, 92415, 157757, 373778]
  },
  'Membership_Mutual_Benefit': {
    color: '#9E8B6F',
    desc: 'Fraternal orders, mutual benefit societies, civic membership organizations.',
    ntee: 'NTEE: Y · Z',
    orgs: 9785,
    bands: [45548, 100165, 258066, 1540726]
  },
}

function formatRevenue(num: number): string {
  if (num >= 1000000) return `$${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `$${(num / 1000).toFixed(0)}K`
  return `$${num}`
}

const COLORS = Object.values(OPERATING_MODELS).map(m => m.color)

export default function ResearchOperatingModels({
  sessionToken,
  metadata,
}: ResearchOperatingModelsProps) {
  const [modelData, setModelData] = useState<Record<string, any[]>>({})
  const [selectedModel, setSelectedModel] = useState<string>('Activity_Programming')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadResearchSnapshot()
      .then((snap) => {
        // Group data by operating model with revenue range labels
        const grouped: Record<string, any[]> = {}
        snap.revenue_bands.forEach((item) => {
          if (!grouped[item.operating_model]) {
            grouped[item.operating_model] = []
          }
          const bandThresholds = OPERATING_MODELS[item.operating_model]?.bands || []
          const bandIndex = item.revenue_band_number
          const label = bandIndex === 0
            ? `Under ${formatRevenue(bandThresholds[0])}`
            : bandIndex < bandThresholds.length
            ? `${formatRevenue(bandThresholds[bandIndex - 1])} – ${formatRevenue(bandThresholds[bandIndex])}`
            : `Over ${formatRevenue(bandThresholds[bandThresholds.length - 1])}`

          grouped[item.operating_model].push({
            band: item.revenue_band_number,
            count: item.count,
            name: label,
            revenue_range: label,
          })
        })
        setModelData(grouped)
      })
      .catch((error) => console.error('Failed to load data:', error))
      .finally(() => setLoading(false))
  }, [])

  const CustomTooltip = (props: any) => {
    if (props.active && props.payload && props.payload[0]) {
      const item = props.payload[0].payload
      return (
        <div className="bg-deep-navy text-warm-cream p-3 rounded shadow-lg text-sm border border-soft-gold">
          <p className="text-xs text-cool-grey">Revenue Band {item.band}</p>
          <p className="font-bold text-soft-gold mt-1">{item.count?.toLocaleString()} orgs</p>
        </div>
      )
    }
    return null
  }

  const selectedData = modelData[selectedModel] || []
  const selectedColor = OPERATING_MODELS[selectedModel]?.color || '#B8902F'
  const selectedConfig = OPERATING_MODELS[selectedModel]

  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-6">
        Operating Models & Revenue Bands (v4 Reference)
      </h2>

      <div className="bg-warm-cream/30 border-l-4 border-soft-gold p-4 mb-8 rounded-r">
        <p className="text-sm text-deep-navy font-semibold mb-2">Reference: V4 Segmentation</p>
        <p className="text-sm text-slate">
          This section documents the nine operating models from our v4 system. We have transitioned to a simpler
          three-archetype model (v5) for financial context scoring. Operating models remain useful for understanding
          mission-driven segmentation across the nonprofit sector.
        </p>
      </div>

      <p className="text-cool-grey mb-8 max-w-2xl">
        Click any operating model to see how organizations are distributed across revenue bands within that group.
      </p>

      {loading ? (
        <div className="h-96 flex items-center justify-center text-cool-grey">
          Loading...
        </div>
      ) : (
        <>
          {/* Model Tabs */}
          <div className="flex flex-wrap gap-2 mb-8 pb-4 border-b border-light-grey">
            {Object.entries(OPERATING_MODELS).map(([model, config]) => (
              <button
                key={model}
                onClick={() => setSelectedModel(model)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedModel === model
                    ? 'text-white'
                    : 'bg-warm-cream text-cool-grey hover:bg-light-grey'
                }`}
                style={{
                  backgroundColor: selectedModel === model ? config.color : undefined,
                }}
              >
                {model.replace(/_/g, ' ')}
              </button>
            ))}
          </div>

          {/* Selected Model Details */}
          {selectedConfig && (
            <div className="bg-white rounded-lg p-6 border border-light-grey mb-8">
              <div className="mb-6">
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: selectedColor }}
                  />
                  <h3 className="text-xl font-semibold text-deep-navy">
                    {selectedModel.replace(/_/g, ' ')}
                  </h3>
                </div>
                <p className="text-cool-grey text-sm mb-2">{selectedConfig.desc}</p>
                <div className="flex gap-6 text-xs text-cool-grey">
                  <span>{selectedConfig.ntee}</span>
                  <span>{selectedConfig.orgs.toLocaleString()} organizations total</span>
                </div>
              </div>

              {/* Revenue Band Chart */}
              <div className="bg-deep-navy/[0.02] rounded-lg p-6">
                <p className="text-xs font-semibold text-cool-grey uppercase tracking-wide mb-4">
                  Distribution across revenue bands
                </p>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={selectedData}>
                    <XAxis
                      dataKey="revenue_range"
                      label={{ value: 'Revenue Range', position: 'insideBottomRight', offset: -5 }}
                      tick={{ fontSize: 11 }}
                      angle={-45}
                      textAnchor="end"
                      height={100}
                    />
                    <YAxis label={{ value: 'Organizations', angle: -90, position: 'insideLeft' }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="count" fill={selectedColor} radius={[8, 8, 0, 0]}>
                      {selectedData.map((entry: any, index: number) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={selectedColor}
                          style={{ opacity: 0.8 + (index % 2) * 0.15 }}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* All Operating Models Summary */}
          <div className="mt-12">
            <h3 className="text-xl font-semibold text-deep-navy mb-6">All Operating Models</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(OPERATING_MODELS).map(([model, config]) => (
                <div
                  key={model}
                  className="p-4 rounded-lg border-l-4 bg-white cursor-pointer transition-shadow hover:shadow-md"
                  onClick={() => setSelectedModel(model)}
                  style={{ borderLeftColor: config.color }}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: config.color }}
                      />
                      <h4 className="font-semibold text-deep-navy text-sm">
                        {model.replace(/_/g, ' ')}
                      </h4>
                    </div>
                    <div className="text-xs font-bold text-soft-gold whitespace-nowrap">
                      {config.orgs.toLocaleString()}
                    </div>
                  </div>
                  <p className="text-xs text-cool-grey mb-2">{config.desc}</p>
                  <p className="text-xs text-cool-grey font-mono">{config.ntee}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
