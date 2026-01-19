import React, { useState, useEffect } from 'react';
import { Database, RefreshCw, TrendingUp, AlertTriangle, Plus, Clock } from 'lucide-react';
import { getConnections } from '../services/api';
import {
  getIndexRecommendations,
  getUnusedIndexes,
  getMissingIndexes,
  getIndexStatistics,
  getIndexHistory,
  analyzeIndexUsage,
  IndexRecommendation,
  IndexStatistics,
} from '../services/indexes';
import IndexCard from '../components/Indexes/IndexCard';
import type { Connection } from '../types';

type TabType = 'recommendations' | 'unused' | 'missing' | 'history';

const IndexManagement: React.FC = () => {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('recommendations');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [recommendations, setRecommendations] = useState<IndexRecommendation[]>([]);
  const [unusedIndexes, setUnusedIndexes] = useState<any>(null);
  const [missingIndexes, setMissingIndexes] = useState<any>(null);
  const [statistics, setStatistics] = useState<IndexStatistics | null>(null);
  const [history, setHistory] = useState<any>(null);

  // Load connections on mount
  useEffect(() => {
    loadConnections();
  }, []);

  // Load data when connection changes
  useEffect(() => {
    if (selectedConnection) {
      loadAllData();
    }
  }, [selectedConnection]);

  const loadConnections = async () => {
    try {
      const data = await getConnections();
      setConnections(data);
      if (data.length > 0 && !selectedConnection) {
        setSelectedConnection(data[0].id);
      }
    } catch (err: any) {
      setError('Failed to load connections');
      console.error(err);
    }
  };

  const loadAllData = async () => {
    if (!selectedConnection) return;

    setLoading(true);
    setError(null);

    try {
      const [recsData, statsData, unusedData, missingData, historyData] = await Promise.all([
        getIndexRecommendations(selectedConnection),
        getIndexStatistics(selectedConnection),
        getUnusedIndexes(selectedConnection),
        getMissingIndexes(selectedConnection),
        getIndexHistory(selectedConnection),
      ]);

      setRecommendations(recsData);
      setStatistics(statsData);
      setUnusedIndexes(unusedData);
      setMissingIndexes(missingData);
      setHistory(historyData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load index data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedConnection) return;

    setAnalyzing(true);
    setError(null);

    try {
      await analyzeIndexUsage(selectedConnection);
      await loadAllData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze indexes');
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRefresh = () => {
    loadAllData();
  };

  const formatBytes = (bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(2)} ${units[unitIndex]}`;
  };

  const renderStatistics = () => {
    if (!statistics) return null;

    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Total Indexes</p>
              <p className="text-3xl font-bold text-gray-900">{statistics.total_indexes}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Database className="w-8 h-8 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Unused Indexes</p>
              <p className="text-3xl font-bold text-orange-600">{statistics.unused_count}</p>
            </div>
            <div className="p-3 bg-orange-100 rounded-lg">
              <AlertTriangle className="w-8 h-8 text-orange-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Missing Indexes</p>
              <p className="text-3xl font-bold text-red-600">
                {missingIndexes?.missing_count || 0}
              </p>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <Plus className="w-8 h-8 text-red-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Total Size</p>
              <p className="text-2xl font-bold text-purple-600">{statistics.total_size}</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <TrendingUp className="w-8 h-8 text-purple-600" />
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderRecommendations = () => {
    if (recommendations.length === 0) {
      return (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <Database className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Recommendations</h3>
          <p className="text-gray-600">
            No index recommendations available for this connection.
          </p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {recommendations.map((rec) => (
          <IndexCard
            key={rec.id}
            recommendation={rec}
            onApply={handleRefresh}
            onReject={handleRefresh}
          />
        ))}
      </div>
    );
  };

  const renderUnusedIndexes = () => {
    const unusedList = Array.isArray(unusedIndexes?.unused_indexes) ? unusedIndexes.unused_indexes : [];

    if (unusedList.length === 0) {
      return (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <TrendingUp className="w-16 h-16 text-green-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">All Indexes Are Used</h3>
          <p className="text-gray-600">
            Great! All indexes are being actively used by queries.
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {unusedList.map((idx: any, index: number) => (
          <div key={index} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {idx.schema && `${idx.schema}.`}{idx.table}
                </h3>
                <p className="text-sm text-gray-600 font-mono">{idx.index}</p>
              </div>
              <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium">
                Unused
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <p className="text-xs text-gray-600">Scans</p>
                <p className="text-lg font-semibold text-gray-900">{idx.scans || 0}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Size</p>
                <p className="text-lg font-semibold text-gray-900">{idx.size || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Type</p>
                <p className="text-sm font-semibold text-gray-900">{idx.type || 'N/A'}</p>
              </div>
            </div>
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-gray-700">{idx.recommendation}</p>
              <p className="text-xs text-gray-600 mt-1">{idx.reason}</p>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderMissingIndexes = () => {
    const missingList = Array.isArray(missingIndexes?.missing_indexes) ? missingIndexes.missing_indexes : [];

    if (missingList.length === 0) {
      return (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <Database className="w-16 h-16 text-green-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Missing Indexes</h3>
          <p className="text-gray-600">
            No missing index suggestions at this time.
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {missingList.map((idx: any, index: number) => (
          <div key={index} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {idx.schema && `${idx.schema}.`}{idx.table}
                </h3>
                {idx.columns && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {idx.columns.map((col: string, colIdx: number) => (
                      <span
                        key={colIdx}
                        className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-mono"
                      >
                        {col}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                Missing
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <p className="text-xs text-gray-600">Sequential Scans</p>
                <p className="text-lg font-semibold text-red-600">{idx.seq_scans || idx.seeks_scans || 0}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Rows Read</p>
                <p className="text-lg font-semibold text-gray-900">
                  {idx.rows_read?.toLocaleString() || 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Impact</p>
                <p className="text-sm font-semibold text-orange-600">
                  {idx.avg_impact ? `${idx.avg_impact.toFixed(1)}%` : 'High'}
                </p>
              </div>
            </div>
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm font-medium text-gray-900 mb-1">{idx.recommendation}</p>
              <p className="text-xs text-gray-600">{idx.reason}</p>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderHistory = () => {
    const changes = Array.isArray(history?.changes) ? history.changes : [];

    if (changes.length === 0) {
      return (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No History</h3>
          <p className="text-gray-600">
            No index changes have been recorded yet.
          </p>
        </div>
      );
    }

    return (
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Index Change History ({history.total_changes})
          </h3>
        </div>
        <div className="divide-y divide-gray-200">
          {changes.map((change: IndexRecommendation) => (
            <div key={change.id} className="p-6 hover:bg-gray-50">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      change.recommendation_type === 'create'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {change.recommendation_type.toUpperCase()}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {change.schema_name && `${change.schema_name}.`}{change.table_name}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 font-mono mb-2">{change.index_name}</p>
                  {change.columns.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {change.columns.map((col, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs font-mono">
                          {col}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="text-xs text-gray-500">{change.reason}</p>
                </div>
                <div className="text-right ml-4">
                  <p className="text-xs text-gray-500">
                    {change.applied_at && new Date(change.applied_at).toLocaleDateString()}
                  </p>
                  <p className="text-xs text-gray-400">
                    {change.applied_at && new Date(change.applied_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Index Management</h1>
          <p className="text-gray-600">
            Analyze, optimize, and manage database indexes across your connections
          </p>
        </div>

        {/* Connection Selector & Actions */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div className="flex-1 max-w-md">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Connection
              </label>
              <select
                value={selectedConnection || ''}
                onChange={(e) => setSelectedConnection(Number(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select a connection...</option>
                {connections.map((conn) => (
                  <option key={conn.id} value={conn.id}>
                    {conn.name} ({conn.engine})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={handleAnalyze}
                disabled={!selectedConnection || analyzing}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
              >
                <Database className="w-4 h-4" />
                <span>{analyzing ? 'Analyzing...' : 'Analyze'}</span>
              </button>
              <button
                onClick={handleRefresh}
                disabled={!selectedConnection || loading}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Statistics */}
        {selectedConnection && !loading && renderStatistics()}

        {/* Tabs */}
        {selectedConnection && (
          <>
            <div className="bg-white rounded-lg shadow-md mb-8">
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6" aria-label="Tabs">
                  {[
                    { id: 'recommendations', label: 'Recommendations', count: recommendations.length },
                    { id: 'unused', label: 'Unused', count: unusedIndexes?.unused_count || 0 },
                    { id: 'missing', label: 'Missing', count: missingIndexes?.missing_count || 0 },
                    { id: 'history', label: 'History', count: history?.total_changes || 0 },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as TabType)}
                      className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                        activeTab === tab.id
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      {tab.label}
                      {tab.count > 0 && (
                        <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                          activeTab === tab.id
                            ? 'bg-blue-100 text-blue-600'
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {tab.count}
                        </span>
                      )}
                    </button>
                  ))}
                </nav>
              </div>
            </div>

            {/* Tab Content */}
            {loading ? (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <RefreshCw className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Loading index data...</p>
              </div>
            ) : (
              <div>
                {activeTab === 'recommendations' && renderRecommendations()}
                {activeTab === 'unused' && renderUnusedIndexes()}
                {activeTab === 'missing' && renderMissingIndexes()}
                {activeTab === 'history' && renderHistory()}
              </div>
            )}
          </>
        )}

        {/* No Connection Selected */}
        {!selectedConnection && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <Database className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Connection Selected</h3>
            <p className="text-gray-600">
              Please select a database connection to view index management options.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default IndexManagement;
