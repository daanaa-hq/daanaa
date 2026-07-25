import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Volunteer {
  id: string;
  volunteer_name: string;
  volunteer_email: string;
  role: string;
  status: string;
  created_at: string;
}

interface HourSubmission {
  id: string;
  volunteer_name: string;
  hours: number;
  job_description: string;
  service_date: string;
  status: string;
  notes?: string;
}

export default function VolunteerApprovalDashboard() {
  const { eventId } = useParams<{ eventId: string }>();
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [pendingHours, setPendingHours] = useState<HourSubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [volRes, reportRes] = await Promise.all([
          fetch(`/api/events/${eventId}/volunteers`),
          fetch(`/api/events/${eventId}/report`)
        ]);

        if (!volRes.ok || !reportRes.ok) throw new Error('Failed to fetch data');

        const volunteers = await volRes.json();
        setVolunteers(volunteers);

        const report = await reportRes.json();
        // Extract pending hours from report
        const pending: HourSubmission[] = [];
        if (report.volunteers) {
          report.volunteers.forEach((v: any) => {
            if (v.pending_hours > 0) {
              pending.push({
                id: `${v.volunteer_name}-pending`,
                volunteer_name: v.volunteer_name,
                hours: v.pending_hours,
                job_description: 'Pending',
                service_date: '',
                status: 'pending'
              });
            }
          });
        }
        setPendingHours(pending);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [eventId]);

  const handleApprove = async (hourId: string) => {
    setApproving(hourId);
    try {
      const token = localStorage.getItem('auth_token') || '';
      const response = await fetch(`/api/events/${eventId}/hours/${hourId}/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('Failed to approve');

      setPendingHours(prev => prev.filter(h => h.id !== hourId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve');
    } finally {
      setApproving(null);
    }
  };

  if (loading) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8 bg-gradient-to-br from-purple-50 to-pink-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">Volunteer Management</h1>

        {error && <div className="bg-destructive/5 border border-destructive/20 p-4 rounded text-destructive mb-6">{error}</div>}

        {/* Volunteers Grid */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Registered Volunteers ({volunteers.length})</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {volunteers.map(v => (
              <Card key={v.id}>
                <CardContent className="pt-6">
                  <h3 className="font-semibold text-lg text-gray-900">{v.volunteer_name}</h3>
                  <p className="text-sm text-gray-600">{v.volunteer_email}</p>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Role: {v.role || 'Unspecified'}</span>
                    <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                      v.status === 'checked_in' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {v.status === 'checked_in' ? 'Checked In' : 'Registered'}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Pending Approvals */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Hour Submissions Pending Approval</h2>
          {pendingHours.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-gray-600">All hours have been approved!</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {pendingHours.map(h => (
                <Card key={h.id}>
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-semibold text-lg text-gray-900">{h.volunteer_name}</h3>
                        <p className="text-sm text-gray-600">{h.hours} hours · {h.job_description}</p>
                        {h.notes && <p className="text-sm text-gray-600 mt-1">Notes: {h.notes}</p>}
                      </div>
                      <span className="inline-block px-3 py-1 rounded bg-yellow-100 text-yellow-800 text-xs font-semibold">
                        Pending
                      </span>
                    </div>
                    <Button
                      onClick={() => handleApprove(h.id)}
                      disabled={approving === h.id}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg font-semibold"
                    >
                      {approving === h.id ? 'Approving...' : 'Approve'}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
