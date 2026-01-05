"""
Test script to verify monitoring page fix
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_monitoring_status():
    """Test monitoring status endpoint"""
    print("Testing /api/monitoring/status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/monitoring/status")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response Data:")
            print(json.dumps(data, indent=2, default=str))
            
            # Check for expected fields
            expected_fields = [
                'is_running', 
                'last_poll_time', 
                'next_poll_time', 
                'interval_minutes', 
                'queries_discovered', 
                'active_connections'
            ]
            
            missing_fields = [field for field in expected_fields if field not in data]
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
                return False
            else:
                print("✅ All expected fields present!")
                return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_queries_endpoint():
    """Test queries endpoint"""
    print("\nTesting /api/monitoring/queries endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/monitoring/queries")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Number of queries: {len(data)}")
            
            if len(data) > 0:
                print("Sample query:")
                print(json.dumps(data[0], indent=2, default=str))
                
                # Check for expected fields
                expected_fields = [
                    'id',
                    'connection_id',
                    'sql_text',
                    'avg_execution_time',
                    'total_execution_time',
                    'calls',
                    'discovered_at',
                    'last_seen'
                ]
                
                missing_fields = [field for field in expected_fields if field not in data[0]]
                if missing_fields:
                    print(f"❌ Missing fields: {missing_fields}")
                    return False
                else:
                    print("✅ All expected fields present!")
                    return True
            else:
                print("✅ No queries yet (expected for new installation)")
                return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_connections_endpoint():
    """Test connections endpoint"""
    print("\nTesting /api/connections endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/connections")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Number of connections: {len(data)}")
            
            if len(data) > 0:
                print("Sample connection:")
                print(json.dumps(data[0], indent=2, default=str))
                print("✅ Connections endpoint working!")
            else:
                print("✅ No connections yet (expected for new installation)")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Monitoring Page Fix - API Testing")
    print("=" * 60)
    
    # Test health check first
    print("\nTesting health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is running!")
        else:
            print("❌ Backend health check failed")
            exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Please make sure the backend is running on http://localhost:8000")
        exit(1)
    
    # Run tests
    results = []
    results.append(("Monitoring Status", test_monitoring_status()))
    results.append(("Queries Endpoint", test_queries_endpoint()))
    results.append(("Connections Endpoint", test_connections_endpoint()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed! The monitoring page should now work correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
