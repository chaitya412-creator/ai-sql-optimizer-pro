"""
Complete setup script for dashboard detection testing
Creates connection and optimizations with all 9 issue types
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime, timedelta
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, Connection, Optimization
from app.core.security import security_manager

# Database configuration
DATABASE_URL = "sqlite:///backend/app/db/observability.db"

def create_test_connection(session):
    """Create a test database connection"""
    print("\n1. Creating test connection...")
    
    # Check if connection already exists
    existing = session.query(Connection).first()
    if existing:
        print(f"✓ Using existing connection: {existing.name} (ID: {existing.id})")
        return existing
    
    # Create new test connection
    encrypted_password = security_manager.encrypt("admin123")
    
    connection = Connection(
        name="Test PostgreSQL",
        engine="postgresql",
        host="192.168.1.81",
        port=5432,
        database="mydb",
        username="admin",
        password_encrypted=encrypted_password,
        ssl_enabled=False,
        monitoring_enabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(connection)
    session.commit()
    session.refresh(connection)
    
    print(f"✓ Created test connection: {connection.name} (ID: {connection.id})")
    return connection


def create_detection_result(issue_type, severity, count=1):
    """Create a detection result with specified issue type"""
    issues = []
    
    issue_configs = {
        "missing_index": {
            "title": "Missing index on table",
            "description": "Sequential scan on large table without index",
            "affected_objects": ["users", "orders"],
            "recommendations": [
                "CREATE INDEX idx_users_email ON users(email);",
                "Add index on frequently queried columns"
            ]
        },
        "inefficient_index": {
            "title": "Inefficient index with low selectivity",
            "description": "Index on status column with only 2-3 distinct values",
            "affected_objects": ["customers"],
            "recommendations": [
                "Consider composite index for better selectivity",
                "Review index usage statistics"
            ]
        },
        "poor_join_strategy": {
            "title": "Inefficient nested loop join",
            "description": "Nested loop join processing large dataset",
            "affected_objects": ["join_operation"],
            "recommendations": [
                "Add indexes on join columns",
                "Consider Hash Join for large datasets"
            ]
        },
        "full_table_scan": {
            "title": "Full table scan on large table",
            "description": "Scanning 500,000+ rows without index",
            "affected_objects": ["logs", "transactions"],
            "recommendations": [
                "Add index on WHERE clause columns",
                "Consider table partitioning"
            ]
        },
        "suboptimal_pattern": {
            "title": "Suboptimal query pattern detected",
            "description": "SELECT *, LIKE with leading wildcard, or function on indexed column",
            "affected_objects": ["query_pattern"],
            "recommendations": [
                "Specify only required columns",
                "Avoid leading wildcards in LIKE"
            ]
        },
        "stale_statistics": {
            "title": "Stale table statistics",
            "description": "Table statistics not updated recently",
            "affected_objects": ["products", "orders"],
            "recommendations": [
                "Run ANALYZE on affected tables",
                "Enable auto-analyze"
            ]
        },
        "wrong_cardinality": {
            "title": "Wrong cardinality estimate",
            "description": "Query optimizer misestimating row counts",
            "affected_objects": ["customers"],
            "recommendations": [
                "Update table statistics",
                "Consider histogram statistics"
            ]
        },
        "orm_generated": {
            "title": "ORM-generated SQL anti-pattern",
            "description": "Excessive JOINs or N+1 query pattern",
            "affected_objects": ["orm_pattern"],
            "recommendations": [
                "Use eager loading / JOIN FETCH",
                "Batch queries together"
            ]
        },
        "high_io_workload": {
            "title": "High disk I/O workload",
            "description": "Low cache hit ratio with excessive disk reads",
            "affected_objects": ["io_performance"],
            "recommendations": [
                "Add indexes to reduce disk reads",
                "Increase buffer pool size"
            ]
        },
        "inefficient_reporting": {
            "title": "Inefficient reporting query",
            "description": "Multiple aggregations without pagination",
            "affected_objects": ["reporting_query"],
            "recommendations": [
                "Add LIMIT clause for pagination",
                "Consider materialized views"
            ]
        }
    }
    
    config = issue_configs.get(issue_type, issue_configs["suboptimal_pattern"])
    
    for i in range(count):
        issues.append({
            "issue_type": issue_type,
            "severity": severity,
            "title": config["title"],
            "description": config["description"],
            "affected_objects": config["affected_objects"],
            "recommendations": config["recommendations"],
            "metrics": {},
            "detected_at": datetime.utcnow().isoformat()
        })
    
    severity_counts = {
        "critical": sum(1 for i in issues if i["severity"] == "critical"),
        "high": sum(1 for i in issues if i["severity"] == "high"),
        "medium": sum(1 for i in issues if i["severity"] == "medium"),
        "low": sum(1 for i in issues if i["severity"] == "low")
    }
    
    return {
        "issues": issues,
        "recommendations": config["recommendations"],
        "summary": f"Detected {len(issues)} {issue_type.replace('_', ' ')} issue(s)",
        "total_issues": len(issues),
        "critical_issues": severity_counts["critical"],
        "high_issues": severity_counts["high"],
        "medium_issues": severity_counts["medium"],
        "low_issues": severity_counts["low"]
    }


def create_test_optimizations(session, connection):
    """Create test optimizations with all 9 issue types"""
    print("\n2. Creating test optimizations with detected issues...")
    
    test_cases = [
        {"original_sql": "SELECT * FROM users WHERE email = 'user@example.com'", "optimized_sql": "SELECT id, username, email FROM users WHERE email = 'user@example.com'", "issue_type": "missing_index", "severity": "critical", "count": 2},
        {"original_sql": "SELECT * FROM orders WHERE customer_id = 12345", "optimized_sql": "SELECT id, order_number FROM orders WHERE customer_id = 12345", "issue_type": "missing_index", "severity": "high", "count": 1},
        {"original_sql": "SELECT * FROM customers WHERE status = 'active'", "optimized_sql": "SELECT id, name FROM customers WHERE status = 'active'", "issue_type": "inefficient_index", "severity": "medium", "count": 1},
        {"original_sql": "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id", "optimized_sql": "SELECT u.id, o.id FROM users u JOIN orders o ON u.id = o.user_id", "issue_type": "poor_join_strategy", "severity": "high", "count": 1},
        {"original_sql": "SELECT * FROM logs WHERE message LIKE '%error%'", "optimized_sql": "SELECT id, message FROM logs WHERE log_level = 'ERROR'", "issue_type": "full_table_scan", "severity": "critical", "count": 2},
        {"original_sql": "SELECT * FROM transactions WHERE amount > 1000", "optimized_sql": "SELECT id, amount FROM transactions WHERE amount > 1000", "issue_type": "full_table_scan", "severity": "high", "count": 1},
        {"original_sql": "SELECT * FROM products WHERE category = 'Electronics'", "optimized_sql": "SELECT id, name, price FROM products WHERE category = 'Electronics'", "issue_type": "suboptimal_pattern", "severity": "medium", "count": 2},
        {"original_sql": "SELECT * FROM products WHERE name LIKE '%phone%'", "optimized_sql": "SELECT id, name FROM products WHERE name ILIKE 'phone%'", "issue_type": "suboptimal_pattern", "severity": "medium", "count": 1},
        {"original_sql": "SELECT * FROM users WHERE UPPER(email) = 'TEST@EXAMPLE.COM'", "optimized_sql": "SELECT id, email FROM users WHERE email = 'test@example.com'", "issue_type": "suboptimal_pattern", "severity": "low", "count": 1},
        {"original_sql": "SELECT COUNT(*) FROM orders WHERE status = 'pending'", "optimized_sql": "SELECT COUNT(*) FROM orders WHERE status = 'pending' AND created_at > NOW() - INTERVAL '7 days'", "issue_type": "stale_statistics", "severity": "medium", "count": 1},
        {"original_sql": "SELECT * FROM customers WHERE status = 'inactive'", "optimized_sql": "SELECT id, name FROM customers WHERE status = 'inactive'", "issue_type": "wrong_cardinality", "severity": "medium", "count": 1},
        {"original_sql": "SELECT * FROM users WHERE id = 1", "optimized_sql": "SELECT u.*, o.* FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE u.id = 1", "issue_type": "orm_generated", "severity": "critical", "count": 1},
        {"original_sql": "SELECT u.*, s.*, o.* FROM users u LEFT JOIN sessions s ON u.id = s.user_id LEFT JOIN orders o ON u.id = o.user_id", "optimized_sql": "SELECT u.id, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id", "issue_type": "orm_generated", "severity": "high", "count": 1},
        {"original_sql": "SELECT t.*, u.* FROM transactions t JOIN users u ON t.user_id = u.id WHERE t.created_at > NOW() - INTERVAL '30 days'", "optimized_sql": "SELECT t.id, u.username FROM transactions t JOIN users u ON t.user_id = u.id WHERE t.created_at > NOW() - INTERVAL '30 days' LIMIT 100", "issue_type": "high_io_workload", "severity": "high", "count": 1},
        {"original_sql": "SELECT * FROM logs WHERE created_at > NOW() - INTERVAL '7 days'", "optimized_sql": "SELECT id, message FROM logs WHERE created_at > NOW() - INTERVAL '7 days' AND log_level IN ('ERROR', 'CRITICAL')", "issue_type": "high_io_workload", "severity": "medium", "count": 1},
        {"original_sql": "SELECT DATE_TRUNC('day', created_at), COUNT(*), SUM(total_amount) FROM orders GROUP BY DATE_TRUNC('day', created_at)", "optimized_sql": "SELECT DATE_TRUNC('day', created_at), COUNT(*), SUM(total_amount) FROM orders WHERE created_at > NOW() - INTERVAL '90 days' GROUP BY DATE_TRUNC('day', created_at) LIMIT 90", "issue_type": "inefficient_reporting", "severity": "medium", "count": 1},
        {"original_sql": "SELECT user_id, COUNT(*), ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) FROM sessions GROUP BY user_id", "optimized_sql": "SELECT user_id, COUNT(*) FROM sessions WHERE started_at > NOW() - INTERVAL '30 days' GROUP BY user_id ORDER BY COUNT(*) DESC LIMIT 100", "issue_type": "inefficient_reporting", "severity": "low", "count": 1}
    ]
    
    created_count = 0
    issue_type_counts = {}
    
    for i, test_case in enumerate(test_cases, 1):
        detection_result = create_detection_result(
            test_case["issue_type"],
            test_case["severity"],
            test_case["count"]
        )
        
        optimization = Optimization(
            query_id=None,
            connection_id=connection.id,
            original_sql=test_case["original_sql"],
            optimized_sql=test_case["optimized_sql"],
            execution_plan=None,
            explanation=f"Optimized to address {test_case['issue_type']}",
            recommendations=f"Apply recommended fixes for {test_case['issue_type']}",
            estimated_improvement_pct=round(20 + (i * 5) % 60, 1),
            status="pending",
            created_at=datetime.utcnow() - timedelta(hours=i),
            detected_issues=detection_result
        )
        
        session.add(optimization)
        
        issue_type = test_case["issue_type"]
        issue_type_counts[issue_type] = issue_type_counts.get(issue_type, 0) + test_case["count"]
        created_count += 1
        
        print(f"   ✓ #{i}: {test_case['issue_type']} ({test_case['severity']}) - {test_case['count']} issue(s)")
    
    session.commit()
    
    print(f"\n✓ Created {created_count} optimizations")
    return issue_type_counts


def main():
    """Main setup function"""
    print("\n" + "="*70)
    print("DASHBOARD DETECTION TEST DATA SETUP")
    print("="*70)
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Step 1: Create test connection
        connection = create_test_connection(session)
        
        # Step 2: Create test optimizations
        issue_type_counts = create_test_optimizations(session, connection)
        
        # Step 3: Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"\nIssue Type Distribution:")
        for issue_type, count in sorted(issue_type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {issue_type.replace('_', ' ').title()}: {count}")
        
        total_issues = sum(issue_type_counts.values())
        print(f"\n✓ Total issues: {total_issues}")
        print(f"✓ Total optimizations: {len(issue_type_counts)}")
        
        print("\n" + "="*70)
        print("✅ SETUP COMPLETE")
        print("="*70)
        
        print("\nNext steps:")
        print("1. Start/restart the backend server")
        print("2. Open dashboard in browser: http://localhost:3000")
        print("3. Verify 'Issues by Type' section displays all categories")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n❌ Setup failed. Check error messages above.")
        sys.exit(1)
