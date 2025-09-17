"use client";
import React, { useState, useEffect } from 'react';

interface AIActivity {
  id: string;
  timestamp: string;
  type: 'scan' | 'analyze' | 'detect' | 'decision' | 'alert' | 'process' | 'learn' | 'generate';
  platform?: string;
  action: string;
  details: string;
  status: 'running' | 'completed' | 'failed' | 'pending';
  confidence?: number;
  url?: string;
  duration?: number;
  keywords?: string[];
  language?: 'en' | 'bn' | 'both';
  learning_data?: {
    patterns: string[];
    improvements: string[];
    accuracy: number;
  };
}

interface AIAgentStats {
  totalScans: number;
  activeScans: number;
  detectionsFound: number;
  decisionsMade: number;
  alertsSent: number;
  avgConfidence: number;
  platformsActive: string[];
  keywordsGenerated: number;
  learningSessions: number;
  accuracyImprovement: number;
  languagesProcessed: string[];
}

export default function AIActivityPanel() {
  console.log('🚀 AIActivityPanel component is rendering!');
  const [activities, setActivities] = useState<AIActivity[]>([]);
  const [stats, setStats] = useState<AIAgentStats>({
    totalScans: 0,
    activeScans: 0,
    detectionsFound: 0,
    decisionsMade: 0,
    alertsSent: 0,
    avgConfidence: 0,
    platformsActive: [],
    keywordsGenerated: 0,
    learningSessions: 0,
    accuracyImprovement: 0,
    languagesProcessed: []
  });
  const [isConnected, setIsConnected] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'live' | 'timeline' | 'grid'>('live');

  const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
  const apiKey = process.env.NEXT_PUBLIC_API_KEY || 'devtoken123';

  // Real-time data fetching from API
  useEffect(() => {
    console.log('🔄 AIActivityPanel useEffect triggered - fetching data...');

    const fetchRealTimeData = async () => {
      try {
        // Fetch AI activities from API
        const activitiesResponse = await fetch(`${apiBase}/tools/ai.activities`, {
          headers: { 'X-API-Key': apiKey }
        });
        
        if (activitiesResponse.ok) {
          const activitiesData = await activitiesResponse.json();
          console.log('Raw activities response:', activitiesData);
          if (activitiesData.activities && Array.isArray(activitiesData.activities)) {
            setActivities(activitiesData.activities);
            setIsConnected(true);
            console.log('Real AI activities loaded:', activitiesData.activities.length);
          } else {
            console.error('Invalid activities data structure:', activitiesData);
          }
        } else {
          console.error('Activities response not ok:', activitiesResponse.status, activitiesResponse.statusText);
        }

        // Fetch AI stats from API
        const statsResponse = await fetch(`${apiBase}/tools/ai.stats`, {
          headers: { 'X-API-Key': apiKey }
        });
        
        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          console.log('Raw stats response:', statsData);
          setStats({
            totalScans: statsData.total_scans || 0,
            activeScans: statsData.active_scans || 0,
            detectionsFound: statsData.detections_found || 0,
            decisionsMade: statsData.decisions_made || 0,
            alertsSent: statsData.alerts_sent || 0,
            avgConfidence: statsData.avg_confidence || 0,
            platformsActive: statsData.platforms_active || [],
            keywordsGenerated: statsData.keywords_generated || 0,
            learningSessions: statsData.learning_sessions || 0,
            accuracyImprovement: statsData.accuracy_improvement || 0,
            languagesProcessed: statsData.languages_processed || []
          });
          console.log('Real AI stats loaded:', statsData);
        } else {
          console.error('Stats response not ok:', statsResponse.status, statsResponse.statusText);
        }
      } catch (error) {
        console.error('Failed to fetch real-time data:', error);
        setIsConnected(false);
      }
    };

    // Initial data fetch
    fetchRealTimeData();

    // Real-time updates every 5 seconds
    const interval = setInterval(() => {
      fetchRealTimeData();
    }, 5000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  // Update stats based on activities
  useEffect(() => {
    console.log('Activities changed, recalculating stats. Activities count:', activities.length);
    if (activities.length > 0) {
      const newStats: AIAgentStats = {
        totalScans: activities.filter(a => a.type === 'scan').length,
        activeScans: activities.filter(a => a.type === 'scan' && a.status === 'running').length,
        detectionsFound: activities.filter(a => a.type === 'detect').length,
        decisionsMade: activities.filter(a => a.type === 'decision').length,
        alertsSent: activities.filter(a => a.type === 'alert').length,
        avgConfidence: activities
          .filter(a => a.confidence !== undefined && a.confidence !== null)
          .reduce((sum, a) => sum + (a.confidence || 0), 0) / 
          Math.max(activities.filter(a => a.confidence !== undefined && a.confidence !== null).length, 1),
        platformsActive: Array.from(new Set(activities
          .filter(a => a.platform)
          .map(a => a.platform!)
        )),
        keywordsGenerated: activities.filter(a => a.keywords && a.keywords.length > 0).length,
        learningSessions: activities.filter(a => a.type === 'learn').length,
        accuracyImprovement: activities
          .filter(a => a.learning_data)
          .reduce((sum, a) => sum + (a.learning_data?.accuracy || 0), 0) / 
          Math.max(activities.filter(a => a.learning_data).length, 1),
        languagesProcessed: Array.from(new Set(activities
          .filter(a => a.language)
          .map(a => a.language!)
        ))
      };
      console.log('Calculated stats from activities:', newStats);
      console.log('Activity types found:', activities.map(a => a.type));
      console.log('Activities with keywords:', activities.filter(a => a.keywords && a.keywords.length > 0).length);
      setStats(newStats);
    } else {
      console.log('No activities available for stats calculation');
    }
  }, [activities]);

  const getStatusColor = (status: AIActivity['status']) => {
    switch (status) {
      case 'running': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'completed': return 'text-green-600 bg-green-50 border-green-200';
      case 'failed': return 'text-red-600 bg-red-50 border-red-200';
      case 'pending': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getTypeIcon = (type: AIActivity['type']) => {
    switch (type) {
      case 'scan': return '🔍';
      case 'analyze': return '🔬';
      case 'detect': return '🎯';
      case 'decision': return '🧠';
      case 'alert': return '🚨';
      case 'process': return '⚙️';
      case 'learn': return '📚';
      case 'generate': return '✨';
      default: return '📊';
    }
  };

  const getPlatformIcon = (platform?: string) => {
    switch (platform) {
      case 'youtube': return '📺';
      case 'telegram': return '📱';
      case 'facebook': return '📘';
      case 'twitter': return '🐦';
      case 'instagram': return '📷';
      case 'google': return '🔍';
      default: return '🌐';
    }
  };

  const getLanguageLabel = (language?: string) => {
    switch (language) {
      case 'en': return '🇺🇸 English';
      case 'bn': return '🇧🇩 Bengali';
      case 'both': return '🌍 Both';
      default: return '🌐 Unknown';
    }
  };

  const filteredActivities = activities.filter(activity => {
    const typeMatch = selectedFilter === 'all' || activity.type === selectedFilter;
    const languageMatch = selectedLanguage === 'all' || 
                         (selectedLanguage === 'en' && activity.language === 'en') ||
                         (selectedLanguage === 'bn' && activity.language === 'bn') ||
                         (selectedLanguage === 'both' && activity.language === 'both');
    
    // Debug logging for first few activities
    if (activities.indexOf(activity) < 3) {
      console.log('Filtering activity:', {
        id: activity.id,
        type: activity.type,
        language: activity.language,
        selectedFilter,
        selectedLanguage,
        typeMatch,
        languageMatch,
        passes: typeMatch && languageMatch
      });
    }
    
    return typeMatch && languageMatch;
  });

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* View Mode Controls */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 px-8 py-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-3 px-4 py-2 rounded-full ${isConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
              <span className="text-sm font-semibold">
                {isConnected ? 'Live' : 'Disconnected'}
              </span>
            </div>
            <div className="flex space-x-2 bg-gray-100 p-1 rounded-lg">
              <button 
                onClick={() => setViewMode('live')}
                className={`px-4 py-2 text-sm rounded-md transition-all duration-200 font-medium ${
                  viewMode === 'live' 
                    ? 'bg-white text-green-600 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                Live
              </button>
              <button 
                onClick={() => setViewMode('timeline')}
                className={`px-4 py-2 text-sm rounded-md transition-all duration-200 font-medium ${
                  viewMode === 'timeline' 
                    ? 'bg-white text-blue-600 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                Timeline
              </button>
              <button 
                onClick={() => setViewMode('grid')}
                className={`px-4 py-2 text-sm rounded-md transition-all duration-200 font-medium ${
                  viewMode === 'grid' 
                    ? 'bg-white text-blue-600 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                Grid
              </button>
            </div>
            <button 
              onClick={() => setActivities([])}
              className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all duration-200 font-medium"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Enhanced Stats Cards with Professional Design */}
      <div className="p-8">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6 mb-8">
          <div className="group bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg">
                <span className="text-white text-xl">🔍</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Total Scans</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalScans}</p>
              </div>
            </div>
          </div>

          <div className="group bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg">
                <span className="text-white text-xl">🎯</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Detections</p>
                <p className="text-2xl font-bold text-gray-900">{stats.detectionsFound}</p>
              </div>
            </div>
          </div>

          <div className="group bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg">
                <span className="text-white text-xl">🧠</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Decisions</p>
                <p className="text-2xl font-bold text-gray-900">{stats.decisionsMade}</p>
              </div>
            </div>
          </div>

          <div className="group bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl shadow-lg">
                <span className="text-white text-xl">📊</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Confidence</p>
                <p className="text-2xl font-bold text-gray-900">{stats.avgConfidence.toFixed(1)}%</p>
              </div>
            </div>
          </div>

          <div className="group bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-xl shadow-lg">
                <span className="text-white text-xl">✨</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Keywords</p>
                <p className="text-2xl font-bold text-gray-900">{stats.keywordsGenerated}</p>
              </div>
            </div>
          </div>

          <div className="group bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl shadow-lg">
                <span className="text-white text-xl">📚</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Learning</p>
                <p className="text-2xl font-bold text-gray-900">{stats.learningSessions}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Language and Platform Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <span className="mr-3 text-2xl">🌍</span>
              Languages Processed
            </h3>
            <div className="flex flex-wrap gap-3">
              {stats.languagesProcessed.map(lang => (
                <span key={lang} className="inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-md">
                  {getLanguageLabel(lang)}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <span className="mr-3 text-2xl">📱</span>
              Active Platforms
            </h3>
            <div className="flex flex-wrap gap-3">
              {stats.platformsActive.map(platform => (
                <span key={platform} className="inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold bg-gradient-to-r from-green-500 to-green-600 text-white shadow-md">
                  {getPlatformIcon(platform)} {platform}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Enhanced Filters with Professional Design */}
        <div className="bg-white/70 backdrop-blur-sm p-6 rounded-2xl shadow-lg border border-white/20 mb-8">
          <div className="flex flex-wrap gap-8">
            <div className="flex-1 min-w-0">
              <label className="block text-sm font-bold text-gray-700 mb-3 uppercase tracking-wide">Activity Type</label>
              <div className="flex flex-wrap gap-2">
                {['all', 'scan', 'analyze', 'detect', 'decision', 'alert', 'process', 'learn', 'generate'].map(filter => (
                  <button
                    key={filter}
                    onClick={() => setSelectedFilter(filter)}
                    className={`px-4 py-2 text-sm rounded-lg transition-all duration-200 font-medium ${
                      selectedFilter === filter
                        ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-md'
                    }`}
                  >
                    {filter.charAt(0).toUpperCase() + filter.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="flex-1 min-w-0">
              <label className="block text-sm font-bold text-gray-700 mb-3 uppercase tracking-wide">Language</label>
              <div className="flex flex-wrap gap-2">
                {['all', 'en', 'bn', 'both'].map(lang => (
                  <button
                    key={lang}
                    onClick={() => setSelectedLanguage(lang)}
                    className={`px-4 py-2 text-sm rounded-lg transition-all duration-200 font-medium ${
                      selectedLanguage === lang
                        ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-md'
                    }`}
                  >
                    {lang === 'all' ? 'All' : getLanguageLabel(lang)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Activity Feed with Professional Cards */}
      <div className="flex-1 overflow-hidden px-8 pb-8">
        {/* Debug Info */}
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Debug:</strong> Total Activities: {activities.length} | Filtered: {filteredActivities.length} | View Mode: {viewMode}
          </p>
          <p className="text-sm text-blue-600 mt-2">
            <strong>Last Update:</strong> {new Date().toLocaleTimeString()} | API: {apiBase} | Status: {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </p>
        </div>
        
        {filteredActivities.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-bold text-gray-700 mb-2">No Activities Found</h3>
            <p className="text-gray-500">Try adjusting your filters or check the API connection</p>
            <div className="mt-4 text-sm text-gray-400">
              <p>API Base: {apiBase}</p>
              <p>Connection Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
            </div>
          </div>
        ) : viewMode === 'live' ? (
          <div className="space-y-4">
            {filteredActivities.map((activity) => (
              <div
                key={activity.id}
                className="group bg-white/80 backdrop-blur-sm rounded-xl border border-white/20 p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
              >
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                      <span className="text-2xl">{getTypeIcon(activity.type)}</span>
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="text-lg font-bold text-gray-900">{activity.action}</h4>
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border shadow-sm ${getStatusColor(activity.status)}`}>
                        {activity.status}
                      </span>
                    </div>
                    <p className="text-gray-700 text-sm mb-3">{activity.details}</p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span className="flex items-center">
                        <span className="mr-1">🕒</span>
                        {activity.timestamp ? new Date(Number(activity.timestamp) * 1000).toLocaleTimeString() : 'N/A'}
                      </span>
                      {activity.platform && (
                        <span className="flex items-center">
                          <span className="mr-1">{getPlatformIcon(activity.platform)}</span>
                          {activity.platform}
                        </span>
                      )}
                      {activity.language && (
                        <span className="flex items-center">
                          <span className="mr-1">🌍</span>
                          {getLanguageLabel(activity.language)}
                        </span>
                      )}
                    </div>
                  </div>
                  {activity.keywords && activity.keywords.length > 0 && (
                    <div className="flex-shrink-0">
                      <div className="text-right">
                        <p className="text-xs font-bold text-gray-700 mb-2">Keywords</p>
                        <div className="flex flex-wrap gap-1 justify-end">
                          {activity.keywords.slice(0, 3).map((keyword, idx) => (
                            <span key={idx} className="text-xs bg-gradient-to-r from-yellow-400 to-yellow-500 text-white px-2 py-1 rounded-full font-medium">
                              {keyword.length > 15 ? keyword.substring(0, 15) + '...' : keyword}
                            </span>
                          ))}
                          {activity.keywords.length > 3 && (
                            <span className="text-xs text-gray-500 font-medium">+{activity.keywords.length - 3}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : viewMode === 'timeline' ? (
          <div className="space-y-6">
            {filteredActivities.map((activity) => (
              <div
                key={activity.id}
                className="group bg-white/80 backdrop-blur-sm rounded-2xl border border-white/20 p-8 hover:shadow-2xl transition-all duration-300 hover:-translate-y-1"
              >
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-start space-x-6">
                    <div className="flex-shrink-0">
                      <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300">
                        <span className="text-3xl">{getTypeIcon(activity.type)}</span>
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-4 mb-3">
                        <h4 className="text-xl font-bold text-gray-900">{activity.action}</h4>
                        {activity.platform && (
                          <span className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full font-medium">
                            {getPlatformIcon(activity.platform)} {activity.platform}
                          </span>
                        )}
                        {activity.language && (
                          <span className="text-sm text-gray-600 bg-blue-100 px-3 py-1 rounded-full font-medium">
                            {getLanguageLabel(activity.language)}
                          </span>
                        )}
                      </div>
                      <p className="text-gray-700 text-lg mb-4">{activity.details}</p>
                      
                      {/* Enhanced Keywords Section */}
                      {activity.keywords && activity.keywords.length > 0 && (
                        <div className="mb-6">
                          <h5 className="text-sm font-bold text-gray-700 mb-3 flex items-center uppercase tracking-wide">
                            <span className="mr-2 text-lg">✨</span>
                            Generated Keywords ({activity.language === 'bn' ? 'Bengali' : activity.language === 'en' ? 'English' : 'Both'})
                          </h5>
                          <div className="flex flex-wrap gap-3">
                            {activity.keywords.map((keyword, idx) => (
                              <span key={idx} className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-gradient-to-r from-yellow-400 to-yellow-500 text-white shadow-md border border-yellow-300">
                                {keyword}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Enhanced Learning Data Section */}
                      {activity.learning_data && (
                        <div className="mb-6">
                          <h5 className="text-sm font-bold text-gray-700 mb-3 flex items-center uppercase tracking-wide">
                            <span className="mr-2 text-lg">📚</span>
                            AI Learning Insights
                          </h5>
                          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-100">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                              <div>
                                <p className="text-xs font-bold text-indigo-700 uppercase tracking-wide mb-2">Patterns Learned</p>
                                <div className="flex flex-wrap gap-2">
                                  {activity.learning_data.patterns.map((pattern, idx) => (
                                    <span key={idx} className="text-xs bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full font-medium">
                                      {pattern}
                                    </span>
                                  ))}
                                </div>
                              </div>
                              <div>
                                <p className="text-xs font-bold text-indigo-700 uppercase tracking-wide mb-2">Improvements</p>
                                <div className="flex flex-wrap gap-2">
                                  {activity.learning_data.improvements.map((improvement, idx) => (
                                    <span key={idx} className="text-xs bg-green-100 text-green-800 px-3 py-1 rounded-full font-medium">
                                      {improvement}
                                    </span>
                                  ))}
                                </div>
                              </div>
                              <div>
                                <p className="text-xs font-bold text-indigo-700 uppercase tracking-wide mb-2">Accuracy</p>
                                <p className="text-3xl font-bold text-indigo-600">{activity.learning_data.accuracy.toFixed(1)}%</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {activity.url && (
                        <a 
                          href={activity.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:text-blue-800 break-all inline-block mb-4 font-medium"
                        >
                          🔗 {activity.url}
                        </a>
                      )}
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <span className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-bold border shadow-md ${getStatusColor(activity.status)}`}>
                      {activity.status}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-sm text-gray-500 border-t border-gray-100 pt-6">
                  <div className="flex items-center space-x-6">
                    <span className="flex items-center font-medium">
                      <span className="mr-2">🕒</span>
                      {activity.timestamp ? new Date(Number(activity.timestamp) * 1000).toLocaleTimeString() : 'N/A'}
                    </span>
                    {activity.confidence && (
                      <span className="flex items-center font-medium">
                        <span className="mr-2">📊</span>
                        Confidence: {activity.confidence.toFixed(1)}%
                      </span>
                    )}
                    {activity.duration && (
                      <span className="flex items-center font-medium">
                        <span className="mr-2">⚡</span>
                        Duration: {activity.duration}ms
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredActivities.map((activity) => (
              <div
                key={activity.id}
                className="group bg-white/80 backdrop-blur-sm rounded-2xl border border-white/20 p-6 hover:shadow-2xl transition-all duration-300 hover:-translate-y-2"
              >
                <div className="flex items-center space-x-4 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                    <span className="text-xl">{getTypeIcon(activity.type)}</span>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-bold text-gray-900 text-sm">{activity.action}</h4>
                    <p className="text-xs text-gray-500">{activity.platform}</p>
                  </div>
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border shadow-sm ${getStatusColor(activity.status)}`}>
                    {activity.status}
                  </span>
                </div>
                
                <p className="text-sm text-gray-700 mb-4">{activity.details}</p>
                
                {activity.keywords && activity.keywords.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Keywords:</p>
                    <div className="flex flex-wrap gap-2">
                      {activity.keywords.slice(0, 3).map((keyword, idx) => (
                        <span key={idx} className="text-xs bg-gradient-to-r from-yellow-400 to-yellow-500 text-white px-2 py-1 rounded-full font-medium">
                          {keyword}
                        </span>
                      ))}
                      {activity.keywords.length > 3 && (
                        <span className="text-xs text-gray-500 font-medium">+{activity.keywords.length - 3} more</span>
                      )}
                    </div>
                  </div>
                )}
                
                <div className="text-xs text-gray-500 font-medium">
                  {activity.timestamp ? new Date(Number(activity.timestamp) * 1000).toLocaleTimeString() : 'N/A'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
