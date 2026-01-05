"""
Test script to verify all SQL Optimizer features are working
Run this after starting the backend to test all endpoints
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_optimize_query():
    """Test the main optimization endpoint with comprehensive detection"""
    print_section("TEST 1: Query Optimization with Detection")
    
    # This query should trigger multiple detections
    test_query = """
    SELECT * FROM users 
    WHERE email LIKE '%@example.com' 
    AND created_at > '2024-01-01'
    ORDER BY created_at
    """
    
    payload = {
        "connection_id": 1,  # Adjust based on your setup
        "sql_query": test_query,
        "include_execution_plan": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/optimizer/optimize", json=payload)
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Optimization successful!")
            print(f"\n📊 Optimization ID: {result['id']}")
            print(f"📝 Original SQL: {result['original_sql'][:50]}...")
            print(f"✨ Optimized SQL: {result['optimized_sql'][:50]}...")
            
            # Check detected issues
            if result.get('detected_issues'):
                issues = result['detected_issues']
                print(f"\n🔍 Detected Issues:")
                print(f"   Total: {issues['total_issues']}")
                print(f"   Critical: {issues['critical_issues']}")
                print(f"   High: {issues['high_issues']}")
                print(f"   Medium: {issues['medium_issues']}")
                print(f"   Low: {issues['low_issues']}")
                
                if issues.get('issues'):
                    print(f"\n📋 Issue Details:")
                    for i, issue in enumerate(issues['issues'][:3], 1):
                        print(f"   {i}. [{issue['severity'].upper()}] {issue['title']}")
                        print(f"      Type: {issue['issue_type']}")
                        print(f"      Description: {issue['description'][:80]}...")
            
            # Check execution plan
            if result.get('execution_plan'):
                print(f"\n📊 Execution Plan: Available")
            
            # Check improvement
            if result.get('estimated_improvement_pct'):
                print(f"\n📈 Estimated Improvement: {result['estimated_improvement_pct']}%")
            
            return result['id']
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_explain_plan(optimization_id):
    """Test execution plan explanation"""
    print_section("TEST 2: Execution Plan Explanation")
    
    payload = {
        "connection_id": 1,
        "sql_query": "SELECT * FROM users WHERE id > 100",
        "execution_plan": None  # Will be fetched
    }
    
    try:
        response = requests.post(f"{BASE_URL}/optimizer/explain-plan", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Plan explanation successful!")
            
            if result.get('success'):
                print(f"\n📖 Explanation: {result.get('explanation', '')[:200]}...")
                print(f"\n📝 Summary: {result.get('summary', '')[:150]}...")
                
                if result.get('key_operations'):
                    print(f"\n🔑 Key Operations:")
                    for op in result['key_operations']:
                        print(f"   - {op}")
                
                if result.get('bottlenecks'):
                    print(f"\n⚠️ Bottlenecks:")
                    for bottleneck in result['bottlenecks']:
                        print(f"   - {bottleneck}")
            else:
                print(f"⚠️ Explanation not available: {result.get('explanation')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_generate_fixes(optimization_id):
    """Test fix recommendation generation"""
    print_section("TEST 3: Generate Fix Recommendations")
    
    payload = {
        "optimization_id": optimization_id,
        "include_indexes": True,
        "include_maintenance": True,
        "include_rewrites": True,
        "include_config": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/optimizer/generate-fixes", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Fix generation successful!")
            
            if result.get('success'):
                print(f"\n🔧 Total Fixes: {result['total_fixes']}")
                print(f"🎯 High Impact: {result['high_impact_count']}")
                
                # Index recommendations
                if result.get('index_recommendations'):
                    print(f"\n📊 Index Recommendations ({len(result['index_recommendations'])}):")
                    for i, fix in enumerate(result['index_recommendations'][:3], 1):
                        print(f"   {i}. [{fix['estimated_impact'].upper()}] {fix['description']}")
                        if fix.get('sql'):
                            print(f"      SQL: {fix['sql'][:80]}...")
                
                # Maintenance tasks
                if result.get('maintenance_tasks'):
                    print(f"\n🔄 Maintenance Tasks ({len(result['maintenance_tasks'])}):")
                    for i, fix in enumerate(result['maintenance_tasks'][:3], 1):
                        print(f"   {i}. [{fix['estimated_impact'].upper()}] {fix['description']}")
                
                # Query rewrites
                if result.get('query_rewrites'):
                    print(f"\n📝 Query Rewrites ({len(result['query_rewrites'])}):")
                    for i, fix in enumerate(result['query_rewrites'][:3], 1):
                        print(f"   {i}. {fix['description'][:80]}...")
                
                return result
            else:
                print(f"⚠️ No fixes generated")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

def test_apply_fix_dry_run(optimization_id):
    """Test applying a fix in dry-run mode"""
    print_section("TEST 4: Apply Fix (Dry Run)")
    
    payload = {
        "optimization_id": optimization_id,
        "fix_type": "index_creation",
        "fix_sql": "CREATE INDEX idx_test ON users(email)",
        "dry_run": True,
        "skip_safety_checks": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/optimizer/apply-fix", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ Dry run successful!")
                print(f"\n📝 Status: {result.get('status')}")
                print(f"💬 Message: {result.get('message')}")
                
                if result.get('safety_checks'):
                    checks = result['safety_checks']
                    print(f"\n🛡️ Safety Checks:")
                    print(f"   Passed: {checks.get('passed')}")
                    print(f"   Checks: {', '.join(checks.get('checks_performed', []))}")
                    
                    if checks.get('warnings'):
                        print(f"   Warnings: {len(checks['warnings'])}")
                    if checks.get('errors'):
                        print(f"   Errors: {len(checks['errors'])}")
            else:
                print(f"⚠️ Dry run failed: {result.get('message')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_validate_performance(optimization_id):
    """Test performance validation"""
    print_section("TEST 5: Performance Validation")
    
    payload = {
        "optimization_id": optimization_id,
        "run_original": True,
        "run_optimized": True,
        "iterations": 3
    }
    
    try:
        print("⏳ Running performance test (this may take a moment)...")
        response = requests.post(f"{BASE_URL}/optimizer/validate-performance", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ Performance validation successful!")
                
                print(f"\n📊 Results:")
                print(f"   Faster: {'Yes ✅' if result.get('is_faster') else 'No ❌'}")
                
                if result.get('improvement_pct') is not None:
                    pct = result['improvement_pct']
                    print(f"   Improvement: {pct:+.1f}%")
                
                if result.get('improvement_ms') is not None:
                    ms = result['improvement_ms']
                    print(f"   Time Saved: {ms:+.2f} ms")
                
                # Original metrics
                if result.get('original_metrics'):
                    om = result['original_metrics']
                    print(f"\n📈 Original Query:")
                    print(f"   Execution Time: {om.get('execution_time_ms', 0):.2f} ms")
                    if om.get('buffer_hits') is not None:
                        print(f"   Buffer Hits: {om['buffer_hits']:,}")
                    if om.get('buffer_reads') is not None:
                        print(f"   Buffer Reads: {om['buffer_reads']:,}")
                
                # Optimized metrics
                if result.get('optimized_metrics'):
                    opt = result['optimized_metrics']
                    print(f"\n✨ Optimized Query:")
                    print(f"   Execution Time: {opt.get('execution_time_ms', 0):.2f} ms")
                    if opt.get('buffer_hits') is not None:
                        print(f"   Buffer Hits: {opt['buffer_hits']:,}")
                    if opt.get('buffer_reads') is not None:
                        print(f"   Buffer Reads: {opt['buffer_reads']:,}")
                
                # Validation notes
                if result.get('validation_notes'):
                    print(f"\n📝 Notes:")
                    for note in result['validation_notes']:
                        print(f"   - {note}")
            else:
                print(f"⚠️ Validation failed")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_list_issues():
    """Test listing detected issues"""
    print_section("TEST 6: List All Issues")
    
    try:
        response = requests.get(f"{BASE_URL}/optimizer/issues?limit=10")
        
        if response.status_code == 200:
            issues = response.json()
            print(f"✅ Found {len(issues)} issues")
            
            if issues:
                print(f"\n📋 Recent Issues:")
                for i, issue in enumerate(issues[:5], 1):
                    print(f"\n   {i}. [{issue['severity'].upper()}] {issue['title']}")
                    print(f"      Type: {issue['issue_type']}")
                    print(f"      Resolved: {'Yes ✅' if issue.get('resolved') else 'No ⏳'}")
                    print(f"      Detected: {issue['detected_at']}")
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("\n" + "🚀"*40)
    print("  SQL OPTIMIZER - COMPREHENSIVE FEATURE TEST")
    print("🚀"*40)
    print(f"\nTesting against: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Optimize query (main feature)
    optimization_id = test_optimize_query()
    
    if optimization_id:
        # Test 2: Explain execution plan
        test_explain_plan(optimization_id)
        
        # Test 3: Generate fix recommendations
        test_generate_fixes(optimization_id)
        
        # Test 4: Apply fix (dry run)
        test_apply_fix_dry_run(optimization_id)
        
        # Test 5: Validate performance
        test_validate_performance(optimization_id)
    
    # Test 6: List issues
    test_list_issues()
    
    print_section("TEST SUMMARY")
    print("""
✅ All tests completed!

If you see ✅ for most tests, all features are working correctly.

To see these features in the UI:
1. Open http://localhost:5173
2. Go to Optimizer page
3. Enter a SQL query
4. Check "Include execution plan analysis"
5. Click "Optimize Query"
6. SCROLL DOWN to see:
   - 📊 Execution Plan Explanation
   - 🔧 Actionable Fix Recommendations
   - 📈 Performance Validation

Note: Some tests may fail if:
- Database connection is not configured (connection_id: 1)
- Ollama is not running
- sqlcoder:latest model is not installed
    """)

if __name__ == "__main__":
    main()
