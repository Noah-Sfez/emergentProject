import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  HomeIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  CalendarDaysIcon,
  Bars3Icon,
  XMarkIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/react/24/outline';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon, current: location.pathname === '/' },
    { name: 'Documents', href: '/documents', icon: DocumentTextIcon, current: location.pathname === '/documents' },
    { name: 'Messages', href: '/messages', icon: ChatBubbleLeftRightIcon, current: location.pathname === '/messages' },
    { name: 'Meetings', href: '/meetings', icon: CalendarDaysIcon, current: location.pathname === '/meetings' },
  ];

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <div className={`relative z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        
        <div className="fixed inset-y-0 left-0 flex w-full max-w-xs flex-col bg-white shadow-xl">
          <div className="flex h-16 items-center justify-between px-4">
            <h1 className="text-xl font-bold text-gray-900">Family Office</h1>
            <button
              type="button"
              className="-m-2 p-2 text-gray-400 hover:text-gray-500"
              onClick={() => setSidebarOpen(false)}
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          
          <nav className="flex-1 px-2 py-4">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`group flex items-center px-2 py-2 text-base font-medium rounded-md ${
                  item.current
                    ? 'bg-primary-100 text-primary-900'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="mr-4 h-6 w-6" />
                {item.name}
              </Link>
            ))}
          </nav>
          
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-center">
              <UserCircleIcon className="h-8 w-8 text-gray-400" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-gray-500">{user?.role}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="mt-3 flex items-center px-2 py-2 text-sm font-medium text-red-600 hover:text-red-900"
            >
              <ArrowRightOnRectangleIcon className="mr-2 h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex min-h-0 flex-1 flex-col bg-white border-r border-gray-200">
          <div className="flex h-16 items-center px-4 bg-primary-600">
            <h1 className="text-xl font-bold text-white">Family Office</h1>
          </div>
          
          <nav className="flex-1 px-2 py-4">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                  item.current
                    ? 'bg-primary-100 text-primary-900'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <item.icon className="mr-3 h-5 w-5" />
                {item.name}
              </Link>
            ))}
          </nav>
          
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-center">
              <UserCircleIcon className="h-8 w-8 text-gray-400" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-gray-500">{user?.role}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="mt-3 flex items-center px-2 py-2 text-sm font-medium text-red-600 hover:text-red-900"
            >
              <ArrowRightOnRectangleIcon className="mr-2 h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        <div className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 lg:px-6">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-400 hover:text-gray-500 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
          
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-500">
              Welcome back, {user?.first_name}!
            </div>
          </div>
        </div>
        
        <main className="py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;