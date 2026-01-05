import { useState, useEffect } from 'react';
import { Sparkles, Database, AlertCircle, CheckCircle, Loader, AlertTriangle, Info, XCircle } from 'lucide-react';
import { optimizeQuery, getConnections } from '../services/api';
import type { Connection, OptimizationResult, DetectedIssue } from '../types';
import { ExecutionPlanExplainer, FixRecommendations, PerformanceComparison } from '../components/Optimizer';

export default function Optimizer() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<number | null>(null);
  const [sqlQuery, setSqlQuery] = useState('');
  const [includeExecutionPlan, setIncludeExecutionPlan] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      const data = await getConnections();
      setConnections(data.filter(c => c.monitoring_enabled));
      if (data.length > 0) {
        setSelectedConnection(data[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load connections:', err);
    }
  };

  const handleOptimize = async () => {
    if (!selectedConnection) {
      setError('Please select a database connection');
      return;
    }
    if (!sqlQuery.trim()) {
      setError('Please enter a SQL query');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResult(null);
      const data = await optimizeQuery({
        connection_id: selectedConnection,
        sql_query: sqlQuery,
        include_execution_plan: includeExecutionPlan,
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to optimize query');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-700 bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700';
      case 'high':
        return 'text-orange-700 bg-orange-100 dark:bg-orange-900/30 border-orange-300 dark:border-orange-700';
      case 'medium':
        return 'text-yellow-700 bg-yellow-100 dark:bg-yellow-900/30 border-yellow-300 dark:border-yellow-700';
      case 'low':
        return 'text-blue-700 bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700';
      default:
        return 'text-gray-700 bg-gray-100 dark:bg-gray-900/30 border-gray-300 dark:border-gray-700';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="w-5 h-5" />;
      case 'high':
        return <AlertTriangle className="w-5 h-5" />;
      case 'medium':
        return <AlertCircle className="w-5 h-5" />;
      case 'low':
        return <Info className="w-5 h-5" />;
      default:
        return <Info className="w-5 h-5" />;
    }
  };

  const getIssueTypeLabel = (issueType: string) => {
    return issueType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">SQL Query Optimizer</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Optimize your SQL queries with AI-powered suggestions and comprehensive issue detection
        </p>
      </div>

      {/* Input Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="space-y-4">
          {/* Connection Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Database Connection
            </label>
            <select
              value={selectedConnection || ''}
              onChange={(e) => setSelectedConnection(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              {connections.length === 0 ? (
                <option value="">No active connections</option>
              ) : (
                connections.map((conn) => (
                  <option key={conn.id} value={conn.id}>
                    {conn.name} ({conn.engine})
                  </option>
                ))
              )}
            </select>
          </div>

          {/* SQL Query Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              SQL Query
            </label>
            <textarea
              value={sqlQuery}
              onChange={(e) => setSqlQuery(e.target.value)}
              placeholder="Enter your SQL query here..."
              rows={10}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white font-mono text-sm"
            />
          </div>

          {/* Options */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="includeExecutionPlan"
              checked={includeExecutionPlan}
              onChange={(e) => setIncludeExecutionPlan(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="includeExecutionPlan" className="text-sm text-gray-700 dark:text-gray-300">
              Include execution plan analysis
            </label>
          </div>

          {/* Optimize Button */}
          <button
            onClick={handleOptimize}
            disabled={loading || !selectedConnection || !sqlQuery.trim()}
            className="w-full flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                <span>Optimizing...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>Optimize Query</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Results Section */}
      {result && (
        <div className="space-y-6">
          {/* Detection Summary */}
          {result.detected_issues && result.detected_issues.total_issues > 0 && (
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    🔍 Performance Issues Detected
                  </h3>
                  <p className="text-gray-700 dark:text-gray-300">
                    {result.detected_issues.summary}
                  </p>
                </div>
              </div>
              
              {/* Issue Count Badges */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                {result.detected_issues.critical_issues > 0 && (
                  <div className="bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                      <div>
                        <p className="text-2xl font-bold text-red-700 dark:text-red-300">
                          {result.detected_issues.critical_issues}
                        </p>
                        <p className="text-xs text-red-600 dark:text-red-400">Critical</p>
                      </div>
                    </div>
                  </div>
                )}
                {result.detected_issues.high_issues > 0 && (
                  <div className="bg-orange-100 dark:bg-orange-900/30 border border-orange-300 dark:border-orange-700 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                      <div>
                        <p className="text-2xl font-bold text-orange-700 dark:text-orange-300">
                          {result.detected_issues.high_issues}
                        </p>
                        <p className="text-xs text-orange-600 dark:text-orange-400">High</p>
                      </div>
                    </div>
                  </div>
                )}
                {result.detected_issues.medium_issues > 0 && (
                  <div className="bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                      <div>
                        <p className="text-2xl font-bold text-yellow-700 dark:text-yellow-300">
                          {result.detected_issues.medium_issues}
                        </p>
                        <p className="text-xs text-yellow-600 dark:text-yellow-400">Medium</p>
                      </div>
                    </div>
                  </div>
                )}
                {result.detected_issues.low_issues > 0 && (
                  <div className="bg-blue-100 dark:bg-blue-900/30 border border-blue-300 dark:border-blue-700 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <Info className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                      <div>
                        <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                          {result.detected_issues.low_issues}
                        </p>
                        <p className="text-xs text-blue-600 dark:text-blue-400">Low</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Detected Issues Details */}
          {result.detected_issues && result.detected_issues.issues.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Detected Performance Issues ({result.detected_issues.issues.length})
                </h3>
              </div>
              <div className="p-6 space-y-4">
                {result.detected_issues.issues.map((issue: DetectedIssue, index: number) => (
                  <div
                    key={index}
                    className={`border rounded-lg p-4 ${getSeverityColor(issue.severity)}`}
                  >
                    {/* Issue Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        {getSeverityIcon(issue.severity)}
                        <div>
                          <h4 className="font-semibold text-lg">{issue.title}</h4>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className="text-xs font-medium px-2 py-1 rounded-full bg-white/50 dark:bg-black/20">
                              {issue.severity.toUpperCase()}
                            </span>
                            <span className="text-xs opacity-75">
                              {getIssueTypeLabel(issue.issue_type)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Issue Description */}
                    <p className="text-sm mb-3 opacity-90">
                      {issue.description}
                    </p>

                    {/* Affected Objects */}
                    {issue.affected_objects && issue.affected_objects.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs font-semibold mb-1">Affected Objects:</p>
                        <div className="flex flex-wrap gap-1">
                          {issue.affected_objects.map((obj, idx) => (
                            <span
                              key={idx}
                              className="text-xs px-2 py-1 rounded bg-white/50 dark:bg-black/20 font-mono"
                            >
                              {obj}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Metrics */}
                    {issue.metrics && Object.keys(issue.metrics).length > 0 && (
                      <div className="mb-3 p-2 bg-white/30 dark:bg-black/10 rounded">
                        <p className="text-xs font-semibold mb-1">Metrics:</p>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                          {Object.entries(issue.metrics).map(([key, value]) => (
                            <div key={key} className="text-xs">
                              <span className="opacity-75">{key.replace(/_/g, ' ')}:</span>{' '}
                              <span className="font-semibold">
                                {typeof value === 'number' ? value.toLocaleString() : String(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recommendations */}
                    {issue.recommendations && issue.recommendations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-current/20">
                        <p className="text-xs font-semibold mb-2">💡 Recommendations:</p>
                        <ul className="space-y-1">
                          {issue.recommendations.map((rec, idx) => (
                            <li key={idx} className="text-sm flex items-start space-x-2">
                              <span className="opacity-50">•</span>
                              <span className="flex-1">{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Improvement Badge */}
          {result.estimated_improvement_pct && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 flex items-center space-x-3">
              <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
              <div>
                <p className="text-green-800 dark:text-green-200 font-semibold">
                  Estimated Performance Improvement: {result.estimated_improvement_pct}%
                </p>
              </div>
            </div>
          )}

          {/* Original vs Optimized */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Original Query */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Original Query
                </h3>
              </div>
              <div className="p-4">
                <pre className="text-sm font-mono text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words">
                  {result.original_sql}
                </pre>
              </div>
            </div>

            {/* Optimized Query */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-green-200 dark:border-green-700">
              <div className="p-4 border-b border-green-200 dark:border-green-700 bg-green-50 dark:bg-green-900/20">
                <h3 className="text-lg font-semibold text-green-900 dark:text-green-100">
                  Optimized Query
                </h3>
              </div>
              <div className="p-4">
                <pre className="text-sm font-mono text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words">
                  {result.optimized_sql}
                </pre>
              </div>
            </div>
          </div>

          {/* Explanation */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Explanation
            </h3>
            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
              {result.explanation}
            </p>
          </div>

          {/* Recommendations */}
          {result.recommendations && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Recommendations
              </h3>
              <div className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {result.recommendations}
              </div>
            </div>
          )}

          {/* NEW: Execution Plan Explanation */}
          {result.execution_plan && selectedConnection && (
            <ExecutionPlanExplainer
              connectionId={selectedConnection}
              sqlQuery={sqlQuery}
              executionPlan={result.execution_plan}
            />
          )}

          {/* NEW: Actionable Fix Recommendations */}
          {result.detected_issues && result.detected_issues.total_issues > 0 && (
            <FixRecommendations
              optimizationId={result.id}
              detectedIssues={result.detected_issues}
              onFixApplied={() => {
                // Optionally reload the optimization to see updated status
                console.log('Fix applied successfully');
              }}
            />
          )}

          {/* NEW: Performance Validation */}
          <PerformanceComparison optimizationId={result.id} />
        </div>
      )}
    </div>
  );
}
