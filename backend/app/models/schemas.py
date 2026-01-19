"""
Pydantic Schemas for API Request/Response Validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DatabaseEngine(str, Enum):
    """Supported database engines"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    MSSQL = "mssql"


class OptimizationStatus(str, Enum):
    """Optimization status"""
    PENDING = "pending"
    APPLIED = "applied"
    VALIDATED = "validated"
    FAILED = "failed"


class IssueType(str, Enum):
    """Types of SQL optimization issues"""
    MISSING_INDEX = "missing_index"
    INEFFICIENT_INDEX = "inefficient_index"
    POOR_JOIN_STRATEGY = "poor_join_strategy"
    FULL_TABLE_SCAN = "full_table_scan"
    SUBOPTIMAL_PATTERN = "suboptimal_pattern"
    STALE_STATISTICS = "stale_statistics"
    WRONG_CARDINALITY = "wrong_cardinality"
    ORM_GENERATED = "orm_generated"
    HIGH_IO_WORKLOAD = "high_io_workload"
    INEFFICIENT_REPORTING = "inefficient_reporting"


class IssueSeverity(str, Enum):
    """Severity levels for detected issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Connection Schemas
class ConnectionCreate(BaseModel):
    """Create connection request"""
    name: str = Field(..., min_length=1, max_length=255)
    engine: DatabaseEngine
    host: str = Field(..., min_length=1)
    port: int = Field(..., gt=0, lt=65536)
    database: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    ssl_enabled: bool = False
    monitoring_enabled: bool = True


class ConnectionUpdate(BaseModel):
    """Update connection request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    host: Optional[str] = None
    port: Optional[int] = Field(None, gt=0, lt=65536)
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_enabled: Optional[bool] = None
    monitoring_enabled: Optional[bool] = None


class ConnectionResponse(BaseModel):
    """Connection response"""
    id: int
    name: str
    engine: str
    host: str
    port: int
    database: str
    username: str
    ssl_enabled: bool
    monitoring_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_monitored_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True
    
    @property
    def db_type(self) -> str:
        """Alias for engine field to match frontend expectations"""
        return self.engine


class ConnectionTestResponse(BaseModel):
    """Connection test response"""
    success: bool
    message: str
    latency_ms: Optional[float] = None


# Query Schemas
class QueryResponse(BaseModel):
    """Query response"""
    id: int
    connection_id: int
    query_hash: str
    sql_text: str
    avg_execution_time: float
    total_execution_time: float
    calls: int
    rows_returned: Optional[int] = None
    buffer_hits: Optional[int] = None
    buffer_reads: Optional[int] = None
    discovered_at: datetime
    last_seen: datetime
    optimized: bool
    
    class Config:
        from_attributes = True
        populate_by_name = True
    
    @classmethod
    def from_orm(cls, obj):
        """Custom ORM mapping to handle field name differences"""
        return cls(
            id=obj.id,
            connection_id=obj.connection_id,
            query_hash=obj.query_hash,
            sql_text=obj.sql_text,
            avg_execution_time=obj.avg_exec_time_ms,
            total_execution_time=obj.total_exec_time_ms,
            calls=obj.calls,
            rows_returned=obj.rows_returned,
            buffer_hits=obj.buffer_hits,
            buffer_reads=obj.buffer_reads,
            discovered_at=obj.discovered_at,
            last_seen=obj.last_seen_at,
            optimized=obj.optimized
        )


class QueryAnalyzeRequest(BaseModel):
    """Analyze query request"""
    connection_id: int
    sql_query: str = Field(..., min_length=1)
    include_execution_plan: bool = True


# Detection Result Schemas
class DetectedIssue(BaseModel):
    """Detected performance issue"""
    issue_type: str
    severity: str
    title: str
    description: str
    affected_objects: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any] = {}
    detected_at: str


class DetectionResult(BaseModel):
    """Comprehensive detection result"""
    issues: List[DetectedIssue]
    recommendations: List[str]
    summary: str
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int


# Optimization Schemas
class OptimizationRequest(BaseModel):
    """Optimization request"""
    query_id: Optional[int] = None
    connection_id: int
    sql_query: str = Field(..., min_length=1)
    include_execution_plan: bool = True


