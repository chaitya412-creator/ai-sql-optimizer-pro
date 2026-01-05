"""
ML Refinement Module
Analyzes feedback data and refines the ML model for better accuracy
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import logging

from app.models.database import (
    OptimizationFeedback,
    OptimizationPattern,
    Optimization,
    Connection
)

logger = logging.getLogger(__name__)


class MLRefinement:
    """ML model refinement and continuous learning"""
    
    def __init__(self, db: Session):
        self.db = db
        self.min_feedback_samples = 10  # Minimum samples for refinement
        self.pattern_confidence_threshold = 0.7  # 70% success rate
    
    async def analyze_feedback_data(
        self,
        connection_id: Optional[int] = None,
        days: int = 30
    ) -> Dict:
        """
        Analyze feedback data to identify trends and patterns
        
        Args:
            connection_id: Optional connection ID to filter by
            days: Number of days to analyze
            
        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info(f"Analyzing feedback data for last {days} days")
            
            # Get feedback from specified period
            start_date = datetime.utcnow() - timedelta(days=days)
            query = self.db.query(OptimizationFeedback).filter(
                OptimizationFeedback.measured_at >= start_date
            )
            
            if connection_id:
                query = query.filter(OptimizationFeedback.connection_id == connection_id)
            
            feedbacks = query.all()
            
            if not feedbacks:
                return {
                    'total_feedback': 0,
                    'analysis_period_days': days,
                    'message': 'No feedback data available for analysis'
                }
            
            # Calculate metrics
            total = len(feedbacks)
            successful = sum(1 for f in feedbacks if f.feedback_status == 'success')
            partial = sum(1 for f in feedbacks if f.feedback_status == 'partial')
            failed = sum(1 for f in feedbacks if f.feedback_status == 'failed')
            
            avg_accuracy = sum(f.accuracy_score or 0 for f in feedbacks) / total
            avg_improvement = sum(f.actual_improvement_pct or 0 for f in feedbacks) / total
            avg_estimated = sum(f.estimated_improvement_pct or 0 for f in feedbacks) / total
            
            # Calculate accuracy trend
            accuracy_trend = self._calculate_accuracy_trend(feedbacks)
            
            # Identify common patterns in successful optimizations
            successful_patterns = self._identify_successful_patterns(feedbacks)
            
            # Identify areas for improvement
            improvement_areas = self._identify_improvement_areas(feedbacks)
            
            analysis = {
                'total_feedback': total,
                'successful_count': successful,
                'partial_count': partial,
                'failed_count': failed,
                'success_rate': round((successful / total) * 100, 2),
                'avg_accuracy': round(avg_accuracy, 2),
                'avg_actual_improvement': round(avg_improvement, 2),
                'avg_estimated_improvement': round(avg_estimated, 2),
                'estimation_bias': round(avg_estimated - avg_improvement, 2),
                'accuracy_trend': accuracy_trend,
                'successful_patterns': successful_patterns,
                'improvement_areas': improvement_areas,
                'analysis_period_days': days,
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Feedback analysis complete: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing feedback data: {str(e)}")
            raise
    
    def _calculate_accuracy_trend(self, feedbacks: List[OptimizationFeedback]) -> str:
        """Calculate if accuracy is improving, declining, or stable"""
        if len(feedbacks) < 10:
            return "insufficient_data"
        
        # Sort by date
        sorted_feedbacks = sorted(feedbacks, key=lambda f: f.measured_at)
        
        # Split into first half and second half
        mid = len(sorted_feedbacks) // 2
        first_half = sorted_feedbacks[:mid]
        second_half = sorted_feedbacks[mid:]
        
        avg_first = sum(f.accuracy_score or 0 for f in first_half) / len(first_half)
        avg_second = sum(f.accuracy_score or 0 for f in second_half) / len(second_half)
        
        diff = avg_second - avg_first
        
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"
    
    def _identify_successful_patterns(
        self,
        feedbacks: List[OptimizationFeedback]
    ) -> List[Dict]:
        """Identify patterns in successful optimizations"""
        successful = [f for f in feedbacks if f.feedback_status == 'success']
        
        if not successful:
            return []
        
        patterns = []
        
        # Group by optimization characteristics
        # This is a simplified version - in production, you'd use more sophisticated pattern matching
        for feedback in successful[:10]:  # Top 10 successful
            optimization = self.db.query(Optimization).filter(
                Optimization.id == feedback.optimization_id
            ).first()
            
            if optimization:
                patterns.append({
                    'optimization_id': optimization.id,
                    'improvement_pct': feedback.actual_improvement_pct,
                    'accuracy_score': feedback.accuracy_score,
                    'has_execution_plan': optimization.execution_plan is not None
                })
        
        return patterns
    
    def _identify_improvement_areas(
        self,
        feedbacks: List[OptimizationFeedback]
    ) -> List[str]:
        """Identify areas where the model needs improvement"""
        areas = []
        
        # Check for consistent overestimation
        overestimations = [
            f for f in feedbacks
            if f.estimated_improvement_pct and f.actual_improvement_pct
            and f.estimated_improvement_pct > f.actual_improvement_pct + 10
        ]
        
        if len(overestimations) > len(feedbacks) * 0.3:
            areas.append("Consistently overestimating improvements")
        
        # Check for consistent underestimation
        underestimations = [
            f for f in feedbacks
            if f.estimated_improvement_pct and f.actual_improvement_pct
            and f.actual_improvement_pct > f.estimated_improvement_pct + 10
        ]
        
        if len(underestimations) > len(feedbacks) * 0.3:
            areas.append("Consistently underestimating improvements")
        
        # Check for low accuracy
        low_accuracy = [f for f in feedbacks if (f.accuracy_score or 0) < 50]
        if len(low_accuracy) > len(feedbacks) * 0.3:
            areas.append("Low overall accuracy - needs more training data")
        
        # Check for failed optimizations
        failed = [f for f in feedbacks if f.feedback_status == 'failed']
        if len(failed) > len(feedbacks) * 0.2:
            areas.append("High failure rate - review optimization logic")
        
        return areas if areas else ["No major issues identified"]
    
    def calculate_model_accuracy(
        self,
        connection_id: Optional[int] = None,
        days: int = 30
    ) -> float:
        """
        Calculate overall model accuracy
        
        Args:
            connection_id: Optional connection ID to filter by
            days: Number of days to consider
            
        Returns:
            Accuracy percentage (0-100)
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = self.db.query(OptimizationFeedback).filter(
                OptimizationFeedback.measured_at >= start_date
            )
            
            if connection_id:
                query = query.filter(OptimizationFeedback.connection_id == connection_id)
            
            feedbacks = query.all()
            
            if not feedbacks:
                return 0.0
            
            total_accuracy = sum(f.accuracy_score or 0 for f in feedbacks)
            avg_accuracy = total_accuracy / len(feedbacks)
            
            return round(avg_accuracy, 2)
            
        except Exception as e:
            logger.error(f"Error calculating model accuracy: {str(e)}")
            return 0.0
    
    async def identify_successful_patterns(
        self,
        min_success_rate: float = 0.7,
        min_applications: int = 3
    ) -> List[Dict]:
        """
        Identify successful optimization patterns
        
        Args:
            min_success_rate: Minimum success rate (0-1)
            min_applications: Minimum number of times pattern was applied
            
        Returns:
            List of successful patterns
        """
        try:
            logger.info("Identifying successful optimization patterns")
            
            # Get all patterns with sufficient applications
            patterns = self.db.query(OptimizationPattern).filter(
                OptimizationPattern.times_applied >= min_applications
            ).all()
            
            successful_patterns = []
            
            for pattern in patterns:
                success_rate = (
                    pattern.times_successful / pattern.times_applied
                    if pattern.times_applied > 0 else 0
                )
                
                if success_rate >= min_success_rate:
                    successful_patterns.append({
                        'id': pattern.id,
                        'pattern_type': pattern.pattern_type,
                        'pattern_signature': pattern.pattern_signature,
                        'success_rate': round(success_rate * 100, 2),
                        'avg_improvement_pct': pattern.avg_improvement_pct,
                        'times_applied': pattern.times_applied,
                        'times_successful': pattern.times_successful,
                        'database_type': pattern.database_type,
                        'created_at': pattern.created_at.isoformat()
                    })
            
            # Sort by success rate and improvement
            successful_patterns.sort(
                key=lambda p: (p['success_rate'], p['avg_improvement_pct']),
                reverse=True
            )
            
            logger.info(f"Found {len(successful_patterns)} successful patterns")
            return successful_patterns
            
        except Exception as e:
            logger.error(f"Error identifying successful patterns: {str(e)}")
            return []
    
    async def update_pattern_success_rates(self) -> Dict:
        """
        Update success rates for all patterns based on recent feedback
        
        Returns:
            Dictionary with update statistics
        """
        try:
            logger.info("Updating pattern success rates")
            
            patterns = self.db.query(OptimizationPattern).all()
            updated_count = 0
            
            for pattern in patterns:
                # Get optimizations that used this pattern
                # This is simplified - in production, you'd track pattern usage
                optimizations = self.db.query(Optimization).filter(
                    Optimization.created_at >= pattern.created_at
                ).all()
                
                if not optimizations:
                    continue
                
                # Get feedback for these optimizations
                optimization_ids = [o.id for o in optimizations]
                feedbacks = self.db.query(OptimizationFeedback).filter(
                    OptimizationFeedback.optimization_id.in_(optimization_ids)
                ).all()
                
                if feedbacks:
                    successful = sum(
                        1 for f in feedbacks
                        if f.feedback_status == 'success'
                    )
                    
                    avg_improvement = sum(
                        f.actual_improvement_pct or 0 for f in feedbacks
                    ) / len(feedbacks)
                    
                    # Update pattern
                    pattern.times_applied = len(feedbacks)
                    pattern.times_successful = successful
                    pattern.success_rate = successful / len(feedbacks) if len(feedbacks) > 0 else 0
                    pattern.avg_improvement_pct = avg_improvement
                    pattern.updated_at = datetime.utcnow()
                    
                    updated_count += 1
            
            self.db.commit()
            
            result = {
                'patterns_updated': updated_count,
                'total_patterns': len(patterns),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Pattern update complete: {result}")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating pattern success rates: {str(e)}")
            raise
    
    async def generate_improvement_report(
        self,
        connection_id: Optional[int] = None,
        days: int = 30
    ) -> Dict:
        """
        Generate comprehensive improvement report
        
        Args:
            connection_id: Optional connection ID to filter by
            days: Number of days to analyze
            
        Returns:
            Dictionary with improvement report
        """
        try:
            logger.info("Generating improvement report")
            
            # Analyze feedback
            analysis = await self.analyze_feedback_data(connection_id, days)
            
            # Get model accuracy
            accuracy = self.calculate_model_accuracy(connection_id, days)
            
            # Get successful patterns
            patterns = await self.identify_successful_patterns()
            
            # Calculate improvement over time
            start_date = datetime.utcnow() - timedelta(days=days)
            mid_date = datetime.utcnow() - timedelta(days=days//2)
            
            # First half accuracy
            first_half = self.db.query(OptimizationFeedback).filter(
                and_(
                    OptimizationFeedback.measured_at >= start_date,
                    OptimizationFeedback.measured_at < mid_date
                )
            )
            if connection_id:
                first_half = first_half.filter(
                    OptimizationFeedback.connection_id == connection_id
                )
            first_half_feedbacks = first_half.all()
            
            # Second half accuracy
            second_half = self.db.query(OptimizationFeedback).filter(
                OptimizationFeedback.measured_at >= mid_date
            )
            if connection_id:
                second_half = second_half.filter(
                    OptimizationFeedback.connection_id == connection_id
                )
            second_half_feedbacks = second_half.all()
            
            first_accuracy = (
                sum(f.accuracy_score or 0 for f in first_half_feedbacks) / len(first_half_feedbacks)
                if first_half_feedbacks else 0
            )
            second_accuracy = (
                sum(f.accuracy_score or 0 for f in second_half_feedbacks) / len(second_half_feedbacks)
                if second_half_feedbacks else 0
            )
            
            accuracy_improvement = second_accuracy - first_accuracy
            
            report = {
                'summary': {
                    'current_accuracy': accuracy,
                    'accuracy_improvement': round(accuracy_improvement, 2),
                    'total_feedback': analysis['total_feedback'],
                    'success_rate': analysis['success_rate'],
                    'analysis_period_days': days
                },
                'feedback_analysis': analysis,
                'successful_patterns': patterns[:10],  # Top 10
                'recommendations': self._generate_recommendations(analysis, accuracy),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info("Improvement report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating improvement report: {str(e)}")
            raise
    
    def _generate_recommendations(
        self,
        analysis: Dict,
        accuracy: float
    ) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Check accuracy
        if accuracy < 70:
            recommendations.append(
                "Model accuracy is below 70%. Collect more feedback data to improve predictions."
            )
        elif accuracy > 90:
            recommendations.append(
                "Excellent model accuracy! Continue monitoring and collecting feedback."
            )
        
        # Check success rate
        success_rate = analysis.get('success_rate', 0)
        if success_rate < 60:
            recommendations.append(
                "Success rate is below 60%. Review failed optimizations and adjust strategies."
            )
        
        # Check estimation bias
        bias = analysis.get('estimation_bias', 0)
        if abs(bias) > 10:
            if bias > 0:
                recommendations.append(
                    f"Model is overestimating improvements by {bias:.1f}%. Adjust estimation algorithms."
                )
            else:
                recommendations.append(
                    f"Model is underestimating improvements by {abs(bias):.1f}%. Adjust estimation algorithms."
                )
        
        # Check trend
        trend = analysis.get('accuracy_trend', 'unknown')
        if trend == 'declining':
            recommendations.append(
                "Accuracy is declining. Review recent changes and consider model retraining."
            )
        elif trend == 'improving':
            recommendations.append(
                "Accuracy is improving! Current approach is working well."
            )
        
        # Check improvement areas
        improvement_areas = analysis.get('improvement_areas', [])
        for area in improvement_areas:
            if area != "No major issues identified":
                recommendations.append(f"Action needed: {area}")
        
        if not recommendations:
            recommendations.append(
                "Model is performing well. Continue monitoring and collecting feedback."
            )
        
        return recommendations
    
    def get_accuracy_trend(
        self,
        connection_id: Optional[int] = None,
        days: int = 30
    ) -> List[Dict]:
        """
        Get accuracy trend over time
        
        Args:
            connection_id: Optional connection ID to filter by
            days: Number of days to analyze
            
        Returns:
            List of daily accuracy data points
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = self.db.query(OptimizationFeedback).filter(
                OptimizationFeedback.measured_at >= start_date
            )
            
            if connection_id:
                query = query.filter(
                    OptimizationFeedback.connection_id == connection_id
                )
            
            feedbacks = query.order_by(OptimizationFeedback.measured_at).all()
            
            if not feedbacks:
                return []
            
            # Group by day
            daily_data = {}
            for feedback in feedbacks:
                date_key = feedback.measured_at.date().isoformat()
                
                if date_key not in daily_data:
                    daily_data[date_key] = {
                        'date': date_key,
                        'accuracy_scores': [],
                        'improvement_scores': []
                    }
                
                daily_data[date_key]['accuracy_scores'].append(
                    feedback.accuracy_score or 0
                )
                daily_data[date_key]['improvement_scores'].append(
                    feedback.actual_improvement_pct or 0
                )
            
            # Calculate daily averages
            trend_data = []
            for date_key, data in sorted(daily_data.items()):
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
            return []
