import { useState } from 'react';
import { 
  Settings, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  X,
  RefreshCw 
} from 'lucide-react';
import { ConfigRecommendation } from '../../services/configuration';

interface ConfigCardProps {
  recommendation: ConfigRecommendation;
  onApply: (parameter: string, value: string) => Promise<void>;
  onReject?: (parameter: string) => void;
  disabled?: boolean;
}

export default function ConfigCard({
  recommendation,
  onApply,
  onReject,
  disabled = false,
}: ConfigCardProps) {
  const [loading, setLoading] = useState(false);
  const [applied, setApplied] = useState(false);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'low':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <AlertTriangle className="w-4 h-4" />;
      case 'medium':
        return <TrendingUp className="w-4 h-4" />;
      default:
        return <Settings className="w-4 h-4" />;
    }
  };

  const handleApply = async () => {
    setLoading(true);
    try {
      await onApply(recommendation.parameter, recommendation.recommended_value);
      setApplied(true);
    } catch (error) {
      console.error('Failed to apply configuration:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = () => {
    if (onReject) {
      onReject(recommendation.parameter);
    }
  };

  if (applied) {
    return (
      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
        <div className="flex items-center space-x-3">
          <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-green-900 dark:text-green-100">
              {recommendation.parameter}
            </h4>
            <p className="text-xs text-green-700 dark:text-green-300 mt-1">
              Configuration applied successfully
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <Settings className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
              {recommendation.parameter}
            </h4>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {recommendation.category}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${getPriorityColor(
              recommendation.priority
            )}`}
          >
            {getPriorityIcon(recommendation.priority)}
            <span className="capitalize">{recommendation.priority}</span>
          </span>
          {recommendation.requires_restart && (
            <span className="px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400 flex items-center space-x-1">
              <RefreshCw className="w-3 h-3" />
              <span>Restart</span>
            </span>
          )}
        </div>
      </div>

      {/* Values Comparison */}
      <div className="grid grid-cols-2 gap-3 mb-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Current</p>
          <p className="text-sm font-mono font-semibold text-gray-900 dark:text-white break-all">
            {recommendation.current_value}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Recommended</p>
          <p className="text-sm font-mono font-semibold text-blue-600 dark:text-blue-400 break-all">
            {recommendation.recommended_value}
          </p>
        </div>
      </div>

      {/* Reason */}
      <div className="mb-3">
        <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
          Reason:
        </p>
        <p className="text-xs text-gray-600 dark:text-gray-400">
          {recommendation.reason}
        </p>
      </div>

      {/* Impact */}
      <div className="mb-4 p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <p className="text-xs font-medium text-blue-900 dark:text-blue-100">
            Expected Impact:
          </p>
        </div>
        <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
          {recommendation.impact_estimate}
        </p>
      </div>

      {/* Actions */}
      <div className="flex space-x-2">
        <button
          onClick={handleApply}
          disabled={disabled || loading}
          className="flex-1 px-3 py-2 text-sm font-medium text-white bg-gradient-to-r 
                   from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 
                   hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed 
                   transition-all duration-200 flex items-center justify-center space-x-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Applying...</span>
            </>
          ) : (
            <>
              <CheckCircle className="w-4 h-4" />
              <span>Apply</span>
            </>
          )}
        </button>
        {onReject && (
          <button
            onClick={handleReject}
            disabled={disabled || loading}
            className="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 
                     bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 
                     rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors
                     flex items-center space-x-2"
          >
            <X className="w-4 h-4" />
            <span>Reject</span>
          </button>
        )}
      </div>
    </div>
  );
}
