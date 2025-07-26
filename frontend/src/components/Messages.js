import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  UserCircleIcon,
  PlusIcon
} from '@heroicons/react/24/outline';

const Messages = () => {
  const { user, API_BASE_URL } = useAuth();
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [families, setFamilies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newMessage, setNewMessage] = useState('');
  const [selectedRecipient, setSelectedRecipient] = useState('');
  const [selectedFamily, setSelectedFamily] = useState('');
  const [showNewMessageModal, setShowNewMessageModal] = useState(false);

  useEffect(() => {
    fetchMessages();
    fetchUsers();
    fetchFamilies();
  }, []);

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
      toast.error('Failed to fetch messages');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      // We need to create an endpoint to get users for messaging
      // For now, we'll use an empty array
      setUsers([]);
    } catch (error) {
      console.error('Error fetching users:', error);
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

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedRecipient || !selectedFamily) {
      toast.error('Please fill all fields');
      return;
    }

    try {
      await axios.post(`${API_BASE_URL}/api/messages`, {
        content: newMessage,
        recipient_id: selectedRecipient,
        family_id: selectedFamily
      });
      
      toast.success('Message sent successfully');
      setNewMessage('');
      setSelectedRecipient('');
      setSelectedFamily('');
      setShowNewMessageModal(false);
      fetchMessages();
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message');
    }
  };

  const groupMessagesByConversation = (messages) => {
    const grouped = {};
    messages.forEach(message => {
      const conversationKey = [message.sender_id, message.recipient_id].sort().join('-');
      if (!grouped[conversationKey]) {
        grouped[conversationKey] = [];
      }
      grouped[conversationKey].push(message);
    });
    return grouped;
  };

  const groupedMessages = groupMessagesByConversation(messages);

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
          <h1 className="text-2xl font-bold text-gray-900">Messages</h1>
          <p className="text-gray-600">Secure communication with your family office</p>
        </div>
        <button
          onClick={() => setShowNewMessageModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          New Message
        </button>
      </div>

      {/* Messages List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Conversations ({Object.keys(groupedMessages).length})
          </h3>
        </div>
        <div className="divide-y divide-gray-200">
          {Object.keys(groupedMessages).length > 0 ? (
            Object.values(groupedMessages).map((conversation, index) => {
              const latestMessage = conversation[conversation.length - 1];
              const isCurrentUserSender = latestMessage.sender_id === user.id;
              
              return (
                <div key={index} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <UserCircleIcon className="h-10 w-10 text-gray-400 mr-4" />
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">
                          {isCurrentUserSender ? 'To User' : 'From User'}
                        </h4>
                        <p className="text-sm text-gray-500 mt-1">
                          {latestMessage.content}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(latestMessage.created_at).toLocaleDateString()} at{' '}
                          {new Date(latestMessage.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500">
                        {conversation.length} message{conversation.length > 1 ? 's' : ''}
                      </span>
                      {!latestMessage.is_read && !isCurrentUserSender && (
                        <div className="h-2 w-2 bg-primary-500 rounded-full"></div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="p-6 text-center">
              <ChatBubbleLeftRightIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No messages found</p>
              <p className="text-sm text-gray-400 mt-2">
                Start a conversation by clicking "New Message"
              </p>
            </div>
          )}
        </div>
      </div>

      {/* All Messages */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">All Messages</h3>
        </div>
        <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
          {messages.map((message) => (
            <div key={message.id} className="p-4">
              <div className={`flex ${message.sender_id === user.id ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.sender_id === user.id
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}>
                  <p className="text-sm">{message.content}</p>
                  <p className={`text-xs mt-1 ${
                    message.sender_id === user.id ? 'text-primary-100' : 'text-gray-500'
                  }`}>
                    {new Date(message.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* New Message Modal */}
      {showNewMessageModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Send New Message</h3>
            <form onSubmit={sendMessage} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Family
                </label>
                <select
                  value={selectedFamily}
                  onChange={(e) => setSelectedFamily(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                >
                  <option value="">Select Family</option>
                  {families.map(family => (
                    <option key={family.id} value={family.id}>{family.name}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Recipient
                </label>
                <input
                  type="text"
                  value={selectedRecipient}
                  onChange={(e) => setSelectedRecipient(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Enter recipient ID"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Message
                </label>
                <textarea
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Type your message..."
                  required
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowNewMessageModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
                >
                  <PaperAirplaneIcon className="h-4 w-4 mr-2" />
                  Send
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Messages;