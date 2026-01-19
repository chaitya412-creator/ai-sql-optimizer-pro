"""
Index Management Module
Analyzes database indexes and provides recommendations for optimization
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from loguru import logger

from app.models.database import Connection, IndexRecommendation
from app.core.db_manager import DatabaseManager
from app.core.security import SecurityManager


class IndexManager:
    """Manages database index analysis and recommendations"""
    
    def __init__(self):
        self.security_manager = SecurityManager()
    
    def analyze_index_usage(
        self,
        connection_id: int,
        db_session: Session
    ) -> Dict[str, Any]:
        """
        Analyze index usage statistics for a connection
        
        Returns comprehensive index usage data including:
        - Total indexes
        - Unused indexes
        - Index sizes
        - Usage statistics
        """
        try:
            # Get connection details
            connection = db_session.query(Connection).filter(Connection.id == connection_id).first()
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            # Get database-specific index statistics
            if connection.engine == "postgresql":
                stats = self._analyze_postgresql_indexes(connection)
            elif connection.engine == "mysql":
                stats = self._analyze_mysql_indexes(connection)
            elif connection.engine == "mssql":
                stats = self._analyze_mssql_indexes(connection)
            else:
                raise ValueError(f"Unsupported database type: {connection.engine}")
            
            logger.info(f"Index analysis complete for connection {connection_id}")
            return stats
            
        except Exception as e:
            logger.error(f"Error analyzing indexes: {e}")
            raise
    
    def _analyze_postgresql_indexes(
        self,
        connection: Connection
    ) -> Dict[str, Any]:
        """Analyze PostgreSQL indexes"""
        try:
            # Decrypt password
            password = self.security_manager.decrypt(connection.password_encrypted)
            
            # Initialize database manager
            db_manager = DatabaseManager(
                engine=connection.engine,
                host=connection.host,
                port=connection.port,
                database=connection.database,
                username=connection.username,
                password=password,
                ssl_enabled=connection.ssl_enabled
            )
            
            success, msg = db_manager.connect()
            if not success:
               raise Exception(f"Failed to connect to database: {msg}")

            # Query for index usage statistics
            query = """
                SELECT
                    schemaname,
                    relname AS tablename,
                    indexrelname AS indexname,
                    idx_scan as scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched,
                    pg_size_pretty(pg_relation_size(indexrelid)) as size,
                    pg_relation_size(indexrelid) as size_bytes
                FROM pg_stat_user_indexes
                ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC
            """
            
            result = db_manager.execute_query(query)
            indexes = []
            
            for row in result:
                indexes.append({
                    "schema": row["schemaname"],
                    "table": row["tablename"],
                    "index": row["indexname"],
                    "scans": row["scans"] or 0,
                    "tuples_read": row["tuples_read"] or 0,
                    "tuples_fetched": row["tuples_fetched"] or 0,
                    "size": row["size"],
                    "size_bytes": row["size_bytes"]
                })
            
            db_manager.disconnect()

            # Calculate statistics
            total_indexes = len(indexes)
            unused_indexes = [idx for idx in indexes if idx["scans"] == 0]
            rarely_used = [idx for idx in indexes if 0 < idx["scans"] < 10]
            total_size = sum(idx["size_bytes"] for idx in indexes)
            
            
            return {
                "total_indexes": total_indexes,
                "unused_count": len(unused_indexes),
                "rarely_used_count": len(rarely_used),
                "total_size_bytes": total_size,
                "total_size": self._format_bytes(total_size),
                "indexes": indexes,
                "unused_indexes": unused_indexes,
                "rarely_used_indexes": rarely_used
            }
            
        except Exception as e:
            logger.error(f"Error analyzing PostgreSQL indexes: {e}")
            raise
    
    def _analyze_mysql_indexes(
        self,
        connection: Connection
    ) -> Dict[str, Any]:
        """Analyze MySQL indexes"""
        try:
            # Decrypt password
            password = self.security_manager.decrypt(connection.password_encrypted)
            
            db_manager = DatabaseManager(
                engine=connection.engine,
                host=connection.host,
                port=connection.port,
                database=connection.database,
                username=connection.username,
                password=password,
                ssl_enabled=connection.ssl_enabled
            )
            success, msg = db_manager.connect()
            if not success:
               raise Exception(f"Failed to connect to database: {msg}")

            # Query for index statistics
            query = """
                SELECT
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    INDEX_NAME,
                    CARDINALITY,
                    INDEX_TYPE
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
                GROUP BY TABLE_SCHEMA, TABLE_NAME, INDEX_NAME
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
            
            result = db_manager.execute_query(query)
            indexes = []
            
            for row in result:
                indexes.append({
                    "schema": row["TABLE_SCHEMA"],
                    "table": row["TABLE_NAME"],
                    "index": row["INDEX_NAME"],
                    "cardinality": row["CARDINALITY"] or 0,
                    "type": row["INDEX_TYPE"]
                })
            
            total_indexes = len(indexes)
            
            db_manager.disconnect()
            
            return {
                "total_indexes": total_indexes,
                "indexes": indexes,
                "note": "MySQL index usage statistics require performance_schema"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing MySQL indexes: {e}")
            raise
    
    def _analyze_mssql_indexes(
        self,
        connection: Connection
    ) -> Dict[str, Any]:
        """Analyze MSSQL indexes"""
        try:
            # Decrypt password
            password = self.security_manager.decrypt(connection.password_encrypted)

            db_manager = DatabaseManager(
                engine=connection.engine,
                host=connection.host,
                port=connection.port,
                database=connection.database,
                username=connection.username,
                password=password,
                ssl_enabled=connection.ssl_enabled
            )
            success, msg = db_manager.connect()
            if not success:
               raise Exception(f"Failed to connect to database: {msg}")
               
            # Query for index usage statistics
            query = """
                SELECT
                    OBJECT_SCHEMA_NAME(i.object_id) AS schema_name,
                    OBJECT_NAME(i.object_id) AS table_name,
                    i.name AS index_name,
                    i.type_desc AS index_type,
                    ISNULL(s.user_seeks, 0) AS user_seeks,
                    ISNULL(s.user_scans, 0) AS user_scans,
                    ISNULL(s.user_lookups, 0) AS user_lookups,
                    ISNULL(s.user_updates, 0) AS user_updates
                FROM sys.indexes i
                LEFT JOIN sys.dm_db_index_usage_stats s
                    ON i.object_id = s.object_id AND i.index_id = s.index_id
                WHERE i.object_id > 100
                    AND i.type_desc != 'HEAP'
                ORDER BY (ISNULL(s.user_seeks, 0) + ISNULL(s.user_scans, 0) + ISNULL(s.user_lookups, 0)) ASC
            """
            
            result = db_manager.execute_query(query)
            indexes = []
            
            for row in result:
                total_reads = row["user_seeks"] + row["user_scans"] + row["user_lookups"]
                indexes.append({
                    "schema": row["schema_name"],
                    "table": row["table_name"],
                    "index": row["index_name"],
                    "type": row["index_type"],
                    "seeks": row["user_seeks"],
                    "scans": row["user_scans"],
                    "lookups": row["user_lookups"],
                    "updates": row["user_updates"],
                    "total_reads": total_reads
                })
            
            total_indexes = len(indexes)
            unused_indexes = [idx for idx in indexes if idx["total_reads"] == 0]
            
            db_manager.disconnect()
            
            return {
                "total_indexes": total_indexes,
                "unused_count": len(unused_indexes),
                "indexes": indexes,
                "unused_indexes": unused_indexes
            }
            
        except Exception as e:
            logger.error(f"Error analyzing MSSQL indexes: {e}")
            raise
    
    def identify_unused_indexes(
        self,
        connection_id: int,
        db_session: Session,
        usage_threshold: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Identify indexes that are unused or rarely used
        
        Args:
            connection_id: Database connection ID
            db_session: Database session
            usage_threshold: Minimum scans to consider index as used
        
        Returns:
            List of unused/rarely used indexes
        """
        try:
            stats = self.analyze_index_usage(connection_id, db_session)
            
            unused = []
            for idx in stats.get("indexes", []):
                scans = idx.get("scans", idx.get("total_reads", 0))
                if scans < usage_threshold:
                    unused.append({
                        "schema": idx.get("schema"),
                        "table": idx.get("table"),
                        "index": idx.get("index"),
                        "scans": scans,
                        "size": idx.get("size", "Unknown"),
                        "recommendation": "Consider dropping this index",
                        "reason": f"Only {scans} scans recorded"
                    })
            
            return unused
            
        except Exception as e:
            logger.error(f"Error identifying unused indexes: {e}")
            raise
    
    def detect_missing_indexes(
        self,
        connection_id: int,
        db_session: Session
    ) -> List[Dict[str, Any]]:
        """
        Detect missing indexes based on query patterns
        
        Analyzes slow queries and table scans to recommend new indexes
        """
        try:
            connection = db_session.query(Connection).filter(Connection.id == connection_id).first()
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            if connection.engine == "postgresql":
                return self._detect_missing_postgresql_indexes(connection)
            elif connection.engine == "mssql":
                return self._detect_missing_mssql_indexes(connection)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error detecting missing indexes: {e}")
            raise
    
    def _detect_missing_postgresql_indexes(
        self,
        connection: Connection
    ) -> List[Dict[str, Any]]:
        """Detect missing indexes in PostgreSQL"""
        try:
            # Decrypt password
            password = self.security_manager.decrypt(connection.password_encrypted)

            db_manager = DatabaseManager(
                engine=connection.engine,
                host=connection.host,
                port=connection.port,
                database=connection.database,
                username=connection.username,
                password=password,
                ssl_enabled=connection.ssl_enabled
            )
            success, msg = db_manager.connect()
            if not success:
               logger.error(f"Failed to connect to database: {msg}")
               return []
            
            # Query for tables with sequential scans
            query = """
                SELECT
                    schemaname,
                    relname AS tablename,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    n_live_tup
                FROM pg_stat_user_tables
                WHERE seq_scan > 1000
                    AND seq_tup_read > 100000
                    AND (idx_scan IS NULL OR idx_scan < seq_scan)
                ORDER BY seq_tup_read DESC
                LIMIT 20
            """
            
            result = db_manager.execute_query(query)
            missing = []
            
            for row in result:
                missing.append({
                    "schema": row["schemaname"],
                    "table": row["tablename"],
                    "seq_scans": row["seq_scan"],
                    "rows_read": row["seq_tup_read"],
                    "index_scans": row["idx_scan"] or 0,
                    "live_tuples": row["n_live_tup"],
                    "recommendation": "Consider adding index",
                    "reason": f"High sequential scans ({row['seq_scan']}) with {row['seq_tup_read']} rows read"
                })
            
            db_manager.disconnect()
            return missing
            
        except Exception as e:
            logger.error(f"Error detecting missing PostgreSQL indexes: {e}")
            return []
    
    def _detect_missing_mssql_indexes(
        self,
        connection: Connection
    ) -> List[Dict[str, Any]]:
        """Detect missing indexes in MSSQL"""
        try:
            # Decrypt password
            password = self.security_manager.decrypt(connection.password_encrypted)

            db_manager = DatabaseManager(
                engine=connection.engine,
                host=connection.host,
                port=connection.port,
                database=connection.database,
                username=connection.username,
                password=password,
                ssl_enabled=connection.ssl_enabled
            )
            success, msg = db_manager.connect()
            if not success:
               logger.error(f"Failed to connect to database: {msg}")
               return []
               
            # Query for missing index recommendations
            query = """
                SELECT TOP 20
                    OBJECT_SCHEMA_NAME(d.object_id) AS schema_name,
                    OBJECT_NAME(d.object_id) AS table_name,
                    d.equality_columns,
                    d.inequality_columns,
                    d.included_columns,
                    s.avg_total_user_cost,
                    s.avg_user_impact,
                    s.user_seeks + s.user_scans AS total_seeks_scans
                FROM sys.dm_db_missing_index_details d
                INNER JOIN sys.dm_db_missing_index_groups g
                    ON d.index_handle = g.index_handle
                INNER JOIN sys.dm_db_missing_index_group_stats s
                    ON g.index_group_handle = s.group_handle
                WHERE d.database_id = DB_ID()
                ORDER BY s.avg_total_user_cost * s.avg_user_impact * (s.user_seeks + s.user_scans) DESC
            """
            
            result = db_manager.execute_query(query)
            missing = []
            
            for row in result:
                columns = []
                if row["equality_columns"]:  # equality_columns
                    columns.extend(row["equality_columns"].split(', '))
                if row["inequality_columns"]:  # inequality_columns
                    columns.extend(row["inequality_columns"].split(', '))
                
                missing.append({
                    "schema": row["schema_name"],
                    "table": row["table_name"],
                    "columns": columns,
                    "included_columns": row["included_columns"].split(', ') if row["included_columns"] else [],
                    "avg_cost": float(row["avg_total_user_cost"]),
                    "avg_impact": float(row["avg_user_impact"]),
                    "seeks_scans": int(row["total_seeks_scans"]),
                    "recommendation": "Create index",
                    "reason": f"High impact ({row['avg_user_impact']:.1f}%) with {row['total_seeks_scans']} seeks/scans"
                })
            
            db_manager.disconnect()
            return missing
            
        except Exception as e:
            logger.error(f"Error detecting missing MSSQL indexes: {e}")
            return []
    
    def recommend_composite_indexes(
        self,
        connection_id: int,
        db_session: Session
    ) -> List[Dict[str, Any]]:
        """
        Recommend composite indexes based on query patterns
        
        Analyzes queries to find columns frequently used together
        """
        # This would require query log analysis
        # For now, return empty list - can be enhanced later
        return []
    
    def calculate_index_benefit(
        self,
        connection_id: int,
        table_name: str,
        columns: List[str],
        db_session: Session
    ) -> Dict[str, Any]:
        """
        Calculate estimated benefit of creating an index
        
        Returns cost/benefit analysis
        """
        try:
            # Simplified benefit calculation
            # In production, this would analyze query patterns and table statistics
            
            estimated_benefit = 0.0
            estimated_cost = 0.0
            
            # Placeholder logic - would be enhanced with actual analysis
            num_columns = len(columns)
            estimated_benefit = min(50.0 * num_columns, 80.0)  # Up to 80% improvement
            estimated_cost = 10.0 * num_columns  # Storage/maintenance cost

            
            return {
                "table": table_name,
                "columns": columns,
                "estimated_benefit_pct": estimated_benefit,
                "estimated_cost_score": estimated_cost,
                "recommendation": "beneficial" if estimated_benefit > estimated_cost else "not_recommended"
            }
            
        except Exception as e:
            logger.error(f"Error calculating index benefit: {e}")
            raise
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