class OptimizationResponse(BaseModel):
    """Optimization response"""
    id: int
    query_id: Optional[int] = None
    connection_id: int
    original_sql: str
    optimized_sql: str
    execution_plan: Optional[Dict[str, Any]] = None
    explanation: str
    recommendations: Optional[str] = None
    estimated_improvement_pct: Optional[float] = None
    status: str
    created_at: datetime
    applied_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    detected_issues: Optional[Dict[str, Any]] = None  # Detection results
    
    class Config:
        from_attributes = True


class OptimizationApplyRequest(BaseModel):
    """Apply optimization request"""
    optimization_id: int
    sql_to_execute: Optional[str] = None  # Specific SQL to run (e.g. CREATE INDEX)
    force: bool = False
    skip_safety_checks: bool = False


class OptimizationApplyResponse(BaseModel):
    """Apply optimization response"""
    success: bool
    message: str
    optimization_id: int
    applied_at: Optional[datetime] = None


class OptimizationValidateRequest(BaseModel):
    """Validate optimization request"""
    optimization_id: int


class OptimizationValidateResponse(BaseModel):
    """Validate optimization response"""
    success: bool
    message: str
    optimization_id: int
    original_time_ms: float
    optimized_time_ms: float
    improvement_pct: float
    validated_at: datetime
    applied_at: Optional[datetime] = None


# Query Issue Schemas
class QueryIssueResponse(BaseModel):
    """Query issue response"""
    id: int
    query_id: Optional[int] = None
    optimization_id: Optional[int] = None
    connection_id: int
    issue_type: str
    severity: str
    title: str
    description: str
    affected_objects: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any] = {}
    detected_at: datetime
    resolved: bool
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Dashboard Schemas
class TopQuery(BaseModel):
    """Top query for dashboard"""
    id: int
    connection_name: str
    sql_text: str
    avg_execution_time: float
    total_execution_time: float
    calls: int
    severity: str  # 'low', 'medium', 'high'


class PerformanceTrend(BaseModel):
    """Performance trend data point"""
    timestamp: str
    avg_time: float
    slow_queries: int
    total_queries: int


class IssueTypeSummary(BaseModel):
    """Summary of issues by type"""
    issue_type: str
    count: int
    critical: int
    high: int
    medium: int
    low: int


class CriticalIssuePreview(BaseModel):
    """Preview of a critical issue for dashboard"""
    optimization_id: int
    connection_name: str
    issue_type: str
    severity: str
    title: str
    description: str
    detected_at: str


class DetectionSummary(BaseModel):
    """Summary of all detected issues across optimizations"""
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    issues_by_type: List[IssueTypeSummary]
    recent_critical_issues: List[CriticalIssuePreview]
    total_optimizations_with_issues: int
    last_updated: datetime


class IssueDetail(BaseModel):
    """Detailed information about a single issue"""
    issue_type: str
    severity: str
    title: str
    description: str
    recommendations: List[str] = []


class QueryWithIssues(BaseModel):
    """Query with its detected issues"""
    optimization_id: int
    connection_id: int
    connection_name: str
    original_sql: str
    optimized_sql: str  # Add optimized SQL
    sql_preview: str  # Truncated version for display
    issue_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    issues: List[IssueDetail]
    detected_at: datetime
    recommendations: Optional[str] = None  # Add recommendations
    estimated_improvement_pct: Optional[float] = None  # Add improvement percentage
    
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_connections: int
    active_connections: int
    total_queries_discovered: int
    total_optimizations: int
    optimizations_applied: int
    avg_improvement_pct: Optional[float] = None
    top_bottlenecks: List[QueryResponse]
    optimizations_with_issues: int = 0
    total_detected_issues: int = 0


class MonitoringStatus(BaseModel):
    """Monitoring agent status"""
    is_running: bool
    last_poll_time: Optional[datetime] = None
    next_poll_time: Optional[datetime] = None
    interval_minutes: int
    queries_discovered: int
    active_connections: int


# Health Check Schema
class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    ollama: Dict[str, Any]
    monitoring_agent: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Error Response Schema
