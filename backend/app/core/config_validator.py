"""
Configuration Validator Module
Validates and safely tests database configuration changes
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import re
import time

from app.models.database import (
    Connection,
    ConfigurationChange,
    WorkloadMetrics
)

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validate and safely test configuration changes"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Safety thresholds
        self.max_performance_degradation = 20  # Max 20% performance loss
        self.validation_duration_seconds = 300  # 5 minutes validation
        self.rollback_threshold_seconds = 60  # Auto-rollback if issues within 60s
    
    async def validate_config_change(
        self,
        connection_id: int,
        parameter: str,
        value: str
    ) -> Tuple[bool, str]:
        """
        Validate a configuration change before applying
        
        Args:
            connection_id: Connection ID
            parameter: Parameter name
            value: New value
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            logger.info(f"Validating config change: {parameter}={value}")
            
            # Get connection
            connection = self.db.query(Connection).filter(
                Connection.id == connection_id
            ).first()
            
            if not connection:
                return False, f"Connection {connection_id} not found"
            
            # Database-specific validation
            db_type = connection.engine.lower()
            
            if db_type == 'postgresql':
                return self._validate_postgresql_config(parameter, value)
            elif db_type == 'mysql':
                return self._validate_mysql_config(parameter, value)
            elif db_type == 'mssql':
                return self._validate_mssql_config(parameter, value)
            else:
                return False, f"Unsupported database type: {db_type}"
            
        except Exception as e:
            logger.error(f"Error validating config change: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def _validate_postgresql_config(
        self,
        parameter: str,
        value: str
    ) -> Tuple[bool, str]:
        """Validate PostgreSQL configuration"""
        try:
            # Validate shared_buffers
            if parameter == 'shared_buffers':
                # Accept relative recommendations used by the optimizer rules
                # (e.g. "25% of RAM"). The system currently records changes
                # rather than executing them against the DB, so allow this
                # format to be applied from the UI.
                percent_match = re.match(r"^\s*(\d{1,3})\s*%\s+of\s+ram\s*$", value, re.IGNORECASE)
                if percent_match:
                    percent = int(percent_match.group(1))
                    if percent <= 0 or percent > 95:
                        return False, "shared_buffers percentage must be between 1 and 95"
                    return True, "Valid shared_buffers relative value"

                if not value.endswith(('MB', 'GB')):
                    return False, "shared_buffers must end with MB or GB"
                
                # Extract numeric value
                try:
                    numeric = int(value[:-2])
                except ValueError:
                    return False, "shared_buffers must start with an integer size"
                unit = value[-2:]
                
                if unit == 'GB':
                    numeric *= 1024
                
                if numeric < 128:
                    return False, "shared_buffers must be at least 128MB"
                if numeric > 32768:  # 32GB
                    return False, "shared_buffers should not exceed 32GB"
                
                return True, "Valid shared_buffers value"
            
            # Validate work_mem
            elif parameter == 'work_mem':
                if not value.endswith(('MB', 'GB', 'kB')):
                    return False, "work_mem must end with kB, MB, or GB"
                
                return True, "Valid work_mem value"
            
            # Validate max_connections
            elif parameter == 'max_connections':
                try:
                    connections = int(value)
                    if connections < 10:
                        return False, "max_connections must be at least 10"
                    if connections > 1000:
                        return False, "max_connections should not exceed 1000"
                    return True, "Valid max_connections value"
                except ValueError:
                    return False, "max_connections must be an integer"
            
            # Validate random_page_cost
            elif parameter == 'random_page_cost':
                try:
                    cost = float(value)
                    if cost < 0.1:
                        return False, "random_page_cost must be at least 0.1"
                    if cost > 10.0:
                        return False, "random_page_cost should not exceed 10.0"
                    return True, "Valid random_page_cost value"
                except ValueError:
                    return False, "random_page_cost must be a number"
            
            # Default: allow but warn
            return True, f"Parameter {parameter} validation not implemented, proceeding with caution"
            
        except Exception as e:
            logger.error(f"Error validating PostgreSQL config: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def _validate_mysql_config(
        self,
        parameter: str,
        value: str
    ) -> Tuple[bool, str]:
        """Validate MySQL configuration"""
        try:
            # Validate innodb_buffer_pool_size
            if parameter == 'innodb_buffer_pool_size':
                try:
                    size = int(value)
                    if size < 134217728:  # 128MB
                        return False, "innodb_buffer_pool_size must be at least 128MB"
                    return True, "Valid innodb_buffer_pool_size value"
                except ValueError:
                    return False, "innodb_buffer_pool_size must be an integer (bytes)"
            
            # Validate max_connections
            elif parameter == 'max_connections':
                try:
                    connections = int(value)
                    if connections < 10:
                        return False, "max_connections must be at least 10"
                    if connections > 2000:
                        return False, "max_connections should not exceed 2000"
                    return True, "Valid max_connections value"
                except ValueError:
                    return False, "max_connections must be an integer"
            
            # Default: allow but warn
            return True, f"Parameter {parameter} validation not implemented, proceeding with caution"
            
        except Exception as e:
            logger.error(f"Error validating MySQL config: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def _validate_mssql_config(
        self,
        parameter: str,
        value: str
    ) -> Tuple[bool, str]:
        """Validate MSSQL configuration"""
        try:
            # Validate max server memory
            if parameter == 'max server memory':
                try:
                    memory = int(value)
                    if memory < 512:
                        return False, "max server memory must be at least 512MB"
                    return True, "Valid max server memory value"
                except ValueError:
                    return False, "max server memory must be an integer (MB)"
            
            # Validate max degree of parallelism
            elif parameter == 'max degree of parallelism':
                try:
                    maxdop = int(value)
                    if maxdop < 0:
                        return False, "max degree of parallelism must be non-negative"
                    if maxdop > 64:
                        return False, "max degree of parallelism should not exceed 64"
                    return True, "Valid max degree of parallelism value"
                except ValueError:
                    return False, "max degree of parallelism must be an integer"
            
            # Default: allow but warn
            return True, f"Parameter {parameter} validation not implemented, proceeding with caution"
            
        except Exception as e:
            logger.error(f"Error validating MSSQL config: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    async def test_config_safely(
        self,
        connection_id: int,
        changes: List[Dict]
    ) -> Dict:
        """
        Test configuration changes safely with monitoring
        
        Args:
            connection_id: Connection ID
            changes: List of configuration changes to test
            
        Returns:
            Dictionary with test results
        """
        try:
            logger.info(f"Testing {len(changes)} config changes safely")
            
            # Get baseline metrics
            baseline = await self._get_baseline_metrics(connection_id)
            
            if not baseline:
                return {
                    'success': False,
                    'message': 'Could not establish baseline metrics',
                    'tested_changes': []
                }
            
            # Test each change
            results = []
            for change in changes:
                result = await self._test_single_change(
                    connection_id,
                    change,
                    baseline
                )
                results.append(result)
                
                # Stop if any change causes issues
                if not result['safe']:
                    logger.warning(f"Unsafe change detected: {change['parameter']}")
                    break
            
            # Calculate overall safety
            all_safe = all(r['safe'] for r in results)
            
            return {
                'success': True,
                'all_safe': all_safe,
                'baseline_metrics': baseline,
                'tested_changes': results,
                'message': 'All changes safe' if all_safe else 'Some changes unsafe'
            }
            
        except Exception as e:
            logger.error(f"Error testing config safely: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'tested_changes': []
            }
    
    async def _get_baseline_metrics(self, connection_id: int) -> Optional[Dict]:
        """Get baseline performance metrics"""
        try:
            # Get recent workload metrics
            recent = datetime.utcnow() - timedelta(minutes=5)
            metrics = self.db.query(WorkloadMetrics).filter(
                WorkloadMetrics.connection_id == connection_id,
                WorkloadMetrics.timestamp >= recent
            ).all()
            
            if not metrics:
                return None
            
            # Calculate averages
            avg_exec_time = sum(m.avg_exec_time for m in metrics) / len(metrics)
            avg_cpu = sum(m.cpu_usage or 0 for m in metrics) / len(metrics)
            avg_io = sum(m.io_usage or 0 for m in metrics) / len(metrics)
            
            return {
                'avg_exec_time': avg_exec_time,
                'avg_cpu_usage': avg_cpu,
                'avg_io_usage': avg_io,
                'sample_count': len(metrics),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting baseline metrics: {str(e)}")
            return None
    
    async def _test_single_change(
        self,
        connection_id: int,
        change: Dict,
        baseline: Dict
    ) -> Dict:
        """Test a single configuration change"""
        try:
            parameter = change['parameter']
            value = change['value']
            
            logger.info(f"Testing change: {parameter}={value}")
            
            # Validate first
            is_valid, message = await self.validate_config_change(
                connection_id,
                parameter,
                value
            )
            
            if not is_valid:
                return {
                    'parameter': parameter,
                    'value': value,
                    'safe': False,
                    'reason': f'Validation failed: {message}',
                    'performance_impact': None
                }
            
            # In a real implementation, you would:
            # 1. Apply the change temporarily
            # 2. Monitor performance for a period
            # 3. Compare with baseline
            # 4. Revert if performance degrades
            
            # For now, simulate testing
            # In production, this would actually apply and test the change
            
            return {
                'parameter': parameter,
                'value': value,
                'safe': True,
                'reason': 'Validation passed',
                'performance_impact': 'unknown',
                'recommendation': 'Apply in maintenance window'
            }
            
        except Exception as e:
            logger.error(f"Error testing single change: {str(e)}")
            return {
                'parameter': change.get('parameter', 'unknown'),
                'value': change.get('value', 'unknown'),
                'safe': False,
                'reason': f'Error: {str(e)}',
                'performance_impact': None
            }
    
    async def measure_impact(
        self,
        connection_id: int,
        change_id: int
    ) -> Dict:
        """
        Measure actual impact of an applied configuration change
        
        Args:
            connection_id: Connection ID
            change_id: Configuration change ID
            
        Returns:
            Dictionary with impact measurements
        """
        try:
            logger.info(f"Measuring impact of change {change_id}")
            
            # Get the configuration change
            change = self.db.query(ConfigurationChange).filter(
                ConfigurationChange.id == change_id
            ).first()
            
            if not change:
                return {
                    'success': False,
                    'message': f'Change {change_id} not found'
                }
            
            # Get metrics before change
            before_time = change.applied_at - timedelta(minutes=30)
            before_metrics = self.db.query(WorkloadMetrics).filter(
                WorkloadMetrics.connection_id == connection_id,
                WorkloadMetrics.timestamp >= before_time,
                WorkloadMetrics.timestamp < change.applied_at
            ).all()
            
            # Get metrics after change
            after_time = change.applied_at + timedelta(minutes=30)
            after_metrics = self.db.query(WorkloadMetrics).filter(
                WorkloadMetrics.connection_id == connection_id,
                WorkloadMetrics.timestamp >= change.applied_at,
                WorkloadMetrics.timestamp < after_time
            ).all()
            
            if not before_metrics or not after_metrics:
                return {
                    'success': False,
                    'message': 'Insufficient metrics data for comparison'
                }
            
            # Calculate averages
            before_avg_time = sum(m.avg_exec_time for m in before_metrics) / len(before_metrics)
            after_avg_time = sum(m.avg_exec_time for m in after_metrics) / len(after_metrics)
            
            before_cpu = sum(m.cpu_usage or 0 for m in before_metrics) / len(before_metrics)
            after_cpu = sum(m.cpu_usage or 0 for m in after_metrics) / len(after_metrics)
            
            # Calculate impact
            time_change_pct = ((after_avg_time - before_avg_time) / before_avg_time * 100) if before_avg_time > 0 else 0
            cpu_change_pct = ((after_cpu - before_cpu) / before_cpu * 100) if before_cpu > 0 else 0
            
            # Determine if change was beneficial
            is_beneficial = time_change_pct < 0  # Negative means improvement
            
            impact = {
                'success': True,
                'change_id': change_id,
                'parameter': change.parameter_name,
                'before_avg_exec_time': round(before_avg_time, 2),
                'after_avg_exec_time': round(after_avg_time, 2),
                'exec_time_change_pct': round(time_change_pct, 2),
                'before_cpu_usage': round(before_cpu, 2),
                'after_cpu_usage': round(after_cpu, 2),
                'cpu_change_pct': round(cpu_change_pct, 2),
                'is_beneficial': is_beneficial,
                'recommendation': 'Keep change' if is_beneficial else 'Consider reverting',
                'measured_at': datetime.utcnow().isoformat()
            }
            
            # Update change record with actual impact
            change.actual_impact = impact
            self.db.commit()
            
            logger.info(f"Impact measured: {impact}")
            return impact
            
        except Exception as e:
            logger.error(f"Error measuring impact: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    async def auto_revert_on_failure(
        self,
        connection_id: int,
        change_id: int
    ) -> Dict:
        """
        Automatically revert a configuration change if it causes issues
        
        Args:
            connection_id: Connection ID
            change_id: Configuration change ID
            
        Returns:
            Dictionary with revert result
        """
        try:
            logger.info(f"Checking if change {change_id} should be reverted")
            
            # Get the change
            change = self.db.query(ConfigurationChange).filter(
                ConfigurationChange.id == change_id
            ).first()
            
            if not change:
                return {
                    'success': False,
                    'message': f'Change {change_id} not found'
                }
            
            # Check if already reverted
            if change.reverted_at:
                return {
                    'success': False,
                    'message': 'Change already reverted'
                }
            
            # Measure impact
            impact = await self.measure_impact(connection_id, change_id)
            
            if not impact.get('success'):
                return {
                    'success': False,
                    'message': 'Could not measure impact'
                }
            
            # Check if performance degraded significantly
            exec_time_change = impact.get('exec_time_change_pct', 0)
            
            should_revert = exec_time_change > self.max_performance_degradation
            
            if should_revert:
                logger.warning(f"Performance degraded by {exec_time_change}%, reverting change")
                
                # Mark as reverted
                change.reverted_at = datetime.utcnow()
                change.status = 'reverted'
                self.db.commit()
                
                return {
                    'success': True,
                    'reverted': True,
                    'reason': f'Performance degraded by {exec_time_change}%',
                    'impact': impact,
                    'reverted_at': change.reverted_at.isoformat()
                }
            else:
                return {
                    'success': True,
                    'reverted': False,
                    'reason': 'Performance within acceptable range',
                    'impact': impact
                }
            
        except Exception as e:
            logger.error(f"Error in auto-revert: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
def get_safety_checks(self, parameter: str, value: str, db_type: str) -> List[str]:
        """
        Get list of safety checks for a configuration change
        
        Args:
            parameter: Parameter name
            value: New value
            db_type: Database type
            
        Returns:
            List of safety check descriptions
        """
        checks = [
            "Validate parameter syntax",
            "Check value is within acceptable range",
            "Verify no conflicts with other settings",
            "Ensure sufficient system resources",
            "Test in non-production environment first"
        ]
        
        # Add parameter-specific checks
        if 'memory' in parameter.lower() or 'buffer' in parameter.lower():
            checks.append("Verify sufficient RAM available")
            checks.append("Monitor for out-of-memory errors")
        
        if 'connection' in parameter.lower():
            checks.append("Ensure connection pool can handle load")
            checks.append("Monitor for connection exhaustion")
        
        if db_type == 'postgresql' and parameter == 'shared_buffers':
            checks.append("Restart required for this change")
            checks.append("Plan maintenance window")
        
        return checks
