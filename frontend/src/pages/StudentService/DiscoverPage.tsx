/**
 * DiscoverPage.tsx
 * Student discovers volunteer opportunities
 * Route: /student/discover
 */

import React, { useState, useEffect } from 'react';
import { Search, MapPin, Clock, Heart } from 'lucide-react';

interface Opportunity {
  opportunity_id: string;
  nonprofit_ein: string;
  nonprofit_name: string;
  title: string;
  description: string;
  cause_area: string;
  location: string;
  location_type: 'in-person' | 'hybrid' | 'remote';
  commitment_hours?: number;
  student_enrollment_status?: 'interested' | 'committed' | 'in-progress' | null;
}

interface PaginationData {
  data: Opportunity[];
  total: number;
  page: number;
  pages: number;
  limit: number;
}

export default function DiscoverPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [causeFilter, setCauseFilter] = useState('');
  const [locationTypeFilter, setLocationTypeFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pagination, setPagination] = useState<PaginationData | null>(null);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  // Fetch opportunities
  useEffect(() => {
    const fetchOpportunities = async () => {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams();
        if (causeFilter) params.append('cause', causeFilter);
        if (locationTypeFilter) params.append('location_type', locationTypeFilter);
        params.append('page', currentPage.toString());
        params.append('limit', '20');

        const response = await fetch(`${API_URL}/api/student/opportunities?${params}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('firebase_token') || ''}`,
          },
        });

        if (!response.ok) throw new Error('Failed to fetch opportunities');

        const data = await response.json();
        setOpportunities(data.data);
        setPagination(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchOpportunities();
  }, [causeFilter, locationTypeFilter, currentPage]);

  // Filter opportunities by search term (client-side)
  const filteredOpportunities = opportunities.filter(opp =>
    opp.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    opp.nonprofit_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    opp.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleEnroll = async (opportunityId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/student/opportunities/${opportunityId}/enroll`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('firebase_token') || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ hours_committed: 10 }),
      });

      if (!response.ok) throw new Error('Failed to enroll');

      // Refresh opportunities to update enrollment status
      setOpportunities(ops =>
        ops.map(op =>
          op.opportunity_id === opportunityId
            ? { ...op, student_enrollment_status: 'interested' }
            : op
        )
      );
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to enroll');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <h1 className="text-4xl font-bold text-gray-900">Find Volunteer Opportunities</h1>
          <p className="mt-2 text-lg text-gray-600">
            Discover meaningful ways to contribute to your community
          </p>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Search Bar */}
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search opportunities, organizations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Filter Row */}
          <div className="flex gap-4 flex-wrap">
            <select
              value={causeFilter}
              onChange={(e) => { setCauseFilter(e.target.value); setCurrentPage(1); }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Causes</option>
              <option value="education">Education</option>
              <option value="health">Health</option>
              <option value="environment">Environment</option>
              <option value="community">Community</option>
              <option value="animals">Animals</option>
            </select>

            <select
              value={locationTypeFilter}
              onChange={(e) => { setLocationTypeFilter(e.target.value); setCurrentPage(1); }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Locations</option>
              <option value="in-person">In-Person</option>
              <option value="hybrid">Hybrid</option>
              <option value="remote">Remote</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="mt-4 text-gray-600">Loading opportunities...</p>
          </div>
        )}

        {error && (
          <div className="bg-destructive/5 border border-destructive/20 rounded-lg p-4">
            <p className="text-red-800">Error: {error}</p>
          </div>
        )}

        {!loading && filteredOpportunities.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-600 text-lg">No opportunities found. Try adjusting your filters.</p>
          </div>
        )}

        {/* Opportunities Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredOpportunities.map((opportunity) => (
            <div
              key={opportunity.opportunity_id}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6 cursor-pointer"
              onClick={() => setSelectedOpportunity(opportunity)}
            >
              {/* Header */}
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{opportunity.title}</h3>
                  <p className="text-sm text-gray-600">{opportunity.nonprofit_name}</p>
                </div>
                {opportunity.student_enrollment_status === 'interested' && (
                  <Heart className="w-5 h-5 text-red-500 fill-red-500" />
                )}
              </div>

              {/* Cause Tag */}
              <div className="mb-3">
                <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full">
                  {opportunity.cause_area}
                </span>
              </div>

              {/* Description */}
              <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                {opportunity.description}
              </p>

              {/* Details */}
              <div className="space-y-2 mb-4 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  <span>{opportunity.location_type === 'in-person' ? opportunity.location : opportunity.location_type}</span>
                </div>
                {opportunity.commitment_hours && (
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    <span>{opportunity.commitment_hours} hours commitment</span>
                  </div>
                )}
              </div>

              {/* Action Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleEnroll(opportunity.opportunity_id);
                }}
                className={`w-full py-2 px-4 rounded-lg font-medium text-sm transition-colors ${
                  opportunity.student_enrollment_status === 'interested'
                    ? 'bg-green-100 text-green-800 cursor-default'
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
                disabled={opportunity.student_enrollment_status === 'interested'}
              >
                {opportunity.student_enrollment_status === 'interested' ? 'Enrolled ✓' : 'Enroll Now'}
              </button>
            </div>
          ))}
        </div>

        {/* Pagination */}
        {pagination && pagination.pages > 1 && (
          <div className="flex justify-center gap-2 mt-12">
            {Array.from({ length: pagination.pages }).map((_, i) => (
              <button
                key={i + 1}
                onClick={() => setCurrentPage(i + 1)}
                className={`px-4 py-2 rounded-lg ${
                  currentPage === i + 1
                    ? 'bg-blue-500 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:border-blue-500'
                }`}
              >
                {i + 1}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Opportunity Detail Modal */}
      {selectedOpportunity && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <button
                onClick={() => setSelectedOpportunity(null)}
                className="float-right text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>

              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {selectedOpportunity.title}
              </h2>
              <p className="text-gray-600 mb-4">{selectedOpportunity.nonprofit_name}</p>

              <div className="space-y-3 mb-6">
                <p className="text-gray-700">{selectedOpportunity.description}</p>

                <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                  <div>
                    <span className="font-semibold text-gray-900">Cause:</span>
                    <span className="ml-2">{selectedOpportunity.cause_area}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-gray-900">Location:</span>
                    <span className="ml-2">{selectedOpportunity.location}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-gray-900">Type:</span>
                    <span className="ml-2 capitalize">{selectedOpportunity.location_type}</span>
                  </div>
                  {selectedOpportunity.commitment_hours && (
                    <div>
                      <span className="font-semibold text-gray-900">Commitment:</span>
                      <span className="ml-2">{selectedOpportunity.commitment_hours} hours</span>
                    </div>
                  )}
                </div>
              </div>

              <button
                onClick={() => {
                  handleEnroll(selectedOpportunity.opportunity_id);
                  setSelectedOpportunity(null);
                }}
                className={`w-full py-3 px-4 rounded-lg font-semibold transition-colors ${
                  selectedOpportunity.student_enrollment_status === 'interested'
                    ? 'bg-green-100 text-green-800 cursor-default'
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
                disabled={selectedOpportunity.student_enrollment_status === 'interested'}
              >
                {selectedOpportunity.student_enrollment_status === 'interested' ? 'Already Enrolled' : 'Enroll Now'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
