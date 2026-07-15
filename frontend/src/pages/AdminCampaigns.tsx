import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'

interface Campaign {
  id: string
  title: string
  carousel_type: string
  status: 'draft' | 'pending_approval' | 'approved' | 'scheduled' | 'posted'
  created_at: string
  approved_at?: string
  scheduled_for?: string
  posted_at?: string
}

interface Analytics {
  impressions?: number
  likes?: number
  comments?: number
  shares?: number
  clicks?: number
}

export function AdminCampaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null)
  const [analytics, setAnalytics] = useState<Record<string, Analytics>>({})
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('draft')

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const fetchCampaigns = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/campaigns/batch/list?status=${activeTab}`)
      const data = await res.json()
      setCampaigns(data.campaigns)
    } catch (error) {
      console.error('Failed to fetch campaigns:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchAnalytics = async (campaignId: string) => {
    try {
      const res = await fetch(`/api/campaigns/${campaignId}/analytics`)
      const data = await res.json()
      setAnalytics((prev) => ({
        ...prev,
        [campaignId]: data.metrics,
      }))
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
    }
  }

  const handleSubmitForApproval = async (campaignId: string) => {
    try {
      await fetch(`/api/campaigns/${campaignId}/submit-for-approval`, {
        method: 'POST',
      })
      fetchCampaigns()
    } catch (error) {
      console.error('Failed to submit for approval:', error)
    }
  }

  const handleApprove = async (campaignId: string) => {
    try {
      await fetch(`/api/campaigns/${campaignId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved_by: 'akbar' }),
      })
      fetchCampaigns()
    } catch (error) {
      console.error('Failed to approve:', error)
    }
  }

  const handleSchedule = async (campaignId: string, scheduledFor: string) => {
    try {
      await fetch(`/api/campaigns/${campaignId}/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scheduled_for: scheduledFor }),
      })
      fetchCampaigns()
    } catch (error) {
      console.error('Failed to schedule:', error)
    }
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'bg-gray-100'
      case 'pending_approval':
        return 'bg-yellow-100'
      case 'approved':
        return 'bg-blue-100'
      case 'scheduled':
        return 'bg-purple-100'
      case 'posted':
        return 'bg-green-100'
      default:
        return 'bg-gray-100'
    }
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Campaign Manager</h1>
        <p className="text-gray-600 mt-2">Create, review, and schedule LinkedIn carousels</p>
      </div>

      <Tabs value={activeTab} onValueChange={(val) => {
        setActiveTab(val)
        fetchCampaigns()
      }}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="draft">Drafts</TabsTrigger>
          <TabsTrigger value="pending_approval">Pending</TabsTrigger>
          <TabsTrigger value="approved">Approved</TabsTrigger>
          <TabsTrigger value="scheduled">Scheduled</TabsTrigger>
          <TabsTrigger value="posted">Posted</TabsTrigger>
        </TabsList>

        {['draft', 'pending_approval', 'approved', 'scheduled', 'posted'].map((status) => (
          <TabsContent key={status} value={status} className="space-y-4">
            {loading ? (
              <div className="text-center py-8">Loading...</div>
            ) : campaigns.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No campaigns</div>
            ) : (
              <div className="grid gap-4">
                {campaigns.map((campaign) => (
                  <Card
                    key={campaign.id}
                    className={`cursor-pointer transition hover:shadow-md ${statusColor(campaign.status)}`}
                    onClick={() => {
                      setSelectedCampaign(campaign)
                      fetchAnalytics(campaign.id)
                    }}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-lg">{campaign.title}</CardTitle>
                          <CardDescription>{campaign.carousel_type}</CardDescription>
                        </div>
                        <Badge variant="secondary">{campaign.status.replace('_', ' ')}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>Created: {new Date(campaign.created_at).toLocaleDateString()}</p>
                        {campaign.scheduled_for && (
                          <p>Scheduled: {new Date(campaign.scheduled_for).toLocaleDateString()}</p>
                        )}
                      </div>

                      {selectedCampaign?.id === campaign.id && analytics[campaign.id] && (
                        <div className="mt-4 pt-4 border-t space-y-2 text-sm">
                          <p>📊 Analytics (Last 7 days)</p>
                          <div className="grid grid-cols-2 gap-2">
                            {Object.entries(analytics[campaign.id]).map(([key, value]) => (
                              <div key={key} className="bg-white bg-opacity-50 p-2 rounded">
                                <p className="text-gray-600">{key}</p>
                                <p className="font-bold text-lg">{value}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="mt-4 flex gap-2">
                        {campaign.status === 'draft' && (
                          <Button
                            size="sm"
                            variant="default"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleSubmitForApproval(campaign.id)
                            }}
                          >
                            Submit for Approval
                          </Button>
                        )}
                        {campaign.status === 'pending_approval' && (
                          <Button
                            size="sm"
                            variant="default"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleApprove(campaign.id)
                            }}
                          >
                            Approve
                          </Button>
                        )}
                        {campaign.status === 'approved' && (
                          <Button
                            size="sm"
                            variant="default"
                            onClick={(e) => {
                              e.stopPropagation()
                              // Show date picker for scheduling
                              const date = new Date()
                              date.setDate(date.getDate() + 1)
                              handleSchedule(campaign.id, date.toISOString())
                            }}
                          >
                            Schedule
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>

      {selectedCampaign && (
        <Card>
          <CardHeader>
            <CardTitle>Campaign Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="font-semibold">{selectedCampaign.title}</h3>
              <p className="text-sm text-gray-600">{selectedCampaign.carousel_type}</p>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Status</p>
                <p className="font-semibold">{selectedCampaign.status}</p>
              </div>
              <div>
                <p className="text-gray-600">Created</p>
                <p className="font-semibold">{new Date(selectedCampaign.created_at).toLocaleDateString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