class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Execution Plan Explanation Schemas
class ExplainPlanRequest(BaseModel):
    """Request for execution plan explanation"""
    connection_id: int
    sql_query: str = Field(..., min_length=1)
    execution_plan: Optional[Dict[str, Any]] = None


class ExplainPlanResponse(BaseModel):
    """Natural language explanation of execution plan"""
    success: bool
    explanation: str
    summary: str
    key_operations: List[str] = []
    bottlenecks: List[str] = []
    estimated_cost: Optional[float] = None


# Fix Recommendation Schemas
class FixRecommendation(BaseModel):
    """A single fix recommendation"""
    fix_type: str  # 'index_creation', 'statistics_update', 'query_rewrite', etc.
    sql: str
    description: str
    estimated_impact: str  # 'low', 'medium', 'high'
    affected_objects: List[str] = []
    safety_level: str = "safe"  # 'safe', 'caution', 'dangerous'


class GenerateFixesRequest(BaseModel):
    """Request to generate fix recommendations"""
    optimization_id: int
    include_maintenance: bool = True
    include_indexes: bool = True
    include_rewrites: bool = True
    include_config: bool = False


class GenerateFixesResponse(BaseModel):
    """Categorized fix recommendations"""
    success: bool
    optimization_id: int
    index_recommendations: List[FixRecommendation] = []
    maintenance_tasks: List[FixRecommendation] = []
    query_rewrites: List[FixRecommendation] = []
    configuration_changes: List[FixRecommendation] = []
    total_fixes: int
    high_impact_count: int


# Apply Fix Schemas
class ApplyFixRequest(BaseModel):
    """Request to apply a fix"""
    optimization_id: int
    fix_type: str
    fix_sql: str
    dry_run: bool = True
    skip_safety_checks: bool = False


class SafetyCheckResult(BaseModel):
    """Result of safety checks"""
    passed: bool
    checks_performed: List[str] = []
    warnings: List[str] = []
    errors: List[str] = []


class ApplyFixResponse(BaseModel):
    """Response from applying a fix"""
    success: bool
    fix_id: Optional[int] = None
    fix_type: str
    status: str  # 'pending', 'validating', 'applying', 'applied', 'failed'
    message: str
    execution_time_sec: Optional[float] = None
    rollback_sql: Optional[str] = None
    safety_checks: Optional[SafetyCheckResult] = None
    applied_at: Optional[datetime] = None


# Performance Validation Schemas
class PerformanceMetrics(BaseModel):
    """Performance metrics for a query"""
    execution_time_ms: float
    planning_time_ms: Optional[float] = None
    rows_returned: Optional[int] = None
    buffer_hits: Optional[int] = None
    buffer_reads: Optional[int] = None
    io_cost: Optional[float] = None


class ValidatePerformanceRequest(BaseModel):
    """Request to validate performance improvement"""
    optimization_id: int
    run_original: bool = True
    run_optimized: bool = True
    iterations: int = Field(default=3, ge=1, le=10)


class ValidatePerformanceResponse(BaseModel):
    """Performance validation results"""
    success: bool
    optimization_id: int
    original_metrics: Optional[PerformanceMetrics] = None
    optimized_metrics: Optional[PerformanceMetrics] = None
    improvement_pct: Optional[float] = None
    improvement_ms: Optional[float] = None
    is_faster: bool
    validation_notes: List[str] = []
    validated_at: datetime


# Fix History Schemas
class AppliedFixRecord(BaseModel):
    """Record of an applied fix"""
    id: int
    optimization_id: int
    fix_type: str
    fix_sql: str
    rollback_sql: Optional[str] = None
    status: str
    applied_by: Optional[str] = None
    applied_at: datetime
    execution_time_sec: float
    can_rollback: bool


class FixHistoryResponse(BaseModel):
    """History of applied fixes"""
    total_fixes: int
    applied_fixes: List[AppliedFixRecord]
    rollback_available: bool


class RollbackFixRequest(BaseModel):
    """Request to rollback a fix"""
    fix_id: int
    force: bool = False


class RollbackFixResponse(BaseModel):
    """Response from rolling back a fix"""
    success: bool
    fix_id: int
    message: str
    rollback_sql: Optional[str] = None
    rolled_back_at: Optional[datetime] = None


