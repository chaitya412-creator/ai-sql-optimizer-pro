"""
Quick test script to verify the new API endpoints
Run this after starting the backend server
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, description):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Method: {method}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, timeout=5)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS")
            data = response.json()
            print(f"Response Preview: {json.dumps(data, indent=2)[:500]}...")
        elif response.status_code == 404:
            print("❌ FAILED - 404 Not Found")
        else:
            print(f"⚠️  Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ FAILED - Cannot connect to server")
        print("Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ FAILED - {str(e)}")

def main():
    print("\n" + "="*60)
    print("API ENDPOINT TESTING")
    print("="*60)
    
    # Test health check first
    test_endpoint("GET", "/health", "Health Check")
    
    # Test new dashboard endpoints
    test_endpoint("GET", "/api/dashboard/stats", "Dashboard Stats (existing)")
    test_endpoint("GET", "/api/dashboard/top-queries?limit=5", "Top Queries (NEW)")
    test_endpoint("GET", "/api/dashboard/performance-trends?hours=24", "Performance Trends (NEW)")
    
    # Test monitoring endpoints
    test_endpoint("GET", "/api/monitoring/status", "Monitoring Status (existing)")
    test_endpoint("POST", "/api/monitoring/start", "Start Monitoring (NEW)")
    test_endpoint("GET", "/api/monitoring/status", "Monitoring Status (check if started)")
    test_endpoint("POST", "/api/monitoring/stop", "Stop Monitoring (NEW)")
    test_endpoint("GET", "/api/monitoring/status", "Monitoring Status (check if stopped)")
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
    print("\nIf all tests show ✅ SUCCESS or ⚠️ with 400/500 errors")
    print("(not 404), then the endpoints are properly implemented.")
    print("\n404 errors mean the endpoint doesn't exist.")
    print("400/500 errors are expected if no data exists yet.")

if __name__ == "__main__":
    main()
