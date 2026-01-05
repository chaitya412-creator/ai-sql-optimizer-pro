"""
Performance Tracker Module
Tracks before/after metrics for optimizations and calculates actual improvements
"""
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.models.database import OptimizationFeedback, Optimization, Connection
from app.core.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """Track performance metrics before and after optimization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.db_manager = DatabaseManager()
    
    async def track_before_metrics(
        self,
        connection_id: int,
        query_sql: str,
        execution_count: int = 3
    ) -> Dict:
        """
        Track performance metrics before optimization is applied
        
        Args:
            connection_id: Database connection ID
            query_sql: SQL query to measure
            execution_count: Number of times to execute for average
            
        Returns:
            Dictionary with before metrics
        """
        try:
            logger.info(f"Tracking before metrics for connection {connection_id}")
            
            # Get connection details
            connection = self.db.query(Connection).filter(
                Connection.id == connection_id
            ).first()
            
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            # Execute query multiple times and collect metrics
            metrics_list = []
            
            for i in range(execution_count):
                try:
                    metrics = await self._execute_and_measure(
                        connection,
                        query_sql
                    )
                    metrics_list.append(metrics)
                except Exception as e:
                    logger.warning(f"Execution {i+1} failed: {str(e)}")
                    continue
            
            if not metrics_list:
                raise Exception("All execution attempts failed")
            
            # Calculate averages
            avg_metrics = self._calculate_average_metrics(metrics_list)
            
            logger.info(f"Before metrics tracked: {avg_metrics}")
            return avg_metrics
            
        except Exception as e:
            logger.error(f"Error tracking before metrics: {str(e)}")
            raise
    
    async def track_after_metrics(
        self,
        connection_id: int,
        query_sql: str,
        execution_count: int = 3
    ) -> Dict:
        """
        Track performance metrics after optimization is applied
        
        Args:
            connection_id: Database connection ID
            query_sql: Optimized SQL query to measure
            execution_count: Number of times to execute for average
            
        Returns:
            Dictionary with after metrics
        """
        try:
            logger.info(f"Tracking after metrics for connection {connection_id}")
            
            # Same process as before metrics
            connection = self.db.query(Connection).filter(
                Connection.id == connection_id
            ).first()
            
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            metrics_list = []
            
            for i in range(execution_count):
                try:
                    metrics = await self._execute_and_measure(
                        connection,
                        query_sql
                    )
                    metrics_list.append(metrics)
                except Exception as e:
                    logger.warning(f"Execution {i+1} failed: {str(e)}")
                    continue
            
            if not metrics_list:
                raise Exception("All execution attempts failed")
            
            avg_metrics = self._calculate_average_metrics(metrics_list)
            
            logger.info(f"After metrics tracked: {avg_metrics}")
            return avg_metrics
            
        except Exception as e:
            logger.error(f"Error tracking after metrics: {str(e)}")
            raise
    
    async def _execute_and_measure(
        self,
        connection: Connection,
        query_sql: str
    ) -> Dict:
        """
        Execute query and measure performance metrics
        
        Args:
            connection: Database connection object
            query_sql: SQL query to execute
            
        Returns:
            Dictionary with execution metrics
        """
        try:
            # Connect to target database
            conn = await self.db_manager.get_connection(connection.id)
            
            # Start timing
            start_time = datetime.utcnow()
            
            # Execute query with EXPLAIN ANALYZE for detailed metrics
            if connection.engine == 'postgresql':
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query_sql}"
            elif connection.engine == 'mysql':
                explain_query = f"EXPLAIN ANALYZE {query_sql}"
            elif connection.engine == 'mssql':
                explain_query = f"SET STATISTICS TIME ON; SET STATISTICS IO ON; {query_sql}"
            else:
                # Fallback: just execute the query
                explain_query = query_sql
            
            result = conn.execute(text(explain_query))
            rows = result.fetchall()
            
            # End timing
            end_time = datetime.utcnow()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Extract metrics based on database type
            metrics = {
                'exec_time_ms': execution_time_ms,
                'rows_returned': len(rows) if rows else 0,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Parse database-specific metrics
            if connection.engine == 'postgresql':
                metrics.update(self._parse_postgres_metrics(rows))
            elif connection.engine == 'mysql':
                metrics.update(self._parse_mysql_metrics(rows))
            elif connection.engine == 'mssql':
                metrics.update(self._parse_mssql_metrics(rows))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error executing and measuring query: {str(e)}")
            raise
    
    def _parse_postgres_metrics(self, explain_result: List) -> Dict:
        """Parse PostgreSQL EXPLAIN ANALYZE output"""
        try:
            if not explain_result or not explain_result[0]:
                return {}
            
            plan = explain_result[0][0]
            if isinstance(plan, str):
                import json
                plan = json.loads(plan)
            
            execution_time = plan[0].get('Execution Time', 0)
            planning_time = plan[0].get('Planning Time', 0)
            
            plan_node = plan[0].get('Plan', {})
            
            return {
                'execution_time_ms': execution_time,
                'planning_time_ms': planning_time,
                'total_cost': plan_node.get('Total Cost', 0),
                'rows_scanned': plan_node.get('Actual Rows', 0),
                'shared_hit_blocks': plan_node.get('Shared Hit Blocks', 0),
                'shared_read_blocks': plan_node.get('Shared Read Blocks', 0),
            }
        except Exception as e:
            logger.warning(f"Error parsing PostgreSQL metrics: {str(e)}")
            return {}
    
    def _parse_mysql_metrics(self, explain_result: List) -> Dict:
        """Parse MySQL EXPLAIN ANALYZE output"""
        try:
            # MySQL EXPLAIN ANALYZE returns different format
            return {
                'rows_examined': 0,  # Parse from result
                'rows_sent': 0,
            }
        except Exception as e:
            logger.warning(f"Error parsing MySQL metrics: {str(e)}")
            return {}
    
    def _parse_mssql_metrics(self, explain_result: List) -> Dict:
        """Parse MSSQL statistics output"""
        try:
            return {
                'cpu_time_ms': 0,  # Parse from result
                'elapsed_time_ms': 0,
                'logical_reads': 0,
                'physical_reads': 0,
            }
        except Exception as e:
            logger.warning(f"Error parsing MSSQL metrics: {str(e)}")
            return {}
    
    def _calculate_average_metrics(self, metrics_list: List[Dict]) -> Dict:
        """Calculate average metrics from multiple executions"""
        if not metrics_list:
            return {}
        
        # Initialize sums
        avg_metrics = {}
        numeric_keys = [
            'exec_time_ms', 'execution_time_ms', 'planning_time_ms',
            'total_cost', 'rows_scanned', 'rows_returned',
            'shared_hit_blocks', 'shared_read_blocks',
            'cpu_time_ms', 'elapsed_time_ms', 'logical_reads', 'physical_reads'
        ]
        
        # Sum all numeric values
        for key in numeric_keys:
            values = [m.get(key, 0) for m in metrics_list if key in m]
            if values:
                avg_metrics[key] = sum(values) / len(values)
        
        # Add non-numeric fields from first execution
        avg_metrics['timestamp'] = metrics_list[0].get('timestamp')
        avg_metrics['execution_count'] = len(metrics_list)
        
        return avg_metrics
    
    def calculate_improvement(
        self,
        before_metrics: Dict,
        after_metrics: Dict
    ) -> float:
        """
        Calculate improvement percentage
        
        Args:
            before_metrics: Metrics before optimization
            after_metrics: Metrics after optimization
            
        Returns:
            Improvement percentage (positive = better, negative = worse)
        """
        try:
            # Use execution time as primary metric
            before_time = before_metrics.get('exec_time_ms') or before_metrics.get('execution_time_ms', 0)
            after_time = after_metrics.get('exec_time_ms') or after_metrics.get('execution_time_ms', 0)
            
            if before_time == 0:
                return 0.0
            
            improvement_pct = ((before_time - after_time) / before_time) * 100
            
            logger.info(f"Calculated improvement: {improvement_pct:.2f}%")
            return round(improvement_pct, 2)
            
        except Exception as e:
            logger.error(f"Error calculating improvement: {str(e)}")
            return 0.0
    
    def compare_estimated_vs_actual(
        self,
        estimated_improvement: float,
        actual_improvement: float
    ) -> Dict:
        """
        Compare estimated vs actual improvement
        
        Args:
            estimated_improvement: Estimated improvement percentage
            actual_improvement: Actual improvement percentage
            
        Returns:
            Dictionary with comparison metrics
        """
        try:
            # Calculate accuracy
            if estimated_improvement == 0:
                accuracy = 0.0
            else:
                error = abs(estimated_improvement - actual_improvement)
                accuracy = max(0, 100 - (error / abs(estimated_improvement) * 100))
            
            # Determine status
            if actual_improvement >= estimated_improvement * 0.8:
                status = "success"
            elif actual_improvement >= 0:
                status = "partial"
            else:
                status = "failed"
            
            comparison = {
                'estimated_improvement_pct': estimated_improvement,
                'actual_improvement_pct': actual_improvement,
                'accuracy_score': round(accuracy, 2),
                'difference': round(actual_improvement - estimated_improvement, 2),
                'status': status
            }
            
            logger.info(f"Comparison: {comparison}")
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing improvements: {str(e)}")
            return {
                'estimated_improvement_pct': estimated_improvement,
                'actual_improvement_pct': actual_improvement,
                'accuracy_score': 0.0,
                'difference': 0.0,
                'status': 'error'
            }
    
    async def store_feedback(
        self,
        optimization_id: int,
        before_metrics: Dict,
        after_metrics: Dict,
        dba_rating: Optional[int] = None,
        dba_comments: Optional[str] = None
    ) -> OptimizationFeedback:
        """
        Store feedback in database
        
        Args:
            optimization_id: Optimization ID
            before_metrics: Metrics before optimization
            after_metrics: Metrics after optimization
            dba_rating: DBA rating (1-5)
            dba_comments: DBA comments
            
        Returns:
            Created OptimizationFeedback object
        """
        try:
            # Get optimization
            optimization = self.db.query(Optimization).filter(
                Optimization.id == optimization_id
            ).first()
            
            if not optimization:
                raise ValueError(f"Optimization {optimization_id} not found")
            
            # Calculate improvements
            actual_improvement = self.calculate_improvement(before_metrics, after_metrics)
            estimated_improvement = optimization.estimated_improvement_pct or 0.0
            
            comparison = self.compare_estimated_vs_actual(
                estimated_improvement,
                actual_improvement
            )
            
            # Create feedback record
            feedback = OptimizationFeedback(
                optimization_id=optimization_id,
                connection_id=optimization.connection_id,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                actual_improvement_pct=actual_improvement,
                estimated_improvement_pct=estimated_improvement,
                accuracy_score=comparison['accuracy_score'],
                applied_at=optimization.applied_at or datetime.utcnow(),
                measured_at=datetime.utcnow(),
                feedback_status=comparison['status'],
                dba_rating=dba_rating,
                dba_comments=dba_comments
            )
            
            self.db.add(feedback)
            self.db.commit()
            self.db.refresh(feedback)
            
            logger.info(f"Feedback stored for optimization {optimization_id}")
            return feedback
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing feedback: {str(e)}")
            raise
    
    def get_accuracy_score(self, optimization_id: int) -> float:
        """
        Get accuracy score for an optimization
        
        Args:
            optimization_id: Optimization ID
            
        Returns:
            Accuracy score (0-100)
        """
        try:
            feedback = self.db.query(OptimizationFeedback).filter(
                OptimizationFeedback.optimization_id == optimization_id
            ).first()
            
            if not feedback:
                return 0.0
            
            return feedback.accuracy_score or 0.0
            
        except Exception as e:
            logger.error(f"Error getting accuracy score: {str(e)}")
            return 0.0
    
    def get_feedback_stats(self, connection_id: Optional[int] = None) -> Dict:
        """
        Get feedback statistics
        
        Args:
            connection_id: Optional connection ID to filter by
            
        Returns:
            Dictionary with feedback statistics
        """
        try:
            query = self.db.query(OptimizationFeedback)
            
            if connection_id:
                query = query.filter(OptimizationFeedback.connection_id == connection_id)
            
            feedbacks = query.all()
            
            if not feedbacks:
                return {
                    'total_feedback': 0,
                    'avg_accuracy': 0.0,
                    'avg_improvement': 0.0,
                    'success_rate': 0.0,
                    'avg_rating': 0.0
                }
            
            total = len(feedbacks)
            avg_accuracy = sum(f.accuracy_score or 0 for f in feedbacks) / total
            avg_improvement = sum(f.actual_improvement_pct or 0 for f in feedbacks) / total
            success_count = sum(1 for f in feedbacks if f.feedback_status == 'success')
            success_rate = (success_count / total) * 100
            
            ratings = [f.dba_rating for f in feedbacks if f.dba_rating]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
            
            stats = {
                'total_feedback': total,
                'avg_accuracy': round(avg_accuracy, 2),
                'avg_improvement': round(avg_improvement, 2),
                'success_rate': round(success_rate, 2),
                'avg_rating': round(avg_rating, 2),
                'success_count': success_count,
                'partial_count': sum(1 for f in feedbacks if f.feedback_status == 'partial'),
                'failed_count': sum(1 for f in feedbacks if f.feedback_status == 'failed')
            }
            
            logger.info(f"Feedback stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting feedback stats: {str(e)}")
            return {
                'total_feedback': 0,
                'avg_accuracy': 0.0,
                'avg_improvement': 0.0,
                'success_rate': 0.0,
                'avg_rating': 0.0
            }
