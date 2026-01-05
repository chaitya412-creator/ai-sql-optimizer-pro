import React, { useState } from 'react';
import { Database, Check, X, AlertCircle, TrendingUp, HardDrive, Activity } from 'lucide-react';
import { IndexRecommendation, createIndex, dropIndex } from '../../services/indexes';

interface IndexCardProps {
  recommendation: IndexRecommendation;
  onApply?: () => void;
  onReject?: () => void;
}

const IndexCard: React.FC<IndexCardProps> = ({ recommendation, onApply, onReject }) => {
  const [loading, setLoading] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [action, setAction] = useState<'apply' | 'reject' | null>(null);
  const [error, setError] = useState<string | null>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'recommended':
        return 'bg-blue-100 text-blue-800';
      case 'created':
        return 'bg-green-100 text-green-800';
      case 'dropped':
        return 'bg-gray-100 text-gray-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRecommendationTypeColor = (type: string) => {
    switch (type) {
      case 'create':
        return 'text-green-600';
      case 'drop':
        return 'text-red-600';
      case 'modify':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };

  const handleApply = async () => {
    setLoading(true);
    setError(null);
    
    try {
      if (recommendation.recommendation_type === 'create') {
        await createIndex({
          connection_id: recommendation.connection_id,
          table_name: recommendation.table_name,
          index_name: recommendation.index_name || `idx_${recommendation.table_name}_${recommendation.columns.join('_')}`,
          columns: recommendation.columns,
          index_type: recommendation.index_type,
          schema_name: recommendation.schema_name,
        });
      } else if (recommendation.recommendation_type === 'drop' && recommendation.index_name) {
        await dropIndex({
          connection_id: recommendation.connection_id,
          table_name: recommendation.table_name,
          index_name: recommendation.index_name,
          schema_name: recommendation.schema_name,
        });
      }
      
      setShowConfirm(false);
      if (onApply) onApply();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to apply recommendation');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = () => {
    setShowConfirm(false);
    if (onReject) onReject();
  };

  const openConfirmDialog = (actionType: 'apply' | 'reject') => {
    setAction(actionType);
    setShowConfirm(true);
    setError(null);
  };

  const formatBytes = (bytes?: number) => {
    if (!bytes) return 'N/A';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(2)} ${units[unitIndex]}`;
  };

  return (
    <>
      <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Database className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {recommendation.table_name}
              </h3>
              <p className="text-sm text-gray-500">
                {recommendation.schema_name && `${recommendation.schema_name}.`}
                {recommendation.index_name || 'New Index'}
              </p>
            </div>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(recommendation.status)}`}>
            {recommendation.status}
          </span>
        </div>

        {/* Recommendation Type */}
        <div className="mb-4">
          <span className={`text-sm font-medium ${getRecommendationTypeColor(recommendation.recommendation_type)}`}>
            {recommendation.recommendation_type.toUpperCase()} INDEX
          </span>
        </div>

        {/* Columns */}
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">Columns:</p>
          <div className="flex flex-wrap gap-2">
            {recommendation.columns.map((col, idx) => (
              <span
                key={idx}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md text-sm font-mono"
              >
                {col}
              </span>
            ))}
          </div>
        </div>

        {/* Index Type */}
        <div className="mb-4">
          <p className="text-sm text-gray-600">
            Type: <span className="font-medium text-gray-900">{recommendation.index_type}</span>
          </p>
        </div>

        {/* Reason */}
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-gray-700">{recommendation.reason}</p>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          {recommendation.estimated_benefit !== undefined && (
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600 mx-auto mb-1" />
              <p className="text-xs text-gray-600">Benefit</p>
              <p className="text-lg font-semibold text-green-600">
                {recommendation.estimated_benefit.toFixed(1)}%
              </p>
            </div>
          )}
          
          {recommendation.size_bytes !== undefined && (
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <HardDrive className="w-5 h-5 text-blue-600 mx-auto mb-1" />
              <p className="text-xs text-gray-600">Size</p>
              <p className="text-sm font-semibold text-blue-600">
                {formatBytes(recommendation.size_bytes)}
              </p>
            </div>
          )}
          
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <Activity className="w-5 h-5 text-purple-600 mx-auto mb-1" />
            <p className="text-xs text-gray-600">Scans</p>
            <p className="text-lg font-semibold text-purple-600">
              {recommendation.scans}
            </p>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Actions */}
        {recommendation.status === 'recommended' && (
          <div className="flex space-x-3">
            <button
              onClick={() => openConfirmDialog('apply')}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
            >
              <Check className="w-4 h-4" />
              <span>{loading ? 'Applying...' : 'Apply'}</span>
            </button>
            <button
              onClick={() => openConfirmDialog('reject')}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
            >
              <X className="w-4 h-4" />
              <span>Reject</span>
            </button>
          </div>
        )}

        {/* Applied/Dropped Info */}
        {recommendation.applied_at && (
          <div className="mt-4 text-sm text-gray-500">
            {recommendation.recommendation_type === 'create' ? 'Created' : 'Dropped'} on{' '}
            {new Date(recommendation.applied_at).toLocaleString()}
          </div>
        )}
      </div>

      {/* Confirmation Dialog */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {action === 'apply' ? 'Apply Recommendation?' : 'Reject Recommendation?'}
            </h3>
            <p className="text-gray-600 mb-6">
              {action === 'apply'
                ? `This will ${recommendation.recommendation_type} the index "${recommendation.index_name || 'new index'}" on table "${recommendation.table_name}". This action cannot be undone.`
                : 'This will mark the recommendation as rejected. You can always review it later.'}
            </p>
            <div className="flex space-x-3">
              <button
                onClick={action === 'apply' ? handleApply : handleReject}
                disabled={loading}
                className={`flex-1 px-4 py-2 rounded-lg text-white ${
                  action === 'apply'
                    ? 'bg-blue-600 hover:bg-blue-700'
                    : 'bg-red-600 hover:bg-red-700'
                } disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors`}
              >
                {loading ? 'Processing...' : 'Confirm'}
              </button>
              <button
                onClick={() => setShowConfirm(false)}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default IndexCard;
