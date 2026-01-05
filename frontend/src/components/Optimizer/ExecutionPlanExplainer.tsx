import { useState, useEffect } from 'react';
import { FileText, ChevronDown, ChevronUp, AlertTriangle, Loader, CheckCircle } from 'lucide-react';
import { explainExecutionPlan } from '../../services/api';
import type { ExecutionPlanExplanation } from '../../types';

interface ExecutionPlanExplainerProps {
  connectionId: number;
  sqlQuery: string;
  executionPlan?: any;
}

export default function ExecutionPlanExplainer({
  connectionId,
  sqlQuery,
  executionPlan
}: ExecutionPlanExplainerProps) {
  const [explanation, setExplanation] = useState<ExecutionPlanExplanation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    loadExplanation();
  }, [connectionId, sqlQuery, executionPlan]);

  const loadExplanation = async () => {
    if (!executionPlan) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await explainExecutionPlan({
        connection_id: connectionId,
        sql_query: sqlQuery,
        execution_plan: executionPlan
      });
      setExplanation(data);
    } catch (err: any) {
      setError(err.message || 'Failed to explain execution plan');
      console.error('Error explaining plan:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!executionPlan) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div
        className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center space-x-3">
          <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            📊 Execution Plan Explanation
          </h3>
        </div>
        <button className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded">
          {expanded ? (
            <ChevronUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          )}
        </button>
      </div>

      {/* Content */}
      {expanded && (
        <div className="p-6">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <Loader className="w-6 h-6 animate-spin text-blue-600 dark:text-blue-400" />
              <span className="ml-2 text-gray-600 dark:text-gray-400">
                Analyzing execution plan...
              </span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-red-800 dark:text-red-200 font-semibold">
                  Failed to explain execution plan
                </p>
                <p className="text-red-700 dark:text-red-300 text-sm mt-1">{error}</p>
              </div>
            </div>
          )}

          {explanation && explanation.success && (
            <div className="space-y-6">
              {/* Summary */}
              {explanation.summary && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
                    Summary
                  </h4>
                  <p className="text-blue-800 dark:text-blue-200 text-sm leading-relaxed">
                    {explanation.summary}
                  </p>
                </div>
              )}

              {/* Full Explanation */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                  Detailed Explanation
                </h4>
                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                  <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                    {explanation.explanation}
                  </p>
                </div>
              </div>

              {/* Key Operations */}
              {explanation.key_operations && explanation.key_operations.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                    Key Operations
                  </h4>
                  <div className="space-y-2">
                    {explanation.key_operations.map((operation, index) => (
                      <div
                        key={index}
                        className="flex items-start space-x-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3 border border-gray-200 dark:border-gray-700"
                      >
                        <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-gray-700 dark:text-gray-300">
                          {operation}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Performance Bottlenecks */}
              {explanation.bottlenecks && explanation.bottlenecks.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-orange-600 dark:text-orange-400" />
                    <span>Performance Bottlenecks</span>
                  </h4>
                  <div className="space-y-2">
                    {explanation.bottlenecks.map((bottleneck, index) => (
                      <div
                        key={index}
                        className="flex items-start space-x-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3 border border-orange-200 dark:border-orange-800"
                      >
                        <AlertTriangle className="w-4 h-4 text-orange-600 dark:text-orange-400 flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-orange-800 dark:text-orange-200">
                          {bottleneck}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Estimated Cost */}
              {explanation.estimated_cost !== undefined && (
                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Estimated Cost
                    </span>
                    <span className="text-lg font-bold text-gray-900 dark:text-white">
                      {explanation.estimated_cost.toFixed(2)}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {explanation && !explanation.success && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                {explanation.explanation || 'Could not generate execution plan explanation'}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
