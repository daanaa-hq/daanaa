import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { Search, Mail, Phone, MapPin, Award, Calendar } from 'lucide-react'

interface Volunteer {
  email: string
  name: string
  total_hours: number
  submissions_count: number
  last_service_date: string
  status: 'active' | 'inactive'
  avg_task_type?: string
}

export default function NonprofitVolunteerDirectoryV2() {
  const { ein } = useParams<{ ein: string }>()
  const { user, getIdToken } = useAuth()
  const [volunteers, setVolunteers] = useState<Volunteer[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<'hours' | 'submissions' | 'recent'>('hours')

  useEffect(() => {
    const fetchVolunteers = async () => {
      if (!ein || !user) return

      const token = await getIdToken()
      if (!token) return

      try {
        const res = await fetch(`/api/nonprofit/${ein}/volunteer/directory`, {
          headers: { Authorization: `Bearer ${token}` },
        })

        if (res.ok) {
          const data = await res.json()
          setVolunteers(data.data || data.volunteers || [])
        }
      } catch (error) {
        console.error('Volunteer fetch failed:', error)
      } finally {
        setLoading(false)
      }
    }

    setLoading(true)
    fetchVolunteers()
  }, [ein, user, getIdToken])

  const filteredVolunteers = volunteers
    .filter((v) => v.name.toLowerCase().includes(search.toLowerCase()) ||
                  v.email.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (sortBy === 'hours') return b.total_hours - a.total_hours
      if (sortBy === 'submissions') return b.submissions_count - a.submissions_count
      return new Date(b.last_service_date).getTime() - new Date(a.last_service_date).getTime()
    })

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full border-4 border-soft-gold border-t-transparent animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Loading volunteer directory...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Volunteer Directory</h1>
          <p className="text-slate-600">
            {volunteers.length} volunteers · {volunteers.reduce((sum, v) => sum + v.total_hours, 0).toFixed(0)} total hours
          </p>
        </div>

        {/* Search & Sort */}
        <div className="flex gap-4 mb-6 flex-wrap">
          <div className="flex-1 min-w-72 relative">
            <Search size={20} className="absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-soft-gold"
            />
          </div>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'hours' | 'submissions' | 'recent')}
            className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-soft-gold bg-white"
          >
            <option value="hours">Most Hours</option>
            <option value="submissions">Most Submissions</option>
            <option value="recent">Most Recent</option>
          </select>
        </div>

        {/* Volunteers Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredVolunteers.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <p className="text-slate-600 text-lg">No volunteers found</p>
            </div>
          ) : (
            filteredVolunteers.map((volunteer) => (
              <div
                key={volunteer.email}
                className="bg-white rounded-lg border border-slate-200 p-6 hover:shadow-lg transition"
              >
                {/* Status Badge */}
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">{volunteer.name}</h3>
                    <p className="text-sm text-slate-600">{volunteer.email}</p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${
                      volunteer.status === 'active'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-slate-100 text-slate-800'
                    }`}
                  >
                    {volunteer.status === 'active' ? '● Active' : '● Inactive'}
                  </span>
                </div>

                {/* Stats */}
                <div className="space-y-3 mb-4">
                  <div className="flex items-center gap-3">
                    <Award size={18} className="text-amber-500" />
                    <div>
                      <p className="text-xs text-slate-600 font-medium">TOTAL HOURS</p>
                      <p className="text-lg font-bold text-slate-900">
                        {volunteer.total_hours.toFixed(1)}h
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Calendar size={18} className="text-blue-500" />
                    <div>
                      <p className="text-xs text-slate-600 font-medium">SUBMISSIONS</p>
                      <p className="text-lg font-bold text-slate-900">
                        {volunteer.submissions_count}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <MapPin size={18} className="text-red-500" />
                    <div>
                      <p className="text-xs text-slate-600 font-medium">LAST SERVICE</p>
                      <p className="text-sm text-slate-900">
                        {new Date(volunteer.last_service_date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-4 border-t border-slate-200">
                  <button className="flex-1 px-3 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition flex items-center justify-center gap-2">
                    <Mail size={16} />
                    Email
                  </button>
                  <button className="flex-1 px-3 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition">
                    View Profile
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
