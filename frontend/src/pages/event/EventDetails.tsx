import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface EventData {
  id: string;
  name: string;
  description: string;
  event_date: string;
  location: string;
  organizer_name: string;
  status: string;
  donation_url: string;
  donation_enabled: boolean;
}

export default function EventDetails() {
  const { eventId } = useParams<{ eventId: string }>();
  const [event, setEvent] = useState<EventData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvent = async () => {
      try {
        const response = await fetch(`/api/events/${eventId}`);
        if (!response.ok) throw new Error('Event not found');
        const data = await response.json();
        setEvent(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load event');
      } finally {
        setLoading(false);
      }
    };

    fetchEvent();
  }, [eventId]);

  if (loading) return <div className="p-8">Loading event details...</div>;
  if (error) return <div className="p-8 text-destructive">Error: {error}</div>;
  if (!event) return <div className="p-8">Event not found</div>;

  return (
    <div className="p-8 bg-gradient-to-br from-amber-50 to-orange-50 min-h-screen">
      <div className="max-w-4xl mx-auto">
        {/* Event Header */}
        <Card className="mb-8 bg-white">
          <CardHeader>
            <div className="flex justify-between items-start mb-4">
              <div>
                <CardTitle className="text-4xl">{event.name}</CardTitle>
                <p className="text-gray-600 mt-2">{event.event_date}</p>
              </div>
              <span className={`px-4 py-2 rounded-full text-sm font-semibold ${
                event.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {event.status.toUpperCase()}
              </span>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-1">Description</h3>
              <p className="text-gray-700">{event.description || 'No description provided'}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-1">Location</h3>
              <p className="text-gray-700">{event.location || 'TBD'}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-1">Organized by</h3>
              <p className="text-gray-700">{event.organizer_name}</p>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <Button asChild variant="default" className="bg-green-600 hover:bg-green-700">
            <a href={`/event/${eventId}/register`}>Register as Volunteer</a>
          </Button>
          <Button asChild variant="outline">
            <a href={`/event/${eventId}/log-hours`}>Log Hours</a>
          </Button>
        </div>

        {/* Donation Section */}
        {event.donation_enabled && event.donation_url && (
          <Card className="bg-gradient-to-r from-red-50 to-pink-50 border-destructive/20">
            <CardHeader>
              <CardTitle className="text-2xl">Support This Event</CardTitle>
              <p className="text-gray-600 text-sm mt-2">Your donation helps make this event possible</p>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 mb-6">
                Every contribution directly supports {event.name}. All donations are tax-deductible.
              </p>
              <Button asChild className="w-full bg-red-600 hover:bg-red-700 text-white py-3 text-lg rounded-lg font-semibold">
                <a href={event.donation_url} target="_blank" rel="noopener noreferrer">
                  Donate Now
                </a>
              </Button>
              <p className="text-xs text-gray-500 mt-3 text-center">
                You will be redirected to a secure donation page
              </p>
            </CardContent>
          </Card>
        )}

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <Card>
            <CardContent className="pt-6">
              <h3 className="text-sm font-medium text-gray-600 mb-2">How It Works</h3>
              <ol className="text-sm text-gray-700 space-y-2">
                <li>1. Register as a volunteer</li>
                <li>2. Show up and volunteer</li>
                <li>3. Log your hours</li>
                <li>4. Get recognized!</li>
              </ol>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <h3 className="text-sm font-medium text-gray-600 mb-2">Quick Links</h3>
              <ul className="text-sm text-blue-600 space-y-2">
                <li><a href={`/event/${eventId}/dashboard`} className="hover:underline">View Dashboard</a></li>
                <li><a href={`/event/${eventId}/report`} className="hover:underline">View Report</a></li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <h3 className="text-sm font-medium text-gray-600 mb-2">Questions?</h3>
              <p className="text-sm text-gray-700">
                Contact the event organizer at {event.organizer_name}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
