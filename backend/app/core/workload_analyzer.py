"""
Workload Analyzer Module
Analyzes database workload patterns and characteristics
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models.database import (
    Connection,
    Query,
    WorkloadMetrics
)

logger = logging.getLogger(__name__)


class WorkloadAnalyzer:
    """Analyze database workload patterns"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def analyze_workload_pattern(
        self,
        connection_id: int,
        days: int = 7
    ) -> Dict:
        """
        Analyze workload patterns for a connection
        
        Args:
            connection_id: Connection ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with workload pattern analysis
        """
        try:
            logger.info(f"Analyzing workload pattern for connection {connection_id}")
            
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
            ).order_by(WorkloadMetrics.timestamp).all()
            
            if not metrics:
                return {
                    'connection_id': connection_id,
                    'message': 'No workload data available',
                    'pattern': 'unknown'
                }
            
            # Analyze patterns
            hourly_pattern = self._analyze_hourly_pattern(metrics)
            daily_pattern = self._analyze_daily_pattern(metrics)
            query_pattern = await self._analyze_query_pattern(connection_id, days)
            resource_pattern = self._analyze_resource_pattern(metrics)
            
            # Classify workload type
            workload_type = self._classify_workload_type(metrics, query_pattern)
            
            # Identify trends
            trends = self._identify_trends(metrics)
            
            # Generate insights
            insights = self._generate_insights(
                hourly_pattern,
                daily_pattern,
                query_pattern,
                resource_pattern,
                workload_type
            )
            
            pattern = {
                'connection_id': connection_id,
                'database_type': connection.engine,
                'analysis_period_days': days,
                'workload_type': workload_type,
                'hourly_pattern': hourly_pattern,
                'daily_pattern': daily_pattern,
                'query_pattern': query_pattern,
                'resource_pattern': resource_pattern,
                'trends': trends,
                'insights': insights,
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Workload pattern analysis complete")
            return pattern
            
        except Exception as e:
            logger.error(f"Error analyzing workload pattern: {str(e)}")
            raise
    
    def _analyze_hourly_pattern(self, metrics: List[WorkloadMetrics]) -> Dict:
        """Analyze hourly workload patterns"""
        try:
            # Group by hour
            hourly_data = {}
            for metric in metrics:
                hour = metric.timestamp.hour
                if hour not in hourly_data:
                    hourly_data[hour] = {
                        'queries': [],
                        'exec_times': [],
                        'cpu': [],
                        'io': []
                    }
                
                hourly_data[hour]['queries'].append(metric.total_queries)
                hourly_data[hour]['exec_times'].append(metric.avg_exec_time)
                if metric.cpu_usage:
                    hourly_data[hour]['cpu'].append(metric.cpu_usage)
                if metric.io_usage:
                    hourly_data[hour]['io'].append(metric.io_usage)
            
            # Calculate averages for each hour
            hourly_avg = {}
            for hour, data in hourly_data.items():
                hourly_avg[hour] = {
                    'avg_queries': sum(data['queries']) / len(data['queries']),
                    'avg_exec_time': sum(data['exec_times']) / len(data['exec_times']),
                    'avg_cpu': sum(data['cpu']) / len(data['cpu']) if data['cpu'] else 0,
                    'avg_io': sum(data['io']) / len(data['io']) if data['io'] else 0
                }
            
            # Identify peak hours
            if hourly_avg:
                query_values = [h['avg_queries'] for h in hourly_avg.values()]
                threshold = sorted(query_values)[int(len(query_values) * 0.8)] if len(query_values) > 5 else max(query_values)
                peak_hours = [h for h, data in hourly_avg.items() if data['avg_queries'] >= threshold]
            else:
                peak_hours = []
            
            return {
                'hourly_averages': hourly_avg,
                'peak_hours': sorted(peak_hours),
                'off_peak_hours': [h for h in range(24) if h not in peak_hours]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing hourly pattern: {str(e)}")
            return {'hourly_averages': {}, 'peak_hours': [], 'off_peak_hours': []}
    
    def _analyze_daily_pattern(self, metrics: List[WorkloadMetrics]) -> Dict:
        """Analyze daily workload patterns"""
        try:
            # Group by day of week
            daily_data = {}
            for metric in metrics:
                day = metric.timestamp.strftime('%A')  # Monday, Tuesday, etc.
                if day not in daily_data:
                    daily_data[day] = {
                        'queries': [],
                        'exec_times': []
                    }
                
                daily_data[day]['queries'].append(metric.total_queries)
                daily_data[day]['exec_times'].append(metric.avg_exec_time)
            
            # Calculate averages
            daily_avg = {}
            for day, data in daily_data.items():
                daily_avg[day] = {
                    'avg_queries': sum(data['queries']) / len(data['queries']),
                    'avg_exec_time': sum(data['exec_times']) / len(data['exec_times'])
                }
            
            # Identify busiest days
            if daily_avg:
                busiest_day = max(daily_avg.items(), key=lambda x: x[1]['avg_queries'])
                quietest_day = min(daily_avg.items(), key=lambda x: x[1]['avg_queries'])
            else:
                busiest_day = ('Unknown', {'avg_queries': 0, 'avg_exec_time': 0})
                quietest_day = ('Unknown', {'avg_queries': 0, 'avg_exec_time': 0})
            
            return {
                'daily_averages': daily_avg,
                'busiest_day': busiest_day[0],
                'quietest_day': quietest_day[0]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing daily pattern: {str(e)}")
            return {'daily_averages': {}, 'busiest_day': 'Unknown', 'quietest_day': 'Unknown'}
    
    async def _analyze_query_pattern(
        self,
        connection_id: int,
        days: int
    ) -> Dict:
        """Analyze query execution patterns"""
        try:
            # Get queries from the period
            start_date = datetime.utcnow() - timedelta(days=days)
            queries = self.db.query(Query).filter(
                Query.connection_id == connection_id,
                Query.last_seen_at >= start_date
            ).all()
            
            if not queries:
                return {
                    'total_queries': 0,
                    'unique_queries': 0,
                    'avg_calls_per_query': 0,
                    'slow_queries': 0
                }
            
            total_queries = len(queries)
            total_calls = sum(q.calls for q in queries)
            avg_calls = total_calls / total_queries if total_queries > 0 else 0
            
            # Identify slow queries (> 1 second)
            slow_queries = [q for q in queries if q.avg_exec_time_ms > 1000]
            
            # Identify most frequent queries
            frequent_queries = sorted(queries, key=lambda q: q.calls, reverse=True)[:5]
            
            # Identify most expensive queries
            expensive_queries = sorted(queries, key=lambda q: q.total_exec_time_ms, reverse=True)[:5]
            
            return {
                'total_queries': total_queries,
                'unique_queries': total_queries,
                'total_calls': total_calls,
                'avg_calls_per_query': round(avg_calls, 2),
                'slow_queries_count': len(slow_queries),
                'slow_queries_pct': round(len(slow_queries) / total_queries * 100, 2) if total_queries > 0 else 0,
                'most_frequent': [
                    {
                        'query_id': q.id,
                        'calls': q.calls,
                        'avg_time_ms': q.avg_exec_time_ms
                    }
                    for q in frequent_queries
                ],
                'most_expensive': [
                    {
                        'query_id': q.id,
                        'total_time_ms': q.total_exec_time_ms,
                        'calls': q.calls
                    }
                    for q in expensive_queries
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing query pattern: {str(e)}")
            return {
                'total_queries': 0,
                'unique_queries': 0,
                'avg_calls_per_query': 0,
                'slow_queries_count': 0
            }
    
    def _analyze_resource_pattern(self, metrics: List[WorkloadMetrics]) -> Dict:
        """Analyze resource usage patterns"""
        try:
            cpu_values = [m.cpu_usage for m in metrics if m.cpu_usage is not None]
            io_values = [m.io_usage for m in metrics if m.io_usage is not None]
            memory_values = [m.memory_usage for m in metrics if m.memory_usage is not None]
            
            return {
                'cpu': {
                    'avg': round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else 0,
                    'max': round(max(cpu_values), 2) if cpu_values else 0,
                    'min': round(min(cpu_values), 2) if cpu_values else 0
                },
                'io': {
                    'avg': round(sum(io_values) / len(io_values), 2) if io_values else 0,
                    'max': round(max(io_values), 2) if io_values else 0,
                    'min': round(min(io_values), 2) if io_values else 0
                },
                'memory': {
                    'avg': round(sum(memory_values) / len(memory_values), 2) if memory_values else 0,
                    'max': round(max(memory_values), 2) if memory_values else 0,
                    'min': round(min(memory_values), 2) if memory_values else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing resource pattern: {str(e)}")
            return {'cpu': {}, 'io': {}, 'memory': {}}
    
    def _classify_workload_type(
        self,
        metrics: List[WorkloadMetrics],
        query_pattern: Dict
    ) -> str:
        """Classify workload type (OLTP, OLAP, Mixed)"""
        try:
            # Calculate average queries per hour
            total_queries = sum(m.total_queries for m in metrics)
            hours = len(metrics) / 60  # Assuming metrics are per minute
            queries_per_hour = total_queries / hours if hours > 0 else 0
            
            # Calculate average execution time
            avg_exec_time = sum(m.avg_exec_time for m in metrics) / len(metrics)
            
            # Get slow query percentage
            slow_query_pct = query_pattern.get('slow_queries_pct', 0)
            
            # Classification logic
            # OLTP: High query rate, low execution time, few slow queries
            if queries_per_hour > 1000 and avg_exec_time < 100 and slow_query_pct < 10:
                return "oltp"
            
            # OLAP: Low query rate, high execution time, many slow queries
            if queries_per_hour < 100 and avg_exec_time > 1000 and slow_query_pct > 30:
                return "olap"
            
            # Mixed workload
            return "mixed"
            
        except Exception as e:
            logger.error(f"Error classifying workload type: {str(e)}")
            return "unknown"
    
    def _identify_trends(self, metrics: List[WorkloadMetrics]) -> Dict:
        """Identify trends in workload over time"""
        try:
            if len(metrics) < 10:
                return {'message': 'Insufficient data for trend analysis'}
            
            # Split into first half and second half
            mid = len(metrics) // 2
            first_half = metrics[:mid]
            second_half = metrics[mid:]
            
            # Calculate averages for each half
            first_avg_queries = sum(m.total_queries for m in first_half) / len(first_half)
            second_avg_queries = sum(m.total_queries for m in second_half) / len(second_half)
            
            first_avg_time = sum(m.avg_exec_time for m in first_half) / len(first_half)
            second_avg_time = sum(m.avg_exec_time for m in second_half) / len(second_half)
            
            # Determine trends
            query_trend = 'increasing' if second_avg_queries > first_avg_queries * 1.1 else \
                         'decreasing' if second_avg_queries < first_avg_queries * 0.9 else \
                         'stable'
            
            time_trend = 'increasing' if second_avg_time > first_avg_time * 1.1 else \
                        'decreasing' if second_avg_time < first_avg_time * 0.9 else \
                        'stable'
            
            return {
                'query_volume_trend': query_trend,
                'execution_time_trend': time_trend,
                'first_period_avg_queries': round(first_avg_queries, 2),
                'second_period_avg_queries': round(second_avg_queries, 2),
                'first_period_avg_time': round(first_avg_time, 2),
                'second_period_avg_time': round(second_avg_time, 2)
            }
            
        except Exception as e:
            logger.error(f"Error identifying trends: {str(e)}")
            return {'message': 'Error analyzing trends'}
    
    def _generate_insights(
        self,
        hourly: Dict,
        daily: Dict,
        query: Dict,
        resource: Dict,
        workload_type: str
    ) -> List[str]:
        """Generate insights from workload analysis"""
        insights = []
        
        # Workload type insights
        if workload_type == 'oltp':
            insights.append("OLTP workload detected: Optimize for high concurrency and low latency")
        elif workload_type == 'olap':
            insights.append("OLAP workload detected: Optimize for complex queries and large data scans")
        elif workload_type == 'mixed':
            insights.append("Mixed workload detected: Balance between OLTP and OLAP optimizations")
        
        # Peak hours insights
        peak_hours = hourly.get('peak_hours', [])
        if peak_hours:
            peak_str = ', '.join(f"{h}:00" for h in peak_hours)
            insights.append(f"Peak hours identified: {peak_str}. Schedule maintenance outside these times")
        
        # Slow query insights
        slow_pct = query.get('slow_queries_pct', 0)
        if slow_pct > 20:
            insights.append(f"{slow_pct}% of queries are slow (>1s). Consider optimization")
        elif slow_pct > 10:
            insights.append(f"{slow_pct}% of queries are slow. Monitor and optimize as needed")
        
        # Resource usage insights
        cpu_avg = resource.get('cpu', {}).get('avg', 0)
        if cpu_avg > 80:
            insights.append(f"High CPU usage ({cpu_avg}%). Consider scaling or optimization")
        elif cpu_avg > 60:
            insights.append(f"Moderate CPU usage ({cpu_avg}%). Monitor for growth")
        
        io_avg = resource.get('io', {}).get('avg', 0)
        if io_avg > 80:
            insights.append(f"High I/O usage ({io_avg}%). Consider faster storage or caching")
        
        memory_avg = resource.get('memory', {}).get('avg', 0)
        if memory_avg > 80:
            insights.append(f"High memory usage ({memory_avg}%). Consider increasing memory or optimization")
        
        # Daily pattern insights
        busiest = daily.get('busiest_day', 'Unknown')
        if busiest != 'Unknown':
            insights.append(f"Busiest day: {busiest}. Plan capacity accordingly")
        
        return insights if insights else ["No significant insights identified"]
    
    def generate_proactive_recommendations(
        self,
        connection_id: int,
        days: int = 7
    ) -> List[Dict]:
        """
        Generate proactive optimization recommendations based on workload analysis
        
        Args:
            connection_id: Connection ID
            days: Number of days to analyze
            
        Returns:
            List of recommendation dictionaries
        """
        try:
            logger.info(f"Generating proactive recommendations for connection {connection_id}")
            
            # Get workload metrics
            start_date = datetime.utcnow() - timedelta(days=days)
            metrics = self.db.query(WorkloadMetrics).filter(
                WorkloadMetrics.connection_id == connection_id,
                WorkloadMetrics.timestamp >= start_date
            ).all()
            
            if not metrics:
                return []
            
            recommendations = []
            
            # Analyze patterns
            hourly_pattern = self._analyze_hourly_pattern(metrics)
            query_pattern = self.db.query(Query).filter(
                Query.connection_id == connection_id,
                Query.last_seen_at >= start_date
            ).all()
            
            # Recommendation 1: Index optimization based on slow queries
            slow_queries = [q for q in query_pattern if q.avg_exec_time_ms > 1000]
            if len(slow_queries) > 0:
                recommendations.append({
                    'type': 'index_optimization',
                    'priority': 'high' if len(slow_queries) > 10 else 'medium',
                    'title': 'Index Optimization Needed',
                    'description': f'Found {len(slow_queries)} slow queries that may benefit from indexing',
                    'action': 'Review slow queries and create appropriate indexes',
                    'estimated_impact': 'High - Can reduce query time by 50-90%',
                    'affected_queries': len(slow_queries)
                })
            
            # Recommendation 2: Peak hour capacity planning
            peak_hours = hourly_pattern.get('peak_hours', [])
            if len(peak_hours) > 0:
                avg_peak_queries = sum(
                    hourly_pattern['hourly_averages'][h]['avg_queries'] 
                    for h in peak_hours
                ) / len(peak_hours)
                
                recommendations.append({
                    'type': 'capacity_planning',
                    'priority': 'medium',
                    'title': 'Peak Hour Capacity Planning',
                    'description': f'Peak hours ({len(peak_hours)} hours) handle {avg_peak_queries:.0f} queries/hour on average',
                    'action': 'Consider auto-scaling or connection pooling during peak hours',
                    'estimated_impact': 'Medium - Improves response time during peak load',
                    'peak_hours': peak_hours
                })
            
            # Recommendation 3: Query caching for frequent queries
            frequent_queries = sorted(query_pattern, key=lambda q: q.calls, reverse=True)[:10]
            if frequent_queries and frequent_queries[0].calls > 100:
                total_time_saved = sum(q.total_exec_time_ms for q in frequent_queries[:5])
                recommendations.append({
                    'type': 'query_caching',
                    'priority': 'high',
                    'title': 'Enable Query Result Caching',
                    'description': f'Top 5 frequent queries account for {total_time_saved/1000:.1f}s of execution time',
                    'action': 'Implement query result caching for frequently executed queries',
                    'estimated_impact': f'High - Can save {total_time_saved/1000:.1f}s per analysis period',
                    'cacheable_queries': len(frequent_queries)
                })
            
            # Recommendation 4: Resource optimization
            cpu_values = [m.cpu_usage for m in metrics if m.cpu_usage is not None]
            if cpu_values:
                avg_cpu = sum(cpu_values) / len(cpu_values)
                max_cpu = max(cpu_values)
                
                if avg_cpu > 70:
                    recommendations.append({
                        'type': 'resource_optimization',
                        'priority': 'high' if avg_cpu > 85 else 'medium',
                        'title': 'High CPU Usage Detected',
                        'description': f'Average CPU usage: {avg_cpu:.1f}%, Peak: {max_cpu:.1f}%',
                        'action': 'Review query efficiency, consider vertical scaling, or optimize database configuration',
                        'estimated_impact': 'High - Prevents performance degradation',
                        'current_usage': avg_cpu
                    })
            
            # Recommendation 5: Workload-specific optimizations
            workload_type = self._classify_workload_type(metrics, {
                'slow_queries_pct': len(slow_queries) / len(query_pattern) * 100 if query_pattern else 0
            })
            
            if workload_type == 'oltp':
                recommendations.append({
                    'type': 'workload_optimization',
                    'priority': 'medium',
                    'title': 'OLTP Workload Optimization',
                    'description': 'Workload is primarily OLTP (high transaction volume)',
                    'action': 'Optimize for: connection pooling, index tuning, and query plan caching',
                    'estimated_impact': 'Medium - Improves transaction throughput',
                    'workload_type': 'oltp'
                })
            elif workload_type == 'olap':
                recommendations.append({
                    'type': 'workload_optimization',
                    'priority': 'medium',
                    'title': 'OLAP Workload Optimization',
                    'description': 'Workload is primarily OLAP (analytical queries)',
                    'action': 'Optimize for: parallel query execution, materialized views, and columnar storage',
                    'estimated_impact': 'Medium - Improves analytical query performance',
                    'workload_type': 'olap'
                })
            
            logger.info(f"Generated {len(recommendations)} proactive recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating proactive recommendations: {str(e)}")
            return []
    
    def predict_performance_trends(
        self,
        connection_id: int,
        days: int = 7
    ) -> Dict:
        """
        Predict future performance trends based on historical data
        
        Args:
            connection_id: Connection ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend predictions
        """
        try:
            logger.info(f"Predicting performance trends for connection {connection_id}")
            
            # Get workload metrics
            start_date = datetime.utcnow() - timedelta(days=days)
            metrics = self.db.query(WorkloadMetrics).filter(
                WorkloadMetrics.connection_id == connection_id,
                WorkloadMetrics.timestamp >= start_date
            ).order_by(WorkloadMetrics.timestamp).all()
            
            if len(metrics) < 10:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need at least 10 data points for trend prediction'
                }
            
            # Calculate trends using simple linear regression approach
            query_volumes = [m.total_queries for m in metrics]
            exec_times = [m.avg_exec_time for m in metrics]
            
            # Calculate growth rates
            first_half_queries = sum(query_volumes[:len(query_volumes)//2]) / (len(query_volumes)//2)
            second_half_queries = sum(query_volumes[len(query_volumes)//2:]) / (len(query_volumes) - len(query_volumes)//2)
            query_growth_rate = ((second_half_queries - first_half_queries) / first_half_queries * 100) if first_half_queries > 0 else 0
            
            first_half_time = sum(exec_times[:len(exec_times)//2]) / (len(exec_times)//2)
            second_half_time = sum(exec_times[len(exec_times)//2:]) / (len(exec_times) - len(exec_times)//2)
            time_growth_rate = ((second_half_time - first_half_time) / first_half_time * 100) if first_half_time > 0 else 0
            
            # Predict next period
            current_avg_queries = sum(query_volumes[-7:]) / min(7, len(query_volumes))
            predicted_queries = current_avg_queries * (1 + query_growth_rate / 100)
            
            current_avg_time = sum(exec_times[-7:]) / min(7, len(exec_times))
            predicted_time = current_avg_time * (1 + time_growth_rate / 100)
            
            # Determine trend direction
            query_trend = 'increasing' if query_growth_rate > 5 else 'decreasing' if query_growth_rate < -5 else 'stable'
            time_trend = 'increasing' if time_growth_rate > 5 else 'decreasing' if time_growth_rate < -5 else 'stable'
            
            # Generate warnings
            warnings = []
            if query_growth_rate > 20:
                warnings.append(f"Query volume growing rapidly ({query_growth_rate:.1f}%). Plan for capacity increase")
            if time_growth_rate > 20:
                warnings.append(f"Execution time increasing rapidly ({time_growth_rate:.1f}%). Investigate performance degradation")
            
            return {
                'status': 'success',
                'analysis_period_days': days,
                'query_volume': {
                    'current_avg': round(current_avg_queries, 2),
                    'predicted_next_period': round(predicted_queries, 2),
                    'growth_rate_pct': round(query_growth_rate, 2),
                    'trend': query_trend
                },
                'execution_time': {
                    'current_avg_ms': round(current_avg_time, 2),
                    'predicted_next_period_ms': round(predicted_time, 2),
                    'growth_rate_pct': round(time_growth_rate, 2),
                    'trend': time_trend
                },
                'warnings': warnings,
                'confidence': 'medium' if len(metrics) > 20 else 'low',
                'predicted_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting performance trends: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def identify_peak_hours(
        self,
        connection_id: int,
        days: int = 7
    ) -> List[int]:
        """
        Identify peak hours for a connection
        
        Args:
            connection_id: Connection ID
            days: Number of days to analyze
            
        Returns:
            List of peak hours (0-23)
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            metrics = self.db.query(WorkloadMetrics).filter(
                WorkloadMetrics.connection_id == connection_id,
                WorkloadMetrics.timestamp >= start_date
            ).all()
            
            if not metrics:
                return []
            
            hourly_pattern = self._analyze_hourly_pattern(metrics)
            return hourly_pattern.get('peak_hours', [])
            
        except Exception as e:
            logger.error(f"Error identifying peak hours: {str(e)}")
            return []
    
    async def detect_workload_shifts(
        self,
        connection_id: int,
        days: int = 7
    ) -> List[Dict]:
        """
        Detect significant shifts in workload patterns
        
        Args:
            connection_id: Connection ID
            days: Number of days to analyze
            
        Returns:
            List of detected workload shifts
        """
        try:
            logger.info(f"Detecting workload shifts for connection {connection_id}")
            
            start_date = datetime.utcnow() - timedelta(days=days)
            metrics = self.db.query(WorkloadMetrics).filter(
                WorkloadMetrics.connection_id == connection_id,
                WorkloadMetrics.timestamp >= start_date
            ).order_by(WorkloadMetrics.timestamp).all()
            
            if len(metrics) < 20:
                return []
            
            shifts = []
            
            # Analyze in windows
            window_size = len(metrics) // 4  # 4 windows
            
            for i in range(3):  # Compare 3 consecutive windows
                window1 = metrics[i * window_size:(i + 1) * window_size]
                window2 = metrics[(i + 1) * window_size:(i + 2) * window_size]
                
                avg1_queries = sum(m.total_queries for m in window1) / len(window1)
                avg2_queries = sum(m.total_queries for m in window2) / len(window2)
                
                avg1_time = sum(m.avg_exec_time for m in window1) / len(window1)
                avg2_time = sum(m.avg_exec_time for m in window2) / len(window2)
                
                # Detect significant changes (>30%)
                query_change = ((avg2_queries - avg1_queries) / avg1_queries * 100) if avg1_queries > 0 else 0
                time_change = ((avg2_time - avg1_time) / avg1_time * 100) if avg1_time > 0 else 0
                
                if abs(query_change) > 30 or abs(time_change) > 30:
                    shifts.append({
                        'detected_at': window2[0].timestamp.isoformat(),
                        'query_volume_change_pct': round(query_change, 2),
                        'execution_time_change_pct': round(time_change, 2),
                        'severity': 'high' if abs(query_change) > 50 or abs(time_change) > 50 else 'medium'
                    })
            
            logger.info(f"Detected {len(shifts)} workload shifts")
            return shifts
            
        except Exception as e:
            logger.error(f"Error detecting workload shifts: {str(e)}")
            return []
    
    def classify_workload_type(
        self,
        connection_id: int,
        days: int = 7
    ) -> str:
        """
        Classify workload type for a connection
        
        Args:
            connection_id: Connection ID
            days: Number of days to analyze
            
        Returns:
            Workload type (oltp, olap, mixed, unknown)
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            metrics = self.db.query(WorkloadMetrics).filter(
                WorkloadMetrics.connection_id == connection_id,
                WorkloadMetrics.timestamp >= start_date
            ).all()
            
            if not metrics:
                return "unknown"
            
            # Get query pattern
            query_pattern = self.db.query(Query).filter(
                Query.connection_id == connection_id,
                Query.last_seen_at >= start_date
            ).all()
            
            query_info = {
                'slow_queries_pct': len([q for q in query_pattern if q.avg_exec_time_ms > 1000]) / len(query_pattern) * 100 if query_pattern else 0
            }
            
            return self._classify_workload_type(metrics, query_info)
            
        except Exception as e:
            logger.error(f"Error classifying workload type: {str(e)}")
            return "unknown"
    
    async def store_workload_metrics(
        self,
        connection_id: int,
        metrics: Dict
    ) -> bool:
        """
        Store workload metrics in database
        
        Args:
            connection_id: Connection ID
            metrics: Metrics dictionary
            
        Returns:
            True if stored successfully
        """
        try:
            workload_metric = WorkloadMetrics(
                connection_id=connection_id,
                timestamp=datetime.utcnow(),
                total_queries=metrics.get('total_queries', 0),
                avg_exec_time=metrics.get('avg_exec_time', 0.0),
                cpu_usage=metrics.get('cpu_usage'),
                io_usage=metrics.get('io_usage'),
                memory_usage=metrics.get('memory_usage'),
                active_connections=metrics.get('active_connections'),
                slow_queries_count=metrics.get('slow_queries_count'),
                workload_type=metrics.get('workload_type')
            )
            
            self.db.add(workload_metric)
            self.db.commit()
            
            logger.info(f"Workload metrics stored for connection {connection_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing workload metrics: {str(e)}")
            return False
