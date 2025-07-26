import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import {
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  CalendarDaysIcon,
  UserGroupIcon,
  ClockIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const Dashboard = () => {
  const { user, API_BASE_URL } = useAuth();
  const [stats, setStats] = useState({
    documents: 0,
    messages: 0,
    meetings: 0,
    families: 0
  });
  const [recentDocuments, setRecentDocuments] = useState([]);
  const [recentMessages, setRecentMessages] = useState([]);
  const [upcomingMeetings, setUpcomingMeetings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [documentsRes, messagesRes, meetingsRes, familiesRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/documents`),
        axios.get(`${API_BASE_URL}/api/messages`),
        axios.get(`${API_BASE_URL}/api/meetings`),
        axios.get(`${API_BASE_URL}/api/families`)
      ]);

      setStats({
        documents: documentsRes.data.length,
        messages: messagesRes.data.length,
        meetings: meetingsRes.data.length,
        families: familiesRes.data.length
      });

      setRecentDocuments(documentsRes.data.slice(0, 5));
      setRecentMessages(messagesRes.data.slice(0, 5));
      setUpcomingMeetings(meetingsRes.data.slice(0, 5));
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRoleBasedWelcomeMessage = () => {
    switch (user?.role) {
      case 'admin':
        return 'System Administrator Dashboard';
      case 'family_office_admin':
        return 'Family Office Management Dashboard';
      case 'advisor':
        return 'Advisor Dashboard';
      case 'family_member':
        return 'Family Portal Dashboard';
      default:
        return 'Dashboard';
    }
  };

  const statCards = [
    {
      name: 'Documents',
      value: stats.documents,
      icon: DocumentTextIcon,
      color: 'bg-blue-500',
      href: '/documents'
    },
    {
      name: 'Messages',
      value: stats.messages,
      icon: ChatBubbleLeftRightIcon,
      color: 'bg-green-500',
      href: '/messages'
    },
    {
      name: 'Meetings',
      value: stats.meetings,
      icon: CalendarDaysIcon,
      color: 'bg-purple-500',
      href: '/meetings'
    },
    {
      name: 'Families',
      value: stats.families,
      icon: UserGroupIcon,
      color: 'bg-orange-500',
      href: '/families'
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {getRoleBasedWelcomeMessage()}
            </h1>
            <p className="text-gray-600">
              Welcome back, {user?.first_name} {user?.last_name}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Role: {user?.role}</p>
            <p className="text-sm text-gray-500">
              Last login: {new Date().toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card) => (
          <div key={card.name} className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center">
              <div className={`${card.color} rounded-md p-3`}>
                <card.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{card.name}</p>
                <p className="text-2xl font-bold text-gray-900">{card.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Documents */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Documents</h3>
          </div>
          <div className="p-6">
            {recentDocuments.length > 0 ? (
              <div className="space-y-3">
                {recentDocuments.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      <DocumentTextIcon className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{doc.original_filename}</p>
                        <p className="text-xs text-gray-500">{doc.document_type}</p>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500">
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No documents found</p>
            )}
          </div>
        </div>

        {/* Recent Messages */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Messages</h3>
          </div>
          <div className="p-6">
            {recentMessages.length > 0 ? (
              <div className="space-y-3">
                {recentMessages.map((message) => (
                  <div key={message.id} className="flex items-start p-3 bg-gray-50 rounded-lg">
                    <ChatBubbleLeftRightIcon className="h-5 w-5 text-gray-400 mr-3 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm text-gray-900">{message.content}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(message.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No messages found</p>
            )}
          </div>
        </div>

        {/* Upcoming Meetings */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Upcoming Meetings</h3>
          </div>
          <div className="p-6">
            {upcomingMeetings.length > 0 ? (
              <div className="space-y-3">
                {upcomingMeetings.map((meeting) => (
                  <div key={meeting.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      <CalendarDaysIcon className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{meeting.title}</p>
                        <p className="text-xs text-gray-500">{meeting.status}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">
                        {new Date(meeting.start_time).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(meeting.start_time).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No meetings scheduled</p>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                <DocumentTextIcon className="h-4 w-4 mr-2" />
                Upload Document
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                <ChatBubbleLeftRightIcon className="h-4 w-4 mr-2" />
                Send Message
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                <CalendarDaysIcon className="h-4 w-4 mr-2" />
                Schedule Meeting
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">System Status</h3>
            <p className="text-sm text-gray-500">All systems operational</p>
          </div>
          <div className="flex items-center">
            <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
            <span className="text-sm text-green-600">Online</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;