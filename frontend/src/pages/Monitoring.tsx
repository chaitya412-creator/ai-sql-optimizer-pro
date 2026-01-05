import { useState, useEffect } from 'react';
import { Play, Square, RefreshCw, Filter, AlertTriangle, XCircle, Info, Database, ArrowRight, Shield, TrendingUp, Zap } from 'lucide-react';
import { getMonitoringStatus, startMonitoring, stopMonitoring, triggerMonitoring, getDiscoveredQueries, getConnections, getMonitoringIssues, getIssuesSummary } from '../services/api';
import type { MonitoringStatus, Query, Connection } from '../types';
import { Link } from 'react-router-dom';

interface MonitoringIssue {
  id: number;
  query_id: number;
  connection_id: number;
  issue_type: string;
  severity: string;
  title: string;
  description: string;
  affected_objects: string[];
  recommendations: string[];
  metrics: Record<string, any>;
  detected_at: string;
  resolved: boolean;
}

interface IssuesSummary {
  total_issues: number;
  critical_issues: number;
  high_issues: number;
  medium_issues: number;
  low_issues: number;
  issues_by_type: Array<{
    issue_type: string;
    count: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  }>;
  recent_critical_issues: Array<{
    issue_id: number;
    query_id: number;
    connection_name: string;
    issue_type: string;
    severity: string;
    title: string;
    description: string;
    detected_at: string;
    sql_preview: string;
  }>;
  last_updated: string;
}

