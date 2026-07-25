import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle, XCircle, Lightbulb, Calendar, MessageCircle, Send } from 'lucide-react'

interface WeeklyTheme {
  id: number
  week_starting: string
  theme_title: string
  theme_angle: string
  data_hook: string
  confidence_score: number
}

interface Opportunity {
  id: number
  title: string
  opportunity_type: string
  quality_score: number
  relevance_angle: string
}

interface Comment {
  id: number
  title: string
  opportunity_type: string
  comment_text: string
  quality_score: number
}

interface Stats {
  themes: { total: number; approved: number }
  opportunities: { total: number; comments_generated: number }
  comments_published: number
}

export function SocialManagerDashboard() {
  const [activeTab, setActiveTab] = useState('themes')
  const [themes, setThemes] = useState<WeeklyTheme[]>([])
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [comments, setComments] = useState<Comment[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [themesRes, oppRes, commentsRes, statsRes] = await Promise.all([
        fetch('/api/social-manager/weekly-themes'),
        fetch('/api/social-manager/opportunities'),
        fetch('/api/social-manager/comments'),
        fetch('/api/social-manager/stats')
      ])

      if (themesRes.ok) setThemes((await themesRes.json()).pending_themes || [])
      if (oppRes.ok) setOpportunities((await oppRes.json()).opportunities || [])
      if (commentsRes.ok) setComments((await commentsRes.json()).pending_comments || [])
      if (statsRes.ok) setStats(await statsRes.json())
    } catch (error) {
      console.error('Failed to fetch social manager data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApproveTheme = async (themeId: number) => {
    await fetch(`/api/social-manager/weekly-themes/${themeId}/approve`, { method: 'POST' })
    await fetchData()
  }

  const handleRejectTheme = async (themeId: number) => {
    await fetch(`/api/social-manager/weekly-themes/${themeId}/reject`, { method: 'POST' })
    await fetchData()
  }

  const handlePublishComment = async (commentId: number) => {
    await fetch(`/api/social-manager/comments/${commentId}/publish`, { method: 'POST' })
    await fetchData()
  }

  if (loading) {
    return <div className="text-center text-gray-500 p-6">Loading social manager...</div>
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Social Media Manager</h1>
        <p className="text-gray-600">Review autonomously curated weekly themes & comments. You approve, we handle the rest.</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Themes Created</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{stats.themes.total}</p>
              <p className="text-xs text-gray-500 mt-1">{stats.themes.approved} approved</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Opportunities Found</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-blue-600">{stats.opportunities.total}</p>
              <p className="text-xs text-gray-500 mt-1">{stats.opportunities.comments_generated} comments</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Comments Published</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-green-600">{stats.comments_published}</p>
              <p className="text-xs text-gray-500 mt-1">Last 30 days</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Pending Review</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-amber-600">{themes.length + comments.length}</p>
              <p className="text-xs text-gray-500 mt-1">Await your approval</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Workflow Alert */}
      <Alert className="border-green-200 bg-green-50 dark:bg-green-950">
        <Lightbulb className="h-4 w-4 text-green-600" />
        <AlertDescription className="text-green-800 dark:text-green-200 text-sm">
          ✓ Workflow: AI generates themes & comments → You review → Click approve → I handle LinkedIn posting (your checklist)
        </AlertDescription>
      </Alert>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="themes" className="gap-2">
            <Calendar size={16} /> Weekly Themes ({themes.length})
          </TabsTrigger>
          <TabsTrigger value="opportunities" className="gap-2">
            <Lightbulb size={16} /> Opportunities ({opportunities.length})
          </TabsTrigger>
          <TabsTrigger value="comments" className="gap-2">
            <MessageCircle size={16} /> Comments ({comments.length})
          </TabsTrigger>
        </TabsList>

        {/* Themes Tab */}
        <TabsContent value="themes" className="space-y-4">
          {themes.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center text-gray-500">
                No pending themes — check back next week
              </CardContent>
            </Card>
          ) : (
            themes.map(theme => (
              <Card key={theme.id} className="border-l-4 border-l-blue-500">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{theme.theme_title}</CardTitle>
                      <CardDescription>Week of {new Date(theme.week_starting).toLocaleDateString()}</CardDescription>
                    </div>
                    <Badge className="bg-blue-600">{(theme.confidence_score * 100).toFixed(0)}%</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Angle</p>
                    <p className="text-sm mt-1">{theme.theme_angle}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Data Hook</p>
                    <p className="text-sm mt-1">{theme.data_hook}</p>
                  </div>
                  <div className="flex gap-2 pt-2">
                    <Button
                      onClick={() => handleApproveTheme(theme.id)}
                      className="bg-green-600 hover:bg-green-700 gap-2 flex-1"
                    >
                      <CheckCircle size={16} />
                      Approve & Create Carousel
                    </Button>
                    <Button
                      onClick={() => handleRejectTheme(theme.id)}
                      variant="outline"
                      className="text-destructive hover:text-destructive flex-1"
                    >
                      <XCircle size={16} />
                      Reject
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        {/* Opportunities Tab */}
        <TabsContent value="opportunities" className="space-y-4">
          {opportunities.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center text-gray-500">
                No trending opportunities detected
              </CardContent>
            </Card>
          ) : (
            opportunities.map(opp => (
              <Card key={opp.id} className="border-l-4 border-l-purple-500">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-base">{opp.title}</CardTitle>
                      <CardDescription className="capitalize">{opp.opportunity_type.replace('_', ' ')}</CardDescription>
                    </div>
                    <Badge variant="secondary">{(opp.quality_score * 100).toFixed(0)}% quality</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">{opp.relevance_angle}</p>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        {/* Comments Tab */}
        <TabsContent value="comments" className="space-y-4">
          {comments.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center text-gray-500">
                No comments ready for posting
              </CardContent>
            </Card>
          ) : (
            comments.map(comment => (
              <Card key={comment.id} className="border-l-4 border-l-green-500">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-sm font-medium">Comment on: {comment.title}</CardTitle>
                      <CardDescription className="capitalize mt-1">{comment.opportunity_type.replace('_', ' ')}</CardDescription>
                    </div>
                    <Badge className="bg-green-600">{(comment.quality_score * 100).toFixed(0)}%</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded border border-gray-200 dark:border-gray-800">
                    <p className="text-sm whitespace-pre-wrap">{comment.comment_text}</p>
                  </div>
                  <Button
                    onClick={() => handlePublishComment(comment.id)}
                    className="bg-blue-600 hover:bg-blue-700 gap-2 w-full"
                  >
                    <Send size={16} />
                    Publish to LinkedIn
                  </Button>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>

      {/* Posting Instructions */}
      <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900 dark:text-blue-100 text-sm">Your Checklist</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 dark:text-blue-200 space-y-2">
          <div>✓ Review weekly theme + data hook</div>
          <div>✓ Click "Approve & Create Carousel" (we'll build it)</div>
          <div>✓ Review comment + click "Publish to LinkedIn"</div>
          <div>✓ Comment posts automatically (when we wire LinkedIn API)</div>
        </CardContent>
      </Card>

      <div className="text-center text-sm text-gray-500">
        <p>⚡ Auto-refreshes every 30 seconds</p>
      </div>
    </div>
  )
}
