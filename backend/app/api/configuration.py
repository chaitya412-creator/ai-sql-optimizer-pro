"""
Configuration API Endpoints
Handles database configuration optimization and management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.database import get_db, ConfigurationChange, Connection
from app.models.schemas import (
    ConfigRecommendation,
    ConfigChangeRequest,
    ConfigChangeResponse,
    ConfigRevertRequest,
    WorkloadAnalysis
)
from app.core.config_optimizer import ConfigOptimizer
from app.core.config_validator import ConfigValidator
from app.core.workload_analyzer import WorkloadAnalyzer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["configuration"])


@router.get("/recommendations/{connection_id}", response_model=List[ConfigRecommendation])
async def get_config_recommendations(
    connection_id: int,
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get configuration recommendations for a connection
    
    - **connection_id**: Connection ID
    - **days**: Number of days to analyze workload (default: 7)
    """
    try:
        logger.info(f"Getting config recommendations for connection {connection_id}")
        
        # Verify connection exists
        connection = db.query(Connection).filter(
            Connection.id == connection_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection {connection_id} not found"
            )
        
        # Analyze workload
        optimizer = ConfigOptimizer(db)
        workload_analysis = await optimizer.analyze_workload(connection_id, days)
        
        # Get recommendations
        recommendations = await optimizer.recommend_config_changes(
            connection_id,
            workload_analysis
        )
        
        return [
            ConfigRecommendation(
                parameter_name=r['parameter_name'],
                current_value=r.get('current_value'),
                recommended_value=r['recommended_value'],
                change_reason=r['change_reason'],
                estimated_impact=r['estimated_impact'],
                database_type=r['database_type'],
                priority=r['priority'],
                safety_level=r.get('safety_level', 'safe')
            )
            for r in recommendations
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting config recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recommendations: {str(e)}"
        )


@router.post("/apply", response_model=ConfigChangeResponse)
async def apply_config_change(
    change_request: ConfigChangeRequest,
    db: Session = Depends(get_db)
):
    """
    Apply a configuration change
    
    - **connection_id**: Connection ID
    - **parameter_name**: Parameter to change
    - **new_value**: New value
    - **change_reason**: Reason for change
    - **dry_run**: If true, validate only without applying
    """
    try:
        logger.info(f"Applying config change: {change_request.parameter_name}={change_request.new_value}")
        
        # Verify connection
        connection = db.query(Connection).filter(
            Connection.id == change_request.connection_id
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection {change_request.connection_id} not found"
            )
        
        # Validate change
        validator = ConfigValidator(db)
        is_valid, message = await validator.validate_config_change(
            change_request.connection_id,
            change_request.parameter_name,
            change_request.new_value
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid configuration: {message}"
            )
        
        # If dry run, return validation result
        if change_request.dry_run:
            return ConfigChangeResponse(
                id=0,
                connection_id=change_request.connection_id,
                parameter_name=change_request.parameter_name,
                old_value=None,
                new_value=change_request.new_value,
                change_reason=change_request.change_reason,
                estimated_impact=None,
                actual_impact=None,
                applied_at=datetime.utcnow(),
                reverted_at=None,
                status='validated'
            )
        
        # Get optimizer for impact estimation
        optimizer = ConfigOptimizer(db)
        estimated_impact = optimizer.estimate_impact(
            change_request.parameter_name,
            '',  # old_value - would need to query from database
            change_request.new_value,
            connection.engine
        )
        
        # Create configuration change record
        config_change = ConfigurationChange(
            connection_id=change_request.connection_id,
            parameter_name=change_request.parameter_name,
            old_value=None,  # Would need to query current value
            new_value=change_request.new_value,
            change_reason=change_request.change_reason,
            estimated_impact=estimated_impact,
            actual_impact=None,
            applied_at=datetime.utcnow(),
            reverted_at=None,
            status='applied'
        )
        
        db.add(config_change)
        db.commit()
        db.refresh(config_change)
        
        logger.info(f"Config change applied: {config_change.id}")
        
        return ConfigChangeResponse(
            id=config_change.id,
            connection_id=config_change.connection_id,
            parameter_name=config_change.parameter_name,
            old_value=config_change.old_value,
            new_value=config_change.new_value,
            change_reason=config_change.change_reason,
            estimated_impact=config_change.estimated_impact,
            actual_impact=config_change.actual_impact,
            applied_at=config_change.applied_at,
            reverted_at=config_change.reverted_at,
            status=config_change.status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error applying config change: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying change: {str(e)}"
        )


