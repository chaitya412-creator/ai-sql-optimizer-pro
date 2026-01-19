"""
SQL Optimizer API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.models.database import get_db, Connection, Query, Optimization, QueryIssue
from app.models import schemas
from app.models.schemas import (
    OptimizationRequest, OptimizationResponse,
    OptimizationApplyRequest, OptimizationApplyResponse,
    OptimizationValidateRequest, OptimizationValidateResponse,
    DetectionResult, QueryIssueResponse
)
from app.core.security import security_manager
from app.core.db_manager import DatabaseManager
from app.core.ollama_client import OllamaClient
from app.core.plan_analyzer import PlanAnalyzer, RecommendationRanker
from loguru import logger

router = APIRouter()


@router.post("/optimize", response_model=OptimizationResponse, status_code=status.HTTP_201_CREATED)
async def optimize_query(
    request: OptimizationRequest,
    db: Session = Depends(get_db)
):
    """
    Optimize a SQL query using AI with comprehensive issue detection
    This is the CORE optimization endpoint with enhanced detection
    """
    try:
        # Get connection details
        connection = db.query(Connection).filter(
            Connection.id == request.connection_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection with id {request.connection_id} not found"
            )
        
        # Decrypt password
        password = security_manager.decrypt(connection.password_encrypted)
        
        # Create database manager
        db_manager = DatabaseManager(
            engine=connection.engine,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password=password,
            ssl_enabled=connection.ssl_enabled
        )
        
        # Connect to database
        success, message = db_manager.connect()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to database: {message}"
            )
        
        try:
            # Step 1: Extract table names from query
            table_names = PlanAnalyzer.extract_table_names(request.sql_query)
            logger.info(f"Extracted tables: {table_names}")
            
            # Step 2: Get schema DDL for tables
            schema_ddl = db_manager.get_schema_ddl(table_names)
            logger.info(f"Retrieved schema DDL for {len(table_names)} tables")
            
            # Step 3: Get execution plan (if requested)
            execution_plan = None
            if request.include_execution_plan:
                execution_plan = db_manager.get_execution_plan(request.sql_query)
                logger.info(f"Retrieved execution plan")
            
            # Step 4: Perform comprehensive detection analysis
            query_stats = None
            if request.query_id:
                # Get query stats if available
                query_obj = db.query(Query).filter(Query.id == request.query_id).first()
                if query_obj:
                    query_stats = {
                        "buffer_hits": query_obj.buffer_hits,
                        "buffer_reads": query_obj.buffer_reads,
                        "avg_time_ms": query_obj.avg_exec_time_ms,
                        "calls": query_obj.calls
                    }

            # Fetch table stats (if possible) to enable stale-statistics and cardinality detectors
            table_stats = None
            try:
                table_names = PlanAnalyzer.extract_table_names(request.sql_query)
                if table_names:
                    table_stats = db_manager.get_table_stats(table_names)
                    logger.debug(f"Fetched table stats for tables: {list(table_stats.keys())}")
            except Exception as e:
                logger.error(f"Failed to fetch table stats: {e}")
                table_stats = None
            
            detection_result = PlanAnalyzer.analyze_plan(
                plan=execution_plan,
                engine=connection.engine,
                sql_query=request.sql_query,
                query_stats=query_stats,
                table_stats=table_stats,
                query_context=None  # TODO: Add context for ORM detection
            )
            
            # Rank issues by impact
            if detection_result.get("issues"):
                # Convert dict issues back to DetectionResult objects for ranking
                from app.core.plan_analyzer import DetectionResult as DR
                issue_objs = [DR(**issue) for issue in detection_result["issues"]]
                ranked_objs = RecommendationRanker.rank_issues(issue_objs)
                # Convert back to dicts
                detection_result["issues"] = [issue.to_dict() for issue in ranked_objs]
            
            logger.info(f"Detection complete: {detection_result['total_issues']} issues found")
            
            # Step 5: Call Ollama for optimization with detected issues
            ollama_client = OllamaClient()
            optimization_result = await ollama_client.optimize_query(
                sql_query=request.sql_query,
                schema_ddl=schema_ddl,
                execution_plan=execution_plan,
                database_type=connection.engine,
                detected_issues=detection_result  # Pass detected issues to Ollama
            )
            
            if not optimization_result.get("success"):
                error_detail = optimization_result.get('error', 'Unknown error')
                raw_response = optimization_result.get('raw_response', '')
                
                # Provide detailed error message
                if raw_response:
                    error_message = (
                        f"Optimization failed: {error_detail}\n\n"
                        f"LLM Response Preview:\n{raw_response[:500]}..."
                        if len(raw_response) > 500 else
                        f"Optimization failed: {error_detail}\n\nLLM Response:\n{raw_response}"
                    )
                else:
                    error_message = f"Optimization failed: {error_detail}"
                
                logger.error(f"Optimization failed - Error: {error_detail}, Response length: {len(raw_response)}")
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_message
                )
            
            # Step 6: Store optimization result with detected issues
            # Convert execution_plan to dict if it's a list
            plan_to_store = None
            if execution_plan:
                if isinstance(execution_plan, list) and len(execution_plan) > 0:
                    plan_to_store = execution_plan[0]  # Take first element if list
                elif isinstance(execution_plan, dict):
                    plan_to_store = execution_plan
            
            optimization = Optimization(
                query_id=request.query_id,
                connection_id=request.connection_id,
                original_sql=request.sql_query,
                optimized_sql=optimization_result["optimized_sql"],
                execution_plan=plan_to_store,
                explanation=optimization_result["explanation"],
                recommendations=optimization_result["recommendations"],
                status="pending",
                created_at=datetime.utcnow(),
                detected_issues=detection_result  # Store detection results
            )
            
            db.add(optimization)
            db.commit()
            db.refresh(optimization)
            
            # Step 7: Store individual issues in QueryIssue table
            for issue in detection_result.get("issues", []):
                query_issue = QueryIssue(
                    query_id=request.query_id,
                    optimization_id=optimization.id,
                    connection_id=request.connection_id,
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
            
            db.commit()
            
            # Update query as optimized if query_id provided
            if request.query_id:
                query = db.query(Query).filter(Query.id == request.query_id).first()
                if query:
                    query.optimized = True
                    db.commit()
            
            logger.info(f"Optimization created with id: {optimization.id}, {len(detection_result.get('issues', []))} issues stored")
            return optimization
        
        finally:
            db_manager.disconnect()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/analyze", response_model=DetectionResult)
async def analyze_query(
    request: OptimizationRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a SQL query for performance issues without optimization
    Returns comprehensive detection results
    """
    try:
        # Get connection details
        connection = db.query(Connection).filter(
            Connection.id == request.connection_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection with id {request.connection_id} not found"
            )
        
        # Decrypt password
        password = security_manager.decrypt(connection.password_encrypted)
        
        # Create database manager
        db_manager = DatabaseManager(
            engine=connection.engine,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password=password,
            ssl_enabled=connection.ssl_enabled
        )
        
        # Connect to database
        success, message = db_manager.connect()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to database: {message}"
            )
        
        try:
            # Get execution plan
            execution_plan = None
            if request.include_execution_plan:
                execution_plan = db_manager.get_execution_plan(request.sql_query)
            
            # Get query stats if available
            query_stats = None
            if request.query_id:
                query_obj = db.query(Query).filter(Query.id == request.query_id).first()
                if query_obj:
                    query_stats = {
                        "buffer_hits": query_obj.buffer_hits,
                        "buffer_reads": query_obj.buffer_reads,
                        "avg_time_ms": query_obj.avg_exec_time_ms,
                        "calls": query_obj.calls
                    }
            
            # Perform comprehensive detection
            detection_result = PlanAnalyzer.analyze_plan(
                plan=execution_plan,
                engine=connection.engine,
                sql_query=request.sql_query,
                query_stats=query_stats,
                table_stats=None,
                query_context=None
            )
            
            # Rank issues by impact
            if detection_result.get("issues"):
                from app.core.plan_analyzer import DetectionResult as DR
                issue_objs = [DR(**issue) for issue in detection_result["issues"]]
                ranked_objs = RecommendationRanker.rank_issues(issue_objs)
                detection_result["issues"] = [issue.to_dict() for issue in ranked_objs]
            
            logger.info(f"Analysis complete: {detection_result['total_issues']} issues detected")
            return DetectionResult(**detection_result)
        
        finally:
            db_manager.disconnect()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/optimizations", response_model=List[OptimizationResponse])
