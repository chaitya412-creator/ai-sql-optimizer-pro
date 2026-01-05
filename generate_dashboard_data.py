"""
Generate test data for dashboard display using the API
"""
import requests
import json
import time

# API endpoint
API_URL = "http://localhost:8000"

# Sample problematic queries
TEST_QUERIES = [
    "SELECT * FROM users WHERE id > 100",
    "SELECT name FROM products WHERE name LIKE '%phone%'",
    "SELECT * FROM orders WHERE status = 'pending' OR status = 'processing' OR status = 'shipped' OR status = 'delivered'",
    "SELECT * FROM users WHERE UPPER(email) = 'TEST@EXAMPLE.COM'",
    """
    SELECT u.*, o.*, p.*
    FROM users u
    JOIN orders o ON u.id = o.user_id
    JOIN products p ON o.product_id = p.id
    WHERE u.created_at > '2024-01-01'
    """
]

def create_connection():
    """Create a test database connection"""
    print("\nCreating test connection...")
    
    connection_data = {
        "name": "Test PostgreSQL",
        "engine": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "username": "postgres",
        "password": "password",
        "ssl_enabled": False,
        "monitoring_enabled": True
    }
    
    try:
        response = requests.post(f"{API_URL}/api/connections", json=connection_data)
        if response.status_code == 201 or response.status_code == 200:
            connection = response.json()
            print(f"✓ Created connection with ID: {connection['id']}")
            return connection
        else:
            print(f"Failed to create connection: {response.text}")
            # Try to get existing connections
            response = requests.get(f"{API_URL}/api/connections")
            if response.status_code == 200 and len(response.json()) > 0:
                connection = response.json()[0]
                print(f"✓ Using existing connection: {connection['name']} (ID: {connection['id']})")
                return connection
            return None
    except Exception as e:
        print(f"Error creating connection: {e}")
        return None

def optimize_query(connection_id, sql_query):
    """Optimize a SQL query to generate detection data"""
    print(f"\nOptimizing query: {sql_query[:50]}...")
    
    optimization_data = {
        "connection_id": connection_id,
        "sql_query": sql_query,
        "include_execution_plan": True
    }
    
    try:
        response = requests.post(f"{API_URL}/api/optimizer/optimize", json=optimization_data)
        if response.status_code == 201 or response.status_code == 200:
            optimization = response.json()
            issues_count = 0
            if optimization.get("detected_issues"):
                issues_count = optimization["detected_issues"].get("total_issues", 0)
            print(f"✓ Created optimization with ID: {optimization['id']} - {issues_count} issues")
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
    """Main function to generate test data"""
    print("\n" + "="*70)
    print("GENERATING TEST DATA FOR DASHBOARD")
    print("="*70)
    
    # Step 1: Create or get connection
    connection = create_connection()
    if not connection:
        print("❌ Failed to create or get connection. Exiting.")
        return
    
    # Step 2: Optimize queries
    optimizations = []
    for sql in TEST_QUERIES:
        optimization = optimize_query(connection["id"], sql)
        if optimization:
            optimizations.append(optimization)
        time.sleep(1)  # Small delay to avoid overwhelming the API
    
    # Step 3: Check dashboard stats
    print("\nWaiting for backend to process data...")
    time.sleep(3)
    stats = check_dashboard_stats()
    
    print("\n" + "="*70)
    print("✅ TEST DATA GENERATION COMPLETE")
    print("="*70)
    
    if stats:
        print(f"Dashboard should now display:")
        print(f"- Total Queries: {stats['total_queries_discovered']}")
        print(f"- Total Optimizations: {stats['total_optimizations']}")
        print(f"- Total Detected Issues: {stats['total_detected_issues']}")
    
    print("\nPlease restart the backend service to ensure data is refreshed:")
    print("docker-compose restart backend")
    print("\nThen refresh the dashboard page in your browser.")

if __name__ == "__main__":
    main()
