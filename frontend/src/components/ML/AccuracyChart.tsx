import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { MLAccuracyTrend } from '../../services/ml';

interface AccuracyChartProps {
  data: MLAccuracyTrend[];
  loading?: boolean;
}

export default function AccuracyChart({ data, loading = false }: AccuracyChartProps) {
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center">
        <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-600 dark:text-gray-400">No accuracy data available yet</p>
        <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
          Data will appear after collecting feedback
        </p>
      </div>
    );
  }

  // Calculate trend
  const firstAccuracy = data[0]?.accuracy || 0;
  const lastAccuracy = data[data.length - 1]?.accuracy || 0;
  const trend = lastAccuracy - firstAccuracy;
  const trendPercent = firstAccuracy > 0 ? (trend / firstAccuracy) * 100 : 0;

  const getTrendIcon = () => {
    if (Math.abs(trendPercent) < 1) {
      return <Minus className="w-5 h-5 text-gray-500" />;
    }
    return trendPercent > 0 ? (
      <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
    ) : (
      <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />
    );
  };

  const getTrendColor = () => {
    if (Math.abs(trendPercent) < 1) {
      return 'text-gray-600 dark:text-gray-400';
    }
    return trendPercent > 0
      ? 'text-green-600 dark:text-green-400'
      : 'text-red-600 dark:text-red-400';
  };

  // Format data for chart
  const chartData = data.map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    accuracy: (item.accuracy * 100).toFixed(1),
    feedbackCount: item.feedback_count,
    improvement: item.avg_improvement.toFixed(1),
  }));

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Model Accuracy Trend
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Last {data.length} days
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {getTrendIcon()}
          <div className="text-right">
            <p className={`text-lg font-semibold ${getTrendColor()}`}>
              {trendPercent > 0 ? '+' : ''}
              {trendPercent.toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Trend</p>
          </div>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
          <XAxis
            dataKey="date"
            stroke="#9CA3AF"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            stroke="#9CA3AF"
            style={{ fontSize: '12px' }}
            domain={[0, 100]}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#F9FAFB',
            }}
            formatter={(value: any, name: string) => {
              if (name === 'accuracy') return [`${value}%`, 'Accuracy'];
              if (name === 'feedbackCount') return [value, 'Feedback Count'];
              if (name === 'improvement') return [`${value}%`, 'Avg Improvement'];
              return [value, name];
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: '12px' }}
            formatter={(value) => {
              if (value === 'accuracy') return 'Accuracy';
              if (value === 'feedbackCount') return 'Feedback Count';
              if (value === 'improvement') return 'Avg Improvement';
              return value;
            }}
          />
          <Line
            type="monotone"
            dataKey="accuracy"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={{ fill: '#3B82F6', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {lastAccuracy.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Current Accuracy</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {data.reduce((sum, item) => sum + item.feedback_count, 0)}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Total Feedback</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {(data.reduce((sum, item) => sum + item.avg_improvement, 0) / data.length).toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Avg Improvement</p>
        </div>
      </div>
    </div>
  );
}
