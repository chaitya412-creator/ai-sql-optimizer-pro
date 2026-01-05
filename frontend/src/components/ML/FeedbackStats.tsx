import { MessageSquare, Target, TrendingUp, CheckCircle, BarChart3 } from 'lucide-react';
import { FeedbackStats as FeedbackStatsType } from '../../services/feedback';

interface FeedbackStatsProps {
  stats: FeedbackStatsType;
  loading?: boolean;
}

export default function FeedbackStats({ stats, loading = false }: FeedbackStatsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6"
          >
            <div className="animate-pulse space-y-3">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Feedback',
      value: stats.total_feedback,
      icon: MessageSquare,
      color: 'blue',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
      iconColor: 'text-blue-600 dark:text-blue-400',
      description: 'Feedback submissions',
    },
    {
      title: 'Model Accuracy',
      value: `${(stats.avg_accuracy * 100).toFixed(1)}%`,
      icon: Target,
      color: 'green',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      iconColor: 'text-green-600 dark:text-green-400',
      description: 'Average prediction accuracy',
    },
    {
      title: 'Avg Improvement',
      value: `${stats.avg_improvement.toFixed(1)}%`,
      icon: TrendingUp,
      color: 'purple',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30',
      iconColor: 'text-purple-600 dark:text-purple-400',
      description: 'Performance gain',
    },
    {
      title: 'Success Rate',
      value: `${(stats.success_rate * 100).toFixed(1)}%`,
      icon: CheckCircle,
      color: 'emerald',
      bgColor: 'bg-emerald-100 dark:bg-emerald-900/30',
      iconColor: 'text-emerald-600 dark:text-emerald-400',
      description: 'Successful optimizations',
    },
    {
      title: 'Total Optimizations',
      value: stats.total_optimizations,
      icon: BarChart3,
      color: 'orange',
      bgColor: 'bg-orange-100 dark:bg-orange-900/30',
      iconColor: 'text-orange-600 dark:text-orange-400',
      description: 'Queries optimized',
    },
    {
      title: 'Feedback Rate',
      value: `${(stats.feedback_rate * 100).toFixed(1)}%`,
      icon: MessageSquare,
      color: 'indigo',
      bgColor: 'bg-indigo-100 dark:bg-indigo-900/30',
      iconColor: 'text-indigo-600 dark:text-indigo-400',
      description: 'Feedback coverage',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {statCards.map((card, index) => (
        <div
          key={index}
          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-lg transition-shadow"
        >
          {/* Icon */}
          <div className={`w-12 h-12 ${card.bgColor} rounded-lg flex items-center justify-center mb-4`}>
            <card.icon className={`w-6 h-6 ${card.iconColor}`} />
          </div>

          {/* Title */}
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
            {card.title}
          </h3>

          {/* Value */}
          <p className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            {card.value}
          </p>

          {/* Description */}
          <p className="text-xs text-gray-500 dark:text-gray-500">
            {card.description}
          </p>

          {/* Progress Bar (for percentage values) */}
          {typeof card.value === 'string' && card.value.includes('%') && (
            <div className="mt-3">
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full bg-gradient-to-r from-${card.color}-500 to-${card.color}-600`}
                  style={{
                    width: card.value,
                  }}
                ></div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
