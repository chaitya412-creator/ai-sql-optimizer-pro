"""
Populate Dashboard with Detection Data
Creates optimizations with all 9 issue types for dashboard display testing
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
                "Consider Hash Join for large datasets",
                "Increase work_mem for hash joins"
            ]
        },
        "full_table_scan": {
            "title": "Full table scan on large table",
            "description": "Scanning 500,000+ rows without index",
            "affected_objects": ["logs", "transactions"],
            "recommendations": [
                "Add index on WHERE clause columns",
                "Consider table partitioning",
                "Review query filters"
            ]
        },
        "suboptimal_pattern": {
            "title": "Suboptimal query pattern detected",
            "description": "SELECT *, LIKE with leading wildcard, or function on indexed column",
            "affected_objects": ["query_pattern"],
            "recommendations": [
                "Specify only required columns",
                "Avoid leading wildcards in LIKE",
                "Move functions to comparison value"
            ]
        },
        "stale_statistics": {
            "title": "Stale table statistics",
            "description": "Table statistics not updated recently",
            "affected_objects": ["products", "orders"],
            "recommendations": [
                "Run ANALYZE on affected tables",
                "Enable auto-analyze",
                "Schedule regular statistics updates"
            ]
        },
        "wrong_cardinality": {
            "title": "Wrong cardinality estimate",
            "description": "Query optimizer misestimating row counts due to skewed data",
            "affected_objects": ["customers"],
            "recommendations": [
                "Update table statistics",
                "Consider histogram statistics",
                "Review data distribution"
            ]
        },
        "orm_generated": {
            "title": "ORM-generated SQL anti-pattern",
            "description": "Excessive JOINs or N+1 query pattern",
            "affected_objects": ["orm_pattern"],
            "recommendations": [
                "Use eager loading / JOIN FETCH",
                "Implement select_related() or prefetch_related()",
                "Batch queries together"
            ]
        },
        "high_io_workload": {
            "title": "High disk I/O workload",
            "description": "Low cache hit ratio with excessive disk reads",
            "affected_objects": ["io_performance"],
            "recommendations": [
                "Add indexes to reduce disk reads",
                "Increase buffer pool size",
                "Use covering indexes"
            ]
        },
        "inefficient_reporting": {
            "title": "Inefficient reporting query",
            "description": "Multiple aggregations or window functions without pagination",
            "affected_objects": ["reporting_query"],
            "recommendations": [
                "Add LIMIT clause for pagination",
                "Consider materialized views",
                "Cache results if data doesn't change frequently"
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


def create_test_optimizations():
    """Create test optimizations with all 9 issue types"""
    
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get or create a test connection
        connection = session.query(Connection).first()
        
        if not connection:
            print("❌ No connections found in database. Please create a connection first.")
            return False
        
        print(f"✓ Using connection: {connection.name} (ID: {connection.id})")
        
        # Define test cases for all 9 issue types
        test_cases = [
            # 1. Missing Index (Critical)
            {
                "original_sql": "SELECT * FROM users WHERE email = 'user@example.com'",
                "optimized_sql": "SELECT id, username, email FROM users WHERE email = 'user@example.com'",
                "issue_type": "missing_index",
                "severity": "critical",
                "count": 2,
                "explanation": "Added index on email column and specified required columns",
                "recommendations": "CREATE INDEX idx_users_email ON users(email);"
            },
            # 2. Missing Index (High)
            {
                "original_sql": "SELECT * FROM orders WHERE customer_id = 12345",
                "optimized_sql": "SELECT id, order_number, total_amount FROM orders WHERE customer_id = 12345",
                "issue_type": "missing_index",
                "severity": "high",
                "count": 1,
                "explanation": "Added index on customer_id for faster lookups",
                "recommendations": "CREATE INDEX idx_orders_customer_id ON orders(customer_id);"
            },
            # 3. Inefficient Index (Medium)
            {
                "original_sql": "SELECT * FROM customers WHERE status = 'active'",
                "optimized_sql": "SELECT id, name, email FROM customers WHERE status = 'active' AND created_at > '2024-01-01'",
                "issue_type": "inefficient_index",
                "severity": "medium",
                "count": 1,
                "explanation": "Added additional filter and composite index for better selectivity",
                "recommendations": "CREATE INDEX idx_customers_status_created ON customers(status, created_at);"
            },
            # 4. Poor Join Strategy (High)
            {
                "original_sql": """SELECT u.*, o.*, p.* FROM users u
                    JOIN orders o ON u.id = o.user_id
                    JOIN order_items oi ON o.id = oi.order_id
                    JOIN products p ON oi.product_id = p.id""",
                "optimized_sql": """SELECT u.id, u.username, o.id, o.order_number, p.name
                    FROM users u
                    JOIN orders o ON u.id = o.user_id
                    JOIN order_items oi ON o.id = oi.order_id
                    JOIN products p ON oi.product_id = p.id
                    WHERE u.status = 'active'""",
                "issue_type": "poor_join_strategy",
                "severity": "high",
                "count": 1,
                "explanation": "Added indexes on join columns and specified required columns",
                "recommendations": "CREATE INDEX idx_orders_user_id ON orders(user_id); CREATE INDEX idx_order_items_order_id ON order_items(order_id);"
            },
            # 5. Full Table Scan (Critical)
            {
                "original_sql": "SELECT * FROM logs WHERE message LIKE '%error%'",
                "optimized_sql": "SELECT id, log_level, message, created_at FROM logs WHERE log_level = 'ERROR' AND created_at > NOW() - INTERVAL '7 days'",
                "issue_type": "full_table_scan",
                "severity": "critical",
                "count": 2,
                "explanation": "Changed to indexed column and added time filter",
                "recommendations": "CREATE INDEX idx_logs_level_created ON logs(log_level, created_at);"
            },
            # 6. Full Table Scan (High)
            {
                "original_sql": "SELECT * FROM transactions WHERE amount > 1000",
                "optimized_sql": "SELECT id, transaction_id, amount, created_at FROM transactions WHERE amount > 1000 AND created_at > NOW() - INTERVAL '30 days'",
                "issue_type": "full_table_scan",
                "severity": "high",
                "count": 1,
                "explanation": "Added index on amount and time filter",
                "recommendations": "CREATE INDEX idx_transactions_amount ON transactions(amount);"
            },
            # 7. Suboptimal Pattern (Medium) - SELECT *
            {
                "original_sql": "SELECT * FROM products WHERE category = 'Electronics'",
                "optimized_sql": "SELECT id, name, price, stock_quantity FROM products WHERE category = 'Electronics'",
                "issue_type": "suboptimal_pattern",
                "severity": "medium",
                "count": 2,
                "explanation": "Specified only required columns instead of SELECT *",
                "recommendations": "Always specify required columns explicitly"
            },
            # 8. Suboptimal Pattern (Medium) - LIKE wildcard
            {
                "original_sql": "SELECT * FROM products WHERE name LIKE '%phone%'",
                "optimized_sql": "SELECT id, name, price FROM products WHERE name ILIKE 'phone%' OR category = 'Electronics'",
                "issue_type": "suboptimal_pattern",
                "severity": "medium",
                "count": 1,
                "explanation": "Removed leading wildcard and added category filter",
                "recommendations": "Avoid leading wildcards; consider full-text search"
            },
            # 9. Suboptimal Pattern (Low) - Function on column
            {
                "original_sql": "SELECT * FROM users WHERE UPPER(email) = 'TEST@EXAMPLE.COM'",
                "optimized_sql": "SELECT id, username, email FROM users WHERE email = 'test@example.com'",
                "issue_type": "suboptimal_pattern",
                "severity": "low",
                "count": 1,
                "explanation": "Removed function from indexed column",
                "recommendations": "Store email in lowercase or create functional index"
            },
            # 10. Stale Statistics (Medium)
            {
                "original_sql": "SELECT COUNT(*) FROM orders WHERE status = 'pending'",
                "optimized_sql": "SELECT COUNT(*) FROM orders WHERE status = 'pending' AND created_at > NOW() - INTERVAL '7 days'",
                "issue_type": "stale_statistics",
                "severity": "medium",
                "count": 1,
                "explanation": "Added time filter and updated statistics",
                "recommendations": "ANALYZE orders; Enable auto-analyze"
            },
            # 11. Wrong Cardinality (Medium)
            {
                "original_sql": "SELECT * FROM customers WHERE status = 'inactive'",
                "optimized_sql": "SELECT id, name, email FROM customers WHERE status = 'inactive' AND last_activity < NOW() - INTERVAL '90 days'",
                "issue_type": "wrong_cardinality",
                "severity": "medium",
                "count": 1,
                "explanation": "Added additional filter for skewed data",
                "recommendations": "ANALYZE customers; Consider histogram statistics"
            },
            # 12. ORM Generated (Critical) - N+1
            {
                "original_sql": "SELECT * FROM users WHERE id = 1",
                "optimized_sql": """SELECT u.*, o.* FROM users u
                    LEFT JOIN orders o ON u.id = o.user_id
                    WHERE u.id = 1""",
                "issue_type": "orm_generated",
                "severity": "critical",
                "count": 1,
                "explanation": "Used eager loading to prevent N+1 queries",
                "recommendations": "Use select_related() or prefetch_related() in ORM"
            },
            # 13. ORM Generated (High) - Excessive JOINs
            {
                "original_sql": """SELECT u.*, s.*, o.*, c.*, p.*
                    FROM users u
                    LEFT JOIN sessions s ON u.id = s.user_id
                    LEFT JOIN orders o ON u.id = o.user_id
                    LEFT JOIN customers c ON o.customer_id = c.id
                    LEFT JOIN products p ON p.id IN (SELECT product_id FROM order_items WHERE order_id = o.id)""",
                "optimized_sql": """SELECT u.id, u.username, COUNT(o.id) as order_count
                    FROM users u
                    LEFT JOIN orders o ON u.id = o.user_id
                    GROUP BY u.id, u.username""",
                "issue_type": "orm_generated",
                "severity": "high",
                "count": 1,
                "explanation": "Reduced excessive JOINs and used aggregation",
                "recommendations": "Split into multiple queries; use lazy loading"
            },
            # 14. High IO Workload (High)
            {
                "original_sql": """SELECT t.*, u.username, u.email
                    FROM transactions t
                    JOIN users u ON t.user_id = u.id
                    WHERE t.created_at > NOW() - INTERVAL '30 days'
                    ORDER BY t.amount DESC""",
                "optimized_sql": """SELECT t.id, t.transaction_id, t.amount, u.username
                    FROM transactions t
                    JOIN users u ON t.user_id = u.id
                    WHERE t.created_at > NOW() - INTERVAL '30 days'
                    ORDER BY t.amount DESC
                    LIMIT 100""",
                "issue_type": "high_io_workload",
                "severity": "high",
                "count": 1,
                "explanation": "Added LIMIT and specified columns to reduce I/O",
                "recommendations": "CREATE INDEX idx_transactions_created_amount ON transactions(created_at, amount);"
            },
            # 15. High IO Workload (Medium)
            {
                "original_sql": "SELECT * FROM logs WHERE created_at > NOW() - INTERVAL '7 days'",
                "optimized_sql": "SELECT id, log_level, message FROM logs WHERE created_at > NOW() - INTERVAL '7 days' AND log_level IN ('ERROR', 'CRITICAL')",
                "issue_type": "high_io_workload",
                "severity": "medium",
                "count": 1,
                "explanation": "Added filter to reduce data access",
                "recommendations": "CREATE INDEX idx_logs_created_level ON logs(created_at, log_level);"
            },
            # 16. Inefficient Reporting (Medium)
            {
                "original_sql": """SELECT DATE_TRUNC('day', created_at) as day,
                    COUNT(*) as total_orders,
                    SUM(total_amount) as revenue,
                    AVG(total_amount) as avg_order
                    FROM orders
                    GROUP BY DATE_TRUNC('day', created_at)""",
                "optimized_sql": """SELECT DATE_TRUNC('day', created_at) as day,
                    COUNT(*) as total_orders,
                    SUM(total_amount) as revenue,
                    AVG(total_amount) as avg_order
                    FROM orders
                    WHERE created_at > NOW() - INTERVAL '90 days'
                    GROUP BY DATE_TRUNC('day', created_at)
                    ORDER BY day DESC
                    LIMIT 90""",
                "issue_type": "inefficient_reporting",
                "severity": "medium",
                "count": 1,
                "explanation": "Added time filter and pagination",
                "recommendations": "Consider materialized view for frequently accessed reports"
            },
            # 17. Inefficient Reporting (Low) - Window functions
            {
                "original_sql": """SELECT user_id,
                    COUNT(*) as session_count,
                    ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank
                    FROM sessions
                    GROUP BY user_id""",
                "optimized_sql": """SELECT user_id,
                    COUNT(*) as session_count,
                    ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank
                    FROM sessions
                    WHERE started_at > NOW() - INTERVAL '30 days'
                    GROUP BY user_id
                    ORDER BY session_count DESC
                    LIMIT 100""",
                "issue_type": "inefficient_reporting",
                "severity": "low",
                "count": 1,
                "explanation": "Added time filter and pagination for window function",
                "recommendations": "Add LIMIT for pagination; consider caching results"
            }
        ]
        
        print(f"\n{'='*70}")
        print("CREATING TEST OPTIMIZATIONS WITH DETECTED ISSUES")
        print(f"{'='*70}\n")
        
        created_count = 0
        issue_type_counts = {}
        
        for i, test_case in enumerate(test_cases, 1):
            # Create detection result
            detection_result = create_detection_result(
                test_case["issue_type"],
                test_case["severity"],
                test_case["count"]
            )
            
            # Create optimization
            optimization = Optimization(
                query_id=None,
                connection_id=connection.id,
                original_sql=test_case["original_sql"],
                optimized_sql=test_case["optimized_sql"],
                execution_plan=None,
                explanation=test_case["explanation"],
                recommendations=test_case["recommendations"],
                estimated_improvement_pct=round(20 + (i * 5) % 60, 1),  # Vary between 20-80%
                status="pending",
                created_at=datetime.utcnow() - timedelta(hours=i),
                detected_issues=detection_result  # Store as dict (SQLAlchemy will convert to JSON)
            )
            
            session.add(optimization)
            
            # Track counts
            issue_type = test_case["issue_type"]
            issue_type_counts[issue_type] = issue_type_counts.get(issue_type, 0) + test_case["count"]
            
            created_count += 1
            
            print(f"✓ Created optimization #{i}: {test_case['issue_type']} ({test_case['severity']}) - {test_case['count']} issue(s)")
        
        # Commit all changes
        session.commit()
        
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}\n")
        print(f"✓ Created {created_count} optimizations with detected issues")
        print(f"\nIssue Type Distribution:")
        for issue_type, count in sorted(issue_type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {issue_type.replace('_', ' ').title()}: {count}")
        
        total_issues = sum(issue_type_counts.values())
        print(f"\n✓ Total issues: {total_issues}")
        
        print(f"\n{'='*70}")
        print("✅ DATA POPULATION COMPLETE")
        print(f"{'='*70}\n")
        
        print("Next steps:")
        print("1. Restart the backend server (if running)")
        print("2. Refresh the dashboard in your browser")
        print("3. Verify 'Issues by Type' section displays all categories")
        print("4. Check that counts match the summary above")
        
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
    print("\n" + "="*70)
    print("DASHBOARD DETECTION DATA POPULATION SCRIPT")
    print("="*70)
    print("\nThis script will create test optimizations with all 9 issue types")
    print("to populate the dashboard detection display.\n")
    
    input("Press Enter to continue or Ctrl+C to cancel...")
    
    success = create_test_optimizations()
    
    if success:
        print("\n✅ Success! Dashboard should now display issue type breakdown.")
    else:
        print("\n❌ Failed to populate data. Check error messages above.")
