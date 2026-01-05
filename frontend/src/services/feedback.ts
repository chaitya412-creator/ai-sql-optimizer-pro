import { api } from './api';

// Types
export interface FeedbackMetrics {
  execution_time_ms: number;
  rows_affected?: number;
  cpu_usage?: number;
  io_operations?: number;
  memory_usage?: number;
}

export interface FeedbackCreate {
  optimization_id: number;
  before_metrics: FeedbackMetrics;
  after_metrics: FeedbackMetrics;
  dba_rating?: number;
  dba_comments?: string;
}

export interface FeedbackResponse {
  id: number;
  optimization_id: number;
  before_metrics: FeedbackMetrics;
  after_metrics: FeedbackMetrics;
  actual_improvement_pct: number;
  estimated_improvement_pct: number;
  accuracy_score: number;
  dba_rating?: number;
  dba_comments?: string;
  feedback_status: string;
  created_at: string;
  updated_at?: string;
}

export interface FeedbackStats {
  total_feedback: number;
  avg_accuracy: number;
  avg_improvement: number;
  success_rate: number;
  total_optimizations: number;
  feedback_rate: number;
}

export interface AccuracyMetrics {
  current_accuracy: number;
  total_feedback: number;
  avg_improvement: number;
  last_updated: string;
}

export interface AccuracyTrend {
  date: string;
  accuracy: number;
  feedback_count: number;
  avg_improvement: number;
}

// API Functions
export const feedbackService = {
  /**
   * Submit feedback for an optimization
   */
  async submitFeedback(data: FeedbackCreate): Promise<FeedbackResponse> {
    const response = await (api as any).client.post('/api/feedback', data);
    return response.data;
  },

  /**
   * Get feedback for a specific optimization
   */
  async getFeedback(optimizationId: number): Promise<FeedbackResponse> {
    const response = await (api as any).client.get(`/api/feedback/${optimizationId}`);
    return response.data;
  },

  /**
   * List all feedback with optional filters
   */
  async listFeedback(params?: {
    connection_id?: number;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<FeedbackResponse[]> {
    const response = await (api as any).client.get('/api/feedback/list/all', { params });
    return response.data;
  },

  /**
   * Update existing feedback
   */
  async updateFeedback(
    id: number,
    data: Partial<FeedbackCreate>
  ): Promise<FeedbackResponse> {
    const response = await (api as any).client.put(`/api/feedback/${id}`, data);
    return response.data;
  },

  /**
   * Get feedback statistics
   */
  async getStats(connectionId?: number): Promise<FeedbackStats> {
    const params = connectionId ? { connection_id: connectionId } : {};
    const response = await (api as any).client.get('/api/feedback/stats/summary', { params });
    return response.data;
  },

  /**
   * Get current accuracy metrics
   */
  async getAccuracy(connectionId?: number): Promise<AccuracyMetrics> {
    const params = connectionId ? { connection_id: connectionId } : {};
    const response = await (api as any).client.get('/api/feedback/accuracy/current', { params });
    return response.data;
  },

  /**
   * Get accuracy trend over time
   */
  async getAccuracyTrend(days: number = 30, connectionId?: number): Promise<AccuracyTrend[]> {
    const params: any = { days };
    if (connectionId) params.connection_id = connectionId;
    const response = await (api as any).client.get('/api/feedback/accuracy/trend', { params });
    return response.data;
  },
};

export default feedbackService;
