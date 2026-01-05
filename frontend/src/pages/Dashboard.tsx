import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Database, Zap, Clock, AlertTriangle, XCircle, Info, Shield, ArrowRight, Filter } from 'lucide-react';
import { getDashboardStats, getTopQueries, getPerformanceTrends, getDetectionSummary, getQueriesWithIssues, getConnections } from '../services/api';
import type { DashboardStats, TopQuery, PerformanceTrend, DetectionSummary, QueryWithIssues, Connection } from '../types';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [topQueries, setTopQueries] = useState<TopQuery[]>([]);
  const [trends, setTrends] = useState<PerformanceTrend[]>([]);
  const [detectionSummary, setDetectionSummary] = useState<DetectionSummary | null>(null);
  const [queriesWithIssues, setQueriesWithIssues] = useState<QueryWithIssues[]>([]);
  const [expandedQueries, setExpandedQueries] = useState<Set<number>>(new Set());
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConnections();
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [selectedConnectionId]);

  const loadConnections = async () => {
    try {
      const connectionsData = await getConnections();
      setConnections(connectionsData);
    } catch (err: any) {
      console.error('Failed to load connections:', err);
    }
  };

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, queriesData, trendsData, detectionData, queriesWithIssuesData] = await Promise.all([
        getDashboardStats(selectedConnectionId || undefined),
        getTopQueries(10, selectedConnectionId || undefined),
        getPerformanceTrends(24, selectedConnectionId || undefined),
        getDetectionSummary(selectedConnectionId || undefined).catch(() => null), // Don't fail if no detections yet
        getQueriesWithIssues(10, selectedConnectionId || undefined).catch(() => []), // Don't fail if no queries with issues
      ]);
      setStats(statsData);
      setTopQueries(queriesData);
      setTrends(trendsData);
      setDetectionSummary(detectionData);
      setQueriesWithIssues(queriesWithIssuesData);
      
      // Log data for debugging
      console.log('Dashboard stats:', statsData);
      console.log('Selected connection:', selectedConnectionId);
      console.log('Detection summary:', detectionData);
      console.log('Queries with issues:', queriesWithIssuesData);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelectedConnectionId(value === 'all' ? null : parseInt(value));
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

  const toggleQueryExpansion = (optimizationId: number) => {
    setExpandedQueries(prev => {
      const newSet = new Set(prev);
      if (newSet.has(optimizationId)) {
        newSet.delete(optimizationId);
      } else {
        newSet.add(optimizationId);
      }
      return newSet;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-200">{error}</p>
        <button
          onClick={loadDashboardData}
          className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  // Show empty state if no connections exist
  if (stats && stats.total_connections === 0) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Overview of your SQL optimization metrics
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
              Get started by adding your first database connection. Once connected, you'll see performance metrics, 
              detected issues, and optimization recommendations right here.
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
                  What you'll get after connecting:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                  <div className="flex items-start space-x-3">
                    <TrendingUp className="w-5 h-5 text-green-500 mt-0.5" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">Performance Monitoring</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Track query execution times and bottlenecks</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <AlertTriangle className="w-5 h-5 text-orange-500 mt-0.5" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">Issue Detection</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Automatically detect performance problems</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <Zap className="w-5 h-5 text-yellow-500 mt-0.5" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">AI-Powered Optimization</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Get intelligent query optimization suggestions</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <Shield className="w-5 h-5 text-blue-500 mt-0.5" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">Safe Recommendations</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Review and apply optimizations safely</p>
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
      {/* Header with Connection Filter */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Overview of your SQL optimization metrics
          </p>
        </div>
        
        {/* Connection Filter Dropdown */}
        {connections.length > 0 && (
          <div className="flex items-center space-x-3">
            <Filter className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            <select
              value={selectedConnectionId || 'all'}
              onChange={handleConnectionChange}
              className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Connections</option>
              {connections.map((conn) => (
                <option key={conn.id} value={conn.id}>
                  {conn.name} ({conn.engine})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Queries"
          value={stats?.total_queries_discovered || 0}
          icon={Database}
          color="blue"
        />
        <StatCard
          title="Active Connections"
          value={stats?.active_connections || 0}
          icon={Clock}
          color="purple"
        />
        <StatCard
          title="Detected Issues"
          value={stats?.total_detected_issues || 0}
          icon={AlertTriangle}
          color="red"
        />
        <StatCard
          title="Optimizations"
          value={stats?.total_optimizations || 0}
          icon={Zap}
          color="green"
        />
      </div>

      {/* Performance Issues Overview */}
      {detectionSummary && detectionSummary.total_issues > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                🔍 Performance Issues Detected
              </h2>
              <p className="text-gray-700 dark:text-gray-300">
                Found {detectionSummary.total_issues} performance issue{detectionSummary.total_issues !== 1 ? 's' : ''} across {detectionSummary.total_optimizations_with_issues} optimized quer{detectionSummary.total_optimizations_with_issues !== 1 ? 'ies' : 'y'}
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
            {detectionSummary.critical_issues > 0 && (
              <div className="bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <XCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
                  <div>
                    <p className="text-3xl font-bold text-red-700 dark:text-red-300">
                      {detectionSummary.critical_issues}
                    </p>
                    <p className="text-sm text-red-600 dark:text-red-400">Critical</p>
                  </div>
                </div>
              </div>
            )}
            {detectionSummary.high_issues > 0 && (
              <div className="bg-orange-100 dark:bg-orange-900/30 border border-orange-300 dark:border-orange-700 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                  <div>
                    <p className="text-3xl font-bold text-orange-700 dark:text-orange-300">
                      {detectionSummary.high_issues}
                    </p>
                    <p className="text-sm text-orange-600 dark:text-orange-400">High</p>
                  </div>
                </div>
              </div>
            )}
            {detectionSummary.medium_issues > 0 && (
              <div className="bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
                  <div>
                    <p className="text-3xl font-bold text-yellow-700 dark:text-yellow-300">
                      {detectionSummary.medium_issues}
                    </p>
                    <p className="text-sm text-yellow-600 dark:text-yellow-400">Medium</p>
                  </div>
                </div>
              </div>
            )}
            {detectionSummary.low_issues > 0 && (
              <div className="bg-blue-100 dark:bg-blue-900/30 border border-blue-300 dark:border-blue-700 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <Info className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  <div>
                    <p className="text-3xl font-bold text-blue-700 dark:text-blue-300">
                      {detectionSummary.low_issues}
                    </p>
                    <p className="text-sm text-blue-600 dark:text-blue-400">Low</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Issues by Type */}
          {detectionSummary.issues_by_type.length > 0 && (
            <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-4 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                Issues by Type ({detectionSummary.issues_by_type.length} types detected)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
                {detectionSummary.issues_by_type.map((issueType, index) => (
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

          {/* Critical Issues Preview */}
          {detectionSummary.recent_critical_issues.length > 0 && (
            <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                ⚠️ Critical Issues Requiring Attention
              </h3>
              <div className="space-y-2">
                {detectionSummary.recent_critical_issues.map((issue, index) => (
                  <div
                    key={index}
                    className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <XCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                          <span className="font-semibold text-red-900 dark:text-red-100">
                            {issue.title}
                          </span>
                        </div>
                        <p className="text-sm text-red-800 dark:text-red-200 mb-2">
                          {issue.description}
                        </p>
                        <div className="flex items-center space-x-3 text-xs text-red-700 dark:text-red-300">
                          <span className="flex items-center space-x-1">
                            <Database className="w-3 h-3" />
                            <span>{issue.connection_name}</span>
                          </span>
                          <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 rounded">
                            {getIssueTypeLabel(issue.issue_type)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 text-center">
                <Link
                  to="/optimizer"
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  View all issues in Optimizer →
                </Link>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Queries with Detected Issues */}
      {queriesWithIssues.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              📋 Queries with Detected Issues
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              SQL queries that have performance issues requiring attention
            </p>
          </div>
          <div className="p-6 space-y-4">
            {queriesWithIssues.map((queryWithIssue) => {
              const isExpanded = expandedQueries.has(queryWithIssue.optimization_id);
              const highestSeverity = queryWithIssue.critical_count > 0 ? 'critical' :
                                     queryWithIssue.high_count > 0 ? 'high' :
                                     queryWithIssue.medium_count > 0 ? 'medium' : 'low';
              
              return (
                <div
                  key={queryWithIssue.optimization_id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
                >
                  {/* Query Header */}
                  <div className="bg-gray-50 dark:bg-gray-900/50 p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <Database className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                          <span className="font-medium text-gray-900 dark:text-white">
                            {queryWithIssue.connection_name}
                          </span>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(highestSeverity)}`}>
                            {queryWithIssue.issue_count} issue{queryWithIssue.issue_count !== 1 ? 's' : ''}
                          </span>
                          {queryWithIssue.estimated_improvement_pct && (
                            <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">
                              +{queryWithIssue.estimated_improvement_pct.toFixed(1)}% faster
                            </span>
                          )}
                        </div>
                        
                        {/* Issue Count Badges */}
                        <div className="flex space-x-2 text-xs">
                          {queryWithIssue.critical_count > 0 && (
                            <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded">
                              {queryWithIssue.critical_count} Critical
                            </span>
                          )}
                          {queryWithIssue.high_count > 0 && (
                            <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded">
                              {queryWithIssue.high_count} High
                            </span>
                          )}
                          {queryWithIssue.medium_count > 0 && (
                            <span className="px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded">
                              {queryWithIssue.medium_count} Medium
                            </span>
                          )}
                          {queryWithIssue.low_count > 0 && (
                            <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
                              {queryWithIssue.low_count} Low
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <button
                        onClick={() => toggleQueryExpansion(queryWithIssue.optimization_id)}
                        className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        {isExpanded ? 'Hide Details' : 'Show Details'}
                      </button>
                    </div>
                    
                    {/* SQL Comparison - Side by Side */}
                    {!isExpanded ? (
                      <div className="bg-white dark:bg-gray-800 rounded p-3 font-mono text-xs text-gray-700 dark:text-gray-300">
                        {queryWithIssue.sql_preview}
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-3">
                        {/* Original SQL */}
                        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                          <div className="bg-gray-100 dark:bg-gray-900 px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                            <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                              ❌ Original Query (With Issues)
                            </span>
                          </div>
                          <div className="p-3 font-mono text-xs text-gray-700 dark:text-gray-300 max-h-64 overflow-y-auto">
                            {queryWithIssue.original_sql}
                          </div>
                        </div>
                        
                        {/* Optimized SQL */}
                        <div className="bg-white dark:bg-gray-800 rounded-lg border-2 border-green-300 dark:border-green-700 overflow-hidden">
                          <div className="bg-green-50 dark:bg-green-900/20 px-3 py-2 border-b border-green-200 dark:border-green-700">
                            <span className="text-xs font-semibold text-green-700 dark:text-green-300">
                              ✅ Optimized Query (Recommended)
                            </span>
                          </div>
                          <div className="p-3 font-mono text-xs text-gray-700 dark:text-gray-300 max-h-64 overflow-y-auto">
                            {queryWithIssue.optimized_sql ? (
                              queryWithIssue.optimized_sql
                            ) : (
                              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                                <p className="mb-2">⚠️ Optimization not available</p>
                                <p className="text-xs">
                                  The LLM could not generate a valid optimization for this query.
                                  <br />
                                  Please try optimizing again or review the detected issues manually.
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Recommendations */}
                    {isExpanded && queryWithIssue.recommendations && (
                      <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg">
                        <p className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-2">
                          💡 Optimization Recommendations:
                        </p>
                        <p className="text-sm text-blue-800 dark:text-blue-200 whitespace-pre-wrap">
                          {queryWithIssue.recommendations}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  {/* Issue Details (Expanded) */}
                  {isExpanded && (
                    <div className="p-4 space-y-3 bg-white dark:bg-gray-800">
                      {queryWithIssue.issues.map((issue, idx) => (
                        <div
                          key={idx}
                          className={`border rounded-lg p-3 ${
                            issue.severity === 'critical' ? 'border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20' :
                            issue.severity === 'high' ? 'border-orange-300 dark:border-orange-700 bg-orange-50 dark:bg-orange-900/20' :
                            issue.severity === 'medium' ? 'border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20' :
                            'border-blue-300 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/20'
                          }`}
                        >
                          <div className="flex items-start space-x-3">
                            <AlertTriangle className={`w-5 h-5 mt-0.5 ${
                              issue.severity === 'critical' ? 'text-red-600 dark:text-red-400' :
                              issue.severity === 'high' ? 'text-orange-600 dark:text-orange-400' :
                              issue.severity === 'medium' ? 'text-yellow-600 dark:text-yellow-400' :
                              'text-blue-600 dark:text-blue-400'
                            }`} />
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                <span className="font-semibold text-gray-900 dark:text-white">
                                  {issue.title}
                                </span>
                                <span className={`px-2 py-0.5 text-xs font-medium rounded ${getSeverityColor(issue.severity)}`}>
                                  {issue.severity}
                                </span>
                                <span className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                                  {getIssueTypeLabel(issue.issue_type)}
                                </span>
                              </div>
                              <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                                {issue.description}
                              </p>
                              {issue.recommendations && issue.recommendations.length > 0 && (
                                <div className="mt-2">
                                  <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                    Recommendations:
                                  </p>
                                  <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                                    {issue.recommendations.map((rec, recIdx) => (
                                      <li key={recIdx} className="flex items-start space-x-2">
                                        <span className="text-blue-600 dark:text-blue-400">•</span>
                                        <span>{rec}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Top Slow Queries */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Top Slow Queries
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Queries with the highest execution times
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Connection
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Query
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Avg Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Calls
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Severity
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {topQueries.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                    No queries found. Start monitoring to discover slow queries.
                  </td>
                </tr>
              ) : (
                topQueries.map((query) => (
                  <tr key={query.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {query.connection_name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">
                      <div className="max-w-md truncate font-mono text-xs">
                        {query.sql_text}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {query.avg_execution_time.toFixed(2)}ms
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {query.calls}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(query.severity)}`}>
                        {query.severity}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Performance Trends */}
      {trends.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Performance Trends (24h)
          </h2>
          <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
            <p>Chart visualization would go here (using recharts)</p>
          </div>
        </div>
      )}
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  color: 'blue' | 'purple' | 'red' | 'green';
}

function StatCard({ title, value, icon: Icon, color }: StatCardProps) {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    red: 'from-red-500 to-red-600',
    green: 'from-green-500 to-green-600',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">{value}</p>
        </div>
        <div className={`w-12 h-12 bg-gradient-to-br ${colorClasses[color]} rounded-lg flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
}