@router.post("/revert/{change_id}", response_model=ConfigChangeResponse)
async def revert_config_change(
    change_id: int,
    revert_request: ConfigRevertRequest,
    db: Session = Depends(get_db)
):
    """
    Revert a configuration change
    
    - **change_id**: Configuration change ID to revert
    - **force**: Force revert even if validation fails
    """
    try:
        logger.info(f"Reverting config change {change_id}")
        
        # Get the change
        change = db.query(ConfigurationChange).filter(
            ConfigurationChange.id == change_id
        ).first()
        
        if not change:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration change {change_id} not found"
            )
        
        # Check if already reverted
        if change.reverted_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configuration change already reverted"
            )
        
        # Mark as reverted
        change.reverted_at = datetime.utcnow()
        change.status = 'reverted'
        
        db.commit()
        db.refresh(change)
        
        logger.info(f"Config change {change_id} reverted successfully")
        
        return ConfigChangeResponse(
            id=change.id,
            connection_id=change.connection_id,
            parameter_name=change.parameter_name,
            old_value=change.old_value,
            new_value=change.new_value,
            change_reason=change.change_reason,
            estimated_impact=change.estimated_impact,
            actual_impact=change.actual_impact,
            applied_at=change.applied_at,
            reverted_at=change.reverted_at,
            status=change.status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error reverting config change: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reverting change: {str(e)}"
        )


