import React from 'react';
import { CheckCircle, TrendingUp, Database, Calendar } from 'lucide-react';
import type { Pattern } from '../../services/patterns';

interface PatternCardProps {
  pattern: Pattern;
  onViewDetails: (pattern: Pattern) => void;
}

const PatternCard: React.FC<PatternCardProps> = ({ pattern, onViewDetails }) => {
  // Get category color
  const getCategoryColor = (category?: string) => {
    const colors: Record<string, string> = {
      'JOIN_OPTIMIZATION': 'bg-blue-100 text-blue-800',
      'SUBQUERY_OPTIMIZATION': 'bg-purple-100 text-purple-800',
      'INDEX_RECOMMENDATION': 'bg-green-100 text-green-800',
      'QUERY_REWRITE': 'bg-yellow-100 text-yellow-800',
      'AGGREGATION_OPTIMIZATION': 'bg-orange-100 text-orange-800',
      'WINDOW_FUNCTION': 'bg-pink-100 text-pink-800',
      'CTE_OPTIMIZATION': 'bg-indigo-100 text-indigo-800',
      'ANTI_PATTERN': 'bg-red-100 text-red-800',
    };
    return colors[category || ''] || 'bg-gray-100 text-gray-800';
  };

  // Get success rate color
  const getSuccessRateColor = (rate: number) => {
    if (rate >= 80) return 'text-green-600';
    if (rate >= 60) return 'text-yellow-600';
    if (rate >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  // Get database badge color
  const getDatabaseColor = (dbType: string) => {
    const colors: Record<string, string> = {
      'postgresql': 'bg-blue-50 text-blue-700 border-blue-200',
      'mysql': 'bg-orange-50 text-orange-700 border-orange-200',
      'mssql': 'bg-red-50 text-red-700 border-red-200',
    };
    return colors[dbType.toLowerCase()] || 'bg-gray-50 text-gray-700 border-gray-200';
  };

  // Format category name
  const formatCategory = (category?: string) => {
    if (!category) return 'General';
    return category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 p-6 cursor-pointer"
         onClick={() => onViewDetails(pattern)}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            {pattern.category && (
              <span className={`px-2 py-1 rounded text-xs font-medium ${getCategoryColor(pattern.category)}`}>
                {formatCategory(pattern.category)}
              </span>
            )}
            <span className={`px-2 py-1 rounded text-xs font-medium border ${getDatabaseColor(pattern.database_type)}`}>
              {pattern.database_type.toUpperCase()}
            </span>
          </div>
          <h3 className="text-sm font-mono text-gray-600 truncate">
            {pattern.pattern_signature}
          </h3>
        </div>
      </div>

      {/* Success Rate */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm text-gray-600">Success Rate</span>
          <span className={`text-lg font-bold ${getSuccessRateColor(pattern.success_rate)}`}>
            {pattern.success_rate.toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              pattern.success_rate >= 80 ? 'bg-green-500' :
              pattern.success_rate >= 60 ? 'bg-yellow-500' :
              pattern.success_rate >= 40 ? 'bg-orange-500' : 'bg-red-500'
            }`}
            style={{ width: `${pattern.success_rate}%` }}
          />
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <TrendingUp className="w-4 h-4 text-green-600" />
          </div>
          <p className="text-xs text-gray-600">Improvement</p>
          <p className="text-sm font-semibold text-gray-900">
            {pattern.avg_improvement_pct.toFixed(1)}%
          </p>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <CheckCircle className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-xs text-gray-600">Applied</p>
          <p className="text-sm font-semibold text-gray-900">
            {pattern.times_applied}
          </p>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <Database className="w-4 h-4 text-purple-600" />
          </div>
          <p className="text-xs text-gray-600">Successful</p>
          <p className="text-sm font-semibold text-gray-900">
            {pattern.times_successful}
          </p>
        </div>
      </div>

      {/* Pattern Type */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <div className="flex items-center space-x-2 text-xs text-gray-500">
          <Calendar className="w-3 h-3" />
          <span>{new Date(pattern.created_at).toLocaleDateString()}</span>
        </div>
        <span className="text-xs font-medium text-blue-600 hover:text-blue-700">
          View Details →
        </span>
      </div>
    </div>
  );
};

export default PatternCard;
