"""
Comprehensive Test Database Generator for AI SQL Optimizer Pro
Creates realistic test data demonstrating all 9 SQL optimization issue types

Database: PostgreSQL at 192.168.1.81:5432/mydb
Issues Covered:
1. Missing indexes
2. Inefficient indexes
3. Poor join strategies
4. Full table scans
5. Suboptimal query patterns
6. Stale statistics
7. Wrong cardinality estimates
8. ORM-generated SQL
9. High I/O workloads
10. Inefficient reporting
"""

import psycopg2
from psycopg2.extras import execute_values
import random
import hashlib
from datetime import datetime, timedelta
from faker import Faker
import json

# Database connection parameters
DB_CONFIG = {
    "dbname": "mydb",
    "user": "admin",
    "password": "admin123",
    "host": "192.168.1.81",
    "port": 5432
}

fake = Faker()
Faker.seed(42)
random.seed(42)


class TestDatabaseGenerator:
    """Generates comprehensive test data for SQL optimization testing"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✓ Disconnected from database")
    
    def execute_sql(self, sql, params=None, commit=True):
        """Execute SQL statement"""
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            if commit:
                self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ SQL Error: {e}")
            self.conn.rollback()
            return False
    
    def create_test_tables(self):
        """Create test tables with various optimization issues"""
        print("\n" + "="*70)
        print("CREATING TEST TABLES")
        print("="*70)
        
        # Drop existing test tables
        drop_tables = """
        DROP TABLE IF EXISTS test_order_items CASCADE;
        DROP TABLE IF EXISTS test_orders CASCADE;
        DROP TABLE IF EXISTS test_products CASCADE;
        DROP TABLE IF EXISTS test_customers CASCADE;
        DROP TABLE IF EXISTS test_users CASCADE;
        DROP TABLE IF EXISTS test_transactions CASCADE;
        DROP TABLE IF EXISTS test_logs CASCADE;
        DROP TABLE IF EXISTS test_reports CASCADE;
        DROP TABLE IF EXISTS test_sessions CASCADE;
        """
        print("\n1. Dropping existing test tables...")
        self.execute_sql(drop_tables)
        
        # Table 1: Users (Missing index on email - Issue #1)
        print("\n2. Creating test_users table (missing index on email)...")
        users_table = """
        CREATE TABLE test_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            login_count INTEGER DEFAULT 0
        );
        -- Intentionally NO index on email to demonstrate missing index issue
        """
        self.execute_sql(users_table)
        
        # Table 2: Customers (Inefficient index - Issue #2)
        print("\n3. Creating test_customers table (inefficient index)...")
        customers_table = """
        CREATE TABLE test_customers (
            id SERIAL PRIMARY KEY,
            customer_code VARCHAR(50),
            company_name VARCHAR(255),
            contact_name VARCHAR(255),
            country VARCHAR(100),
            city VARCHAR(100),
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        -- Low selectivity index (status has only 2-3 values)
        CREATE INDEX idx_customers_status ON test_customers(status);
        """
        self.execute_sql(customers_table)
        
        # Table 3: Products (No indexes for joins - Issue #3)
        print("\n4. Creating test_products table (no join indexes)...")
        products_table = """
        CREATE TABLE test_products (
            id SERIAL PRIMARY KEY,
            product_code VARCHAR(50),
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            price DECIMAL(10, 2),
            stock_quantity INTEGER DEFAULT 0,
            supplier_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        -- Intentionally NO index on category or supplier_id for join issues
        """
        self.execute_sql(products_table)
        
        # Table 4: Orders (For full table scan testing - Issue #4)
        print("\n5. Creating test_orders table (full table scan scenarios)...")
        orders_table = """
        CREATE TABLE test_orders (
            id SERIAL PRIMARY KEY,
            order_number VARCHAR(50),
            customer_id INTEGER,
            user_id INTEGER,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'pending',
            total_amount DECIMAL(12, 2),
            shipping_address TEXT,
            notes TEXT
        );
        -- Only primary key, no other indexes
        """
        self.execute_sql(orders_table)
        
        # Table 5: Order Items (For complex joins - Issue #3)
        print("\n6. Creating test_order_items table...")
        order_items_table = """
        CREATE TABLE test_order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price DECIMAL(10, 2),
            discount DECIMAL(5, 2) DEFAULT 0
        );
        -- No foreign key indexes
        """
        self.execute_sql(order_items_table)
        
        # Table 6: Transactions (High I/O workload - Issue #9)
        print("\n7. Creating test_transactions table (high I/O)...")
        transactions_table = """
        CREATE TABLE test_transactions (
            id SERIAL PRIMARY KEY,
            transaction_id VARCHAR(100),
            user_id INTEGER,
            transaction_type VARCHAR(50),
            amount DECIMAL(12, 2),
            currency VARCHAR(10) DEFAULT 'USD',
            status VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );
        -- No indexes except primary key
        """
        self.execute_sql(transactions_table)
        
        # Table 7: Logs (For reporting queries - Issue #10)
        print("\n8. Creating test_logs table (reporting scenarios)...")
        logs_table = """
        CREATE TABLE test_logs (
            id SERIAL PRIMARY KEY,
            log_level VARCHAR(20),
            message TEXT,
            user_id INTEGER,
            ip_address VARCHAR(50),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            request_duration INTEGER
        );
        -- No indexes for aggregation queries
        """
        self.execute_sql(logs_table)
        
        # Table 8: Reports (Inefficient reporting - Issue #10)
        print("\n9. Creating test_reports table...")
        reports_table = """
        CREATE TABLE test_reports (
            id SERIAL PRIMARY KEY,
            report_name VARCHAR(255),
            report_type VARCHAR(50),
            generated_by INTEGER,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data JSONB,
            row_count INTEGER,
            execution_time INTEGER
        );
        """
        self.execute_sql(reports_table)
        
        # Table 9: Sessions (For ORM N+1 testing - Issue #8)
        print("\n10. Creating test_sessions table (ORM patterns)...")
        sessions_table = """
        CREATE TABLE test_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            session_token VARCHAR(255),
            ip_address VARCHAR(50),
            user_agent TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
        """
        self.execute_sql(sessions_table)
        
        print("\n✓ All test tables created successfully")
    
    def populate_users(self, count=50000):
        """Populate users table"""
        print(f"\nPopulating test_users with {count:,} records...")
        
        batch_size = 1000
        for i in range(0, count, batch_size):
            users = []
            for j in range(batch_size):
                if i + j >= count:
                    break
                users.append((
                    fake.user_name(),
                    fake.email(),
                    fake.first_name(),
                    fake.last_name(),
                    random.choice(['active', 'inactive', 'suspended']),
                    fake.date_time_between(start_date='-2y', end_date='now'),
                    fake.date_time_between(start_date='-30d', end_date='now') if random.random() > 0.3 else None,
                    random.randint(0, 500)
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_users 
                   (username, email, first_name, last_name, status, created_at, last_login, login_count)
                   VALUES %s""",
                users
            )
            self.conn.commit()
            
            if (i + batch_size) % 10000 == 0:
                print(f"  Inserted {i + batch_size:,} users...")
        
        print(f"✓ Inserted {count:,} users")
    
    def populate_customers(self, count=20000):
        """Populate customers table with skewed data (Issue #7 - Wrong cardinality)"""
        print(f"\nPopulating test_customers with {count:,} records (skewed distribution)...")
        
        batch_size = 1000
        # Create skewed distribution: 90% active, 10% inactive
        for i in range(0, count, batch_size):
            customers = []
            for j in range(batch_size):
                if i + j >= count:
                    break
                # Skewed status distribution
                status = 'active' if random.random() < 0.9 else 'inactive'
                customers.append((
                    f"CUST{i+j:06d}",
                    fake.company(),
                    fake.name(),
                    fake.country(),
                    fake.city(),
                    status,
                    fake.date_time_between(start_date='-3y', end_date='now')
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_customers 
                   (customer_code, company_name, contact_name, country, city, status, created_at)
                   VALUES %s""",
                customers
            )
            self.conn.commit()
            
            if (i + batch_size) % 5000 == 0:
                print(f"  Inserted {i + batch_size:,} customers...")
        
        print(f"✓ Inserted {count:,} customers (90% active, 10% inactive)")
    
    def populate_products(self, count=10000):
        """Populate products table"""
        print(f"\nPopulating test_products with {count:,} records...")
        
        categories = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports', 
                     'Toys', 'Food', 'Beauty', 'Automotive', 'Office']
        
        batch_size = 1000
        for i in range(0, count, batch_size):
            products = []
            for j in range(batch_size):
                if i + j >= count:
                    break
                products.append((
                    f"PROD{i+j:06d}",
                    fake.catch_phrase(),
                    random.choice(categories),
                    round(random.uniform(5.99, 999.99), 2),
                    random.randint(0, 1000),
                    random.randint(1, 500),
                    fake.date_time_between(start_date='-2y', end_date='now')
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_products 
                   (product_code, name, category, price, stock_quantity, supplier_id, created_at)
                   VALUES %s""",
                products
            )
            self.conn.commit()
            
            if (i + batch_size) % 5000 == 0:
                print(f"  Inserted {i + batch_size:,} products...")
        
        print(f"✓ Inserted {count:,} products")
    
    def populate_orders(self, count=100000):
        """Populate orders table"""
        print(f"\nPopulating test_orders with {count:,} records...")
        
        statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        
        batch_size = 1000
        for i in range(0, count, batch_size):
            orders = []
            for j in range(batch_size):
                if i + j >= count:
                    break
                orders.append((
                    f"ORD{i+j:08d}",
                    random.randint(1, 20000),  # customer_id
                    random.randint(1, 50000),  # user_id
                    fake.date_time_between(start_date='-1y', end_date='now'),
                    random.choice(statuses),
                    round(random.uniform(10.00, 5000.00), 2),
                    fake.address(),
                    fake.text(max_nb_chars=200) if random.random() > 0.7 else None
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_orders 
                   (order_number, customer_id, user_id, order_date, status, total_amount, shipping_address, notes)
                   VALUES %s""",
                orders
            )
            self.conn.commit()
            
            if (i + batch_size) % 20000 == 0:
                print(f"  Inserted {i + batch_size:,} orders...")
        
        print(f"✓ Inserted {count:,} orders")
    
    def populate_order_items(self, count=250000):
        """Populate order items table"""
        print(f"\nPopulating test_order_items with {count:,} records...")
        
        batch_size = 1000
        for i in range(0, count, batch_size):
            items = []
            for j in range(batch_size):
                if i + j >= count:
                    break
                items.append((
                    random.randint(1, 100000),  # order_id
                    random.randint(1, 10000),   # product_id
                    random.randint(1, 10),
                    round(random.uniform(5.99, 999.99), 2),
                    round(random.uniform(0, 20), 2) if random.random() > 0.7 else 0
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_order_items 
                   (order_id, product_id, quantity, unit_price, discount)
                   VALUES %s""",
                items
            )
            self.conn.commit()
            
            if (i + batch_size) % 50000 == 0:
                print(f"  Inserted {i + batch_size:,} order items...")
        
        print(f"✓ Inserted {count:,} order items")
    
    def populate_transactions(self, count=150000):
        """Populate transactions table (High I/O scenarios)"""
        print(f"\nPopulating test_transactions with {count:,} records...")
        
        transaction_types = ['purchase', 'refund', 'transfer', 'withdrawal', 'deposit']
        statuses = ['completed', 'pending', 'failed', 'cancelled']
        
        batch_size = 1000
        for i in range(0, count, batch_size):
            transactions = []
            for j in range(batch_size):
                if i + j >= count:
                    break
                metadata = {
                    'ip': fake.ipv4(),
                    'device': random.choice(['mobile', 'desktop', 'tablet']),
                    'location': fake.city()
                }
                transactions.append((
                    fake.uuid4(),
                    random.randint(1, 50000),
                    random.choice(transaction_types),
                    round(random.uniform(1.00, 10000.00), 2),
                    random.choice(['USD', 'EUR', 'GBP']),
                    random.choice(statuses),
                    fake.date_time_between(start_date='-6m', end_date='now'),
                    json.dumps(metadata)
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_transactions 
                   (transaction_id, user_id, transaction_type, amount, currency, status, created_at, metadata)
                   VALUES %s""",
                transactions
            )
            self.conn.commit()
            
            if (i + batch_size) % 30000 == 0:
                print(f"  Inserted {i + batch_size:,} transactions...")
        
        print(f"✓ Inserted {count:,} transactions")
    
    def populate_logs(self, count=500000):
        """Populate logs table (Reporting scenarios)"""
        print(f"\nPopulating test_logs with {count:,} records...")
        
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        batch_size = 2000
        for i in range(0, count, batch_size):
            logs = []
            for j in range(batch_size):
                if i + j >= count:
                    break
                logs.append((
                    random.choice(log_levels),
                    fake.sentence(),
                    random.randint(1, 50000) if random.random() > 0.3 else None,
                    fake.ipv4(),
                    fake.user_agent(),
                    fake.date_time_between(start_date='-30d', end_date='now'),
                    random.randint(10, 5000)
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_logs 
                   (log_level, message, user_id, ip_address, user_agent, created_at, request_duration)
                   VALUES %s""",
                logs
            )
            self.conn.commit()
            
            if (i + batch_size) % 100000 == 0:
                print(f"  Inserted {i + batch_size:,} logs...")
        
        print(f"✓ Inserted {count:,} logs")
    
    def populate_sessions(self, count=30000):
        """Populate sessions table (ORM N+1 scenarios)"""
        print(f"\nPopulating test_sessions with {count:,} records...")
        
        batch_size = 1000
        for i in range(0, count, batch_size):
            sessions = []
            for j in range(batch_size):
                if i + j >= count:
                    break
                started = fake.date_time_between(start_date='-7d', end_date='now')
                sessions.append((
                    random.randint(1, 50000),
                    fake.uuid4(),
                    fake.ipv4(),
                    fake.user_agent(),
                    started,
                    started + timedelta(minutes=random.randint(1, 240)),
                    random.choice([True, False])
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_sessions 
                   (user_id, session_token, ip_address, user_agent, started_at, last_activity, is_active)
                   VALUES %s""",
                sessions
            )
            self.conn.commit()
            
            if (i + batch_size) % 10000 == 0:
                print(f"  Inserted {i + batch_size:,} sessions...")
        
        print(f"✓ Inserted {count:,} sessions")
    
    def create_stale_statistics(self):
        """Simulate stale statistics (Issue #6)"""
        print("\nSimulating stale statistics...")
        
        # Disable autovacuum temporarily for test tables
        stale_stats_sql = """
        -- Mark statistics as old by not analyzing tables
        -- In production, this happens when tables aren't analyzed regularly
        """
        print("✓ Statistics will be stale (tables not analyzed)")
    
    def populate_all_tables(self):
        """Populate all test tables with data"""
        print("\n" + "="*70)
        print("POPULATING TEST DATA")
        print("="*70)
        
        self.populate_users(50000)
        self.populate_customers(20000)
        self.populate_products(10000)
        self.populate_orders(100000)
        self.populate_order_items(250000)
        self.populate_transactions(150000)
        self.populate_logs(500000)
        self.populate_sessions(30000)
        
        print("\n✓ All tables populated successfully")
        print(f"\nTotal records created: ~1,110,000")
    
    def create_problematic_queries(self):
        """Create and store problematic SQL queries"""
        print("\n" + "="*70)
        print("CREATING PROBLEMATIC QUERIES")
        print("="*70)
        
        queries = [
            # Issue #1: Missing Index
            {
                "sql": "SELECT * FROM test_users WHERE email = 'user@example.com'",
                "description": "Missing index on email column",
                "issue_type": "missing_index"
            },
            {
                "sql": "SELECT * FROM test_orders WHERE customer_id = 12345",
                "description": "Missing index on customer_id",
                "issue_type": "missing_index"
            },
            
            # Issue #2: Inefficient Index
            {
                "sql": "SELECT * FROM test_customers WHERE status = 'active'",
                "description": "Low selectivity index (90% of rows are active)",
                "issue_type": "inefficient_index"
            },
            
            # Issue #3: Poor Join Strategy
            {
                "sql": """
                SELECT u.*, o.*, p.*, oi.*
                FROM test_users u
                JOIN test_orders o ON u.id = o.user_id
                JOIN test_order_items oi ON o.id = oi.order_id
                JOIN test_products p ON oi.product_id = p.id
                WHERE u.status = 'active'
                """,
                "description": "Multiple joins without proper indexes",
                "issue_type": "poor_join_strategy"
            },
            
            # Issue #4: Full Table Scan
            {
                "sql": "SELECT * FROM test_logs WHERE message LIKE '%error%'",
                "description": "Full table scan on 500K rows",
                "issue_type": "full_table_scan"
            },
            {
                "sql": "SELECT * FROM test_transactions WHERE amount > 1000",
                "description": "Full scan without index on amount",
                "issue_type": "full_table_scan"
            },
            
            # Issue #5: Suboptimal Patterns
            {
                "sql": "SELECT * FROM test_users WHERE id > 100",
                "description": "SELECT * anti-pattern",
                "issue_type": "suboptimal_pattern"
            },
            {
                "sql": """
                SELECT DISTINCT u.username, u.email 
                FROM test_users u 
                JOIN test_sessions s ON u.id = s.user_id
                """,
                "description": "Unnecessary DISTINCT",
                "issue_type": "suboptimal_pattern"
            },
            {
                "sql": """
                SELECT * FROM test_products 
                WHERE status = 'active' OR status = 'pending' OR status = 'processing' OR status = 'shipped'
                """,
                "description": "Multiple OR conditions instead of IN",
                "issue_type": "suboptimal_pattern"
            },
            {
                "sql": """
                SELECT u.*, 
                       (SELECT COUNT(*) FROM test_orders WHERE user_id = u.id) as order_count
                FROM test_users u
                """,
                "description": "Correlated subquery in SELECT",
                "issue_type": "suboptimal_pattern"
            },
            {
                "sql": "SELECT * FROM test_users WHERE email NOT IN (SELECT email FROM test_customers)",
                "description": "NOT IN with subquery",
                "issue_type": "suboptimal_pattern"
            },
            {
                "sql": "SELECT * FROM test_products WHERE name LIKE '%phone%'",
                "description": "LIKE with leading wildcard",
                "issue_type": "suboptimal_pattern"
            },
            {
                "sql": "SELECT * FROM test_users WHERE UPPER(email) = 'TEST@EXAMPLE.COM'",
                "description": "Function on indexed column",
                "issue_type": "suboptimal_pattern"
            },
            
            # Issue #7: Wrong Cardinality (skewed data)
            {
                "sql": "SELECT * FROM test_customers WHERE status = 'inactive'",
                "description": "Query on skewed data (only 10% inactive)",
                "issue_type": "wrong_cardinality"
            },
            
            # Issue #8: ORM-Generated SQL
            {
                "sql": """
                SELECT u.*, s.*, o.*, c.*, p.*
                FROM test_users u
                LEFT JOIN test_sessions s ON u.id = s.user_id
                LEFT JOIN test_orders o ON u.id = o.user_id
                LEFT JOIN test_customers c ON o.customer_id = c.id
                LEFT JOIN test_products p ON p.id IN (SELECT product_id FROM test_order_items WHERE order_id = o.id)
                """,
                "description": "Excessive JOINs typical of ORM eager loading",
                "issue_type": "orm_generated"
            },
            {
                "sql": "SELECT * FROM test_users WHERE id = 1",
                "description": "N+1 query pattern (would be executed many times)",
                "issue_type": "orm_generated"
            },
            
            # Issue #9: High I/O Workload
            {
                "sql": """
                SELECT t.*, u.username, u.email
                FROM test_transactions t
                JOIN test_users u ON t.user_id = u.id
                WHERE t.created_at > NOW() - INTERVAL '30 days'
                ORDER BY t.amount DESC
                """,
                "description": "Large dataset without proper indexes",
                "issue_type": "high_io_workload"
            },
            
            # Issue #10: Inefficient Reporting
            {
                "sql": """
                SELECT 
                    DATE_TRUNC('day', created_at) as day,
                    COUNT(*) as total_orders,
                    SUM(total_amount) as revenue,
                    AVG(total_amount) as avg_order,
                    MAX(total_amount) as max_order,
                    MIN(total_amount) as min_order
                FROM test_orders
                GROUP BY DATE_TRUNC('day', created_at)
                """,
                "description": "Multiple aggregations without LIMIT",
                "issue_type": "inefficient_reporting"
            },
            {
                "sql": """
                SELECT 
                    user_id,
                    COUNT(*) as session_count,
                    ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank,
                    DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) as dense_rank,
                    LAG(COUNT(*)) OVER (ORDER BY COUNT(*) DESC) as prev_count
                FROM test_sessions
                GROUP BY user_id
                """,
                "description": "Multiple window functions without pagination",
                "issue_type": "inefficient_reporting"
            },
            
            # Combined issues
            {
                "sql": """
                SELECT * FROM test_logs 
                WHERE log_level = 'ERROR' 
                   OR log_level = 'CRITICAL' 
                   OR log_level = 'WARNING'
                ORDER BY created_at DESC
                """,
                "description": "SELECT * + Multiple ORs + No LIMIT on large table",
                "issue_type": "multiple_issues"
            },
        ]
        
        print(f"\nCreated {len(queries)} problematic query examples")
        return queries
    
    def generate_summary_report(self):
        """Generate summary of created test data"""
        print("\n" + "="*70)
        print("TEST DATABASE SUMMARY")
        print("="*70)
        
        tables = [
            'test_users', 'test_customers', 'test_products', 'test_orders',
            'test_order_items', 'test_transactions', 'test_logs', 'test_sessions'
        ]
        
        print("\nTable Statistics:")
        print("-" * 70)
        
        total_rows = 0
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            total_rows += count
            print(f"  {table:25s}: {count:>10,} rows")
        
        print("-" * 70)
        print(f"  {'TOTAL':25s}: {total_rows:>10,} rows")
        
        print("\n" + "="*70)
        print("OPTIMIZATION ISSUES DEMONSTRATED")
        print("="*70)
        
        issues = [
            ("1. Missing Indexes", "test_users.email, test_orders.customer_id"),
            ("2. Inefficient Indexes", "test_customers.status (low selectivity)"),
            ("3. Poor Join Strategies", "Multiple tables without join indexes"),
            ("4. Full Table Scans", "test_logs, test_transactions"),
            ("5. Suboptimal Patterns", "SELECT *, DISTINCT, OR chains, subqueries"),
            ("6. Stale Statistics", "Tables not analyzed"),
            ("7. Wrong Cardinality", "test_customers.status (90/10 split)"),
            ("8. ORM-Generated SQL", "Excessive JOINs, N+1 patterns"),
            ("9. High I/O Workloads", "Large datasets without indexes"),
            ("10. Inefficient Reporting", "Aggregations without LIMIT, window functions")
        ]
        
        for issue, description in issues:
            print(f"\n{issue}")
            print(f"  → {description}")
        
        print("\n" + "="*70)


def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("AI SQL OPTIMIZER PRO - TEST DATABASE GENERATOR")
    print("="*70)
    print(f"\nTarget Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    print(f"User: {DB_CONFIG['user']}")
    print("\nThis script will:")
    print("  1. Create test tables with various optimization issues")
    print("  2. Populate tables with ~1.1 million records")
    print("  3. Generate problematic SQL queries")
    print("  4. Demonstrate all 9 SQL optimization issue types")
    
    input("\nPress Enter to continue or Ctrl+C to cancel...")
    
    generator = TestDatabaseGenerator()
    
    try:
        # Connect to database
        if not generator.connect():
            print("\n❌ Failed to connect to database. Exiting.")
            return
        
        # Create test tables
        generator.create_test_tables()
        
        # Populate tables with data
        generator.populate_all_tables()
        
        # Create stale statistics
        generator.create_stale_statistics()
        
        # Generate problematic queries
        queries = generator.create_problematic_queries()
        
        # Generate summary report
        generator.generate_summary_report()
        
        print("\n" + "="*70)
        print("✅ TEST DATABASE CREATION COMPLETE")
        print("="*70)
        
        print("\n📋 NEXT STEPS:")
        print("\n1. Test queries using the application's optimizer:")
        print("   - Connect to this database in the application")
        print("   - Run the problematic queries through the optimizer")
        print("   - Verify that all 9 issue types are detected")
        
        print("\n2. Example queries to test:")
        print("\n   Missing Index:")
        print("   SELECT * FROM test_users WHERE email = 'user@example.com';")
        
        print("\n   Full Table Scan:")
        print("   SELECT * FROM test_logs WHERE message LIKE '%error%';")
        
        print("\n   Poor Join Strategy:")
        print("   SELECT u.*, o.*, p.* FROM test_users u")
        print("   JOIN test_orders o ON u.id = o.user_id")
        print("   JOIN test_order_items oi ON o.id = oi.order_id")
        print("   JOIN test_products p ON oi.product_id = p.id;")
        
        print("\n3. Monitor performance:")
        print("   - Check execution times")
        print("   - Review detected issues")
        print("   - Apply recommended optimizations")
        
        print("\n" + "="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        generator.disconnect()


if __name__ == "__main__":
    main()
