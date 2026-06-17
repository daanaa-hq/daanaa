import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { getVerifiedHours, VerifiedHour } from '../data/api'

export default function VerifiedHours() {
  const { getIdToken } = useAuth()
  const [hours, setHours] = useState<VerifiedHour[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadHours = async () => {
      try {
        const idToken = await getIdToken()
        if (!idToken) {
          console.error('No auth token available')
          setLoading(false)
          return
        }
        const data = await getVerifiedHours(idToken)
        setHours(data || [])
      } catch (err) {
        console.error('Error fetching verified hours:', err)
      } finally {
        setLoading(false)
      }
    }

    loadHours()
  }, [getIdToken])

  if (loading) {
    return <div className="text-center text-cool-grey py-8">Loading...</div>
  }

  if (hours.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-cool-grey mb-3">No verified hours yet.</p>
        <p className="text-sm text-slate-500">
          When a nonprofit confirms your volunteer hours, they will appear here.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {hours.map((h) => (
        <div key={h.id} className="p-4 border border-green-200 bg-green-50 rounded-lg">
          <div className="flex items-start justify-between mb-2">
            <div>
              <p className="font-semibold text-deep-navy">{h.nonprofit_name}</p>
              <p className="text-sm text-cool-grey">{h.service_date}</p>
              {h.notes && <p className="text-xs text-slate-600 mt-2 italic">{h.notes}</p>}
            </div>
            <div className="text-right whitespace-nowrap ml-4">
              <p className="font-semibold text-deep-navy">{h.hours_confirmed.toFixed(1)} hours</p>
              <p className="text-sm text-green-700 font-medium">✓ Verified</p>
            </div>
          </div>

          <div className="pt-3 border-t border-green-200 mt-3">
            <p className="text-sm text-deep-navy">
              Estimated community value: <span className="font-semibold">${h.estimated_value.toFixed(2)}</span>
            </p>
            <p className="text-xs text-slate-600 mt-2">
              This estimate is for personal impact tracking only. It is not a donation receipt, tax deduction, wage, or payment.
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
