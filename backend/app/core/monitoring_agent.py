"""
Proactive Monitoring Agent
Automatically discovers slow queries from target databases
Includes automatic performance issue detection
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger
import hashlib

from app.models.database import SessionLocal, Connection, Query, QueryIssue, WorkloadMetrics
from app.core.db_manager import DatabaseManager
from app.core.security import security_manager
from app.core.plan_analyzer import PlanAnalyzer
from app.config import settings


class MonitoringAgent:
    """
    Background service that periodically polls databases for slow queries
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running_flag = False
        self.last_run = None
        self.queries_discovered_last_run = 0
    
    def start(self):
        """Start the monitoring agent"""
        if not settings.MONITORING_ENABLED:
            logger.info("Monitoring agent is disabled in configuration")
            return
        
        # Schedule the monitoring job
        self.scheduler.add_job(
            self._monitor_databases,
            'interval',
            minutes=settings.MONITORING_INTERVAL_MINUTES,
            id='monitor_databases',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running_flag = True
        logger.info(f"✅ Monitoring agent started (interval: {settings.MONITORING_INTERVAL_MINUTES} minutes)")
    
    def stop(self):
        """Stop the monitoring agent"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running_flag = False
            logger.info("Monitoring agent stopped")
    
    def is_running(self) -> bool:
        """Check if monitoring agent is running"""
        return self.is_running_flag and self.scheduler.running
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitoring agent status"""
        next_run = None
        if self.scheduler.running:
            jobs = self.scheduler.get_jobs()
            if jobs:
                next_run = jobs[0].next_run_time
        
        # Get active connections count
        db = SessionLocal()
        try:
            active_connections = db.query(Connection).filter(
                Connection.monitoring_enabled == True
            ).count()
        finally:
            db.close()
        
        return {
            "is_running": self.is_running(),
            "last_poll_time": self.last_run,
            "next_poll_time": next_run,
            "interval_minutes": settings.MONITORING_INTERVAL_MINUTES,
            "queries_discovered": self.queries_discovered_last_run,
            "active_connections": active_connections
        }
    
    def _monitor_databases(self):
        """
        Main monitoring function - polls all enabled connections
        """
        logger.info("🔍 Starting database monitoring cycle...")
        self.last_run = datetime.utcnow()
        total_queries_discovered = 0
        
        db = SessionLocal()
        try:
            # Get all connections with monitoring enabled
            connections = db.query(Connection).filter(
                Connection.monitoring_enabled == True
            ).all()
            
            logger.info(f"Found {len(connections)} connections to monitor")
            
            for conn in connections:
                try:
                    queries_found = self._monitor_connection(db, conn)
                    total_queries_discovered += queries_found
                    
                    # Update last monitored timestamp
                    conn.last_monitored_at = datetime.utcnow()
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Error monitoring connection {conn.name}: {e}")
                    db.rollback()
            
            self.queries_discovered_last_run = total_queries_discovered
            logger.info(f"✅ Monitoring cycle complete. Discovered {total_queries_discovered} queries")
        
        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}")
        
        finally:
            db.close()
    
    def _monitor_connection(self, db, conn: Connection) -> int:
        """
        Monitor a single database connection
        Returns: Number of queries discovered
        """
        logger.info(f"Monitoring connection: {conn.name} ({conn.engine})")
        
        try:
            # Decrypt password
            password = security_manager.decrypt(conn.password_encrypted)
            
            # Create database manager
            db_manager = DatabaseManager(
                engine=conn.engine,
                host=conn.host,
                port=conn.port,
                database=conn.database,
                username=conn.username,
                password=password,
                ssl_enabled=conn.ssl_enabled
            )
            
            # Connect to database
            success, message = db_manager.connect()
            if not success:
                logger.error(f"Failed to connect to {conn.name}: {message}")
                return 0
            
            try:
                # Get slow queries
                slow_queries = db_manager.get_slow_queries(
                    limit=settings.MAX_QUERIES_PER_POLL
                )
                
                logger.info(f"Found {len(slow_queries)} slow queries from {conn.name}")
                
                # Store queries in observability database
                queries_added = 0
                total_calls = 0
                weighted_exec_ms_sum = 0.0
                slow_queries_count = 0
                for query_data in slow_queries:
                    try:
                        # Generate query hash
                        sql_text = query_data.get("sql_text", "")
                        if not sql_text or sql_text.strip() == "":
                            continue

                        calls = int(query_data.get("calls", 0) or 0)
                        avg_time_ms = float(query_data.get("avg_time_ms", 0) or 0.0)
                        total_calls += calls
                        weighted_exec_ms_sum += avg_time_ms * calls
                        if avg_time_ms >= 1000:
                            slow_queries_count += 1
                        
                        query_hash = hashlib.sha256(sql_text.encode()).hexdigest()[:64]
                        
                        # Check if query already exists
                        existing_query = db.query(Query).filter(
                            Query.connection_id == conn.id,
                            Query.query_hash == query_hash
                        ).first()
                        
                        if existing_query:
                            # Update existing query
                            existing_query.avg_exec_time_ms = query_data.get("avg_time_ms", 0)
                            existing_query.total_exec_time_ms = query_data.get("total_time_ms", 0)
                            existing_query.calls = query_data.get("calls", 0)
                            existing_query.rows_returned = query_data.get("rows_returned")
                            existing_query.buffer_hits = query_data.get("buffer_hits")
                            existing_query.buffer_reads = query_data.get("buffer_reads")
                            existing_query.last_seen_at = datetime.utcnow()
                            query_obj = existing_query
                        else:
                            # Create new query record
                            new_query = Query(
                                connection_id=conn.id,
                                query_hash=query_hash,
                                sql_text=sql_text,
                                avg_exec_time_ms=query_data.get("avg_time_ms", 0),
                                total_exec_time_ms=query_data.get("total_time_ms", 0),
                                calls=query_data.get("calls", 0),
                                rows_returned=query_data.get("rows_returned"),
                                buffer_hits=query_data.get("buffer_hits"),
                                buffer_reads=query_data.get("buffer_reads"),
                                discovered_at=datetime.utcnow(),
                                last_seen_at=datetime.utcnow(),
                                optimized=False
                            )
                            db.add(new_query)
                            db.flush()  # Get the ID
                            query_obj = new_query
                            queries_added += 1
                        
                        db.commit()
                        
                        # Perform automatic analysis for new or updated queries
                        self._analyze_query(db, db_manager, query_obj, conn)
                    
                    except Exception as e:
                        logger.error(f"Error storing query: {e}")
                        db.rollback()

                # Store workload metrics even if no queries were discovered.
                # This ensures Workload Analysis can show charts once monitoring runs.
                try:
                    avg_exec_time_ms = (weighted_exec_ms_sum / total_calls) if total_calls > 0 else 0.0
                    workload_metric = WorkloadMetrics(
                        connection_id=conn.id,
                        timestamp=datetime.utcnow(),
                        total_queries=total_calls,
                        avg_exec_time=avg_exec_time_ms,
                        cpu_usage=None,
                        io_usage=None,
                        memory_usage=None,
                        active_connections=None,
                        slow_queries_count=slow_queries_count,
                        workload_type=None,
                    )
                    db.add(workload_metric)
                    db.commit()
                except Exception as e:
                    logger.error(f"Error storing workload metrics for connection {conn.id}: {e}")
                    db.rollback()
                
                logger.info(f"Added {queries_added} new queries from {conn.name}")
                return queries_added
            
            finally:
                db_manager.disconnect()
        
        except Exception as e:
            logger.error(f"Error in _monitor_connection: {e}")
            return 0
    
    def _analyze_query(self, db, db_manager: DatabaseManager, query_obj: Query, conn: Connection):
        """
        Automatically analyze a discovered query for performance issues
        """
        try:
            logger.info(f"Analyzing query {query_obj.id} for performance issues...")
            
            # Get execution plan (optional, may fail for some queries)
            execution_plan = None
            try:
                execution_plan = db_manager.get_execution_plan(query_obj.sql_text)
            except Exception as e:
                logger.warning(f"Could not get execution plan: {e}")
            
            # Prepare query stats
            query_stats = {
                "buffer_hits": query_obj.buffer_hits,
                "buffer_reads": query_obj.buffer_reads,
                "avg_time_ms": query_obj.avg_exec_time_ms,
                "calls": query_obj.calls
            }
            
            # Perform comprehensive detection
            detection_result = PlanAnalyzer.analyze_plan(
                plan=execution_plan,
                engine=conn.engine,
                sql_query=query_obj.sql_text,
                query_stats=query_stats,
                table_stats=None,
                query_context=None
            )
            
            # Store detection results in query
            query_obj.detected_issues = detection_result
            
            # Delete old issues for this query
            db.query(QueryIssue).filter(
                QueryIssue.query_id == query_obj.id
            ).delete()
            
            # Store individual issues
            issues_stored = 0
            for issue in detection_result.get("issues", []):
                # Skip the "execution plan not available" informational issue
                if issue.get("title") == "Execution plan not available":
                    continue
                
                query_issue = QueryIssue(
                    query_id=query_obj.id,
                    optimization_id=None,
                    connection_id=conn.id,
                    issue_type=issue["issue_type"],
                    severity=issue["severity"],
                    title=issue["title"],
                    description=issue["description"],
                    affected_objects=issue["affected_objects"],
                    recommendations=issue["recommendations"],
                    metrics=issue.get("metrics", {}),
                    detected_at=datetime.utcnow(),
                    resolved=False
                )
                db.add(query_issue)
                issues_stored += 1
            
            db.commit()
            
            logger.info(f"✅ Analysis complete for query {query_obj.id}: {detection_result['total_issues']} issues detected, {issues_stored} stored")
        
        except Exception as e:
            logger.error(f"Error analyzing query {query_obj.id}: {e}")
            db.rollback()
    
    def trigger_manual_run(self):
        """Manually trigger a monitoring cycle"""
        logger.info("Manual monitoring cycle triggered")
        self._monitor_databases()
