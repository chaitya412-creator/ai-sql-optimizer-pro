"""
Safe Fix Applicator
Applies SQL optimizations and fixes with safety checks and rollback capabilities
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, time
from loguru import logger
from enum import Enum
import re


class FixType(str, Enum):
    """Types of fixes that can be applied"""
    INDEX_CREATION = "index_creation"
    STATISTICS_UPDATE = "statistics_update"
    QUERY_REWRITE = "query_rewrite"
    CONFIGURATION_CHANGE = "configuration_change"
    VACUUM = "vacuum"
    REINDEX = "reindex"


class FixStatus(str, Enum):
    """Status of fix application"""
    PENDING = "pending"
    VALIDATING = "validating"
    APPLYING = "applying"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class SafetyCheckResult:
    """Result of safety checks"""
    
    def __init__(self, passed: bool, reason: str = ""):
        self.passed = passed
        self.reason = reason
        self.timestamp = datetime.utcnow()


class FixApplicator:
    """Applies database fixes safely with rollback capabilities"""
    
    def __init__(self, db_manager, config: Optional[Dict[str, Any]] = None):
        """
        Initialize fix applicator
        
        Args:
            db_manager: DatabaseManager instance
            config: Configuration for safety checks
        """
        self.db_manager = db_manager
        self.config = config or {}
        self.applied_fixes = []
        self.rollback_stack = []
    
    def apply_fix(
        self,
        fix_type: FixType,
        fix_sql: str,
        dry_run: bool = False,
        skip_safety_checks: bool = False
    ) -> Dict[str, Any]:
        """
        Apply a single fix with safety checks
        
        Args:
            fix_type: Type of fix to apply
            fix_sql: SQL statement to execute
            dry_run: If True, only validate without executing
            skip_safety_checks: Skip safety validations
        
        Returns:
            Result dictionary with success status and details
        """
        try:
            logger.info(f"Applying fix: {fix_type.value} (dry_run={dry_run})")
            
            # Step 1: Safety checks
            if not skip_safety_checks:
                safety_result = self._run_safety_checks(fix_type, fix_sql)
                if not safety_result.passed:
                    return {
                        "success": False,
                        "status": FixStatus.FAILED.value,
                        "error": f"Safety check failed: {safety_result.reason}",
                        "fix_type": fix_type.value
                    }
            
            # Step 2: Validate SQL syntax
            validation_result = self._validate_sql(fix_sql)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "status": FixStatus.FAILED.value,
                    "error": f"SQL validation failed: {validation_result['error']}",
                    "fix_type": fix_type.value
                }
            
            # Step 3: Dry run mode - return without executing
            if dry_run:
                return {
                    "success": True,
                    "status": FixStatus.VALIDATING.value,
                    "message": "Dry run successful - fix is valid and safe to apply",
                    "fix_type": fix_type.value,
                    "fix_sql": fix_sql
                }
            
            # Step 4: Create rollback plan
            rollback_sql = self._generate_rollback_sql(fix_type, fix_sql)
            
            # Step 5: Execute fix
            start_time = datetime.utcnow()
            
            try:
                # Begin transaction for DDL if supported
                if fix_type in [FixType.INDEX_CREATION, FixType.REINDEX]:
                    # Some databases don't support transactional DDL
                    result = self.db_manager.execute_query(fix_sql)
                else:
                    result = self.db_manager.execute_query(fix_sql)
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Step 6: Record fix for potential rollback
                fix_record = {
                    "fix_type": fix_type.value,
                    "fix_sql": fix_sql,
                    "rollback_sql": rollback_sql,
                    "applied_at": start_time,
                    "execution_time_sec": execution_time,
                    "result": result
                }
                
                self.applied_fixes.append(fix_record)
                self.rollback_stack.append(rollback_sql)
                
                logger.info(f"Fix applied successfully in {execution_time:.2f}s")
                
                return {
                    "success": True,
                    "status": FixStatus.APPLIED.value,
                    "message": f"Fix applied successfully in {execution_time:.2f}s",
                    "fix_type": fix_type.value,
                    "fix_sql": fix_sql,
                    "rollback_sql": rollback_sql,
                    "execution_time_sec": execution_time
                }
            
            except Exception as e:
                logger.error(f"Fix application failed: {e}")
                return {
                    "success": False,
                    "status": FixStatus.FAILED.value,
                    "error": str(e),
                    "fix_type": fix_type.value
                }
        
        except Exception as e:
            logger.error(f"Error in apply_fix: {e}")
            return {
                "success": False,
                "status": FixStatus.FAILED.value,
                "error": str(e),
                "fix_type": fix_type.value
            }
    
    def apply_fixes_batch(
        self,
        fixes: List[Dict[str, Any]],
        dry_run: bool = False,
        stop_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Apply multiple fixes in batch
        
        Args:
            fixes: List of fix dictionaries with 'type' and 'sql' keys
            dry_run: If True, validate all without executing
            stop_on_error: If True, stop on first error
        
        Returns:
            Batch result with individual fix results
        """
        results = []
        successful = 0
        failed = 0
        
        for i, fix in enumerate(fixes):
            fix_type = FixType(fix["type"])
            fix_sql = fix["sql"]
            
            result = self.apply_fix(
                fix_type=fix_type,
                fix_sql=fix_sql,
                dry_run=dry_run,
                skip_safety_checks=fix.get("skip_safety_checks", False)
            )
            
            results.append(result)
            
            if result["success"]:
                successful += 1
            else:
                failed += 1
                if stop_on_error and not dry_run:
                    logger.warning(f"Stopping batch at fix {i+1} due to error")
                    break
        
        return {
            "total_fixes": len(fixes),
            "successful": successful,
            "failed": failed,
            "results": results,
            "dry_run": dry_run
        }
    
    def rollback_last_fix(self) -> Dict[str, Any]:
        """Rollback the last applied fix"""
        if not self.rollback_stack:
            return {
                "success": False,
                "error": "No fixes to rollback"
            }
        
        try:
            rollback_sql = self.rollback_stack.pop()
            last_fix = self.applied_fixes.pop()
            
            if rollback_sql:
                logger.info(f"Rolling back fix: {last_fix['fix_type']}")
                self.db_manager.execute_query(rollback_sql)
                
                return {
                    "success": True,
                    "message": f"Rolled back {last_fix['fix_type']}",
                    "fix_type": last_fix['fix_type'],
                    "rollback_sql": rollback_sql
                }
            else:
                return {
                    "success": False,
                    "error": "No rollback SQL available for this fix"
                }
        
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def rollback_all(self) -> Dict[str, Any]:
        """Rollback all applied fixes in reverse order"""
        results = []
        
        while self.rollback_stack:
            result = self.rollback_last_fix()
            results.append(result)
        
        successful = sum(1 for r in results if r["success"])
        
        return {
            "total_rolled_back": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "results": results
        }
    
    def _run_safety_checks(self, fix_type: FixType, fix_sql: str) -> SafetyCheckResult:
        """Run safety checks before applying fix"""
        
        # Check 1: Business hours (if configured)
        if self.config.get("business_hours_only", False):
            if not self._is_business_hours():
                return SafetyCheckResult(
                    False,
                    "Fix can only be applied during business hours"
                )
        
        # Check 2: Dangerous operations
        if self._is_dangerous_operation(fix_sql):
            if not self.config.get("allow_dangerous_operations", False):
                return SafetyCheckResult(
                    False,
                    "Dangerous operation detected (DROP, TRUNCATE, DELETE without WHERE)"
                )
        
        # Check 3: DDL execution enabled
        if fix_type in [FixType.INDEX_CREATION, FixType.REINDEX]:
            if not self.config.get("enable_ddl_execution", True):
                return SafetyCheckResult(
                    False,
                    "DDL execution is disabled in configuration"
                )
        
        # Check 4: Lock detection (if possible)
        if self._has_active_locks():
            return SafetyCheckResult(
                False,
                "Active locks detected on target tables"
            )
        
        return SafetyCheckResult(True, "All safety checks passed")
    
    def _validate_sql(self, sql: str) -> Dict[str, Any]:
        """Validate SQL syntax"""
        try:
            # Basic validation
            if not sql or not sql.strip():
                return {"valid": False, "error": "Empty SQL statement"}
            
            # Check for SQL injection patterns
            dangerous_patterns = [
                r";\s*DROP\s+",
                r";\s*DELETE\s+FROM\s+\w+\s*;",
                r"--\s*$",
                r"/\*.*\*/"
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, sql, re.IGNORECASE):
                    return {
                        "valid": False,
                        "error": f"Potentially dangerous pattern detected: {pattern}"
                    }
            
            return {"valid": True}
        
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _generate_rollback_sql(self, fix_type: FixType, fix_sql: str) -> Optional[str]:
        """Generate rollback SQL for a fix"""
        try:
            if fix_type == FixType.INDEX_CREATION:
                # Extract index name from CREATE INDEX statement
                match = re.search(r'CREATE\s+INDEX\s+(\w+)', fix_sql, re.IGNORECASE)
                if match:
                    index_name = match.group(1)
                    return f"DROP INDEX IF EXISTS {index_name};"
            
            elif fix_type == FixType.STATISTICS_UPDATE:
                # ANALYZE doesn't need rollback
                return None
            
            elif fix_type == FixType.VACUUM:
                # VACUUM doesn't need rollback
                return None
            
            elif fix_type == FixType.QUERY_REWRITE:
                # Query rewrites don't need rollback (they're not DDL)
                return None
            
            elif fix_type == FixType.CONFIGURATION_CHANGE:
                # Would need to store original config value
                return "-- Manual rollback required for configuration changes"
            
            return None
        
        except Exception as e:
            logger.error(f"Error generating rollback SQL: {e}")
            return None
    
    def _is_business_hours(self) -> bool:
        """Check if current time is within business hours"""
        now = datetime.now().time()
        
        # Default business hours: 9 AM to 5 PM
        start_hour = self.config.get("business_hours_start", 9)
        end_hour = self.config.get("business_hours_end", 17)
        
        business_start = time(start_hour, 0)
        business_end = time(end_hour, 0)
        
        # Check if weekend
        if datetime.now().weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        return business_start <= now <= business_end
    
    def _is_dangerous_operation(self, sql: str) -> bool:
        """Check if SQL contains dangerous operations"""
        dangerous_keywords = [
            r'\bDROP\s+TABLE\b',
            r'\bTRUNCATE\b',
            r'\bDELETE\s+FROM\s+\w+\s*;',  # DELETE without WHERE
            r'\bUPDATE\s+\w+\s+SET\s+.*\s*;'  # UPDATE without WHERE
        ]
        
        for pattern in dangerous_keywords:
            if re.search(pattern, sql, re.IGNORECASE):
                return True
        
        return False
    
    def _has_active_locks(self) -> bool:
        """Check for active locks on target tables"""
        try:
            # This would need to query database-specific lock tables
            # Simplified implementation
            return False
        except Exception as e:
            logger.error(f"Error checking locks: {e}")
            return False
    
    def get_applied_fixes_summary(self) -> Dict[str, Any]:
        """Get summary of all applied fixes"""
        return {
            "total_fixes_applied": len(self.applied_fixes),
            "fixes": self.applied_fixes,
            "rollback_available": len(self.rollback_stack) > 0,
            "rollback_count": len(self.rollback_stack)
        }


