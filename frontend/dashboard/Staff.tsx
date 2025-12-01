import React, { useState, useEffect } from 'react';
import { Bell, Package, CheckCircle, Clock, User, Barcode as BarcodeIcon, RefreshCw } from 'lucide-react';
import io from 'socket.io-client';

export default function StaffDashboard() {
  const [collections, setCollections] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const API_URL = 'http://localhost:8000';

  useEffect(() => {
    fetchCollections();
    
    const socket = io(API_URL);
    
    socket.on('connect', () => {
      console.log('Connected to notification server');
      setConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from server');
      setConnected(false);
    });

    socket.on('new_collection', (data) => {
      console.log('New collection notification:', data);
      
      const notification = {
        id: Date.now(),
        type: 'new',
        message: `${data.customer_name} is waiting for collection`,
        data: data,
        timestamp: new Date().toISOString()
      };
      
      setNotifications(prev => [notification, ...prev].slice(0, 10));
      
      playNotificationSound();
      
      fetchCollections();
    });

    socket.on('collection_completed', (data) => {
      console.log('Collection completed:', data);
      fetchCollections();
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const fetchCollections = async () => {
    try {
      const response = await fetch(`${API_URL}/api/collections`);
      const data = await response.json();
      setCollections(data.collections || []);
    } catch (err) {
      console.error('Failed to fetch collections:', err);
    } finally {
      setLoading(false);
    }
  };

  const playNotificationSound = () => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.3);
  };

  const completeCollection = async (id) => {
    try {
      const response = await fetch(`${API_URL}/api/collections/${id}/complete`, {
        method: 'PATCH'
      });
      
      if (response.ok) {
        fetchCollections();
      }
    } catch (err) {
      console.error('Failed to complete collection:', err);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-700';
      case 'ready':
        return 'bg-green-100 text-green-700';
      case 'collected':
        return 'bg-gray-100 text-gray-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const filteredCollections = collections.filter(c => {
    if (filter === 'pending') return c.status === 'ready';
    if (filter === 'completed') return c.status === 'collected';
    return true;
  });

  const pendingCount = collections.filter(c => c.status === 'ready').length;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
                <Package className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Staff Dashboard</h1>
                <p className="text-sm text-gray-600">M&S Click & Collect</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${connected ? 'bg-green-50' : 'bg-red-50'}`}>
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
                <span className={`text-sm font-medium ${connected ? 'text-green-700' : 'text-red-700'}`}>
                  {connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              <button
                onClick={fetchCollections}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Refresh"
              >
                <RefreshCw className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Waiting</p>
                <p className="text-3xl font-bold text-green-600">{pendingCount}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <Clock className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Completed Today</p>
                <p className="text-3xl font-bold text-gray-900">
                  {collections.filter(c => c.status === 'collected').length}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Orders</p>
                <p className="text-3xl font-bold text-gray-900">{collections.length}</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Package className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>
        </div>

        {notifications.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <Bell className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-blue-900 mb-2">Recent Notifications</h3>
                <div className="space-y-2">
                  {notifications.slice(0, 3).map(notif => (
                    <div key={notif.id} className="text-sm text-blue-800">
                      🔔 {notif.message}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Collections Queue</h2>
              <div className="flex gap-2">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-3 py-1 rounded text-sm font-medium ${
                    filter === 'all' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  All ({collections.length})
                </button>
                <button
                  onClick={() => setFilter('pending')}
                  className={`px-3 py-1 rounded text-sm font-medium ${
                    filter === 'pending' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700'
                  }`}
                >