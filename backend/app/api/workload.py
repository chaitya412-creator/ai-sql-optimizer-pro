"""
Workload Analysis API Endpoints
Provides workload pattern analysis and performance trend predictions
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.models.database import get_db
from app.core.workload_analyzer import WorkloadAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/analysis/{connection_id}")
async def get_workload_analysis(
    connection_id: int,
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive workload analysis for a connection
    
    Args:
        connection_id: Database connection ID
        days: Number of days to analyze (1-90)
        
    Returns:
        Comprehensive workload analysis including patterns, trends, and insights
    """
    try:
        logger.info(f"Getting workload analysis for connection {connection_id}, days={days}")
        
        analyzer = WorkloadAnalyzer(db)
        analysis = await analyzer.analyze_workload_pattern(connection_id, days)
        
        # Add recommendations and predictions
        recommendations = analyzer.generate_proactive_recommendations(connection_id, days)
        predictions = analyzer.predict_performance_trends(connection_id, days)
        
        # Combine all analysis data
        result = {
            **analysis,
            'recommendations': recommendations,
            'predictions': predictions
        }
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting workload analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze workload: {str(e)}")


@router.get("/patterns/{connection_id}")
async def get_workload_patterns(
    connection_id: int,
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get detected workload patterns for a connection
    
    Args:
        connection_id: Database connection ID
        days: Number of days to analyze (1-90)
        
    Returns:
        Workload patterns including hourly, daily, and query patterns
    """
    try:
        logger.info(f"Getting workload patterns for connection {connection_id}")
        
        analyzer = WorkloadAnalyzer(db)
        analysis = await analyzer.analyze_workload_pattern(connection_id, days)
        
        # Extract pattern-specific data
        patterns = {
            'connection_id': connection_id,
            'analysis_period_days': days,
            'workload_type': analysis.get('workload_type', 'unknown'),
            'hourly_pattern': analysis.get('hourly_pattern', {}),
            'daily_pattern': analysis.get('daily_pattern', {}),
            'query_pattern': analysis.get('query_pattern', {}),
            'resource_pattern': analysis.get('resource_pattern', {}),
            'peak_hours': analysis.get('hourly_pattern', {}).get('peak_hours', []),
            'off_peak_hours': analysis.get('hourly_pattern', {}).get('off_peak_hours', []),
            'busiest_day': analysis.get('daily_pattern', {}).get('busiest_day', 'Unknown'),
            'quietest_day': analysis.get('daily_pattern', {}).get('quietest_day', 'Unknown'),
            'analyzed_at': analysis.get('analyzed_at')
        }
        
        return patterns
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting workload patterns: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get patterns: {str(e)}")


@router.get("/trends/{connection_id}")
async def get_performance_trends(
    connection_id: int,
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get performance trends and predictions for a connection
    
    Args:
        connection_id: Database connection ID
        days: Number of days to analyze (1-90)
        
    Returns:
        Performance trends including predictions and warnings
    """
    try:
        logger.info(f"Getting performance trends for connection {connection_id}")
        
        analyzer = WorkloadAnalyzer(db)
        
        # Get historical trends
        analysis = await analyzer.analyze_workload_pattern(connection_id, days)
        historical_trends = analysis.get('trends', {})
        
        # Get predictions
        predictions = analyzer.predict_performance_trends(connection_id, days)
        
        # Get workload shifts
        shifts = await analyzer.detect_workload_shifts(connection_id, days)
        
        trends = {
            'connection_id': connection_id,
            'analysis_period_days': days,
            'historical_trends': historical_trends,
            'predictions': predictions,
            'workload_shifts': shifts,
            'shift_count': len(shifts),
            'analyzed_at': analysis.get('analyzed_at')
        }
        
        return trends
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting performance trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")


@router.post("/analyze")
async def trigger_workload_analysis(
    connection_id: int = Query(..., description="Database connection ID"),
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze"),
    include_recommendations: bool = Query(default=True, description="Include proactive recommendations"),
    include_predictions: bool = Query(default=True, description="Include performance predictions"),
    db: Session = Depends(get_db)
):
    """
    Trigger a comprehensive workload analysis
    
    Args:
        connection_id: Database connection ID
        days: Number of days to analyze (1-90)
        include_recommendations: Whether to include recommendations
        include_predictions: Whether to include predictions
        
    Returns:
        Complete workload analysis with optional recommendations and predictions
    """
    try:
        logger.info(f"Triggering workload analysis for connection {connection_id}")
        
        analyzer = WorkloadAnalyzer(db)
        
        # Perform comprehensive analysis
        analysis = await analyzer.analyze_workload_pattern(connection_id, days)
        
        result = {
            'status': 'success',
            'connection_id': connection_id,
            'analysis': analysis
        }
        
        # Add recommendations if requested
        if include_recommendations:
            recommendations = analyzer.generate_proactive_recommendations(connection_id, days)
            result['recommendations'] = recommendations
            result['recommendation_count'] = len(recommendations)
        
        # Add predictions if requested
        if include_predictions:
            predictions = analyzer.predict_performance_trends(connection_id, days)
            result['predictions'] = predictions
        
        # Add workload shifts
        shifts = await analyzer.detect_workload_shifts(connection_id, days)
        result['workload_shifts'] = shifts
        result['shift_count'] = len(shifts)
        
        logger.info(f"Workload analysis completed successfully")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error triggering workload analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze workload: {str(e)}")


@router.get("/recommendations/{connection_id}")
async def get_proactive_recommendations(
    connection_id: int,
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get proactive optimization recommendations based on workload analysis
    
    Args:
        connection_id: Database connection ID
        days: Number of days to analyze (1-90)
        
    Returns:
        List of proactive recommendations with priorities and estimated impacts
    """
    try:
        logger.info(f"Getting proactive recommendations for connection {connection_id}")
        
        analyzer = WorkloadAnalyzer(db)
        recommendations = analyzer.generate_proactive_recommendations(connection_id, days)
        
        # Sort by priority (high, medium, low)
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        sorted_recommendations = sorted(
            recommendations,
            key=lambda x: priority_order.get(x.get('priority', 'low'), 3)
        )
        
        return {
            'connection_id': connection_id,
            'analysis_period_days': days,
            'total_recommendations': len(sorted_recommendations),
            'high_priority_count': len([r for r in sorted_recommendations if r.get('priority') == 'high']),
            'medium_priority_count': len([r for r in sorted_recommendations if r.get('priority') == 'medium']),
            'low_priority_count': len([r for r in sorted_recommendations if r.get('priority') == 'low']),
            'recommendations': sorted_recommendations
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")
