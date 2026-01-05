import { api } from './api';

// Types
export interface ConfigRecommendation {
  parameter: string;
  current_value: string;
  recommended_value: string;
  reason: string;
  impact_estimate: string;
  priority: 'high' | 'medium' | 'low';
  requires_restart: boolean;
  category: string;
}

export interface ConfigChange {
  id: number;
  connection_id: number;
  parameter: string;
  old_value: string;
  new_value: string;
  status: 'pending' | 'applied' | 'reverted' | 'failed';
  applied_at?: string;
  reverted_at?: string;
  impact_measured?: boolean;
  performance_impact?: number;
  created_at: string;
}

export interface ConfigApplyRequest {
  connection_id: number;
  parameter: string;
  new_value: string;
  test_mode?: boolean;
}

export interface ConfigValidation {
  valid: boolean;
  errors: string[];
  warnings: string[];
  safe_to_apply: boolean;
}

export interface WorkloadAnalysis {
  connection_id: number;
  workload_type: 'OLTP' | 'OLAP' | 'Mixed';
  peak_hours: number[];
  avg_query_rate: number;
  avg_execution_time: number;
  total_queries: number;
  slow_queries_count: number;
  analysis_period: string;
  insights: string[];
}

export interface WorkloadPattern {
  hourly_pattern: { hour: number; query_count: number; avg_time: number }[];
  daily_pattern: { day: string; query_count: number; avg_time: number }[];
  query_types: { type: string; count: number; percentage: number }[];
  resource_usage: {
    cpu_avg: number;
    memory_avg: number;
    io_avg: number;
  };
}

export interface WorkloadShift {
  detected_at: string;
  shift_type: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  recommendation: string;
}

export interface ImpactMeasurement {
  change_id: number;
  before_metrics: {
    avg_execution_time: number;
    query_rate: number;
    cpu_usage: number;
    memory_usage: number;
  };
  after_metrics: {
    avg_execution_time: number;
    query_rate: number;
    cpu_usage: number;
    memory_usage: number;
  };
  improvement_pct: number;
  success: boolean;
  measured_at: string;
}

// API Functions
export const configurationService = {
  /**
   * Get configuration recommendations for a connection
   */
  async getRecommendations(connectionId: number): Promise<ConfigRecommendation[]> {
    const response = await (api as any).client.get(
      `/api/config/recommendations/${connectionId}`
    );
    return response.data;
  },

  /**
   * Get database-specific configuration rules
   */
  async getConfigRules(databaseType: string): Promise<any> {
    const response = await (api as any).client.get(
      `/api/config/rules/${databaseType}`
    );
    return response.data;
  },

  /**
   * Apply a configuration change
   */
  async applyChange(data: ConfigApplyRequest): Promise<ConfigChange> {
    const response = await (api as any).client.post('/api/config/apply', data);
    return response.data;
  },

  /**
   * Revert a configuration change
   */
  async revertChange(changeId: number): Promise<ConfigChange> {
    const response = await (api as any).client.post(
      `/api/config/revert/${changeId}`
    );
    return response.data;
  },

  /**
   * Validate a configuration change before applying
   */
  async validateChange(data: {
    connection_id: number;
    parameter: string;
    new_value: string;
  }): Promise<ConfigValidation> {
    const response = await (api as any).client.post('/api/config/validate', data);
    return response.data;
  },

  /**
   * Get configuration change history
   */
  async getChangeHistory(connectionId: number): Promise<ConfigChange[]> {
    const response = await (api as any).client.get(
      `/api/config/history/${connectionId}`
    );
    return response.data;
  },

  /**
   * Get workload analysis for a connection
   */
  async getWorkloadAnalysis(connectionId: number): Promise<WorkloadAnalysis> {
    const response = await (api as any).client.get(
      `/api/config/workload/analysis/${connectionId}`
    );
    return response.data;
  },

  /**
   * Get detailed workload pattern
   */
  async getWorkloadPattern(connectionId: number): Promise<WorkloadPattern> {
    const response = await (api as any).client.get(
      `/api/config/workload/pattern/${connectionId}`
    );
    return response.data;
  },

  /**
   * Detect workload shifts
   */
  async detectWorkloadShifts(connectionId: number): Promise<WorkloadShift[]> {
    const response = await (api as any).client.get(
      `/api/config/workload/shifts/${connectionId}`
    );
    return response.data;
  },

  /**
   * Measure impact of a configuration change
   */
  async measureImpact(changeId: number): Promise<ImpactMeasurement> {
    const response = await (api as any).client.post(
      `/api/config/impact/measure/${changeId}`
    );
    return response.data;
  },

  /**
   * Health check for configuration service
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await (api as any).client.get('/api/config/health');
    return response.data;
  },
};

export default configurationService;
