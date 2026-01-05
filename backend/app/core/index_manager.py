"""
Index Management Module
Analyzes database indexes and provides recommendations for optimization
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.database import Connection, IndexRecommendation
from app.core.db_manager import DatabaseManager


class IndexManager:
    """Manages database index analysis and recommendations"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    async def analyze_index_usage(
        self,
        connection_id: int,
        db_session: AsyncSession
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
            connection = await db_session.get(Connection, connection_id)
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            # Get database-specific index statistics
            if connection.db_type == "postgresql":
                stats = await self._analyze_postgresql_indexes(connection)
            elif connection.db_type == "mysql":
                stats = await self._analyze_mysql_indexes(connection)
            elif connection.db_type == "mssql":
                stats = await self._analyze_mssql_indexes(connection)
            else:
                raise ValueError(f"Unsupported database type: {connection.db_type}")
            
            logger.info(f"Index analysis complete for connection {connection_id}")
            return stats
            
        except Exception as e:
            logger.error(f"Error analyzing indexes: {e}")
            raise
    
    async def _analyze_postgresql_indexes(
        self,
        connection: Connection
    ) -> Dict[str, Any]:
        """Analyze PostgreSQL indexes"""
        try:
            conn = await self.db_manager.get_connection(connection.id)
            
            # Query for index usage statistics
            query = text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched,
                    pg_size_pretty(pg_relation_size(indexrelid)) as size,
                    pg_relation_size(indexrelid) as size_bytes
                FROM pg_stat_user_indexes
                ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC
            """)
            
            result = await conn.execute(query)
            indexes = []
            
            for row in result:
                indexes.append({
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "scans": row[3] or 0,
                    "tuples_read": row[4] or 0,
                    "tuples_fetched": row[5] or 0,
                    "size": row[6],
                    "size_bytes": row[7]
                })
            
            # Calculate statistics
            total_indexes = len(indexes)
            unused_indexes = [idx for idx in indexes if idx["scans"] == 0]
            rarely_used = [idx for idx in indexes if 0 < idx["scans"] < 10]
            total_size = sum(idx["size_bytes"] for idx in indexes)
            
            await conn.close()
            
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
    
    async def _analyze_mysql_indexes(
        self,
        connection: Connection
    ) -> Dict[str, Any]:
        """Analyze MySQL indexes"""
        try:
            conn = await self.db_manager.get_connection(connection.id)
            
            # Query for index statistics
            query = text("""
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
            """)
            
            result = await conn.execute(query)
            indexes = []
            
            for row in result:
                indexes.append({
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "cardinality": row[3] or 0,
                    "type": row[4]
                })
            
            total_indexes = len(indexes)
            
            await conn.close()
            
            return {
                "total_indexes": total_indexes,
                "indexes": indexes,
                "note": "MySQL index usage statistics require performance_schema"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing MySQL indexes: {e}")
            raise
    
    async def _analyze_mssql_indexes(
        self,
        connection: Connection
    ) -> Dict[str, Any]:
        """Analyze MSSQL indexes"""
        try:
            conn = await self.db_manager.get_connection(connection.id)
            
            # Query for index usage statistics
            query = text("""
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
            """)
            
            result = await conn.execute(query)
            indexes = []
            
            for row in result:
                total_reads = row[4] + row[5] + row[6]
                indexes.append({
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "type": row[3],
                    "seeks": row[4],
                    "scans": row[5],
                    "lookups": row[6],
                    "updates": row[7],
                    "total_reads": total_reads
                })
            
            total_indexes = len(indexes)
            unused_indexes = [idx for idx in indexes if idx["total_reads"] == 0]
            
            await conn.close()
            
            return {
                "total_indexes": total_indexes,
                "unused_count": len(unused_indexes),
                "indexes": indexes,
                "unused_indexes": unused_indexes
            }
            
        except Exception as e:
            logger.error(f"Error analyzing MSSQL indexes: {e}")
            raise
    
    async def identify_unused_indexes(
        self,
        connection_id: int,
        db_session: AsyncSession,
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
            stats = await self.analyze_index_usage(connection_id, db_session)
            
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
    
    async def detect_missing_indexes(
        self,
        connection_id: int,
        db_session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Detect missing indexes based on query patterns
        
        Analyzes slow queries and table scans to recommend new indexes
        """
        try:
            connection = await db_session.get(Connection, connection_id)
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            if connection.db_type == "postgresql":
                return await self._detect_missing_postgresql_indexes(connection)
            elif connection.db_type == "mssql":
                return await self._detect_missing_mssql_indexes(connection)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error detecting missing indexes: {e}")
            raise
    
    async def _detect_missing_postgresql_indexes(
        self,
        connection: Connection
    ) -> List[Dict[str, Any]]:
        """Detect missing indexes in PostgreSQL"""
        try:
            conn = await self.db_manager.get_connection(connection.id)
            
            # Query for tables with sequential scans
            query = text("""
                SELECT
                    schemaname,
                    tablename,
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
            """)
            
            result = await conn.execute(query)
            missing = []
            
            for row in result:
                missing.append({
                    "schema": row[0],
                    "table": row[1],
                    "seq_scans": row[2],
                    "rows_read": row[3],
                    "index_scans": row[4] or 0,
                    "live_tuples": row[5],
                    "recommendation": "Consider adding index",
                    "reason": f"High sequential scans ({row[2]}) with {row[3]} rows read"
                })
            
            await conn.close()
            return missing
            
        except Exception as e:
            logger.error(f"Error detecting missing PostgreSQL indexes: {e}")
            return []
    
    async def _detect_missing_mssql_indexes(
        self,
        connection: Connection
    ) -> List[Dict[str, Any]]:
        """Detect missing indexes in MSSQL"""
        try:
            conn = await self.db_manager.get_connection(connection.id)
            
            # Query for missing index recommendations
            query = text("""
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
            """)
            
            result = await conn.execute(query)
            missing = []
            
            for row in result:
                columns = []
                if row[2]:  # equality_columns
                    columns.extend(row[2].split(', '))
                if row[3]:  # inequality_columns
                    columns.extend(row[3].split(', '))
                
                missing.append({
                    "schema": row[0],
                    "table": row[1],
                    "columns": columns,
                    "included_columns": row[4].split(', ') if row[4] else [],
                    "avg_cost": float(row[5]),
                    "avg_impact": float(row[6]),
                    "seeks_scans": int(row[7]),
                    "recommendation": "Create index",
                    "reason": f"High impact ({row[6]:.1f}%) with {row[7]} seeks/scans"
                })
            
            await conn.close()
            return missing
            
        except Exception as e:
            logger.error(f"Error detecting missing MSSQL indexes: {e}")
            return []
    
    async def recommend_composite_indexes(
        self,
        connection_id: int,
        db_session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Recommend composite indexes based on query patterns
        
        Analyzes queries to find columns frequently used together
        """
        # This would require query log analysis
        # For now, return empty list - can be enhanced later
        return []
    
    async def calculate_index_benefit(
        self,
        connection_id: int,
        table_name: str,
        columns: List[str],
        db_session: AsyncSession
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
