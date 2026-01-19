import axios, { AxiosInstance } from 'axios';
import type {
  Connection,
  ConnectionCreate,
  ConnectionTest,
  OptimizationRequest,
  OptimizationResult,
  MonitoringStatus,
  DashboardStats,
  TopQuery,
  Query,
  PerformanceTrend,
  DetectionSummary,
  QueryWithIssues,
  ExecutionPlanExplanation,
  ExplainPlanRequest,
  GenerateFixesRequest,
  GenerateFixesResponse,
  ApplyFixRequest,
  ApplyFixResult,
  ValidatePerformanceRequest,
  PerformanceValidation,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  private static readonly LONG_RUNNING_TIMEOUT_MS = 300000; // 5 minutes

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health Check
  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }

  // Connection APIs
  async getConnections(): Promise<Connection[]> {
    // FastAPI redirects `/api/connections` -> `/api/connections/`.
    // Avoid CORS/redirect edge cases by hitting the canonical route.
    const response = await this.client.get('/api/connections/');
    return response.data;
  }

  async getConnection(id: number): Promise<Connection> {
    const response = await this.client.get(`/api/connections/${id}`);
    return response.data;
  }

  async createConnection(data: ConnectionCreate): Promise<Connection> {
    const response = await this.client.post('/api/connections', data);
    return response.data;
  }

  async updateConnection(id: number, data: Partial<ConnectionCreate>): Promise<Connection> {
    const response = await this.client.put(`/api/connections/${id}`, data);
    return response.data;
  }

  async deleteConnection(id: number): Promise<void> {
    await this.client.delete(`/api/connections/${id}`);
  }

  async testConnection(id: number): Promise<ConnectionTest> {
    const response = await this.client.post(`/api/connections/${id}/test`);
    return response.data;
  }

  // Monitoring APIs
  async getMonitoringStatus(): Promise<MonitoringStatus> {
    const response = await this.client.get('/api/monitoring/status');
    return response.data;
  }

  async startMonitoring(): Promise<{ message: string }> {
    const response = await this.client.post('/api/monitoring/start');
    return response.data;
  }

  async stopMonitoring(): Promise<{ message: string }> {
    const response = await this.client.post('/api/monitoring/stop');
    return response.data;
  }

  async triggerMonitoring(): Promise<{ message: string }> {
    const response = await this.client.post('/api/monitoring/trigger');
    return response.data;
  }

  async getDiscoveredQueries(connectionId?: number): Promise<Query[]> {
    const params = connectionId ? { connection_id: connectionId } : {};
    const response = await this.client.get('/api/monitoring/queries', { params });
    return response.data;
  }

  async getDiscoveredQuery(queryId: number): Promise<Query> {
    const response = await this.client.get(`/api/monitoring/queries/${queryId}`);
    return response.data;
  }

  async getMonitoringIssues(params?: {
    connection_id?: number;
    severity?: string;
    issue_type?: string;
    resolved?: boolean;
    limit?: number;
  }): Promise<any[]> {
    const response = await this.client.get('/api/monitoring/issues', { params });
    return response.data;
  }

  async getIssuesSummary(connectionId?: number): Promise<any> {
    const params = connectionId ? { connection_id: connectionId } : {};
    const response = await this.client.get('/api/monitoring/issues/summary', { params });
    return response.data;
  }

  async generateCorrectedCode(issueId: number): Promise<any> {
    const response = await this.client.post(
      `/api/monitoring/issues/${issueId}/generate-corrected-code`,
      undefined,
      { timeout: ApiClient.LONG_RUNNING_TIMEOUT_MS }
    );
    return response.data;
  }

  async generateOptimizedQuery(queryId: number): Promise<any> {
    const response = await this.client.post(
      `/api/monitoring/queries/${queryId}/generate-optimized-query`,
      undefined,
      { timeout: ApiClient.LONG_RUNNING_TIMEOUT_MS }
    );
    return response.data;
  }

  // Optimizer APIs
  async optimizeQuery(data: OptimizationRequest): Promise<OptimizationResult> {
    const response = await this.client.post('/api/optimizer/optimize', data);
    return response.data;
  }

  async explainExecutionPlan(data: ExplainPlanRequest): Promise<ExecutionPlanExplanation> {
    const response = await this.client.post('/api/optimizer/explain-plan', data);
    return response.data;
  }

  async generateFixRecommendations(data: GenerateFixesRequest): Promise<GenerateFixesResponse> {
    const response = await this.client.post('/api/optimizer/generate-fixes', data);
    return response.data;
  }

  async applyFix(data: ApplyFixRequest): Promise<ApplyFixResult> {
    const response = await this.client.post('/api/optimizer/apply-fix', data);
    return response.data;
  }

  async validatePerformance(data: ValidatePerformanceRequest): Promise<PerformanceValidation> {
    const response = await this.client.post('/api/optimizer/validate-performance', data);
    return response.data;
  }

  // Dashboard APIs
  async getDashboardStats(connectionId?: number): Promise<DashboardStats> {
    const params = connectionId ? { connection_id: connectionId } : {};
    const response = await this.client.get('/api/dashboard/stats', { params });
    return response.data;
  }

  async getTopQueries(limit: number = 10, connectionId?: number): Promise<TopQuery[]> {
    const params: any = { limit };
    if (connectionId) {
      params.connection_id = connectionId;
    }
    const response = await this.client.get('/api/dashboard/top-queries', { params });
    return response.data;
  }

  async getPerformanceTrends(hours: number = 24, connectionId?: number): Promise<PerformanceTrend[]> {
    const params: any = { hours };
    if (connectionId) {
      params.connection_id = connectionId;
    }
    const response = await this.client.get('/api/dashboard/performance-trends', { params });
    return response.data;
  }

  async getDetectionSummary(connectionId?: number): Promise<DetectionSummary> {
    const params = connectionId ? { connection_id: connectionId } : {};
    const response = await this.client.get('/api/dashboard/detection-summary', { params });
    return response.data;
  }

  async getQueriesWithIssues(limit: number = 20, connectionId?: number): Promise<QueryWithIssues[]> {
    const params: any = { limit };
    if (connectionId) {
      params.connection_id = connectionId;
    }
    const response = await this.client.get('/api/dashboard/queries-with-issues', { params });
    return response.data;
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export individual methods for convenience with proper binding
export const healthCheck = () => api.healthCheck();
export const getConnections = () => api.getConnections();
export const getConnection = (id: number) => api.getConnection(id);
export const createConnection = (data: ConnectionCreate) => api.createConnection(data);
export const updateConnection = (id: number, data: Partial<ConnectionCreate>) => api.updateConnection(id, data);
export const deleteConnection = (id: number) => api.deleteConnection(id);
export const testConnection = (id: number) => api.testConnection(id);
export const getMonitoringStatus = () => api.getMonitoringStatus();
export const startMonitoring = () => api.startMonitoring();
export const stopMonitoring = () => api.stopMonitoring();
export const triggerMonitoring = () => api.triggerMonitoring();
export const getDiscoveredQueries = (connectionId?: number) => api.getDiscoveredQueries(connectionId);
export const getDiscoveredQuery = (queryId: number) => api.getDiscoveredQuery(queryId);
export const getMonitoringIssues = (params?: any) => api.getMonitoringIssues(params);
export const getIssuesSummary = (connectionId?: number) => api.getIssuesSummary(connectionId);
export const generateCorrectedCode = (issueId: number) => api.generateCorrectedCode(issueId);
export const generateOptimizedQuery = (queryId: number) => api.generateOptimizedQuery(queryId);
export const optimizeQuery = (data: OptimizationRequest) => api.optimizeQuery(data);
export const explainExecutionPlan = (data: ExplainPlanRequest) => api.explainExecutionPlan(data);
export const generateFixRecommendations = (data: GenerateFixesRequest) => api.generateFixRecommendations(data);
export const applyFix = (data: ApplyFixRequest) => api.applyFix(data);
export const validatePerformance = (data: ValidatePerformanceRequest) => api.validatePerformance(data);
export const getDashboardStats = (connectionId?: number) => api.getDashboardStats(connectionId);
export const getTopQueries = (limit?: number, connectionId?: number) => api.getTopQueries(limit, connectionId);
export const getPerformanceTrends = (hours?: number, connectionId?: number) => api.getPerformanceTrends(hours, connectionId);
export const getDetectionSummary = (connectionId?: number) => api.getDetectionSummary(connectionId);
export const getQueriesWithIssues = (limit?: number, connectionId?: number) => api.getQueriesWithIssues(limit, connectionId);

export default api;
