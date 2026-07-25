import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface DashboardData {
  event_name: string;
  event_date: string;
  status: string;
  volunteer_count: number;
  total_hours_approved: number;
  volunteer_count_checked_in: number;
  avg_hours_per_volunteer: number;
}

export default function EventDashboard() {
  const { eventId } = useParams<{ eventId: string }>();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch(`/api/events/${eventId}/dashboard`);
        if (!response.ok) throw new Error('Failed to fetch dashboard');
        const data = await response.json();
        setDashboard(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    const interval = setInterval(fetchDashboard, 30000); // Refresh every 30 seconds
    fetchDashboard();
    return () => clearInterval(interval);
  }, [eventId]);

  if (loading) return <div className="p-8">Loading dashboard...</div>;
  if (error) return <div className="p-8 text-destructive">Error: {error}</div>;
  if (!dashboard) return <div className="p-8">No data available</div>;

  return (
    <div className="p-8 bg-gradient-to-br from-blue-50 to-indigo-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Event Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">{dashboard.event_name}</h1>
          <p className="text-lg text-gray-600 mt-2">{dashboard.event_date}</p>
          <span className={`inline-block mt-4 px-4 py-1 rounded-full text-sm font-semibold ${
            dashboard.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
          }`}>
            {dashboard.status.toUpperCase()}
          </span>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Volunteers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-indigo-600">{dashboard.volunteer_count}</div>
              <p className="text-xs text-gray-500 mt-1">Registered</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Total Hours</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">{dashboard.total_hours_approved.toFixed(1)}</div>
              <p className="text-xs text-gray-500 mt-1">Approved</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Checked In</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{dashboard.volunteer_count_checked_in}</div>
              <p className="text-xs text-gray-500 mt-1">On-site</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Avg Hours</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">{dashboard.avg_hours_per_volunteer.toFixed(1)}</div>
              <p className="text-xs text-gray-500 mt-1">Per volunteer</p>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <Button asChild variant="default">
            <a href={`/event/${eventId}/volunteers`}>Manage Volunteers</a>
          </Button>
          <Button asChild variant="outline">
            <a href={`/event/${eventId}/report`}>View Report</a>
          </Button>
        </div>
      </div>
    </div>
  );
}
