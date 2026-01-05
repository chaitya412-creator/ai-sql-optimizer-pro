"""
Execution Plan Normalizer
Standardizes execution plans across different database engines
Extracts common metrics and patterns for analysis
"""
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from enum import Enum


class PlanNodeType(str, Enum):
    """Standardized plan node types"""
    SEQ_SCAN = "sequential_scan"
    INDEX_SCAN = "index_scan"
    INDEX_ONLY_SCAN = "index_only_scan"
    BITMAP_SCAN = "bitmap_scan"
    NESTED_LOOP = "nested_loop"
    HASH_JOIN = "hash_join"
    MERGE_JOIN = "merge_join"
    SORT = "sort"
    AGGREGATE = "aggregate"
    LIMIT = "limit"
    SUBQUERY = "subquery"
    CTE = "cte"
    UNKNOWN = "unknown"


class NormalizedPlanNode:
    """Standardized representation of a plan node"""
    
    def __init__(
        self,
        node_type: PlanNodeType,
        operation: str,
        relation_name: Optional[str] = None,
        index_name: Optional[str] = None,
        estimated_rows: int = 0,
        actual_rows: Optional[int] = None,
        estimated_cost: float = 0.0,
        actual_time_ms: Optional[float] = None,
        filter_condition: Optional[str] = None,
        join_type: Optional[str] = None,
        children: Optional[List['NormalizedPlanNode']] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.node_type = node_type
        self.operation = operation
        self.relation_name = relation_name
        self.index_name = index_name
        self.estimated_rows = estimated_rows
        self.actual_rows = actual_rows
        self.estimated_cost = estimated_cost
        self.actual_time_ms = actual_time_ms
        self.filter_condition = filter_condition
        self.join_type = join_type
        self.children = children or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "node_type": self.node_type.value,
            "operation": self.operation,
            "relation_name": self.relation_name,
            "index_name": self.index_name,
            "estimated_rows": self.estimated_rows,
            "actual_rows": self.actual_rows,
            "estimated_cost": self.estimated_cost,
            "actual_time_ms": self.actual_time_ms,
            "filter_condition": self.filter_condition,
            "join_type": self.join_type,
            "children": [child.to_dict() for child in self.children],
            "metadata": self.metadata
        }
    
    def get_cardinality_error(self) -> Optional[float]:
        """Calculate cardinality estimation error"""
        if self.actual_rows is not None and self.estimated_rows > 0:
            return abs(self.actual_rows - self.estimated_rows) / self.estimated_rows
        return None


