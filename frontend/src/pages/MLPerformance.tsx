import { useState, useEffect } from 'react';
import { Brain, RefreshCw, AlertCircle, Zap } from 'lucide-react';
import mlService, { MLAccuracyTrend, OptimizationPattern, RefinementHistory } from '../services/ml';
import feedbackService, { FeedbackStats as FeedbackStatsType } from '../services/feedback';
import AccuracyChart from '../components/ML/AccuracyChart';
import PatternList from '../components/ML/PatternList';
import FeedbackStatsComponent from '../components/ML/FeedbackStats';

export default function MLPerformance() {
  const [accuracyTrend, setAccuracyTrend] = useState<MLAccuracyTrend[]>([]);
  const [patterns, setPatterns] = useState<OptimizationPattern[]>([]);
  const [refinementHistory, setRefinementHistory] = useState<RefinementHistory[]>([]);
  const [stats, setStats] = useState<FeedbackStatsType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refining, setRefining] = useState(false);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      await Promise.all([
        loadAccuracyTrend(),
        loadPatterns(),
        loadRefinementHistory(),
        loadStats(),
      ]);
    } catch (err: any) {
      setError('Failed to load ML performance data');
    } finally {
      setLoading(false);
    }
  };

  const loadAccuracyTrend = async () => {
    try {
      const data = await mlService.getAccuracyTrend(30);
      setAccuracyTrend(data);
    } catch (err: any) {
      console.error('Failed to load accuracy trend:', err);
    }
  };

  const loadPatterns = async () => {
    try {
      const data = await mlService.getPatterns({ limit: 10 });
      setPatterns(data);
    } catch (err: any) {
      console.error('Failed to load patterns:', err);
    }
  };

  const loadRefinementHistory = async () => {
    try {
      const data = await mlService.getRefinementHistory(10);
      setRefinementHistory(data);
    } catch (err: any) {
      console.error('Failed to load refinement history:', err);
    }
  };

  const loadStats = async () => {
    try {
      const data = await feedbackService.getStats();
      setStats(data);
    } catch (err: any) {
      console.error('Failed to load stats:', err);
    }
  };

  const handleTriggerRefinement = async () => {
    setRefining(true);
    setError(null);
    
    try {
      const result = await mlService.triggerRefinement();
      alert(`Refinement complete!\n\nPatterns analyzed: ${result.patterns_analyzed}\nPatterns updated: ${result.patterns_updated}\nNew accuracy: ${(result.new_accuracy * 100).toFixed(1)}%`);
      
      // Reload data
      await loadAllData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to trigger refinement');
    } finally {
      setRefining(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center space-x-3">
            <Brain className="w-8 h-8" />
            <span>ML Performance</span>
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Monitor and improve machine learning model accuracy
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={loadAllData}
            disabled={loading}
            className="px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 
                     text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={handleTriggerRefinement}
            disabled={refining || loading}
            className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg 
                     hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed 
                     transition-all duration-200 flex items-center space-x-2"
          >
            <Zap className={`w-4 h-4 ${refining ? 'animate-pulse' : ''}`} />
            <span>{refining ? 'Refining...' : 'Trigger Refinement'}</span>
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Feedback Statistics */}
      {stats && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Feedback Statistics
          </h2>
          <FeedbackStatsComponent stats={stats} loading={loading} />
        </div>
      )}

      {/* Accuracy Trend Chart */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Model Accuracy Over Time
        </h2>
        <AccuracyChart data={accuracyTrend} loading={loading} />
      </div>

      {/* Successful Patterns */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Top Optimization Patterns
        </h2>
        <PatternList patterns={patterns} loading={loading} />
      </div>

      {/* Refinement History */}
      {refinementHistory.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Refinement History
          </h2>
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700/30">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Patterns Updated
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Accuracy Change
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {refinementHistory.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {item.refinement_type}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                        {item.description}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {item.patterns_updated}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`text-sm font-semibold ${
                            item.improvement > 0
                              ? 'text-green-600 dark:text-green-400'
                              : item.improvement < 0
                              ? 'text-red-600 dark:text-red-400'
                              : 'text-gray-600 dark:text-gray-400'
                          }`}
                        >
                          {item.improvement > 0 ? '+' : ''}
                          {(item.improvement * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${
                            item.status === 'success'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                              : item.status === 'failed'
                              ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                              : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                        {new Date(item.executed_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
