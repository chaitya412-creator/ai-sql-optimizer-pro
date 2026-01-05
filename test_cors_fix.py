"""
Test script to verify CORS configuration and monitoring endpoints
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_cors_headers(endpoint: str, method: str = "GET") -> Dict[str, Any]:
    """Test CORS headers for a specific endpoint"""
    print(f"\nTesting {method} {endpoint}")
    
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": "Content-Type"
    }
    
    try:
        # Test OPTIONS preflight request
        if method != "OPTIONS":
            print(f"  → Sending OPTIONS preflight request...")
            options_response = requests.options(
                f"{BASE_URL}{endpoint}",
                headers=headers,
                timeout=5
            )
            print(f"  ✓ OPTIONS Status: {options_response.status_code}")
            print(f"  ✓ CORS Headers:")
            for header, value in options_response.headers.items():
                if "access-control" in header.lower():
                    print(f"    - {header}: {value}")
        
        # Test actual request
        print(f"  → Sending {method} request...")
        if method == "GET":
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers={"Origin": "http://localhost:3000"},
                timeout=5
            )
        elif method == "POST":
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                headers={"Origin": "http://localhost:3000"},
                json={},
                timeout=5
            )
        
        print(f"  ✓ {method} Status: {response.status_code}")
        print(f"  ✓ CORS Headers:")
        for header, value in response.headers.items():
            if "access-control" in header.lower():
                print(f"    - {header}: {value}")
        
        # Check for required CORS headers
        required_headers = [
            "access-control-allow-origin",
            "access-control-allow-credentials"
        ]
        
        missing_headers = []
        for header in required_headers:
            if header not in [h.lower() for h in response.headers.keys()]:
                missing_headers.append(header)
        
        if missing_headers:
            print(f"  ⚠ Missing CORS headers: {', '.join(missing_headers)}")
        else:
            print(f"  ✓ All required CORS headers present")
        
        return {
            "success": True,
            "status_code": response.status_code,
            "headers": dict(response.headers)
        }
    
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def test_monitoring_endpoints():
    """Test monitoring endpoints"""
    print_section("Testing Monitoring Endpoints")
    
    endpoints = [
        ("/api/monitoring/status", "GET"),
        ("/api/monitoring/queries", "GET"),
        ("/api/connections", "GET"),
    ]
    
    results = {}
    for endpoint, method in endpoints:
        results[endpoint] = test_cors_headers(endpoint, method)
    
    return results

def test_health_check():
    """Test health check endpoint"""
    print_section("Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"  ✓ Status: {response.status_code}")
        print(f"  ✓ Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    """Main test function"""
    print_section("CORS Configuration Test")
    print("Testing CORS headers and monitoring endpoints")
    print(f"Base URL: {BASE_URL}")
    
    # Test health check first
    health_ok = test_health_check()
    
    if not health_ok:
        print("\n⚠ Warning: Health check failed. Backend may not be running.")
        print("Please start the backend with: docker-compose up backend")
        return
    
    # Test monitoring endpoints
    results = test_monitoring_endpoints()
    
    # Summary
    print_section("Test Summary")
    success_count = sum(1 for r in results.values() if r.get("success", False))
    total_count = len(results)
    
    print(f"\nTests Passed: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n✓ All CORS tests passed!")
        print("\nNext steps:")
        print("1. Restart your frontend: npm run dev")
        print("2. Check the browser console for CORS errors")
        print("3. Verify that API requests are successful")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Ensure backend is running: docker-compose up backend")
        print("2. Check backend logs: docker-compose logs backend")
        print("3. Verify CORS_ORIGINS environment variable is set correctly")

if __name__ == "__main__":
    main()
