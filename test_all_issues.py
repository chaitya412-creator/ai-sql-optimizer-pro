"""
Comprehensive Test Script for All 10 SQL Optimization Issues
Tests each issue type to verify detection works correctly
"""

import psycopg2
import time
from datetime import datetime

# Database connection
DB_CONFIG = {
    "dbname": "mydb",
    "user": "admin",
    "password": "admin123",
    "host": "192.168.1.81",
    "port": 5432
}

class IssueTestRunner:
    """Test runner for all SQL optimization issues"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.test_results = []
        
    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✓ Disconnected from database")
    
    def run_test_query(self, issue_type, test_name, sql):
        """Run a single test query"""
        print(f"\n  Testing: {test_name}")
        
        try:
            start_time = time.time()
            self.cursor.execute(f"EXPLAIN ANALYZE {sql}")
            result = self.cursor.fetchall()
            execution_time = time.time() - start_time
            
            # Parse execution plan
            plan_text = "\n".join([row[0] for row in result])
            
            # Check for expected patterns
            issues_found = []
            
            if "Seq Scan" in plan_text:
                issues_found.append("Sequential Scan")
            if "Bitmap" in plan_text:
                issues_found.append("Bitmap Scan")
            if "Nested Loop" in plan_text:
                issues_found.append("Nested Loop")
            if "Hash Join" in plan_text:
                issues_found.append("Hash Join")
            
            print(f"  ✓ Execution time: {execution_time:.3f}s")
            print(f"  ✓ Issues found: {', '.join(issues_found) if issues_found else 'None'}")
            
            self.test_results.append({
                "issue_type": issue_type,
                "test_name": test_name,
                "execution_time": execution_time,
                "issues_found": issues_found,
                "success": True
            })
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.test_results.append({
                "issue_type": issue_type,
                "test_name": test_name,
                "error": str(e),
                "success": False
            })
            return False
    
    def test_missing_indexes(self):
        """Test missing index detection"""
        print("\n" + "="*80)
        print("1. TESTING MISSING INDEXES")
        print("="*80)
        
        tests = [
            ("Missing index on email", 
             "SELECT * FROM test_users WHERE email = 'user@example.com'"),
            ("Missing index on customer_id",
             "SELECT * FROM test_orders WHERE customer_id = 12345"),
            ("Missing index on department",
             "SELECT * FROM test_users WHERE department = 'Engineering'")
        ]
        
        for test_name, sql in tests:
            self.run_test_query("missing_index", test_name, sql)
    
    def test_inefficient_indexes(self):
        """Test inefficient index detection"""
        print("\n" + "="*80)
        print("2. TESTING INEFFICIENT INDEXES")
        print("="*80)
        
        tests = [
            ("Low selectivity index",
             "SELECT * FROM test_customers WHERE status = 'active'"),
            ("Wrong column order",
             "SELECT * FROM test_customers WHERE country = 'USA' AND city = 'New York'")
        ]
        
        for test_name, sql in tests:
            self.run_test_query("inefficient_index", test_name, sql)
    
    def test_poor_joins(self):
        """Test poor join strategy detection"""
        print("\n" + "="*80)
        print("3. TESTING POOR JOIN STRATEGIES")
        print("="*80)
        
        tests = [
            ("Multiple joins without indexes",
             """SELECT u.username, o.order_number, p.name, oi.quantity
                FROM test_users u
                JOIN test_orders o ON u.id = o.user_id
                JOIN test_order_items oi ON o.id = oi.order_id
                JOIN test_products p ON oi.product_id = p.id
                WHERE u.status = 'active'
                LIMIT 100"""),
            ("Cross join",
             """SELECT * FROM test_products p, test_customers c
                WHERE p.category = 'Electronics'
                LIMIT 100""")
        ]
        
        for test_name, sql in tests:
            self.run_test_query("poor_join_strategy", test_name, sql)
    
    def test_full_table_scans(self):
        """Test full table scan detection"""
        print("\n" + "="*80)
        print("4. TESTING FULL TABLE SCANS")
        print("="*80)
        
        tests = [
            ("LIKE with leading wildcard",
             "SELECT * FROM test_logs WHERE message LIKE '%error%' LIMIT 100"),
            ("Range query without index",
             "SELECT * FROM test_transactions WHERE amount > 1000 LIMIT 100"),
            ("Date range without index",
             "SELECT * FROM test_orders WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31' LIMIT 100")
        ]
        
        for test_name, sql in tests:
            self.run_test_query("full_table_scan", test_name, sql)
    
    def test_suboptimal_patterns(self):
        """Test suboptimal pattern detection"""
        print("\n" + "="*80)
        print("5. TESTING SUBOPTIMAL QUERY PATTERNS")
        print("="*80)
        
        tests = [
            ("SELECT * anti-pattern",
             "SELECT * FROM test_users WHERE id > 100 LIMIT 10"),
            ("Correlated subquery",
             """SELECT u.username, u.email,
                       (SELECT COUNT(*) FROM test_orders WHERE user_id = u.id) as order_count
                FROM test_users u
                LIMIT 100"""),
            ("Function on indexed column",
             "SELECT * FROM test_users WHERE UPPER(email) = 'TEST@EXAMPLE.COM'")
        ]
        
        for test_name, sql in tests:
            self.run_test_query("suboptimal_pattern", test_name, sql)
    
    def test_orm_patterns(self):
        """Test ORM-generated SQL detection"""
        print("\n" + "="*80)
        print("8. TESTING ORM-GENERATED SQL")
        print("="*80)
        
        tests = [
            ("Excessive JOINs",
             """SELECT u.*, s.*, o.*, c.*
                FROM test_users u
                LEFT JOIN test_sessions s ON u.id = s.user_id
                LEFT JOIN test_orders o ON u.id = o.user_id
                LEFT JOIN test_customers c ON o.customer_id = c.id
                LIMIT 10"""),
            ("SELECT * with multiple JOINs",
             """SELECT * FROM test_users u
                JOIN test_orders o ON u.id = o.user_id
                JOIN test_customers c ON o.customer_id = c.id
                LIMIT 100""")
        ]
        
        for test_name, sql in tests:
            self.run_test_query("orm_generated", test_name, sql)
    
    def test_high_io(self):
        """Test high I/O workload detection"""
        print("\n" + "="*80)
        print("9. TESTING HIGH I/O WORKLOADS")
        print("="*80)
        
        tests = [
            ("Large dataset with JSONB/TEXT",
             """SELECT t.*, u.username, u.email
                FROM test_transactions t
                JOIN test_users u ON t.user_id = u.id
                WHERE t.created_at > NOW() - INTERVAL '30 days'
                ORDER BY t.amount DESC
                LIMIT 100"""),
            ("Query with large result set",
             "SELECT * FROM test_logs WHERE log_level IN ('ERROR', 'CRITICAL', 'WARNING') LIMIT 1000")
        ]
        
        for test_name, sql in tests:
            self.run_test_query("high_io_workload", test_name, sql)
    
    def test_inefficient_reporting(self):
        """Test inefficient reporting query detection"""
        print("\n" + "="*80)
        print("10. TESTING INEFFICIENT REPORTING QUERIES")
        print("="*80)
        
        tests = [
            ("Multiple aggregations",
             """SELECT 
                    DATE_TRUNC('day', order_date) as day,
                    COUNT(*) as total_orders,
                    SUM(total_amount) as revenue,
                    AVG(total_amount) as avg_order
                FROM test_orders
                GROUP BY DATE_TRUNC('day', order_date)
                ORDER BY day DESC
                LIMIT 10"""),
            ("Complex analytics on users",
             """SELECT 
                    department,
                    status,
                    COUNT(*) as user_count,
                    AVG(salary) as avg_salary,
                    MAX(salary) as max_salary,
                    MIN(salary) as min_salary
                FROM test_users
                GROUP BY department, status
                ORDER BY user_count DESC
                LIMIT 10""")
        ]
        
        for test_name, sql in tests:
            self.run_test_query("inefficient_reporting", test_name, sql)
    
    def verify_database_setup(self):
        """Verify database tables and data"""
        print("\n" + "="*80)
        print("VERIFYING DATABASE SETUP")
        print("="*80)
        
        tables = [
            'test_users', 'test_customers', 'test_products', 'test_orders',
            'test_order_items', 'test_transactions', 'test_logs', 'test_sessions',
            'test_analytics', 'test_audit_log'
        ]
        
        print("\nTable Row Counts:")
        print("-" * 80)
        
        total_rows = 0
        for table in tables:
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                total_rows += count
                print(f"  {table:25s}: {count:>10,} rows")
            except Exception as e:
                print(f"  {table:25s}: ❌ Error: {e}")
        
        print("-" * 80)
        print(f"  {'TOTAL':25s}: {total_rows:>10,} rows")
        
        return total_rows > 0
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        successful = sum(1 for r in self.test_results if r["success"])
        failed = total_tests - successful
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        if successful > 0:
            avg_time = sum(r.get("execution_time", 0) for r in self.test_results if r["success"]) / successful
            print(f"Average Execution Time: {avg_time:.3f}s")
        
        # Group by issue type
        print("\nTests by Issue Type:")
        print("-" * 80)
        
        issue_types = {}
        for result in self.test_results:
            issue_type = result["issue_type"]
            if issue_type not in issue_types:
                issue_types[issue_type] = {"total": 0, "successful": 0}
            issue_types[issue_type]["total"] += 1
            if result["success"]:
                issue_types[issue_type]["successful"] += 1
        
        for issue_type, counts in sorted(issue_types.items()):
            print(f"  {issue_type:30s}: {counts['successful']}/{counts['total']} passed")
        
        print("\n" + "="*80)
        
        if failed == 0:
            print("✅ ALL TESTS PASSED!")
        else:
            print(f"⚠️  {failed} test(s) failed. Review errors above.")
        
        print("="*80)


def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("AI SQL OPTIMIZER PRO - COMPREHENSIVE ISSUE TESTING")
    print("="*80)
    print(f"\nDatabase: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    runner = IssueTestRunner()
    
    try:
        # Connect
        if not runner.connect():
            print("\n❌ Failed to connect to database. Exiting.")
            return
        
        # Verify setup
        if not runner.verify_database_setup():
            print("\n❌ Database setup verification failed. Exiting.")
            return
        
        # Run all tests
        runner.test_missing_indexes()
        runner.test_inefficient_indexes()
        runner.test_poor_joins()
        runner.test_full_table_scans()
        runner.test_suboptimal_patterns()
        runner.test_orm_patterns()
        runner.test_high_io()
        runner.test_inefficient_reporting()
        
        # Generate summary
        runner.generate_summary()
        
        print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        runner.disconnect()


if __name__ == "__main__":
    main()
