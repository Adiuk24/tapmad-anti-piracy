"use client";
import React, { useState, useEffect } from 'react';
import Rows, { ChatPanel } from './Rows';
import AIActivityPanel from './components/AIActivityPanel';

// Client-side only timestamp component
function TimestampDisplay({ lastUpdate }: { lastUpdate: Date | null }) {
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);
  
  if (!mounted) {
    return <p className="text-sm text-gray-500">Last updated: Initializing...</p>;
  }
  
  return (
    <p className="text-sm text-gray-500">
      Last updated: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Initializing...'}
    </p>
  );
}

export default function Home() {
  const [activeTab, setActiveTab] = useState('detections');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [rows, setRows] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState('online');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
  const apiKey = process.env.NEXT_PUBLIC_API_KEY || 'devtoken123';

  // Initialize date on client side to prevent hydration issues
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setLastUpdate(new Date());
    }
  }, []);

  // Real-time data fetching
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${apiBase}/detections`, {
          headers: {
            'X-API-Key': apiKey,
          },
        });
        if (response.ok) {
          const data = await response.json();
          setRows(data.data?.detections || []);
        }
        setSystemStatus('online');
      } catch (error) {
        console.error('Failed to fetch data:', error);
        setSystemStatus('offline');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    
    // Real-time updates every 5 seconds
    const interval = setInterval(() => {
      fetchData();
      setLastUpdate(new Date());
    }, 5000);

    return () => clearInterval(interval);
  }, [apiBase, apiKey]);

  const navItems = [
    { id: 'detections', label: 'Detections', icon: '🔍', count: rows.length },
    { id: 'chat', label: 'AI Agent', icon: '🤖' },
    { id: 'ai-activity', label: 'AI Activity', icon: '🧠' },
    { id: 'monitoring', label: 'Monitoring', icon: '📡' },
    { id: 'analytics', label: 'Analytics', icon: '📊' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ];

  const getSystemStatusColor = () => {
    return systemStatus === 'online' ? 'text-green-600' : 'text-red-600';
  };

  const getSystemStatusBg = () => {
    return systemStatus === 'online' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200';
  };

  return (
    <div className="h-screen flex bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Enhanced Collapsible Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-white/90 backdrop-blur-sm border-r border-gray-200/50 flex flex-col transition-all duration-300 ease-in-out shadow-lg`}>
        {/* Enhanced Header with Collapse Toggle */}
        <div className="p-4 border-b border-gray-200/50">
          <div className="flex items-center justify-between">
            <div className={`flex items-center space-x-3 ${sidebarCollapsed ? 'justify-center' : ''}`}>
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-lg tracking-wide">t</span>
              </div>
              {!sidebarCollapsed && (
                <div>
                  <h1 className="text-lg font-bold text-gray-900">Tapmad</h1>
                  <p className="text-xs text-gray-500 font-medium">Anti-Piracy System</p>
                </div>
              )}
            </div>
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className={`p-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-all duration-200 ${sidebarCollapsed ? 'mx-auto' : ''}`}
            >
              <svg 
                className={`w-4 h-4 text-gray-600 transition-transform duration-300 ${sidebarCollapsed ? 'rotate-180' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          </div>
        </div>

        {/* Enhanced Navigation */}
        <nav className="flex-1 p-3">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => {
                    console.log('Tab clicked:', item.id);
                    setActiveTab(item.id);
                  }}
                  className={`w-full flex items-center justify-between px-3 py-3 rounded-xl text-left transition-all duration-200 font-medium ${
                    activeTab === item.id
                      ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg'
                      : 'text-gray-700 hover:bg-gray-50 hover:shadow-md'
                  } ${sidebarCollapsed ? 'justify-center' : ''}`}
                >
                  <div className={`flex items-center space-x-3 ${sidebarCollapsed ? 'justify-center' : ''}`}>
                    <span className="text-lg">{item.icon}</span>
                    {!sidebarCollapsed && <span className="font-semibold">{item.label}</span>}
                  </div>
                  {!sidebarCollapsed && item.count !== undefined && (
                    <span className={`text-xs px-2 py-1 rounded-full font-bold ${
                      activeTab === item.id 
                        ? 'bg-white/20 text-white' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {item.count}
                    </span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* Enhanced System Status */}
        <div className="p-3 border-t border-gray-200/50">
          <div className={`rounded-xl p-3 ${getSystemStatusBg()} border`}>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${systemStatus === 'online' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
              {!sidebarCollapsed && (
                <span className={`text-sm font-bold ${getSystemStatusColor()}`}>
                  System {systemStatus === 'online' ? 'Online' : 'Offline'}
                </span>
              )}
            </div>
            {!sidebarCollapsed && (
              <p className="text-xs text-gray-600 mt-1 font-medium">
                Last update: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Initializing...'}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Enhanced Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Enhanced Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 px-8 py-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 capitalize flex items-center">
                <span className="mr-4 text-4xl">
                  {activeTab === 'detections' && '🔍'}
                  {activeTab === 'chat' && '🤖'}
                  {activeTab === 'ai-activity' && '🧠'}
                  {activeTab === 'monitoring' && '📡'}
                  {activeTab === 'analytics' && '📊'}
                  {activeTab === 'settings' && '⚙️'}
                </span>
                {activeTab === 'detections' && 'Content Detections'}
                {activeTab === 'chat' && 'AI Agent Chat'}
                {activeTab === 'ai-activity' && 'AI Agent Activity'}
                {activeTab === 'monitoring' && 'System Monitoring'}
                {activeTab === 'analytics' && 'Analytics Dashboard'}
                {activeTab === 'settings' && 'System Settings'}
              </h2>
              <p className="text-sm text-gray-600 mt-2 font-medium">
                {activeTab === 'detections' && 'Monitor and manage detected pirated content'}
                {activeTab === 'chat' && 'Interact with the AI agent for content analysis'}
                {activeTab === 'ai-activity' && 'Real-time monitoring of AI agent activities, learning, and keyword generation'}
                {activeTab === 'monitoring' && 'System health, platform activity, and alerts'}
                {activeTab === 'analytics' && 'Comprehensive analytics and reporting'}
                {activeTab === 'settings' && 'Configure system settings and preferences'}
              </p>
            </div>
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-3 px-4 py-2 rounded-full bg-green-100 text-green-700">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-semibold">Live</span>
              </div>
              <button 
                onClick={() => window.location.reload()}
                className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl hover:from-green-600 hover:to-green-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl"
              >
                Refresh
              </button>
            </div>
          </div>
        </header>

        {/* Enhanced Main Content */}
        <main className="flex-1 overflow-hidden">
          <div className="h-full flex">
            {activeTab === 'detections' && (
              <div className="flex-1 p-8 overflow-auto">
                {isLoading ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
                      <p className="text-lg text-gray-600 font-medium">Loading detections...</p>
                      <p className="text-sm text-gray-500 mt-2">Fetching real-time data</p>
                    </div>
                  </div>
                ) : (
                  <Rows rows={rows} />
                )}
              </div>
            )}

            {activeTab === 'chat' && (
              <div className="flex-1 h-full">
                <ChatPanel />
              </div>
            )}

            {activeTab === 'ai-activity' && (
              <div className="flex-1 h-full">
                <AIActivityPanel />
              </div>
            )}

            {activeTab === 'monitoring' && (
              <div className="flex-1 p-8 overflow-auto">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                    <div className="flex items-center">
                      <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg">
                        <span className="text-white text-xl">🖥️</span>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">API Status</p>
                        <p className="text-2xl font-bold text-gray-900">Online</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                    <div className="flex items-center">
                      <div className="p-3 bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg">
                        <span className="text-white text-xl">🗄️</span>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Database</p>
                        <p className="text-2xl font-bold text-gray-900">Connected</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                    <div className="flex items-center">
                      <div className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg">
                        <span className="text-white text-xl">🧠</span>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">LLM Service</p>
                        <p className="text-2xl font-bold text-gray-900">Active</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                    <div className="flex items-center">
                      <div className="p-3 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl shadow-lg">
                        <span className="text-white text-xl">📡</span>
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Redis Cache</p>
                        <p className="text-2xl font-bold text-gray-900">Connected</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                    <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                      <span className="mr-3 text-2xl">📱</span>
                      Platform Activity
                    </h3>
                    <div className="space-y-3">
                      {['YouTube', 'Telegram', 'Facebook', 'Twitter', 'Instagram', 'Google Search'].map((platform) => (
                        <div key={platform} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <span className="font-medium text-gray-700">{platform}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            <span className="text-sm text-green-600 font-semibold">Active</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                    <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                      <span className="mr-3 text-2xl">🚨</span>
                      Recent Alerts
                    </h3>
                    <div className="space-y-3">
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm font-medium text-red-800">High confidence detection found</p>
                        <p className="text-xs text-red-600 mt-1">2 minutes ago</p>
                      </div>
                      <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <p className="text-sm font-medium text-yellow-800">Processing queue backlog</p>
                        <p className="text-xs text-yellow-600 mt-1">5 minutes ago</p>
                      </div>
                      <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                        <p className="text-sm font-medium text-green-800">System health check passed</p>
                        <p className="text-xs text-green-600 mt-1">10 minutes ago</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'analytics' && (
              <div className="flex-1 p-8 overflow-auto">
                <div className="bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 min-h-full rounded-2xl p-8">
                  {/* Header */}
                  <div className="mb-8">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                          <span className="mr-4 text-4xl">📊</span>
                          Analytics Dashboard
                        </h1>
                        <p className="text-gray-600 mt-2">Comprehensive insights and performance metrics</p>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-3 px-4 py-2 rounded-full bg-green-100 text-green-700">
                          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                          <span className="text-sm font-semibold">Live</span>
                        </div>
                        <button 
                          onClick={() => window.location.reload()}
                          className="px-6 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg hover:from-green-600 hover:to-green-700 transition-all duration-200 font-semibold"
                        >
                          Refresh
                        </button>
                      </div>
                    </div>
                    <TimestampDisplay lastUpdate={lastUpdate} />
                  </div>

                  {/* Key Metrics Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300">
                      <div className="flex items-center">
                        <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg">
                          <span className="text-white text-xl">🔍</span>
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Total Detections</p>
                          <p className="text-2xl font-bold text-gray-900">{rows.length}</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300">
                      <div className="flex items-center">
                        <div className="p-3 bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg">
                          <span className="text-white text-xl">✅</span>
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Approved</p>
                          <p className="text-2xl font-bold text-gray-900">{rows.filter(r => r.decision === 'approve').length}</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300">
                      <div className="flex items-center">
                        <div className="p-3 bg-gradient-to-br from-red-500 to-red-600 rounded-xl shadow-lg">
                          <span className="text-white text-xl">❌</span>
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Rejected</p>
                          <p className="text-2xl font-bold text-gray-900">{rows.filter(r => r.decision === 'reject').length}</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300">
                      <div className="flex items-center">
                        <div className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg">
                          <span className="text-white text-xl">⚡</span>
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Success Rate</p>
                          <p className="text-2xl font-bold text-gray-900">95.2%</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Platform Distribution */}
                  <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20 mb-8">
                    <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                      <span className="mr-3 text-2xl">📱</span>
                      Platform Distribution
                    </h3>
                    <div className="space-y-3">
                      {['youtube', 'telegram', 'facebook', 'twitter', 'instagram', 'google'].map(platform => {
                        const count = rows.filter(r => r.platform === platform).length;
                        const percentage = rows.length > 0 ? (count / rows.length) * 100 : 0;
                        return (
                          <div key={platform} className="flex items-center justify-between">
                            <div className="flex items-center">
                              <span className="w-4 h-4 bg-gradient-to-r from-green-400 to-blue-500 rounded mr-3"></span>
                              <span className="font-medium text-gray-700 capitalize">{platform}</span>
                            </div>
                            <div className="flex items-center space-x-3">
                              <div className="w-32 bg-gray-200 rounded-full h-2">
                                <div 
                                  className="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full" 
                                  style={{ width: `${percentage}%` }}
                                ></div>
                              </div>
                              <span className="text-sm text-gray-500 w-12 text-right">{count}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Additional Metrics */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Top Keywords */}
                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                        <span className="mr-3 text-2xl">🔑</span>
                        Top Keywords
                      </h3>
                      <div className="space-y-3">
                        {[
                          { keyword: 'live cricket streaming', count: 45, language: 'en' },
                          { keyword: 'ট্যাপম্যাড লাইভ', count: 32, language: 'bn' },
                          { keyword: 'sports highlights', count: 28, language: 'en' },
                          { keyword: 'ফুটবল ম্যাচ লাইভ', count: 25, language: 'bn' },
                          { keyword: 'match replay', count: 22, language: 'en' }
                        ].map((keyword, index) => (
                          <div key={index} className="flex items-center justify-between">
                            <div className="flex items-center">
                              <span className="text-sm font-medium text-gray-700">{keyword.keyword}</span>
                              <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                                keyword.language === 'en' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
                              }`}>
                                {keyword.language.toUpperCase()}
                              </span>
                            </div>
                            <span className="text-sm font-bold text-gray-900">{keyword.count}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* System Performance */}
                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                        <span className="mr-3 text-2xl">⚙️</span>
                        System Performance
                      </h3>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-700">Avg Response Time</span>
                          <span className="text-sm font-bold text-gray-900">2.5s</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-700">Success Rate</span>
                          <span className="text-sm font-bold text-green-600">95.2%</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-700">Active Scans</span>
                          <span className="text-sm font-bold text-blue-600">3</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-700">Total Scans</span>
                          <span className="text-sm font-bold text-gray-900">156</span>
                        </div>
                      </div>
                    </div>

                    {/* Detection Status */}
                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                        <span className="mr-3 text-2xl">📊</span>
                        Detection Status
                      </h3>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-700">High Confidence</span>
                          <span className="text-sm font-bold text-green-600">12</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-700">Medium Confidence</span>
                          <span className="text-sm font-bold text-yellow-600">8</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-700">Low Confidence</span>
                          <span className="text-sm font-bold text-red-600">3</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="flex-1 p-8 overflow-auto">
                {console.log('Rendering settings page, activeTab:', activeTab)}
                <div className="max-w-4xl mx-auto">
                  {/* Header */}
                  <div className="mb-8">
                    <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                      <span className="mr-4 text-4xl">⚙️</span>
                      System Settings
                    </h2>
                    <p className="text-sm text-gray-600 mt-2 font-medium">Configure system settings and preferences</p>
                  </div>

                  {/* Settings Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    
                    {/* API Configuration */}
                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                        <span className="mr-3 text-2xl">🔗</span>
                        API Configuration
                      </h3>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">API Base URL</label>
                          <input 
                            type="text" 
                            value="http://localhost:8000" 
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            readOnly
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
                          <input 
                            type="password" 
                            value="devtoken123" 
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            readOnly
                          />
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                          <span className="text-sm text-green-600 font-medium">API Connection Active</span>
                        </div>
                      </div>
                    </div>

                    {/* Scanning Settings */}
                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                        <span className="mr-3 text-2xl">🔍</span>
                        Scanning Settings
                      </h3>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Max Candidates Per Scan</label>
                          <input 
                            type="number" 
                            value="20" 
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Scan Timeout (seconds)</label>
                          <input 
                            type="number" 
                            value="300" 
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                          />
                        </div>
                        <div className="flex items-center">
                          <input type="checkbox" id="auto-enforcement" className="mr-3" />
                          <label htmlFor="auto-enforcement" className="text-sm font-medium text-gray-700">
                            Enable Auto Enforcement
                          </label>
                        </div>
                      </div>
                    </div>

                    {/* Platform Settings */}
                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                        <span className="mr-3 text-2xl">📱</span>
                        Platform Settings
                      </h3>
                      <div className="space-y-3">
                        {['YouTube', 'Telegram', 'Facebook', 'Twitter', 'Instagram', 'Google Search'].map((platform) => (
                          <div key={platform} className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-700">{platform}</span>
                            <div className="flex items-center space-x-2">
                              <input type="checkbox" defaultChecked className="mr-2" />
                              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Notification Settings */}
                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                        <span className="mr-3 text-2xl">🔔</span>
                        Notification Settings
                      </h3>
                      <div className="space-y-4">
                        <div className="flex items-center">
                          <input type="checkbox" id="high-confidence" defaultChecked className="mr-3" />
                          <label htmlFor="high-confidence" className="text-sm font-medium text-gray-700">
                            High Confidence Detections
                          </label>
                        </div>
                        <div className="flex items-center">
                          <input type="checkbox" id="system-alerts" defaultChecked className="mr-3" />
                          <label htmlFor="system-alerts" className="text-sm font-medium text-gray-700">
                            System Health Alerts
                          </label>
                        </div>
                        <div className="flex items-center">
                          <input type="checkbox" id="processing-backlog" className="mr-3" />
                          <label htmlFor="processing-backlog" className="text-sm font-medium text-gray-700">
                            Processing Backlog Alerts
                          </label>
                        </div>
                        <div className="flex items-center">
                          <input type="checkbox" id="platform-activity" defaultChecked className="mr-3" />
                          <label htmlFor="platform-activity" className="text-sm font-medium text-gray-700">
                            New Platform Activity
                          </label>
                        </div>
                      </div>
                    </div>

                    {/* Language Settings */}
                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                        <span className="mr-3 text-2xl">🌍</span>
                        Language Settings
                      </h3>
                      <div className="space-y-4">
                        <div className="flex items-center">
                          <input type="checkbox" id="english" defaultChecked className="mr-3" />
                          <label htmlFor="english" className="text-sm font-medium text-gray-700">English</label>
                        </div>
                        <div className="flex items-center">
                          <input type="checkbox" id="bengali" defaultChecked className="mr-3" />
                          <label htmlFor="bengali" className="text-sm font-medium text-gray-700">Bengali (বাংলা)</label>
                        </div>
                        <div className="flex items-center">
                          <input type="checkbox" id="auto-detect" defaultChecked className="mr-3" />
                          <label htmlFor="auto-detect" className="text-sm font-medium text-gray-700">Auto-detect Language</label>
                        </div>
                      </div>
                    </div>

                    {/* System Information */}
                    <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
                      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                        <span className="mr-3 text-2xl">ℹ️</span>
                        System Information
                      </h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-sm font-medium text-gray-700">Version</span>
                          <span className="text-sm text-gray-900">1.0.0</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm font-medium text-gray-700">Last Updated</span>
                          <span className="text-sm text-gray-900">Today</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm font-medium text-gray-700">Status</span>
                          <span className="text-sm text-green-600 font-medium">Online</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm font-medium text-gray-700">Uptime</span>
                          <span className="text-sm text-gray-900">2 days, 14 hours</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="mt-8 flex justify-end space-x-4">
                    <button className="px-6 py-3 bg-gray-500 text-white rounded-xl hover:bg-gray-600 transition-all duration-200 font-semibold">
                      Reset to Defaults
                    </button>
                    <button className="px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl hover:from-green-600 hover:to-green-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl">
                      Save Settings
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
