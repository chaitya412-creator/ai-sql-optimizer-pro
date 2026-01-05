"""
Dashboard Statistics API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json

from app.models.database import get_db, Connection, Query, Optimization
from app.models.schemas import (
    DashboardStats, QueryResponse, TopQuery, PerformanceTrend,
    DetectionSummary, IssueTypeSummary, CriticalIssuePreview,
    QueryWithIssues, IssueDetail
)
from loguru import logger

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    connection_id: int = None,
    db: Session = Depends(get_db)
):
    """Get dashboard statistics, optionally filtered by connection_id"""
    try:
        # Build base query for connections
        connection_query = db.query(func.count(Connection.id))
        if connection_id:
            connection_query = connection_query.filter(Connection.id == connection_id)
        
        total_connections = connection_query.scalar()
        
        # If no connections exist, return empty stats
        if not total_connections or total_connections == 0:
            logger.info("No connections found, returning empty dashboard stats")
            return DashboardStats(
                total_connections=0,
                active_connections=0,
                total_queries_discovered=0,
                total_optimizations=0,
                optimizations_applied=0,
                avg_improvement_pct=None,
                top_bottlenecks=[],
                optimizations_with_issues=0,
                total_detected_issues=0
            )
        
        # Active connections (monitoring enabled)
        active_query = db.query(func.count(Connection.id)).filter(
            Connection.monitoring_enabled == True
        )
        if connection_id:
            active_query = active_query.filter(Connection.id == connection_id)
        active_connections = active_query.scalar()
        
        # Total queries discovered
        queries_query = db.query(func.count(Query.id))
        if connection_id:
            queries_query = queries_query.filter(Query.connection_id == connection_id)
        total_queries_discovered = queries_query.scalar()
        
        # Total optimizations
        opt_query = db.query(func.count(Optimization.id))
        if connection_id:
            opt_query = opt_query.filter(Optimization.connection_id == connection_id)
        total_optimizations = opt_query.scalar()
        
        # Optimizations applied
        applied_query = db.query(func.count(Optimization.id)).filter(
            Optimization.status == "applied"
        )
        if connection_id:
            applied_query = applied_query.filter(Optimization.connection_id == connection_id)
        optimizations_applied = applied_query.scalar()
        
        # Average improvement percentage
        avg_query = db.query(
            func.avg(Optimization.estimated_improvement_pct)
        ).filter(
            Optimization.estimated_improvement_pct.isnot(None)
        )
        if connection_id:
            avg_query = avg_query.filter(Optimization.connection_id == connection_id)
        avg_improvement = avg_query.scalar()
        
        # Top bottlenecks (top 10 worst queries)
        bottleneck_query = db.query(Query).order_by(
            Query.total_exec_time_ms.desc()
        )
        if connection_id:
            bottleneck_query = bottleneck_query.filter(Query.connection_id == connection_id)
        top_bottlenecks = bottleneck_query.limit(10).all()
        
        # Get detection summary for stats
        detection_summary = None
        try:
            # Count total issues from QueryIssue table (proactive monitoring)
            proactive_issues_query = db.query(func.count(QueryIssue.id)).filter(
                QueryIssue.resolved == False
            )
            if connection_id:
                proactive_issues_query = proactive_issues_query.filter(QueryIssue.connection_id == connection_id)
            
            total_proactive_issues = proactive_issues_query.scalar() or 0
            
            # Get all optimizations with detected issues (on-demand optimization)
            issues_query = db.query(Optimization).filter(
                Optimization.detected_issues.isnot(None)
            )
            if connection_id:
                issues_query = issues_query.filter(Optimization.connection_id == connection_id)
            
            optimizations_with_issues_list = issues_query.all()
            optimizations_with_issues = len(optimizations_with_issues_list)
            
            # Count total issues by summing up issues in each optimization
            total_optimization_issues = 0
            for opt in optimizations_with_issues_list:
                try:
                    if isinstance(opt.detected_issues, str):
                        issues_data = json.loads(opt.detected_issues)
                    else:
                        issues_data = opt.detected_issues
                    
                    total_optimization_issues += issues_data.get("total_issues", 0)
                except Exception as e:
                    logger.warning(f"Error parsing detected_issues for optimization {opt.id}: {e}")
                    total_optimization_issues += 1
            
            total_issues = total_proactive_issues + total_optimization_issues
        except Exception as e:
            logger.error(f"Error getting detection stats: {e}")
            optimizations_with_issues = 0
            total_issues = 0
        
        return DashboardStats(
            total_connections=total_connections or 0,
            active_connections=active_connections or 0,
            total_queries_discovered=total_queries_discovered or 0,
            total_optimizations=total_optimizations or 0,
            optimizations_applied=optimizations_applied or 0,
            avg_improvement_pct=float(avg_improvement) if avg_improvement else None,
            top_bottlenecks=[QueryResponse.from_orm(q) for q in top_bottlenecks],
            optimizations_with_issues=optimizations_with_issues,
            total_detected_issues=total_issues
        )
    
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/top-queries", response_model=List[TopQuery])
async def get_top_queries(
    limit: int = 10,
    connection_id: int = None,
    db: Session = Depends(get_db)
):
    """Get top queries by execution time, optionally filtered by connection_id"""
    try:
        # Check if any connections exist
        connection_query = db.query(func.count(Connection.id))
        if connection_id:
            connection_query = connection_query.filter(Connection.id == connection_id)
        total_connections = connection_query.scalar()
        if not total_connections or total_connections == 0:
            logger.info("No connections found, returning empty top queries list")
            return []
        
        # Query top queries ordered by total execution time
        query = db.query(Query).order_by(
            Query.total_exec_time_ms.desc()
        )
        if connection_id:
            query = query.filter(Query.connection_id == connection_id)
        top_queries = query.limit(limit).all()
        
        result = []
        for query in top_queries:
            # Get connection name
            connection = db.query(Connection).filter(
                Connection.id == query.connection_id
            ).first()
            
            # Determine severity based on execution time
            avg_time = query.avg_exec_time_ms
            if avg_time > 5000:  # > 5 seconds
                severity = "high"
            elif avg_time > 1000:  # > 1 second
                severity = "medium"
            else:
                severity = "low"
            
            result.append(TopQuery(
                id=query.id,
                connection_name=connection.name if connection else "Unknown",
                sql_text=query.sql_text[:200] + "..." if len(query.sql_text) > 200 else query.sql_text,
                avg_execution_time=query.avg_exec_time_ms,
                total_execution_time=query.total_exec_time_ms,
                calls=query.calls,
                severity=severity
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting top queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/performance-trends", response_model=List[PerformanceTrend])
async def get_performance_trends(
    hours: int = 24,
    connection_id: int = None,
    db: Session = Depends(get_db)
):
    """Get performance trends over time, optionally filtered by connection_id"""
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get queries discovered in the time range
        query = db.query(Query).filter(
            Query.discovered_at >= start_time
        )
        if connection_id:
            query = query.filter(Query.connection_id == connection_id)
        queries = query.all()
        
        # Group by hour and calculate metrics
        trends = {}
        for query in queries:
            # Round to hour
            hour_key = query.discovered_at.replace(minute=0, second=0, microsecond=0)
            hour_str = hour_key.isoformat()
            
            if hour_str not in trends:
                trends[hour_str] = {
                    "total_time": 0,
                    "count": 0,
                    "slow_count": 0
                }
            
            trends[hour_str]["total_time"] += query.avg_exec_time_ms
            trends[hour_str]["count"] += 1
            
            # Count as slow if avg execution time > 1 second
            if query.avg_exec_time_ms > 1000:
                trends[hour_str]["slow_count"] += 1
        
        # Convert to list of PerformanceTrend objects
        result = []
        for timestamp, data in sorted(trends.items()):
            avg_time = data["total_time"] / data["count"] if data["count"] > 0 else 0
            result.append(PerformanceTrend(
                timestamp=timestamp,
                avg_time=avg_time,
                slow_queries=data["slow_count"],
                total_queries=data["count"]
            ))
        
        # If no data, return empty trends for each hour
        if not result:
            for i in range(hours):
                hour = end_time - timedelta(hours=i)
                hour = hour.replace(minute=0, second=0, microsecond=0)
                result.append(PerformanceTrend(
                    timestamp=hour.isoformat(),
                    avg_time=0,
                    slow_queries=0,
                    total_queries=0
                ))
        
        return sorted(result, key=lambda x: x.timestamp)
    
    except Exception as e:
        logger.error(f"Error getting performance trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 20,
    connection_id: int = None,
    db: Session = Depends(get_db)
):
    """Get recent optimization activity, optionally filtered by connection_id"""
    try:
        query = db.query(Optimization).order_by(
            Optimization.created_at.desc()
        )
        if connection_id:
            query = query.filter(Optimization.connection_id == connection_id)
        recent_optimizations = query.limit(limit).all()
        
        activity = []
        for opt in recent_optimizations:
            connection = db.query(Connection).filter(
                Connection.id == opt.connection_id
            ).first()
            
            activity.append({
                "id": opt.id,
                "connection_name": connection.name if connection else "Unknown",
                "status": opt.status,
                "created_at": opt.created_at,
                "applied_at": opt.applied_at
            })
        
        return activity
    
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/detection-summary", response_model=DetectionSummary)
async def get_detection_summary(
    connection_id: int = None,
    db: Session = Depends(get_db)
):
    """Get aggregated detection summary, optionally filtered by connection_id"""
    try:
        # Check if any connections exist
        connection_query = db.query(func.count(Connection.id))
        if connection_id:
            connection_query = connection_query.filter(Connection.id == connection_id)
        total_connections = connection_query.scalar()
        if not total_connections or total_connections == 0:
            logger.info("No connections found, returning empty detection summary")
            return DetectionSummary(
                total_issues=0,
                critical_issues=0,
                high_issues=0,
                medium_issues=0,
                low_issues=0,
                issues_by_type=[],
                recent_critical_issues=[],
                total_optimizations_with_issues=0,
                last_updated=datetime.utcnow()
            )
        
        # Get all optimizations with detected issues
        query = db.query(Optimization).filter(
            Optimization.detected_issues.isnot(None)
        )
        if connection_id:
            query = query.filter(Optimization.connection_id == connection_id)
        optimizations = query.all()
        
        # Initialize counters
        total_issues = 0
        critical_issues = 0
        high_issues = 0
        medium_issues = 0
        low_issues = 0
        issues_by_type: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            "count": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        })
        recent_critical: List[Dict[str, Any]] = []
        
        # Process each optimization
        for opt in optimizations:
            if not opt.detected_issues:
                continue
            
            try:
                # Parse detected_issues JSON
                if isinstance(opt.detected_issues, str):
                    issues_data = json.loads(opt.detected_issues)
                else:
                    issues_data = opt.detected_issues
                
                # Get connection name
                connection = db.query(Connection).filter(
                    Connection.id == opt.connection_id
                ).first()
                connection_name = connection.name if connection else "Unknown"
                
                # Aggregate severity counts
                total_issues += issues_data.get("total_issues", 0)
                critical_issues += issues_data.get("critical_issues", 0)
                high_issues += issues_data.get("high_issues", 0)
                medium_issues += issues_data.get("medium_issues", 0)
                low_issues += issues_data.get("low_issues", 0)
                
                # Process individual issues
                for issue in issues_data.get("issues", []):
                    issue_type = issue.get("issue_type", "unknown")
                    severity = issue.get("severity", "low")
                    
                    # Count by type
                    issues_by_type[issue_type]["count"] += 1
                    issues_by_type[issue_type][severity] += 1
                    
                    # Collect critical issues for preview
                    if severity == "critical" and len(recent_critical) < 10:
                        recent_critical.append({
                            "optimization_id": opt.id,
                            "connection_name": connection_name,
                            "issue_type": issue_type,
                            "severity": severity,
                            "title": issue.get("title", "Unknown Issue"),
                            "description": issue.get("description", ""),
                            "detected_at": issue.get("detected_at", opt.created_at.isoformat())
                        })
            
            except Exception as e:
                logger.warning(f"Error processing optimization {opt.id} issues: {e}")
                continue
        
        # Convert issues_by_type to list of IssueTypeSummary
        issues_by_type_list = [
            IssueTypeSummary(
                issue_type=issue_type,
                count=data["count"],
                critical=data["critical"],
                high=data["high"],
                medium=data["medium"],
                low=data["low"]
            )
            for issue_type, data in issues_by_type.items()
        ]
        
        # Sort by total count descending
        issues_by_type_list.sort(key=lambda x: x.count, reverse=True)
        
        # Convert recent_critical to CriticalIssuePreview objects
        recent_critical_list = [
            CriticalIssuePreview(**issue)
            for issue in recent_critical
        ]
        
        # Sort by detected_at descending
        recent_critical_list.sort(key=lambda x: x.detected_at, reverse=True)
        
        return DetectionSummary(
            total_issues=total_issues,
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            issues_by_type=issues_by_type_list,
            recent_critical_issues=recent_critical_list[:5],  # Top 5 critical
            total_optimizations_with_issues=len(optimizations),
            last_updated=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error getting detection summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/queries-with-issues", response_model=List[QueryWithIssues])
async def get_queries_with_issues(
    limit: int = 20,
    connection_id: int = None,
    db: Session = Depends(get_db)
):
    """Get queries (optimizations) with their detected issues, optionally filtered by connection_id"""
    try:
        # Check if any connections exist
        connection_query = db.query(func.count(Connection.id))
        if connection_id:
            connection_query = connection_query.filter(Connection.id == connection_id)
        total_connections = connection_query.scalar()
        if not total_connections or total_connections == 0:
            logger.info("No connections found, returning empty queries with issues list")
            return []
        
        # Get optimizations with detected issues, ordered by severity and time
        query = db.query(Optimization).filter(
            Optimization.detected_issues.isnot(None)
        ).order_by(
            Optimization.created_at.desc()
        )
        if connection_id:
            query = query.filter(Optimization.connection_id == connection_id)
        optimizations = query.limit(limit).all()
        
        result = []
        
        for opt in optimizations:
            if not opt.detected_issues:
                continue
            
            try:
                # Parse detected_issues JSON
                if isinstance(opt.detected_issues, str):
                    issues_data = json.loads(opt.detected_issues)
                else:
                    issues_data = opt.detected_issues
                
                # Get connection name
                connection = db.query(Connection).filter(
                    Connection.id == opt.connection_id
                ).first()
                connection_name = connection.name if connection else "Unknown"
                
                # Extract issue counts
                critical_count = issues_data.get("critical_issues", 0)
                high_count = issues_data.get("high_issues", 0)
                medium_count = issues_data.get("medium_issues", 0)
                low_count = issues_data.get("low_issues", 0)
                total_count = issues_data.get("total_issues", 0)
                
                # Process individual issues
                issue_details = []
                for issue in issues_data.get("issues", []):
                    issue_details.append(IssueDetail(
                        issue_type=issue.get("issue_type", "unknown"),
                        severity=issue.get("severity", "low"),
                        title=issue.get("title", "Unknown Issue"),
                        description=issue.get("description", ""),
                        recommendations=issue.get("recommendations", [])
                    ))
                
                # Create SQL preview (truncate to 200 chars)
                sql_preview = opt.original_sql[:200] + "..." if len(opt.original_sql) > 200 else opt.original_sql
                
                # Determine detected_at timestamp
                detected_at = opt.created_at
                if issues_data.get("issues") and len(issues_data["issues"]) > 0:
                    first_issue = issues_data["issues"][0]
                    if "detected_at" in first_issue:
                        try:
                            detected_at = datetime.fromisoformat(first_issue["detected_at"].replace('Z', '+00:00'))
                        except:
                            pass
                
                # Check if optimized_sql is valid (not an error message)
                optimized_sql_to_display = opt.optimized_sql
                if opt.optimized_sql and (
                    opt.optimized_sql.strip().startswith('--') and 
                    any(indicator in opt.optimized_sql.lower() for indicator in [
                        'optimization failed', 'could not parse', 'error:', 'failed to'
                    ])
                ):
                    # This is an error message, not valid SQL
                    optimized_sql_to_display = ""
                    logger.warning(f"Optimization {opt.id} has invalid optimized_sql (error message)")
                
                result.append(QueryWithIssues(
                    optimization_id=opt.id,
                    connection_id=opt.connection_id,
                    connection_name=connection_name,
                    original_sql=opt.original_sql,
                    optimized_sql=optimized_sql_to_display,  # Use validated SQL
                    sql_preview=sql_preview,
                    issue_count=total_count,
                    critical_count=critical_count,
                    high_count=high_count,
                    medium_count=medium_count,
                    low_count=low_count,
                    issues=issue_details,
                    detected_at=detected_at,
                    recommendations=opt.recommendations,  # Add recommendations
                    estimated_improvement_pct=opt.estimated_improvement_pct  # Add improvement
                ))
            
            except Exception as e:
                logger.warning(f"Error processing optimization {opt.id} for queries-with-issues: {e}")
                continue
        
        # Sort by severity (critical first) and then by detected_at
        def sort_key(q: QueryWithIssues):
            # Priority: critical > high > medium > low, then by time (newest first)
            severity_weight = (
                q.critical_count * 1000 +
                q.high_count * 100 +
                q.medium_count * 10 +
                q.low_count
            )
            return (-severity_weight, -q.detected_at.timestamp())
        
        result.sort(key=sort_key)
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting queries with issues: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
