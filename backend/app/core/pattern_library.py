"""
Pattern Library Module
Enhanced pattern management and browsing system
"""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from loguru import logger

from app.models.database import OptimizationPattern


class PatternLibrary:
    """Enhanced pattern library for browsing and managing optimization patterns"""
    
    # Pattern categories
    CATEGORIES = {
        'JOIN_OPTIMIZATION': 'Join Optimization',
        'SUBQUERY_OPTIMIZATION': 'Subquery Optimization',
        'INDEX_RECOMMENDATION': 'Index Recommendation',
        'QUERY_REWRITE': 'Query Rewrite',
        'AGGREGATION_OPTIMIZATION': 'Aggregation Optimization',
        'WINDOW_FUNCTION': 'Window Function',
        'CTE_OPTIMIZATION': 'CTE Optimization',
        'ANTI_PATTERN': 'Anti-Pattern Detection'
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all_patterns(
        self,
        database_type: Optional[str] = None,
        pattern_type: Optional[str] = None,
        category: Optional[str] = None,
        min_success_rate: Optional[float] = None,
        min_applications: Optional[int] = None,
        sort_by: str = 'success_rate',
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get all patterns with optional filters
        
        Args:
            database_type: Filter by database type
            pattern_type: Filter by pattern type
            category: Filter by category
            min_success_rate: Minimum success rate (0-1)
            min_applications: Minimum times applied
            sort_by: Sort field (success_rate, improvement, applications, created_at)
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of pattern dictionaries
        """
        try:
            logger.info(f"Getting patterns with filters: db={database_type}, type={pattern_type}")
            
            # Build query
            query = select(OptimizationPattern)
            
            # Apply filters
            conditions = []
            
            if database_type:
                conditions.append(OptimizationPattern.database_type == database_type)
            
            if pattern_type:
                conditions.append(OptimizationPattern.pattern_type == pattern_type)
            
            if min_success_rate is not None:
                conditions.append(OptimizationPattern.success_rate >= min_success_rate)
            
            if min_applications is not None:
                conditions.append(OptimizationPattern.times_applied >= min_applications)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Apply sorting
            if sort_by == 'success_rate':
                query = query.order_by(OptimizationPattern.success_rate.desc())
            elif sort_by == 'improvement':
                query = query.order_by(OptimizationPattern.avg_improvement_pct.desc())
            elif sort_by == 'applications':
                query = query.order_by(OptimizationPattern.times_applied.desc())
            elif sort_by == 'created_at':
                query = query.order_by(OptimizationPattern.created_at.desc())
            else:
                query = query.order_by(OptimizationPattern.success_rate.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = await self.db.execute(query)
            patterns = result.scalars().all()
            
            # Convert to dictionaries with category
            pattern_list = []
            for pattern in patterns:
                pattern_dict = {
                    'id': pattern.id,
                    'pattern_type': pattern.pattern_type,
                    'pattern_signature': pattern.pattern_signature,
                    'original_pattern': pattern.original_pattern,
                    'optimized_pattern': pattern.optimized_pattern,
                    'success_rate': round(pattern.success_rate * 100, 2),
                    'avg_improvement_pct': round(pattern.avg_improvement_pct, 2),
                    'times_applied': pattern.times_applied,
                    'times_successful': pattern.times_successful,
                    'database_type': pattern.database_type,
                    'category': self._categorize_pattern(pattern),
                    'created_at': pattern.created_at.isoformat(),
                    'updated_at': pattern.updated_at.isoformat()
                }
                pattern_list.append(pattern_dict)
            
            logger.info(f"Retrieved {len(pattern_list)} patterns")
            return pattern_list
            
        except Exception as e:
            logger.error(f"Error getting patterns: {e}")
            return []
    
    async def get_pattern_by_id(self, pattern_id: int) -> Optional[Dict]:
        """
        Get detailed information about a specific pattern
        
        Args:
            pattern_id: Pattern ID
            
        Returns:
            Pattern dictionary or None
        """
        try:
            pattern = await self.db.get(OptimizationPattern, pattern_id)
            
            if not pattern:
                logger.warning(f"Pattern {pattern_id} not found")
                return None
            
            return {
                'id': pattern.id,
                'pattern_type': pattern.pattern_type,
                'pattern_signature': pattern.pattern_signature,
                'original_pattern': pattern.original_pattern,
                'optimized_pattern': pattern.optimized_pattern,
                'success_rate': round(pattern.success_rate * 100, 2),
                'avg_improvement_pct': round(pattern.avg_improvement_pct, 2),
                'times_applied': pattern.times_applied,
                'times_successful': pattern.times_successful,
                'database_type': pattern.database_type,
                'category': self._categorize_pattern(pattern),
                'created_at': pattern.created_at.isoformat(),
                'updated_at': pattern.updated_at.isoformat(),
                'description': self._generate_description(pattern)
            }
            
        except Exception as e:
            logger.error(f"Error getting pattern {pattern_id}: {e}")
            return None
    
    async def search_patterns(
        self,
        query: str,
        database_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search patterns by query string
        
        Args:
            query: Search query
            database_type: Optional database type filter
            category: Optional category filter
            limit: Maximum results
            
        Returns:
            List of matching patterns
        """
        try:
            logger.info(f"Searching patterns for: {query}")
            
            # Build search conditions
            search_term = f"%{query.upper()}%"
            
            conditions = [
                or_(
                    OptimizationPattern.pattern_signature.ilike(search_term),
                    OptimizationPattern.original_pattern.ilike(search_term),
                    OptimizationPattern.optimized_pattern.ilike(search_term),
                    OptimizationPattern.pattern_type.ilike(search_term)
                )
            ]
            
            if database_type:
                conditions.append(OptimizationPattern.database_type == database_type)
            
            # Execute search
            result = await self.db.execute(
                select(OptimizationPattern)
                .where(and_(*conditions))
                .order_by(OptimizationPattern.success_rate.desc())
                .limit(limit)
            )
            patterns = result.scalars().all()
            
            # Filter by category if specified
            pattern_list = []
            for pattern in patterns:
                pattern_category = self._categorize_pattern(pattern)
                if category and pattern_category != category:
                    continue
                
                pattern_list.append({
                    'id': pattern.id,
                    'pattern_type': pattern.pattern_type,
                    'pattern_signature': pattern.pattern_signature,
                    'original_pattern': pattern.original_pattern[:200] + '...' if len(pattern.original_pattern) > 200 else pattern.original_pattern,
                    'optimized_pattern': pattern.optimized_pattern[:200] + '...' if len(pattern.optimized_pattern) > 200 else pattern.optimized_pattern,
                    'success_rate': round(pattern.success_rate * 100, 2),
                    'avg_improvement_pct': round(pattern.avg_improvement_pct, 2),
                    'times_applied': pattern.times_applied,
                    'database_type': pattern.database_type,
                    'category': pattern_category
                })
            
            logger.info(f"Found {len(pattern_list)} matching patterns")
            return pattern_list
            
        except Exception as e:
            logger.error(f"Error searching patterns: {e}")
            return []
    
    async def get_patterns_by_category(
        self,
        category: str,
        database_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get patterns by category
        
        Args:
            category: Pattern category
            database_type: Optional database type filter
            limit: Maximum results
            
        Returns:
            List of patterns in category
        """
        try:
            # Get all patterns and filter by category
            all_patterns = await self.get_all_patterns(
                database_type=database_type,
                limit=1000  # Get more to filter
            )
            
            # Filter by category
            category_patterns = [
                p for p in all_patterns
                if p.get('category') == category
            ]
            
            # Limit results
            return category_patterns[:limit]
            
        except Exception as e:
            logger.error(f"Error getting patterns by category: {e}")
            return []
    
    async def get_categories(self) -> List[Dict]:
        """
        Get all pattern categories with counts
        
        Returns:
            List of category dictionaries
        """
        try:
            # Get all patterns
            result = await self.db.execute(select(OptimizationPattern))
            patterns = result.scalars().all()
            
            # Count by category
            category_counts = {}
            category_success_rates = {}
            
            for pattern in patterns:
                category = self._categorize_pattern(pattern)
                
                if category not in category_counts:
                    category_counts[category] = 0
                    category_success_rates[category] = []
                
                category_counts[category] += 1
                category_success_rates[category].append(pattern.success_rate)
            
            # Build category list
            categories = []
            for cat_key, cat_name in self.CATEGORIES.items():
                count = category_counts.get(cat_key, 0)
                success_rates = category_success_rates.get(cat_key, [])
                avg_success = sum(success_rates) / len(success_rates) if success_rates else 0
                
                categories.append({
                    'name': cat_key,
                    'display_name': cat_name,
                    'count': count,
                    'avg_success_rate': round(avg_success * 100, 2),
                    'description': self._get_category_description(cat_key)
                })
            
            # Sort by count
            categories.sort(key=lambda x: x['count'], reverse=True)
            
            return categories
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    async def get_pattern_statistics(self) -> Dict:
        """
        Get overall pattern library statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            # Count total patterns
            total_result = await self.db.execute(
                select(func.count(OptimizationPattern.id))
            )
            total_patterns = total_result.scalar()
            
            # Count by database type
            db_result = await self.db.execute(
                select(
                    OptimizationPattern.database_type,
                    func.count(OptimizationPattern.id)
                ).group_by(OptimizationPattern.database_type)
            )
            by_database = {row[0]: row[1] for row in db_result.all()}
            
            # Calculate averages
            avg_result = await self.db.execute(
                select(
                    func.avg(OptimizationPattern.success_rate),
                    func.sum(OptimizationPattern.times_applied),
                    func.sum(OptimizationPattern.times_successful)
                )
            )
            avg_row = avg_result.first()
            
            avg_success_rate = avg_row[0] if avg_row[0] else 0
            total_applications = avg_row[1] if avg_row[1] else 0
            total_successful = avg_row[2] if avg_row[2] else 0
            
            # Get category counts
            all_patterns = await self.db.execute(select(OptimizationPattern))
            patterns = all_patterns.scalars().all()
            
            by_category = {}
            for pattern in patterns:
                category = self._categorize_pattern(pattern)
                by_category[category] = by_category.get(category, 0) + 1
            
            return {
                'total_patterns': total_patterns,
                'by_database': by_database,
                'by_category': by_category,
                'avg_success_rate': round(avg_success_rate * 100, 2),
                'total_applications': total_applications,
                'total_successful': total_successful,
                'overall_success_rate': round((total_successful / total_applications * 100) if total_applications > 0 else 0, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                'total_patterns': 0,
                'by_database': {},
                'by_category': {},
                'avg_success_rate': 0,
                'total_applications': 0,
                'total_successful': 0,
                'overall_success_rate': 0
            }
    
    async def get_top_patterns(
        self,
        limit: int = 10,
        database_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get top performing patterns
        
        Args:
            limit: Maximum results
            database_type: Optional database type filter
            
        Returns:
            List of top patterns
        """
        try:
            query = select(OptimizationPattern).where(
                OptimizationPattern.times_applied >= 3  # Minimum applications
            )
            
            if database_type:
                query = query.where(OptimizationPattern.database_type == database_type)
            
            query = query.order_by(
                OptimizationPattern.success_rate.desc(),
                OptimizationPattern.avg_improvement_pct.desc()
            ).limit(limit)
            
            result = await self.db.execute(query)
            patterns = result.scalars().all()
            
            return [
                {
                    'id': p.id,
                    'pattern_type': p.pattern_type,
                    'pattern_signature': p.pattern_signature,
                    'success_rate': round(p.success_rate * 100, 2),
                    'avg_improvement_pct': round(p.avg_improvement_pct, 2),
                    'times_applied': p.times_applied,
                    'times_successful': p.times_successful,
                    'database_type': p.database_type,
                    'category': self._categorize_pattern(p)
                }
                for p in patterns
            ]
            
        except Exception as e:
            logger.error(f"Error getting top patterns: {e}")
            return []
    
    def _categorize_pattern(self, pattern: OptimizationPattern) -> str:
        """Categorize a pattern based on its characteristics"""
        signature = pattern.pattern_signature.upper()
        original = pattern.original_pattern.upper()
        pattern_type = pattern.pattern_type.upper()
        
        # Check for specific patterns
        if 'JOIN' in signature or 'JOIN' in original:
            return 'JOIN_OPTIMIZATION'
        elif 'SUBQUERY' in signature or 'SELECT' in original and original.count('SELECT') > 1:
            return 'SUBQUERY_OPTIMIZATION'
        elif pattern_type == 'INDEX' or 'INDEX' in pattern_type:
            return 'INDEX_RECOMMENDATION'
        elif 'GROUP_BY' in signature or 'GROUP BY' in original:
            return 'AGGREGATION_OPTIMIZATION'
        elif 'WINDOW' in signature or 'OVER' in original:
            return 'WINDOW_FUNCTION'
        elif 'CTE' in signature or 'WITH' in original:
            return 'CTE_OPTIMIZATION'
        elif pattern_type == 'REWRITE':
            return 'QUERY_REWRITE'
        else:
            return 'QUERY_REWRITE'  # Default category
    
    def _get_category_description(self, category: str) -> str:
        """Get description for a category"""
        descriptions = {
            'JOIN_OPTIMIZATION': 'Optimize JOIN operations for better performance',
            'SUBQUERY_OPTIMIZATION': 'Convert subqueries to more efficient forms',
            'INDEX_RECOMMENDATION': 'Suggest indexes to improve query performance',
            'QUERY_REWRITE': 'Rewrite queries for better execution plans',
            'AGGREGATION_OPTIMIZATION': 'Optimize GROUP BY and aggregation queries',
            'WINDOW_FUNCTION': 'Optimize window function usage',
            'CTE_OPTIMIZATION': 'Optimize Common Table Expressions',
            'ANTI_PATTERN': 'Detect and fix common anti-patterns'
        }
        return descriptions.get(category, 'General optimization patterns')
    
    def _generate_description(self, pattern: OptimizationPattern) -> str:
        """Generate a human-readable description of the pattern"""
        category = self._categorize_pattern(pattern)
        success_rate = round(pattern.success_rate * 100, 2)
        improvement = round(pattern.avg_improvement_pct, 2)
        
        return (
            f"This {category.replace('_', ' ').lower()} pattern has been successfully "
            f"applied {pattern.times_successful} out of {pattern.times_applied} times "
            f"({success_rate}% success rate), achieving an average performance "
            f"improvement of {improvement}%."
        )
    
    async def load_common_patterns(self) -> int:
        """
        Load common optimization patterns into the library
        
        Returns:
            Number of patterns loaded
        """
        try:
            logger.info("Loading common patterns")
            
            common_patterns = self._get_common_patterns()
            loaded_count = 0
            
            for pattern_data in common_patterns:
                # Check if pattern already exists
                result = await self.db.execute(
                    select(OptimizationPattern).where(
                        and_(
                            OptimizationPattern.pattern_signature == pattern_data['signature'],
                            OptimizationPattern.database_type == pattern_data['database_type']
                        )
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    pattern = OptimizationPattern(
                        pattern_type=pattern_data['type'],
                        pattern_signature=pattern_data['signature'],
                        original_pattern=pattern_data['original'],
                        optimized_pattern=pattern_data['optimized'],
                        success_rate=0.0,
                        avg_improvement_pct=0.0,
                        times_applied=0,
                        times_successful=0,
                        database_type=pattern_data['database_type'],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.db.add(pattern)
                    loaded_count += 1
            
            await self.db.commit()
            logger.info(f"Loaded {loaded_count} common patterns")
            return loaded_count
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error loading common patterns: {e}")
            return 0
    
    def _get_common_patterns(self) -> List[Dict]:
        """Get list of common optimization patterns"""
        return [
            {
                'type': 'rewrite',
                'signature': 'SUBQUERY_TO_JOIN',
                'original': 'SELECT * FROM table1 WHERE id IN (SELECT id FROM table2 WHERE condition)',
                'optimized': 'SELECT t1.* FROM table1 t1 INNER JOIN table2 t2 ON t1.id = t2.id WHERE t2.condition',
                'database_type': 'postgresql'
            },
            {
                'type': 'rewrite',
                'signature': 'EXISTS_INSTEAD_OF_IN',
                'original': 'SELECT * FROM table1 WHERE id IN (SELECT id FROM table2)',
                'optimized': 'SELECT * FROM table1 t1 WHERE EXISTS (SELECT 1 FROM table2 t2 WHERE t2.id = t1.id)',
                'database_type': 'postgresql'
            },
            {
                'type': 'index',
                'signature': 'ADD_WHERE_INDEX',
                'original': 'SELECT * FROM users WHERE email = ?',
                'optimized': 'CREATE INDEX idx_users_email ON users(email); SELECT * FROM users WHERE email = ?',
                'database_type': 'postgresql'
            }
        ]
