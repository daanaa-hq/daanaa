import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const JOB_TYPES = ['Setup', 'Registration', 'Scoring', 'Food Service', 'Cleanup', 'Other'];

interface Volunteer {
  id: string;
  volunteer_name: string;
  volunteer_email: string;
}

export default function LogVolunteerHours() {
  const { eventId } = useParams<{ eventId: string }>();
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [formData, setFormData] = useState({
    volunteer_id: '',
    hours: '',
    job_description: '',
    service_date: new Date().toISOString().split('T')[0],
    notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const fetchVolunteers = async () => {
      try {
        const response = await fetch(`/api/events/${eventId}/volunteers`);
        if (!response.ok) throw new Error('Failed to fetch volunteers');
        const data = await response.json();
        setVolunteers(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load volunteers');
      } finally {
        setLoading(false);
      }
    };

    fetchVolunteers();
  }, [eventId]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const payload = {
        ...formData,
        hours: parseFloat(formData.hours)
      };

      const response = await fetch(`/api/events/${eventId}/hours`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to log hours');
      }

      setSuccess(true);
      setFormData({
        volunteer_id: '',
        hours: '',
        job_description: '',
        service_date: new Date().toISOString().split('T')[0],
        notes: ''
      });
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-8 bg-gradient-to-br from-blue-50 to-cyan-50 min-h-screen">
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Log Volunteer Hours</CardTitle>
            <p className="text-gray-600 text-sm mt-2">Record time served for this event</p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Volunteer Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Volunteer *
                </label>
                <select
                  name="volunteer_id"
                  value={formData.volunteer_id}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={loading || volunteers.length === 0}
                >
                  <option value="">
                    {loading ? 'Loading volunteers...' : 'Select a volunteer'}
                  </option>
                  {volunteers.map(v => (
                    <option key={v.id} value={v.id}>
                      {v.volunteer_name} ({v.volunteer_email})
                    </option>
                  ))}
                </select>
                {!loading && volunteers.length === 0 && (
                  <p className="text-sm text-gray-500 mt-1">No volunteers registered yet</p>
                )}
              </div>

              {/* Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Service Date *
                </label>
                <Input
                  type="date"
                  name="service_date"
                  value={formData.service_date}
                  onChange={handleChange}
                  required
                  className="w-full"
                />
              </div>

              {/* Hours */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Hours Worked *
                </label>
                <Input
                  type="number"
                  name="hours"
                  value={formData.hours}
                  onChange={handleChange}
                  required
                  step="0.5"
                  min="0"
                  placeholder="4.5"
                  className="w-full"
                />
              </div>

              {/* Job Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job Type *
                </label>
                <select
                  name="job_description"
                  value={formData.job_description}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select job type</option>
                  {JOB_TYPES.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Additional Notes
                </label>
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                  placeholder="Any additional details about this shift..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>

              {/* Messages */}
              {error && <div className="bg-red-50 border border-red-200 p-3 rounded text-red-700 text-sm">{error}</div>}
              {success && <div className="bg-green-50 border border-green-200 p-3 rounded text-green-700 text-sm">Hours logged successfully!</div>}

              {/* Submit */}
              <Button
                type="submit"
                disabled={submitting || loading || volunteers.length === 0}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-semibold"
              >
                {submitting ? 'Submitting...' : 'Log Hours'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
