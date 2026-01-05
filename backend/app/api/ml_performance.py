"""
ML Performance API Endpoints
Provides ML model performance metrics and analytics
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.database import get_db, OptimizationPattern
from app.models.schemas import (
    PatternResponse,
    PatternMatchResult,
    MLAccuracyTrend,
    MLPerformanceMetrics,
    AccuracyMetrics
)
from app.core.ml_refinement import MLRefinement
from app.core.pattern_matcher import PatternMatcher
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml", tags=["ml-performance"])


@router.get("/accuracy", response_model=AccuracyMetrics)
async def get_current_accuracy(
    connection_id: Optional[int] = None,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get current ML model accuracy metrics
    
    - **connection_id**: Optional filter by connection
    - **days**: Number of days to analyze (default: 30)
    """
    try:
        logger.info(f"Getting current accuracy for last {days} days")
        
        refinement = MLRefinement(db)
        accuracy = refinement.calculate_model_accuracy(connection_id, days)
        
        # Get additional metrics
        analysis = await refinement.analyze_feedback_data(connection_id, days)
        
        return AccuracyMetrics(
            current_accuracy=accuracy,
            total_optimizations=analysis.get('total_feedback', 0),
            successful_optimizations=analysis.get('successful_count', 0),
            avg_improvement=analysis.get('avg_actual_improvement', 0.0),
            confidence_score=min(100, (analysis.get('total_feedback', 0) / 100) * 100)
        )
        
    except Exception as e:
        logger.error(f"Error getting current accuracy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting accuracy metrics: {str(e)}"
        )


