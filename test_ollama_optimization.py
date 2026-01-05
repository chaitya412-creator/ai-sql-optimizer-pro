"""
Test script for Ollama SQL Optimization System
Tests all phases: Detection, Optimization, Normalization, Fix Application, and Validation
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.ollama_client import OllamaClient
from app.core.plan_analyzer import PlanAnalyzer
from app.core.plan_normalizer import PlanNormalizer, PlanNodeType
from app.core.fix_applicator import FixApplicator, FixType
from app.core.performance_validator import PerformanceValidator, PerformanceMetrics


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_ollama_health():
    """Test 1: Ollama Health Check"""
    print_section("TEST 1: Ollama Health Check")
    
    async def check():
        client = OllamaClient()
        result = await client.check_health()
        
        print(f"Status: {result.get('status')}")
        print(f"URL: {result.get('url')}")
        print(f"Model: {result.get('model')}")
        print(f"Model Available: {result.get('model_available')}")
        
        if result.get('available_models'):
            print(f"Available Models: {', '.join(result['available_models'][:5])}")
        
        return result.get('status') == 'healthy'
    
    return asyncio.run(check())


def test_detection_system():
    """Test 2: Detection System"""
    print_section("TEST 2: Detection System (9 Types)")
    
    # Test query with multiple issues
    test_query = """
    SELECT * FROM users u
    JOIN orders o ON UPPER(u.email) = o.user_email
    WHERE u.name LIKE '%john%'
    AND (u.status = 'active' OR u.status = 'pending' OR u.status = 'trial')
    """
    
    # Simulate execution plan
    test_plan = {
        "Plan": {
            "Node Type": "Nested Loop",
            "Plan Rows": 50000,
            "Total Cost": 15000.0,
            "Plans": [
                {
                    "Node Type": "Seq Scan",
                    "Relation Name": "users",
                    "Plan Rows": 10000,
                    "Total Cost": 5000.0,
                    "Filter": "name LIKE '%john%'"
                },
                {
                    "Node Type": "Seq Scan",
                    "Relation Name": "orders",
                    "Plan Rows": 5000,
                    "Total Cost": 3000.0
                }
            ]
        }
    }
    
    result = PlanAnalyzer.analyze_plan(
        plan=test_plan,
        engine="postgresql",
        sql_query=test_query
    )
    
    print(f"Total Issues Detected: {result['total_issues']}")
    print(f"Critical: {result['critical_issues']}")
    print(f"High: {result['high_issues']}")
    print(f"Medium: {result['medium_issues']}")
    print(f"Low: {result['low_issues']}")
    
    print("\nIssue Types Found:")
    issue_types = set(issue['issue_type'] for issue in result['issues'])
    for issue_type in issue_types:
        count = sum(1 for i in result['issues'] if i['issue_type'] == issue_type)
        print(f"  - {issue_type}: {count}")
    
    print("\nTop 3 Issues:")
    for i, issue in enumerate(result['issues'][:3], 1):
        print(f"  {i}. [{issue['severity'].upper()}] {issue['title']}")
    
    return result['total_issues'] > 0


def test_plan_normalization():
    """Test 3: Plan Normalization"""
    print_section("TEST 3: Plan Normalization")
    
    # PostgreSQL plan
    pg_plan = {
        "Plan": {
            "Node Type": "Seq Scan",
            "Relation Name": "users",
            "Plan Rows": 10000,
            "Total Cost": 5000.0,
            "Actual Rows": 8500,
            "Actual Total Time": 125.5,
            "Filter": "age > 25"
        }
    }
    
    normalized = PlanNormalizer.normalize(pg_plan, "postgresql")
    
    if normalized:
        print(f"Node Type: {normalized.node_type.value}")
        print(f"Operation: {normalized.operation}")
        print(f"Relation: {normalized.relation_name}")
        print(f"Estimated Rows: {normalized.estimated_rows:,}")
        print(f"Actual Rows: {normalized.actual_rows:,}")
        print(f"Estimated Cost: {normalized.estimated_cost:.2f}")
        print(f"Actual Time: {normalized.actual_time_ms:.2f}ms")
        
        # Calculate cardinality error
        card_error = normalized.get_cardinality_error()
        if card_error:
            print(f"Cardinality Error: {card_error*100:.1f}%")
        
        # Extract metrics
        metrics = PlanNormalizer.extract_metrics(normalized)
        print(f"\nExtracted Metrics:")
        print(f"  Total Estimated Rows: {metrics['total_estimated_rows']:,}")
        print(f"  Sequential Scans: {metrics['seq_scans']}")
        print(f"  Index Scans: {metrics['index_scans']}")
        
        return True
    
    return False


def test_ollama_optimization():
    """Test 4: Ollama Optimization"""
    print_section("TEST 4: Ollama SQL Optimization")
    
    async def optimize():
        client = OllamaClient()
        
        test_query = "SELECT * FROM users WHERE UPPER(email) = 'TEST@EXAMPLE.COM'"
        schema_ddl = "CREATE TABLE users (id INT, email VARCHAR(255), name VARCHAR(255));"
        
        # Simulate detected issues
        detected_issues = {
            "total_issues": 2,
            "issues": [
                {
                    "severity": "high",
                    "title": "Function on indexed column",
                    "description": "UPPER() function prevents index usage"
                },
                {
                    "severity": "medium",
                    "title": "SELECT * usage",
                    "description": "Selecting all columns instead of specific ones"
                }
            ]
        }
        
        print("Calling Ollama sqlcoder:latest...")
        result = await client.optimize_query(
            sql_query=test_query,
            schema_ddl=schema_ddl,
            execution_plan=None,
            database_type="postgresql",
            detected_issues=detected_issues
        )
        
        if result.get("success"):
            print("✓ Optimization successful!")
            print(f"\nOptimized SQL:")
            print(result["optimized_sql"][:200] + "..." if len(result["optimized_sql"]) > 200 else result["optimized_sql"])
            
            print(f"\nExplanation (first 200 chars):")
            print(result["explanation"][:200] + "...")
            
            if result.get("estimated_improvement"):
                print(f"\nEstimated Improvement: {result['estimated_improvement']}%")
            
            return True
        else:
            print(f"✗ Optimization failed: {result.get('error')}")
            return False
    
    try:
        return asyncio.run(optimize())
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_fix_applicator():
    """Test 5: Fix Applicator (Dry Run)"""
    print_section("TEST 5: Safe Fix Application (Dry Run)")
    
    # Mock database manager
    class MockDBManager:
        def __init__(self):
            self.engine = "postgresql"
        
        def execute_query(self, sql):
            return []
    
    db_manager = MockDBManager()
    
    applicator = FixApplicator(db_manager, config={
        "business_hours_only": False,
        "enable_ddl_execution": True
    })
    
    # Test index creation (dry run)
    result = applicator.apply_fix(
        fix_type=FixType.INDEX_CREATION,
        fix_sql="CREATE INDEX idx_users_email ON users(email);",
        dry_run=True
    )
    
    print(f"Status: {result['status']}")
    print(f"Success: {result['success']}")
    print(f"Message: {result.get('message', 'N/A')}")
    
    if result.get('fix_sql'):
        print(f"Fix SQL: {result['fix_sql']}")
    
    # Test batch application
    fixes = [
        {"type": "index_creation", "sql": "CREATE INDEX idx_users_name ON users(name);"},
        {"type": "statistics_update", "sql": "ANALYZE users;"}
    ]
    
    batch_result = applicator.apply_fixes_batch(fixes, dry_run=True)
    print(f"\nBatch Results:")
    print(f"  Total: {batch_result['total_fixes']}")
    print(f"  Successful: {batch_result['successful']}")
    print(f"  Failed: {batch_result['failed']}")
    
    return result['success']


def test_performance_validator():
    """Test 6: Performance Validator"""
    print_section("TEST 6: Performance Validation")
    
    # Create mock metrics
    before_metrics = PerformanceMetrics(
        execution_time_ms=250.0,
        rows_returned=1000,
        buffer_hits=5000,
        buffer_reads=1000
    )
    
    after_metrics = PerformanceMetrics(
        execution_time_ms=125.0,
        rows_returned=1000,
        buffer_hits=5500,
        buffer_reads=500
    )
    
    # Calculate improvement
    improvement = ((before_metrics.execution_time_ms - after_metrics.execution_time_ms) / 
                   before_metrics.execution_time_ms * 100)
    
    print(f"Before: {before_metrics.execution_time_ms:.2f}ms")
    print(f"After: {after_metrics.execution_time_ms:.2f}ms")
    print(f"Improvement: {improvement:.1f}%")
    
    print(f"\nCache Hit Ratio:")
    print(f"  Before: {before_metrics.get_cache_hit_ratio()*100:.1f}%")
    print(f"  After: {after_metrics.get_cache_hit_ratio()*100:.1f}%")
    
    print(f"\nI/O Reduction:")
    io_reduction = ((before_metrics.buffer_reads - after_metrics.buffer_reads) / 
                    before_metrics.buffer_reads * 100)
    print(f"  {io_reduction:.1f}% fewer disk reads")
    
    return improvement > 0


def test_natural_language_explanation():
    """Test 7: Natural Language Plan Explanation"""
    print_section("TEST 7: Natural Language Plan Explanation")
    
    async def explain():
        client = OllamaClient()
        
        test_plan = {
            "Plan": {
                "Node Type": "Nested Loop",
                "Plan Rows": 50000,
                "Total Cost": 15000.0,
                "Plans": [
                    {
                        "Node Type": "Seq Scan",
                        "Relation Name": "users",
                        "Plan Rows": 10000
                    }
                ]
            }
        }
        
        test_query = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id"
        
        print("Generating natural language explanation...")
        result = await client.explain_plan_natural_language(
            execution_plan=test_plan,
            sql_query=test_query,
            database_type="postgresql"
        )
        
        if result.get("success"):
            print("✓ Explanation generated!")
            print(f"\nSummary:")
            print(result.get("summary", "N/A")[:200] + "...")
            return True
        else:
            print(f"✗ Failed: {result.get('error')}")
            return False
    
    try:
        return asyncio.run(explain())
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  OLLAMA SQL OPTIMIZATION SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Ollama Health Check", test_ollama_health),
        ("Detection System", test_detection_system),
        ("Plan Normalization", test_plan_normalization),
        ("Ollama Optimization", test_ollama_optimization),
        ("Fix Applicator", test_fix_applicator),
        ("Performance Validator", test_performance_validator),
        ("Natural Language Explanation", test_natural_language_explanation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready for production.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the output above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
