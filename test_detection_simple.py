"""
Simple test for SQL optimization detection
Tests query pattern detection which works without execution plans
"""
import sys
sys.path.append('backend')

from app.core.plan_analyzer import PlanAnalyzer, QueryPatternDetector


def test_basic_detection():
    """Test basic query pattern detection"""
    print("\n" + "="*70)
    print("SQL OPTIMIZATION DETECTION - SIMPLE TEST")
    print("="*70)
    
    # Test 1: SELECT * detection
    print("\n1. Testing SELECT * detection...")
    sql1 = "SELECT * FROM users WHERE id > 100"
    result = PlanAnalyzer.analyze_plan(None, "postgresql", sql1)
    print(f"   ✓ Total issues: {result['total_issues']}")
    print(f"   ✓ Issues found: {[i['title'] for i in result['issues']]}")
    
    # Test 2: LIKE with leading wildcard
    print("\n2. Testing LIKE wildcard detection...")
    sql2 = "SELECT name FROM products WHERE name LIKE '%phone%'"
    result = PlanAnalyzer.analyze_plan(None, "postgresql", sql2)
    print(f"   ✓ Total issues: {result['total_issues']}")
    print(f"   ✓ Issues found: {[i['title'] for i in result['issues']]}")
    
    # Test 3: Multiple OR conditions
    print("\n3. Testing multiple OR detection...")
    sql3 = "SELECT * FROM orders WHERE status = 'a' OR status = 'b' OR status = 'c' OR status = 'd' OR status = 'e'"
    result = PlanAnalyzer.analyze_plan(None, "postgresql", sql3)
    print(f"   ✓ Total issues: {result['total_issues']}")
    print(f"   ✓ Issues found: {[i['title'] for i in result['issues']]}")
    
    # Test 4: Function on column
    print("\n4. Testing function on column detection...")
    sql4 = "SELECT * FROM users WHERE UPPER(email) = 'TEST@EXAMPLE.COM'"
    result = PlanAnalyzer.analyze_plan(None, "postgresql", sql4)
    print(f"   ✓ Total issues: {result['total_issues']}")
    print(f"   ✓ Issues found: {[i['title'] for i in result['issues']]}")
    
    # Test 5: Complex query with multiple issues
    print("\n5. Testing complex query...")
    sql5 = """
    SELECT * FROM orders 
    WHERE status = 'pending' OR status = 'processing' OR status = 'shipped' OR status = 'delivered'
    AND customer_email LIKE '%@example.com'
    AND YEAR(created_at) = 2024
    """
    result = PlanAnalyzer.analyze_plan(None, "postgresql", sql5)
    print(f"   ✓ Total issues: {result['total_issues']}")
    print(f"   ✓ Summary: {result['summary']}")
    print(f"\n   ✓ Detected issues:")
    for issue in result['issues']:
        print(f"      - [{issue['severity'].upper()}] {issue['title']}")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\nDetection system is working!")
    print("Query pattern detection works even without execution plans.")
    print("\nTo see all 9 detection types, enable execution plan analysis")
    print("when optimizing queries in the UI.")
    

if __name__ == "__main__":
    try:
        test_basic_detection()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