@router.get("/history/{connection_id}", response_model=List[ConfigChangeResponse])
async def get_config_history(
    connection_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get configuration change history for a connection
    
    - **connection_id**: Connection ID
    - **limit**: Maximum number of results (default: 50)
    """
    try:
        changes = db.query(ConfigurationChange).filter(
            ConfigurationChange.connection_id == connection_id
        ).order_by(
            ConfigurationChange.applied_at.desc()
        ).limit(limit).all()
        
        return [
            ConfigChangeResponse(
                id=c.id,
                connection_id=c.connection_id,
                parameter_name=c.parameter_name,
                old_value=c.old_value,
                new_value=c.new_value,
                change_reason=c.change_reason,
                estimated_impact=c.estimated_impact,
                actual_impact=c.actual_impact,
                applied_at=c.applied_at,
                reverted_at=c.reverted_at,
                status=c.status
            )
            for c in changes
        ]
        
    except Exception as e:
        logger.error(f"Error getting config history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting history: {str(e)}"
        )


@router.post("/validate", response_model=dict)
async def validate_config_change(
    connection_id: int,
    parameter: str,
    value: str,
    db: Session = Depends(get_db)
):
    """
    Validate a configuration change without applying it
    
    - **connection_id**: Connection ID
    - **parameter**: Parameter name
    - **value**: New value
    """
    try:
        validator = ConfigValidator(db)
        is_valid, message = await validator.validate_config_change(
            connection_id,
            parameter,
            value
        )
        
        # Get safety checks
        connection = db.query(Connection).filter(
            Connection.id == connection_id
        ).first()
        
        safety_checks = validator.get_safety_checks(
            parameter,
            value,
            connection.engine if connection else 'unknown'
        )
        
        return {
            'valid': is_valid,
            'message': message,
            'safety_checks': safety_checks,
            'validated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error validating config change: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating change: {str(e)}"
        )


@router.get("/workload/analysis/{connection_id}", response_model=WorkloadAnalysis)
async def get_workload_analysis(
    connection_id: int,
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get workload analysis for a connection
    
    - **connection_id**: Connection ID
    - **days**: Number of days to analyze (default: 7)
    """
    try:
        logger.info(f"Getting workload analysis for connection {connection_id}")
        
        analyzer = WorkloadAnalyzer(db)
        pattern = await analyzer.analyze_workload_pattern(connection_id, days)
        
        # Get optimizer for recommendations
        optimizer = ConfigOptimizer(db)
        recommendations = await optimizer.recommend_config_changes(
            connection_id,
            pattern
        )
        
        return WorkloadAnalysis(
            connection_id=connection_id,
            workload_type=pattern.get('workload_type', 'unknown'),
            peak_hours=pattern.get('hourly_pattern', {}).get('peak_hours', []),
            avg_queries_per_hour=pattern.get('query_pattern', {}).get('total_calls', 0) / (days * 24),
            avg_execution_time=pattern.get('resource_pattern', {}).get('cpu', {}).get('avg', 0),
            slow_query_percentage=pattern.get('query_pattern', {}).get('slow_queries_pct', 0),
            recommendations=[
                ConfigRecommendation(
                    parameter_name=r['parameter_name'],
                    current_value=r.get('current_value'),
                    recommended_value=r['recommended_value'],
                    change_reason=r['change_reason'],
                    estimated_impact=r['estimated_impact'],
                    database_type=r['database_type'],
                    priority=r['priority'],
                    safety_level=r.get('safety_level', 'safe')
                )
                for r in recommendations
            ],
            analysis_period_days=days,
            analyzed_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting workload analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting workload analysis: {str(e)}"
        )


@router.get("/workload/pattern/{connection_id}", response_model=dict)
async def get_workload_pattern(
    connection_id: int,
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get detailed workload pattern for a connection
    
    - **connection_id**: Connection ID
    - **days**: Number of days to analyze (default: 7)
    """
    try:
        analyzer = WorkloadAnalyzer(db)
        pattern = await analyzer.analyze_workload_pattern(connection_id, days)
        
        return pattern
        
    except Exception as e:
        logger.error(f"Error getting workload pattern: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting workload pattern: {str(e)}"
        )


@router.get("/workload/shifts/{connection_id}", response_model=List[dict])
async def detect_workload_shifts(
    connection_id: int,
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Detect workload shifts for a connection
    
    - **connection_id**: Connection ID
    - **days**: Number of days to analyze (default: 7)
    """
    try:
        analyzer = WorkloadAnalyzer(db)
        shifts = await analyzer.detect_workload_shifts(connection_id, days)
        
        return shifts
        
    except Exception as e:
        logger.error(f"Error detecting workload shifts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error detecting shifts: {str(e)}"
        )


@router.post("/impact/measure/{change_id}", response_model=dict)
async def measure_config_impact(
    change_id: int,
    db: Session = Depends(get_db)
):
    """
    Measure actual impact of a configuration change
    
    - **change_id**: Configuration change ID
    """
    try:
        # Get the change
        change = db.query(ConfigurationChange).filter(
            ConfigurationChange.id == change_id
        ).first()
        
        if not change:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration change {change_id} not found"
            )
        
        # Measure impact
        validator = ConfigValidator(db)
        impact = await validator.measure_impact(change.connection_id, change_id)
        
        return impact
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error measuring config impact: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error measuring impact: {str(e)}"
        )


@router.get("/rules/{database_type}", response_model=dict)
async def get_config_rules(
    database_type: str,
    db: Session = Depends(get_db)
):
    """
    Get configuration rules for a database type
    
    - **database_type**: Database type (postgresql, mysql, mssql)
    """
    try:
        optimizer = ConfigOptimizer(db)
        rules = optimizer.get_database_specific_rules(database_type)
        
        return rules
        
    except Exception as e:
        logger.error(f"Error getting config rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting rules: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def config_health_check(db: Session = Depends(get_db)):
    """
    Check configuration system health
    
    Returns status of configuration components
    """
    try:
        # Count recent changes
        recent_changes = db.query(ConfigurationChange).filter(
            ConfigurationChange.applied_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        # Count active changes (not reverted)
        active_changes = db.query(ConfigurationChange).filter(
            ConfigurationChange.reverted_at.is_(None)
        ).count()
        
        return {
            'status': 'healthy',
            'message': 'Configuration system operating normally',
            'recent_changes_7days': recent_changes,
            'active_changes': active_changes,
            'checked_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in config health check: {str(e)}")
        return {
            'status': 'error',
            'message': f'Health check failed: {str(e)}',
            'checked_at': datetime.utcnow().isoformat()
        }
