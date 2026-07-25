/**
 * ServiceLogPage.tsx
 * Student logs and views volunteer hours
 * Route: /student/service-log
 */

import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit2, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface ServiceLog {
  service_log_id: string;
  nonprofit_ein: string;
  nonprofit_name: string;
  service_date: string;
  hours_claimed: number;
  activity_description: string;
  submission_status: 'submitted' | 'approved' | 'rejected' | 'flagged' | 'disputed';
  submitted_at: string;
  approved_at?: string;
  rejected_reason?: string;
}

interface ServiceLogSummary {
  total_hours_submitted: number;
  total_hours_approved: number;
  pending_approval: number;
  rejected: number;
}

export default function ServiceLogPage() {
  const { user, getIdToken } = useAuth();
  const [logs, setLogs] = useState<ServiceLog[]>([]);
  const [summary, setSummary] = useState<ServiceLogSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    nonprofit_ein: '',
    service_date: '',
    hours_claimed: '',
    activity_description: '',
    supervisor_name: '',
  });

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  // Fetch service logs
  const fetchLogs = async () => {
    try {
      if (!user) {
        alert('Please sign in to view service logs');
        return;
      }
      setLoading(true);
      const token = await getIdToken();
      const response = await fetch(`${API_URL}/api/student/service-log`, {
        headers: {
          'Authorization': `Bearer ${token || ''}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch service logs');

      const data = await response.json();
      setLogs(data.data);
      setSummary(data.summary);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error loading service logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchLogs();
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (!user) {
        alert('Please sign in to log hours');
        return;
      }

      // Validation
      if (!formData.nonprofit_ein || !formData.service_date || !formData.hours_claimed || !formData.activity_description) {
        alert('Please fill in all required fields');
        return;
      }

      const hours = parseFloat(formData.hours_claimed);
      if (hours <= 0 || hours > 24) {
        alert('Hours must be between 0.5 and 24');
        return;
      }

      const token = await getIdToken();
      const response = await fetch(`${API_URL}/api/student/service-log/submit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to submit hours');
      }

      // Success
      alert('Hours logged successfully!');
      setFormData({
        nonprofit_ein: '',
        service_date: '',
        hours_claimed: '',
        activity_description: '',
        supervisor_name: '',
      });
      setShowForm(false);
      fetchLogs();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error submitting hours');
    }
  };

  const handleDelete = async (serviceLogId: string) => {
    if (!confirm('Delete this service log? This action cannot be undone.')) return;

    try {
      if (!user) {
        alert('Please sign in to delete logs');
        return;
      }

      const token = await getIdToken();
      const response = await fetch(`${API_URL}/api/student/service-log/${serviceLogId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token || ''}`,
        },
      });

      if (!response.ok) throw new Error('Failed to delete');

      alert('Service log deleted');
      fetchLogs();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error deleting log');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'rejected':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'submitted':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-orange-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      submitted: 'bg-yellow-100 text-yellow-800',
      flagged: 'bg-orange-100 text-orange-800',
      disputed: 'bg-purple-100 text-purple-800',
    };

    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${styles[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Service Log</h1>
              <p className="mt-2 text-gray-600">Track your volunteer hours</p>
            </div>
            <button
              onClick={() => setShowForm(!showForm)}
              className="inline-flex items-center gap-2 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 font-medium"
            >
              <Plus className="w-5 h-5" />
              Log Hours
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <p className="text-gray-600 text-sm">Total Submitted</p>
              <p className="text-2xl font-bold text-gray-900">{summary.total_hours_submitted.toFixed(1)}</p>
              <p className="text-xs text-gray-500">hours</p>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <p className="text-gray-600 text-sm">Approved</p>
              <p className="text-2xl font-bold text-green-600">{summary.total_hours_approved.toFixed(1)}</p>
              <p className="text-xs text-gray-500">hours</p>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <p className="text-gray-600 text-sm">Pending</p>
              <p className="text-2xl font-bold text-yellow-600">{summary.pending_approval}</p>
              <p className="text-xs text-gray-500">submissions</p>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <p className="text-gray-600 text-sm">Rejected</p>
              <p className="text-2xl font-bold text-destructive">{summary.rejected}</p>
              <p className="text-xs text-gray-500">submissions</p>
            </div>
          </div>
        )}

        {/* Form */}
        {showForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Log Service Hours</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Organization */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Organization <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="EIN or organization name"
                    value={formData.nonprofit_ein}
                    onChange={(e) => setFormData({ ...formData, nonprofit_ein: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Service Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={formData.service_date}
                    onChange={(e) => setFormData({ ...formData, service_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Hours */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Hours <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="0.5"
                    max="24"
                    placeholder="e.g., 4.5"
                    value={formData.hours_claimed}
                    onChange={(e) => setFormData({ ...formData, hours_claimed: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Supervisor Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Supervisor Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., Jane Smith"
                    value={formData.supervisor_name}
                    onChange={(e) => setFormData({ ...formData, supervisor_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Activity Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  What did you do? <span className="text-red-500">*</span>
                </label>
                <textarea
                  placeholder="Describe your volunteer work in detail..."
                  value={formData.activity_description}
                  onChange={(e) => setFormData({ ...formData, activity_description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Buttons */}
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 font-medium"
                >
                  Log Hours
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Service Logs List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="mt-4 text-gray-600">Loading service logs...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="bg-white rounded-lg p-12 text-center shadow-sm">
            <p className="text-gray-600 text-lg">No service logs yet. Click "Log Hours" to get started!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {logs.map((log) => (
              <div key={log.service_log_id} className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900">{log.nonprofit_name}</h3>
                    <p className="text-sm text-gray-600">{new Date(log.service_date).toLocaleDateString()}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(log.submission_status)}
                    {getStatusBadge(log.submission_status)}
                  </div>
                </div>

                <p className="text-gray-700 mb-4">{log.activity_description}</p>

                <div className="flex justify-between items-center mb-4">
                  <div className="text-2xl font-bold text-gray-900">
                    {log.hours_claimed.toFixed(1)} <span className="text-lg text-gray-600">hours</span>
                  </div>
                  {log.rejected_reason && (
                    <div className="text-sm text-destructive">
                      <strong>Rejection reason:</strong> {log.rejected_reason}
                    </div>
                  )}
                </div>

                {/* Actions */}
                {log.submission_status === 'submitted' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleDelete(log.service_log_id)}
                      className="inline-flex items-center gap-2 px-3 py-2 text-destructive hover:bg-destructive/5 rounded-lg border border-destructive/20"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