# Feedback Schemas (Phase 2: ML Enhancement)
class FeedbackCreate(BaseModel):
    """Create feedback request"""
    optimization_id: int
    before_metrics: Dict[str, Any]
    after_metrics: Dict[str, Any]
    dba_rating: Optional[int] = Field(None, ge=1, le=5)
    dba_comments: Optional[str] = None


class FeedbackUpdate(BaseModel):
    """Update feedback request"""
    dba_rating: Optional[int] = Field(None, ge=1, le=5)
    dba_comments: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response"""
    id: int
    optimization_id: int
    connection_id: int
    before_metrics: Dict[str, Any]
    after_metrics: Dict[str, Any]
    actual_improvement_pct: Optional[float] = None
    estimated_improvement_pct: Optional[float] = None
    accuracy_score: Optional[float] = None
    applied_at: datetime
    measured_at: datetime
    feedback_status: str
    dba_rating: Optional[int] = None
    dba_comments: Optional[str] = None
    
    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    """Feedback statistics"""
    total_feedback: int
    avg_accuracy: float
    avg_improvement: float
    success_rate: float
    avg_rating: float
    success_count: int = 0
    partial_count: int = 0
    failed_count: int = 0


class AccuracyMetrics(BaseModel):
    """Model accuracy metrics"""
    current_accuracy: float
    total_optimizations: int
    successful_optimizations: int
    avg_improvement: float
    confidence_score: float


# Pattern Schemas (Phase 2: ML Enhancement)
class PatternResponse(BaseModel):
    """Optimization pattern response"""
    id: int
    pattern_type: str
    pattern_signature: str
    original_pattern: str
    optimized_pattern: str
    success_rate: float
    avg_improvement_pct: float
    times_applied: int
    times_successful: int
    database_type: str
    category: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PatternMatchResult(BaseModel):
    """Pattern matching result"""
    matched: bool
    pattern_id: Optional[int] = None
    pattern_type: Optional[str] = None
    success_rate: Optional[float] = None
    avg_improvement: Optional[float] = None
    confidence: float = 0.0


# Configuration Schemas (Phase 2: ML Enhancement)
class ConfigRecommendation(BaseModel):
    """Database configuration recommendation"""
    parameter_name: str
    current_value: Optional[str] = None
    recommended_value: str
    change_reason: str
    estimated_impact: Dict[str, Any]
    database_type: str
    priority: str  # 'low', 'medium', 'high', 'critical'
    safety_level: str = "safe"  # 'safe', 'caution', 'dangerous'


class ConfigChangeRequest(BaseModel):
    """Request to apply configuration change"""
    connection_id: int
    parameter_name: str
    new_value: str
    change_reason: str
    dry_run: bool = True


class ConfigChangeResponse(BaseModel):
    """Configuration change response"""
    id: int
    connection_id: int
    parameter_name: str
    old_value: Optional[str] = None
    new_value: str
    change_reason: str
    estimated_impact: Optional[Dict[str, Any]] = None
    actual_impact: Optional[Dict[str, Any]] = None
    applied_at: datetime
    reverted_at: Optional[datetime] = None
    status: str
    
    class Config:
        from_attributes = True


class ConfigRevertRequest(BaseModel):
    """Request to revert configuration change"""
    change_id: int
    force: bool = False


class WorkloadAnalysis(BaseModel):
    """Workload analysis result"""
    connection_id: int
    workload_type: str  # 'oltp', 'olap', 'mixed'
    peak_hours: List[int] = []
    avg_query_rate: float
    avg_execution_time: float
    total_queries: int = 0
    slow_queries_count: int = 0
    slow_query_percentage: float
    recommendations: List[ConfigRecommendation] = []
    analysis_period_days: int = 7
    insights: List[str] = []
    analyzed_at: datetime


class WorkloadMetricsResponse(BaseModel):
    """Workload metrics response"""
    id: int
    connection_id: int
    timestamp: datetime
    total_queries: int
    avg_exec_time: float
    cpu_usage: Optional[float] = None
    io_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    active_connections: Optional[int] = None
    slow_queries_count: Optional[int] = None
    workload_type: Optional[str] = None
    
    class Config:
        from_attributes = True


# ML Performance Schemas (Phase 2: ML Enhancement)
class MLAccuracyTrend(BaseModel):
    """ML model accuracy trend data point"""
    date: str
    accuracy: float
    improvement: float
    count: int


class MLRefinementHistory(BaseModel):
    """ML model refinement history record"""
    id: int
    refinement_date: datetime
    patterns_identified: int
    patterns_updated: int
    avg_accuracy_before: float
    avg_accuracy_after: float
    improvement: float
    feedback_analyzed: int


class MLPerformanceMetrics(BaseModel):
    """Comprehensive ML performance metrics"""
    current_accuracy: float
    accuracy_trend: List[MLAccuracyTrend]
    total_patterns: int
    successful_patterns: int
    total_feedback: int
    recent_refinements: List[MLRefinementHistory]
    confidence_score: float


# Index Management Schemas (Phase 4)
class IndexRecommendationBase(BaseModel):
    """Base schema for index recommendations"""
    table_name: str = Field(..., min_length=1)
    columns: List[str] = Field(..., min_items=1)
    index_type: str = Field(default="btree")
    recommendation_type: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    schema_name: Optional[str] = None


class IndexRecommendationCreate(IndexRecommendationBase):
    """Create index recommendation request"""
    connection_id: int = Field(..., gt=0)
    estimated_benefit: Optional[float] = Field(None, ge=0, le=100)
    estimated_cost: Optional[float] = Field(None, ge=0)


class IndexRecommendationResponse(IndexRecommendationBase):
    """Index recommendation response"""
    id: int
    connection_id: int
    index_name: Optional[str] = None
    estimated_benefit: Optional[float] = None
    estimated_cost: Optional[float] = None
    usage_count: int
    last_used_at: Optional[datetime] = None
    status: str
    created_at: datetime
    applied_at: Optional[datetime] = None
    size_bytes: Optional[int] = None
    scans: int
    
    class Config:
        from_attributes = True


class IndexStatistics(BaseModel):
    """Index statistics summary"""
    total_indexes: int
    unused_count: int
    rarely_used_count: int = 0
    total_size_bytes: int
    total_size: str
    indexes: List[Dict[str, Any]] = []
    unused_indexes: List[Dict[str, Any]] = []
    rarely_used_indexes: List[Dict[str, Any]] = []


class IndexCreateRequest(BaseModel):
    """Request to create a new index"""
    connection_id: int = Field(..., gt=0)
    table_name: str = Field(..., min_length=1)
    index_name: str = Field(..., min_length=1)
    columns: List[str] = Field(..., min_items=1)
    index_type: str = Field(default="btree")
    unique: bool = False
    schema_name: Optional[str] = None


class IndexDropRequest(BaseModel):
    """Request to drop an existing index"""
    connection_id: int = Field(..., gt=0)
    table_name: str = Field(..., min_length=1)
    index_name: str = Field(..., min_length=1)
    schema_name: Optional[str] = None


class IndexAnalysisResponse(BaseModel):
    """Index analysis response"""
    connection_id: int
    analysis_type: str
    results: Dict[str, Any]
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class IndexHistoryResponse(BaseModel):
    """Index change history response"""
    connection_id: int
    changes: List[IndexRecommendationResponse]
    total_changes: int


# Pattern Library Schemas (Phase 4: Task 4.3)
class PatternStatistics(BaseModel):
    """Pattern library statistics"""
    total_patterns: int
    by_database: Dict[str, int]
    by_category: Dict[str, int]
    avg_success_rate: float
    total_applications: int
    total_successful: int
    overall_success_rate: float


class PatternCategoryResponse(BaseModel):
    """Pattern category information"""
    name: str
    display_name: str
    count: int
    avg_success_rate: float
    description: str


class PatternSearchRequest(BaseModel):
    """Pattern search request"""
    query: str = Field(..., min_length=1)
    database_type: Optional[str] = None
    category: Optional[str] = None
    min_success_rate: Optional[float] = Field(None, ge=0, le=1)
