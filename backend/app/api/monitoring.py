"""
Monitoring Agent API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models.database import get_db, Query, Connection
from app.models.schemas import QueryResponse, MonitoringStatus
from loguru import logger
from app.config import settings

router = APIRouter()

# This will be injected from main.py
monitoring_agent = None


def set_monitoring_agent(agent):
    """Set the monitoring agent instance"""
    global monitoring_agent
    monitoring_agent = agent


@router.get("/status", response_model=MonitoringStatus)
async def get_monitoring_status(db: Session = Depends(get_db)):
    """Get monitoring agent status"""
    try:
        if not monitoring_agent:
            return MonitoringStatus(
                is_running=False,
                last_poll_time=None,
                next_poll_time=None,
                interval_minutes=0,
                queries_discovered=0,
                active_connections=0
            )
        
        status_data = monitoring_agent.get_status()
        
        # Get actual total queries discovered from database
        total_queries = db.query(Query).count()
        status_data["queries_discovered"] = total_queries
        
        return status_data
    
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/start")
async def start_monitoring():
    """Start the monitoring agent"""
    try:
        if not monitoring_agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monitoring agent is not initialized"
            )
        
        if monitoring_agent.is_running():
            return {
                "message": "Monitoring agent is already running"
            }
        
        # Start monitoring agent
        monitoring_agent.start()
        logger.info("Monitoring agent started via API")
        
        return {
            "message": "Monitoring agent started successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/stop")
async def stop_monitoring():
    """Stop the monitoring agent"""
    try:
        if not monitoring_agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monitoring agent is not initialized"
            )
        
        if not monitoring_agent.is_running():
            return {
                "message": "Monitoring agent is not running"
            }
        
        # Stop monitoring agent
        monitoring_agent.stop()
        logger.info("Monitoring agent stopped via API")
        
        return {
            "message": "Monitoring agent stopped successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/trigger")
async def trigger_monitoring():
    """Manually trigger a monitoring cycle"""
    try:
        if not monitoring_agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monitoring agent is not initialized"
            )
        
        if not monitoring_agent.is_running():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monitoring agent is not running"
            )
        
        # Trigger manual run
        monitoring_agent.trigger_manual_run()
        
        return {
            "success": True,
            "message": "Monitoring cycle triggered successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/queries", response_model=List[QueryResponse])
async def get_discovered_queries(
    connection_id: int = None,
    limit: int = 100,
    optimized: bool = None,
    db: Session = Depends(get_db)
):
    """Get discovered queries from monitoring"""
    try:
        logger.info(f"Fetching discovered queries - connection_id: {connection_id}, limit: {limit}, optimized: {optimized}")
        
        # Validate database session
        if db is None:
            logger.error("Database session is None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database session not available"
            )
        
        # Build query
        query = db.query(Query)
        
        # Filter by connection if specified
        if connection_id:
            logger.debug(f"Filtering by connection_id: {connection_id}")
            query = query.filter(Query.connection_id == connection_id)
        
        # Filter by optimization status if specified
        if optimized is not None:
            logger.debug(f"Filtering by optimized: {optimized}")
            query = query.filter(Query.optimized == optimized)
        
        # Order by total execution time (worst first)
        query = query.order_by(Query.total_exec_time_ms.desc())
        
        # Limit results
        query = query.limit(limit)
        
        # Execute query
        queries = query.all()
        logger.info(f"Successfully fetched {len(queries)} queries")
        
        # Convert to response models using from_orm
        return [QueryResponse.from_orm(q) for q in queries]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting discovered queries: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch queries: {str(e)}"
        )


@router.get("/queries/{query_id}", response_model=QueryResponse)
async def get_query_details(query_id: int, db: Session = Depends(get_db)):
    """Get details of a specific discovered query"""
    try:
        query = db.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with id {query_id} not found"
            )
        # Convert to response model using from_orm
        return QueryResponse.from_orm(query)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting query details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/issues")
async def get_monitoring_issues(
    connection_id: int = None,
    severity: str = None,
    issue_type: str = None,
    resolved: bool = False,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get detected performance issues from monitoring"""
    try:
        from app.models.database import QueryIssue
        
        logger.info(f"Fetching monitoring issues - connection_id: {connection_id}, severity: {severity}, issue_type: {issue_type}")
        
        # Build query
        query = db.query(QueryIssue)
        
        # Filter by connection if specified
        if connection_id:
            query = query.filter(QueryIssue.connection_id == connection_id)
        
        # Filter by severity if specified
        if severity:
            query = query.filter(QueryIssue.severity == severity)
        
        # Filter by issue type if specified
        if issue_type:
            query = query.filter(QueryIssue.issue_type == issue_type)
        
        # Filter by resolved status
        query = query.filter(QueryIssue.resolved == resolved)
        
        # Order by severity (critical first) and detected time
        severity_order = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3
        }
        
        # Get all issues
        issues = query.order_by(QueryIssue.detected_at.desc()).limit(limit).all()
        
        # Sort by severity
        issues_sorted = sorted(issues, key=lambda x: (severity_order.get(x.severity, 4), -x.detected_at.timestamp()))
        
        logger.info(f"Successfully fetched {len(issues_sorted)} issues")
        
        # Convert to dict format
        result = []
        for issue in issues_sorted:
            result.append({
                "id": issue.id,
                "query_id": issue.query_id,
                "connection_id": issue.connection_id,
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "title": issue.title,
                "description": issue.description,
                "affected_objects": issue.affected_objects,
                "recommendations": issue.recommendations,
                "metrics": issue.metrics,
                "detected_at": issue.detected_at.isoformat(),
                "resolved": issue.resolved
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting monitoring issues: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch issues: {str(e)}"
        )


@router.post("/issues/{issue_id}/generate-corrected-code")
async def generate_corrected_code_for_issue(
    issue_id: int,
    db: Session = Depends(get_db)
):
    """Generate corrected SQL code for a specific issue using olmo-3:latest"""
    try:
        from app.models.database import QueryIssue
        from app.core.ollama_client import OllamaClient
        
        logger.info(f"Generating corrected code for issue {issue_id}")
        
        # Get the issue
        issue = db.query(QueryIssue).filter(QueryIssue.id == issue_id).first()
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with id {issue_id} not found"
            )
        
        # Get the related query
        query = db.query(Query).filter(Query.id == issue.query_id).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with id {issue.query_id} not found"
            )
        
        # Get the connection to determine database type
        connection = db.query(Connection).filter(Connection.id == issue.connection_id).first()
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection with id {issue.connection_id} not found"
            )
        
        # Prepare issue details
        issue_details = {
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            "title": issue.title,
            "description": issue.description,
            "affected_objects": issue.affected_objects,
            "metrics": issue.metrics
        }
        
        # Initialize Ollama client
        ollama_client = OllamaClient()

        # Check Ollama health and model availability
        code_gen_model = settings.OLLAMA_CODE_GENERATION_MODEL
        health_status = await ollama_client.check_health(model_name=code_gen_model)
        
        if not health_status.get("model_available"):
            logger.error(f"Ollama code generation model '{code_gen_model}' is not available. Status: {health_status}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"The code generation model '{code_gen_model}' is not available in the Ollama service. Please ensure the model is pulled and running."
            )
        
        # Generate corrected code
        result = await ollama_client.generate_corrected_code(
            original_sql=query.sql_text,
            issue_details=issue_details,
            recommendations=issue.recommendations,
            database_type=connection.engine,
            schema_ddl=None  # Could be enhanced to fetch schema
        )
        
        if not result.get("success"):
            logger.error(f"Failed to generate corrected code: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate corrected code: {result.get('error', 'Unknown error')}"
            )
        
        logger.info(f"Successfully generated corrected code for issue {issue_id}")

        return {
            "success": True,
            "issue_id": issue_id,
            "original_sql": query.sql_text,
            "corrected_sql": result["corrected_sql"],
            "explanation": result["explanation"],
            "changes_made": result["changes_made"],
            "used_model": result.get("used_model"),
            "tried_models": result.get("tried_models"),
            "issue_details": {
                "type": issue.issue_type,
                "severity": issue.severity,
                "title": issue.title,
                "recommendations": issue.recommendations
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating corrected code for issue {issue_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate corrected code: {str(e)}"
        )


@router.post("/queries/{query_id}/generate-optimized-query")
async def generate_optimized_query_for_discovered_query(
    query_id: int,
    db: Session = Depends(get_db)
):
    """Generate optimized SQL query using sqlcoder:latest for a discovered query"""
    try:
        from app.core.ollama_client import OllamaClient
        
        logger.info(f"Generating optimized query for query {query_id} using sqlcoder:latest")
        
        # Get the query
        query = db.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with id {query_id} not found"
            )
        
        # Get the connection to determine database type
        connection = db.query(Connection).filter(Connection.id == query.connection_id).first()
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection with id {query.connection_id} not found"
            )
        
        # Initialize Ollama client
        ollama_client = OllamaClient()
        
        # Generate optimized query using sqlcoder:latest
        # Note: We don't have execution plan or schema DDL here, but sqlcoder can still optimize
        result = await ollama_client.optimize_query(
            sql_query=query.sql_text,
            schema_ddl="",  # Could be enhanced to fetch schema
            execution_plan=None,
            database_type=connection.engine,
            detected_issues=None
        )
        
        if not result.get("success"):
            logger.error(f"Failed to generate optimized query: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate optimized query: {result.get('error', 'Unknown error')}"
            )
        
        logger.info(f"Successfully generated optimized query for query {query_id}")
        
        return {
            "success": True,
            "query_id": query_id,
            "original_sql": query.sql_text,
            "optimized_sql": result["optimized_sql"],
            "explanation": result["explanation"],
            "recommendations": result["recommendations"],
            "estimated_improvement": result.get("estimated_improvement"),
            "query_metrics": {
                "avg_execution_time": query.avg_exec_time_ms,
                "total_execution_time": query.total_exec_time_ms,
                "calls": query.calls,
                "rows_returned": query.rows_returned
            },
            "connection": {
                "name": connection.name,
                "engine": connection.engine
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating optimized query for query {query_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate optimized query: {str(e)}"
        )


@router.get("/issues/summary")
async def get_issues_summary(
    connection_id: int = None,
    db: Session = Depends(get_db)
):
    """Get summary of detected issues"""
    try:
        from app.models.database import QueryIssue
        from sqlalchemy import func
        
        logger.info(f"Fetching issues summary - connection_id: {connection_id}")
        
        # Build base query
        query = db.query(QueryIssue).filter(QueryIssue.resolved == False)
        
        if connection_id:
            query = query.filter(QueryIssue.connection_id == connection_id)
        
        # Get all unresolved issues
        issues = query.all()
        
        # Count by severity
        critical_count = sum(1 for i in issues if i.severity == 'critical')
        high_count = sum(1 for i in issues if i.severity == 'high')
        medium_count = sum(1 for i in issues if i.severity == 'medium')
        low_count = sum(1 for i in issues if i.severity == 'low')
        
        # Count by type
        issue_types = {}
        for issue in issues:
            issue_type = issue.issue_type
            if issue_type not in issue_types:
                issue_types[issue_type] = {
                    "issue_type": issue_type,
                    "count": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            issue_types[issue_type]["count"] += 1
            issue_types[issue_type][issue.severity] += 1
        
        # Get recent critical issues
        recent_critical = query.filter(
            QueryIssue.severity == 'critical'
        ).order_by(QueryIssue.detected_at.desc()).limit(5).all()
        
        recent_critical_list = []
        for issue in recent_critical:
            # Get query info
            query_obj = db.query(Query).filter(Query.id == issue.query_id).first()
            connection = db.query(Connection).filter(Connection.id == issue.connection_id).first()
            
            recent_critical_list.append({
                "issue_id": issue.id,
                "query_id": issue.query_id,
                "connection_name": connection.name if connection else "Unknown",
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "title": issue.title,
                "description": issue.description,
                "detected_at": issue.detected_at.isoformat(),
                "sql_preview": query_obj.sql_text[:100] + "..." if query_obj and len(query_obj.sql_text) > 100 else query_obj.sql_text if query_obj else ""
            })
        
        summary = {
            "total_issues": len(issues),
            "critical_issues": critical_count,
            "high_issues": high_count,
            "medium_issues": medium_count,
            "low_issues": low_count,
            "issues_by_type": list(issue_types.values()),
            "recent_critical_issues": recent_critical_list,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Issues summary: {len(issues)} total issues")
        return summary
    
    except Exception as e:
        logger.error(f"Error getting issues summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch issues summary: {str(e)}"
        )
