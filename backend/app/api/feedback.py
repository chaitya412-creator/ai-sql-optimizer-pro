"""
Feedback API Endpoints
Handles optimization feedback submission and retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.database import get_db, OptimizationFeedback, Optimization
from app.models.schemas import (
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackResponse,
    FeedbackStats,
    AccuracyMetrics
)
from app.core.performance_tracker import PerformanceTracker
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Submit feedback for an optimization
    
    - **optimization_id**: ID of the optimization
    - **before_metrics**: Performance metrics before optimization
    - **after_metrics**: Performance metrics after optimization
    - **dba_rating**: Optional rating (1-5 stars)
    - **dba_comments**: Optional comments
    """
    try:
        logger.info(f"Submitting feedback for optimization {feedback_data.optimization_id}")
        
        # Verify optimization exists
        optimization = db.query(Optimization).filter(
            Optimization.id == feedback_data.optimization_id
        ).first()
        
        if not optimization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Optimization {feedback_data.optimization_id} not found"
            )
        
        # Create performance tracker
        tracker = PerformanceTracker(db)
        
        # Store feedback
        feedback = await tracker.store_feedback(
            optimization_id=feedback_data.optimization_id,
            before_metrics=feedback_data.before_metrics,
            after_metrics=feedback_data.after_metrics,
            dba_rating=feedback_data.dba_rating,
            dba_comments=feedback_data.dba_comments
        )
        
        logger.info(f"Feedback submitted successfully: {feedback.id}")
        
        return FeedbackResponse(
            id=feedback.id,
            optimization_id=feedback.optimization_id,
            connection_id=feedback.connection_id,
            before_metrics=feedback.before_metrics,
            after_metrics=feedback.after_metrics,
            actual_improvement_pct=feedback.actual_improvement_pct,
            estimated_improvement_pct=feedback.estimated_improvement_pct,
            accuracy_score=feedback.accuracy_score,
            applied_at=feedback.applied_at,
            measured_at=feedback.measured_at,
            feedback_status=feedback.feedback_status,
            dba_rating=feedback.dba_rating,
            dba_comments=feedback.dba_comments
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting feedback: {str(e)}"
        )


@router.get("/{optimization_id}", response_model=FeedbackResponse)
async def get_feedback(
    optimization_id: int,
    db: Session = Depends(get_db)
):
    """
    Get feedback for a specific optimization
    
    - **optimization_id**: ID of the optimization
    """
    try:
        feedback = db.query(OptimizationFeedback).filter(
            OptimizationFeedback.optimization_id == optimization_id
        ).first()
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback for optimization {optimization_id} not found"
            )
        
        return FeedbackResponse(
            id=feedback.id,
            optimization_id=feedback.optimization_id,
            connection_id=feedback.connection_id,
            before_metrics=feedback.before_metrics,
            after_metrics=feedback.after_metrics,
            actual_improvement_pct=feedback.actual_improvement_pct,
            estimated_improvement_pct=feedback.estimated_improvement_pct,
            accuracy_score=feedback.accuracy_score,
            applied_at=feedback.applied_at,
            measured_at=feedback.measured_at,
            feedback_status=feedback.feedback_status,
            dba_rating=feedback.dba_rating,
            dba_comments=feedback.dba_comments
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting feedback: {str(e)}"
        )


