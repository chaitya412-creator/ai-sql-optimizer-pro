import { api } from './api';

// Types
export interface MLAccuracy {
  current_accuracy: number;
  total_feedback: number;
  avg_improvement: number;
  last_updated: string;
  confidence_level: string;
}

export interface MLAccuracyTrend {
  date: string;
  accuracy: number;
  feedback_count: number;
  avg_improvement: number;
  confidence: number;
}

export interface OptimizationPattern {
  id: number;
  pattern_signature: string;
  database_type: string;
  original_pattern: string;
  optimized_pattern: string;
  success_rate: number;
  usage_count: number;
  avg_improvement_pct: number;
  created_at: string;
  last_used: string;
  description?: string;
}

export interface PatternDetails extends OptimizationPattern {
  example_queries: {
    original: string;
    optimized: string;
    improvement: number;
  }[];
  applicable_scenarios: string[];
  limitations: string[];
}

export interface RefinementHistory {
  id: number;
  refinement_type: string;
  description: string;
  patterns_updated: number;
  accuracy_before: number;
  accuracy_after: number;
  improvement: number;
  executed_at: string;
  status: 'success' | 'failed' | 'partial';
}

export interface MLMetrics {
  total_optimizations: number;
  total_patterns: number;
  avg_pattern_success_rate: number;
  model_accuracy: number;
  feedback_coverage: number;
  last_refinement: string;
}

export interface TriggerRefinementRequest {
  force?: boolean;
  min_feedback_count?: number;
}

export interface TriggerRefinementResponse {
  message: string;
  refinement_id: number;
  patterns_analyzed: number;
  patterns_updated: number;
  new_accuracy: number;
}

// API Functions
export const mlService = {
  /**
   * Get current ML model accuracy
   */
  async getAccuracy(connectionId?: number): Promise<MLAccuracy> {
    const params = connectionId ? { connection_id: connectionId } : {};
    const response = await (api as any).client.get('/api/ml/accuracy', { params });
    return response.data;
  },

  /**
   * Get accuracy trend over time
   */
  async getAccuracyTrend(
    days: number = 30,
    connectionId?: number
  ): Promise<MLAccuracyTrend[]> {
    const params: any = { days };
    if (connectionId) params.connection_id = connectionId;
    const response = await (api as any).client.get('/api/ml/accuracy/trend', {
      params,
    });
    return response.data;
  },

  /**
   * Get list of successful optimization patterns
   */
  async getPatterns(params?: {
    database_type?: string;
    min_success_rate?: number;
    limit?: number;
  }): Promise<OptimizationPattern[]> {
    const response = await (api as any).client.get('/api/ml/patterns', { params });
    return response.data;
  },

  /**
   * Get detailed information about a specific pattern
   */
  async getPatternDetails(patternId: number): Promise<PatternDetails> {
    const response = await (api as any).client.get(`/api/ml/patterns/${patternId}`);
    return response.data;
  },

  /**
   * Get ML refinement history
   */
  async getRefinementHistory(limit: number = 20): Promise<RefinementHistory[]> {
    const response = await (api as any).client.get('/api/ml/refinement/history', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Trigger ML model refinement
   */
  async triggerRefinement(
    data?: TriggerRefinementRequest
  ): Promise<TriggerRefinementResponse> {
    const response = await (api as any).client.post(
      '/api/ml/refinement/trigger',
      data || {}
    );
    return response.data;
  },

  /**
   * Get overall ML metrics
   */
  async getMetrics(): Promise<MLMetrics> {
    const response = await (api as any).client.get('/api/ml/metrics');
    return response.data;
  },

  /**
   * Get pattern statistics by database type
   */
  async getPatternStats(databaseType?: string): Promise<{
    total_patterns: number;
    avg_success_rate: number;
    most_used_patterns: OptimizationPattern[];
    recent_patterns: OptimizationPattern[];
  }> {
    const params = databaseType ? { database_type: databaseType } : {};
    const response = await (api as any).client.get('/api/ml/patterns/stats', {
      params,
    });
    return response.data;
  },

  /**
   * Search patterns by query similarity
   */
  async searchPatterns(query: string, databaseType?: string): Promise<OptimizationPattern[]> {
    const params: any = { query };
    if (databaseType) params.database_type = databaseType;
    const response = await (api as any).client.get('/api/ml/patterns/search', {
      params,
    });
    return response.data;
  },

  /**
   * Health check for ML service
   */
  async healthCheck(): Promise<{ status: string; model_loaded: boolean }> {
    const response = await (api as any).client.get('/api/ml/health');
    return response.data;
  },
};

export default mlService;
