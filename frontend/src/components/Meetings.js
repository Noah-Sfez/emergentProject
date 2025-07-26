import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  CalendarDaysIcon,
  PlusIcon,
  ClockIcon,
  UserGroupIcon,
  VideoCameraIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const Meetings = () => {
  const { user, API_BASE_URL } = useAuth();
  const [meetings, setMeetings] = useState([]);
  const [families, setFamilies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewMeetingModal, setShowNewMeetingModal] = useState(false);
  const [newMeeting, setNewMeeting] = useState({
    title: '',
    description: '',
    start_time: '',
    end_time: '',
    family_id: '',
    advisor_id: user?.id || '',
    meeting_link: ''
  });

  useEffect(() => {
    fetchMeetings();
    fetchFamilies();
  }, []);

  const fetchMeetings = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/meetings`);
      setMeetings(response.data);
    } catch (error) {
      console.error('Error fetching meetings:', error);
      toast.error('Failed to fetch meetings');
    } finally {
      setLoading(false);
    }
  };

  const fetchFamilies = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/families`);
      setFamilies(response.data);
    } catch (error) {
      console.error('Error fetching families:', error);
    }
  };

  const createMeeting = async (e) => {
    e.preventDefault();
    if (!newMeeting.title || !newMeeting.start_time || !newMeeting.end_time || !newMeeting.family_id) {
      toast.error('Please fill all required fields');
      return;
    }

    try {
      await axios.post(`${API_BASE_URL}/api/meetings`, {
        ...newMeeting,
        start_time: new Date(newMeeting.start_time).toISOString(),
        end_time: new Date(newMeeting.end_time).toISOString()
      });
      
      toast.success('Meeting scheduled successfully');
      setNewMeeting({
        title: '',
        description: '',
        start_time: '',
        end_time: '',
        family_id: '',
        advisor_id: user?.id || '',
        meeting_link: ''
      });
      setShowNewMeetingModal(false);
      fetchMeetings();
    } catch (error) {
      console.error('Error creating meeting:', error);
      toast.error('Failed to create meeting');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'scheduled':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      case 'confirmed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-blue-500" />;
      case 'cancelled':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ExclamationTriangleIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    switch (status) {
      case 'scheduled':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'confirmed':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'completed':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'cancelled':
        return `${baseClasses} bg-red-100 text-red-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const isUpcoming = (startTime) => {
    return new Date(startTime) > new Date();
  };

  const upcomingMeetings = meetings.filter(meeting => isUpcoming(meeting.start_time));
  const pastMeetings = meetings.filter(meeting => !isUpcoming(meeting.start_time));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Meetings</h1>
          <p className="text-gray-600">Schedule and manage your meetings</p>
        </div>
        <button
          onClick={() => setShowNewMeetingModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Schedule Meeting
        </button>
      </div>

      {/* Upcoming Meetings */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Upcoming Meetings ({upcomingMeetings.length})
          </h3>
        </div>
        <div className="divide-y divide-gray-200">
          {upcomingMeetings.length > 0 ? (
            upcomingMeetings.map((meeting) => (
              <div key={meeting.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <CalendarDaysIcon className="h-10 w-10 text-gray-400 mr-4" />
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{meeting.title}</h4>
                      <p className="text-sm text-gray-500">{meeting.description}</p>
                      <div className="flex items-center mt-2 space-x-4">
                        <div className="flex items-center text-xs text-gray-500">
                          <ClockIcon className="h-4 w-4 mr-1" />
                          {new Date(meeting.start_time).toLocaleDateString()} at{' '}
                          {new Date(meeting.start_time).toLocaleTimeString()}
                        </div>
                        <div className="flex items-center text-xs text-gray-500">
                          <UserGroupIcon className="h-4 w-4 mr-1" />
                          {meeting.attendees.length} attendees
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={getStatusBadge(meeting.status)}>
                      {meeting.status}
                    </span>
                    {meeting.meeting_link && (
                      <a
                        href={meeting.meeting_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                      >
                        <VideoCameraIcon className="h-4 w-4 mr-1" />
                        Join
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="p-6 text-center">
              <CalendarDaysIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No upcoming meetings</p>
            </div>
          )}
        </div>
      </div>

      {/* Past Meetings */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Past Meetings ({pastMeetings.length})
          </h3>
        </div>
        <div className="divide-y divide-gray-200">
          {pastMeetings.length > 0 ? (
            pastMeetings.map((meeting) => (
              <div key={meeting.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <CalendarDaysIcon className="h-10 w-10 text-gray-400 mr-4" />
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{meeting.title}</h4>
                      <p className="text-sm text-gray-500">{meeting.description}</p>
                      <div className="flex items-center mt-2 space-x-4">
                        <div className="flex items-center text-xs text-gray-500">
                          <ClockIcon className="h-4 w-4 mr-1" />
                          {new Date(meeting.start_time).toLocaleDateString()} at{' '}
                          {new Date(meeting.start_time).toLocaleTimeString()}
                        </div>
                        {meeting.notes && (
                          <div className="text-xs text-gray-500">
                            Notes available
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={getStatusBadge(meeting.status)}>
                      {meeting.status}
                    </span>
                    {getStatusIcon(meeting.status)}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="p-6 text-center">
              <CalendarDaysIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No past meetings</p>
            </div>
          )}
        </div>
      </div>

      {/* New Meeting Modal */}
      {showNewMeetingModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Schedule New Meeting</h3>
            <form onSubmit={createMeeting} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  value={newMeeting.title}
                  onChange={(e) => setNewMeeting({...newMeeting, title: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={newMeeting.description}
                  onChange={(e) => setNewMeeting({...newMeeting, description: e.target.value})}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Family *
                </label>
                <select
                  value={newMeeting.family_id}
                  onChange={(e) => setNewMeeting({...newMeeting, family_id: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                >
                  <option value="">Select Family</option>
                  {families.map(family => (
                    <option key={family.id} value={family.id}>{family.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start Time *
                  </label>
                  <input
                    type="datetime-local"
                    value={newMeeting.start_time}
                    onChange={(e) => setNewMeeting({...newMeeting, start_time: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Time *
                  </label>
                  <input
                    type="datetime-local"
                    value={newMeeting.end_time}
                    onChange={(e) => setNewMeeting({...newMeeting, end_time: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Meeting Link
                </label>
                <input
                  type="url"
                  value={newMeeting.meeting_link}
                  onChange={(e) => setNewMeeting({...newMeeting, meeting_link: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="https://zoom.us/j/..."
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowNewMeetingModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
                >
                  Schedule Meeting
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Meetings;