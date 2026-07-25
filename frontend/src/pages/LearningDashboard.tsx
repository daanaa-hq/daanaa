import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { TrendingUp, Brain, Zap, CheckCircle, AlertCircle, Award } from 'lucide-react'

interface LearningStatus {
  carousel_stats: { total_carousels: number; total_impressions: number; avg_engagement_rate: number }
  learning_stats: { total_themes: number; avg_confidence: number; high_confidence_themes: number }
  recommendation_stats: { pending: number; approved: number; rejected: number }
  autonomy_level: number
}

interface Theme {
  theme: string
  carousel_count: number
  avg_engagement_rate: number
  confidence_score: number
  last_seen: string
}

export function LearningDashboard() {
  const [status, setStatus] = useState<LearningStatus | null>(null)
  const [themes, setThemes] = useState<Theme[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [statusRes, themesRes, summaryRes] = await Promise.all([
        fetch('/api/learning/status'),
        fetch('/api/learning/themes'),
        fetch('/api/learning/summary')
      ])

      if (statusRes.ok) setStatus(await statusRes.json())
      if (themesRes.ok) setThemes((await themesRes.json()).all_themes || [])
      if (summaryRes.ok) setSummary(await summaryRes.json())
    } catch (error) {
      console.error('Failed to fetch learning data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="w-full max-w-6xl mx-auto p-6">
        <div className="text-center text-gray-500">Loading learning dashboard...</div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Learning Engine Status</h1>
        <p className="text-gray-600">Real-time continuous improvement metrics and discovered themes</p>
      </div>

      {/* Autonomy Level */}
      {status && (
        <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950 dark:to-cyan-950">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="text-blue-600" size={20} />
              Platform Autonomy
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Learning Progress</span>
                <span className="text-2xl font-bold text-blue-600">{status.autonomy_level}%</span>
              </div>
              <Progress value={status.autonomy_level} className="h-3" />
            </div>
            <p className="text-sm text-gray-600">
              System is {status.autonomy_level > 70 ? 'highly' : status.autonomy_level > 40 ? 'moderately' : 'learning to be'} autonomous.
              {status.autonomy_level > 80 && ' Ready for auto-execute workflows.'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Key Metrics Grid */}
      {status && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Carousels Posted</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{status.carousel_stats.total_carousels}</p>
              <p className="text-xs text-gray-500 mt-1">Total campaigns</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Avg Engagement</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{(status.carousel_stats.avg_engagement_rate || 0).toFixed(2)}%</p>
              <p className="text-xs text-gray-500 mt-1">Across all carousels</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Discovered Themes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{status.learning_stats.total_themes}</p>
              <p className="text-xs text-gray-500 mt-1">{status.learning_stats.high_confidence_themes} high-confidence</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Pending Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-amber-600">{status.recommendation_stats.pending}</p>
              <p className="text-xs text-gray-500 mt-1">Awaiting approval</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Learning Progress */}
      {summary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="text-purple-600" size={20} />
              Learning Progress
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Themes Discovered */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Themes Discovered</span>
                  <Badge variant="secondary">
                    {summary.learning_progress.discovered_themes} total
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>High Confidence</span>
                    <span className="font-semibold">{summary.learning_progress.high_confidence_themes}</span>
                  </div>
                  <Progress value={(summary.learning_progress.high_confidence_themes / (summary.learning_progress.discovered_themes || 1)) * 100} />
                </div>
                <p className="text-xs text-gray-500">
                  Avg confidence: {(summary.learning_progress.avg_theme_confidence * 100).toFixed(1)}%
                </p>
              </div>

              {/* Recommendation Quality */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Recommendation Quality</span>
                  <Badge variant="outline">
                    {summary.recommendation_quality.acceptance_rate_pct.toFixed(0)}% approved
                  </Badge>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-green-600">✓ Approved</span>
                    <span>{summary.recommendation_quality.approved}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-destructive">✗ Rejected</span>
                    <span>{summary.recommendation_quality.rejected}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Trend */}
            {summary.performance_trend && (
              <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg border border-gray-200 dark:border-gray-800">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Engagement Trend</span>
                  <div className="flex items-center gap-2">
                    {summary.performance_trend.trend === 'improving' && (
                      <>
                        <TrendingUp className="text-green-600" size={16} />
                        <span className="text-sm font-semibold text-green-600">Improving</span>
                      </>
                    )}
                    {summary.performance_trend.trend === 'stable' && (
                      <>
                        <Award className="text-blue-600" size={16} />
                        <span className="text-sm font-semibold text-blue-600">Stable</span>
                      </>
                    )}
                    {summary.performance_trend.trend === 'declining' && (
                      <>
                        <AlertCircle className="text-amber-600" size={16} />
                        <span className="text-sm font-semibold text-amber-600">Declining</span>
                      </>
                    )}
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  7-day avg: {(summary.performance_trend.last_7_days.engagement_rate_last_7d || 0).toFixed(2)}% |
                  30-day avg: {(summary.performance_trend.last_30_days.engagement_rate_last_30d || 0).toFixed(2)}%
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* High-Confidence Themes */}
      {themes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="text-amber-600" size={20} />
              Strongest Engagement Signals
            </CardTitle>
            <CardDescription>Themes with highest engagement and confidence scores</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {themes.slice(0, 5).map((theme) => (
                <div key={theme.theme} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
                  <div className="flex-1">
                    <div className="font-semibold capitalize">{theme.theme.replace(/_/g, ' ')}</div>
                    <div className="flex gap-4 mt-1 text-xs text-gray-600">
                      <span>Carousels: {theme.carousel_count}</span>
                      <span>Engagement: {theme.avg_engagement_rate.toFixed(2)}%</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-blue-600">{(theme.confidence_score * 100).toFixed(0)}%</div>
                    <div className="text-xs text-gray-500">Confidence</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* System Status */}
      <div className="text-center text-sm text-gray-500">
        <p>⚡ Learning dashboard auto-refreshes every 30 seconds</p>
      </div>
    </div>
  )
}