async def list_optimizations(
    connection_id: int = None,
    status_filter: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all optimizations"""
    try:
        query = db.query(Optimization)
        
        if connection_id:
            query = query.filter(Optimization.connection_id == connection_id)
        
        if status_filter:
            query = query.filter(Optimization.status == status_filter)
        
        query = query.order_by(Optimization.created_at.desc()).limit(limit)
        
        optimizations = query.all()
        return optimizations
    
    except Exception as e:
        logger.error(f"Error listing optimizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/optimizations/{optimization_id}", response_model=OptimizationResponse)
async def get_optimization(optimization_id: int, db: Session = Depends(get_db)):
    """Get a specific optimization"""
    try:
        optimization = db.query(Optimization).filter(
            Optimization.id == optimization_id
        ).first()
        
        if not optimization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization with id {optimization_id} not found"
            )
        
        return optimization
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/issues", response_model=List[QueryIssueResponse])
async def list_issues(
    connection_id: int = None,
    severity: str = None,
    resolved: bool = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List detected performance issues"""
    try:
        query = db.query(QueryIssue)
        
        if connection_id:
            query = query.filter(QueryIssue.connection_id == connection_id)
        
        if severity:
            query = query.filter(QueryIssue.severity == severity)
        
        if resolved is not None:
            query = query.filter(QueryIssue.resolved == resolved)
        
        query = query.order_by(QueryIssue.detected_at.desc()).limit(limit)
        
        issues = query.all()
        return issues
    
    except Exception as e:
        logger.error(f"Error listing issues: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/apply", response_model=OptimizationApplyResponse)
async def apply_optimization(
    request: OptimizationApplyRequest,
    db: Session = Depends(get_db)
):
    """
    Apply an optimization (execute the recommended SQL or mark as applied)
    """
    try:
        optimization = db.query(Optimization).filter(
            Optimization.id == request.optimization_id
        ).first()
        
        if not optimization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization with id {request.optimization_id} not found"
            )
        
        # Get connection details
        connection = db.query(Connection).filter(
            Connection.id == optimization.connection_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection with id {optimization.connection_id} not found"
            )
        
        # Decrypt password
        password = security_manager.decrypt(connection.password_encrypted)
        
        # Create database manager
        db_manager = DatabaseManager(
            engine=connection.engine,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password=password,
            ssl_enabled=connection.ssl_enabled
        )
        
        # Connect to database
        success, message = db_manager.connect()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to database: {message}"
            )
        
        try:
            # If SQL is provided, execute it
            if request.sql_to_execute:
                logger.info(f"Executing optimization SQL: {request.sql_to_execute}")
                # Basic safety check: only allow DDL and ANALYZE
                sql_upper = request.sql_to_execute.upper().strip()
                if not any(sql_upper.startswith(cmd) for cmd in ["CREATE", "DROP", "ALTER", "ANALYZE", "VACUUM", "SET"]):
                    if not request.skip_safety_checks:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Only DDL (CREATE, DROP, ALTER) and maintenance (ANALYZE, VACUUM, SET) commands are allowed for safety."
                        )
                
                # Execute the SQL
                db_manager.execute_query(request.sql_to_execute)
                message = "Optimization SQL executed successfully"
            else:
                message = "Optimization marked as applied"
            
            # Update status
            optimization.status = "applied"
            optimization.applied_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Applied optimization {request.optimization_id}")
            
            return OptimizationApplyResponse(
                success=True,
                message=message,
                optimization_id=request.optimization_id,
                applied_at=optimization.applied_at
            )
        
        finally:
            db_manager.disconnect()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/validate", response_model=OptimizationValidateResponse)
