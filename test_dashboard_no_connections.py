"""
Test Dashboard API endpoints with no connections
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_dashboard_stats():
    """Test /api/dashboard/stats endpoint"""
    print("\n" + "="*70)
    print("Testing: GET /api/dashboard/stats")
    print("="*70)
    
    try:
        response = requests.get(f"{API_URL}/api/dashboard/stats")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify all values are zero/empty
            assert data['total_connections'] == 0, "total_connections should be 0"
            assert data['active_connections'] == 0, "active_connections should be 0"
            assert data['total_queries_discovered'] == 0, "total_queries_discovered should be 0"
            assert data['total_optimizations'] == 0, "total_optimizations should be 0"
            assert data['optimizations_applied'] == 0, "optimizations_applied should be 0"
            assert data['top_bottlenecks'] == [], "top_bottlenecks should be empty"
            assert data['total_detected_issues'] == 0, "total_detected_issues should be 0"
            
            print("✅ PASSED: All values are correctly zero/empty")
            return True
        else:
            print(f"❌ FAILED: Unexpected status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_top_queries():
    """Test /api/dashboard/top-queries endpoint"""
    print("\n" + "="*70)
    print("Testing: GET /api/dashboard/top-queries")
    print("="*70)
    
    try:
        response = requests.get(f"{API_URL}/api/dashboard/top-queries")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            assert data == [], "Should return empty list"
            print("✅ PASSED: Returns empty list")
            return True
        else:
            print(f"❌ FAILED: Unexpected status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_detection_summary():
    """Test /api/dashboard/detection-summary endpoint"""
    print("\n" + "="*70)
    print("Testing: GET /api/dashboard/detection-summary")
    print("="*70)
    
    try:
        response = requests.get(f"{API_URL}/api/dashboard/detection-summary")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            assert data['total_issues'] == 0, "total_issues should be 0"
            assert data['critical_issues'] == 0, "critical_issues should be 0"
            assert data['high_issues'] == 0, "high_issues should be 0"
            assert data['medium_issues'] == 0, "medium_issues should be 0"
            assert data['low_issues'] == 0, "low_issues should be 0"
            assert data['issues_by_type'] == [], "issues_by_type should be empty"
            assert data['recent_critical_issues'] == [], "recent_critical_issues should be empty"
            assert data['total_optimizations_with_issues'] == 0, "total_optimizations_with_issues should be 0"
            
            print("✅ PASSED: All values are correctly zero/empty")
            return True
        else:
            print(f"❌ FAILED: Unexpected status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_queries_with_issues():
    """Test /api/dashboard/queries-with-issues endpoint"""
    print("\n" + "="*70)
    print("Testing: GET /api/dashboard/queries-with-issues")
    print("="*70)
    
    try:
        response = requests.get(f"{API_URL}/api/dashboard/queries-with-issues")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            assert data == [], "Should return empty list"
            print("✅ PASSED: Returns empty list")
            return True
        else:
            print(f"❌ FAILED: Unexpected status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("DASHBOARD NO CONNECTIONS API TEST")
    print("="*70)
    print("Testing all dashboard endpoints with no database connections")
    
    results = []
    results.append(("Dashboard Stats", test_dashboard_stats()))
    results.append(("Top Queries", test_top_queries()))
    results.append(("Detection Summary", test_detection_summary()))
    results.append(("Queries with Issues", test_queries_with_issues()))
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️ SOME TESTS FAILED")
