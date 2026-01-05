"""
Index Management API Endpoints
Provides endpoints for analyzing, creating, and managing database indexes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from loguru import logger
from datetime import datetime

from app.models.database import get_db, Connection, IndexRecommendation
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

router = APIRouter()


@router.get("/recommendations/{connection_id}", response_model=List[IndexRecommendationResponse])
async def get_index_recommendations(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
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
        connection = await db.get(Connection, connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        # Get stored recommendations
        result = await db.execute(
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
async def get_unused_indexes(
    connection_id: int,
    usage_threshold: int = 10,
    db: AsyncSession = Depends(get_db)
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
        connection = await db.get(Connection, connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        # Analyze unused indexes
        manager = IndexManager()
        unused = await manager.identify_unused_indexes(connection_id, db, usage_threshold)
        
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
async def get_missing_indexes(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get missing index suggestions based on query patterns
    
    Analyzes slow queries and table scans to recommend new indexes
    """
    try:
        # Verify connection exists
        connection = await db.get(Connection, connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        # Detect missing indexes
        manager = IndexManager()
        missing = await manager.detect_missing_indexes(connection_id, db)
        
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
async def get_index_statistics(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
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
        connection = await db.get(Connection, connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        # Analyze index usage
        manager = IndexManager()
        stats = await manager.analyze_index_usage(connection_id, db)
        
        logger.info(f"Retrieved index statistics for connection {connection_id}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting index statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_index(
    request: IndexCreateRequest,
    db: AsyncSession = Depends(get_db)
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
        connection = await db.get(Connection, request.connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {request.connection_id} not found")
        
        # Build CREATE INDEX statement
        db_manager = DatabaseManager()
        conn = await db_manager.get_connection(request.connection_id)
        
        # Format column list
        columns_str = ", ".join(request.columns)
        
        # Build schema prefix if provided
        schema_prefix = f"{request.schema_name}." if request.schema_name else ""
        
        # Build CREATE INDEX SQL based on database type
        if connection.engine == "postgresql":
            unique_str = "UNIQUE " if request.unique else ""
            sql = f"CREATE {unique_str}INDEX {request.index_name} ON {schema_prefix}{request.table_name} USING {request.index_type} ({columns_str})"
        elif connection.engine == "mysql":
            unique_str = "UNIQUE " if request.unique else ""
            sql = f"CREATE {unique_str}INDEX {request.index_name} ON {schema_prefix}{request.table_name} ({columns_str})"
        elif connection.engine == "mssql":
            unique_str = "UNIQUE " if request.unique else ""
            sql = f"CREATE {unique_str}INDEX {request.index_name} ON {schema_prefix}{request.table_name} ({columns_str})"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported database type: {connection.engine}")
        
        # Execute CREATE INDEX
        from sqlalchemy import text
        await conn.execute(text(sql))
        await conn.commit()
        await conn.close()
        
        # Store recommendation record
        recommendation = IndexRecommendation(
            connection_id=request.connection_id,
            table_name=request.table_name,
            index_name=request.index_name,
            columns=request.columns,
            index_type=request.index_type,
            recommendation_type="create",
            status="created",
            reason=f"Index created via API",
            schema_name=request.schema_name,
            applied_at=datetime.utcnow()
        )
        db.add(recommendation)
        await db.commit()
        
        logger.info(f"Created index {request.index_name} on {request.table_name} for connection {request.connection_id}")
        
        return {
            "success": True,
            "message": f"Index {request.index_name} created successfully",
            "index_name": request.index_name,
            "table_name": request.table_name,
            "columns": request.columns,
            "sql": sql
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drop")
async def drop_index(
    request: IndexDropRequest,
    db: AsyncSession = Depends(get_db)
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
        connection = await db.get(Connection, request.connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {request.connection_id} not found")
        
        # Build DROP INDEX statement
        db_manager = DatabaseManager()
        conn = await db_manager.get_connection(request.connection_id)
        
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
        from sqlalchemy import text
        await conn.execute(text(sql))
        await conn.commit()
        await conn.close()
        
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
        await db.commit()
        
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
async def get_index_history(
    connection_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
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
        connection = await db.get(Connection, connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        # Get index change history
        result = await db.execute(
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
    db: AsyncSession = Depends(get_db)
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
        connection = await db.get(Connection, connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail=f"Connection {connection_id} not found")
        
        # Perform comprehensive analysis
        manager = IndexManager()
        
        # Get all analysis data
        usage_stats = await manager.analyze_index_usage(connection_id, db)
        unused = await manager.identify_unused_indexes(connection_id, db)
        missing = await manager.detect_missing_indexes(connection_id, db)
        
        results = {
            "usage_statistics": usage_stats,
            "unused_indexes": unused,
            "missing_indexes": missing,
            "summary": {
                "total_indexes": usage_stats.get("total_indexes", 0),
                "unused_count": len(unused),
                "missing_count": len(missing),
                "total_size": usage_stats.get("total_size", "0 B")
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