async def validate_optimization(
    request: OptimizationValidateRequest,
    db: Session = Depends(get_db)
):
    """
    Validate an optimization by comparing original vs optimized query performance
    """
    try:
        optimization = db.query(Optimization).filter(
            Optimization.id == request.optimization_id
        ).first()
        
        if not optimization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization with id {request.optimization_id} not found"
            )
        
        # Get connection details
        connection = db.query(Connection).filter(
            Connection.id == optimization.connection_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection with id {optimization.connection_id} not found"
            )
        
        # Decrypt password
        password = security_manager.decrypt(connection.password_encrypted)
        
        # Create database manager
        db_manager = DatabaseManager(
            engine=connection.engine,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password=password,
            ssl_enabled=connection.ssl_enabled
        )
        
        # Connect to database
        success, message = db_manager.connect()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to database: {message}"
            )
        
        try:
            import time
            
            # Measure original query
            start_time = time.time()
            db_manager.execute_query(optimization.original_sql)
            original_time = (time.time() - start_time) * 1000
            
            # Measure optimized query
            start_time = time.time()
            db_manager.execute_query(optimization.optimized_sql)
            optimized_time = (time.time() - start_time) * 1000
            
            # Calculate improvement
            improvement_pct = 0
            if original_time > 0:
                improvement_pct = ((original_time - optimized_time) / original_time) * 100
            
            # Update optimization record
            optimization.status = "validated"
            optimization.validated_at = datetime.utcnow()
            optimization.estimated_improvement_pct = improvement_pct
            db.commit()
            
            logger.info(f"Validated optimization {request.optimization_id}: {improvement_pct:.2f}% improvement")
            
            return OptimizationValidateResponse(
                success=True,
                message=f"Validation complete: {improvement_pct:.2f}% improvement",
                optimization_id=request.optimization_id,
                original_time_ms=original_time,
                optimized_time_ms=optimized_time,
                improvement_pct=improvement_pct,
                validated_at=optimization.validated_at
            )
            
        finally:
            db_manager.disconnect()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/optimizations/{optimization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_optimization(optimization_id: int, db: Session = Depends(get_db)):
    """Delete an optimization"""
    try:
        optimization = db.query(Optimization).filter(
            Optimization.id == optimization_id
        ).first()
        
        if not optimization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization with id {optimization_id} not found"
            )
        
        db.delete(optimization)
        db.commit()
        
        logger.info(f"Deleted optimization {optimization_id}")
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/explain-plan")
async def explain_execution_plan(
    request: schemas.ExplainPlanRequest,
    db: Session = Depends(get_db)
):
    """
    Get natural language explanation of execution plan
    """
    try:
        # Get connection
        connection = db.query(Connection).filter(
            Connection.id == request.connection_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection with id {request.connection_id} not found"
            )
        
        # Get execution plan if not provided
        execution_plan = request.execution_plan
        if not execution_plan:
            password = security_manager.decrypt(connection.password_encrypted)
            db_manager = DatabaseManager(
                engine=connection.engine,
                host=connection.host,
                port=connection.port,
                database=connection.database,
                username=connection.username,
                password=password,
                ssl_enabled=connection.ssl_enabled
            )
            
            success, message = db_manager.connect()
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to connect to database: {message}"
                )
            
            try:
                execution_plan = db_manager.get_execution_plan(request.sql_query)
            finally:
                db_manager.disconnect()
        
        if not execution_plan:
            return schemas.ExplainPlanResponse(
                success=False,
                explanation="Could not retrieve execution plan",
                summary="Execution plan not available",
                key_operations=[],
                bottlenecks=[]
            )
        
        # Call Ollama for natural language explanation
        ollama_client = OllamaClient()
        result = await ollama_client.explain_plan_natural_language(
            execution_plan=execution_plan,
            sql_query=request.sql_query,
            database_type=connection.engine
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to explain plan: {result.get('error')}"
            )
        
        # Extract key operations and bottlenecks from explanation
        explanation = result.get("explanation", "")
        key_operations = []
        bottlenecks = []
        
        # Simple parsing - could be enhanced
        if "sequential scan" in explanation.lower() or "seq scan" in explanation.lower():
            bottlenecks.append("Sequential scan detected - consider adding indexes")
        if "nested loop" in explanation.lower():
            key_operations.append("Nested Loop Join")
        if "hash join" in explanation.lower():
            key_operations.append("Hash Join")
        if "index scan" in explanation.lower():
            key_operations.append("Index Scan")
        
        return schemas.ExplainPlanResponse(
            success=True,
            explanation=explanation,
            summary=result.get("summary", ""),
            key_operations=key_operations,
            bottlenecks=bottlenecks,
            estimated_cost=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/generate-fixes")
async def generate_fix_recommendations(
    request: schemas.GenerateFixesRequest,
    db: Session = Depends(get_db)
):
    """
    Generate actionable fix recommendations for an optimization
    """
    try:
        # Get optimization
        optimization = db.query(Optimization).filter(
            Optimization.id == request.optimization_id
        ).first()
        
        if not optimization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization with id {request.optimization_id} not found"
            )
        
        # Get connection
        connection = db.query(Connection).filter(
            Connection.id == optimization.connection_id
        ).first()
        
        # Get detected issues
        detected_issues = optimization.detected_issues
        if not detected_issues or not detected_issues.get("issues"):
            return schemas.GenerateFixesResponse(
                success=True,
                optimization_id=request.optimization_id,
                index_recommendations=[],
                maintenance_tasks=[],
                query_rewrites=[],
                configuration_changes=[],
                total_fixes=0,
                high_impact_count=0
            )
        
        # Get schema DDL
        password = security_manager.decrypt(connection.password_encrypted)
        db_manager = DatabaseManager(
            engine=connection.engine,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password=password,
            ssl_enabled=connection.ssl_enabled
        )
        
        success, message = db_manager.connect()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to database: {message}"
            )
        
        try:
            table_names = PlanAnalyzer.extract_table_names(optimization.original_sql)
            schema_ddl = db_manager.get_schema_ddl(table_names)
        finally:
            db_manager.disconnect()
        
        # Call Ollama to generate fix recommendations
        ollama_client = OllamaClient()
        result = await ollama_client.generate_fix_recommendations(
            detected_issues=detected_issues.get("issues", []),
            schema_ddl=schema_ddl,
            database_type=connection.engine
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate fixes: {result.get('error')}"
            )
        
        # Parse recommendations into structured format
        from app.core.fix_applicator import FixRecommendationParser
        
        index_recs = []
        if request.include_indexes and result.get("index_recommendations"):
            for rec in result["index_recommendations"]:
                sql = rec.get("sql") if isinstance(rec, dict) else str(rec)
                if not sql:
                    continue
                index_recs.append(schemas.FixRecommendation(
                    fix_type=(rec.get("fix_type") if isinstance(rec, dict) else "index_creation") or "index_creation",
                    sql=sql,
                    description=(rec.get("description") if isinstance(rec, dict) else None) or "Index recommendation",
                    estimated_impact=(rec.get("estimated_impact") if isinstance(rec, dict) else None) or "high",
                    affected_objects=(rec.get("affected_objects") if isinstance(rec, dict) else None) or [],
                    safety_level=(rec.get("safety_level") if isinstance(rec, dict) else None) or "safe"
                ))
        
        maintenance_tasks = []
        if request.include_maintenance and result.get("maintenance_tasks"):
            for rec in result["maintenance_tasks"]:
                sql = rec.get("sql") if isinstance(rec, dict) else str(rec)
                if not sql:
                    continue
                task_type = (rec.get("fix_type") if isinstance(rec, dict) else None) or (
                    "statistics_update" if "ANALYZE" in sql.upper() else "vacuum"
                )
                maintenance_tasks.append(schemas.FixRecommendation(
                    fix_type=task_type,
                    sql=sql,
                    description=(rec.get("description") if isinstance(rec, dict) else None) or "Maintenance task",
                    estimated_impact=(rec.get("estimated_impact") if isinstance(rec, dict) else None) or "medium",
                    affected_objects=(rec.get("affected_objects") if isinstance(rec, dict) else None) or [],
                    safety_level=(rec.get("safety_level") if isinstance(rec, dict) else None) or "safe"
                ))
        
        query_rewrites = []
        if request.include_rewrites and result.get("query_rewrites"):
            for rec in result["query_rewrites"]:
                if isinstance(rec, dict):
                    sql = rec.get("sql") or ""
                    desc = rec.get("description") or "Query rewrite"
                    impact = rec.get("estimated_impact") or "medium"
                    affected = rec.get("affected_objects") or []
                    safety = rec.get("safety_level") or "safe"
                else:
                    sql = ""
                    desc = str(rec)
                    impact = "medium"
                    affected = []
                    safety = "safe"

                query_rewrites.append(schemas.FixRecommendation(
                    fix_type="query_rewrite",
                    sql=sql,
                    description=desc,
                    estimated_impact=impact,
                    affected_objects=affected,
                    safety_level=safety
                ))
        
        config_changes = []
        if request.include_config and result.get("configuration_changes"):
            for rec in result["configuration_changes"]:
                if isinstance(rec, dict):
                    sql = rec.get("sql") or ""
                    desc = rec.get("description") or "Configuration change"
                    impact = rec.get("estimated_impact") or "low"
                    affected = rec.get("affected_objects") or []
                    safety = rec.get("safety_level") or "caution"
                else:
                    sql = ""
                    desc = str(rec)
                    impact = "low"
                    affected = []
                    safety = "caution"

                config_changes.append(schemas.FixRecommendation(
                    fix_type="configuration_change",
                    sql=sql,
                    description=desc,
                    estimated_impact=impact,
                    affected_objects=affected,
                    safety_level=safety
                ))
        
        total_fixes = len(index_recs) + len(maintenance_tasks) + len(query_rewrites) + len(config_changes)
        high_impact = len([r for r in index_recs if r.estimated_impact == "high"])
        
        return schemas.GenerateFixesResponse(
            success=True,
            optimization_id=request.optimization_id,
            index_recommendations=index_recs,
            maintenance_tasks=maintenance_tasks,
            query_rewrites=query_rewrites,
            configuration_changes=config_changes,
            total_fixes=total_fixes,
            high_impact_count=high_impact
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating fixes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/apply-fix")
async def apply_fix(
    request: schemas.ApplyFixRequest,
    db: Session = Depends(get_db)
):
    """
    Apply a specific fix with safety checks
    """
    try:
        # Get optimization
        optimization = db.query(Optimization).filter(
            Optimization.id == request.optimization_id
        ).first()
        
        if not optimization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization with id {request.optimization_id} not found"
            )
        
        # Get connection
        connection = db.query(Connection).filter(
            Connection.id == optimization.connection_id
        ).first()
        
        # Create database manager
        password = security_manager.decrypt(connection.password_encrypted)
        db_manager = DatabaseManager(
            engine=connection.engine,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password=password,
            ssl_enabled=connection.ssl_enabled
        )
        
        success, message = db_manager.connect()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to database: {message}"
            )
        
        try:
            # Create fix applicator
            from app.core.fix_applicator import FixApplicator, FixType
            
            config = {
                "enable_ddl_execution": True,
                "allow_dangerous_operations": False,
                "business_hours_only": False
            }
            
            applicator = FixApplicator(db_manager, config)
            
            # Apply fix
            fix_type = FixType(request.fix_type)
            result = applicator.apply_fix(
                fix_type=fix_type,
                fix_sql=request.fix_sql,
                dry_run=request.dry_run,
                skip_safety_checks=request.skip_safety_checks
            )
            
            # Create safety check result
            safety_checks = None
            if not request.skip_safety_checks:
                safety_checks = schemas.SafetyCheckResult(
                    passed=result.get("success", False),
                    checks_performed=["SQL validation", "Dangerous operation check"],
                    warnings=[],
                    errors=[] if result.get("success") else [result.get("error", "Unknown error")]
                )
            
            return schemas.ApplyFixResponse(
                success=result.get("success", False),
                fix_id=None,  # Would need to store in database
                fix_type=request.fix_type,
                status=result.get("status", "failed"),
                message=result.get("message", result.get("error", "Unknown error")),
                execution_time_sec=result.get("execution_time_sec"),
                rollback_sql=result.get("rollback_sql"),
                safety_checks=safety_checks,
                applied_at=datetime.utcnow() if result.get("success") and not request.dry_run else None
            )
        
        finally:
            db_manager.disconnect()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying fix: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/validate-performance")
