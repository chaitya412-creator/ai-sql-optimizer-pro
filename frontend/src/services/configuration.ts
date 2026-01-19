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
    // Map backend snake_case to frontend interface
    if (Array.isArray(response.data)) {
      return response.data.map((item: any) => ({
        parameter: item.parameter_name,
        current_value: item.current_value,
        recommended_value: item.recommended_value,
        reason: item.change_reason,
        impact_estimate: typeof item.estimated_impact === 'object' 
          ? Object.entries(item.estimated_impact).map(([k, v]) => `${k}: ${v}`).join(', ')
          : String(item.estimated_impact || 'Moderate'),
        priority: item.priority,
        requires_restart: false, 
        category: item.database_type || 'General'
      }));
    }
    return [];
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
    const payload = {
      connection_id: data.connection_id,
      parameter_name: data.parameter,
      new_value: data.new_value,
      change_reason: "Manual application via UI",
      dry_run: false
    };
    
    const response = await (api as any).client.post('/api/config/apply', payload);
    const item = response.data;
    return {
      id: item.id,
      connection_id: item.connection_id,
      parameter: item.parameter_name,
      old_value: item.old_value,
      new_value: item.new_value,
      status: item.status,
      applied_at: item.applied_at,
      reverted_at: item.reverted_at,
      impact_measured: !!item.actual_impact,
      performance_impact: 0, 
      created_at: item.applied_at
    };
  },

  /**
   * Revert a configuration change
   */
  async revertChange(changeId: number): Promise<ConfigChange> {
    const response = await (api as any).client.post(
      `/api/config/revert/${changeId}`
    );
    const item = response.data;
    return {
      id: item.id,
      connection_id: item.connection_id,
      parameter: item.parameter_name,
      old_value: item.old_value,
      new_value: item.new_value,
      status: item.status,
      applied_at: item.applied_at,
      reverted_at: item.reverted_at,
      impact_measured: !!item.actual_impact,
      performance_impact: 0, 
      created_at: item.applied_at || new Date().toISOString()
    };
  },

  /**
   * Validate a configuration change before applying
   */
  async validateChange(data: {
    connection_id: number;
    parameter: string;
    new_value: string;
  }): Promise<ConfigValidation> {
    const response = await (api as any).client.post('/api/config/validate', {
        ...data,
        parameter_name: data.parameter
    });
    return response.data;
  },

  /**
   * Get configuration change history
   */
  async getChangeHistory(connectionId: number): Promise<ConfigChange[]> {
    const response = await (api as any).client.get(
      `/api/config/history/${connectionId}`
    );
    if (Array.isArray(response.data)) {
        return response.data.map((item: any) => ({
          id: item.id,
          connection_id: item.connection_id,
          parameter: item.parameter_name,
          old_value: item.old_value,
          new_value: item.new_value,
          status: item.status,
          applied_at: item.applied_at,
          reverted_at: item.reverted_at,
          impact_measured: !!item.actual_impact,
          performance_impact: 0, 
          created_at: item.applied_at || new Date().toISOString()
        }));
    }
    return [];
  },

  /**
   * Get workload analysis for a connection
   */
  async getWorkloadAnalysis(connectionId: number): Promise<WorkloadAnalysis> {
    const response = await (api as any).client.get(
      `/api/config/workload/analysis/${connectionId}`
    );
    const data = response.data;
    return {
      connection_id: data.connection_id,
      workload_type: data.workload_type as 'OLTP' | 'OLAP' | 'Mixed',
      peak_hours: data.peak_hours,
      avg_query_rate: data.avg_query_rate,
      avg_execution_time: data.avg_execution_time,
      total_queries: data.total_queries,
      slow_queries_count: data.slow_queries_count,
      analysis_period: `${data.analysis_period_days || 7} days`,
      insights: data.insights
    };
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