@router.get("/accuracy/trend", response_model=List[MLAccuracyTrend])
async def get_accuracy_trend(
    days: int = Query(default=30, ge=1, le=365),
    connection_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get ML model accuracy trend over time
    
    - **days**: Number of days to analyze (default: 30)
    - **connection_id**: Optional filter by connection
    """
    try:
        logger.info(f"Getting accuracy trend for last {days} days")
        
        refinement = MLRefinement(db)
        trend_data = refinement.get_accuracy_trend(connection_id, days)
        
        return [
            MLAccuracyTrend(
                date=item['date'],
                accuracy=item['accuracy'],
                improvement=item['improvement'],
                count=item['count']
            )
            for item in trend_data
        ]
        
    except Exception as e:
        logger.error(f"Error getting accuracy trend: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting accuracy trend: {str(e)}"
        )


@router.get("/patterns", response_model=List[PatternResponse])
async def get_patterns(
    database_type: Optional[str] = None,
    pattern_type: Optional[str] = None,
    min_success_rate: float = Query(default=0.7, ge=0.0, le=1.0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get successful optimization patterns
    
    - **database_type**: Filter by database type (postgresql, mysql, mssql)
    - **pattern_type**: Filter by pattern type (index, rewrite, config)
    - **min_success_rate**: Minimum success rate (0-1, default: 0.7)
    - **limit**: Maximum number of results (default: 10)
    """
    try:
        logger.info(f"Getting patterns with min_success_rate={min_success_rate}")
        
        query = db.query(OptimizationPattern)
        
        if database_type:
            query = query.filter(OptimizationPattern.database_type == database_type)
        
        if pattern_type:
            query = query.filter(OptimizationPattern.pattern_type == pattern_type)
        
        # Filter by success rate
        query = query.filter(OptimizationPattern.success_rate >= min_success_rate)
        
        # Filter for patterns with sufficient data
        query = query.filter(OptimizationPattern.times_applied >= 3)
        
        # Order by success rate and improvement
        patterns = query.order_by(
            OptimizationPattern.success_rate.desc(),
            OptimizationPattern.avg_improvement_pct.desc()
        ).limit(limit).all()
        
        return [
            PatternResponse(
                id=p.id,
                pattern_type=p.pattern_type,
                pattern_signature=p.pattern_signature,
                original_pattern=p.original_pattern,
                optimized_pattern=p.optimized_pattern,
                success_rate=p.success_rate,
                avg_improvement_pct=p.avg_improvement_pct,
                times_applied=p.times_applied,
                times_successful=p.times_successful,
                database_type=p.database_type,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in patterns
        ]
        
    except Exception as e:
        logger.error(f"Error getting patterns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting patterns: {str(e)}"
        )


@router.get("/patterns/{pattern_id}", response_model=PatternResponse)
async def get_pattern_details(
    pattern_id: int,
    db: Session = Depends(get_db)
):
    """
    Get details for a specific pattern
    
    - **pattern_id**: Pattern ID
    """
    try:
        pattern = db.query(OptimizationPattern).filter(
            OptimizationPattern.id == pattern_id
        ).first()
        
        if not pattern:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pattern {pattern_id} not found"
            )
        
        return PatternResponse(
            id=pattern.id,
            pattern_type=pattern.pattern_type,
            pattern_signature=pattern.pattern_signature,
            original_pattern=pattern.original_pattern,
            optimized_pattern=pattern.optimized_pattern,
            success_rate=pattern.success_rate,
            avg_improvement_pct=pattern.avg_improvement_pct,
            times_applied=pattern.times_applied,
            times_successful=pattern.times_successful,
            database_type=pattern.database_type,
            created_at=pattern.created_at,
            updated_at=pattern.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pattern details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting pattern details: {str(e)}"
        )


@router.post("/patterns/match", response_model=PatternMatchResult)
async def match_query_to_pattern(
    sql_query: str,
    connection_id: int,
    db: Session = Depends(get_db)
):
    """
    Match a SQL query to known patterns
    
    - **sql_query**: SQL query to match
    - **connection_id**: Connection ID (to determine database type)
    """
    try:
        logger.info(f"Matching query to patterns for connection {connection_id}")
        
        matcher = PatternMatcher(db)
        result = await matcher.match_and_suggest(sql_query, connection_id)
        
        if result.get('matched'):
            best_match = result['best_match']
            return PatternMatchResult(
                matched=True,
                pattern_id=best_match['pattern_id'],
                pattern_type=best_match['pattern_type'],
                success_rate=best_match['success_rate'],
                avg_improvement=best_match['avg_improvement_pct'],
                confidence=best_match['confidence']
            )
        else:
            return PatternMatchResult(
                matched=False,
                confidence=0.0
            )
        
    except Exception as e:
        logger.error(f"Error matching query to pattern: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error matching query: {str(e)}"
        )


@router.get("/analysis/feedback", response_model=dict)
async def analyze_feedback(
    connection_id: Optional[int] = None,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive feedback analysis
    
    - **connection_id**: Optional filter by connection
    - **days**: Number of days to analyze (default: 30)
    """
    try:
        logger.info(f"Analyzing feedback for last {days} days")
        
        refinement = MLRefinement(db)
        analysis = await refinement.analyze_feedback_data(connection_id, days)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing feedback: {str(e)}"
        )


@router.get("/report/improvement", response_model=dict)
async def get_improvement_report(
    connection_id: Optional[int] = None,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive ML improvement report
    
    - **connection_id**: Optional filter by connection
    - **days**: Number of days to analyze (default: 30)
    """
    try:
        logger.info(f"Generating improvement report for last {days} days")
        
        refinement = MLRefinement(db)
        report = await refinement.generate_improvement_report(connection_id, days)
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating improvement report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.post("/refinement/trigger", response_model=dict)
async def trigger_refinement(
    db: Session = Depends(get_db)
):
    """
    Manually trigger ML model refinement
    
    This will:
    - Analyze all feedback data
    - Update pattern success rates
    - Identify successful patterns
    - Generate recommendations
    """
    try:
        logger.info("Manually triggering ML refinement")
        
        refinement = MLRefinement(db)
        
        # Update pattern success rates
        update_result = await refinement.update_pattern_success_rates()
        
        # Identify successful patterns
        patterns = await refinement.identify_successful_patterns()
        
        # Analyze feedback
        analysis = await refinement.analyze_feedback_data(days=30)
        
        result = {
            'success': True,
            'message': 'ML refinement completed successfully',
            'patterns_updated': update_result['patterns_updated'],
            'successful_patterns_found': len(patterns),
            'current_accuracy': analysis.get('avg_accuracy', 0.0),
            'success_rate': analysis.get('success_rate', 0.0),
            'recommendations': refinement._generate_recommendations(
                analysis,
                analysis.get('avg_accuracy', 0.0)
            ),
            'refined_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Refinement complete: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error triggering refinement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering refinement: {str(e)}"
        )


@router.get("/stats/summary", response_model=dict)
async def get_ml_stats_summary(
    connection_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get summary of ML performance statistics
    
    - **connection_id**: Optional filter by connection
    """
    try:
        logger.info("Getting ML stats summary")
        
        refinement = MLRefinement(db)
        matcher = PatternMatcher(db)
        
        # Get accuracy
        accuracy = refinement.calculate_model_accuracy(connection_id, days=30)
        
        # Get feedback analysis
        analysis = await refinement.analyze_feedback_data(connection_id, days=30)
        
        # Get patterns
        patterns = matcher.get_top_patterns(limit=10)
        
        # Get successful patterns
        successful_patterns = await refinement.identify_successful_patterns()
        
        summary = {
            'current_accuracy': accuracy,
            'total_feedback': analysis.get('total_feedback', 0),
            'success_rate': analysis.get('success_rate', 0.0),
            'avg_improvement': analysis.get('avg_actual_improvement', 0.0),
            'total_patterns': len(patterns),
            'successful_patterns': len(successful_patterns),
            'accuracy_trend': analysis.get('accuracy_trend', 'unknown'),
            'estimation_bias': analysis.get('estimation_bias', 0.0),
            'top_patterns': patterns[:5],  # Top 5
            'improvement_areas': analysis.get('improvement_areas', []),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting ML stats summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting stats summary: {str(e)}"
        )


@router.get("/patterns/top", response_model=List[dict])
async def get_top_patterns(
    database_type: Optional[str] = None,
    pattern_type: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get top performing patterns
    
    - **database_type**: Filter by database type
    - **pattern_type**: Filter by pattern type
    - **limit**: Maximum number of results (default: 10)
    """
    try:
        logger.info("Getting top patterns")
        
        matcher = PatternMatcher(db)
        patterns = matcher.get_top_patterns(database_type, pattern_type, limit)
        
        return patterns
        
    except Exception as e:
        logger.error(f"Error getting top patterns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting top patterns: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def ml_health_check(db: Session = Depends(get_db)):
    """
    Check ML system health
    
    Returns status of ML components and data availability
    """
    try:
        refinement = MLRefinement(db)
        
        # Check feedback data
        analysis = await refinement.analyze_feedback_data(days=7)
        feedback_count = analysis.get('total_feedback', 0)
        
        # Check patterns
        patterns = db.query(OptimizationPattern).count()
        
        # Determine health status
        if feedback_count >= 10 and patterns >= 5:
            status_level = "healthy"
            message = "ML system is operating normally"
        elif feedback_count >= 5 or patterns >= 3:
            status_level = "warning"
            message = "ML system needs more data for optimal performance"
        else:
            status_level = "insufficient_data"
            message = "ML system needs more feedback and patterns"
        
        return {
            'status': status_level,
            'message': message,
            'feedback_count_7days': feedback_count,
            'total_patterns': patterns,
            'min_feedback_needed': 10,
            'min_patterns_needed': 5,
            'checked_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in ML health check: {str(e)}")
        return {
            'status': 'error',
            'message': f'Health check failed: {str(e)}',
            'checked_at': datetime.utcnow().isoformat()
        }
