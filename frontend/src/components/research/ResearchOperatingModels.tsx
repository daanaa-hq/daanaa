import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

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

// 9 operating models with colors and descriptions
const OPERATING_MODELS: Record<string, {color: string; desc: string; ntee: string; orgs: number}> = {
  'Activity_Programming': {
    color: '#D4B968',
    desc: 'Schools, museums, theaters, sports leagues, YMCAs, libraries, and cultural venues.',
    ntee: 'NTEE: A · B · N',
    orgs: 120508
  },
  'Direct_Delivery': {
    color: '#B8902F',
    desc: 'Legal aid, employment training, housing providers, and social service agencies.',
    ntee: 'NTEE: I · J · L',
    orgs: 34235
  },
  'Community_Human_Services': {
    color: '#E8C896',
    desc: 'Youth development, family services, community improvement organizations.',
    ntee: 'NTEE: O · P · S',
    orgs: 78812
  },
  'Clinical_Reimbursement': {
    color: '#8B7355',
    desc: 'Hospitals, clinics, mental health centers, disease organizations, medical research.',
    ntee: 'NTEE: E · F · G · H',
    orgs: 37932
  },
  'Emergency_Logistics': {
    color: '#7A6B5A',
    desc: 'Food banks, food pantries, disaster relief, and public safety nonprofits.',
    ntee: 'NTEE: K · M',
    orgs: 15828
  },
  'Cause_Advocacy_Research': {
    color: '#A0826D',
    desc: 'Environmental, animal welfare, international development, civil rights, research.',
    ntee: 'NTEE: C · D · Q · R · U · V',
    orgs: 28745
  },
  'Intermediary_Public_Benefit': {
    color: '#B8936F',
    desc: 'Community foundations, United Way affiliates, grantmaking bodies.',
    ntee: 'NTEE: T · W',
    orgs: 25822
  },
  'Faith_Community': {
    color: '#C9A876',
    desc: 'Congregations, parishes, religious ministries, faith-based organizations.',
    ntee: 'NTEE: X',
    orgs: 16691
  },
  'Membership_Mutual_Benefit': {
    color: '#9E8B6F',
    desc: 'Fraternal orders, mutual benefit societies, civic membership organizations.',
    ntee: 'NTEE: Y · Z',
    orgs: 9785
  },
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
    const fetchData = async () => {
      try {
        const response = await fetch('/api/research/summary/revenue-bands', {
          headers: { 'X-Research-Session': sessionToken },
        })
        if (response.ok) {
          const result = await response.json()
          // Group data by operating model
          const grouped: Record<string, any[]> = {}
          result.data.forEach((item: any) => {
            if (!grouped[item.operating_model]) {
              grouped[item.operating_model] = []
            }
            grouped[item.operating_model].push({
              band: item.revenue_band_number,
              count: item.count,
              name: `Band ${item.revenue_band_number}`,
            })
          })
          setModelData(grouped)
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
        Operating Models & Revenue Bands
      </h2>

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
                <div className="flex gap-6 text-xs text-cool-grey/70">
                  <span>{selectedConfig.ntee}</span>
                  <span>{selectedConfig.orgs.toLocaleString()} organizations total</span>
                </div>
              </div>

              {/* Revenue Band Chart */}
              <div className="bg-deep-navy/[0.02] rounded-lg p-6">
                <p className="text-xs font-semibold text-cool-grey/60 uppercase tracking-wide mb-4">
                  Distribution across revenue bands
                </p>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={selectedData}>
                    <XAxis
                      dataKey="band"
                      label={{ value: 'Revenue Band', position: 'insideBottomRight', offset: -5 }}
                      tick={{ fontSize: 12 }}
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
        </>
      )}
    </div>
  )
}
