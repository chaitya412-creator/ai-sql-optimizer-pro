"""
Comprehensive Test Data Population Script
Creates 17 optimizations with all 10 issue types and 20 total issues
Connects to PostgreSQL database at 192.168.1.81:5432
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime, timedelta
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, Connection, Optimization
from app.core.security import security_manager

# PostgreSQL Database configuration
DB_CONFIG = {
    "dbname": "mydb",
    "user": "admin",
    "password": "admin123",
    "host": "192.168.1.81",
    "port": 5432
}

DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"


def create_detection_result(issue_type, severity, count=1):
    """Create a detection result with specified issue type and severity"""
    issues = []
    
    issue_configs = {
        "missing_index": {
            "title": "Missing index on frequently queried column",
            "description": "Sequential scan on large table without proper indexing",
            "affected_objects": ["users.email", "orders.customer_id"],
            "recommendations": [
                "CREATE INDEX idx_users_email ON users(email);",
                "CREATE INDEX idx_orders_customer_id ON orders(customer_id);",
                "Add indexes on frequently queried columns"
            ]
        },
        "inefficient_index": {
            "title": "Inefficient index with low selectivity",
            "description": "Index on column with only 2-3 distinct values (low cardinality)",
            "affected_objects": ["customers.status", "orders.status"],
            "recommendations": [
                "Consider composite index for better selectivity",
                "Review index usage statistics with pg_stat_user_indexes",
                "DROP INDEX if not used frequently"
            ]
        },
        "poor_join_strategy": {
            "title": "Inefficient nested loop join on large dataset",
            "description": "Nested loop join processing large dataset without proper indexes",
            "affected_objects": ["users", "orders", "order_items"],
            "recommendations": [
                "Add indexes on join columns",
                "Consider Hash Join for large datasets",
                "Increase work_mem for hash joins",
                "ANALYZE tables to update statistics"
            ]
        },
        "full_table_scan": {
            "title": "Full table scan on large table",
            "description": "Scanning 500,000+ rows without index utilization",
            "affected_objects": ["logs", "transactions", "events"],
            "recommendations": [
                "Add index on WHERE clause columns",
                "Consider table partitioning for large tables",
                "Review query filters and add time-based constraints",
                "Use EXPLAIN ANALYZE to verify index usage"
            ]
        },
        "suboptimal_pattern": {
            "title": "Suboptimal SQL pattern detected",
            "description": "Anti-patterns: SELECT *, LIKE with leading wildcard, or function on indexed column",
            "affected_objects": ["query_pattern"],
            "recommendations": [
                "Specify only required columns instead of SELECT *",
                "Avoid leading wildcards in LIKE patterns",
                "Move functions to comparison value, not indexed column",
                "Consider full-text search for text matching"
            ]
        },
        "stale_statistics": {
            "title": "Stale table statistics affecting query planning",
            "description": "Table statistics not updated recently, causing suboptimal query plans",
            "affected_objects": ["products", "orders", "customers"],
            "recommendations": [
                "Run ANALYZE on affected tables",
                "Enable autovacuum and auto-analyze",
                "Schedule regular VACUUM ANALYZE",
                "Monitor pg_stat_user_tables for last analyze time"
            ]
        },
        "wrong_cardinality": {
            "title": "Wrong cardinality estimate by query planner",
            "description": "Query optimizer misestimating row counts due to skewed data distribution",
            "affected_objects": ["customers.status", "orders.priority"],
            "recommendations": [
                "Update table statistics with ANALYZE",
                "Consider histogram statistics for skewed columns",
                "Review data distribution and outliers",
                "Use ALTER TABLE SET STATISTICS for better estimates"
            ]
        },
        "orm_generated": {
            "title": "ORM-generated SQL anti-pattern",
            "description": "Excessive JOINs, N+1 query pattern, or lazy loading issues",
            "affected_objects": ["orm_pattern", "relationships"],
            "recommendations": [
                "Use eager loading with JOIN FETCH",
                "Implement select_related() or prefetch_related()",
                "Batch queries together to avoid N+1",
                "Review ORM query generation and optimize"
            ]
        },
        "high_io_workload": {
            "title": "High disk I/O workload detected",
            "description": "Low buffer cache hit ratio with excessive disk reads",
            "affected_objects": ["io_performance", "buffer_cache"],
            "recommendations": [
                "Add indexes to reduce disk reads",
                "Increase shared_buffers size",
                "Use covering indexes to avoid table lookups",
                "Monitor pg_statio_user_tables for cache hits"
            ]
        },
        "inefficient_reporting": {
            "title": "Inefficient reporting query",
            "description": "Multiple aggregations or window functions without proper optimization",
            "affected_objects": ["reporting_query", "aggregations"],
            "recommendations": [
                "Add LIMIT clause for pagination",
                "Consider materialized views for complex reports",
                "Cache results if data doesn't change frequently",
                "Add time-based filters to reduce dataset"
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
            "metrics": {
                "estimated_rows": 50000 + (i * 10000),
                "actual_rows": 48000 + (i * 9500),
                "execution_time_ms": 150 + (i * 50)
            },
            "detected_at": datetime.utcnow().isoformat()
        })
    
    # Count by severity
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


def clear_existing_data(session):
    """Clear existing test data"""
    try:
        # Delete existing optimizations
        deleted = session.query(Optimization).delete()
        session.commit()
        print(f"✓ Cleared {deleted} existing optimizations")
        return True
    except Exception as e:
        print(f"⚠ Warning: Could not clear existing data: {e}")
        session.rollback()
        return False


def create_comprehensive_test_data():
    """Create 17 optimizations with all 10 issue types and 20 total issues"""
    
    # Create engine and session
    try:
        engine = create_engine(DATABASE_URL)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"✓ Connected to PostgreSQL database at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return False
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get or create a test connection
        connection = session.query(Connection).first()
        
        if not connection:
            print("⚠ No connections found. Creating test connection...")
            # Create a test connection
            connection = Connection(
                name="Test PostgreSQL",
                engine="postgresql",
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=DB_CONFIG['dbname'],
                username=DB_CONFIG['user'],
                password_encrypted=security_manager.encrypt_password(DB_CONFIG['password']),
                ssl_enabled=False,
                monitoring_enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(connection)
            session.commit()
            print(f"✓ Created test connection: {connection.name} (ID: {connection.id})")
        else:
            print(f"✓ Using existing connection: {connection.name} (ID: {connection.id})")
        
        # Clear existing data
        print("\nClearing existing test data...")
        clear_existing_data(session)
        
        # Define 17 test cases covering all 10 issue types with 20 total issues
        test_cases = [
            # 1. Missing Index - Critical (2 issues)
            {
                "original_sql": "SELECT * FROM users WHERE email = 'user@example.com' AND status = 'active'",
                "optimized_sql": "SELECT id, username, email FROM users WHERE email = 'user@example.com' AND status = 'active'",
                "issue_type": "missing_index",
                "severity": "critical",
                "count": 2,
                "explanation": "Added composite index on (email, status) and specified required columns",
                "recommendations": "CREATE INDEX idx_users_email_status ON users(email, status);",
                "improvement": 85.5
            },
            # 2. Missing Index - High (1 issue)
            {
                "original_sql": "SELECT * FROM orders WHERE customer_id = 12345 AND order_date > '2024-01-01'",
                "optimized_sql": "SELECT id, order_number, total_amount FROM orders WHERE customer_id = 12345 AND order_date > '2024-01-01'",
                "issue_type": "missing_index",
                "severity": "high",
                "count": 1,
                "explanation": "Added composite index on (customer_id, order_date) for faster range queries",
                "recommendations": "CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);",
                "improvement": 72.3
            },
            # 3. Inefficient Index - High (1 issue)
            {
                "original_sql": "SELECT * FROM customers WHERE status = 'active' ORDER BY created_at DESC",
                "optimized_sql": "SELECT id, name, email FROM customers WHERE status = 'active' AND created_at > '2023-01-01' ORDER BY created_at DESC",
                "issue_type": "inefficient_index",
                "severity": "high",
                "count": 1,
                "explanation": "Added date filter and composite index for better selectivity",
                "recommendations": "CREATE INDEX idx_customers_status_created ON customers(status, created_at DESC);",
                "improvement": 68.9
            },
            # 4. Inefficient Index - Medium (1 issue)
            {
                "original_sql": "SELECT COUNT(*) FROM orders WHERE status = 'pending'",
                "optimized_sql": "SELECT COUNT(*) FROM orders WHERE status = 'pending' AND created_at > NOW() - INTERVAL '30 days'",
                "issue_type": "inefficient_index",
                "severity": "medium",
                "count": 1,
                "explanation": "Added time constraint to improve index selectivity",
                "recommendations": "CREATE INDEX idx_orders_status_created ON orders(status, created_at);",
                "improvement": 45.2
            },
            # 5. Poor Join Strategy - Critical (1 issue)
            {
                "original_sql": """SELECT u.*, o.*, p.* FROM users u
                    JOIN orders o ON u.id = o.user_id
                    JOIN order_items oi ON o.id = oi.order_id
                    JOIN products p ON oi.product_id = p.id
                    WHERE u.created_at > '2024-01-01'""",
                "optimized_sql": """SELECT u.id, u.username, o.id, o.order_number, p.name, p.price
                    FROM users u
                    JOIN orders o ON u.id = o.user_id
                    JOIN order_items oi ON o.id = oi.order_id
                    JOIN products p ON oi.product_id = p.id
                    WHERE u.created_at > '2024-01-01' AND u.status = 'active'""",
                "issue_type": "poor_join_strategy",
                "severity": "critical",
                "count": 1,
                "explanation": "Added indexes on all join columns and specified required columns",
                "recommendations": "CREATE INDEX idx_orders_user_id ON orders(user_id); CREATE INDEX idx_order_items_order_id ON order_items(order_id); CREATE INDEX idx_order_items_product_id ON order_items(product_id);",
                "improvement": 78.4
            },
            # 6. Poor Join Strategy - High (1 issue)
            {
                "original_sql": """SELECT c.*, o.* FROM customers c
                    LEFT JOIN orders o ON c.id = o.customer_id
                    WHERE c.country = 'USA'""",
                "optimized_sql": """SELECT c.id, c.name, COUNT(o.id) as order_count
                    FROM customers c
                    LEFT JOIN orders o ON c.id = o.customer_id
                    WHERE c.country = 'USA'
                    GROUP BY c.id, c.name""",
                "issue_type": "poor_join_strategy",
                "severity": "high",
                "count": 1,
                "explanation": "Used aggregation instead of returning all order data",
                "recommendations": "CREATE INDEX idx_customers_country ON customers(country); CREATE INDEX idx_orders_customer_id ON orders(customer_id);",
                "improvement": 65.7
            },
            # 7. Full Table Scan - Critical (2 issues)
            {
                "original_sql": "SELECT * FROM logs WHERE message LIKE '%error%' OR message LIKE '%exception%'",
                "optimized_sql": "SELECT id, log_level, message, created_at FROM logs WHERE log_level IN ('ERROR', 'CRITICAL') AND created_at > NOW() - INTERVAL '7 days'",
                "issue_type": "full_table_scan",
                "severity": "critical",
                "count": 2,
                "explanation": "Changed to indexed column and added time filter to avoid full scan",
                "recommendations": "CREATE INDEX idx_logs_level_created ON logs(log_level, created_at); Consider full-text search for message content;",
                "improvement": 92.1
            },
            # 8. Full Table Scan - High (1 issue)
            {
                "original_sql": "SELECT * FROM transactions WHERE amount > 1000 ORDER BY created_at DESC",
                "optimized_sql": "SELECT id, transaction_id, amount, created_at FROM transactions WHERE amount > 1000 AND created_at > NOW() - INTERVAL '90 days' ORDER BY created_at DESC LIMIT 100",
                "issue_type": "full_table_scan",
                "severity": "high",
                "count": 1,
                "explanation": "Added time filter, pagination, and index on amount column",
                "recommendations": "CREATE INDEX idx_transactions_amount_created ON transactions(amount, created_at DESC);",
                "improvement": 71.8
            },
            # 9. Suboptimal Pattern - Medium (2 issues)
            {
                "original_sql": "SELECT * FROM products WHERE category = 'Electronics' AND name LIKE '%phone%'",
                "optimized_sql": "SELECT id, name, price, stock_quantity FROM products WHERE category = 'Electronics' AND name ILIKE 'phone%'",
                "issue_type": "suboptimal_pattern",
                "severity": "medium",
                "count": 2,
                "explanation": "Removed SELECT *, changed to prefix LIKE, specified columns",
                "recommendations": "Always specify required columns; Avoid leading wildcards; Consider full-text search for complex text matching;",
                "improvement": 48.6
            },
            # 10. Suboptimal Pattern - Medium (1 issue)
            {
                "original_sql": "SELECT DISTINCT user_id FROM orders WHERE status = 'completed'",
                "optimized_sql": "SELECT user_id FROM orders WHERE status = 'completed' GROUP BY user_id",
                "issue_type": "suboptimal_pattern",
                "severity": "medium",
                "count": 1,
                "explanation": "Replaced DISTINCT with GROUP BY for better performance",
                "recommendations": "Use GROUP BY instead of DISTINCT when possible; Add index on status column;",
                "improvement": 38.4
            },
            # 11. Suboptimal Pattern - Low (1 issue)
            {
                "original_sql": "SELECT * FROM users WHERE UPPER(email) = 'TEST@EXAMPLE.COM'",
                "optimized_sql": "SELECT id, username, email FROM users WHERE email = 'test@example.com'",
                "issue_type": "suboptimal_pattern",
                "severity": "low",
                "count": 1,
                "explanation": "Removed function from indexed column, normalized comparison value",
                "recommendations": "Store email in lowercase or create functional index; Avoid functions on indexed columns;",
                "improvement": 25.3
            },
            # 12. Stale Statistics - Medium (1 issue)
            {
                "original_sql": "SELECT COUNT(*) FROM orders WHERE status = 'pending' AND priority = 'high'",
                "optimized_sql": "SELECT COUNT(*) FROM orders WHERE status = 'pending' AND priority = 'high' AND created_at > NOW() - INTERVAL '7 days'",
                "issue_type": "stale_statistics",
                "severity": "medium",
                "count": 1,
                "explanation": "Added time filter and updated table statistics",
                "recommendations": "ANALYZE orders; Enable autovacuum; Schedule regular VACUUM ANALYZE;",
                "improvement": 42.7
            },
            # 13. Wrong Cardinality - High (1 issue)
            {
                "original_sql": "SELECT * FROM customers WHERE status = 'inactive' AND last_login < '2023-01-01'",
                "optimized_sql": "SELECT id, name, email FROM customers WHERE status = 'inactive' AND last_login < '2023-01-01' AND created_at < '2022-01-01'",
                "issue_type": "wrong_cardinality",
                "severity": "high",
                "count": 1,
                "explanation": "Added additional filter for skewed data distribution",
                "recommendations": "ANALYZE customers; ALTER TABLE customers ALTER COLUMN status SET STATISTICS 1000; Review data distribution;",
                "improvement": 61.5
            },
            # 14. Wrong Cardinality - Medium (1 issue)
            {
                "original_sql": "SELECT * FROM orders WHERE priority = 'urgent' AND status != 'cancelled'",
                "optimized_sql": "SELECT id, order_number, priority FROM orders WHERE priority = 'urgent' AND status IN ('pending', 'processing', 'completed')",
                "issue_type": "wrong_cardinality",
                "severity": "medium",
                "count": 1,
                "explanation": "Changed negative condition to positive IN clause for better estimates",
                "recommendations": "ANALYZE orders; Use positive conditions instead of NOT; Update statistics on priority column;",
                "improvement": 44.9
            },
            # 15. ORM Generated - Critical (1 issue)
            {
                "original_sql": "SELECT * FROM users WHERE id = 1",
                "optimized_sql": """SELECT u.*, o.id, o.order_number, o.total_amount
                    FROM users u
                    LEFT JOIN orders o ON u.id = o.user_id
                    WHERE u.id = 1""",
                "issue_type": "orm_generated",
                "severity": "critical",
                "count": 1,
                "explanation": "Used eager loading to prevent N+1 query problem",
                "recommendations": "Use select_related() or prefetch_related() in ORM; Implement JOIN FETCH; Avoid lazy loading in loops;",
                "improvement": 88.2
            },
            # 16. ORM Generated - High (1 issue)
            {
                "original_sql": """SELECT u.*, s.*, o.*, c.*, p.*
                    FROM users u
                    LEFT JOIN sessions s ON u.id = s.user_id
                    LEFT JOIN orders o ON u.id = o.user_id
                    LEFT JOIN customers c ON o.customer_id = c.id
                    LEFT JOIN products p ON p.id IN (SELECT product_id FROM order_items WHERE order_id = o.id)""",
                "optimized_sql": """SELECT u.id, u.username, COUNT(DISTINCT o.id) as order_count, COUNT(DISTINCT s.id) as session_count
                    FROM users u
                    LEFT JOIN sessions s ON u.id = s.user_id
                    LEFT JOIN orders o ON u.id = o.user_id
                    WHERE u.status = 'active'
                    GROUP BY u.id, u.username""",
                "issue_type": "orm_generated",
                "severity": "high",
                "count": 1,
                "explanation": "Reduced excessive JOINs and used aggregation",
                "recommendations": "Split into multiple queries; Use lazy loading for rarely accessed data; Review ORM relationship configuration;",
                "improvement": 74.6
            },
            # 17. High IO Workload - High (1 issue) + Inefficient Reporting - Medium (1 issue)
            {
                "original_sql": """SELECT DATE_TRUNC('day', created_at) as day,
                    COUNT(*) as total_orders,
                    SUM(total_amount) as revenue,
                    AVG(total_amount) as avg_order,
                    MAX(total_amount) as max_order
                    FROM orders
                    GROUP BY DATE_TRUNC('day', created_at)
                    ORDER BY day DESC""",
                "optimized_sql": """SELECT DATE_TRUNC('day', created_at) as day,
                    COUNT(*) as total_orders,
                    SUM(total_amount) as revenue,
                    AVG(total_amount) as avg_order,
                    MAX(total_amount) as max_order
                    FROM orders
                    WHERE created_at > NOW() - INTERVAL '90 days'
                    GROUP BY DATE_TRUNC('day', created_at)
                    ORDER BY day DESC
                    LIMIT 90""",
                "issue_type": "high_io_workload",
                "severity": "high",
                "count": 1,
                "explanation": "Added time filter and pagination to reduce I/O workload",
                "recommendations": "CREATE INDEX idx_orders_created ON orders(created_at); Consider materialized view for daily reports; Increase shared_buffers;",
                "improvement": 69.3
            }
        ]
        
        # Add the inefficient_reporting issue to the last optimization
        # This will give us 20 total issues (19 from above + 1 more)
        
        print(f"\n{'='*80}")
        print("CREATING COMPREHENSIVE TEST DATA")
        print(f"{'='*80}\n")
        print(f"Target: 17 optimizations, 10 issue types, 20 total issues\n")
        
        created_count = 0
        issue_type_counts = {}
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        total_issues = 0
        
        for i, test_case in enumerate(test_cases, 1):
            # Create detection result
            detection_result = create_detection_result(
                test_case["issue_type"],
                test_case["severity"],
                test_case["count"]
            )
            
            # For the last optimization, add an additional inefficient_reporting issue
            if i == 17:
                reporting_issue = create_detection_result("inefficient_reporting", "medium", 1)
                # Merge the issues
                detection_result["issues"].extend(reporting_issue["issues"])
                detection_result["total_issues"] += 1
                detection_result["medium_issues"] += 1
                detection_result["summary"] = f"Detected {detection_result['total_issues']} issues: high_io_workload and inefficient_reporting"
                print(f"  → Adding inefficient_reporting issue to optimization #{i}")
            
            # Create optimization
            optimization = Optimization(
                query_id=None,
                connection_id=connection.id,
                original_sql=test_case["original_sql"],
                optimized_sql=test_case["optimized_sql"],
                execution_plan=None,
                explanation=test_case["explanation"],
                recommendations=test_case["recommendations"],
                estimated_improvement_pct=test_case["improvement"],
                status="pending",
                created_at=datetime.utcnow() - timedelta(hours=i),
                detected_issues=detection_result
            )
            
            session.add(optimization)
            
            # Track counts
            issue_type = test_case["issue_type"]
            issue_count = test_case["count"]
            issue_type_counts[issue_type] = issue_type_counts.get(issue_type, 0) + issue_count
            severity_counts[test_case["severity"]] += issue_count
            total_issues += issue_count
            
            # Add the extra inefficient_reporting issue to counts
            if i == 17:
                issue_type_counts["inefficient_reporting"] = issue_type_counts.get("inefficient_reporting", 0) + 1
                severity_counts["medium"] += 1
                total_issues += 1
            
            created_count += 1
            
            print(f"✓ Optimization #{i:2d}: {test_case['issue_type']:25s} ({test_case['severity']:8s}) - {test_case['count']} issue(s)")
        
        # Commit all changes
        session.commit()
        
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}\n")
        print(f"✓ Created {created_count} optimizations with detected issues\n")
        
        print(f"Issue Type Distribution (All 10 types):")
        for issue_type, count in sorted(issue_type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {issue_type.replace('_', ' ').title():35s}: {count:2d} issue(s)")
        
        print(f"\nSeverity Distribution:")
        print(f"  • Critical: {severity_counts['critical']:2d} issues")
        print(f"  • High:     {severity_counts['high']:2d} issues")
        print(f"  • Medium:   {severity_counts['medium']:2d} issues")
        print(f"  • Low:      {severity_counts['low']:2d} issues")
        
        print(f"\n✓ Total issues: {total_issues}")
        print(f"✓ Unique issue types: {len(issue_type_counts)}")
        
        print(f"\n{'='*80}")
        print("✅ DATA POPULATION COMPLETE")
        print(f"{'='*80}\n")
        
        print("Next steps:")
        print("1. Restart the backend server (if running)")
        print("2. Refresh the dashboard in your browser")
        print("3. Verify the dashboard shows:")
        print(f"   • 17 optimizations with detected issues")
        print(f"   • All 10 issue types in 'Issues by Type' section")
        print(f"   • 20 total issues across various severity levels")
        print("4. Check 'Queries with Detected Issues' section displays all queries")
        
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
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST DATA POPULATION SCRIPT")
    print("="*80)
    print(f"\nDatabase: PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Database Name: {DB_CONFIG['dbname']}")
    print(f"User: {DB_CONFIG['user']}")
    print("\nThis script will:")
    print("• Clear existing test data")
    print("• Create 17 optimizations with detected issues")
    print("• Cover all 10 issue types")
    print("• Generate 20 total issues with various severity levels")
    print("\n" + "="*80 + "\n")
    
    input("Press Enter to continue or Ctrl+C to cancel...")
    
    success = create_comprehensive_test_data()
    
    if success:
        print("\n✅ Success! Dashboard should now display comprehensive test data.")
        print("   Refresh your browser to see the updated dashboard.")
    else:
        print("\n❌ Failed to populate data. Check error messages above.")
