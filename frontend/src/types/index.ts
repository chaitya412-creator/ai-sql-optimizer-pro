// Database Connection Types
export interface Connection {
  id: number;
  name: string;
  engine: 'postgresql' | 'mysql' | 'oracle' | 'mssql';
  host: string;
  port: number;
  database: string;
  username: string;
  ssl_enabled: boolean;
  monitoring_enabled: boolean;
  created_at: string;
  updated_at: string;
  last_monitored_at?: string;
}

export interface ConnectionCreate {
  name: string;
  engine: 'postgresql' | 'mysql' | 'oracle' | 'mssql';
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl_enabled?: boolean;
  monitoring_enabled?: boolean;
}

export interface ConnectionTest {
  success: boolean;
  message: string;
  latency_ms?: number;
}

// Query Types
export interface Query {
  id: number;
  connection_id: number;
  sql_text: string;
  avg_execution_time: number;
  total_execution_time: number;
  calls: number;
  discovered_at: string;
  last_seen: string;
}

// Detection Types
export interface DetectedIssue {
  issue_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  affected_objects: string[];
  recommendations: string[];
  metrics: Record<string, any>;
  detected_at: string;
}

export interface DetectionResult {
  issues: DetectedIssue[];
  recommendations: string[];
  summary: string;
  total_issues: number;
  critical_issues: number;
  high_issues: number;
  medium_issues: number;
  low_issues: number;
}

// Optimization Types
export interface OptimizationRequest {
  query_id?: number;
  connection_id: number;
  sql_query: string;
  include_execution_plan: boolean;
}

export interface OptimizationResult {
  id: number;
  query_id?: number;
  connection_id: number;
  original_sql: string;
  optimized_sql: string;
  execution_plan?: any;
  explanation: string;
  recommendations?: string;
  estimated_improvement_pct?: number;
  status: string;
  created_at: string;
  applied_at?: string;
  validated_at?: string;
  detected_issues?: DetectionResult;  // New field for detected issues
}

export interface ExecutionPlan {
  plan_text: string;
  plan_json?: any;
  issues: PlanIssue[];
  total_cost: number;
  estimated_rows: number;
}

export interface PlanIssue {
  type: 'sequential_scan' | 'nested_loop' | 'high_cost' | 'cardinality_mismatch';
  severity: 'low' | 'medium' | 'high';
  description: string;
  table_name?: string;
  suggestion?: string;
}

// Monitoring Types
export interface MonitoringStatus {
  is_running: boolean;
  last_poll_time?: string;
  next_poll_time?: string;
  interval_minutes: number;
  queries_discovered: number;
  active_connections: number;
}

export interface MonitoringConfig {
  enabled: boolean;
  interval_minutes: number;
  max_queries_per_poll: number;
}

// Dashboard Types
export interface DashboardStats {
  total_connections: number;
  active_connections: number;
  total_queries_discovered: number;
  total_optimizations: number;
  optimizations_applied: number;
  avg_improvement_pct?: number;
  top_bottlenecks: any[];
  optimizations_with_issues: number;
  total_detected_issues: number;
}

export interface TopQuery {
  id: number;
  connection_name: string;
  sql_text: string;
  avg_execution_time: number;
  total_execution_time: number;
  calls: number;
  severity: 'low' | 'medium' | 'high';
}

export interface PerformanceTrend {
  timestamp: string;
  avg_time: number;
  slow_queries: number;
  total_queries: number;
}

export interface IssueTypeSummary {
  issue_type: string;
  count: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface CriticalIssuePreview {
  optimization_id: number;
  connection_name: string;
  issue_type: string;
  severity: string;
  title: string;
  description: string;
  detected_at: string;
}

export interface DetectionSummary {
  total_issues: number;
  critical_issues: number;
  high_issues: number;
  medium_issues: number;
  low_issues: number;
  issues_by_type: IssueTypeSummary[];
  recent_critical_issues: CriticalIssuePreview[];
  total_optimizations_with_issues: number;
  last_updated: string;
}

export interface IssueDetail {
  issue_type: string;
  severity: string;
  title: string;
  description: string;
  recommendations: string[];
}

export interface QueryWithIssues {
  optimization_id: number;
  connection_id: number;
  connection_name: string;
  original_sql: string;
  optimized_sql: string;  // Add optimized SQL
  sql_preview: string;
  issue_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  issues: IssueDetail[];
  detected_at: string;
  recommendations?: string;  // Add recommendations
  estimated_improvement_pct?: number;  // Add improvement percentage
}

// UI Component Types
export interface TableColumn<T> {
  key: keyof T;
  label: string;
  render?: (value: any, row: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// Chart Data Types
export interface ChartDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface ChartConfig {
  xAxisKey: string;
  yAxisKey: string;
  color: string;
  label: string;
}

// Execution Plan Explanation Types
export interface ExecutionPlanExplanation {
  success: boolean;
  explanation: string;
  summary: string;
  key_operations: string[];
  bottlenecks: string[];
  estimated_cost?: number;
}

export interface ExplainPlanRequest {
  connection_id: number;
  sql_query: string;
  execution_plan?: any;
}

// Fix Recommendation Types
export interface FixRecommendation {
  fix_type: string;
  sql: string;
  description: string;
  estimated_impact: 'low' | 'medium' | 'high';
  affected_objects: string[];
  safety_level: 'safe' | 'caution' | 'dangerous';
  estimated_cpu_savings?: string;
  estimated_io_savings?: string;
  estimated_latency_savings?: string;
}

export interface GenerateFixesRequest {
  optimization_id: number;
  include_indexes?: boolean;
  include_maintenance?: boolean;
  include_rewrites?: boolean;
  include_config?: boolean;
}

export interface GenerateFixesResponse {
  success: boolean;
  optimization_id: number;
  index_recommendations: FixRecommendation[];
  maintenance_tasks: FixRecommendation[];
  query_rewrites: FixRecommendation[];
  configuration_changes: FixRecommendation[];
  total_fixes: number;
  high_impact_count: number;
}

// Apply Fix Types
export interface SafetyCheckResult {
  passed: boolean;
  checks_performed: string[];
  warnings: string[];
  errors: string[];
}

export interface ApplyFixRequest {
  optimization_id: number;
  fix_type: string;
  fix_sql: string;
  dry_run?: boolean;
  skip_safety_checks?: boolean;
}

export interface ApplyFixResult {
  success: boolean;
  fix_id?: number;
  fix_type: string;
  status: string;
  message: string;
  execution_time_sec?: number;
  rollback_sql?: string;
  safety_checks?: SafetyCheckResult;
  applied_at?: string;
}

// Performance Validation Types
export interface PerformanceMetrics {
  execution_time_ms: number;
  planning_time_ms?: number;
  rows_returned?: number;
  buffer_hits?: number;
  buffer_reads?: number;
  io_cost?: number;
}

export interface ValidatePerformanceRequest {
  optimization_id: number;
  run_original?: boolean;
  run_optimized?: boolean;
  iterations?: number;
}

export interface PerformanceValidation {
  success: boolean;
  optimization_id: number;
  original_metrics?: PerformanceMetrics;
  optimized_metrics?: PerformanceMetrics;
  improvement_pct?: number;
  improvement_ms?: number;
  is_faster: boolean;
  validation_notes: string[];
  validated_at: string;
}
