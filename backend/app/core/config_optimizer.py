"""
Configuration Optimizer Module
Recommends database configuration changes based on workload analysis
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.database import (
    Connection,
    WorkloadMetrics,
    ConfigurationChange,
    Query
)

logger = logging.getLogger(__name__)


class ConfigOptimizer:
    """Optimize database configuration based on workload patterns"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Configuration rules for different database types
        self.config_rules = {
            'postgresql': self._get_postgresql_rules(),
            'mysql': self._get_mysql_rules(),
            'mssql': self._get_mssql_rules()
        }
    
    async def analyze_workload(self, connection_id: int, days: int = 7) -> Dict:
        """
        Analyze workload patterns for a connection
        
        Args:
            connection_id: Connection ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with workload analysis
        """
        try:
            logger.info(f"Analyzing workload for connection {connection_id}")
            
            # Get connection
            connection = self.db.query(Connection).filter(
                Connection.id == connection_id
            ).first()
            
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            # Get workload metrics
            start_date = datetime.utcnow() - timedelta(days=days)
            metrics = self.db.query(WorkloadMetrics).filter(
                WorkloadMetrics.connection_id == connection_id,
                WorkloadMetrics.timestamp >= start_date
            ).all()
            
            if not metrics:
                return {
                    'connection_id': connection_id,
                    'message': 'No workload data available',
                    'recommendations': []
                }
            
            # Calculate workload characteristics
            total_queries = sum(m.total_queries for m in metrics)
            avg_queries_per_hour = total_queries / (days * 24)
            avg_exec_time = sum(m.avg_exec_time for m in metrics) / len(metrics)
            
            # Calculate resource usage
            cpu_usage = [m.cpu_usage for m in metrics if m.cpu_usage is not None]
            io_usage = [m.io_usage for m in metrics if m.io_usage is not None]
            memory_usage = [m.memory_usage for m in metrics if m.memory_usage is not None]
            
            avg_cpu = sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0
            avg_io = sum(io_usage) / len(io_usage) if io_usage else 0
            avg_memory = sum(memory_usage) / len(memory_usage) if memory_usage else 0
            
            # Determine workload type
            workload_type = self._classify_workload(
                avg_queries_per_hour,
                avg_exec_time,
                avg_cpu,
                avg_io
            )
            
            # Identify peak hours
            peak_hours = self._identify_peak_hours(metrics)
            
            # Calculate slow query percentage
            slow_queries = sum(m.slow_queries_count or 0 for m in metrics)
            slow_query_pct = (slow_queries / total_queries * 100) if total_queries > 0 else 0
            
            analysis = {
                'connection_id': connection_id,
                'database_type': connection.engine,
                'analysis_period_days': days,
                'workload_type': workload_type,
                'total_queries': total_queries,
                'avg_queries_per_hour': round(avg_queries_per_hour, 2),
                'avg_execution_time_ms': round(avg_exec_time, 2),
                'avg_cpu_usage_pct': round(avg_cpu, 2),
                'avg_io_usage_pct': round(avg_io, 2),
                'avg_memory_usage_pct': round(avg_memory, 2),
                'slow_query_percentage': round(slow_query_pct, 2),
                'peak_hours': peak_hours,
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Workload analysis complete: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing workload: {str(e)}")
            raise
    
    def _classify_workload(
        self,
        queries_per_hour: float,
        avg_exec_time: float,
        cpu_usage: float,
        io_usage: float
    ) -> str:
        """Classify workload type based on characteristics"""
        
        # OLTP: High query rate, low execution time
        if queries_per_hour > 1000 and avg_exec_time < 100:
            return "oltp"
        
        # OLAP: Low query rate, high execution time
        if queries_per_hour < 100 and avg_exec_time > 1000:
            return "olap"
        
        # Mixed workload
        return "mixed"
    
    def _identify_peak_hours(self, metrics: List[WorkloadMetrics]) -> List[int]:
        """Identify peak hours from metrics"""
        try:
            # Group by hour
            hourly_queries = {}
            for metric in metrics:
                hour = metric.timestamp.hour
                if hour not in hourly_queries:
                    hourly_queries[hour] = []
                hourly_queries[hour].append(metric.total_queries)
            
            # Calculate average for each hour
            hourly_avg = {
                hour: sum(queries) / len(queries)
                for hour, queries in hourly_queries.items()
            }
            
            # Find hours above 80th percentile
            if not hourly_avg:
                return []
            
            values = list(hourly_avg.values())
            threshold = sorted(values)[int(len(values) * 0.8)] if len(values) > 5 else max(values)
            
            peak_hours = [
                hour for hour, avg in hourly_avg.items()
                if avg >= threshold
            ]
            
            return sorted(peak_hours)
            
        except Exception as e:
            logger.error(f"Error identifying peak hours: {str(e)}")
            return []
    
    async def recommend_config_changes(
        self,
        connection_id: int,
        workload_analysis: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Recommend configuration changes based on workload
        
        Args:
            connection_id: Connection ID
            workload_analysis: Optional pre-computed workload analysis
            
        Returns:
            List of configuration recommendations
        """
        try:
            logger.info(f"Generating config recommendations for connection {connection_id}")
            
            # Get connection
            connection = self.db.query(Connection).filter(
                Connection.id == connection_id
            ).first()
            
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            # Get workload analysis if not provided
            if not workload_analysis:
                workload_analysis = await self.analyze_workload(connection_id)
            
            # Get database-specific rules
            db_type = connection.engine.lower()
            if db_type not in self.config_rules:
                logger.warning(f"No config rules for database type: {db_type}")
                return []
            
            rules = self.config_rules[db_type]
            
            # Generate recommendations based on workload
            recommendations = []
            
            for rule in rules:
                recommendation = self._evaluate_rule(rule, workload_analysis)
                if recommendation:
                    recommendations.append(recommendation)
            
            # Sort by priority
            recommendations.sort(
                key=lambda r: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[r['priority']]
            )
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error recommending config changes: {str(e)}")
            raise
    
    def _evaluate_rule(self, rule: Dict, workload: Dict) -> Optional[Dict]:
        """Evaluate a configuration rule against workload"""
        try:
            # Check if rule conditions are met
            conditions = rule.get('conditions', {})
            
            for key, condition in conditions.items():
                workload_value = workload.get(key, 0)
                
                if 'min' in condition and workload_value < condition['min']:
                    continue
                if 'max' in condition and workload_value > condition['max']:
                    continue
                if 'equals' in condition and workload_value != condition['equals']:
                    continue
            
            # All conditions met, return recommendation
            return {
                'parameter_name': rule['parameter'],
                'current_value': rule.get('default_value'),
                'recommended_value': rule['recommended_value'],
                'change_reason': rule['reason'],
                'estimated_impact': rule['estimated_impact'],
                'database_type': workload['database_type'],
                'priority': rule['priority'],
                'safety_level': rule.get('safety_level', 'safe')
            }
            
        except Exception as e:
            logger.error(f"Error evaluating rule: {str(e)}")
            return None
    
    def estimate_impact(
        self,
        parameter: str,
        old_value: str,
        new_value: str,
        database_type: str
    ) -> Dict:
        """
        Estimate impact of a configuration change
        
        Args:
            parameter: Parameter name
            old_value: Current value
            new_value: New value
            database_type: Database type
            
        Returns:
            Dictionary with impact estimation
        """
        try:
            # Get rules for this database type
            rules = self.config_rules.get(database_type.lower(), [])
            
            # Find rule for this parameter
            rule = next((r for r in rules if r['parameter'] == parameter), None)
            
            if not rule:
                return {
                    'performance_impact': 'unknown',
                    'resource_impact': 'unknown',
                    'risk_level': 'medium'
                }
            
            return rule.get('estimated_impact', {
                'performance_impact': 'moderate',
                'resource_impact': 'moderate',
                'risk_level': 'medium'
            })
            
        except Exception as e:
            logger.error(f"Error estimating impact: {str(e)}")
            return {
                'performance_impact': 'unknown',
                'resource_impact': 'unknown',
                'risk_level': 'high'
            }
    
    def _get_postgresql_rules(self) -> List[Dict]:
        """Get PostgreSQL configuration rules"""
        return [
            {
                'parameter': 'shared_buffers',
                'default_value': '128MB',
                'recommended_value': '25% of RAM',
                'reason': 'Increase shared buffers for better caching',
                'conditions': {
                    'avg_memory_usage_pct': {'max': 60}
                },
                'estimated_impact': {
                    'performance_impact': 'high',
                    'resource_impact': 'high',
                    'risk_level': 'low'
                },
                'priority': 'high',
                'safety_level': 'safe'
            },
            {
                'parameter': 'effective_cache_size',
                'default_value': '4GB',
                'recommended_value': '50% of RAM',
                'reason': 'Help query planner make better decisions',
                'conditions': {},
                'estimated_impact': {
                    'performance_impact': 'moderate',
                    'resource_impact': 'none',
                    'risk_level': 'low'
                },
                'priority': 'medium',
                'safety_level': 'safe'
            },
            {
                'parameter': 'work_mem',
                'default_value': '4MB',
                'recommended_value': '16MB',
                'reason': 'Increase work memory for complex queries',
                'conditions': {
                    'workload_type': {'equals': 'olap'}
                },
                'estimated_impact': {
                    'performance_impact': 'high',
                    'resource_impact': 'moderate',
                    'risk_level': 'medium'
                },
                'priority': 'high',
                'safety_level': 'caution'
            },
            {
                'parameter': 'maintenance_work_mem',
                'default_value': '64MB',
                'recommended_value': '256MB',
                'reason': 'Speed up maintenance operations',
                'conditions': {},
                'estimated_impact': {
                    'performance_impact': 'moderate',
                    'resource_impact': 'low',
                    'risk_level': 'low'
                },
                'priority': 'medium',
                'safety_level': 'safe'
            },
            {
                'parameter': 'max_connections',
                'default_value': '100',
                'recommended_value': '200',
                'reason': 'Increase connection limit for high concurrency',
                'conditions': {
                    'avg_queries_per_hour': {'min': 1000}
                },
                'estimated_impact': {
                    'performance_impact': 'moderate',
                    'resource_impact': 'moderate',
                    'risk_level': 'medium'
                },
                'priority': 'high',
                'safety_level': 'caution'
            },
            {
                'parameter': 'random_page_cost',
                'default_value': '4.0',
                'recommended_value': '1.1',
                'reason': 'Optimize for SSD storage',
                'conditions': {
                    'avg_io_usage_pct': {'max': 50}
                },
                'estimated_impact': {
                    'performance_impact': 'moderate',
                    'resource_impact': 'none',
                    'risk_level': 'low'
                },
                'priority': 'medium',
                'safety_level': 'safe'
            }
        ]
    
    def _get_mysql_rules(self) -> List[Dict]:
        """Get MySQL configuration rules"""
        return [
            {
                'parameter': 'innodb_buffer_pool_size',
                'default_value': '128MB',
                'recommended_value': '70% of RAM',
                'reason': 'Increase InnoDB buffer pool for better caching',
                'conditions': {
                    'avg_memory_usage_pct': {'max': 60}
                },
                'estimated_impact': {
                    'performance_impact': 'high',
                    'resource_impact': 'high',
                    'risk_level': 'low'
                },
                'priority': 'high',
                'safety_level': 'safe'
            },
            {
                'parameter': 'innodb_log_file_size',
                'default_value': '48MB',
                'recommended_value': '256MB',
                'reason': 'Reduce checkpoint frequency',
                'conditions': {
                    'workload_type': {'equals': 'oltp'}
                },
                'estimated_impact': {
                    'performance_impact': 'moderate',
                    'resource_impact': 'low',
                    'risk_level': 'medium'
                },
                'priority': 'medium',
                'safety_level': 'caution'
            },
            {
                'parameter': 'max_connections',
                'default_value': '151',
                'recommended_value': '300',
                'reason': 'Increase connection limit for high concurrency',
                'conditions': {
                    'avg_queries_per_hour': {'min': 1000}
                },
                'estimated_impact': {
                    'performance_impact': 'moderate',
                    'resource_impact': 'moderate',
                    'risk_level': 'medium'
                },
                'priority': 'high',
                'safety_level': 'caution'
            },
            {
                'parameter': 'query_cache_size',
                'default_value': '1MB',
                'recommended_value': '64MB',
                'reason': 'Enable query caching for repeated queries',
                'conditions': {
                    'workload_type': {'equals': 'oltp'}
                },
                'estimated_impact': {
                    'performance_impact': 'moderate',
                    'resource_impact': 'low',
                    'risk_level': 'low'
                },
                'priority': 'medium',
                'safety_level': 'safe'
            }
        ]
    
    def _get_mssql_rules(self) -> List[Dict]:
        """Get MSSQL configuration rules"""
        return [
            {
                'parameter': 'max server memory',
                'default_value': '2147483647',
                'recommended_value': '80% of RAM',
                'reason': 'Limit SQL Server memory usage',
                'conditions': {
                    'avg_memory_usage_pct': {'min': 80}
                },
                'estimated_impact': {
                    'performance_impact': 'high',
                    'resource_impact': 'high',
                    'risk_level': 'low'
                },
                'priority': 'high',
                'safety_level': 'safe'
            },
            {
                'parameter': 'max degree of parallelism',
                'default_value': '0',
                'recommended_value': '4',
                'reason': 'Optimize parallel query execution',
                'conditions': {
                    'workload_type': {'equals': 'olap'}
                },
                'estimated_impact': {
                    'performance_impact': 'high',
                    'resource_impact': 'moderate',
                    'risk_level': 'medium'
                },
                'priority': 'high',
                'safety_level': 'caution'
            },
            {
                'parameter': 'cost threshold for parallelism',
                'default_value': '5',
                'recommended_value': '50',
                'reason': 'Reduce unnecessary parallelism',
                'conditions': {
                    'workload_type': {'equals': 'oltp'}
                },
                'estimated_impact': {
                    'performance_impact': 'moderate',
                    'resource_impact': 'low',
                    'risk_level': 'low'
                },
                'priority': 'medium',
                'safety_level': 'safe'
            }
        ]
    
    def get_database_specific_rules(self, db_type: str) -> Dict:
        """
        Get configuration rules for a specific database type
        
        Args:
            db_type: Database type (postgresql, mysql, mssql)
            
        Returns:
            Dictionary with configuration rules
        """
        try:
            rules = self.config_rules.get(db_type.lower(), [])
            
            return {
                'database_type': db_type,
                'total_rules': len(rules),
                'rules': rules
            }
            
        except Exception as e:
            logger.error(f"Error getting database rules: {str(e)}")
            return {
                'database_type': db_type,
                'total_rules': 0,
                'rules': []
            }