class FixRecommendationParser:
    """Parse fix recommendations from Ollama into executable fixes"""
    
    @staticmethod
    def parse_index_recommendations(recommendations: List[str]) -> List[Dict[str, Any]]:
        """Parse index creation recommendations"""
        fixes = []
        
        for rec in recommendations:
            # Extract CREATE INDEX statements
            if "CREATE INDEX" in rec.upper():
                fixes.append({
                    "type": FixType.INDEX_CREATION.value,
                    "sql": rec.strip(),
                    "description": "Create missing index",
                    "estimated_impact": "high"
                })
        
        return fixes
    
    @staticmethod
    def parse_maintenance_tasks(tasks: List[str]) -> List[Dict[str, Any]]:
        """Parse maintenance task recommendations"""
        fixes = []
        
        for task in tasks:
            task_upper = task.upper()
            
            if "ANALYZE" in task_upper:
                fixes.append({
                    "type": FixType.STATISTICS_UPDATE.value,
                    "sql": task.strip(),
                    "description": "Update table statistics",
                    "estimated_impact": "medium"
                })
            
            elif "VACUUM" in task_upper:
                fixes.append({
                    "type": FixType.VACUUM.value,
                    "sql": task.strip(),
                    "description": "Vacuum table",
                    "estimated_impact": "medium"
                })
            
            elif "REINDEX" in task_upper:
                fixes.append({
                    "type": FixType.REINDEX.value,
                    "sql": task.strip(),
                    "description": "Rebuild index",
                    "estimated_impact": "low"
                })
        
        return fixes
    
    @staticmethod
    def parse_all_recommendations(
        ollama_recommendations: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Parse all recommendations from Ollama response"""
        all_fixes = []
        
        # Parse index recommendations
        if "index_recommendations" in ollama_recommendations:
            all_fixes.extend(
                FixRecommendationParser.parse_index_recommendations(
                    ollama_recommendations["index_recommendations"]
                )
            )
        
        # Parse maintenance tasks
        if "maintenance_tasks" in ollama_recommendations:
            all_fixes.extend(
                FixRecommendationParser.parse_maintenance_tasks(
                    ollama_recommendations["maintenance_tasks"]
                )
            )
        
        return all_fixes
