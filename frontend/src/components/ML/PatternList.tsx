import { Database, TrendingUp, Hash, Clock } from 'lucide-react';
import { OptimizationPattern } from '../../services/ml';
import { formatDistanceToNow } from 'date-fns';

interface PatternListProps {
  patterns: OptimizationPattern[];
  loading?: boolean;
  onPatternClick?: (pattern: OptimizationPattern) => void;
}

export default function PatternList({
  patterns,
  loading = false,
  onPatternClick,
}: PatternListProps) {
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!patterns || patterns.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center">
        <Hash className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-600 dark:text-gray-400">No patterns discovered yet</p>
        <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
          Patterns will appear as optimizations are applied and validated
        </p>
      </div>
    );
  }

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 80) return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
    if (rate >= 60) return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30';
    return 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30';
  };

  const getDatabaseIcon = (dbType: string) => {
    const colors: Record<string, string> = {
      postgresql: 'text-blue-600 dark:text-blue-400',
      mysql: 'text-orange-600 dark:text-orange-400',
      mssql: 'text-red-600 dark:text-red-400',
    };
    return colors[dbType.toLowerCase()] || 'text-gray-600 dark:text-gray-400';
  };

  const formatDate = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Successful Optimization Patterns
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          {patterns.length} pattern{patterns.length !== 1 ? 's' : ''} discovered
        </p>
      </div>

      {/* Pattern List */}
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {patterns.map((pattern) => (
          <div
            key={pattern.id}
            onClick={() => onPatternClick && onPatternClick(pattern)}
            className={`p-6 transition-colors ${
              onPatternClick
                ? 'hover:bg-gray-50 dark:hover:bg-gray-700/30 cursor-pointer'
                : ''
            }`}
          >
            {/* Pattern Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <Database className={`w-4 h-4 ${getDatabaseIcon(pattern.database_type)}`} />
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    {pattern.database_type}
                  </span>
                  <span className="text-xs text-gray-400">•</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    ID: {pattern.id}
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                  {pattern.description || 'Optimization Pattern'}
                </h4>
                <p className="text-xs font-mono text-gray-600 dark:text-gray-400 break-all">
                  {pattern.pattern_signature}
                </p>
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-4 gap-4 mt-4">
              {/* Success Rate */}
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Success Rate</p>
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2 py-1 rounded-full text-sm font-bold ${getSuccessRateColor(
                      pattern.success_rate
                    )}`}
                  >
                    {pattern.success_rate.toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Usage Count */}
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Usage Count</p>
                <div className="flex items-center space-x-1">
                  <Hash className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">
                    {pattern.usage_count}
                  </span>
                </div>
              </div>

              {/* Avg Improvement */}
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Avg Improvement</p>
                <div className="flex items-center space-x-1">
                  <TrendingUp className="w-4 h-4 text-green-600 dark:text-green-400" />
                  <span className="text-sm font-semibold text-green-600 dark:text-green-400">
                    {pattern.avg_improvement_pct.toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Last Used */}
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Last Used</p>
                <div className="flex items-center space-x-1">
                  <Clock className="w-4 h-4 text-gray-400" />
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    {formatDate(pattern.last_used)}
                  </span>
                </div>
              </div>
            </div>

            {/* Pattern Preview */}
            <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <p className="text-gray-500 dark:text-gray-400 mb-1">Original Pattern:</p>
                  <p className="font-mono text-gray-700 dark:text-gray-300 truncate">
                    {pattern.original_pattern}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 dark:text-gray-400 mb-1">Optimized Pattern:</p>
                  <p className="font-mono text-blue-600 dark:text-blue-400 truncate">
                    {pattern.optimized_pattern}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
