import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { TrendingUp, MessageCircle, Heart, Share2, Eye, Zap, Target, Flame } from 'lucide-react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Button } from '@/components/ui/button'

interface CarouselMetrics {
  carousel_id: string
  title: string
  posted_at: string
  impressions: number
  engagements: number
  comments: number
  likes: number
  shares: number
  engagement_rate: number
  sentiment_score: number
  trending: boolean
}

interface Theme {
  name: string
  score: number
  frequency: number
  posts: number
  trend: 'up' | 'down' | 'stable'
}

interface Recommendation {
  topic: string
  confidence: number
  reason: string
  related_themes: string[]
  estimated_engagement: number
}

const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']

export function SocialMediaDashboard() {
  const [activeTab, setActiveTab] = useState('overview')
  const [carousels, setCarousels] = useState<CarouselMetrics[]>([])
  const [themes, setThemes] = useState<Theme[]>([])
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      // Simulated data for now - will connect to real API
      setCarousels([
        {
          carousel_id: '1',
          title: 'Reserve Crisis - Part 1',
          posted_at: '2 days ago',
          impressions: 2847,
          engagements: 324,
          comments: 47,
          likes: 187,
          shares: 23,
          engagement_rate: 11.4,
          sentiment_score: 0.89,
          trending: true
        },
        {
          carousel_id: '2',
          title: 'The Invisible 97%',
          posted_at: '5 days ago',
          impressions: 1923,
          engagements: 156,
          comments: 22,
          likes: 98,
          shares: 12,
          engagement_rate: 8.1,
          sentiment_score: 0.76,
          trending: false
        }
      ])

      setThemes([
        { name: 'Financial Health', score: 0.92, frequency: 34, posts: 8, trend: 'up' },
        { name: 'Hidden Gems', score: 0.87, frequency: 28, posts: 6, trend: 'up' },
        { name: 'Donor Impact', score: 0.81, frequency: 22, posts: 5, trend: 'stable' },
        { name: 'Nonprofit Equity', score: 0.78, frequency: 19, posts: 4, trend: 'down' }
      ])

      setRecommendations([
        {
          topic: 'The Funding Paradox',
          confidence: 0.94,
          reason: 'High engagement on financial health content (11.4% rate)',
          related_themes: ['Financial Health', 'Hidden Gems'],
          estimated_engagement: 2200
        },
        {
          topic: 'Small Org Wins',
          confidence: 0.87,
          reason: 'Rising trend in hidden gems discussions',
          related_themes: ['Hidden Gems', 'Donor Impact'],
          estimated_engagement: 1800
        },
        {
          topic: 'Equity in Giving',
          confidence: 0.79,
          reason: 'Emerging theme in comments',
          related_themes: ['Nonprofit Equity'],
          estimated_engagement: 1400
        }
      ])
    } catch (error) {
      console.error('Failed to fetch social data:', error)
    } finally {
      setLoading(false)
    }
  }

  const totalImpressions = carousels.reduce((sum, c) => sum + c.impressions, 0)
  const totalEngagements = carousels.reduce((sum, c) => sum + c.engagements, 0)
  const avgEngagementRate = carousels.length > 0 ? (carousels.reduce((sum, c) => sum + c.engagement_rate, 0) / carousels.length).toFixed(1) : 0

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white">Social Media Insights</h1>
          <p className="text-lg text-slate-600 dark:text-slate-400">LinkedIn performance, engagement themes, and content recommendations</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="border-0 shadow-sm bg-white/80 dark:bg-slate-800/80 backdrop-blur">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Total Impressions</CardTitle>
                <Eye className="w-4 h-4 text-blue-500" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-slate-900 dark:text-white">{totalImpressions.toLocaleString()}</p>
              <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">Last 30 days</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm bg-white/80 dark:bg-slate-800/80 backdrop-blur">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Engagements</CardTitle>
                <Heart className="w-4 h-4 text-red-500" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-slate-900 dark:text-white">{totalEngagements.toLocaleString()}</p>
              <p className="text-xs text-green-600 dark:text-green-400 mt-1">↑ 23% vs last month</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm bg-white/80 dark:bg-slate-800/80 backdrop-blur">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Avg Engagement Rate</CardTitle>
                <Zap className="w-4 h-4 text-amber-500" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-slate-900 dark:text-white">{avgEngagementRate}%</p>
              <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">Industry avg: 3-5%</p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm bg-white/80 dark:bg-slate-800/80 backdrop-blur">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">Trending</CardTitle>
                <Flame className="w-4 h-4 text-orange-500" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-slate-900 dark:text-white">2</p>
              <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">hot carousels</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-white/50 dark:bg-slate-800/50 border-0">
            <TabsTrigger value="overview" className="gap-2">
              <Eye size={16} /> Overview
            </TabsTrigger>
            <TabsTrigger value="themes" className="gap-2">
              <Target size={16} /> Themes
            </TabsTrigger>
            <TabsTrigger value="recommendations" className="gap-2">
              <Zap size={16} /> Recommendations
            </TabsTrigger>
          </TabsList>

          {/* OVERVIEW TAB */}
          <TabsContent value="overview" className="space-y-6">
            {/* Recent Carousels */}
            <Card className="border-0 shadow-sm bg-white dark:bg-slate-800">
              <CardHeader>
                <CardTitle>Recent Carousels</CardTitle>
                <CardDescription>Performance metrics for posted content</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {carousels.map((carousel) => (
                  <div
                    key={carousel.carousel_id}
                    className="p-4 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-slate-900 dark:text-white">{carousel.title}</h3>
                          {carousel.trending && (
                            <Badge className="bg-orange-500/20 text-orange-700 dark:text-orange-300 border-0">
                              <Flame size={12} className="mr-1" /> Trending
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{carousel.posted_at}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-green-600 dark:text-green-400">{carousel.engagement_rate}%</p>
                        <p className="text-xs text-slate-500">engagement</p>
                      </div>
                    </div>

                    {/* Mini Chart */}
                    <div className="h-16 mb-3">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={[
                          { name: 'Day 1', value: carousel.impressions * 0.6 },
                          { name: 'Day 2', value: carousel.impressions * 0.85 },
                          { name: 'Today', value: carousel.impressions }
                        ]}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <Line type="monotone" dataKey="value" stroke="#3b82f6" dot={false} strokeWidth={2} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Metrics Grid */}
                    <div className="grid grid-cols-4 gap-3">
                      <div className="text-center p-2 bg-blue-50 dark:bg-blue-950/30 rounded">
                        <Eye size={16} className="mx-auto text-blue-600 dark:text-blue-400 mb-1" />
                        <p className="text-xs font-semibold text-slate-900 dark:text-white">{carousel.impressions.toLocaleString()}</p>
                        <p className="text-xs text-slate-500">impressions</p>
                      </div>
                      <div className="text-center p-2 bg-destructive/5 dark:bg-red-950/30 rounded">
                        <Heart size={16} className="mx-auto text-destructive dark:text-red-400 mb-1" />
                        <p className="text-xs font-semibold text-slate-900 dark:text-white">{carousel.likes}</p>
                        <p className="text-xs text-slate-500">likes</p>
                      </div>
                      <div className="text-center p-2 bg-alert-amber/5 dark:bg-amber-950/30 rounded">
                        <MessageCircle size={16} className="mx-auto text-amber-600 dark:text-amber-400 mb-1" />
                        <p className="text-xs font-semibold text-slate-900 dark:text-white">{carousel.comments}</p>
                        <p className="text-xs text-slate-500">comments</p>
                      </div>
                      <div className="text-center p-2 bg-green-50 dark:bg-green-950/30 rounded">
                        <Share2 size={16} className="mx-auto text-green-600 dark:text-green-400 mb-1" />
                        <p className="text-xs font-semibold text-slate-900 dark:text-white">{carousel.shares}</p>
                        <p className="text-xs text-slate-500">shares</p>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* THEMES TAB */}
          <TabsContent value="themes" className="space-y-6">
            <Card className="border-0 shadow-sm bg-white dark:bg-slate-800">
              <CardHeader>
                <CardTitle>Engagement Themes</CardTitle>
                <CardDescription>Topics driving the most interaction</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {themes.map((theme, idx) => (
                  <div key={idx} className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-8 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }}></div>
                        <div>
                          <h3 className="font-semibold text-slate-900 dark:text-white">{theme.name}</h3>
                          <p className="text-sm text-slate-500 dark:text-slate-400">{theme.posts} carousels • {theme.frequency} mentions</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-slate-900 dark:text-white">{(theme.score * 100).toFixed(0)}%</p>
                        <Badge className={theme.trend === 'up' ? 'bg-green-500/20 text-green-700 dark:text-green-300' : theme.trend === 'down' ? 'bg-destructive/50/20 text-destructive dark:text-red-300' : 'bg-slate-500/20 text-slate-700 dark:text-slate-300'} variant="outline">
                          {theme.trend === 'up' ? '↑' : theme.trend === 'down' ? '↓' : '→'} {theme.trend}
                        </Badge>
                      </div>
                    </div>
                    <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                      <div
                        className="h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${theme.score * 100}%`,
                          backgroundColor: COLORS[idx % COLORS.length]
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* RECOMMENDATIONS TAB */}
          <TabsContent value="recommendations" className="space-y-6">
            <Card className="border-0 shadow-sm bg-white dark:bg-slate-800">
              <CardHeader>
                <CardTitle>Next Carousel Suggestions</CardTitle>
                <CardDescription>AI-powered recommendations based on engagement data</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-lg border-2 border-slate-200 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-500 transition-colors bg-gradient-to-r from-transparent to-transparent hover:from-blue-50/50 dark:hover:from-blue-950/20"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{rec.topic}</h3>
                        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{rec.reason}</p>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center justify-center">
                          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center">
                            <p className="text-2xl font-bold text-white">{(rec.confidence * 100).toFixed(0)}%</p>
                          </div>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">confidence</p>
                      </div>
                    </div>

                    <div className="mb-3 p-3 bg-slate-50 dark:bg-slate-900/50 rounded">
                      <p className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-2">Related themes:</p>
                      <div className="flex flex-wrap gap-2">
                        {rec.related_themes.map((t, i) => (
                          <Badge key={i} variant="secondary" className="bg-slate-200 dark:bg-slate-700">
                            {t}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-3 border-t border-slate-200 dark:border-slate-700">
                      <div>
                        <p className="text-xs text-slate-500">Estimated reach:</p>
                        <p className="text-lg font-semibold text-slate-900 dark:text-white">{rec.estimated_engagement.toLocaleString()} engagements</p>
                      </div>
                      <Button variant="default" size="default">
                        Approve & Schedule
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500 dark:text-slate-500 py-4">
          <p>⚡ Metrics auto-refresh every 30 seconds</p>
        </div>
      </div>
    </div>
  )
}
