"""
SQLAlchemy Database Models for Observability Store
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

from app.config import settings

Base = declarative_base()

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Connection(Base):
    """Database connection configuration"""
    __tablename__ = "connections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    engine = Column(String(50), nullable=False)  # postgresql, mysql, oracle, mssql
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    ssl_enabled = Column(Boolean, default=False)
    monitoring_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_monitored_at = Column(DateTime, nullable=True)


class Query(Base):
    """Discovered queries from monitoring"""
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, nullable=False)
    query_hash = Column(String(64), nullable=False, index=True)
    sql_text = Column(Text, nullable=False)
    avg_exec_time_ms = Column(Float, nullable=False)
    total_exec_time_ms = Column(Float, nullable=False)
    calls = Column(Integer, nullable=False)
    rows_returned = Column(Integer, nullable=True)
    buffer_hits = Column(Integer, nullable=True)
    buffer_reads = Column(Integer, nullable=True)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    optimized = Column(Boolean, default=False)


class Optimization(Base):
    """Optimization results"""
    __tablename__ = "optimizations"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, nullable=True)  # Optional: can optimize without discovered query
    connection_id = Column(Integer, nullable=False)
    original_sql = Column(Text, nullable=False)
    optimized_sql = Column(Text, nullable=False)
    execution_plan = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=False)
    recommendations = Column(Text, nullable=True)
    estimated_improvement_pct = Column(Float, nullable=True)
    status = Column(String(50), default="pending")  # pending, applied, validated, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)
    validated_at = Column(DateTime, nullable=True)
    # Store detected issues as JSON
    detected_issues = Column(JSON, nullable=True)


class QueryIssue(Base):
    """Detected performance issues for queries"""
    __tablename__ = "query_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, nullable=True)  # Optional: link to Query table
    optimization_id = Column(Integer, nullable=True)  # Optional: link to Optimization table
    connection_id = Column(Integer, nullable=False)
    issue_type = Column(String(50), nullable=False, index=True)  # missing_index, poor_join_strategy, etc.
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    affected_objects = Column(JSON, nullable=False)  # List of tables, columns, indexes affected
    recommendations = Column(JSON, nullable=False)  # List of recommendations
    metrics = Column(JSON, nullable=True)  # Additional metrics (rows_scanned, cost, etc.)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)


class OptimizationFeedback(Base):
    """Feedback on applied optimizations for ML model improvement"""
    __tablename__ = "optimization_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    optimization_id = Column(Integer, nullable=False)
    connection_id = Column(Integer, nullable=False)
    before_metrics = Column(JSON, nullable=False)  # exec_time, cpu, io, rows
    after_metrics = Column(JSON, nullable=False)
    actual_improvement_pct = Column(Float, nullable=True)
    estimated_improvement_pct = Column(Float, nullable=True)
    accuracy_score = Column(Float, nullable=True)
    applied_at = Column(DateTime, nullable=False)
    measured_at = Column(DateTime, default=datetime.utcnow)
    feedback_status = Column(String(50), default="success")  # success, failed, partial
    dba_rating = Column(Integer, nullable=True)  # 1-5 stars
    dba_comments = Column(Text, nullable=True)


class OptimizationPattern(Base):
    """Successful optimization patterns for ML learning"""
    __tablename__ = "optimization_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_type = Column(String(50), nullable=False)  # index, rewrite, config
    pattern_signature = Column(String(255), nullable=False)
    original_pattern = Column(Text, nullable=False)
    optimized_pattern = Column(Text, nullable=False)
    success_rate = Column(Float, default=0.0)
    avg_improvement_pct = Column(Float, default=0.0)
    times_applied = Column(Integer, default=0)
    times_successful = Column(Integer, default=0)
    database_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConfigurationChange(Base):
    """Database configuration changes for tracking and validation"""
    __tablename__ = "configuration_changes"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, nullable=False)
    parameter_name = Column(String(255), nullable=False)
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=False)
    change_reason = Column(Text, nullable=False)
    estimated_impact = Column(JSON, nullable=True)
    actual_impact = Column(JSON, nullable=True)
    applied_at = Column(DateTime, default=datetime.utcnow)
    reverted_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="pending")  # pending, applied, validated, reverted


class WorkloadMetrics(Base):
    """Workload metrics for pattern analysis"""
    __tablename__ = "workload_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    total_queries = Column(Integer, nullable=False)
    avg_exec_time = Column(Float, nullable=False)
    cpu_usage = Column(Float, nullable=True)
    io_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    active_connections = Column(Integer, nullable=True)
    slow_queries_count = Column(Integer, nullable=True)
    workload_type = Column(String(50), nullable=True)  # oltp, olap, mixed


class IndexRecommendation(Base):
    """Index recommendations for database optimization"""
    __tablename__ = "index_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, nullable=False)
    table_name = Column(String(255), nullable=False)
    index_name = Column(String(255), nullable=True)
    columns = Column(JSON, nullable=False)  # List of columns
    index_type = Column(String(50), default="btree")  # btree, hash, gin, gist, etc.
    recommendation_type = Column(String(50), nullable=False)  # create, drop, modify
    
    # Metrics
    estimated_benefit = Column(Float, nullable=True)  # Query speedup %
    estimated_cost = Column(Float, nullable=True)  # Storage/maintenance cost
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), default="recommended")  # recommended, created, dropped, rejected
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)
    
    # Additional metadata
    schema_name = Column(String(255), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    scans = Column(Integer, default=0)


def init_db():
    """Initialize database tables"""
    # Create db directory if it doesn't exist
    db_dir = os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", ""))
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
