"""
Index Management API Endpoints
Provides endpoints for analyzing, creating, and managing database indexes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, text
from typing import List, Optional, Tuple
from loguru import logger
from datetime import datetime
import re

from app.models.database import get_db, Connection, IndexRecommendation, Query
from app.models.schemas import (
    IndexRecommendationResponse,
    IndexStatistics,
    IndexCreateRequest,
    IndexDropRequest,
    IndexAnalysisResponse,
    IndexHistoryResponse
)
from app.core.index_manager import IndexManager
from app.core.db_manager import DatabaseManager
from app.core.security import SecurityManager
from app.core.plan_analyzer import PlanAnalyzer
from app.core.ollama_client import OllamaClient

router = APIRouter()
security_manager = SecurityManager()


_SYSTEM_SCHEMAS = {"pg_catalog", "information_schema", "pg_toast"}


def _is_system_table_ref(table_ref: str) -> bool:
    if not table_ref:
        return True
    t = table_ref.strip().strip('"').lower()
    if any(t.startswith(f"{schema}.") for schema in _SYSTEM_SCHEMAS):
        return True
    # If we only have the bare table name, skip obvious pg_* system objects
    if t.startswith("pg_"):
        return True
    return False


def _strip_identifier_quotes(identifier: str) -> str:
    return identifier.strip().strip('"').strip("'")


def _normalize_schema_table(schema_name: Optional[str], table_name: str) -> Tuple[Optional[str], str]:
    """Normalize schema/table input.

    - If `table_name` is qualified (schema.table), split it.
    - If both schema_name and qualified table_name disagree, raise.
    """
    if not table_name:
        return schema_name, table_name

    raw_table = _strip_identifier_quotes(table_name)
    raw_schema = _strip_identifier_quotes(schema_name) if schema_name else None

    if '.' not in raw_table:
        return raw_schema, raw_table

    inferred_schema, inferred_table = raw_table.split('.', 1)
    inferred_schema = _strip_identifier_quotes(inferred_schema)
    inferred_table = _strip_identifier_quotes(inferred_table)

    if raw_schema and raw_schema.lower() != inferred_schema.lower():
        raise HTTPException(
            status_code=400,
            detail=(
                f"Conflicting schema provided. schema_name='{raw_schema}' but table_name='{raw_table}'. "
                "Provide either an unqualified table_name with schema_name, or a qualified table_name."
            ),
        )

    return inferred_schema, inferred_table


def _resolve_table_ref(
    db_manager: DatabaseManager,
    engine: str,
    schema_name: Optional[str],
    table_name: str,
) -> Tuple[Optional[str], str]:
    """Resolve a table reference.

    Ensures the table exists. If schema is omitted, attempts to infer it.
    Returns (schema_name, table_name).
    """
    schema_name, table_name = _normalize_schema_table(schema_name, table_name)

    if not table_name:
        raise HTTPException(status_code=400, detail="table_name is required")

    engine = (engine or "").lower()

    if engine == "postgresql":
        if schema_name:
            rows = db_manager.execute_query(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
                LIMIT 1
                """,
                (schema_name, table_name),
            )
            if rows:
                return schema_name, table_name

            raise HTTPException(
                status_code=400,
                detail=f"Table '{schema_name}.{table_name}' does not exist in the target database",
            )

        rows = db_manager.execute_query(
            """
            SELECT table_schema
            FROM information_schema.tables
            WHERE table_name = %s
              AND table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            """,
            (table_name,),
        )
        schemas = sorted({r.get("table_schema") for r in rows if r.get("table_schema")})
        if len(schemas) == 1:
            return schemas[0], table_name
        if len(schemas) > 1:
            raise HTTPException(
                status_code=400,
                detail=f"Table '{table_name}' exists in multiple schemas: {schemas}. Please specify schema_name.",
            )
        raise HTTPException(status_code=400, detail=f"Table '{table_name}' does not exist in the target database")

    if engine == "mysql":
        schema_to_check = schema_name or db_manager.database
        rows = db_manager.execute_query(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            LIMIT 1
            """,
            (schema_to_check, table_name),
        )
        if rows:
            return schema_to_check, table_name
        raise HTTPException(status_code=400, detail=f"Table '{schema_to_check}.{table_name}' does not exist in the target database")

    if engine == "mssql":
        schema_to_check = schema_name or "dbo"
        # pyodbc uses ? params, but DatabaseManager.execute_query passes params through; keep it simple and inline.
        rows = db_manager.execute_query(
            """
            SELECT 1
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            """,
            (schema_to_check, table_name),
        )
        if rows:
            return schema_to_check, table_name
        raise HTTPException(status_code=400, detail=f"Table '{schema_to_check}.{table_name}' does not exist in the target database")

    # For other engines, just return normalized input.
    return schema_name, table_name


def _index_exists(
    db_manager: DatabaseManager,
    engine: str,
    index_name: str,
    schema_name: Optional[str] = None,
    table_name: Optional[str] = None,
) -> bool:
    """Check whether an index already exists in the target DB."""
    if not index_name:
        return False

    engine = (engine or "").lower()
    index_name = _strip_identifier_quotes(index_name)

    try:
        if engine == "postgresql":
            schema_to_check = schema_name or "public"
            rows = db_manager.execute_query(
                """
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = %s AND indexname = %s
                LIMIT 1
                """,
                (schema_to_check, index_name),
            )
            return bool(rows)

        if engine == "mysql":
            schema_to_check = schema_name or db_manager.database
            # MySQL's "schema" is the database name.
            rows = db_manager.execute_query(
                """
                SELECT 1
                FROM information_schema.statistics
                WHERE table_schema = %s AND index_name = %s
                LIMIT 1
                """,
                (schema_to_check, index_name),
            )
            return bool(rows)

        if engine == "mssql":
            schema_to_check = schema_name or "dbo"
            if not table_name:
                # Without the table, index lookup is ambiguous in MSSQL.
                return False
            rows = db_manager.execute_query(
                """
                SELECT 1
                FROM sys.indexes i
                INNER JOIN sys.objects o ON o.object_id = i.object_id
                INNER JOIN sys.schemas s ON s.schema_id = o.schema_id
                WHERE s.name = ? AND o.name = ? AND i.name = ?
                """,
                (schema_to_check, table_name, index_name),
            )
            return bool(rows)
    except Exception:
        # If the existence check fails, fall back to attempting creation.
        return False

    return False


def _mark_create_recommendation_applied(
    db: Session,
    connection_id: int,
    table_name: str,
    index_name: str,
    schema_name: Optional[str],
    columns: List[str],
    index_type: str,
    status: str = "created",
):
    """Update an existing recommended record if present; otherwise insert a new applied record."""
    existing = (
        db.query(IndexRecommendation)
        .filter(
            IndexRecommendation.connection_id == connection_id,
            IndexRecommendation.recommendation_type == "create",
            IndexRecommendation.table_name == table_name,
            IndexRecommendation.index_name == index_name,
            IndexRecommendation.status == "recommended",
        )
        .order_by(IndexRecommendation.created_at.desc())
        .first()
    )

    if existing:
        existing.status = status
        existing.applied_at = datetime.utcnow()
        if schema_name:
            existing.schema_name = schema_name
        if columns is not None:
            existing.columns = columns
        if index_type is not None:
            existing.index_type = index_type
        existing.reason = existing.reason or "Index created via API"
        db.commit()
        return existing

    recommendation = IndexRecommendation(
        connection_id=connection_id,
        table_name=table_name,
        index_name=index_name,
        columns=columns or [],
        index_type=index_type or "",
        recommendation_type="create",
        status=status,
        reason="Index created via API",
        schema_name=schema_name,
        applied_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(recommendation)
    db.commit()
    return recommendation


def _parse_create_index_sql(sql: str) -> dict | None:
    """Parse a CREATE INDEX statement into components used by IndexRecommendation."""
    if not sql:
        return None

    normalized = re.sub(r"\s+", " ", sql.strip(), flags=re.MULTILINE)
    normalized = normalized.rstrip(';')

    # Handles common Postgres/MySQL/MSSQL forms:
    # CREATE [UNIQUE] INDEX [IF NOT EXISTS] idx ON [schema.]table [USING btree] (col1, col2)
    pattern = re.compile(
        r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<index>[^\s]+)\s+ON\s+(?:ONLY\s+)?(?P<table>[^\s(]+)\s*(?:USING\s+(?P<using>\w+)\s*)?\((?P<cols>[^\)]+)\)",
        re.IGNORECASE,
    )
    match = pattern.search(normalized)
    if not match:
        return None

    raw_index_name = _strip_identifier_quotes(match.group('index'))
    raw_table = _strip_identifier_quotes(match.group('table'))
    using = match.group('using')
    cols = match.group('cols')

    schema_name = None
    table_name = raw_table
    if '.' in raw_table:
        schema_name, table_name = raw_table.split('.', 1)
        schema_name = _strip_identifier_quotes(schema_name)
        table_name = _strip_identifier_quotes(table_name)

    parsed_cols: List[str] = []
    for col_expr in cols.split(','):
        col_expr = col_expr.strip()
        if not col_expr:
            continue
        # For expressions like lower(email) or column ops like col DESC, take the first token
        token = col_expr
        if '(' not in col_expr:
            token = col_expr.split()[0]
        parsed_cols.append(_strip_identifier_quotes(token))

    return {
        "index_name": raw_index_name,
        "schema_name": schema_name,
        "table_name": table_name,
        "columns": parsed_cols,
        "index_type": (using or "btree").lower(),
    }


def _parse_drop_index_sql(sql: str) -> dict | None:
    """Parse a DROP INDEX statement.

    Supports:
    - Postgres: DROP INDEX [CONCURRENTLY] [IF EXISTS] [schema.]index_name
    - MySQL: DROP INDEX index_name ON [schema.]table_name
    """
    if not sql:
        return None

    normalized = re.sub(r"\s+", " ", sql.strip(), flags=re.MULTILINE)
    normalized = normalized.rstrip(';')

    # MySQL style: DROP INDEX idx_name ON schema.table
    mysql_pattern = re.compile(
        r"DROP\s+INDEX\s+(?P<index>[^\s]+)\s+ON\s+(?P<table>[^\s;]+)",
        re.IGNORECASE,
    )
    m = mysql_pattern.search(normalized)
    if m:
        raw_index_name = _strip_identifier_quotes(m.group('index'))
        raw_table = _strip_identifier_quotes(m.group('table'))

        schema_name = None
        table_name = raw_table
        if '.' in raw_table:
            schema_name, table_name = raw_table.split('.', 1)
            schema_name = _strip_identifier_quotes(schema_name)
            table_name = _strip_identifier_quotes(table_name)

        return {
            "index_name": raw_index_name,
            "schema_name": schema_name,
            "table_name": table_name,
        }

    # Postgres style: DROP INDEX [CONCURRENTLY] [IF EXISTS] schema.index
    pg_pattern = re.compile(
        r"DROP\s+INDEX\s+(?:CONCURRENTLY\s+)?(?:IF\s+EXISTS\s+)?(?P<index>[^\s;]+)",
        re.IGNORECASE,
    )
    m = pg_pattern.search(normalized)
    if not m:
        return None

    raw_index = _strip_identifier_quotes(m.group('index'))
    schema_name = None
    index_name = raw_index
    if '.' in raw_index:
        schema_name, index_name = raw_index.split('.', 1)
        schema_name = _strip_identifier_quotes(schema_name)
        index_name = _strip_identifier_quotes(index_name)

    return {
        "index_name": index_name,
        "schema_name": schema_name,
        "table_name": None,
    }


@router.get("/recommendations/{connection_id}", response_model=List[IndexRecommendationResponse])
def get_index_recommendations(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """
    Get index recommendations for a connection
    
    Analyzes the database and returns recommendations for:
    - New indexes to create
    - Unused indexes to drop
    - Index modifications
    """
    try:
        # Verify connection exists
        connection = db.query(Connection).filter(Connection.id == connection_id).first()
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        # Get stored recommendations
        result = db.execute(
            select(IndexRecommendation)
            .where(IndexRecommendation.connection_id == connection_id)
            .order_by(IndexRecommendation.created_at.desc())
        )
        recommendations = result.scalars().all()
        
        logger.info(f"Retrieved {len(recommendations)} index recommendations for connection {connection_id}")
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting index recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unused/{connection_id}")
def get_unused_indexes(
    connection_id: int,
    usage_threshold: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get unused or rarely used indexes
    
    Args:
        connection_id: Database connection ID
        usage_threshold: Minimum scans to consider index as used (default: 10)
    
    Returns:
        List of unused/rarely used indexes with recommendations
    """
    try:
        # Verify connection exists
        connection = db.query(Connection).filter(Connection.id == connection_id).first()
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        # Analyze unused indexes
        manager = IndexManager()
        unused = manager.identify_unused_indexes(connection_id, db, usage_threshold)
        
        logger.info(f"Found {len(unused)} unused indexes for connection {connection_id}")
        return {
            "connection_id": connection_id,
            "usage_threshold": usage_threshold,
            "unused_count": len(unused),
            "unused_indexes": unused
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unused indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/missing/{connection_id}")
def get_missing_indexes(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """
    Get missing index suggestions based on query patterns
    
    Analyzes slow queries and table scans to recommend new indexes
    """
    try:
        # Verify connection exists
        connection = db.get(Connection, connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        # Detect missing indexes
        manager = IndexManager()
        missing = manager.detect_missing_indexes(connection_id, db)
        
        logger.info(f"Found {len(missing)} missing index suggestions for connection {connection_id}")
        return {
            "connection_id": connection_id,
            "missing_count": len(missing),
            "missing_indexes": missing
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting missing indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/{connection_id}", response_model=IndexStatistics)
def get_index_statistics(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive index statistics for a connection
    
    Returns:
        - Total indexes
        - Unused index count
        - Total size
        - Detailed index information
    """
    try:
        # Verify connection exists
        connection = db.get(Connection, connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        # Analyze index usage
        manager = IndexManager()
        stats = manager.analyze_index_usage(connection_id, db)
        
        logger.info(f"Retrieved index statistics for connection {connection_id}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting index statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
def create_index(
    request: IndexCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new index on a table
    
    Args:
        request: Index creation request with table, columns, and options
    
    Returns:
        Success status and created index details
    """
    try:
        # Verify connection exists
        connection = db.get(Connection, request.connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {request.connection_id} not found")
        
        # Decrypt password
        password = security_manager.decrypt(connection.password_encrypted)

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
             raise HTTPException(status_code=500, detail=f"Database connection failed: {msg}")

        # Resolve schema/table and validate the relation exists before running DDL.
        resolved_schema, resolved_table = _resolve_table_ref(
            db_manager=db_manager,
            engine=connection.engine,
            schema_name=request.schema_name,
            table_name=request.table_name,
        )

        # Resolve schema/table and validate the relation exists before running DDL.
        resolved_schema, resolved_table = _resolve_table_ref(
            db_manager=db_manager,
            engine=connection.engine,
            schema_name=request.schema_name,
            table_name=request.table_name,
        )

        # Format column list
        columns_str = ", ".join(request.columns)
        
        # Build schema prefix if provided
        schema_prefix = f"{resolved_schema}." if resolved_schema else ""

        # If index already exists, treat as a successful apply and mark it created.
        already_exists = _index_exists(
            db_manager=db_manager,
            engine=connection.engine,
            index_name=request.index_name,
            schema_name=resolved_schema,
            table_name=resolved_table,
        )
        
        # Build CREATE INDEX SQL based on database type
        if connection.engine == "postgresql":
            unique_str = "UNIQUE " if request.unique else ""
            if_not_exists = "IF NOT EXISTS "
            sql = f"CREATE {unique_str}INDEX {if_not_exists}{request.index_name} ON {schema_prefix}{resolved_table} USING {request.index_type} ({columns_str})"
        elif connection.engine == "mysql":
            unique_str = "UNIQUE " if request.unique else ""
            sql = f"CREATE {unique_str}INDEX {request.index_name} ON {schema_prefix}{resolved_table} ({columns_str})"
        elif connection.engine == "mssql":
            unique_str = "UNIQUE " if request.unique else ""
            sql = f"CREATE {unique_str}INDEX {request.index_name} ON {schema_prefix}{resolved_table} ({columns_str})"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported database type: {connection.engine}")
        
        executed = False
        if not already_exists:
            # Execute CREATE INDEX (raw cursor for DDL)
            cursor = db_manager.connection.cursor()
            try:
                cursor.execute(sql)
                db_manager.connection.commit()
                executed = True
            except Exception as e:
                # Treat "already exists" as success (race/idempotency)
                msg = str(e)
                if "already exists" in msg.lower() or "duplicate" in msg.lower():
                    already_exists = True
                else:
                    db_manager.disconnect()
                    raise Exception(f"Failed to execute SQL: {e}")
            finally:
                cursor.close()
        db_manager.disconnect()

        # Update/insert recommendation record as applied
        _mark_create_recommendation_applied(
            db=db,
            connection_id=request.connection_id,
            table_name=resolved_table,
            index_name=request.index_name,
            schema_name=resolved_schema,
            columns=request.columns,
            index_type=request.index_type,
            status="created",
        )
        
        logger.info(
            f"Create index requested for {schema_prefix}{resolved_table}.{request.index_name} (executed={executed}, already_exists={already_exists})"
        )
        
        return {
            "success": True,
            "message": (
                f"Index {request.index_name} created successfully" if executed else f"Index {request.index_name} already exists"
            ),
            "index_name": request.index_name,
            "table_name": resolved_table,
            "schema_name": resolved_schema,
            "columns": request.columns,
            "sql": sql
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drop")
def drop_index(
    request: IndexDropRequest,
    db: Session = Depends(get_db)
):
    """
    Drop an existing index
    
    Args:
        request: Index drop request with table and index name
    
    Returns:
        Success status
    """
    try:
        # Verify connection exists
        connection = db.get(Connection, request.connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {request.connection_id} not found")
        
        # Decrypt password
        password = security_manager.decrypt(connection.password_encrypted)

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
             raise HTTPException(status_code=500, detail=f"Database connection failed: {msg}")

        # Build schema prefix if provided
        schema_prefix = f"{request.schema_name}." if request.schema_name else ""
        
        # Build DROP INDEX SQL based on database type
        if connection.engine == "postgresql":
            sql = f"DROP INDEX {schema_prefix}{request.index_name}"
        elif connection.engine == "mysql":
            sql = f"DROP INDEX {request.index_name} ON {schema_prefix}{request.table_name}"
        elif connection.engine == "mssql":
            sql = f"DROP INDEX {request.index_name} ON {schema_prefix}{request.table_name}"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported database type: {connection.engine}")
        
        # Execute DROP INDEX
        # Use raw cursor for DDL
        cursor = db_manager.connection.cursor()
        try:
            cursor.execute(sql)
            db_manager.connection.commit()
        except Exception as e:
            db_manager.disconnect()
            raise Exception(f"Failed to execute SQL: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()
        
        # Store recommendation record
        recommendation = IndexRecommendation(
            connection_id=request.connection_id,
            table_name=request.table_name,
            index_name=request.index_name,
            columns=[],
            index_type="",
            recommendation_type="drop",
            status="dropped",
            reason=f"Index dropped via API",
            schema_name=request.schema_name,
            applied_at=datetime.utcnow()
        )
        db.add(recommendation)
        db.commit()
        
        logger.info(f"Dropped index {request.index_name} from {request.table_name} for connection {request.connection_id}")
        
        return {
            "success": True,
            "message": f"Index {request.index_name} dropped successfully",
            "index_name": request.index_name,
            "table_name": request.table_name,
            "sql": sql
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dropping index: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{connection_id}", response_model=IndexHistoryResponse)
def get_index_history(
    connection_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get index change history for a connection
    
    Args:
        connection_id: Database connection ID
        limit: Maximum number of records to return (default: 50)
    
    Returns:
        List of index changes (creates, drops, modifications)
    """
    try:
        # Verify connection exists
        connection = db.get(Connection, connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        # Get index change history
        result = db.execute(
            select(IndexRecommendation)
            .where(
                and_(
                    IndexRecommendation.connection_id == connection_id,
                    IndexRecommendation.applied_at.isnot(None)
                )
            )
            .order_by(IndexRecommendation.applied_at.desc())
            .limit(limit)
        )
        changes = result.scalars().all()
        
        logger.info(f"Retrieved {len(changes)} index changes for connection {connection_id}")
        
        return {
            "connection_id": connection_id,
            "changes": changes,
            "total_changes": len(changes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting index history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=IndexAnalysisResponse)
async def analyze_index_usage(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """
    Perform comprehensive index analysis
    
    Analyzes:
    - Current index usage
    - Unused indexes
    - Missing indexes
    - Index statistics
    
    Returns:
        Complete analysis results
    """
    try:
        # Verify connection exists
        connection = db.get(Connection, connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        # Perform comprehensive analysis
        manager = IndexManager()
        
        # Get all analysis data
        usage_stats = manager.analyze_index_usage(connection_id, db)
        unused = manager.identify_unused_indexes(connection_id, db)
        missing = manager.detect_missing_indexes(connection_id, db)

        # Generate Ollama-based index recommendations from top slow queries (if available)
        llm_created = 0
        llm_attempted = False
        llm_skip_reason: str | None = None
        llm_response_preview: str | None = None
        try:
            top_queries = (
                db.query(Query)
                .filter(Query.connection_id == connection_id)
                .order_by(Query.avg_exec_time_ms.desc())
                .limit(3)
                .all()
            )

            if top_queries:
                llm_attempted = True

                # Decrypt password
                password = security_manager.decrypt(connection.password_encrypted)

                db_manager = DatabaseManager(
                    engine=connection.engine,
                    host=connection.host,
                    port=connection.port,
                    database=connection.database,
                    username=connection.username,
                    password=password,
                    ssl_enabled=connection.ssl_enabled,
                )

                success, msg = db_manager.connect()
                if success:
                    try:
                        # Cleanup/normalize stored recommendations so the UI doesn't offer
                        # actions that will inevitably fail (e.g., hallucinated tables).
                        try:
                            stale_recs = (
                                db.query(IndexRecommendation)
                                .filter(
                                    IndexRecommendation.connection_id == connection_id,
                                    IndexRecommendation.recommendation_type == "create",
                                    IndexRecommendation.status == "recommended",
                                )
                                .all()
                            )

                            deleted = 0
                            updated = 0
                            for rec in stale_recs:
                                try:
                                    resolved_schema, resolved_table = _resolve_table_ref(
                                        db_manager=db_manager,
                                        engine=connection.engine,
                                        schema_name=rec.schema_name,
                                        table_name=rec.table_name,
                                    )
                                except HTTPException:
                                    db.delete(rec)
                                    deleted += 1
                                    continue

                                if rec.table_name != resolved_table:
                                    rec.table_name = resolved_table
                                    updated += 1
                                if resolved_schema and (rec.schema_name or "").lower() != resolved_schema.lower():
                                    rec.schema_name = resolved_schema
                                    updated += 1

                            if deleted or updated:
                                db.commit()
                                logger.info(
                                    f"Index rec cleanup for connection {connection_id}: deleted={deleted}, updated={updated}"
                                )
                        except Exception as e:
                            logger.info(f"Index rec cleanup skipped: {e}")

                        aggregated_issues: List[dict] = []
                        table_names: set[str] = set()

                        for q in top_queries:
                            if not q.sql_text:
                                continue
                            extracted_tables = PlanAnalyzer.extract_table_names(q.sql_text)
                            extracted_tables = [t for t in extracted_tables if not _is_system_table_ref(t)]
                            table_names.update(extracted_tables)

                            # Always include a lightweight issue per slow query so the LLM
                            # has enough context to propose indexes even when plan analysis
                            # yields no structured issues.
                            if extracted_tables:
                                aggregated_issues.append(
                                    {
                                        "severity": "medium",
                                        "title": "Slow query candidate for indexing",
                                        "description": (
                                            f"Avg time: {q.avg_exec_time_ms}ms; calls: {q.calls}. "
                                            f"SQL: {q.sql_text}"
                                        ),
                                        "affected_objects": list(extracted_tables),
                                    }
                                )

                            execution_plan = None
                            try:
                                execution_plan = db_manager.get_execution_plan(q.sql_text)
                            except Exception:
                                execution_plan = None

                            query_stats = {
                                "buffer_hits": q.buffer_hits,
                                "buffer_reads": q.buffer_reads,
                                "avg_time_ms": q.avg_exec_time_ms,
                                "calls": q.calls,
                            }

                            table_stats = None
                            try:
                                if extracted_tables:
                                    table_stats = db_manager.get_table_stats(extracted_tables)
                            except Exception:
                                table_stats = None

                            detection = PlanAnalyzer.analyze_plan(
                                plan=execution_plan,
                                engine=connection.engine,
                                sql_query=q.sql_text,
                                query_stats=query_stats,
                                table_stats=table_stats,
                                query_context=None,
                            )

                            for issue in detection.get("issues", [])[:10]:
                                aggregated_issues.append(issue)

                        if not table_names:
                            llm_skip_reason = "no_tables_in_top_queries"
                        elif not aggregated_issues:
                            llm_skip_reason = "no_issues_or_queries_for_prompt"
                        else:
                            schema_ddl = db_manager.get_schema_ddl(list(table_names))
                            ollama_client = OllamaClient()
                            llm_result = await ollama_client.generate_fix_recommendations(
                                detected_issues=aggregated_issues,
                                schema_ddl=schema_ddl,
                                database_type=connection.engine,
                            )

                            if llm_result.get("raw_response"):
                                llm_response_preview = str(llm_result.get("raw_response"))[:400]

                            if llm_result.get("success") and llm_result.get("index_recommendations"):
                                index_catalog: dict[str, dict] = {}
                                try:
                                    for idx in (usage_stats.get("indexes") or []):
                                        idx_name = idx.get("index")
                                        if idx_name and idx_name not in index_catalog:
                                            index_catalog[idx_name] = idx
                                except Exception:
                                    index_catalog = {}

                                for fix in llm_result["index_recommendations"]:
                                    sql = (fix.get("sql") if isinstance(fix, dict) else str(fix)).strip()
                                    if not sql:
                                        continue

                                    sql_upper = sql.upper()
                                    if sql_upper.startswith("DROP INDEX"):
                                        parsed_drop = _parse_drop_index_sql(sql)
                                        if not parsed_drop or not parsed_drop.get("index_name"):
                                            continue

                                        # Best-effort resolve table/schema from catalog when not present
                                        table_name = parsed_drop.get("table_name")
                                        schema_name = parsed_drop.get("schema_name")
                                        catalog = index_catalog.get(parsed_drop["index_name"], {})
                                        if not table_name:
                                            table_name = catalog.get("table")
                                        if not schema_name:
                                            schema_name = catalog.get("schema")

                                        if schema_name and schema_name.lower() in _SYSTEM_SCHEMAS:
                                            continue

                                        if not table_name:
                                            continue

                                        existing = (
                                            db.query(IndexRecommendation)
                                            .filter(
                                                IndexRecommendation.connection_id == connection_id,
                                                IndexRecommendation.recommendation_type == "drop",
                                                IndexRecommendation.table_name == table_name,
                                                IndexRecommendation.index_name == parsed_drop["index_name"],
                                                IndexRecommendation.status.in_(["recommended", "dropped"]),
                                            )
                                            .first()
                                        )
                                        if existing:
                                            continue

                                        recommendation = IndexRecommendation(
                                            connection_id=connection_id,
                                            table_name=table_name,
                                            index_name=parsed_drop["index_name"],
                                            columns=[],
                                            index_type=(catalog.get("type") or "btree"),
                                            recommendation_type="drop",
                                            status="recommended",
                                            reason=(fix.get("description") if isinstance(fix, dict) else "Ollama index drop recommendation"),
                                            schema_name=schema_name,
                                            estimated_benefit=None,
                                            usage_count=0,
                                            scans=int(catalog.get("scans") or 0),
                                            size_bytes=catalog.get("size_bytes"),
                                            created_at=datetime.utcnow(),
                                        )
                                        db.add(recommendation)
                                        llm_created += 1
                                        continue

                                    parsed_create = _parse_create_index_sql(sql)
                                    if not parsed_create:
                                        continue

                                    if parsed_create.get("schema_name") and str(parsed_create["schema_name"]).lower() in _SYSTEM_SCHEMAS:
                                        continue
                                    if str(parsed_create.get("table_name") or "").lower().startswith("pg_"):
                                        continue

                                    # Ensure the referenced table exists; also infer schema if omitted.
                                    try:
                                        resolved_schema, resolved_table = _resolve_table_ref(
                                            db_manager=db_manager,
                                            engine=connection.engine,
                                            schema_name=parsed_create.get("schema_name"),
                                            table_name=parsed_create.get("table_name") or "",
                                        )
                                    except HTTPException as he:
                                        logger.info(
                                            f"Skipping LLM index recommendation for non-existent table: "
                                            f"{parsed_create.get('schema_name')}.{parsed_create.get('table_name')} ({he.detail})"
                                        )
                                        continue
                                    except Exception as e:
                                        logger.info(
                                            f"Skipping LLM index recommendation due to table resolution error: {e}"
                                        )
                                        continue

                                    # De-dupe by connection + index + table + type
                                    existing = (
                                        db.query(IndexRecommendation)
                                        .filter(
                                            IndexRecommendation.connection_id == connection_id,
                                            IndexRecommendation.recommendation_type == "create",
                                            IndexRecommendation.table_name == resolved_table,
                                            IndexRecommendation.index_name == parsed_create["index_name"],
                                            IndexRecommendation.status.in_(["recommended", "created"]),
                                        )
                                        .first()
                                    )
                                    if existing:
                                        continue

                                    # Parse CPU savings to a numeric % if present
                                    estimated_benefit = None
                                    if isinstance(fix, dict):
                                        cpu_savings = fix.get("estimated_cpu_savings")
                                        if isinstance(cpu_savings, str):
                                            m = re.search(r"(\d+(?:\.\d+)?)", cpu_savings)
                                            if m:
                                                estimated_benefit = float(m.group(1))

                                    recommendation = IndexRecommendation(
                                        connection_id=connection_id,
                                        table_name=resolved_table,
                                        index_name=parsed_create["index_name"],
                                        columns=parsed_create["columns"],
                                        index_type=parsed_create["index_type"],
                                        recommendation_type="create",
                                        status="recommended",
                                        reason=(fix.get("description") if isinstance(fix, dict) else "Ollama index recommendation"),
                                        schema_name=resolved_schema,
                                        estimated_benefit=estimated_benefit,
                                        usage_count=0,
                                        scans=0,
                                        created_at=datetime.utcnow(),
                                    )
                                    db.add(recommendation)
                                    llm_created += 1

                                if llm_created:
                                    db.commit()
                            else:
                                if not llm_result.get("success"):
                                    llm_skip_reason = f"ollama_error:{llm_result.get('error', 'unknown')}"
                                else:
                                    llm_skip_reason = "ollama_returned_no_index_recommendations"
                    finally:
                        db_manager.disconnect()
                else:
                    logger.warning(f"Skipping Ollama index recs; DB connect failed: {msg}")
                    llm_skip_reason = "target_db_connect_failed"
            else:
                llm_skip_reason = "no_queries_in_observability_store"
        except Exception as e:
            logger.warning(f"Ollama index recommendation generation skipped/failed: {e}")
            llm_skip_reason = f"error:{e}"
        
        results = {
            "usage_statistics": usage_stats,
            "unused_indexes": unused,
            "missing_indexes": missing,
            "summary": {
                "total_indexes": usage_stats.get("total_indexes", 0),
                "unused_count": len(unused),
                "missing_count": len(missing),
                "total_size": usage_stats.get("total_size", "0 B")
            },
            "ollama": {
                "attempted": llm_attempted,
                "index_recommendations_created": llm_created,
                "skip_reason": llm_skip_reason,
                "response_preview": llm_response_preview,
            }
        }
        
        logger.info(f"Completed comprehensive index analysis for connection {connection_id}")
        
        return {
            "connection_id": connection_id,
            "analysis_type": "comprehensive",
            "results": results,
            "analyzed_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
