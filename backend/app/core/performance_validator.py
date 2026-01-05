"""
Performance Validator
Validates performance improvements after applying optimizations
Compares before/after metrics and determines if changes should be kept or rolled back
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import statistics


class PerformanceMetrics:
    """Container for performance metrics"""
    
    def __init__(
        self,
        execution_time_ms: float,
        rows_returned: int,
        buffer_hits: Optional[int] = None,
        buffer_reads: Optional[int] = None,
        cpu_time_ms: Optional[float] = None,
        io_time_ms: Optional[float] = None,
        plan_cost: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ):
        self.execution_time_ms = execution_time_ms
        self.rows_returned = rows_returned
        self.buffer_hits = buffer_hits or 0
        self.buffer_reads = buffer_reads or 0
        self.cpu_time_ms = cpu_time_ms
        self.io_time_ms = io_time_ms
        self.plan_cost = plan_cost
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "execution_time_ms": self.execution_time_ms,
            "rows_returned": self.rows_returned,
            "buffer_hits": self.buffer_hits,
            "buffer_reads": self.buffer_reads,
            "cpu_time_ms": self.cpu_time_ms,
            "io_time_ms": self.io_time_ms,
            "plan_cost": self.plan_cost,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
    
    def get_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        total = self.buffer_hits + self.buffer_reads
        if total > 0:
            return self.buffer_hits / total
        return 0.0


class ValidationResult:
    """Result of performance validation"""
    
    def __init__(
        self,
        improved: bool,
        improvement_pct: float,
        metrics_before: PerformanceMetrics,
        metrics_after: PerformanceMetrics,
        recommendation: str,
        details: Dict[str, Any]
    ):
        self.improved = improved
        self.improvement_pct = improvement_pct
        self.metrics_before = metrics_before
        self.metrics_after = metrics_after
        self.recommendation = recommendation
        self.details = details
        self.validated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "improved": self.improved,
            "improvement_pct": self.improvement_pct,
            "metrics_before": self.metrics_before.to_dict(),
            "metrics_after": self.metrics_after.to_dict(),
            "recommendation": self.recommendation,
            "details": self.details,
            "validated_at": self.validated_at.isoformat()
        }


class PerformanceValidator:
    """Validates performance improvements after optimization"""
    
    def __init__(self, db_manager, config: Optional[Dict[str, Any]] = None):
        """
        Initialize performance validator
        
        Args:
            db_manager: DatabaseManager instance
            config: Validation configuration
        """
        self.db_manager = db_manager
        self.config = config or {}
        self.min_improvement_threshold = self.config.get("min_improvement_pct", 10.0)
        self.max_regression_threshold = self.config.get("max_regression_pct", 5.0)
        self.sample_size = self.config.get("sample_size", 5)
    
    def collect_baseline_metrics(
        self,
        sql_query: str,
        iterations: int = None
    ) -> List[PerformanceMetrics]:
        """
        Collect baseline performance metrics before optimization
        
        Args:
            sql_query: SQL query to measure
            iterations: Number of times to execute (default from config)
        
        Returns:
            List of performance metrics from multiple runs
        """
        iterations = iterations or self.sample_size
        metrics_list = []
        
        logger.info(f"Collecting baseline metrics ({iterations} iterations)")
        
        for i in range(iterations):
            try:
                metrics = self._execute_and_measure(sql_query)
                metrics_list.append(metrics)
                logger.debug(f"Iteration {i+1}: {metrics.execution_time_ms:.2f}ms")
            except Exception as e:
                logger.error(f"Error collecting baseline metric {i+1}: {e}")
        
        return metrics_list
    
    def validate_optimization(
        self,
        original_sql: str,
        optimized_sql: str,
        baseline_metrics: Optional[List[PerformanceMetrics]] = None
    ) -> ValidationResult:
        """
        Validate optimization by comparing performance
        
        Args:
            original_sql: Original SQL query
            optimized_sql: Optimized SQL query
            baseline_metrics: Pre-collected baseline metrics (optional)
        
        Returns:
            ValidationResult with comparison details
        """
        try:
            # Collect baseline if not provided
            if not baseline_metrics:
                logger.info("Collecting baseline metrics...")
                baseline_metrics = self.collect_baseline_metrics(original_sql)
            
            if not baseline_metrics:
                return ValidationResult(
                    improved=False,
                    improvement_pct=0.0,
                    metrics_before=PerformanceMetrics(0, 0),
                    metrics_after=PerformanceMetrics(0, 0),
                    recommendation="Unable to collect baseline metrics",
                    details={"error": "No baseline metrics available"}
                )
            
            # Collect optimized metrics
            logger.info("Collecting optimized metrics...")
            optimized_metrics = self.collect_baseline_metrics(optimized_sql)
            
            if not optimized_metrics:
                return ValidationResult(
                    improved=False,
                    improvement_pct=0.0,
                    metrics_before=self._aggregate_metrics(baseline_metrics),
                    metrics_after=PerformanceMetrics(0, 0),
                    recommendation="Unable to collect optimized metrics",
                    details={"error": "No optimized metrics available"}
                )
            
            # Aggregate metrics
            baseline_avg = self._aggregate_metrics(baseline_metrics)
            optimized_avg = self._aggregate_metrics(optimized_metrics)
            
            # Calculate improvement
            improvement_pct = self._calculate_improvement(
                baseline_avg.execution_time_ms,
                optimized_avg.execution_time_ms
            )
            
            # Determine if improved
            improved = improvement_pct >= self.min_improvement_threshold
            regressed = improvement_pct < -self.max_regression_threshold
            
            # Generate recommendation
            if regressed:
                recommendation = f"ROLLBACK: Performance regressed by {abs(improvement_pct):.1f}%"
            elif improved:
                recommendation = f"KEEP: Performance improved by {improvement_pct:.1f}%"
            else:
                recommendation = f"NEUTRAL: Performance change is {improvement_pct:.1f}% (below threshold)"
            
            # Detailed comparison
            details = {
                "execution_time_improvement_pct": improvement_pct,
                "baseline_avg_ms": baseline_avg.execution_time_ms,
                "optimized_avg_ms": optimized_avg.execution_time_ms,
                "baseline_std_dev": self._calculate_std_dev(
                    [m.execution_time_ms for m in baseline_metrics]
                ),
                "optimized_std_dev": self._calculate_std_dev(
                    [m.execution_time_ms for m in optimized_metrics]
                ),
                "cache_hit_ratio_before": baseline_avg.get_cache_hit_ratio(),
                "cache_hit_ratio_after": optimized_avg.get_cache_hit_ratio(),
                "io_reduction_pct": self._calculate_improvement(
                    baseline_avg.buffer_reads,
                    optimized_avg.buffer_reads
                ) if baseline_avg.buffer_reads > 0 else 0.0,
                "sample_size": len(baseline_metrics),
                "regressed": regressed
            }
            
            logger.info(f"Validation complete: {recommendation}")
            
            return ValidationResult(
                improved=improved and not regressed,
                improvement_pct=improvement_pct,
                metrics_before=baseline_avg,
                metrics_after=optimized_avg,
                recommendation=recommendation,
                details=details
            )
        
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ValidationResult(
                improved=False,
                improvement_pct=0.0,
                metrics_before=PerformanceMetrics(0, 0),
                metrics_after=PerformanceMetrics(0, 0),
                recommendation=f"Validation error: {str(e)}",
                details={"error": str(e)}
            )
    
    def validate_with_workload(
        self,
        original_sql: str,
        optimized_sql: str,
        workload_queries: List[str]
    ) -> Dict[str, Any]:
        """
        Validate optimization impact on entire workload
        
        Args:
            original_sql: Original query
            optimized_sql: Optimized query
            workload_queries: Other queries in the workload
        
        Returns:
            Workload validation results
        """
        results = {
            "target_query": self.validate_optimization(original_sql, optimized_sql),
            "workload_impact": [],
            "overall_improved": False
        }
        
        # Test impact on other queries
        for i, query in enumerate(workload_queries[:10]):  # Limit to 10 queries
            try:
                logger.info(f"Testing workload query {i+1}/{len(workload_queries)}")
                
                # Quick single-run comparison
                before_metrics = self._execute_and_measure(query)
                after_metrics = self._execute_and_measure(query)
                
                improvement = self._calculate_improvement(
                    before_metrics.execution_time_ms,
                    after_metrics.execution_time_ms
                )
                
                results["workload_impact"].append({
                    "query_index": i,
                    "improvement_pct": improvement,
                    "regressed": improvement < -self.max_regression_threshold
                })
            
            except Exception as e:
                logger.error(f"Error testing workload query {i}: {e}")
        
        # Determine overall impact
        target_improved = results["target_query"].improved
        workload_regressions = sum(
            1 for w in results["workload_impact"] if w.get("regressed", False)
        )
        
        results["overall_improved"] = target_improved and workload_regressions == 0
        results["workload_regressions"] = workload_regressions
        
        return results
    
    def _execute_and_measure(self, sql_query: str) -> PerformanceMetrics:
        """Execute query and measure performance"""
        start_time = datetime.utcnow()
        
        try:
            # Get execution plan with timing
            if self.db_manager.engine == "postgresql":
                plan_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql_query}"
                result = self.db_manager.execute_query(plan_query)
                
                if result and len(result) > 0:
                    plan = result[0].get("QUERY PLAN", [{}])[0]
                    
                    execution_time = plan.get("Execution Time", 0.0)
                    planning_time = plan.get("Planning Time", 0.0)
                    total_time = execution_time + planning_time
                    
                    # Extract buffer stats
                    plan_node = plan.get("Plan", {})
                    buffer_hits = plan_node.get("Shared Hit Blocks", 0)
                    buffer_reads = plan_node.get("Shared Read Blocks", 0)
                    
                    return PerformanceMetrics(
                        execution_time_ms=total_time,
                        rows_returned=plan_node.get("Actual Rows", 0),
                        buffer_hits=buffer_hits,
                        buffer_reads=buffer_reads,
                        plan_cost=plan_node.get("Total Cost", 0.0)
                    )
            
            # Fallback: simple execution timing
            result = self.db_manager.execute_query(sql_query)
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return PerformanceMetrics(
                execution_time_ms=execution_time,
                rows_returned=len(result) if result else 0
            )
        
        except Exception as e:
            logger.error(f"Error measuring query performance: {e}")
            raise
    
    def _aggregate_metrics(self, metrics_list: List[PerformanceMetrics]) -> PerformanceMetrics:
        """Aggregate multiple metrics into average"""
        if not metrics_list:
            return PerformanceMetrics(0, 0)
        
        return PerformanceMetrics(
            execution_time_ms=statistics.mean([m.execution_time_ms for m in metrics_list]),
            rows_returned=int(statistics.mean([m.rows_returned for m in metrics_list])),
            buffer_hits=int(statistics.mean([m.buffer_hits for m in metrics_list])),
            buffer_reads=int(statistics.mean([m.buffer_reads for m in metrics_list])),
            cpu_time_ms=statistics.mean([m.cpu_time_ms for m in metrics_list if m.cpu_time_ms]) if any(m.cpu_time_ms for m in metrics_list) else None,
            io_time_ms=statistics.mean([m.io_time_ms for m in metrics_list if m.io_time_ms]) if any(m.io_time_ms for m in metrics_list) else None,
            plan_cost=statistics.mean([m.plan_cost for m in metrics_list if m.plan_cost]) if any(m.plan_cost for m in metrics_list) else None
        )
    
    def _calculate_improvement(self, before: float, after: float) -> float:
        """Calculate percentage improvement"""
        if before == 0:
            return 0.0
        return ((before - after) / before) * 100.0
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        return statistics.stdev(values)
    
    def generate_validation_report(
        self,
        validation_result: ValidationResult
    ) -> str:
        """Generate human-readable validation report"""
        report_lines = [
            "=" * 70,
            "PERFORMANCE VALIDATION REPORT",
            "=" * 70,
            "",
            f"Validation Time: {validation_result.validated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Result: {'✓ IMPROVED' if validation_result.improved else '✗ NOT IMPROVED'}",
            f"Improvement: {validation_result.improvement_pct:.1f}%",
            "",
            "BEFORE OPTIMIZATION:",
            f"  Execution Time: {validation_result.metrics_before.execution_time_ms:.2f}ms",
            f"  Rows Returned: {validation_result.metrics_before.rows_returned:,}",
            f"  Cache Hit Ratio: {validation_result.metrics_before.get_cache_hit_ratio()*100:.1f}%",
            f"  Buffer Reads: {validation_result.metrics_before.buffer_reads:,}",
            "",
            "AFTER OPTIMIZATION:",
            f"  Execution Time: {validation_result.metrics_after.execution_time_ms:.2f}ms",
            f"  Rows Returned: {validation_result.metrics_after.rows_returned:,}",
            f"  Cache Hit Ratio: {validation_result.metrics_after.get_cache_hit_ratio()*100:.1f}%",
            f"  Buffer Reads: {validation_result.metrics_after.buffer_reads:,}",
            "",
            "DETAILED METRICS:",
            f"  Execution Time Improvement: {validation_result.details.get('execution_time_improvement_pct', 0):.1f}%",
            f"  I/O Reduction: {validation_result.details.get('io_reduction_pct', 0):.1f}%",
            f"  Baseline Std Dev: {validation_result.details.get('baseline_std_dev', 0):.2f}ms",
            f"  Optimized Std Dev: {validation_result.details.get('optimized_std_dev', 0):.2f}ms",
            "",
            "RECOMMENDATION:",
            f"  {validation_result.recommendation}",
            "",
            "=" * 70
        ]
        
        return "\n".join(report_lines)
