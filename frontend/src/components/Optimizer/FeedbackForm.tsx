import { useState } from 'react';
import { Star, Send, AlertCircle, CheckCircle } from 'lucide-react';
import { feedbackService, FeedbackCreate, FeedbackMetrics } from '../../services/feedback';

interface FeedbackFormProps {
  optimizationId: number;
  beforeMetrics: FeedbackMetrics;
  afterMetrics: FeedbackMetrics;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export default function FeedbackForm({
  optimizationId,
  beforeMetrics,
  afterMetrics,
  onSuccess,
  onCancel,
}: FeedbackFormProps) {
  const [rating, setRating] = useState<number>(0);
  const [hoveredRating, setHoveredRating] = useState<number>(0);
  const [comments, setComments] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const feedbackData: FeedbackCreate = {
        optimization_id: optimizationId,
        before_metrics: beforeMetrics,
        after_metrics: afterMetrics,
        dba_rating: rating || undefined,
        dba_comments: comments || undefined,
      };

      await feedbackService.submitFeedback(feedbackData);
      setSuccess(true);
      
      setTimeout(() => {
        if (onSuccess) onSuccess();
      }, 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit feedback');
    } finally {
      setLoading(false);
    }
  };

  const calculateImprovement = () => {
    const improvement =
      ((beforeMetrics.execution_time_ms - afterMetrics.execution_time_ms) /
        beforeMetrics.execution_time_ms) *
      100;
    return improvement.toFixed(1);
  };

  if (success) {
    return (
      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
          <div>
            <h3 className="text-lg font-semibold text-green-900 dark:text-green-100">
              Feedback Submitted!
            </h3>
            <p className="text-sm text-green-700 dark:text-green-300 mt-1">
              Thank you for helping improve our optimization accuracy.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Provide Feedback
      </h3>

      {/* Performance Metrics */}
      <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Performance Comparison
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Before</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {beforeMetrics.execution_time_ms}ms
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">After</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {afterMetrics.execution_time_ms}ms
            </p>
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Improvement:{' '}
            <span
              className={`font-semibold ${
                parseFloat(calculateImprovement()) > 0
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-red-600 dark:text-red-400'
              }`}
            >
              {calculateImprovement()}%
            </span>
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Star Rating */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Rate this optimization (optional)
          </label>
          <div className="flex space-x-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => setRating(star)}
                onMouseEnter={() => setHoveredRating(star)}
                onMouseLeave={() => setHoveredRating(0)}
                className="focus:outline-none transition-transform hover:scale-110"
              >
                <Star
                  className={`w-8 h-8 ${
                    star <= (hoveredRating || rating)
                      ? 'fill-yellow-400 text-yellow-400'
                      : 'text-gray-300 dark:text-gray-600'
                  }`}
                />
              </button>
            ))}
          </div>
          {rating > 0 && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {rating === 5 && 'Excellent!'}
              {rating === 4 && 'Very Good'}
              {rating === 3 && 'Good'}
              {rating === 2 && 'Fair'}
              {rating === 1 && 'Needs Improvement'}
            </p>
          )}
        </div>

        {/* Comments */}
        <div>
          <label
            htmlFor="comments"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Additional Comments (optional)
          </label>
          <textarea
            id="comments"
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                     focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     placeholder-gray-400 dark:placeholder-gray-500"
            placeholder="Share your thoughts about this optimization..."
          />
        </div>

        {/* Error Message */}
        {error && (
          <div className="flex items-center space-x-2 text-red-600 dark:text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-4">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 
                       bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 
                       rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r 
                     from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 
                     hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed 
                     transition-all duration-200 flex items-center space-x-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Submitting...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Submit Feedback</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
