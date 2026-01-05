import { api } from './api';

// TypeScript interfaces
export interface HourlyPattern {
  hourly_averages: Record<number, {
    avg_queries: number;
    avg_exec_time: number;
    avg_cpu: number;
    avg_io: number;
  }>;
  peak_hours: number[];
  off_peak_hours: number[];
}

export interface DailyPattern {
  daily_averages: Record<string, {
    avg_queries: number;
    avg_exec_time: number;
  }>;
  busiest_day: string;
  quietest_day: string;
}

export interface QueryPattern {
  total_queries: number;
  unique_queries: number;
  total_calls: number;
  avg_calls_per_query: number;
  slow_queries_count: number;
  slow_queries_pct: number;
  most_frequent: Array<{
    query_id: number;
    calls: number;
    avg_time_ms: number;
  }>;
  most_expensive: Array<{
    query_id: number;
    total_time_ms: number;
    calls: number;
  }>;
}

export interface ResourcePattern {
  cpu: {
    avg: number;
    max: number;
    min: number;
  };
  io: {
    avg: number;
    max: number;
    min: number;
  };
  memory: {
    avg: number;
    max: number;
    min: number;
  };
}

export interface Trends {
  query_volume_trend: 'increasing' | 'decreasing' | 'stable';
  execution_time_trend: 'increasing' | 'decreasing' | 'stable';
  first_period_avg_queries: number;
  second_period_avg_queries: number;
  first_period_avg_time: number;
  second_period_avg_time: number;
}

export interface WorkloadShift {
  detected_at: string;
  query_volume_change_pct: number;
  execution_time_change_pct: number;
  severity: 'high' | 'medium' | 'low';
}

export interface Recommendation {
  type: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  action: string;
  estimated_impact: string;
  [key: string]: any;
}

export interface PerformancePrediction {
  status: string;
  analysis_period_days?: number;
  query_volume?: {
    current_avg: number;
    predicted_next_period: number;
    growth_rate_pct: number;
    trend: 'increasing' | 'decreasing' | 'stable';
  };
  execution_time?: {
    current_avg_ms: number;
    predicted_next_period_ms: number;
    growth_rate_pct: number;
    trend: 'increasing' | 'decreasing' | 'stable';
  };
  warnings?: string[];
  confidence?: 'high' | 'medium' | 'low';
  predicted_at?: string;
  message?: string;
}

export interface WorkloadAnalysis {
  connection_id: number;
  database_type: string;
  analysis_period_days: number;
  workload_type: 'oltp' | 'olap' | 'mixed' | 'unknown';
  hourly_pattern: HourlyPattern;
  daily_pattern: DailyPattern;
  query_pattern: QueryPattern;
  resource_pattern: ResourcePattern;
  trends: Trends;
  insights: string[];
  analyzed_at: string;
  recommendations?: Recommendation[];
  predictions?: PerformancePrediction;
}

export interface WorkloadPatterns {
  connection_id: number;
  analysis_period_days: number;
  workload_type: string;
  hourly_pattern: HourlyPattern;
  daily_pattern: DailyPattern;
  query_pattern: QueryPattern;
  resource_pattern: ResourcePattern;
  peak_hours: number[];
  off_peak_hours: number[];
  busiest_day: string;
  quietest_day: string;
  analyzed_at: string;
}

export interface PerformanceTrends {
  connection_id: number;
  analysis_period_days: number;
  historical_trends: Trends;
  predictions: PerformancePrediction;
  workload_shifts: WorkloadShift[];
  shift_count: number;
  analyzed_at: string;
}

export interface RecommendationsResponse {
  connection_id: number;
  analysis_period_days: number;
  total_recommendations: number;
  high_priority_count: number;
  medium_priority_count: number;
  low_priority_count: number;
  recommendations: Recommendation[];
}

// API functions
export const workloadService = {
  /**
   * Get comprehensive workload analysis
   */
  getAnalysis: async (connectionId: number, days: number = 7): Promise<WorkloadAnalysis> => {
    const response = await api['client'].get(`/api/workload/analysis/${connectionId}`, {
      params: { days }
    });
    return response.data;
  },

  /**
   * Get workload patterns
   */
  getPatterns: async (connectionId: number, days: number = 7): Promise<WorkloadPatterns> => {
    const response = await api['client'].get(`/api/workload/patterns/${connectionId}`, {
      params: { days }
    });
    return response.data;
  },

  /**
   * Get performance trends
   */
  getTrends: async (connectionId: number, days: number = 7): Promise<PerformanceTrends> => {
    const response = await api['client'].get(`/api/workload/trends/${connectionId}`, {
      params: { days }
    });
    return response.data;
  },

  /**
   * Get proactive recommendations
   */
  getRecommendations: async (connectionId: number, days: number = 7): Promise<RecommendationsResponse> => {
    const response = await api['client'].get(`/api/workload/recommendations/${connectionId}`, {
      params: { days }
    });
    return response.data;
  },

  /**
   * Trigger workload analysis
   */
  triggerAnalysis: async (
    connectionId: number,
    days: number = 7,
    includeRecommendations: boolean = true,
    includePredictions: boolean = true
  ): Promise<any> => {
    const response = await api['client'].post('/api/workload/analyze', null, {
      params: {
        connection_id: connectionId,
        days,
        include_recommendations: includeRecommendations,
        include_predictions: includePredictions
      }
    });
    return response.data;
  }
};

export default workloadService;
