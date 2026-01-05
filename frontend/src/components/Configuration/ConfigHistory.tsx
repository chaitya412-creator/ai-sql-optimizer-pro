import { useState } from 'react';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  RotateCcw, 
  AlertCircle,
  TrendingUp,
  TrendingDown 
} from 'lucide-react';
import { ConfigChange } from '../../services/configuration';
import { formatDistanceToNow } from 'date-fns';

interface ConfigHistoryProps {
  changes: ConfigChange[];
  onRevert?: (changeId: number) => Promise<void>;
  loading?: boolean;
}

export default function ConfigHistory({
  changes,
  onRevert,
  loading = false,
}: ConfigHistoryProps) {
  const [revertingId, setRevertingId] = useState<number | null>(null);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'applied':
        return <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />;
      case 'reverted':
        return <RotateCcw className="w-5 h-5 text-gray-600 dark:text-gray-400" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />;
      case 'pending':
        return <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />;
      default:
        return <Clock className="w-5 h-5 text-gray-600 dark:text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'applied':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'reverted':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400';
    }
  };

  const handleRevert = async (changeId: number) => {
    if (!onRevert) return;
    
    setRevertingId(changeId);
    try {
      await onRevert(changeId);
    } catch (error) {
      console.error('Failed to revert change:', error);
    } finally {
      setRevertingId(null);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return dateString;
    }
  };

  if (changes.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center">
        <Clock className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-600 dark:text-gray-400">No configuration changes yet</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Configuration History
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          {changes.length} change{changes.length !== 1 ? 's' : ''} recorded
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-700/30">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Parameter
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Change
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Impact
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {changes.map((change) => (
              <tr
                key={change.id}
                className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
              >
                {/* Parameter */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {change.parameter}
                  </p>
                </td>

                {/* Change */}
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-2 text-sm">
                    <span className="font-mono text-gray-600 dark:text-gray-400">
                      {change.old_value}
                    </span>
                    <span className="text-gray-400">→</span>
                    <span className="font-mono text-blue-600 dark:text-blue-400">
                      {change.new_value}
                    </span>
                  </div>
                </td>

                {/* Impact */}
                <td className="px-6 py-4 whitespace-nowrap">
                  {change.impact_measured && change.performance_impact !== undefined ? (
                    <div className="flex items-center space-x-1">
                      {change.performance_impact > 0 ? (
                        <TrendingUp className="w-4 h-4 text-green-600 dark:text-green-400" />
                      ) : change.performance_impact < 0 ? (
                        <TrendingDown className="w-4 h-4 text-red-600 dark:text-red-400" />
                      ) : null}
                      <span
                        className={`text-sm font-semibold ${
                          change.performance_impact > 0
                            ? 'text-green-600 dark:text-green-400'
                            : change.performance_impact < 0
                            ? 'text-red-600 dark:text-red-400'
                            : 'text-gray-600 dark:text-gray-400'
                        }`}
                      >
                        {change.performance_impact > 0 ? '+' : ''}
                        {change.performance_impact.toFixed(1)}%
                      </span>
                    </div>
                  ) : (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Not measured
                    </span>
                  )}
                </td>

                {/* Status */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(change.status)}
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${getStatusColor(
                        change.status
                      )}`}
                    >
                      {change.status}
                    </span>
                  </div>
                </td>

                {/* Date */}
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                  {formatDate(change.created_at)}
                </td>

                {/* Actions */}
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  {change.status === 'applied' && onRevert && (
                    <button
                      onClick={() => handleRevert(change.id)}
                      disabled={loading || revertingId === change.id}
                      className="inline-flex items-center space-x-1 px-3 py-1 text-sm font-medium 
                               text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 
                               border border-gray-300 dark:border-gray-600 rounded-lg 
                               hover:bg-gray-50 dark:hover:bg-gray-600 
                               disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {revertingId === change.id ? (
                        <>
                          <div className="w-3 h-3 border-2 border-gray-600 border-t-transparent rounded-full animate-spin" />
                          <span>Reverting...</span>
                        </>
                      ) : (
                        <>
                          <RotateCcw className="w-3 h-3" />
                          <span>Revert</span>
                        </>
                      )}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
