"""
Add optimizations with detected issues directly via API
"""
import requests
import json
import time

# API endpoint
API_URL = "http://localhost:8000"

# Sample problematic query
TEST_QUERY = "SELECT * FROM users WHERE id > 100"

def get_connection_id():
    """Get the first available connection ID"""
    try:
        response = requests.get(f"{API_URL}/api/connections")
        if response.status_code == 200:
            connections = response.json()
            if len(connections) > 0:
                return connections[0]["id"]
        return None
    except Exception as e:
        print(f"Error getting connection ID: {e}")
        return None

def optimize_query():
    """Optimize a query to generate detection data"""
    print("\n" + "="*70)
    print("ADDING OPTIMIZATION WITH DETECTED ISSUES")
    print("="*70)
    
    connection_id = get_connection_id()
    if not connection_id:
        print("❌ No connection found. Please create a connection first.")
        return
    
    print(f"\nOptimizing query using connection ID: {connection_id}")
    print(f"Query: {TEST_QUERY}")
    
    optimization_data = {
        "connection_id": connection_id,
        "sql_query": TEST_QUERY,
        "include_execution_plan": True
    }
    
    try:
        response = requests.post(f"{API_URL}/api/optimizer/optimize", json=optimization_data)
        if response.status_code == 201 or response.status_code == 200:
            optimization = response.json()
            print(f"✓ Created optimization with ID: {optimization['id']}")
            
            # Check if detected_issues is present
            if "detected_issues" in optimization and optimization["detected_issues"]:
                issues_count = optimization["detected_issues"].get("total_issues", 0)
                print(f"✓ Detected {issues_count} issues")
            else:
                print("⚠️ No issues detected or detected_issues field missing")
            
            # Apply the optimization to increase the count
            apply_data = {
                "optimization_id": optimization["id"],
                "force": True
            }
            
            response = requests.post(f"{API_URL}/api/optimizer/apply", json=apply_data)
            if response.status_code == 200:
                print(f"✓ Applied optimization")
            else:
                print(f"Failed to apply optimization: {response.text}")
            
            return optimization
        else:
            print(f"Failed to optimize query: {response.text}")
            return None
    except Exception as e:
        print(f"Error optimizing query: {e}")
        return None

def check_dashboard_stats():
    """Check dashboard statistics"""
    print("\nChecking dashboard statistics...")
    
    try:
        response = requests.get(f"{API_URL}/api/dashboard/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✓ Total Queries: {stats['total_queries_discovered']}")
            print(f"✓ Total Optimizations: {stats['total_optimizations']}")
            print(f"✓ Total Detected Issues: {stats['total_detected_issues']}")
            return stats
        else:
            print(f"Failed to get dashboard stats: {response.text}")
            return None
    except Exception as e:
        print(f"Error checking dashboard stats: {e}")
        return None

def main():
    # Step 1: Optimize a query
    optimization = optimize_query()
    
    if not optimization:
        print("\n❌ Failed to create optimization. Exiting.")
        return
    
    # Step 2: Wait for backend to process
    print("\nWaiting for backend to process data...")
    time.sleep(3)
    
    # Step 3: Check dashboard stats
    stats = check_dashboard_stats()
    
    print("\n" + "="*70)
    print("✅ PROCESS COMPLETE")
    print("="*70)
    
    if stats:
        if stats["total_optimizations"] > 0 or stats["total_detected_issues"] > 0:
            print("\nDashboard should now display non-zero values for optimizations and/or detected issues.")
            print("Please refresh the dashboard page in your browser.")
        else:
            print("\nDashboard stats still show zero for optimizations and detected issues.")
            print("Please try the following:")
            print("1. Restart the backend service: docker-compose restart backend")
            print("2. Refresh the dashboard page in your browser")
            print("3. Try running a query optimization through the UI")
    
    print("\nIf the issue persists, there might be a database schema mismatch.")
    print("You may need to rebuild the containers with: docker-compose down && docker-compose up -d")

if __name__ == "__main__":
    main()
