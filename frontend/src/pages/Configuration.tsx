import { useState, useEffect, useRef } from 'react';
import { Settings, AlertCircle, RefreshCw, Database, Activity } from 'lucide-react';
import { getConnections } from '../services/api';
import configurationService, {
  ConfigRecommendation,
  ConfigChange,
  WorkloadAnalysis,
} from '../services/configuration';
import type { Connection } from '../types';
import ConfigCard from '../components/Configuration/ConfigCard';
import ConfigHistory from '../components/Configuration/ConfigHistory';

export default function Configuration() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<number | null>(null);
  const [recommendations, setRecommendations] = useState<ConfigRecommendation[]>([]);
  const [history, setHistory] = useState<ConfigChange[]>([]);
  const [workload, setWorkload] = useState<WorkloadAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedConnectionRef = useRef<number | null>(null);

  // Load connections on mount
  useEffect(() => {
    loadConnections();
  }, []);

  // Update ref and load data when connection is selected
  useEffect(() => {
    selectedConnectionRef.current = selectedConnection;
    
    if (selectedConnection) {
      // Clear previous data immediately to avoid confusion
      setRecommendations([]);
      setHistory([]);
      setWorkload(null);
      
      loadRecommendations();
      loadHistory();
      loadWorkloadAnalysis();
    } else {
      setRecommendations([]);
      setHistory([]);
      setWorkload(null);
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
    }
  };

  const loadRecommendations = async () => {
    const currentId = selectedConnectionRef.current;
    if (!currentId) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await configurationService.getRecommendations(currentId);
      // Only update if the connection is still the same
      if (selectedConnectionRef.current === currentId) {
        setRecommendations(data);
      }
    } catch (err: any) {
      if (selectedConnectionRef.current === currentId) {
        setError(err.response?.data?.detail || 'Failed to load recommendations');
      }
    } finally {
      if (selectedConnectionRef.current === currentId) {
        setLoading(false);
      }
    }
  };

  const loadHistory = async () => {
    const currentId = selectedConnectionRef.current;
    if (!currentId) return;
    
    try {
      const data = await configurationService.getChangeHistory(currentId);
      if (selectedConnectionRef.current === currentId) {
        setHistory(data);
      }
    } catch (err: any) {
      console.error('Failed to load history:', err);
    }
  };

  const loadWorkloadAnalysis = async () => {
    const currentId = selectedConnectionRef.current;
    if (!currentId) return;
    
    try {
      const data = await configurationService.getWorkloadAnalysis(currentId);
      if (selectedConnectionRef.current === currentId) {
        setWorkload(data);
      }
    } catch (err: any) {
      console.error('Failed to load workload analysis:', err);
    }
  };

  const handleApplyConfig = async (parameter: string, value: string) => {
    if (!selectedConnection) return;
    setLoading(true);
    try {
      await configurationService.applyChange({
        connection_id: selectedConnection,
        parameter,
        new_value: value,
      });
      
      // Reload data
      await loadRecommendations();
      await loadHistory();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to apply configuration');
      throw new Error(err.response?.data?.detail || 'Failed to apply configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleRevertChange = async (changeId: number) => {
    try {
      await configurationService.revertChange(changeId);
      await loadHistory();
    } catch (err: any) {
      console.error('Failed to revert change:', err);
    }
  };

  const selectedConn = connections.find((c) => c.id === selectedConnection);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center space-x-3">
            <Settings className="w-8 h-8" />
            <span>Configuration Tuning</span>
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Optimize database configuration based on workload analysis
          </p>
        </div>
        <button
          onClick={loadRecommendations}
          disabled={loading || !selectedConnection}
          className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg 
                   hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed 
                   transition-all duration-200 flex items-center space-x-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Connection Selector */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Select Database Connection
        </label>
        <select
          value={selectedConnection || ''}
          onChange={(e) => setSelectedConnection(Number(e.target.value))}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                   focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Select a connection...</option>
          {connections.map((conn) => (
            <option key={conn.id} value={conn.id}>
              {conn.name} ({conn.engine})
            </option>
          ))}
        </select>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {selectedConnection && (
        <>
          {/* Workload Analysis */}
          {workload && (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <div className="flex items-center space-x-3 mb-4">
                <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Workload Analysis
                </h2>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Workload Type</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {workload.workload_type}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Avg Query Rate</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {workload.avg_query_rate.toFixed(0)}/hr
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Avg Exec Time</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {workload.avg_execution_time.toFixed(0)}ms
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Total Queries</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {workload.total_queries}
                  </p>
                </div>
              </div>
              {workload.insights && workload.insights.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Insights:
                  </p>
                  <ul className="space-y-1">
                    {workload.insights.map((insight, idx) => (
                      <li key={idx} className="text-sm text-gray-600 dark:text-gray-400 flex items-start">
                        <span className="mr-2">•</span>
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Recommendations */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Configuration Recommendations
            </h2>
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 animate-pulse"
                  >
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
                    <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
                  </div>
                ))}
              </div>
            ) : recommendations.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recommendations.map((rec, idx) => (
                  <ConfigCard
                    key={idx}
                    recommendation={rec}
                    onApply={handleApplyConfig}
                    disabled={loading}
                  />
                ))}
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center">
                <Database className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 dark:text-gray-400">
                  No recommendations available
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                  Configuration is already optimized or insufficient data
                </p>
              </div>
            )}
          </div>

          {/* History */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Change History
            </h2>
            <ConfigHistory
              changes={history}
              onRevert={handleRevertChange}
              loading={loading}
            />
          </div>
        </>
      )}
    </div>
  );
}
