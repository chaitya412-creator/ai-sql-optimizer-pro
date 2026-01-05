"""
Pattern Library API Endpoints
Provides endpoints for browsing and managing optimization patterns
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from loguru import logger

from app.models.database import get_db
from app.models.schemas import (
    PatternResponse,
    PatternStatistics,
    PatternCategoryResponse
)
from app.core.pattern_library import PatternLibrary

router = APIRouter()


@router.get("/", response_model=List[PatternResponse])
async def get_all_patterns(
    database_type: Optional[str] = Query(None, description="Filter by database type"),
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_success_rate: Optional[float] = Query(None, ge=0, le=1, description="Minimum success rate (0-1)"),
    min_applications: Optional[int] = Query(None, ge=0, description="Minimum times applied"),
    sort_by: str = Query("success_rate", description="Sort field"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all optimization patterns with optional filters
    
    Query Parameters:
    - database_type: postgresql, mysql, mssql
    - pattern_type: rewrite, index, config, etc.
    - category: JOIN_OPTIMIZATION, SUBQUERY_OPTIMIZATION, etc.
    - min_success_rate: 0.0 to 1.0
    - min_applications: Minimum number of times pattern was applied
    - sort_by: success_rate, improvement, applications, created_at
    - limit: Maximum number of results (1-500)
    - offset: Pagination offset
    """
    try:
        library = PatternLibrary(db)
        patterns = await library.get_all_patterns(
            database_type=database_type,
            pattern_type=pattern_type,
            category=category,
            min_success_rate=min_success_rate,
            min_applications=min_applications,
            sort_by=sort_by,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"Retrieved {len(patterns)} patterns")
        return patterns
        
    except Exception as e:
        logger.error(f"Error getting patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pattern_id}", response_model=PatternResponse)
async def get_pattern_by_id(
    pattern_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific pattern
    
    Args:
        pattern_id: Pattern ID
    """
    try:
        library = PatternLibrary(db)
        pattern = await library.get_pattern_by_id(pattern_id)
        
        if not pattern:
            raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found")
        
        logger.info(f"Retrieved pattern {pattern_id}")
        return pattern
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pattern {pattern_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/query", response_model=List[PatternResponse])
async def search_patterns(
    q: str = Query(..., min_length=1, description="Search query"),
    database_type: Optional[str] = Query(None, description="Filter by database type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search patterns by query string
    
    Searches in:
    - Pattern signature
    - Original SQL
    - Optimized SQL
    - Pattern type
    
    Query Parameters:
    - q: Search query (required)
    - database_type: Optional database filter
    - category: Optional category filter
    - limit: Maximum results (1-200)
    """
    try:
        library = PatternLibrary(db)
        patterns = await library.search_patterns(
            query=q,
            database_type=database_type,
            category=category,
            limit=limit
        )
        
        logger.info(f"Search for '{q}' returned {len(patterns)} results")
        return patterns
        
    except Exception as e:
        logger.error(f"Error searching patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/list", response_model=List[PatternCategoryResponse])
async def get_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all pattern categories with counts and statistics
    
    Returns:
    - Category name and display name
    - Number of patterns in category
    - Average success rate
    - Category description
    """
    try:
        library = PatternLibrary(db)
        categories = await library.get_categories()
        
        logger.info(f"Retrieved {len(categories)} categories")
        return categories
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category/{category_name}", response_model=List[PatternResponse])
async def get_patterns_by_category(
    category_name: str,
    database_type: Optional[str] = Query(None, description="Filter by database type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all patterns in a specific category
    
    Args:
        category_name: Category name (e.g., JOIN_OPTIMIZATION)
    
    Query Parameters:
    - database_type: Optional database filter
    - limit: Maximum results (1-200)
    """
    try:
        library = PatternLibrary(db)
        patterns = await library.get_patterns_by_category(
            category=category_name,
            database_type=database_type,
            limit=limit
        )
        
        logger.info(f"Retrieved {len(patterns)} patterns in category {category_name}")
        return patterns
        
    except Exception as e:
        logger.error(f"Error getting patterns by category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/overview", response_model=PatternStatistics)
async def get_pattern_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall pattern library statistics
    
    Returns:
    - Total number of patterns
    - Patterns by database type
    - Patterns by category
    - Average success rate
    - Total applications and successes
    """
    try:
        library = PatternLibrary(db)
        stats = await library.get_pattern_statistics()
        
        logger.info("Retrieved pattern statistics")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top/performers", response_model=List[PatternResponse])
async def get_top_patterns(
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    database_type: Optional[str] = Query(None, description="Filter by database type"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top performing patterns
    
    Returns patterns with:
    - Highest success rates
    - Best improvement percentages
    - Minimum 3 applications
    
    Query Parameters:
    - limit: Maximum results (1-50)
    - database_type: Optional database filter
    """
    try:
        library = PatternLibrary(db)
        patterns = await library.get_top_patterns(
            limit=limit,
            database_type=database_type
        )
        
        logger.info(f"Retrieved {len(patterns)} top patterns")
        return patterns
        
    except Exception as e:
        logger.error(f"Error getting top patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load-common")
async def load_common_patterns(
    db: AsyncSession = Depends(get_db)
):
    """
    Load common optimization patterns into the library
    
    This endpoint pre-loads a set of well-known optimization patterns
    that can be used as templates for query optimization.
    
    Returns:
    - Number of patterns loaded
    """
    try:
        library = PatternLibrary(db)
        count = await library.load_common_patterns()
        
        logger.info(f"Loaded {count} common patterns")
        return {
            "success": True,
            "patterns_loaded": count,
            "message": f"Successfully loaded {count} common patterns"
        }
        
    except Exception as e:
        logger.error(f"Error loading common patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))