async def validate_performance(
    request: schemas.ValidatePerformanceRequest,
    db: Session = Depends(get_db)
):
    """
    Validate performance improvement by running both queries
    """
    try:
        # Get optimization
        optimization = db.query(Optimization).filter(
            Optimization.id == request.optimization_id
        ).first()
        
        if not optimization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization with id {request.optimization_id} not found"
            )
        
        # Get connection
        connection = db.query(Connection).filter(
            Connection.id == optimization.connection_id
        ).first()
        
        # Create database manager
        password = security_manager.decrypt(connection.password_encrypted)
        db_manager = DatabaseManager(
            engine=connection.engine,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password=password,
            ssl_enabled=connection.ssl_enabled
        )
        
        success, message = db_manager.connect()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to database: {message}"
            )
        
        try:
            from app.core.performance_validator import PerformanceValidator
            
            validator = PerformanceValidator(db_manager)
            
            # Validate performance
            result = validator.validate_optimization(
                original_sql=optimization.original_sql,
                optimized_sql=optimization.optimized_sql,
                iterations=request.iterations
            )
            
            if not result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Validation failed: {result.get('error')}"
                )
            
            # Extract metrics
            original_metrics = None
            if result.get("original_metrics"):
                om = result["original_metrics"]
                original_metrics = schemas.PerformanceMetrics(
                    execution_time_ms=om.get("avg_execution_time", 0),
                    planning_time_ms=om.get("planning_time"),
                    rows_returned=om.get("rows_returned"),
                    buffer_hits=om.get("buffer_hits"),
                    buffer_reads=om.get("buffer_reads"),
                    io_cost=om.get("io_cost")
                )
            
            optimized_metrics = None
            if result.get("optimized_metrics"):
                opt_m = result["optimized_metrics"]
                optimized_metrics = schemas.PerformanceMetrics(
                    execution_time_ms=opt_m.get("avg_execution_time", 0),
                    planning_time_ms=opt_m.get("planning_time"),
                    rows_returned=opt_m.get("rows_returned"),
                    buffer_hits=opt_m.get("buffer_hits"),
                    buffer_reads=opt_m.get("buffer_reads"),
                    io_cost=opt_m.get("io_cost")
                )
            
            improvement_pct = result.get("improvement_percentage")
            improvement_ms = result.get("improvement_ms")
            is_faster = result.get("is_faster", False)
            
            # Update optimization record
            if improvement_pct:
                optimization.estimated_improvement_pct = improvement_pct
                optimization.validated_at = datetime.utcnow()
                optimization.status = "validated"
                db.commit()
            
            return schemas.ValidatePerformanceResponse(
                success=True,
                optimization_id=request.optimization_id,
                original_metrics=original_metrics,
                optimized_metrics=optimized_metrics,
                improvement_pct=improvement_pct,
                improvement_ms=improvement_ms,
                is_faster=is_faster,
                validation_notes=result.get("notes", []),
                validated_at=datetime.utcnow()
            )
        
        finally:
            db_manager.disconnect()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
