import { useState, useEffect } from 'react';
import { Wrench, Database, RefreshCw, Code, Settings, Loader, AlertTriangle, Copy, CheckCircle, Play, TestTube } from 'lucide-react';
import { generateFixRecommendations, applyFix } from '../../services/api';
import type { GenerateFixesResponse, FixRecommendation, DetectionResult } from '../../types';

interface FixRecommendationsProps {
  optimizationId: number;
  detectedIssues?: DetectionResult;
  onFixApplied?: () => void;
}

type TabType = 'indexes' | 'maintenance' | 'rewrites' | 'config';

export default function FixRecommendations({
  optimizationId,
  detectedIssues,
  onFixApplied
}: FixRecommendationsProps) {
  const [fixes, setFixes] = useState<GenerateFixesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('indexes');
  const [applyingFix, setApplyingFix] = useState<string | null>(null);
  const [appliedFixes, setAppliedFixes] = useState<Set<string>>(new Set());
  const [copiedSql, setCopiedSql] = useState<string | null>(null);

  useEffect(() => {
    loadFixes();
  }, [optimizationId]);

  const loadFixes = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await generateFixRecommendations({
        optimization_id: optimizationId,
        include_indexes: true,
        include_maintenance: true,
        include_rewrites: true,
        include_config: false
      });
      setFixes(data);
      
      // Set default tab to first non-empty category
      if (data.index_recommendations.length > 0) {
        setActiveTab('indexes');
      } else if (data.maintenance_tasks.length > 0) {
        setActiveTab('maintenance');
      } else if (data.query_rewrites.length > 0) {
        setActiveTab('rewrites');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate fix recommendations');
      console.error('Error generating fixes:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopySQL = (sql: string, fixId: string) => {
    navigator.clipboard.writeText(sql);
    setCopiedSql(fixId);
    setTimeout(() => setCopiedSql(null), 2000);
  };

  const handleDryRun = async (fix: FixRecommendation, fixId: string) => {
    try {
      setApplyingFix(fixId);
      const result = await applyFix({
        optimization_id: optimizationId,
        fix_type: fix.fix_type,
        fix_sql: fix.sql,
        dry_run: true,
        skip_safety_checks: false
      });
      
      if (result.success) {
        alert(`✅ Dry Run Successful!\n\n${result.message}\n\nSafety checks passed. Ready to apply.`);
      } else {
        alert(`⚠️ Dry Run Failed\n\n${result.message}`);
      }
    } catch (err: any) {
      alert(`❌ Error: ${err.message}`);
    } finally {
      setApplyingFix(null);
    }
  };

  const handleApply = async (fix: FixRecommendation, fixId: string) => {
    if (!confirm(`Are you sure you want to apply this fix?\n\n${fix.description}\n\nSQL: ${fix.sql}`)) {
      return;
    }

    try {
      setApplyingFix(fixId);
      const result = await applyFix({
        optimization_id: optimizationId,
        fix_type: fix.fix_type,
        fix_sql: fix.sql,
        dry_run: false,
        skip_safety_checks: false
      });
      
      if (result.success) {
        setAppliedFixes(prev => new Set([...prev, fixId]));
        alert(`✅ Fix Applied Successfully!\n\n${result.message}\n\nExecution time: ${result.execution_time_sec?.toFixed(2)}s`);
        if (onFixApplied) {
          onFixApplied();
        }
      } else {
        alert(`⚠️ Failed to Apply Fix\n\n${result.message}`);
      }
    } catch (err: any) {
      alert(`❌ Error: ${err.message}`);
    } finally {
      setApplyingFix(null);
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
    }
  };

  const getSafetyColor = (safety: string) => {
    switch (safety) {
      case 'safe':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200';
      case 'caution':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200';
      case 'dangerous':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
    }
  };

  const renderFix = (fix: FixRecommendation, index: number, category: string) => {
    const fixId = `${category}-${index}`;
    const isApplying = applyingFix === fixId;
    const isApplied = appliedFixes.has(fixId);
    const isCopied = copiedSql === fixId;

    return (
      <div
        key={fixId}
        className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800 hover:shadow-md transition-shadow"
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <span className={`text-xs font-semibold px-2 py-1 rounded-full ${getImpactColor(fix.estimated_impact)}`}>
                {fix.estimated_impact.toUpperCase()} IMPACT
              </span>
              <span className={`text-xs font-semibold px-2 py-1 rounded-full ${getSafetyColor(fix.safety_level)}`}>
                {fix.safety_level === 'safe' ? '✅' : fix.safety_level === 'caution' ? '⚠️' : '⛔'} {fix.safety_level.toUpperCase()}
              </span>
              {isApplied && (
                <span className="text-xs font-semibold px-2 py-1 rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200">
                  ✓ APPLIED
                </span>
              )}
            </div>
            <h4 className="font-semibold text-gray-900 dark:text-white">
              {fix.description}
            </h4>
          </div>
        </div>

        {/* SQL Statement */}
        {fix.sql && (
          <div className="mb-3">
            <div className="bg-gray-900 dark:bg-black rounded-lg p-3 relative group">
              <pre className="text-sm text-green-400 font-mono overflow-x-auto">
                {fix.sql}
              </pre>
              <button
                onClick={() => handleCopySQL(fix.sql, fixId)}
                className="absolute top-2 right-2 p-2 bg-gray-800 hover:bg-gray-700 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                title="Copy SQL"
              >
                {isCopied ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4 text-gray-400" />
                )}
              </button>
            </div>
          </div>
        )}

        {/* Affected Objects */}
        {fix.affected_objects && fix.affected_objects.length > 0 && (
          <div className="mb-3">
            <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1">
              Affected Objects:
            </p>
            <div className="flex flex-wrap gap-1">
              {fix.affected_objects.map((obj, idx) => (
                <span
                  key={idx}
                  className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-mono"
                >
                  {obj}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Performance Estimates */}
        {(fix.estimated_cpu_savings || fix.estimated_io_savings || fix.estimated_latency_savings) && (
          <div className="mb-3 p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-100 dark:border-green-800/30">
            <p className="text-xs font-semibold text-green-800 dark:text-green-200 mb-1">
              Projected Savings:
            </p>
            <div className="grid grid-cols-3 gap-2">
              {fix.estimated_latency_savings && (
                <div className="text-xs">
                  <span className="opacity-75">Latency:</span>{' '}
                  <span className="font-semibold text-green-700 dark:text-green-300">{fix.estimated_latency_savings}</span>
                </div>
              )}
              {fix.estimated_cpu_savings && (
                <div className="text-xs">
                  <span className="opacity-75">CPU:</span>{' '}
                  <span className="font-semibold text-green-700 dark:text-green-300">{fix.estimated_cpu_savings}</span>
                </div>
              )}
              {fix.estimated_io_savings && (
                <div className="text-xs">
                  <span className="opacity-75">I/O:</span>{' '}
                  <span className="font-semibold text-green-700 dark:text-green-300">{fix.estimated_io_savings}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center space-x-2 pt-3 border-t border-gray-200 dark:border-gray-700">
          {fix.sql && (
            <>
              <button
                onClick={() => handleDryRun(fix, fixId)}
                disabled={isApplying || isApplied}
                className="flex items-center space-x-1 px-3 py-1.5 text-sm bg-blue-100 hover:bg-blue-200 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isApplying ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <TestTube className="w-4 h-4" />
                )}
                <span>Dry Run</span>
              </button>
              <button
                onClick={() => handleApply(fix, fixId)}
                disabled={isApplying || isApplied}
                className="flex items-center space-x-1 px-3 py-1.5 text-sm bg-green-100 hover:bg-green-200 dark:bg-green-900/30 dark:hover:bg-green-900/50 text-green-700 dark:text-green-300 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isApplying ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                <span>{isApplied ? 'Applied' : 'Apply'}</span>
              </button>
            </>
          )}
        </div>
      </div>
    );
  };

  if (!detectedIssues || detectedIssues.total_issues === 0) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Wrench className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              🔧 Actionable Fix Recommendations
            </h3>
          </div>
          {fixes && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {fixes.total_fixes} fixes available
              </span>
              {fixes.high_impact_count > 0 && (
                <span className="text-xs font-semibold px-2 py-1 rounded-full bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200">
                  {fixes.high_impact_count} high impact
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader className="w-6 h-6 animate-spin text-purple-600 dark:text-purple-400" />
            <span className="ml-2 text-gray-600 dark:text-gray-400">
              Generating fix recommendations...
            </span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-800 dark:text-red-200 font-semibold">
                Failed to generate fix recommendations
              </p>
              <p className="text-red-700 dark:text-red-300 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {fixes && fixes.success && (
          <div>
            {/* Tabs */}
            <div className="flex space-x-1 mb-6 border-b border-gray-200 dark:border-gray-700">
              <button
                onClick={() => setActiveTab('indexes')}
                className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'indexes'
                    ? 'border-purple-600 text-purple-600 dark:text-purple-400'
                    : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                <Database className="w-4 h-4" />
                <span>Indexes ({fixes.index_recommendations.length})</span>
              </button>
              <button
                onClick={() => setActiveTab('maintenance')}
                className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'maintenance'
                    ? 'border-purple-600 text-purple-600 dark:text-purple-400'
                    : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                <RefreshCw className="w-4 h-4" />
                <span>Maintenance ({fixes.maintenance_tasks.length})</span>
              </button>
              <button
                onClick={() => setActiveTab('rewrites')}
                className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'rewrites'
                    ? 'border-purple-600 text-purple-600 dark:text-purple-400'
                    : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                <Code className="w-4 h-4" />
                <span>Rewrites ({fixes.query_rewrites.length})</span>
              </button>
              <button
                onClick={() => setActiveTab('config')}
                className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'config'
                    ? 'border-purple-600 text-purple-600 dark:text-purple-400'
                    : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                <Settings className="w-4 h-4" />
                <span>Config ({fixes.configuration_changes.length})</span>
              </button>
            </div>

            {/* Tab Content */}
            <div className="space-y-4">
              {activeTab === 'indexes' && (
                <>
                  {fixes.index_recommendations.length === 0 ? (
                    <p className="text-gray-600 dark:text-gray-400 text-center py-8">
                      No index recommendations available
                    </p>
                  ) : (
                    fixes.index_recommendations.map((fix, index) => renderFix(fix, index, 'index'))
                  )}
                </>
              )}

              {activeTab === 'maintenance' && (
                <>
                  {fixes.maintenance_tasks.length === 0 ? (
                    <p className="text-gray-600 dark:text-gray-400 text-center py-8">
                      No maintenance tasks available
                    </p>
                  ) : (
                    fixes.maintenance_tasks.map((fix, index) => renderFix(fix, index, 'maintenance'))
                  )}
                </>
              )}

              {activeTab === 'rewrites' && (
                <>
                  {fixes.query_rewrites.length === 0 ? (
                    <p className="text-gray-600 dark:text-gray-400 text-center py-8">
                      No query rewrite suggestions available
                    </p>
                  ) : (
                    fixes.query_rewrites.map((fix, index) => renderFix(fix, index, 'rewrite'))
                  )}
                </>
              )}

              {activeTab === 'config' && (
                <>
                  {fixes.configuration_changes.length === 0 ? (
                    <p className="text-gray-600 dark:text-gray-400 text-center py-8">
                      No configuration changes recommended
                    </p>
                  ) : (
                    fixes.configuration_changes.map((fix, index) => renderFix(fix, index, 'config'))
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