@router.get("/list/all", response_model=List[FeedbackResponse])
async def list_all_feedback(
    connection_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all feedback with optional filters
    
    - **connection_id**: Optional filter by connection
    - **status_filter**: Optional filter by status (success, partial, failed)
    - **limit**: Maximum number of results
    """
    try:
        query = db.query(OptimizationFeedback)
        
        if connection_id:
            query = query.filter(OptimizationFeedback.connection_id == connection_id)
        
        if status_filter:
            query = query.filter(OptimizationFeedback.feedback_status == status_filter)
        
        feedbacks = query.order_by(
            OptimizationFeedback.measured_at.desc()
        ).limit(limit).all()
        
        return [
            FeedbackResponse(
                id=f.id,
                optimization_id=f.optimization_id,
                connection_id=f.connection_id,
                before_metrics=f.before_metrics,
                after_metrics=f.after_metrics,
                actual_improvement_pct=f.actual_improvement_pct,
                estimated_improvement_pct=f.estimated_improvement_pct,
                accuracy_score=f.accuracy_score,
                applied_at=f.applied_at,
                measured_at=f.measured_at,
                feedback_status=f.feedback_status,
                dba_rating=f.dba_rating,
                dba_comments=f.dba_comments
            )
            for f in feedbacks
        ]
        
    except Exception as e:
        logger.error(f"Error listing feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing feedback: {str(e)}"
        )


@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: int,
    feedback_update: FeedbackUpdate,
    db: Session = Depends(get_db)
):
    """
    Update feedback (mainly for DBA rating and comments)
    
    - **feedback_id**: ID of the feedback to update
    - **dba_rating**: Updated rating (1-5 stars)
    - **dba_comments**: Updated comments
    """
    try:
        feedback = db.query(OptimizationFeedback).filter(
            OptimizationFeedback.id == feedback_id
        ).first()
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback {feedback_id} not found"
            )
        
        # Update fields
        if feedback_update.dba_rating is not None:
            feedback.dba_rating = feedback_update.dba_rating
        
        if feedback_update.dba_comments is not None:
            feedback.dba_comments = feedback_update.dba_comments
        
        db.commit()
        db.refresh(feedback)
        
        logger.info(f"Feedback {feedback_id} updated successfully")
        
        return FeedbackResponse(
            id=feedback.id,
            optimization_id=feedback.optimization_id,
            connection_id=feedback.connection_id,
            before_metrics=feedback.before_metrics,
            after_metrics=feedback.after_metrics,
            actual_improvement_pct=feedback.actual_improvement_pct,
            estimated_improvement_pct=feedback.estimated_improvement_pct,
            accuracy_score=feedback.accuracy_score,
            applied_at=feedback.applied_at,
            measured_at=feedback.measured_at,
            feedback_status=feedback.feedback_status,
            dba_rating=feedback.dba_rating,
            dba_comments=feedback.dba_comments
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating feedback: {str(e)}"
        )


@router.get("/stats/summary", response_model=FeedbackStats)
async def get_feedback_stats(
    connection_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get feedback statistics
    
    - **connection_id**: Optional filter by connection
    """
    try:
        tracker = PerformanceTracker(db)
        stats = tracker.get_feedback_stats(connection_id)
        
        return FeedbackStats(
            total_feedback=stats['total_feedback'],
            avg_accuracy=stats['avg_accuracy'],
            avg_improvement=stats['avg_improvement'],
            success_rate=stats['success_rate'],
            avg_rating=stats['avg_rating'],
            success_count=stats.get('success_count', 0),
            partial_count=stats.get('partial_count', 0),
            failed_count=stats.get('failed_count', 0)
        )
        
    except Exception as e:
        logger.error(f"Error getting feedback stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting feedback stats: {str(e)}"
        )


@router.get("/accuracy/current", response_model=AccuracyMetrics)
async def get_current_accuracy(
    connection_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get current model accuracy metrics
    
    - **connection_id**: Optional filter by connection
    """
    try:
        query = db.query(OptimizationFeedback)
        
        if connection_id:
            query = query.filter(OptimizationFeedback.connection_id == connection_id)
        
        # Get recent feedback (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_feedback = query.filter(
            OptimizationFeedback.measured_at >= thirty_days_ago
        ).all()
        
        if not recent_feedback:
            return AccuracyMetrics(
                current_accuracy=0.0,
                total_optimizations=0,
                successful_optimizations=0,
                avg_improvement=0.0,
                confidence_score=0.0
            )
        
        total = len(recent_feedback)
        avg_accuracy = sum(f.accuracy_score or 0 for f in recent_feedback) / total
        successful = sum(1 for f in recent_feedback if f.feedback_status == 'success')
        avg_improvement = sum(f.actual_improvement_pct or 0 for f in recent_feedback) / total
        
        # Calculate confidence score based on sample size and accuracy
        confidence = min(100, (total / 100) * 100) * (avg_accuracy / 100)
        
        return AccuracyMetrics(
            current_accuracy=round(avg_accuracy, 2),
            total_optimizations=total,
            successful_optimizations=successful,
            avg_improvement=round(avg_improvement, 2),
            confidence_score=round(confidence, 2)
        )
        
    except Exception as e:
        logger.error(f"Error getting accuracy metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting accuracy metrics: {str(e)}"
        )


@router.get("/accuracy/trend", response_model=List[dict])
async def get_accuracy_trend(
    days: int = 30,
    connection_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get accuracy trend over time
    
    - **days**: Number of days to look back
    - **connection_id**: Optional filter by connection
    """
    try:
        query = db.query(OptimizationFeedback)
        
        if connection_id:
            query = query.filter(OptimizationFeedback.connection_id == connection_id)
        
        # Get feedback for specified period
        start_date = datetime.utcnow() - timedelta(days=days)
        feedbacks = query.filter(
            OptimizationFeedback.measured_at >= start_date
        ).order_by(OptimizationFeedback.measured_at).all()
        
        if not feedbacks:
            return []
        
        # Group by day and calculate daily accuracy
        daily_accuracy = {}
        
        for feedback in feedbacks:
            date_key = feedback.measured_at.date().isoformat()
            
            if date_key not in daily_accuracy:
                daily_accuracy[date_key] = {
                    'date': date_key,
                    'accuracy_scores': [],
                    'improvement_scores': []
                }
            
            daily_accuracy[date_key]['accuracy_scores'].append(feedback.accuracy_score or 0)
            daily_accuracy[date_key]['improvement_scores'].append(feedback.actual_improvement_pct or 0)
        
        # Calculate averages
        trend_data = []
        for date_key, data in sorted(daily_accuracy.items()):
            avg_accuracy = sum(data['accuracy_scores']) / len(data['accuracy_scores'])
            avg_improvement = sum(data['improvement_scores']) / len(data['improvement_scores'])
            
            trend_data.append({
                'date': data['date'],
                'accuracy': round(avg_accuracy, 2),
                'improvement': round(avg_improvement, 2),
                'count': len(data['accuracy_scores'])
            })
        
        return trend_data
        
    except Exception as e:
        logger.error(f"Error getting accuracy trend: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting accuracy trend: {str(e)}"
        )