export default function Monitoring() {
  const [status, setStatus] = useState<MonitoringStatus | null>(null);
  const [queries, setQueries] = useState<Query[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [issues, setIssues] = useState<MonitoringIssue[]>([]);
  const [issuesSummary, setIssuesSummary] = useState<IssuesSummary | null>(null);
  const [selectedConnection, setSelectedConnection] = useState<number | undefined>();
  const [selectedSeverity, setSelectedSeverity] = useState<string>('');
  const [selectedIssueType, setSelectedIssueType] = useState<string>('');
  const [expandedIssues, setExpandedIssues] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [selectedConnection, selectedSeverity, selectedIssueType]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const issuesParams: any = {};
      if (selectedConnection) issuesParams.connection_id = selectedConnection;
      if (selectedSeverity) issuesParams.severity = selectedSeverity;
      if (selectedIssueType) issuesParams.issue_type = selectedIssueType;
      
      const [statusData, queriesData, connectionsData, issuesData, summaryData] = await Promise.all([
        getMonitoringStatus(),
        getDiscoveredQueries(selectedConnection),
        getConnections(),
        getMonitoringIssues(issuesParams).catch(() => []),
        getIssuesSummary(selectedConnection).catch(() => null),
      ]);
      
      setStatus(statusData);
      setQueries(queriesData);
      setConnections(connectionsData);
      setIssues(issuesData);
      setIssuesSummary(summaryData);
      
      console.log('Monitoring data loaded:', {
        queries: queriesData.length,
        issues: issuesData.length,
        summary: summaryData
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load monitoring data');
      console.error('Monitoring error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    try {
      setActionLoading(true);
      await startMonitoring();
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to start monitoring');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    try {
      setActionLoading(true);
      await stopMonitoring();
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to stop monitoring');
    } finally {
      setActionLoading(false);
    }
  };

  const handleTrigger = async () => {
    try {
      setActionLoading(true);
      await triggerMonitoring();
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to trigger monitoring');
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-100 dark:bg-red-900/30';
      case 'high':
        return 'text-orange-600 bg-orange-100 dark:bg-orange-900/30';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30';
      case 'low':
        return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30';
    }
  };

  const getIssueTypeLabel = (issueType: string) => {
    return issueType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const toggleIssueExpansion = (issueId: number) => {
    setExpandedIssues(prev => {
      const newSet = new Set(prev);
      if (newSet.has(issueId)) {
        newSet.delete(issueId);
      } else {
        newSet.add(issueId);
      }
      return newSet;
    });
  };

  const getUniqueIssueTypes = () => {
    const types = new Set(issues.map(issue => issue.issue_type));
    return Array.from(types);
  };

  if (loading && !status) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Show empty state if no connections exist
  if (connections.length === 0) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Query Monitoring</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor and discover slow queries and performance issues
          </p>
        </div>

        {/* Empty State */}
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-2 border-dashed border-blue-300 dark:border-blue-700 rounded-lg p-12">
          <div className="text-center max-w-2xl mx-auto">
            <div className="mb-6">
              <Database className="w-20 h-20 mx-auto text-blue-500 dark:text-blue-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              No Database Connections Yet
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-8 text-lg">
              Add a database connection to start monitoring queries and detecting performance issues automatically.
            </p>
            <div className="space-y-4">
              <Link
                to="/connections"
                className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium text-lg"
              >
                <Database className="w-5 h-5" />
                <span>Add Your First Connection</span>
                <ArrowRight className="w-5 h-5" />
              </Link>
              <div className="mt-6 pt-6 border-t border-blue-200 dark:border-blue-800">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  What monitoring provides:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                  <div className="flex items-start space-x-3">
                    <TrendingUp className="w-5 h-5 text-green-500 mt-0.5" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">Automatic Query Discovery</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Find slow queries automatically</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <AlertTriangle className="w-5 h-5 text-orange-500 mt-0.5" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">Issue Detection</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Detect missing indexes, poor joins, and more</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <Zap className="w-5 h-5 text-yellow-500 mt-0.5" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">Real-time Monitoring</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Continuous performance tracking</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <Shield className="w-5 h-5 text-blue-500 mt-0.5" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">Actionable Insights</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Get recommendations to fix issues</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Query Monitoring</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Monitor and discover slow queries across your databases
        </p>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Status Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Monitoring Status
            </h2>
            <div className="flex items-center space-x-2 mt-2">
              <div className={`w-3 h-3 rounded-full ${status?.is_running ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {status?.is_running ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
          <div className="flex space-x-2">
            {status?.is_running ? (
              <button
                onClick={handleStop}
                disabled={actionLoading}
                className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                <Square className="w-4 h-4" />
                <span>Stop</span>
              </button>
            ) : (
              <button
                onClick={handleStart}
                disabled={actionLoading}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                <Play className="w-4 h-4" />
                <span>Start</span>
              </button>
            )}
            <button
              onClick={handleTrigger}
              disabled={actionLoading}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${actionLoading ? 'animate-spin' : ''}`} />
              <span>Trigger Now</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">Interval</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {status?.interval_minutes || 0} min
            </p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">Queries Discovered</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {status?.queries_discovered || 0}
            </p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">Active Connections</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {status?.active_connections || 0}
            </p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">Last Poll</p>
            <p className="text-sm font-medium text-gray-900 dark:text-white mt-1">
              {status?.last_poll_time ? formatDate(status.last_poll_time) : 'Never'}
            </p>
          </div>
        </div>
      </div>

      {/* Performance Issues Overview */}
      {issuesSummary && issuesSummary.total_issues > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                🔍 Performance Issues Detected
              </h2>
              <p className="text-gray-700 dark:text-gray-300">
                Found {issuesSummary.total_issues} performance issue{issuesSummary.total_issues !== 1 ? 's' : ''} that need attention
              </p>
            </div>
            <Link
              to="/optimizer"
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <span>Optimize Queries</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Issue Count Badges */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {issuesSummary.critical_issues > 0 && (
              <div className="bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <XCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
                  <div>
                    <p className="text-3xl font-bold text-red-700 dark:text-red-300">
                      {issuesSummary.critical_issues}
                    </p>
                    <p className="text-sm text-red-600 dark:text-red-400">Critical</p>
                  </div>
                </div>
              </div>
            )}
            {issuesSummary.high_issues > 0 && (
              <div className="bg-orange-100 dark:bg-orange-900/30 border border-orange-300 dark:border-orange-700 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                  <div>
                    <p className="text-3xl font-bold text-orange-700 dark:text-orange-300">
                      {issuesSummary.high_issues}
                    </p>
                    <p className="text-sm text-orange-600 dark:text-orange-400">High</p>
                  </div>
                </div>
              </div>
            )}
            {issuesSummary.medium_issues > 0 && (
              <div className="bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
                  <div>
                    <p className="text-3xl font-bold text-yellow-700 dark:text-yellow-300">
                      {issuesSummary.medium_issues}
                    </p>
                    <p className="text-sm text-yellow-600 dark:text-yellow-400">Medium</p>
                  </div>
                </div>
              </div>
            )}
            {issuesSummary.low_issues > 0 && (
              <div className="bg-blue-100 dark:bg-blue-900/30 border border-blue-300 dark:border-blue-700 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <Info className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  <div>
                    <p className="text-3xl font-bold text-blue-700 dark:text-blue-300">
                      {issuesSummary.low_issues}
                    </p>
                    <p className="text-sm text-blue-600 dark:text-blue-400">Low</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Issues by Type */}
          {issuesSummary.issues_by_type.length > 0 && (
            <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                Issues by Type ({issuesSummary.issues_by_type.length} types detected)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
                {issuesSummary.issues_by_type.map((issueType, index) => (
                  <div
                    key={index}
                    className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {getIssueTypeLabel(issueType.issue_type)}
                      </span>
                      <span className="text-lg font-bold text-gray-900 dark:text-white">
                        {issueType.count}
                      </span>
                    </div>
                    <div className="flex space-x-1 text-xs">
                      {issueType.critical > 0 && (
                        <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded">
                          {issueType.critical} C
                        </span>
                      )}
                      {issueType.high > 0 && (
                        <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded">
                          {issueType.high} H
                        </span>
                      )}
                      {issueType.medium > 0 && (
                        <span className="px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded">
                          {issueType.medium} M
                        </span>
                      )}
                      {issueType.low > 0 && (
                        <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
                          {issueType.low} L
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center space-x-4">
          <Filter className="w-5 h-5 text-gray-500" />
          <select
            value={selectedConnection || ''}
            onChange={(e) => setSelectedConnection(e.target.value ? parseInt(e.target.value) : undefined)}
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="">All Connections</option>
            {connections.map((conn) => (
              <option key={conn.id} value={conn.id}>
                {conn.name} ({conn.engine})
              </option>
            ))}
          </select>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            value={selectedIssueType}
            onChange={(e) => setSelectedIssueType(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="">All Issue Types</option>
            {getUniqueIssueTypes().map((type) => (
              <option key={type} value={type}>
                {getIssueTypeLabel(type)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Detected Issues List */}
      {issues.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              🚨 Detected Performance Issues
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {issues.length} issue{issues.length !== 1 ? 's' : ''} found requiring attention
            </p>
          </div>
          <div className="p-6 space-y-4">
            {issues.map((issue) => {
              const isExpanded = expandedIssues.has(issue.id);
              const relatedQuery = queries.find(q => q.id === issue.query_id);
              const connection = connections.find(c => c.id === issue.connection_id);
              
              return (
                <div
                  key={issue.id}
                  className={`border rounded-lg overflow-hidden ${
                    issue.severity === 'critical' ? 'border-red-300 dark:border-red-700' :
                    issue.severity === 'high' ? 'border-orange-300 dark:border-orange-700' :
                    issue.severity === 'medium' ? 'border-yellow-300 dark:border-yellow-700' :
                    'border-blue-300 dark:border-blue-700'
                  }`}
                >
                  {/* Issue Header */}
                  <div className={`p-4 ${
                    issue.severity === 'critical' ? 'bg-red-50 dark:bg-red-900/20' :
                    issue.severity === 'high' ? 'bg-orange-50 dark:bg-orange-900/20' :
                    issue.severity === 'medium' ? 'bg-yellow-50 dark:bg-yellow-900/20' :
                    'bg-blue-50 dark:bg-blue-900/20'
                  }`}>
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <AlertTriangle className={`w-5 h-5 ${
                            issue.severity === 'critical' ? 'text-red-600 dark:text-red-400' :
                            issue.severity === 'high' ? 'text-orange-600 dark:text-orange-400' :
                            issue.severity === 'medium' ? 'text-yellow-600 dark:text-yellow-400' :
                            'text-blue-600 dark:text-blue-400'
                          }`} />
                          <span className="font-semibold text-gray-900 dark:text-white">
                            {issue.title}
                          </span>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(issue.severity)}`}>
                            {issue.severity}
                          </span>
                          <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                            {getIssueTypeLabel(issue.issue_type)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                          {issue.description}
                        </p>
                        <div className="flex items-center space-x-3 text-xs text-gray-600 dark:text-gray-400">
                          <span className="flex items-center space-x-1">
                            <Database className="w-3 h-3" />
                            <span>{connection?.name || 'Unknown'}</span>
                          </span>
                          <span>Detected: {formatDate(issue.detected_at)}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => toggleIssueExpansion(issue.id)}
                        className="text-sm text-blue-600 dark:text-blue-400 hover:underline ml-4"
                      >
                        {isExpanded ? 'Hide Details' : 'Show Details'}
                      </button>
                    </div>

                    {/* Affected Objects */}
                    {issue.affected_objects && issue.affected_objects.length > 0 && (
                      <div className="mb-2">
                        <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                          Affected Objects:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {issue.affected_objects.map((obj, idx) => (
                            <span
                              key={idx}
                              className="text-xs px-2 py-1 rounded bg-white dark:bg-gray-700 font-mono"
                            >
                              {obj}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-4">
                        {/* Metrics */}
                        {issue.metrics && Object.keys(issue.metrics).length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
                              Metrics:
                            </p>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 p-3 bg-white dark:bg-gray-700 rounded">
                              {Object.entries(issue.metrics).map(([key, value]) => (
                                <div key={key} className="text-xs">
                                  <span className="text-gray-600 dark:text-gray-400">
                                    {key.replace(/_/g, ' ')}:
                                  </span>{' '}
                                  <span className="font-semibold text-gray-900 dark:text-white">
                                    {typeof value === 'number' ? value.toLocaleString() : String(value)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Recommendations */}
                        {issue.recommendations && issue.recommendations.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
                              💡 Recommendations:
                            </p>
                            <ul className="space-y-2">
                              {issue.recommendations.map((rec, idx) => (
                                <li key={idx} className="text-sm flex items-start space-x-2 text-gray-700 dark:text-gray-300">
                                  <span className="text-gray-500 dark:text-gray-400">•</span>
                                  <span className="flex-1">{rec}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Related Query */}
                        {relatedQuery && (
                          <div>
                            <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
                              Related Query:
                            </p>
                            <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded">
                              <pre className="text-xs font-mono text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words">
                                {relatedQuery.sql_text.length > 200
                                  ? relatedQuery.sql_text.substring(0, 200) + '...'
                                  : relatedQuery.sql_text}
                              </pre>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Discovered Queries */}
      {queries.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Discovered Queries
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {queries.length} quer{queries.length !== 1 ? 'ies' : 'y'} discovered
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Query
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Connection
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Avg Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Executions
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Last Seen
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {queries.map((query) => {
                  const connection = connections.find(c => c.id === query.connection_id);
                  return (
                    <tr key={query.id} className="hover:bg-gray-50 dark:hover:bg-gray-900/50">
                      <td className="px-6 py-4">
                        <div className="text-sm font-mono text-gray-900 dark:text-white max-w-md truncate">
                          {query.sql_text}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <Database className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-900 dark:text-white">
                            {connection?.name || 'Unknown'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-900 dark:text-white">
                          {query.avg_execution_time.toFixed(2)} ms
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-900 dark:text-white">
                          {query.calls}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {formatDate(query.last_seen)}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
