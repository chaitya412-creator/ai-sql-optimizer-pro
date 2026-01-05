"""
Execution Plan Analyzer
Parses and extracts insights from database execution plans
Detects 9 types of SQL optimization issues
"""
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from enum import Enum
import re
from datetime import datetime, timedelta


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
    CONFIG_TUNING = "config_tuning"


class IssueSeverity(str, Enum):
    """Severity levels for detected issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionResult:
    """Represents a detected optimization issue"""
    
    def __init__(
        self,
        issue_type: IssueType,
        severity: IssueSeverity,
        title: str,
        description: str,
        affected_objects: List[str],
        recommendations: List[str],
        metrics: Optional[Dict[str, Any]] = None
    ):
        self.issue_type = issue_type
        self.severity = severity
        self.title = title
        self.description = description
        self.affected_objects = affected_objects
        self.recommendations = recommendations
        self.metrics = metrics or {}
        self.detected_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "affected_objects": self.affected_objects,
            "recommendations": self.recommendations,
            "metrics": self.metrics,
            "detected_at": self.detected_at.isoformat()
        }


class QueryPatternDetector:
    """Detects suboptimal query patterns"""
    
    @staticmethod
    def detect_patterns(sql_query: str) -> List[DetectionResult]:
        """Detect anti-patterns in SQL query"""
        issues = []
        
        if not sql_query or not sql_query.strip():
            return issues
        
        sql_upper = sql_query.upper()
        sql_clean = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
        sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
        
        # 1. SELECT * usage
        if re.search(r'\bSELECT\s+\*\s+FROM\b', sql_upper):
            issues.append(DetectionResult(
                issue_type=IssueType.SUBOPTIMAL_PATTERN,
                severity=IssueSeverity.MEDIUM,
                title="SELECT * detected",
                description="Query selects all columns instead of specific ones",
                affected_objects=["query_pattern"],
                recommendations=[
                    "Specify only required columns explicitly",
                    "Reduces network traffic and memory usage",
                    "Improves query cache efficiency"
                ],
                metrics={}
            ))
        
        # 2. DISTINCT abuse
        distinct_count = len(re.findall(r'\bDISTINCT\b', sql_upper))
        if distinct_count > 1:
            issues.append(DetectionResult(
                issue_type=IssueType.SUBOPTIMAL_PATTERN,
                severity=IssueSeverity.MEDIUM,
                title="Multiple DISTINCT clauses",
                description=f"Query uses DISTINCT {distinct_count} times",
                affected_objects=["query_pattern"],
                recommendations=[
                    "Review if DISTINCT is necessary",
                    "Consider using GROUP BY instead",
                    "Check for duplicate data issues in source tables"
                ],
                metrics={"distinct_count": distinct_count}
            ))
        
        # 3. OR conditions that could be IN
        or_count = len(re.findall(r'\bOR\b', sql_upper))
        if or_count > 3:
            issues.append(DetectionResult(
                issue_type=IssueType.SUBOPTIMAL_PATTERN,
                severity=IssueSeverity.LOW,
                title="Multiple OR conditions",
                description=f"Query has {or_count} OR conditions",
                affected_objects=["query_pattern"],
                recommendations=[
                    "Consider using IN clause instead of multiple ORs",
                    "Example: WHERE col IN (val1, val2, val3)",
                    "Better for index usage and readability"
                ],
                metrics={"or_count": or_count}
            ))
        
        # 4. Subquery in SELECT clause
        if re.search(r'SELECT.*\(SELECT\b', sql_upper, re.DOTALL):
            issues.append(DetectionResult(
                issue_type=IssueType.SUBOPTIMAL_PATTERN,
                severity=IssueSeverity.HIGH,
                title="Subquery in SELECT clause",
                description="Correlated subquery in SELECT may execute for each row",
                affected_objects=["query_pattern"],
                recommendations=[
                    "Convert to JOIN when possible",
                    "Use window functions if appropriate",
                    "Consider CTEs for better readability"
                ],
                metrics={}
            ))
        
        # 5. NOT IN with subquery
        if re.search(r'\bNOT\s+IN\s*\(SELECT\b', sql_upper):
            issues.append(DetectionResult(
                issue_type=IssueType.SUBOPTIMAL_PATTERN,
                severity=IssueSeverity.HIGH,
                title="NOT IN with subquery",
                description="NOT IN can be slow and may not handle NULLs correctly",
                affected_objects=["query_pattern"],
                recommendations=[
                    "Use NOT EXISTS instead",
                    "Or use LEFT JOIN with IS NULL check",
                    "Better NULL handling and performance"
                ],
                metrics={}
            ))
        
        # 6. LIKE with leading wildcard
        if re.search(r"LIKE\s+['\"]%", sql_upper):
            issues.append(DetectionResult(
                issue_type=IssueType.SUBOPTIMAL_PATTERN,
                severity=IssueSeverity.MEDIUM,
                title="LIKE with leading wildcard",
                description="LIKE '%pattern' prevents index usage",
                affected_objects=["query_pattern"],
                recommendations=[
                    "Avoid leading wildcards when possible",
                    "Consider full-text search for text searching",
                    "Use trigram indexes (PostgreSQL) for pattern matching"
                ],
                metrics={}
            ))
        
        # 7. Functions on indexed columns in WHERE
        if re.search(r'WHERE.*\b(UPPER|LOWER|SUBSTRING|DATE|YEAR|MONTH)\s*\([a-zA-Z_]', sql_upper):
            issues.append(DetectionResult(
                issue_type=IssueType.SUBOPTIMAL_PATTERN,
                severity=IssueSeverity.HIGH,
                title="Function on indexed column in WHERE",
                description="Functions on columns prevent index usage",
                affected_objects=["query_pattern"],
                recommendations=[
                    "Move functions to the comparison value",
                    "Create functional/expression indexes",
                    "Store computed values in separate columns"
                ],
                metrics={}
            ))
        
        return issues


class IndexDetector:
    """Detects missing and inefficient indexes"""
    
    @staticmethod
    def detect_issues(plan: Dict[str, Any], engine: str, sql_query: str) -> List[DetectionResult]:
        """Detect index-related issues from execution plan"""
        issues = []
        
        if not plan:
            return issues
        
        try:
            if engine == "postgresql":
                issues.extend(IndexDetector._analyze_postgresql(plan, sql_query))
            elif engine == "mysql":
                issues.extend(IndexDetector._analyze_mysql(plan, sql_query))
            elif engine == "mssql":
                issues.extend(IndexDetector._analyze_mssql(plan, sql_query))
        except Exception as e:
            logger.error(f"Error detecting index issues: {e}")
        
        return issues
    
    @staticmethod
    def _analyze_postgresql(plan: Dict[str, Any], sql_query: str) -> List[DetectionResult]:
        """Analyze PostgreSQL execution plan for index issues"""
        issues = []
        
        def traverse_plan(node):
            if not isinstance(node, dict):
                return
            
            node_type = node.get("Node Type", "")
            
            # Sequential scans on large tables
            if node_type == "Seq Scan":
                relation = node.get("Relation Name", "unknown")
                rows = node.get("Plan Rows", 0)
                cost = node.get("Total Cost", 0)
                filter_cond = node.get("Filter", "")
                
                if rows > 1000:
                    issues.append(DetectionResult(
                        issue_type=IssueType.MISSING_INDEX,
                        severity=IssueSeverity.HIGH if rows > 10000 else IssueSeverity.MEDIUM,
                        title=f"Missing index on table '{relation}'",
                        description=f"Sequential scan on {rows:,} rows (cost: {cost:.2f})",
                        affected_objects=[relation],
                        recommendations=[
                            f"Add index on table '{relation}'",
                            f"Filter: {filter_cond}" if filter_cond else "Review WHERE clause",
                            f"CREATE INDEX idx_{relation}_col ON {relation}(column_name);"
                        ],
                        metrics={"estimated_rows": rows, "total_cost": cost}
                    ))
            
            # Bitmap heap scans (inefficient index)
            elif node_type == "Bitmap Heap Scan":
                relation = node.get("Relation Name", "unknown")
                rows = node.get("Plan Rows", 0)
                
                if rows > 5000:
                    issues.append(DetectionResult(
                        issue_type=IssueType.INEFFICIENT_INDEX,
                        severity=IssueSeverity.MEDIUM,
                        title=f"Inefficient index on '{relation}'",
                        description=f"Bitmap scan on {rows:,} rows - low selectivity",
                        affected_objects=[relation],
                        recommendations=[
                            "Add more selective index",
                            "Review index column order",
                            "Consider partial indexes"
                        ],
                        metrics={"estimated_rows": rows}
                    ))
            
            if "Plans" in node:
                for child in node["Plans"]:
                    traverse_plan(child)
        
        if isinstance(plan, list) and plan:
            traverse_plan(plan[0].get("Plan", {}))
        elif isinstance(plan, dict):
            traverse_plan(plan.get("Plan", {}))
        
        return issues
    
    @staticmethod
    def _analyze_mysql(plan: Dict[str, Any], sql_query: str) -> List[DetectionResult]:
        """Analyze MySQL execution plan"""
        issues = []
        
        def traverse(node):
            if not isinstance(node, dict):
                return
            
            if "table" in node:
                table_info = node["table"]
                access_type = table_info.get("access_type", "")
                table_name = table_info.get("table_name", "unknown")
                rows = table_info.get("rows_examined_per_scan", 0)
                
                if access_type == "ALL" and rows > 1000:
                    issues.append(DetectionResult(
                        issue_type=IssueType.MISSING_INDEX,
                        severity=IssueSeverity.HIGH if rows > 10000 else IssueSeverity.MEDIUM,
                        title=f"Full table scan on '{table_name}'",
                        description=f"Scanning {rows:,} rows without index",
                        affected_objects=[table_name],
                        recommendations=[
                            f"CREATE INDEX idx_{table_name}_col ON {table_name}(column_name);",
                            "Review WHERE clause columns"
                        ],
                        metrics={"rows_examined": rows}
                    ))
            
            for value in node.values():
                if isinstance(value, (dict, list)):
                    if isinstance(value, dict):
                        traverse(value)
                    else:
                        for item in value:
                            if isinstance(item, dict):
                                traverse(item)
        
        traverse(plan)
        return issues
    
    @staticmethod
    def _analyze_mssql(plan: Dict[str, Any], sql_query: str) -> List[DetectionResult]:
        """Analyze MSSQL execution plan"""
        issues = []
        plan_str = str(plan)
        
        if "Table Scan" in plan_str or "Clustered Index Scan" in plan_str:
            tables = PlanAnalyzer.extract_table_names(sql_query)
            for table in tables:
                issues.append(DetectionResult(
                    issue_type=IssueType.MISSING_INDEX,
                    severity=IssueSeverity.MEDIUM,
                    title=f"Potential missing index on '{table}'",
                    description="Table/index scan detected",
                    affected_objects=[table],
                    recommendations=[
                        f"Review indexes on '{table}'",
                        "Check MSSQL missing index DMVs"
                    ],
                    metrics={}
                ))
        
        return issues


class JoinStrategyDetector:
    """Detects poor join strategies"""
    
    @staticmethod
    def detect_issues(plan: Dict[str, Any], engine: str) -> List[DetectionResult]:
        """Detect inefficient join strategies"""
        issues = []
        
        if not plan:
            return issues
        
        try:
            if engine == "postgresql":
                issues.extend(JoinStrategyDetector._analyze_postgresql(plan))
            elif engine == "mysql":
                issues.extend(JoinStrategyDetector._analyze_mysql(plan))
        except Exception as e:
            logger.error(f"Error detecting join issues: {e}")
        
        return issues
    
    @staticmethod
    def _analyze_postgresql(plan: Dict[str, Any]) -> List[DetectionResult]:
        """Analyze PostgreSQL joins"""
        issues = []
        
        def traverse(node):
            if not isinstance(node, dict):
                return
            
            node_type = node.get("Node Type", "")
            rows = node.get("Plan Rows", 0)
            cost = node.get("Total Cost", 0)
            
            if node_type == "Nested Loop" and rows > 10000:
                issues.append(DetectionResult(
                    issue_type=IssueType.POOR_JOIN_STRATEGY,
                    severity=IssueSeverity.HIGH if rows > 100000 else IssueSeverity.MEDIUM,
                    title="Inefficient nested loop join",
                    description=f"Processing {rows:,} rows (cost: {cost:.2f})",
                    affected_objects=["join_operation"],
                    recommendations=[
                        "Consider Hash Join for large datasets",
                        "Add indexes on join columns",
                        "Increase work_mem for hash joins"
                    ],
                    metrics={"estimated_rows": rows, "total_cost": cost}
                ))
            
            elif node_type == "Hash Join" and rows > 1000000:
                issues.append(DetectionResult(
                    issue_type=IssueType.POOR_JOIN_STRATEGY,
                    severity=IssueSeverity.MEDIUM,
                    title="Large hash join operation",
                    description=f"Processing {rows:,} rows - high memory usage",
                    affected_objects=["join_operation"],
                    recommendations=[
                        "Monitor work_mem usage",
                        "Consider table partitioning",
                        "Add WHERE filters before join"
                    ],
                    metrics={"estimated_rows": rows}
                ))
            
            if "Plans" in node:
                for child in node["Plans"]:
                    traverse(child)
        
        if isinstance(plan, list) and plan:
            traverse(plan[0].get("Plan", {}))
        elif isinstance(plan, dict):
            traverse(plan.get("Plan", {}))
        
        return issues
    
    @staticmethod
    def _analyze_mysql(plan: Dict[str, Any]) -> List[DetectionResult]:
        """Analyze MySQL joins"""
        issues = []
        
        def traverse(node):
            if not isinstance(node, dict):
                return
            
            if "nested_loop" in node:
                nested_loops = node["nested_loop"]
                if isinstance(nested_loops, list):
                    total_rows = sum(
                        t.get("table", {}).get("rows_examined_per_scan", 0)
                        for t in nested_loops if isinstance(t, dict)
                    )
                    
                    if total_rows > 10000:
                        issues.append(DetectionResult(
                            issue_type=IssueType.POOR_JOIN_STRATEGY,
                            severity=IssueSeverity.HIGH if total_rows > 100000 else IssueSeverity.MEDIUM,
                            title="Inefficient nested loop join",
                            description=f"Examining {total_rows:,} total rows",
                            affected_objects=["join_operation"],
                            recommendations=[
                                "Add indexes on join columns",
                                "Ensure statistics are current"
                            ],
                            metrics={"total_rows_examined": total_rows}
                        ))
            
            for value in node.values():
                if isinstance(value, dict):
                    traverse(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            traverse(item)
        
        traverse(plan)
        return issues


class ORMDetector:
    """Detects ORM-generated SQL issues"""
    
    @staticmethod
    def detect_issues(sql_query: str, query_context: Optional[Dict[str, Any]] = None) -> List[DetectionResult]:
        """Detect ORM anti-patterns"""
        issues = []
        
        if not sql_query:
            return issues
        
        sql_upper = sql_query.upper()
        
        try:
            # N+1 query pattern
            if query_context and query_context.get("similar_query_count", 0) > 20:
                issues.append(DetectionResult(
                    issue_type=IssueType.ORM_GENERATED,
                    severity=IssueSeverity.CRITICAL,
                    title="N+1 query problem detected",
                    description=f"Similar query executed {query_context['similar_query_count']} times",
                    affected_objects=["orm_pattern"],
                    recommendations=[
                        "Use eager loading / JOIN FETCH",
                        "Use select_related() or prefetch_related()",
                        "Batch queries together"
                    ],
                    metrics={"similar_query_count": query_context["similar_query_count"]}
                ))
            
            # Excessive JOINs
            join_count = len(re.findall(r'\bJOIN\b', sql_upper))
            if join_count > 5:
                issues.append(DetectionResult(
                    issue_type=IssueType.ORM_GENERATED,
                    severity=IssueSeverity.HIGH if join_count > 8 else IssueSeverity.MEDIUM,
                    title=f"Excessive JOINs ({join_count} tables)",
                    description="Too many tables joined - typical ORM eager loading",
                    affected_objects=["orm_pattern"],
                    recommendations=[
                        "Review if all JOINs are necessary",
                        "Split into multiple queries",
                        "Use lazy loading for rarely accessed data"
                    ],
                    metrics={"join_count": join_count}
                ))
            
            # SELECT * with JOINs
            if re.search(r'\bSELECT\s+\*\s+FROM\b', sql_upper) and join_count > 2:
                issues.append(DetectionResult(
                    issue_type=IssueType.ORM_GENERATED,
                    severity=IssueSeverity.MEDIUM,
                    title="SELECT * with multiple JOINs",
                    description="ORM selecting all columns from joined tables",
                    affected_objects=["orm_pattern"],
                    recommendations=[
                        "Specify only needed columns",
                        "Use .only() or .defer() in ORM",
                        "Reduce data transfer overhead"
                    ],
                    metrics={"join_count": join_count}
                ))
        
        except Exception as e:
            logger.error(f"Error detecting ORM patterns: {e}")
        
        return issues


class IOWorkloadDetector:
    """Detects high I/O workload issues"""
    
    @staticmethod
    def detect_issues(query_stats: Optional[Dict[str, Any]] = None) -> List[DetectionResult]:
        """Detect high I/O patterns"""
        issues = []
        
        if not query_stats:
            return issues
        
        try:
            buffer_hits = query_stats.get("buffer_hits", 0)
            buffer_reads = query_stats.get("buffer_reads", 0)
            
            if buffer_reads > 0:
                total = buffer_hits + buffer_reads
                hit_ratio = buffer_hits / total if total > 0 else 0
                
                # Low cache hit ratio
                if hit_ratio < 0.9 and buffer_reads > 1000:
                    issues.append(DetectionResult(
                        issue_type=IssueType.HIGH_IO_WORKLOAD,
                        severity=IssueSeverity.HIGH if hit_ratio < 0.7 else IssueSeverity.MEDIUM,
                        title="High disk I/O workload",
                        description=f"Cache hit ratio: {hit_ratio*100:.1f}% ({buffer_reads:,} disk reads)",
                        affected_objects=["io_performance"],
                        recommendations=[
                            "Add indexes to reduce disk reads",
                            "Increase buffer pool/cache size",
                            "Use covering indexes"
                        ],
                        metrics={
                            "buffer_hits": buffer_hits,
                            "buffer_reads": buffer_reads,
                            "cache_hit_ratio": hit_ratio
                        }
                    ))
                
                # Excessive buffer usage
                if total > 100000:
                    issues.append(DetectionResult(
                        issue_type=IssueType.HIGH_IO_WORKLOAD,
                        severity=IssueSeverity.MEDIUM,
                        title="Excessive buffer usage",
                        description=f"Accessing {total:,} total buffers",
                        affected_objects=["io_performance"],
                        recommendations=[
                            "Add WHERE filters to reduce data access",
                            "Consider materialized views",
                            "Optimize index selectivity"
                        ],
                        metrics={"total_buffers": total}
                    ))
        
        except Exception as e:
            logger.error(f"Error detecting I/O issues: {e}")
        
        return issues


class ReportingQueryDetector:
    """Detects inefficient reporting queries"""
    
    @staticmethod
    def detect_issues(sql_query: str) -> List[DetectionResult]:
        """Detect inefficient reporting patterns"""
        issues = []
        
        if not sql_query:
            return issues
        
        sql_upper = sql_query.upper()
        
        try:
            # Missing pagination
            has_agg = bool(re.search(r'\b(COUNT|SUM|AVG|MAX|MIN|GROUP BY)\b', sql_upper))
            has_limit = bool(re.search(r'\bLIMIT\b', sql_upper))
            has_top = bool(re.search(r'\bTOP\b', sql_upper))
            
            if has_agg and not has_limit and not has_top:
                issues.append(DetectionResult(
                    issue_type=IssueType.INEFFICIENT_REPORTING,
                    severity=IssueSeverity.MEDIUM,
                    title="Missing pagination in aggregation",
                    description="Aggregation without LIMIT may return excessive results",
                    affected_objects=["reporting_query"],
                    recommendations=[
                        "Add LIMIT clause",
                        "Implement pagination",
                        "Add ORDER BY with LIMIT"
                    ],
                    metrics={}
                ))
            
            # Multiple window functions
            window_funcs = re.findall(
                r'\b(ROW_NUMBER|RANK|DENSE_RANK|LAG|LEAD|FIRST_VALUE|LAST_VALUE)\s*\(',
                sql_upper
            )
            if len(window_funcs) > 2:
                issues.append(DetectionResult(
                    issue_type=IssueType.INEFFICIENT_REPORTING,
                    severity=IssueSeverity.MEDIUM,
                    title=f"Multiple window functions ({len(window_funcs)})",
                    description="Complex window functions are resource-intensive",
                    affected_objects=["reporting_query"],
                    recommendations=[
                        "Consider materializing intermediate results",
                        "Split into multiple queries if possible",
                        "Ensure proper indexing on PARTITION BY columns"
                    ],
                    metrics={"window_function_count": len(window_funcs)}
                ))
            
            # Multiple aggregations
            agg_funcs = re.findall(r'\b(COUNT|SUM|AVG|MAX|MIN|STDDEV|VARIANCE)\s*\(', sql_upper)
            if len(agg_funcs) > 5:
                issues.append(DetectionResult(
                    issue_type=IssueType.INEFFICIENT_REPORTING,
                    severity=IssueSeverity.LOW,
                    title=f"Multiple aggregations ({len(agg_funcs)})",
                    description="Many aggregation functions in single query",
                    affected_objects=["reporting_query"],
                    recommendations=[
                        "Consider pre-aggregating data",
                        "Use summary tables for common reports",
                        "Cache results if data doesn't change frequently"
                    ],
                    metrics={"aggregation_count": len(agg_funcs)}
                ))
        
        except Exception as e:
            logger.error(f"Error detecting reporting issues: {e}")
        
        return issues


class CardinalityDetector:
    """Detects large cardinality estimation errors using EXPLAIN ANALYZE data"""

    @staticmethod
    def detect_issues(plan: Dict[str, Any], engine: str, sql_query: str = "", high_threshold: float = 0.5, medium_threshold: float = 0.2) -> List[DetectionResult]:
        issues = []
        try:
            normalized = None
            try:
                from app.core.plan_normalizer import PlanNormalizer
                normalized = PlanNormalizer.normalize(plan, engine)
            except Exception as e:
                logger.error(f"CardinalityDetector: failed to normalize plan: {e}")
                normalized = None

            def traverse(node: 'NormalizedPlanNode'):
                if not node:
                    return

                err = node.get_cardinality_error()
                if err is not None:
                    # Severity based on error magnitude
                    severity = IssueSeverity.MEDIUM
                    if err >= high_threshold:
                        severity = IssueSeverity.HIGH
                    elif err >= medium_threshold:
                        severity = IssueSeverity.MEDIUM
                    else:
                        severity = IssueSeverity.LOW

                    if err >= medium_threshold:
                        title = f"Cardinality estimation mismatch at '{node.relation_name or node.operation}'"
                        description = (
                            f"Estimated rows: {node.estimated_rows:,}, Actual rows: {node.actual_rows:,} (error: {err*100:.1f}%)"
                        )
                        recs = [
                            "Run ANALYZE on the table(s)",
                            "Investigate statistics (histogram, extended statistics)",
                            "Check for data skew or recent bulk imports"
                        ]
                        affected = [node.relation_name] if node.relation_name else ["query"]

                        issues.append(DetectionResult(
                            issue_type=IssueType.WRONG_CARDINALITY,
                            severity=severity,
                            title=title,
                            description=description,
                            affected_objects=affected,
                            recommendations=recs,
                            metrics={"cardinality_error_ratio": err}
                        ))

                for child in getattr(node, 'children', []) or []:
                    traverse(child)

            if normalized:
                traverse(normalized)

        except Exception as e:
            logger.error(f"CardinalityDetector error: {e}")
        return issues


class StatisticsDetector:
    """Detects stale statistics and suggests ANALYZE tasks"""

    @staticmethod
    def detect_issues(table_stats: Dict[str, Any], plan: Dict[str, Any], engine: str = "") -> List[DetectionResult]:
        issues = []
        try:
            import datetime
            now = datetime.datetime.utcnow()
            for table, stats in (table_stats or {}).items():
                last_analyze = stats.get('last_analyze')
                if last_analyze:
                    # If last_analyze is a string, try ISO parsing; otherwise expect a datetime
                    if isinstance(last_analyze, str):
                        try:
                            last_analyze_dt = datetime.datetime.fromisoformat(last_analyze)
                        except Exception:
                            last_analyze_dt = None
                    else:
                        last_analyze_dt = last_analyze

                    if last_analyze_dt:
                        age_days = (now - last_analyze_dt).days
                        if age_days > 30:
                            issues.append(DetectionResult(
                                issue_type=IssueType.STALE_STATISTICS,
                                severity=IssueSeverity.MEDIUM,
                                title=f"Stale statistics for table '{table}'",
                                description=f"Last ANALYZE was {age_days} days ago",
                                affected_objects=[table],
                                recommendations=[f"Run ANALYZE {table};", "Schedule regular statistics collection"],
                                metrics={"days_since_analyze": age_days}
                            ))
                else:
                    # No analyze information at all
                    issues.append(DetectionResult(
                        issue_type=IssueType.STALE_STATISTICS,
                        severity=IssueSeverity.MEDIUM,
                        title=f"Statistics missing for table '{table}'",
                        description="No ANALYZE timestamp available; statistics may be outdated",
                        affected_objects=[table],
                        recommendations=[f"Run ANALYZE {table};"],
                        metrics={}
                    ))

            # Additionally, check for high seq_scan counts as heuristic for missing indexes/stale stats
            for table, stats in (table_stats or {}).items():
                seq = stats.get('seq_scan', 0) or 0
                idx = stats.get('idx_scan', 0) or 0
                if seq > 1000 and (idx / (seq + 1)) < 0.1:
                    issues.append(DetectionResult(
                        issue_type=IssueType.STALE_STATISTICS,
                        severity=IssueSeverity.MEDIUM,
                        title=f"High sequential scan count on '{table}'",
                        description=f"Seq scans: {seq}, index scans: {idx}",
                        affected_objects=[table],
                        recommendations=[f"Run ANALYZE {table};", "Review indexing strategy"],
                        metrics={"seq_scan": seq, "idx_scan": idx}
                    ))

        except Exception as e:
            logger.error(f"StatisticsDetector error: {e}")
        return issues


class ConfigTuningDetector:
    """Detects database configuration tuning opportunities"""
    
    @staticmethod
    def detect_issues(plan: Optional[Dict[str, Any]], engine: str, query_stats: Optional[Dict[str, Any]] = None) -> List[DetectionResult]:
        issues = []
        
        try:
            if engine == "postgresql":
                issues.extend(ConfigTuningDetector._analyze_postgresql(plan, query_stats))
            elif engine == "mysql":
                issues.extend(ConfigTuningDetector._analyze_mysql(plan, query_stats))
            elif engine == "mssql":
                issues.extend(ConfigTuningDetector._analyze_mssql(plan, query_stats))
        except Exception as e:
            logger.error(f"ConfigTuningDetector error: {e}")
            
        return issues

    @staticmethod
    def _analyze_postgresql(plan: Optional[Dict[str, Any]], query_stats: Optional[Dict[str, Any]]) -> List[DetectionResult]:
        issues = []
        if plan:
            # Check for Hash Joins that might benefit from more work_mem
            def count_hash_joins(node):
                count = 0
                if not isinstance(node, dict): return 0
                if node.get("Node Type") == "Hash Join":
                    count += 1
                if "Plans" in node:
                    for child in node["Plans"]:
                        count += count_hash_joins(child)
                return count
            
            hash_joins = 0
            if isinstance(plan, list) and plan:
                hash_joins = count_hash_joins(plan[0].get("Plan", {}))
            elif isinstance(plan, dict):
                hash_joins = count_hash_joins(plan.get("Plan", {}))
            
            if hash_joins > 2:
                issues.append(DetectionResult(
                    issue_type=IssueType.CONFIG_TUNING,
                    severity=IssueSeverity.LOW,
                    title="PostgreSQL work_mem tuning opportunity",
                    description=f"Query uses {hash_joins} hash joins. Increasing work_mem may improve performance.",
                    affected_objects=["postgresql_config"],
                    recommendations=[
                        "Increase work_mem (e.g., SET work_mem = '64MB';)",
                        "Monitor hash join batches in EXPLAIN ANALYZE",
                        "Consider increasing shared_buffers if I/O is high"
                    ],
                    metrics={"hash_join_count": hash_joins}
                ))
        
        # Check for high I/O as indicator for shared_buffers
        if query_stats:
            reads = query_stats.get("buffer_reads", 0) or 0
            if reads > 10000:
                issues.append(DetectionResult(
                    issue_type=IssueType.CONFIG_TUNING,
                    severity=IssueSeverity.LOW,
                    title="PostgreSQL shared_buffers tuning opportunity",
                    description=f"High disk reads ({reads:,} blocks). Increasing shared_buffers may help.",
                    affected_objects=["postgresql_config"],
                    recommendations=[
                        "Increase shared_buffers (typically 25% of RAM)",
                        "Check effective_cache_size",
                        "Review random_page_cost if using SSDs"
                    ],
                    metrics={"buffer_reads": reads}
                ))
        return issues

    @staticmethod
    def _analyze_mysql(plan: Optional[Dict[str, Any]], query_stats: Optional[Dict[str, Any]]) -> List[DetectionResult]:
        issues = []
        if not plan: return issues
        
        # MySQL JSON plan analysis
        def check_temp_tables(node):
            found = False
            if not isinstance(node, dict): return False
            if node.get("using_temporary_table") or node.get("using_filesort"):
                return True
            for key, value in node.items():
                if isinstance(value, dict):
                    if check_temp_tables(value): return True
                elif isinstance(value, list):
                    for item in value:
                        if check_temp_tables(item): return True
            return False

        if check_temp_tables(plan):
            issues.append(DetectionResult(
                issue_type=IssueType.CONFIG_TUNING,
                severity=IssueSeverity.LOW,
                title="MySQL temporary table tuning",
                description="Query is using temporary tables or filesort. Consider increasing tmp_table_size or max_heap_table_size.",
                affected_objects=["mysql_config"],
                recommendations=[
                    "Increase tmp_table_size and max_heap_table_size",
                    "Increase sort_buffer_size for filesorts",
                    "Optimize query to avoid temporary tables (e.g., better indexes)"
                ],
                metrics={}
            ))
        return issues

    @staticmethod
    def _analyze_mssql(plan: Optional[Dict[str, Any]], query_stats: Optional[Dict[str, Any]]) -> List[DetectionResult]:
        issues = []
        # MS SQL plan analysis (simplified for now as it's XML-based)
        if query_stats and query_stats.get("avg_time_ms", 0) > 5000:
            issues.append(DetectionResult(
                issue_type=IssueType.CONFIG_TUNING,
                severity=IssueSeverity.LOW,
                title="MS SQL Server parallelism tuning",
                description="Long running query detected. Review 'max degree of parallelism' and 'cost threshold for parallelism'.",
                affected_objects=["mssql_config"],
                recommendations=[
                    "Check 'max degree of parallelism' (MAXDOP) setting",
                    "Review 'cost threshold for parallelism'",
                    "Monitor for CXPACKET waits"
                ],
                metrics={}
            ))
        return issues


class RecommendationRanker:
    """Ranks recommendations based on projected savings"""
    
    @staticmethod
    def rank_issues(issues: List[DetectionResult]) -> List[DetectionResult]:
        """Rank issues by severity and estimated impact"""
        def score_issue(issue):
            severity_scores = {
                IssueSeverity.CRITICAL: 10000,
                IssueSeverity.HIGH: 5000,
                IssueSeverity.MEDIUM: 1000,
                IssueSeverity.LOW: 100
            }
            score = severity_scores.get(issue.severity, 0)
            
            # Add weight based on metrics
            if issue.issue_type == IssueType.MISSING_INDEX:
                score += issue.metrics.get("estimated_rows", 0) / 10
            elif issue.issue_type == IssueType.WRONG_CARDINALITY:
                score += issue.metrics.get("cardinality_error_ratio", 0) * 1000
            elif issue.issue_type == IssueType.HIGH_IO_WORKLOAD:
                score += issue.metrics.get("buffer_reads", 0) / 5
            elif issue.issue_type == IssueType.FULL_TABLE_SCAN:
                score += issue.metrics.get("rows_examined", 0) / 10
                
            return score
            
        return sorted(issues, key=score_issue, reverse=True)


class PlanAnalyzer:
    """Analyzes execution plans to identify performance issues"""
    
    @staticmethod
    def extract_table_names(sql_query: str) -> List[str]:
        """Extract table names from SQL query"""
        if not sql_query:
            return []
            
        sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
        sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)
        
        pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, sql_query, re.IGNORECASE)
        
        return list(set(matches))
    
    @staticmethod
    def analyze_plan(
        plan: Optional[Dict[str, Any]],
        engine: str,
        sql_query: str = "",
        query_stats: Optional[Dict[str, Any]] = None,
        table_stats: Optional[Dict[str, Any]] = None,
        query_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive execution plan analysis
        Detects all 9 types of optimization issues
        """
        all_issues = []
        
        try:
            # 1. Query Pattern Detection (always runs)
            if sql_query:
                all_issues.extend(QueryPatternDetector.detect_patterns(sql_query))
            
            # 2-4. Plan-based detection (requires execution plan)
            if plan:
                all_issues.extend(IndexDetector.detect_issues(plan, engine, sql_query))
                all_issues.extend(JoinStrategyDetector.detect_issues(plan, engine))
                # Note: TableScanDetector is covered by IndexDetector
            
            # 5. ORM Detection
            if sql_query:
                all_issues.extend(ORMDetector.detect_issues(sql_query, query_context))
            
            # 6. I/O Workload Detection
            if query_stats:
                all_issues.extend(IOWorkloadDetector.detect_issues(query_stats))
            
            # 7. Reporting Query Detection
            if sql_query:
                all_issues.extend(ReportingQueryDetector.detect_issues(sql_query))
            
            # 8. Cardinality detection (requires EXPLAIN ANALYZE with actual rows)
            try:
                if plan:
                    all_issues.extend(CardinalityDetector.detect_issues(plan, engine, sql_query))
            except Exception as e:
                logger.error(f"Error running CardinalityDetector: {e}")

            # 9. Statistics detection (uses table_stats from DB if provided)
            try:
                if table_stats:
                    all_issues.extend(StatisticsDetector.detect_issues(table_stats, plan, engine))
            except Exception as e:
                logger.error(f"Error running StatisticsDetector: {e}")

            # 10. Configuration Tuning Detection
            try:
                all_issues.extend(ConfigTuningDetector.detect_issues(plan, engine, query_stats))
            except Exception as e:
                logger.error(f"Error running ConfigTuningDetector: {e}")

            # Rank issues by impact
            all_issues = RecommendationRanker.rank_issues(all_issues)

            # Add note if no execution plan
            if not plan:
                all_issues.append(DetectionResult(
                    issue_type=IssueType.SUBOPTIMAL_PATTERN,
                    severity=IssueSeverity.LOW,
                    title="Execution plan not available",
                    description="Enable execution plan analysis for detailed insights on indexes, joins, and I/O patterns",
                    affected_objects=["analysis"],
                    recommendations=[
                        "Check 'Include execution plan analysis' option",
                        "Ensure database user has plan viewing permissions",
                        "PostgreSQL: GRANT SELECT ON pg_stat_statements TO user",
                        "MySQL: GRANT SELECT ON performance_schema.* TO user"
                    ],
                    metrics={}
                ))
            
        except Exception as e:
            logger.error(f"Error during plan analysis: {e}")
            all_issues.append(DetectionResult(
                issue_type=IssueType.SUBOPTIMAL_PATTERN,
                severity=IssueSeverity.LOW,
                title="Analysis error",
                description=f"Error during analysis: {str(e)}",
                affected_objects=["analyzer"],
                recommendations=["Review query and execution plan manually"],
                metrics={}
            ))
        
        # Convert to dict format
        issues_dict = [issue.to_dict() for issue in all_issues]
        
        # Generate summary
        summary = PlanAnalyzer._generate_summary(all_issues)
        
        # Collect recommendations
        all_recommendations = []
        for issue in all_issues:
            all_recommendations.extend(issue.recommendations)
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        
        return {
            "issues": issues_dict,
            "recommendations": unique_recommendations,
            "summary": summary,
            "total_issues": len(issues_dict),
            "critical_issues": sum(1 for i in all_issues if i.severity == IssueSeverity.CRITICAL),
            "high_issues": sum(1 for i in all_issues if i.severity == IssueSeverity.HIGH),
            "medium_issues": sum(1 for i in all_issues if i.severity == IssueSeverity.MEDIUM),
            "low_issues": sum(1 for i in all_issues if i.severity == IssueSeverity.LOW)
        }
    
    @staticmethod
    def _generate_summary(issues: List[DetectionResult]) -> str:
        """Generate human-readable summary"""
        if not issues:
            return "No performance issues detected. Query appears to be well-optimized."
        
        summary_parts = []
        
        # Count by severity
        critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        high = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)
        medium = sum(1 for i in issues if i.severity == IssueSeverity.MEDIUM)
        low = sum(1 for i in issues if i.severity == IssueSeverity.LOW)
        
        summary_parts.append(f"Detected {len(issues)} performance issue(s):")
        
        if critical > 0:
            summary_parts.append(f"- {critical} CRITICAL issue(s) requiring immediate attention")
        if high > 0:
            summary_parts.append(f"- {high} HIGH priority issue(s)")
        if medium > 0:
            summary_parts.append(f"- {medium} MEDIUM priority issue(s)")
        if low > 0:
            summary_parts.append(f"- {low} LOW priority issue(s)")
        
        # Count by type
        issue_types = {}
        for issue in issues:
            issue_type = issue.issue_type.value
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        summary_parts.append("\nIssue breakdown:")
        for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
            summary_parts.append(f"- {issue_type.replace('_', ' ').title()}: {count}")
        
        return "\n".join(summary_parts)
    
    @staticmethod
    def analyze_postgresql_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility
        Use analyze_plan() for comprehensive analysis
        """
        issues = []
        recommendations = []
        
        def traverse_plan(node, depth=0):
            if not isinstance(node, dict):
                return
            
            node_type = node.get("Node Type", "")
            
            # Check for sequential scans
            if node_type == "Seq Scan":
                relation = node.get("Relation Name", "unknown")
                rows = node.get("Plan Rows", 0)
                if rows > 1000:
                    issues.append(f"Sequential scan on large table '{relation}' ({rows} rows)")
                    recommendations.append(f"Consider adding index on '{relation}'")
            
            # Check for nested loops on large datasets
            if node_type == "Nested Loop":
                rows = node.get("Plan Rows", 0)
                if rows > 10000:
                    issues.append(f"Nested loop join with high cardinality ({rows} rows)")
                    recommendations.append("Consider using Hash Join or Merge Join instead")
            
            # Check for high cost operations
            total_cost = node.get("Total Cost", 0)
            if total_cost > 10000:
                issues.append(f"High cost operation: {node_type} (cost: {total_cost})")
            
            # Traverse child nodes
            if "Plans" in node:
                for child in node["Plans"]:
                    traverse_plan(child, depth + 1)
        
        # Start traversal
        if isinstance(plan, list) and len(plan) > 0:
            traverse_plan(plan[0].get("Plan", {}))
        elif isinstance(plan, dict):
            traverse_plan(plan.get("Plan", {}))
        
        return {
            "issues": issues,
            "recommendations": recommendations
        }
    
    @staticmethod
    def analyze_mysql_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility
        Use analyze_plan() for comprehensive analysis
        """
        issues = []
        recommendations = []
        
        query_block = plan.get("query_block", {})
        
        if "table" in query_block:
            table_info = query_block["table"]
            access_type = table_info.get("access_type", "")
            
            if access_type == "ALL":
                table_name = table_info.get("table_name", "unknown")
                issues.append(f"Full table scan on '{table_name}'")
                recommendations.append(f"Add index to '{table_name}'")
        
        return {
            "issues": issues,
            "recommendations": recommendations
        }
