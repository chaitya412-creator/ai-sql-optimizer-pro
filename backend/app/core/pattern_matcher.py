"""
Pattern Matcher Module
Matches queries to known successful optimization patterns
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import hashlib
import re
import logging

from app.models.database import OptimizationPattern, Optimization, Connection

logger = logging.getLogger(__name__)


class PatternMatcher:
    """Match queries to successful optimization patterns"""
    
    def __init__(self, db: Session):
        self.db = db
        self.confidence_threshold = 0.7  # 70% confidence for pattern matching
    
    def extract_pattern_signature(self, sql: str) -> str:
        """
        Extract a normalized pattern signature from SQL query
        
        Args:
            sql: SQL query string
            
        Returns:
            Pattern signature (normalized SQL)
        """
        try:
            # Normalize SQL for pattern matching
            normalized = sql.upper().strip()
            
            # Remove extra whitespace
            normalized = re.sub(r'\s+', ' ', normalized)
            
            # Replace literal values with placeholders
            # Numbers
            normalized = re.sub(r'\b\d+\b', '?', normalized)
            
            # String literals
            normalized = re.sub(r"'[^']*'", '?', normalized)
            
            # IN clauses with multiple values
            normalized = re.sub(r'IN\s*\([^)]+\)', 'IN (?)', normalized)
            
            # Extract key components
            components = []
            
            # Main operation
            if 'SELECT' in normalized:
                components.append('SELECT')
            if 'INSERT' in normalized:
                components.append('INSERT')
            if 'UPDATE' in normalized:
                components.append('UPDATE')
            if 'DELETE' in normalized:
                components.append('DELETE')
            
            # JOIN types
            if 'INNER JOIN' in normalized:
                components.append('INNER_JOIN')
            if 'LEFT JOIN' in normalized or 'LEFT OUTER JOIN' in normalized:
                components.append('LEFT_JOIN')
            if 'RIGHT JOIN' in normalized or 'RIGHT OUTER JOIN' in normalized:
                components.append('RIGHT_JOIN')
            if 'CROSS JOIN' in normalized:
                components.append('CROSS_JOIN')
            
            # Aggregations
            if 'GROUP BY' in normalized:
                components.append('GROUP_BY')
            if 'HAVING' in normalized:
                components.append('HAVING')
            if 'ORDER BY' in normalized:
                components.append('ORDER_BY')
            
            # Subqueries
            subquery_count = normalized.count('SELECT') - 1
            if subquery_count > 0:
                components.append(f'SUBQUERY_{subquery_count}')
            
            # Window functions
            if 'OVER' in normalized and 'PARTITION BY' in normalized:
                components.append('WINDOW_FUNC')
            
            # CTEs
            if 'WITH' in normalized and 'AS' in normalized:
                components.append('CTE')
            
            # Create signature
            signature = '_'.join(components) if components else 'SIMPLE_QUERY'
            
            # Add hash of normalized query for uniqueness
            query_hash = hashlib.md5(normalized.encode()).hexdigest()[:8]
            signature = f"{signature}_{query_hash}"
            
            logger.debug(f"Extracted pattern signature: {signature}")
            return signature
            
        except Exception as e:
            logger.error(f"Error extracting pattern signature: {str(e)}")
            # Return a basic signature
            return f"UNKNOWN_{hashlib.md5(sql.encode()).hexdigest()[:8]}"
    
    async def find_matching_patterns(
        self,
        sql: str,
        database_type: str,
        min_success_rate: float = 0.7,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find patterns that match the given SQL query
        
        Args:
            sql: SQL query to match
            database_type: Database type (postgresql, mysql, mssql)
            min_success_rate: Minimum success rate for patterns
            limit: Maximum number of patterns to return
            
        Returns:
            List of matching patterns with confidence scores
        """
        try:
            logger.info(f"Finding patterns for query on {database_type}")
            
            # Extract signature from query
            signature = self.extract_pattern_signature(sql)
            
            # Find patterns with same signature
            exact_matches = self.db.query(OptimizationPattern).filter(
                OptimizationPattern.pattern_signature == signature,
                OptimizationPattern.database_type == database_type,
                OptimizationPattern.success_rate >= min_success_rate
            ).order_by(
                OptimizationPattern.success_rate.desc(),
                OptimizationPattern.avg_improvement_pct.desc()
            ).limit(limit).all()
            
            matches = []
            
            for pattern in exact_matches:
                confidence = self._calculate_confidence(pattern, sql)
                
                matches.append({
                    'pattern_id': pattern.id,
                    'pattern_type': pattern.pattern_type,
                    'pattern_signature': pattern.pattern_signature,
                    'original_pattern': pattern.original_pattern,
                    'optimized_pattern': pattern.optimized_pattern,
                    'success_rate': round(pattern.success_rate * 100, 2),
                    'avg_improvement_pct': pattern.avg_improvement_pct,
                    'times_applied': pattern.times_applied,
                    'times_successful': pattern.times_successful,
                    'confidence': confidence,
                    'match_type': 'exact'
                })
            
            # If no exact matches, try similar patterns
            if not matches:
                similar_matches = await self._find_similar_patterns(
                    sql,
                    database_type,
                    min_success_rate,
                    limit
                )
                matches.extend(similar_matches)
            
            logger.info(f"Found {len(matches)} matching patterns")
            return matches
            
        except Exception as e:
            logger.error(f"Error finding matching patterns: {str(e)}")
            return []
    
    async def _find_similar_patterns(
        self,
        sql: str,
        database_type: str,
        min_success_rate: float,
        limit: int
    ) -> List[Dict]:
        """Find patterns with similar characteristics"""
        try:
            # Extract query characteristics
            sql_upper = sql.upper()
            has_join = 'JOIN' in sql_upper
            has_subquery = sql_upper.count('SELECT') > 1
            has_group_by = 'GROUP BY' in sql_upper
            has_order_by = 'ORDER BY' in sql_upper
            
            # Get all patterns for this database type
            all_patterns = self.db.query(OptimizationPattern).filter(
                OptimizationPattern.database_type == database_type,
                OptimizationPattern.success_rate >= min_success_rate
            ).all()
            
            similar = []
            
            for pattern in all_patterns:
                # Calculate similarity score
                similarity = 0
                pattern_upper = pattern.original_pattern.upper()
                
                if has_join and 'JOIN' in pattern_upper:
                    similarity += 0.3
                if has_subquery and pattern_upper.count('SELECT') > 1:
                    similarity += 0.2
                if has_group_by and 'GROUP BY' in pattern_upper:
                    similarity += 0.2
                if has_order_by and 'ORDER BY' in pattern_upper:
                    similarity += 0.1
                
                # Check pattern type similarity
                if pattern.pattern_type in ['index', 'rewrite', 'join_optimization']:
                    similarity += 0.2
                
                if similarity >= 0.5:  # At least 50% similar
                    confidence = similarity * pattern.success_rate
                    
                    similar.append({
                        'pattern_id': pattern.id,
                        'pattern_type': pattern.pattern_type,
                        'pattern_signature': pattern.pattern_signature,
                        'original_pattern': pattern.original_pattern,
                        'optimized_pattern': pattern.optimized_pattern,
                        'success_rate': round(pattern.success_rate * 100, 2),
                        'avg_improvement_pct': pattern.avg_improvement_pct,
                        'times_applied': pattern.times_applied,
                        'times_successful': pattern.times_successful,
                        'confidence': round(confidence, 2),
                        'match_type': 'similar',
                        'similarity_score': round(similarity, 2)
                    })
            
            # Sort by confidence and limit
            similar.sort(key=lambda x: x['confidence'], reverse=True)
            return similar[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar patterns: {str(e)}")
            return []
    
    def _calculate_confidence(
        self,
        pattern: OptimizationPattern,
        sql: str
    ) -> float:
        """Calculate confidence score for pattern match"""
        try:
            confidence = pattern.success_rate
            
            # Boost confidence based on number of successful applications
            if pattern.times_successful >= 10:
                confidence *= 1.1
            elif pattern.times_successful >= 5:
                confidence *= 1.05
            
            # Boost confidence based on improvement percentage
            if pattern.avg_improvement_pct >= 50:
                confidence *= 1.1
            elif pattern.avg_improvement_pct >= 30:
                confidence *= 1.05
            
            # Cap at 1.0
            confidence = min(confidence, 1.0)
            
            return round(confidence, 2)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.5
    
    def get_pattern_success_rate(self, pattern_id: int) -> float:
        """
        Get success rate for a specific pattern
        
        Args:
            pattern_id: Pattern ID
            
        Returns:
            Success rate (0-1)
        """
        try:
            pattern = self.db.query(OptimizationPattern).filter(
                OptimizationPattern.id == pattern_id
            ).first()
            
            if not pattern:
                return 0.0
            
            return pattern.success_rate
            
        except Exception as e:
            logger.error(f"Error getting pattern success rate: {str(e)}")
            return 0.0
    
    async def apply_pattern_optimization(
        self,
        sql: str,
        pattern_id: int
    ) -> Optional[str]:
        """
        Apply a pattern's optimization to a query
        
        Args:
            sql: Original SQL query
            pattern_id: Pattern ID to apply
            
        Returns:
            Optimized SQL or None if pattern can't be applied
        """
        try:
            logger.info(f"Applying pattern {pattern_id} to query")
            
            pattern = self.db.query(OptimizationPattern).filter(
                OptimizationPattern.id == pattern_id
            ).first()
            
            if not pattern:
                logger.warning(f"Pattern {pattern_id} not found")
                return None
            
            # This is a simplified version
            # In production, you'd have more sophisticated pattern application logic
            
            # For now, return the pattern's optimized version as a template
            # In a real implementation, you'd:
            # 1. Parse the original query
            # 2. Identify the parts that match the pattern
            # 3. Apply the optimization transformation
            # 4. Reconstruct the optimized query
            
            logger.info(f"Pattern {pattern_id} applied successfully")
            return pattern.optimized_pattern
            
        except Exception as e:
            logger.error(f"Error applying pattern optimization: {str(e)}")
            return None
    
    async def store_new_pattern(
        self,
        original_sql: str,
        optimized_sql: str,
        database_type: str,
        pattern_type: str = 'rewrite',
        initial_improvement: float = 0.0
    ) -> OptimizationPattern:
        """
        Store a new optimization pattern
        
        Args:
            original_sql: Original SQL query
            optimized_sql: Optimized SQL query
            database_type: Database type
            pattern_type: Type of pattern (index, rewrite, config, etc.)
            initial_improvement: Initial improvement percentage
            
        Returns:
            Created OptimizationPattern object
        """
        try:
            logger.info(f"Storing new {pattern_type} pattern for {database_type}")
            
            # Extract signature
            signature = self.extract_pattern_signature(original_sql)
            
            # Check if pattern already exists
            existing = self.db.query(OptimizationPattern).filter(
                OptimizationPattern.pattern_signature == signature,
                OptimizationPattern.database_type == database_type
            ).first()
            
            if existing:
                logger.info(f"Pattern already exists: {existing.id}")
                return existing
            
            # Create new pattern
            pattern = OptimizationPattern(
                pattern_type=pattern_type,
                pattern_signature=signature,
                original_pattern=original_sql,
                optimized_pattern=optimized_sql,
                success_rate=0.0,  # Will be updated as feedback comes in
                avg_improvement_pct=initial_improvement,
                times_applied=0,
                times_successful=0,
                database_type=database_type,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(pattern)
            self.db.commit()
            self.db.refresh(pattern)
            
            logger.info(f"New pattern stored: {pattern.id}")
            return pattern
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing new pattern: {str(e)}")
            raise
    
    async def update_pattern_stats(
        self,
        pattern_id: int,
        was_successful: bool,
        actual_improvement: float
    ) -> bool:
        """
        Update pattern statistics after application
        
        Args:
            pattern_id: Pattern ID
            was_successful: Whether the optimization was successful
            actual_improvement: Actual improvement achieved
            
        Returns:
            True if updated successfully
        """
        try:
            pattern = self.db.query(OptimizationPattern).filter(
                OptimizationPattern.id == pattern_id
            ).first()
            
            if not pattern:
                logger.warning(f"Pattern {pattern_id} not found")
                return False
            
            # Update counts
            pattern.times_applied += 1
            if was_successful:
                pattern.times_successful += 1
            
            # Update success rate
            pattern.success_rate = (
                pattern.times_successful / pattern.times_applied
                if pattern.times_applied > 0 else 0
            )
            
            # Update average improvement (running average)
            if pattern.times_applied == 1:
                pattern.avg_improvement_pct = actual_improvement
            else:
                # Calculate new average
                total_improvement = (
                    pattern.avg_improvement_pct * (pattern.times_applied - 1) +
                    actual_improvement
                )
                pattern.avg_improvement_pct = total_improvement / pattern.times_applied
            
            pattern.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Pattern {pattern_id} stats updated: "
                       f"success_rate={pattern.success_rate:.2f}, "
                       f"avg_improvement={pattern.avg_improvement_pct:.2f}%")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating pattern stats: {str(e)}")
            return False
    
    def get_top_patterns(
        self,
        database_type: Optional[str] = None,
        pattern_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get top performing patterns
        
        Args:
            database_type: Optional database type filter
            pattern_type: Optional pattern type filter
            limit: Maximum number of patterns to return
            
        Returns:
            List of top patterns
        """
        try:
            query = self.db.query(OptimizationPattern)
            
            if database_type:
                query = query.filter(OptimizationPattern.database_type == database_type)
            
            if pattern_type:
                query = query.filter(OptimizationPattern.pattern_type == pattern_type)
            
            # Filter for patterns with sufficient data
            query = query.filter(OptimizationPattern.times_applied >= 3)
            
            # Order by success rate and improvement
            patterns = query.order_by(
                OptimizationPattern.success_rate.desc(),
                OptimizationPattern.avg_improvement_pct.desc()
            ).limit(limit).all()
            
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
                    'created_at': p.created_at.isoformat()
                }
                for p in patterns
            ]
            
        except Exception as e:
            logger.error(f"Error getting top patterns: {str(e)}")
            return []
    
    async def match_and_suggest(
        self,
        sql: str,
        connection_id: int
    ) -> Dict:
        """
        Match query to patterns and provide suggestions
        
        Args:
            sql: SQL query
            connection_id: Connection ID
            
        Returns:
            Dictionary with match results and suggestions
        """
        try:
            # Get connection to determine database type
            connection = self.db.query(Connection).filter(
                Connection.id == connection_id
            ).first()
            
            if not connection:
                return {
                    'matched': False,
                    'message': 'Connection not found'
                }
            
            # Find matching patterns
            matches = await self.find_matching_patterns(
                sql,
                connection.engine,
                min_success_rate=0.6,
                limit=3
            )
            
            if not matches:
                return {
                    'matched': False,
                    'message': 'No matching patterns found',
                    'suggestion': 'This query will be analyzed using the LLM optimizer'
                }
            
            # Get best match
            best_match = matches[0]
            
            return {
                'matched': True,
                'best_match': best_match,
                'all_matches': matches,
                'suggestion': (
                    f"Found {len(matches)} similar pattern(s). "
                    f"Best match has {best_match['success_rate']}% success rate "
                    f"with average {best_match['avg_improvement_pct']}% improvement."
                ),
                'confidence': best_match['confidence']
            }
            
        except Exception as e:
            logger.error(f"Error in match_and_suggest: {str(e)}")
            return {
                'matched': False,
                'message': f'Error: {str(e)}'
            }
