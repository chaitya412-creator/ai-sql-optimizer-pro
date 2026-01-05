import { useState } from 'react';
import { TrendingUp, Play, Loader, AlertTriangle, CheckCircle, ArrowDown, ArrowUp } from 'lucide-react';
import { validatePerformance } from '../../services/api';
import type { PerformanceValidation, PerformanceMetrics } from '../../types';

interface PerformanceComparisonProps {
  optimizationId: number;
}

export default function PerformanceComparison({ optimizationId }: PerformanceComparisonProps) {
  const [validation, setValidation] = useState<PerformanceValidation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunValidation = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await validatePerformance({
        optimization_id: optimizationId,
        run_original: true,
        run_optimized: true,
        iterations: 3
      });
      setValidation(data);
    } catch (err: any) {
      setError(err.message || 'Failed to validate performance');
      console.error('Error validating performance:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (ms: number) => {
    if (ms < 1) return `${(ms * 1000).toFixed(2)} μs`;
    if (ms < 1000) return `${ms.toFixed(2)} ms`;
    return `${(ms / 1000).toFixed(2)} s`;
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const getChangeColor = (change: number, lowerIsBetter: boolean = true) => {
    const isImprovement = lowerIsBetter ? change < 0 : change > 0;
    if (Math.abs(change) < 1) return 'text-gray-600 dark:text-gray-400';
    return isImprovement
      ? 'text-green-600 dark:text-green-400'
      : 'text-red-600 dark:text-red-400';
  };

  const getChangeIcon = (change: number, lowerIsBetter: boolean = true) => {
    const isImprovement = lowerIsBetter ? change < 0 : change > 0;
    if (Math.abs(change) < 1) return null;
    return isImprovement ? (
      <ArrowDown className="w-4 h-4" />
    ) : (
      <ArrowUp className="w-4 h-4" />
    );
  };

  const calculateChange = (original?: number, optimized?: number) => {
    if (original === undefined || optimized === undefined || original === 0) return null;
    return ((optimized - original) / original) * 100;
  };

  const renderMetricRow = (
    label: string,
    originalValue?: number,
    optimizedValue?: number,
    formatter: (val: number) => string = formatNumber,
    lowerIsBetter: boolean = true
  ) => {
    if (originalValue === undefined && optimizedValue === undefined) return null;

    const change = calculateChange(originalValue, optimizedValue);

    return (
      <tr className="border-b border-gray-200 dark:border-gray-700 last:border-0">
        <td className="py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </td>
        <td className="py-3 px-4 text-sm text-gray-900 dark:text-white text-right font-mono">
          {originalValue !== undefined ? formatter(originalValue) : '-'}
        </td>
        <td className="py-3 px-4 text-sm text-gray-900 dark:text-white text-right font-mono">
          {optimizedValue !== undefined ? formatter(optimizedValue) : '-'}
        </td>
        <td className={`py-3 px-4 text-sm text-right font-semibold ${change !== null ? getChangeColor(change, lowerIsBetter) : 'text-gray-400'}`}>
          {change !== null ? (
            <div className="flex items-center justify-end space-x-1">
              {getChangeIcon(change, lowerIsBetter)}
              <span>{change > 0 ? '+' : ''}{change.toFixed(1)}%</span>
            </div>
          ) : (
            '-'
          )}
        </td>
      </tr>
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              📈 Performance Validation
            </h3>
          </div>
          {!validation && !loading && (
            <button
              onClick={handleRunValidation}
              className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all shadow-md"
            >
              <Play className="w-4 h-4" />
              <span>Run Performance Test</span>
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {loading && (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader className="w-8 h-8 animate-spin text-green-600 dark:text-green-400 mb-4" />
            <p className="text-gray-600 dark:text-gray-400 text-center">
              Running performance validation...
              <br />
              <span className="text-sm">This may take a few moments</span>
            </p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-800 dark:text-red-200 font-semibold">
                Failed to validate performance
              </p>
              <p className="text-red-700 dark:text-red-300 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {!validation && !loading && !error && (
          <div className="text-center py-12">
            <TrendingUp className="w-16 h-16 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Run a performance test to compare the original and optimized queries
            </p>
            <button
              onClick={handleRunValidation}
              className="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all shadow-md"
            >
              <Play className="w-5 h-5" />
              <span>Run Performance Test</span>
            </button>
          </div>
        )}

        {validation && validation.success && (
          <div className="space-y-6">
            {/* Improvement Summary */}
            <div className={`rounded-lg p-6 text-center ${
              validation.is_faster
                ? 'bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-800'
                : 'bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 border border-red-200 dark:border-red-800'
            }`}>
              <div className="flex items-center justify-center space-x-3 mb-2">
                {validation.is_faster ? (
                  <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                ) : (
                  <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
                )}
                <h4 className={`text-3xl font-bold ${
                  validation.is_faster
                    ? 'text-green-700 dark:text-green-300'
                    : 'text-red-700 dark:text-red-300'
                }`}>
                  {validation.is_faster ? '🎯 ' : '⚠️ '}
                  {validation.improvement_pct !== undefined
                    ? `${validation.improvement_pct > 0 ? '+' : ''}${validation.improvement_pct.toFixed(1)}%`
                    : 'N/A'}
                </h4>
              </div>
              <p className={`text-lg font-medium ${
                validation.is_faster
                  ? 'text-green-800 dark:text-green-200'
                  : 'text-red-800 dark:text-red-200'
              }`}>
                {validation.is_faster ? 'Performance Improvement' : 'Performance Regression'}
              </p>
              {validation.improvement_ms !== undefined && (
                <p className={`text-sm mt-1 ${
                  validation.is_faster
                    ? 'text-green-700 dark:text-green-300'
                    : 'text-red-700 dark:text-red-300'
                }`}>
                  {validation.is_faster ? 'Faster' : 'Slower'} by {Math.abs(validation.improvement_ms).toFixed(2)} ms
                </p>
              )}
            </div>

            {/* Metrics Comparison Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-300 dark:border-gray-600">
                    <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Metric
                    </th>
                    <th className="py-3 px-4 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Original
                    </th>
                    <th className="py-3 px-4 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Optimized
                    </th>
                    <th className="py-3 px-4 text-right text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Change
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {renderMetricRow(
                    'Execution Time',
                    validation.original_metrics?.execution_time_ms,
                    validation.optimized_metrics?.execution_time_ms,
                    formatTime,
                    true
                  )}
                  {renderMetricRow(
                    'Planning Time',
                    validation.original_metrics?.planning_time_ms,
                    validation.optimized_metrics?.planning_time_ms,
                    formatTime,
                    true
                  )}
                  {renderMetricRow(
                    'Rows Returned',
                    validation.original_metrics?.rows_returned,
                    validation.optimized_metrics?.rows_returned,
                    formatNumber,
                    false
                  )}
                  {renderMetricRow(
                    'Buffer Hits',
                    validation.original_metrics?.buffer_hits,
                    validation.optimized_metrics?.buffer_hits,
                    formatNumber,
                    false
                  )}
                  {renderMetricRow(
                    'Buffer Reads',
                    validation.original_metrics?.buffer_reads,
                    validation.optimized_metrics?.buffer_reads,
                    formatNumber,
                    true
                  )}
                  {renderMetricRow(
                    'I/O Cost',
                    validation.original_metrics?.io_cost,
                    validation.optimized_metrics?.io_cost,
                    (val) => val.toFixed(2),
                    true
                  )}
                </tbody>
              </table>
            </div>

            {/* Validation Notes */}
            {validation.validation_notes && validation.validation_notes.length > 0 && (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
                  📝 Validation Notes
                </h4>
                <ul className="space-y-1">
                  {validation.validation_notes.map((note, index) => (
                    <li key={index} className="text-sm text-blue-800 dark:text-blue-200 flex items-start space-x-2">
                      <span className="text-blue-600 dark:text-blue-400">•</span>
                      <span>{note}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Timestamp */}
            <div className="text-center text-sm text-gray-500 dark:text-gray-400">
              Validated at: {new Date(validation.validated_at).toLocaleString()}
            </div>

            {/* Re-run Button */}
            <div className="text-center">
              <button
                onClick={handleRunValidation}
                disabled={loading}
                className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors"
              >
                <Play className="w-4 h-4" />
                <span>Run Again</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