class PlanNormalizer:
    """Normalizes execution plans from different database engines"""
    
    @staticmethod
    def normalize(plan: Dict[str, Any], engine: str) -> Optional[NormalizedPlanNode]:
        """
        Normalize execution plan to standard format
        
        Args:
            plan: Raw execution plan from database
            engine: Database engine type
        
        Returns:
            Normalized plan tree
        """
        try:
            if engine == "postgresql":
                return PlanNormalizer._normalize_postgresql(plan)
            elif engine == "mysql":
                return PlanNormalizer._normalize_mysql(plan)
            elif engine == "mssql":
                return PlanNormalizer._normalize_mssql(plan)
            elif engine == "oracle":
                return PlanNormalizer._normalize_oracle(plan)
            else:
                logger.warning(f"Unsupported engine for normalization: {engine}")
                return None
        except Exception as e:
            logger.error(f"Plan normalization failed: {e}")
            return None
    
    @staticmethod
    def _normalize_postgresql(plan: Dict[str, Any]) -> Optional[NormalizedPlanNode]:
        """Normalize PostgreSQL execution plan"""
        
        def traverse(node: Dict[str, Any]) -> NormalizedPlanNode:
            node_type_str = node.get("Node Type", "")
            
            # Map PostgreSQL node types to standard types
            node_type = PlanNodeType.UNKNOWN
            if "Seq Scan" in node_type_str:
                node_type = PlanNodeType.SEQ_SCAN
            elif "Index Scan" in node_type_str:
                node_type = PlanNodeType.INDEX_SCAN
            elif "Index Only Scan" in node_type_str:
                node_type = PlanNodeType.INDEX_ONLY_SCAN
            elif "Bitmap" in node_type_str:
                node_type = PlanNodeType.BITMAP_SCAN
            elif "Nested Loop" in node_type_str:
                node_type = PlanNodeType.NESTED_LOOP
            elif "Hash Join" in node_type_str:
                node_type = PlanNodeType.HASH_JOIN
            elif "Merge Join" in node_type_str:
                node_type = PlanNodeType.MERGE_JOIN
            elif "Sort" in node_type_str:
                node_type = PlanNodeType.SORT
            elif "Aggregate" in node_type_str or "Group" in node_type_str:
                node_type = PlanNodeType.AGGREGATE
            elif "Limit" in node_type_str:
                node_type = PlanNodeType.LIMIT
            elif "Subquery" in node_type_str or "SubPlan" in node_type_str:
                node_type = PlanNodeType.SUBQUERY
            elif "CTE" in node_type_str:
                node_type = PlanNodeType.CTE
            
            # Extract metrics
            estimated_rows = node.get("Plan Rows", 0)
            actual_rows = node.get("Actual Rows")
            estimated_cost = node.get("Total Cost", 0.0)
            actual_time = node.get("Actual Total Time")
            
            # Extract relation and index info
            relation_name = node.get("Relation Name")
            index_name = node.get("Index Name")
            
            # Extract filter condition
            filter_cond = node.get("Filter") or node.get("Index Cond") or node.get("Hash Cond") or node.get("Join Filter")
            
            # Extract join type
            join_type = node.get("Join Type")
            
            # Process children
            children = []
            if "Plans" in node:
                for child in node["Plans"]:
                    children.append(traverse(child))
            
            # Additional metadata
            metadata = {
                "startup_cost": node.get("Startup Cost"),
                "rows_removed_by_filter": node.get("Rows Removed by Filter"),
                "shared_hit_blocks": node.get("Shared Hit Blocks"),
                "shared_read_blocks": node.get("Shared Read Blocks"),
                "parallel_aware": node.get("Parallel Aware", False),
                "workers_planned": node.get("Workers Planned"),
                "workers_launched": node.get("Workers Launched")
            }
            
            return NormalizedPlanNode(
                node_type=node_type,
                operation=node_type_str,
                relation_name=relation_name,
                index_name=index_name,
                estimated_rows=estimated_rows,
                actual_rows=actual_rows,
                estimated_cost=estimated_cost,
                actual_time_ms=actual_time,
                filter_condition=filter_cond,
                join_type=join_type,
                children=children,
                metadata=metadata
            )
        
        # Handle both list and dict formats
        if isinstance(plan, list) and plan:
            root = plan[0].get("Plan", {})
        elif isinstance(plan, dict):
            root = plan.get("Plan", plan)
        else:
            return None
        
        return traverse(root)
    
    @staticmethod
    def _normalize_mysql(plan: Dict[str, Any]) -> Optional[NormalizedPlanNode]:
        """Normalize MySQL execution plan"""
        
        def traverse(node: Dict[str, Any]) -> NormalizedPlanNode:
            # MySQL uses different structure
            if "table" in node:
                table_info = node["table"]
                access_type = table_info.get("access_type", "")
                
                # Map MySQL access types
                node_type = PlanNodeType.UNKNOWN
                if access_type == "ALL":
                    node_type = PlanNodeType.SEQ_SCAN
                elif access_type in ["index", "ref", "eq_ref", "const"]:
                    node_type = PlanNodeType.INDEX_SCAN
                elif access_type == "range":
                    node_type = PlanNodeType.INDEX_SCAN
                
                relation_name = table_info.get("table_name")
                index_name = table_info.get("key")
                estimated_rows = table_info.get("rows_examined_per_scan", 0)
                filter_cond = table_info.get("attached_condition")
                
                metadata = {
                    "access_type": access_type,
                    "filtered": table_info.get("filtered"),
                    "cost_info": table_info.get("cost_info", {})
                }
                
                return NormalizedPlanNode(
                    node_type=node_type,
                    operation=access_type,
                    relation_name=relation_name,
                    index_name=index_name,
                    estimated_rows=estimated_rows,
                    filter_condition=filter_cond,
                    metadata=metadata
                )
            
            elif "nested_loop" in node:
                children = []
                for child in node["nested_loop"]:
                    if isinstance(child, dict):
                        children.append(traverse(child))
                
                return NormalizedPlanNode(
                    node_type=PlanNodeType.NESTED_LOOP,
                    operation="Nested Loop",
                    children=children
                )
            
            elif "duplicates_removal" in node:
                child = traverse(node["duplicates_removal"])
                return NormalizedPlanNode(
                    node_type=PlanNodeType.AGGREGATE,
                    operation="Duplicates Removal",
                    children=[child]
                )
            
            else:
                # Generic node
                return NormalizedPlanNode(
                    node_type=PlanNodeType.UNKNOWN,
                    operation="Unknown",
                    metadata=node
                )
        
        query_block = plan.get("query_block", plan)
        return traverse(query_block)
    
    @staticmethod
    def _normalize_mssql(plan: Dict[str, Any]) -> Optional[NormalizedPlanNode]:
        """Normalize MSSQL execution plan"""
        # MSSQL plans are typically XML, converted to dict
        # This is a simplified implementation
        
        plan_str = str(plan)
        
        # Detect common patterns
        node_type = PlanNodeType.UNKNOWN
        operation = "Unknown"
        
        if "Table Scan" in plan_str or "Clustered Index Scan" in plan_str:
            node_type = PlanNodeType.SEQ_SCAN
            operation = "Table Scan"
        elif "Index Seek" in plan_str:
            node_type = PlanNodeType.INDEX_SCAN
            operation = "Index Seek"
        elif "Nested Loops" in plan_str:
            node_type = PlanNodeType.NESTED_LOOP
            operation = "Nested Loops"
        elif "Hash Match" in plan_str:
            node_type = PlanNodeType.HASH_JOIN
            operation = "Hash Match"
        elif "Merge Join" in plan_str:
            node_type = PlanNodeType.MERGE_JOIN
            operation = "Merge Join"
        
        return NormalizedPlanNode(
            node_type=node_type,
            operation=operation,
            metadata={"raw_plan": plan}
        )
    
    @staticmethod
    def _normalize_oracle(plan: Dict[str, Any]) -> Optional[NormalizedPlanNode]:
        """Normalize Oracle execution plan"""
        # Oracle plans from DBMS_XPLAN
        # Simplified implementation
        
        return NormalizedPlanNode(
            node_type=PlanNodeType.UNKNOWN,
            operation="Oracle Plan",
            metadata={"raw_plan": plan}
        )
    
    @staticmethod
    def extract_metrics(normalized_plan: NormalizedPlanNode) -> Dict[str, Any]:
        """Extract key metrics from normalized plan"""
        
        metrics = {
            "total_estimated_rows": 0,
            "total_actual_rows": 0,
            "total_cost": 0.0,
            "total_time_ms": 0.0,
            "seq_scans": 0,
            "index_scans": 0,
            "nested_loops": 0,
            "hash_joins": 0,
            "sorts": 0,
            "max_cardinality_error": 0.0,
            "tables_accessed": set(),
            "indexes_used": set()
        }
        
        def traverse(node: NormalizedPlanNode):
            # Accumulate metrics
            metrics["total_estimated_rows"] += node.estimated_rows
            if node.actual_rows:
                metrics["total_actual_rows"] += node.actual_rows
            metrics["total_cost"] += node.estimated_cost
            if node.actual_time_ms:
                metrics["total_time_ms"] += node.actual_time_ms
            
            # Count node types
            if node.node_type == PlanNodeType.SEQ_SCAN:
                metrics["seq_scans"] += 1
            elif node.node_type in [PlanNodeType.INDEX_SCAN, PlanNodeType.INDEX_ONLY_SCAN]:
                metrics["index_scans"] += 1
            elif node.node_type == PlanNodeType.NESTED_LOOP:
                metrics["nested_loops"] += 1
            elif node.node_type == PlanNodeType.HASH_JOIN:
                metrics["hash_joins"] += 1
            elif node.node_type == PlanNodeType.SORT:
                metrics["sorts"] += 1
            
            # Track cardinality errors
            card_error = node.get_cardinality_error()
            if card_error:
                metrics["max_cardinality_error"] = max(
                    metrics["max_cardinality_error"],
                    card_error
                )
            
            # Track accessed objects
            if node.relation_name:
                metrics["tables_accessed"].add(node.relation_name)
            if node.index_name:
                metrics["indexes_used"].add(node.index_name)
            
            # Traverse children
            for child in node.children:
                traverse(child)
        
        traverse(normalized_plan)
        
        # Convert sets to lists for JSON serialization
        metrics["tables_accessed"] = list(metrics["tables_accessed"])
        metrics["indexes_used"] = list(metrics["indexes_used"])
        
        return metrics
    
    @staticmethod
    def compare_plans(
        plan1: NormalizedPlanNode,
        plan2: NormalizedPlanNode
    ) -> Dict[str, Any]:
        """
        Compare two execution plans
        
        Returns:
            Comparison metrics showing improvements/regressions
        """
        metrics1 = PlanNormalizer.extract_metrics(plan1)
        metrics2 = PlanNormalizer.extract_metrics(plan2)
        
        comparison = {
            "cost_change_pct": 0.0,
            "time_change_pct": 0.0,
            "rows_change_pct": 0.0,
            "seq_scans_change": 0,
            "index_scans_change": 0,
            "improved": False
        }
        
        # Calculate percentage changes
        if metrics1["total_cost"] > 0:
            comparison["cost_change_pct"] = (
                (metrics2["total_cost"] - metrics1["total_cost"]) / metrics1["total_cost"] * 100
            )
        
        if metrics1["total_time_ms"] > 0:
            comparison["time_change_pct"] = (
                (metrics2["total_time_ms"] - metrics1["total_time_ms"]) / metrics1["total_time_ms"] * 100
            )
        
        if metrics1["total_estimated_rows"] > 0:
            comparison["rows_change_pct"] = (
                (metrics2["total_estimated_rows"] - metrics1["total_estimated_rows"]) / 
                metrics1["total_estimated_rows"] * 100
            )
        
        comparison["seq_scans_change"] = metrics2["seq_scans"] - metrics1["seq_scans"]
        comparison["index_scans_change"] = metrics2["index_scans"] - metrics1["index_scans"]
        
        # Determine if improved (lower cost/time, fewer seq scans)
        comparison["improved"] = (
            comparison["cost_change_pct"] < -5 or  # 5% cost reduction
            comparison["time_change_pct"] < -5 or  # 5% time reduction
            comparison["seq_scans_change"] < 0  # Fewer sequential scans
        )
        
        return comparison
    
    @staticmethod
    def find_bottlenecks(normalized_plan: NormalizedPlanNode) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks in the plan"""
        
        bottlenecks = []
        
        def traverse(node: NormalizedPlanNode, depth: int = 0):
            # Check for expensive operations
            if node.estimated_cost > 1000:
                bottlenecks.append({
                    "type": "high_cost",
                    "node_type": node.node_type.value,
                    "operation": node.operation,
                    "cost": node.estimated_cost,
                    "relation": node.relation_name,
                    "depth": depth
                })
            
            # Check for large sequential scans
            if node.node_type == PlanNodeType.SEQ_SCAN and node.estimated_rows > 10000:
                bottlenecks.append({
                    "type": "large_seq_scan",
                    "relation": node.relation_name,
                    "estimated_rows": node.estimated_rows,
                    "depth": depth
                })
            
            # Check for cardinality misestimates
            card_error = node.get_cardinality_error()
            if card_error and card_error > 2.0:  # 200% error
                bottlenecks.append({
                    "type": "cardinality_mismatch",
                    "node_type": node.node_type.value,
                    "estimated": node.estimated_rows,
                    "actual": node.actual_rows,
                    "error_ratio": card_error,
                    "depth": depth
                })
            
            # Traverse children
            for child in node.children:
                traverse(child, depth + 1)
        
        traverse(normalized_plan)
        
        # Sort by severity (cost/rows)
        bottlenecks.sort(key=lambda x: x.get("cost", 0) + x.get("estimated_rows", 0), reverse=True)
        
        return bottlenecks
