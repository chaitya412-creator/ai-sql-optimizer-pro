import { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Clock, 
  Activity, 
  AlertTriangle,
  BarChart3,
  PieChart,
  Lightbulb,
  RefreshCw,
  Database
} from 'lucide-react';
import { workloadService, type WorkloadAnalysis, type Recommendation } from '../services/workload';
import { getConnections } from '../services/api';

interface Connection {
  id: number;
  name: string;
  engine: string;
  host: string;
  port: number;
  database: string;
}

export default function WorkloadAnalysisPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<number | null>(null);
  const [days, setDays] = useState<number>(7);
  const [analysis, setAnalysis] = useState<WorkloadAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load connections on mount
  useEffect(() => {
    loadConnections();
  }, []);

  // Auto-load analysis when connection is selected
  useEffect(() => {
    if (selectedConnection) {
      loadAnalysis();
    }
  }, [selectedConnection, days]);

  const loadConnections = async () => {
    try {
      const data = await getConnections();
      setConnections(data);
      if (data.length > 0 && !selectedConnection) {
        setSelectedConnection(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load connections:', err);
      setError('Failed to load connections');
    }
  };

  const loadAnalysis = async () => {
    if (!selectedConnection) return;

    setLoading(true);
    setError(null);

    try {
      const data = await workloadService.getAnalysis(selectedConnection, days);
      setAnalysis(data);
    } catch (err: any) {
      console.error('Failed to load workload analysis:', err);
      setError(err.response?.data?.detail || 'Failed to load workload analysis');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getWorkloadTypeColor = (type: string) => {
    switch (type) {
      case 'oltp':
        return 'bg-green-100 text-green-800';
      case 'olap':
        return 'bg-purple-100 text-purple-800';
      case 'mixed':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'increasing') return '📈';
    if (trend === 'decreasing') return '📉';
    return '➡️';
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-blue-600" />
            Workload Analysis
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Analyze workload patterns and get proactive optimization recommendations
          </p>
        </div>
        <button
          onClick={loadAnalysis}
          disabled={loading || !selectedConnection}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Connection Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Database Connection
            </label>
            <select
              value={selectedConnection || ''}
              onChange={(e) => setSelectedConnection(Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a connection</option>
              {connections.map((conn) => (
                <option key={conn.id} value={conn.id}>
                  {conn.name} ({conn.engine})
                </option>
              ))}
            </select>
          </div>

          {/* Time Range Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Analysis Period
            </label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value={1}>Last 24 hours</option>
              <option value={3}>Last 3 days</option>
              <option value={7}>Last 7 days</option>
              <option value={14}>Last 14 days</option>
              <option value={30}>Last 30 days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900 dark:text-red-200">Error</h3>
            <p className="text-red-700 dark:text-red-300 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <RefreshCw className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">Analyzing workload patterns...</p>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {!loading && analysis && (
        <>
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Workload Type */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-2">
                <Database className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getWorkloadTypeColor(analysis.workload_type)}`}>
                  {analysis.workload_type.toUpperCase()}
                </span>
              </div>
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Workload Type</h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {analysis.database_type}
              </p>
            </div>

            {/* Total Queries */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <Activity className="w-5 h-5 text-blue-600 mb-2" />
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Queries</h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {analysis.query_pattern.total_queries.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                {analysis.query_pattern.total_calls.toLocaleString()} total calls
              </p>
            </div>

            {/* Avg Execution Time */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <Clock className="w-5 h-5 text-green-600 mb-2" />
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Exec Time</h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {analysis.query_pattern.avg_calls_per_query.toFixed(1)}ms
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                per query execution
              </p>
            </div>

            {/* Slow Queries */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <AlertTriangle className="w-5 h-5 text-orange-600 mb-2" />
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Slow Queries</h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {analysis.query_pattern.slow_queries_pct.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                {analysis.query_pattern.slow_queries_count} queries {'>'}1s
              </p>
            </div>
          </div>

          {/* Peak Hours Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Peak Hours Analysis</h2>
            </div>
            <div className="space-y-2">
              {Object.entries(analysis.hourly_pattern.hourly_averages).map(([hour, data]: [string, any]) => {
                const isPeak = analysis.hourly_pattern.peak_hours.includes(Number(hour));
                const maxQueries = Math.max(...Object.values(analysis.hourly_pattern.hourly_averages).map((d: any) => d.avg_queries));
                const width = (data.avg_queries / maxQueries) * 100;

                return (
                  <div key={hour} className="flex items-center gap-3">
                    <span className="text-sm font-medium text-gray-600 dark:text-gray-400 w-16">
                      {hour}:00
                    </span>
                    <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-8 relative overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          isPeak ? 'bg-gradient-to-r from-red-500 to-orange-500' : 'bg-gradient-to-r from-blue-500 to-cyan-500'
                        }`}
                        style={{ width: `${width}%` }}
                      />
                      <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-gray-900 dark:text-white">
                        {data.avg_queries.toFixed(0)} queries
                      </span>
                    </div>
                    {isPeak && (
                      <span className="text-xs font-medium text-red-600 dark:text-red-400">PEAK</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Performance Trends */}
          {analysis.predictions && analysis.predictions.status === 'success' && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-purple-600" />
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Performance Predictions</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Query Volume Trend */}
                {analysis.predictions.query_volume && (
                  <div className="space-y-3">
                    <h3 className="font-medium text-gray-900 dark:text-white flex items-center gap-2">
                      {getTrendIcon(analysis.predictions.query_volume.trend)} Query Volume
                    </h3>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Current Average:</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {analysis.predictions.query_volume.current_avg.toFixed(0)} queries
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Predicted Next Period:</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {analysis.predictions.query_volume.predicted_next_period.toFixed(0)} queries
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Growth Rate:</span>
                        <span className={`font-medium ${
                          analysis.predictions.query_volume.growth_rate_pct > 0 ? 'text-red-600' : 'text-green-600'
                        }`}>
                          {analysis.predictions.query_volume.growth_rate_pct > 0 ? '+' : ''}
                          {analysis.predictions.query_volume.growth_rate_pct.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Execution Time Trend */}
                {analysis.predictions.execution_time && (
                  <div className="space-y-3">
                    <h3 className="font-medium text-gray-900 dark:text-white flex items-center gap-2">
                      {getTrendIcon(analysis.predictions.execution_time.trend)} Execution Time
                    </h3>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Current Average:</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {analysis.predictions.execution_time.current_avg_ms.toFixed(1)}ms
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Predicted Next Period:</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {analysis.predictions.execution_time.predicted_next_period_ms.toFixed(1)}ms
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Growth Rate:</span>
                        <span className={`font-medium ${
                          analysis.predictions.execution_time.growth_rate_pct > 0 ? 'text-red-600' : 'text-green-600'
                        }`}>
                          {analysis.predictions.execution_time.growth_rate_pct > 0 ? '+' : ''}
                          {analysis.predictions.execution_time.growth_rate_pct.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Warnings */}
              {analysis.predictions.warnings && analysis.predictions.warnings.length > 0 && (
                <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      {analysis.predictions.warnings.map((warning, idx) => (
                        <p key={idx} className="text-sm text-yellow-800 dark:text-yellow-200">{warning}</p>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Proactive Recommendations */}
          {analysis.recommendations && analysis.recommendations.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb className="w-5 h-5 text-yellow-600" />
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Proactive Recommendations ({analysis.recommendations.length})
                </h2>
              </div>
              <div className="space-y-4">
                {analysis.recommendations.map((rec: Recommendation, idx: number) => (
                  <div
                    key={idx}
                    className={`border rounded-lg p-4 ${getPriorityColor(rec.priority)}`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-lg">{rec.title}</h3>
                      <span className="px-2 py-1 rounded text-xs font-medium uppercase">
                        {rec.priority}
                      </span>
                    </div>
                    <p className="text-sm mb-3">{rec.description}</p>
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="font-medium">Action:</span> {rec.action}
                      </div>
                      <div>
                        <span className="font-medium">Estimated Impact:</span> {rec.estimated_impact}
                      </div>
                      <div className="text-xs opacity-75">
                        Type: {rec.type}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Insights */}
          {analysis.insights && analysis.insights.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center gap-2 mb-4">
                <PieChart className="w-5 h-5 text-green-600" />
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Key Insights</h2>
              </div>
              <ul className="space-y-2">
                {analysis.insights.map((insight, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                    <span className="text-green-600 dark:text-green-400 mt-1">•</span>
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!loading && !analysis && !error && selectedConnection && (
        <div className="text-center py-12">
          <TrendingUp className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No Analysis Data Available
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Click "Refresh" to analyze workload patterns for the selected connection
          </p>
        </div>
      )}
    </div>
  );
}
