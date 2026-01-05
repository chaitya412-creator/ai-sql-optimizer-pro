"""
Multi-Database Connection Manager
Supports PostgreSQL, MySQL, Oracle, and SQL Server
"""
import psycopg2
import pymysql
import pyodbc
from typing import Dict, Any, Optional, List, Tuple
from loguru import logger
import time


class DatabaseManager:
    """Manages connections to multiple database types"""
    
    def __init__(self, engine: str, host: str, port: int, database: str, 
                 username: str, password: str, ssl_enabled: bool = False):
        self.engine = engine.lower()
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.ssl_enabled = ssl_enabled
        self.connection = None
    
    def connect(self) -> Tuple[bool, str]:
        """
        Establish database connection
        Returns: (success: bool, message: str)
        """
        try:
            start_time = time.time()
            
            if self.engine == "postgresql":
                self.connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.username,
                    password=self.password,
                    sslmode="require" if self.ssl_enabled else "prefer",
                    connect_timeout=10
                )
            
            elif self.engine == "mysql":
                self.connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.username,
                    password=self.password,
                    ssl={"ssl": True} if self.ssl_enabled else None,
                    connect_timeout=10
                )
            
            elif self.engine == "mssql":
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={self.host},{self.port};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                )
                if self.ssl_enabled:
                    conn_str += "Encrypt=yes;TrustServerCertificate=no;"
                
                self.connection = pyodbc.connect(conn_str, timeout=10)
            
            elif self.engine == "oracle":
                try:
                    import oracledb
                    dsn = f"{self.host}:{self.port}/{self.database}"
                    self.connection = oracledb.connect(
                        user=self.username,
                        password=self.password,
                        dsn=dsn
                    )
                except ImportError:
                    return False, "oracledb library not installed"
            
            else:
                return False, f"Unsupported database engine: {self.engine}"
            
            latency = (time.time() - start_time) * 1000
            logger.info(f"Connected to {self.engine} database in {latency:.2f}ms")
            return True, f"Connected successfully (latency: {latency:.2f}ms)"
        
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False, str(e)
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
                logger.info(f"Disconnected from {self.engine} database")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return results as list of dicts
        """
        if not self.connection:
            raise Exception("Not connected to database")
        
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            return results
        
        finally:
            cursor.close()
    
    def get_execution_plan(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get execution plan for a query
        Returns the plan in a normalized format
        """
        try:
            if self.engine == "postgresql":
                plan_query = f"EXPLAIN (ANALYZE, FORMAT JSON) {query}"
                result = self.execute_query(plan_query)
                if result and len(result) > 0:
                    return result[0].get("QUERY PLAN", {})
            
            elif self.engine == "mysql":
                plan_query = f"EXPLAIN FORMAT=JSON {query}"
                result = self.execute_query(plan_query)
                if result and len(result) > 0:
                    import json
                    return json.loads(result[0].get("EXPLAIN", "{}"))
            
            elif self.engine == "mssql":
                # Enable execution plan
                self.execute_query("SET SHOWPLAN_XML ON")
                result = self.execute_query(query)
                self.execute_query("SET SHOWPLAN_XML OFF")
                return {"plan": result}
            
            elif self.engine == "oracle":
                # Use EXPLAIN PLAN
                self.execute_query(f"EXPLAIN PLAN FOR {query}")
                result = self.execute_query(
                    "SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY())"
                )
                return {"plan": result}
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get execution plan: {e}")
            return None
    
    def get_schema_ddl(self, table_names: List[str]) -> str:
        """
        Get DDL (CREATE TABLE statements) for specified tables
        """
        ddl_statements = []
        
        try:
            for table in table_names:
                if self.engine == "postgresql":
                    query = f"""
                    SELECT 
                        'CREATE TABLE ' || table_name || ' (' ||
                        string_agg(
                            column_name || ' ' || data_type ||
                            CASE WHEN character_maximum_length IS NOT NULL 
                                THEN '(' || character_maximum_length || ')' 
                                ELSE '' END,
                            ', '
                        ) || ');' as ddl
                    FROM information_schema.columns
                    WHERE table_name = %s
                    GROUP BY table_name;
                    """
                    result = self.execute_query(query, (table,))
                    if result:
                        ddl_statements.append(result[0]["ddl"])
                
                elif self.engine == "mysql":
                    query = f"SHOW CREATE TABLE {table}"
                    result = self.execute_query(query)
                    if result:
                        ddl_statements.append(result[0]["Create Table"])
                
                elif self.engine == "mssql":
                    query = f"""
                    SELECT 
                        'CREATE TABLE ' + TABLE_NAME + ' (' +
                        STUFF((
                            SELECT ', ' + COLUMN_NAME + ' ' + DATA_TYPE +
                            CASE WHEN CHARACTER_MAXIMUM_LENGTH IS NOT NULL 
                                THEN '(' + CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR) + ')' 
                                ELSE '' END
                            FROM INFORMATION_SCHEMA.COLUMNS
                            WHERE TABLE_NAME = '{table}'
                            FOR XML PATH('')
                        ), 1, 2, '') + ');' as ddl
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_NAME = '{table}'
                    """
                    result = self.execute_query(query)
                    if result:
                        ddl_statements.append(result[0]["ddl"])
        
        except Exception as e:
            logger.error(f"Failed to get schema DDL: {e}")
        
        return "\n\n".join(ddl_statements)

    def get_table_stats(self, table_names: List[str]) -> Dict[str, Any]:
        """
        Retrieve basic table statistics for given tables
        Returns a mapping of table_name -> stats dict
        """
        stats = {}
        if not table_names:
            return stats
            
        try:
            if self.engine == "postgresql":
                # Use pg_stat_user_tables for last_analyze / scans / tuple counts
                placeholders = ','.join(['%s'] * len(table_names))
                query = f"""
                SELECT relname as table_name,
                       last_analyze,
                       last_vacuum,
                       n_live_tup,
                       seq_scan,
                       idx_scan
                FROM pg_stat_user_tables
                WHERE relname IN ({placeholders});
                """
                results = self.execute_query(query, tuple(table_names))
                for row in results:
                    stats[row['table_name']] = {
                        'last_analyze': row.get('last_analyze'),
                        'last_vacuum': row.get('last_vacuum'),
                        'n_live_tup': row.get('n_live_tup'),
                        'seq_scan': row.get('seq_scan'),
                        'idx_scan': row.get('idx_scan')
                    }
            
            elif self.engine == "mysql":
                # Use information_schema and performance_schema for MySQL
                placeholders = ','.join(['%s'] * len(table_names))
                query = f"""
                SELECT 
                    t.TABLE_NAME as table_name,
                    t.UPDATE_TIME as last_analyze,
                    t.TABLE_ROWS as n_live_tup,
                    s.COUNT_STAR as seq_scan,
                    (SELECT SUM(COUNT_STAR) FROM performance_schema.table_io_waits_summary_by_index_usage 
                     WHERE TABLE_NAME = t.TABLE_NAME AND INDEX_NAME IS NOT NULL) as idx_scan
                FROM information_schema.tables t
                LEFT JOIN performance_schema.table_io_waits_summary_by_index_usage s 
                    ON t.TABLE_NAME = s.TABLE_NAME AND s.INDEX_NAME IS NULL
                WHERE t.TABLE_SCHEMA = DATABASE()
                AND t.TABLE_NAME IN ({placeholders});
                """
                results = self.execute_query(query, tuple(table_names))
                for row in results:
                    stats[row['table_name']] = {
                        'last_analyze': row.get('last_analyze'),
                        'n_live_tup': row.get('n_live_tup'),
                        'seq_scan': row.get('seq_scan'),
                        'idx_scan': row.get('idx_scan')
                    }
            
            elif self.engine == "mssql":
                # Use sys.dm_db_index_usage_stats and sys.partitions for MS SQL
                table_list = "','".join(table_names)
                query = f"""
                SELECT 
                    t.name AS table_name,
                    STATS_DATE(t.object_id, s.stats_id) AS last_analyze,
                    p.rows AS n_live_tup,
                    ius.user_scans AS seq_scan,
                    ius.user_seeks + ius.user_lookups AS idx_scan
                FROM sys.tables t
                LEFT JOIN sys.stats s ON t.object_id = s.object_id
                LEFT JOIN (
                    SELECT object_id, SUM(rows) as rows 
                    FROM sys.partitions 
                    WHERE index_id IN (0,1) 
                    GROUP BY object_id
                ) p ON t.object_id = p.object_id
                LEFT JOIN sys.dm_db_index_usage_stats ius ON t.object_id = ius.object_id 
                    AND ius.database_id = DB_ID()
                WHERE t.name IN ('{table_list}');
                """
                results = self.execute_query(query)
                for row in results:
                    stats[row['table_name']] = {
                        'last_analyze': row.get('last_analyze'),
                        'n_live_tup': row.get('n_live_tup'),
                        'seq_scan': row.get('seq_scan'),
                        'idx_scan': row.get('idx_scan')
                    }
            
            else:
                # Fallback: return empty stats
                logger.debug("get_table_stats: table stats not implemented for engine: %s", self.engine)
        except Exception as e:
            logger.error(f"Failed to get table stats: {e}")
        return stats
    
    def get_slow_queries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get slow queries from database performance views
        """
        try:
            if self.engine == "postgresql":
                query = """
                SELECT 
                    queryid,
                    query as sql_text,
                    calls,
                    total_exec_time as total_time_ms,
                    mean_exec_time as avg_time_ms,
                    rows,
                    shared_blks_hit as buffer_hits,
                    shared_blks_read as buffer_reads
                FROM pg_stat_statements
                ORDER BY total_exec_time DESC
                LIMIT %s;
                """
                return self.execute_query(query, (limit,))
            
            elif self.engine == "mysql":
                query = """
                SELECT 
                    DIGEST as query_hash,
                    DIGEST_TEXT as sql_text,
                    COUNT_STAR as calls,
                    SUM_TIMER_WAIT / 1000000000 as total_time_ms,
                    AVG_TIMER_WAIT / 1000000000 as avg_time_ms,
                    SUM_ROWS_SENT as rows_returned
                FROM performance_schema.events_statements_summary_by_digest
                ORDER BY SUM_TIMER_WAIT DESC
                LIMIT %s;
                """
                return self.execute_query(query, (limit,))
            
            elif self.engine == "mssql":
                query = f"""
                SELECT TOP {limit}
                    qs.query_hash,
                    st.text as sql_text,
                    qs.execution_count as calls,
                    qs.total_elapsed_time / 1000.0 as total_time_ms,
                    qs.total_elapsed_time / qs.execution_count / 1000.0 as avg_time_ms,
                    qs.total_rows as rows_returned
                FROM sys.dm_exec_query_stats qs
                CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
                ORDER BY qs.total_elapsed_time DESC;
                """
                return self.execute_query(query)
            
            elif self.engine == "oracle":
                query = f"""
                SELECT * FROM (
                    SELECT 
                        sql_id as query_hash,
                        sql_text,
                        executions as calls,
                        elapsed_time / 1000 as total_time_ms,
                        elapsed_time / executions / 1000 as avg_time_ms,
                        rows_processed as rows_returned
                    FROM v$sql
                    WHERE executions > 0
                    ORDER BY elapsed_time DESC
                )
                WHERE ROWNUM <= {limit}
                """
                return self.execute_query(query)
            
            return []
        
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []
