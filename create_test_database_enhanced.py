"""
Enhanced Test Database Generator for AI SQL Optimizer Pro
Creates comprehensive test data demonstrating all 10 SQL optimization issue types

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
10. Inefficient reporting queries

Enhanced with:
- More comprehensive test scenarios
- Automated query execution
- Performance metrics collection
- Issue verification
"""

import psycopg2
from psycopg2.extras import execute_values
import random
import hashlib
from datetime import datetime, timedelta
from faker import Faker
import json
import time

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


class EnhancedTestDatabaseGenerator:
    """Enhanced test database generator with comprehensive issue coverage"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.query_results = []
        
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
        print("\n" + "="*80)
        print("CREATING ENHANCED TEST TABLES")
        print("="*80)
        
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
        DROP TABLE IF EXISTS test_analytics CASCADE;
        DROP TABLE IF EXISTS test_audit_log CASCADE;
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
            login_count INTEGER DEFAULT 0,
            department VARCHAR(100),
            salary DECIMAL(10, 2)
        );
        -- Intentionally NO index on email, department, or salary
        -- This will cause full table scans on these columns
        """
        self.execute_sql(users_table)
        
        # Table 2: Customers (Inefficient index - Issue #2)
        print("\n3. Creating test_customers table (inefficient indexes)...")
        customers_table = """
        CREATE TABLE test_customers (
            id SERIAL PRIMARY KEY,
            customer_code VARCHAR(50),
            company_name VARCHAR(255),
            contact_name VARCHAR(255),
            country VARCHAR(100),
            city VARCHAR(100),
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_orders INTEGER DEFAULT 0,
            lifetime_value DECIMAL(12, 2) DEFAULT 0
        );
        -- Low selectivity index (status has only 2-3 values - 90% active)
        CREATE INDEX idx_customers_status ON test_customers(status);
        
        -- Wrong column order in composite index
        CREATE INDEX idx_customers_city_country ON test_customers(city, country);
        -- Should be (country, city) for better selectivity
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
            subcategory VARCHAR(100),
            price DECIMAL(10, 2),
            cost DECIMAL(10, 2),
            stock_quantity INTEGER DEFAULT 0,
            supplier_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        -- Intentionally NO index on category, subcategory, or supplier_id
        -- This will cause poor join performance
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
            notes TEXT,
            payment_method VARCHAR(50),
            discount_code VARCHAR(50)
        );
        -- Only primary key, no other indexes
        -- Queries on customer_id, user_id, order_date, status will scan full table
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
            discount DECIMAL(5, 2) DEFAULT 0,
            tax_amount DECIMAL(10, 2) DEFAULT 0
        );
        -- No foreign key indexes - will cause nested loop joins
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
            metadata JSONB,
            description TEXT,
            reference_number VARCHAR(100)
        );
        -- No indexes except primary key
        -- Large JSONB and TEXT columns increase I/O
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
            request_duration INTEGER,
            endpoint VARCHAR(255),
            http_method VARCHAR(10),
            response_code INTEGER
        );
        -- No indexes for aggregation queries
        -- Will cause full scans for reporting
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
            execution_time INTEGER,
            parameters JSONB
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
            is_active BOOLEAN DEFAULT TRUE,
            page_views INTEGER DEFAULT 0
        );
        -- No index on user_id - will cause N+1 queries
        """
        self.execute_sql(sessions_table)
        
        # Table 10: Analytics (For complex reporting - Issue #10)
        print("\n11. Creating test_analytics table (complex analytics)...")
        analytics_table = """
        CREATE TABLE test_analytics (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(100),
            user_id INTEGER,
            session_id INTEGER,
            event_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            page_url TEXT,
            referrer TEXT,
            device_type VARCHAR(50),
            browser VARCHAR(50)
        );
        -- No indexes - large table for analytics queries
        """
        self.execute_sql(analytics_table)
        
        # Table 11: Audit Log (For stale statistics - Issue #6)
        print("\n12. Creating test_audit_log table (stale statistics)...")
        audit_table = """
        CREATE TABLE test_audit_log (
            id SERIAL PRIMARY KEY,
            table_name VARCHAR(100),
            operation VARCHAR(20),
            user_id INTEGER,
            old_values JSONB,
            new_values JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.execute_sql(audit_table)
        
        print("\n✓ All test tables created successfully")
    
    def populate_users(self, count=50000):
        """Populate users table"""
        print(f"\nPopulating test_users with {count:,} records...")
        
        departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 'Support']
        
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
                    random.randint(0, 500),
                    random.choice(departments),
                    round(random.uniform(30000, 150000), 2)
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_users 
                   (username, email, first_name, last_name, status, created_at, last_login, 
                    login_count, department, salary)
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
                    fake.date_time_between(start_date='-3y', end_date='now'),
                    random.randint(0, 500),
                    round(random.uniform(0, 100000), 2)
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_customers 
                   (customer_code, company_name, contact_name, country, city, status, 
                    created_at, total_orders, lifetime_value)
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
        subcategories = {
            'Electronics': ['Phones', 'Laptops', 'Tablets', 'Accessories'],
            'Clothing': ['Shirts', 'Pants', 'Shoes', 'Accessories'],
            'Books': ['Fiction', 'Non-Fiction', 'Educational', 'Comics'],
            'Home & Garden': ['Furniture', 'Decor', 'Tools', 'Plants'],
            'Sports': ['Equipment', 'Apparel', 'Accessories', 'Nutrition']
        }
        
        batch_size = 1000
        for i in range(0, count, batch_size):
            products = []
            for j in range(batch_size):
                if i + j >= count:
                    break
                category = random.choice(categories)
                subcategory = random.choice(subcategories.get(category, ['General']))
                price = round(random.uniform(5.99, 999.99), 2)
                cost = round(price * random.uniform(0.3, 0.7), 2)
                
                products.append((
                    f"PROD{i+j:06d}",
                    fake.catch_phrase(),
                    category,
                    subcategory,
                    price,
                    cost,
                    random.randint(0, 1000),
                    random.randint(1, 500),
                    fake.date_time_between(start_date='-2y', end_date='now'),
                    fake.date_time_between(start_date='-30d', end_date='now')
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_products 
                   (product_code, name, category, subcategory, price, cost, stock_quantity, 
                    supplier_id, created_at, last_updated)
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
        payment_methods = ['credit_card', 'debit_card', 'paypal', 'bank_transfer', 'cash']
        
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
                    fake.text(max_nb_chars=200) if random.random() > 0.7 else None,
                    random.choice(payment_methods),
                    f"DISC{random.randint(1, 100)}" if random.random() > 0.8 else None
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_orders 
                   (order_number, customer_id, user_id, order_date, status, total_amount, 
                    shipping_address, notes, payment_method, discount_code)
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
                unit_price = round(random.uniform(5.99, 999.99), 2)
                items.append((
                    random.randint(1, 100000),  # order_id
                    random.randint(1, 10000),   # product_id
                    random.randint(1, 10),
                    unit_price,
                    round(random.uniform(0, 20), 2) if random.random() > 0.7 else 0,
                    round(unit_price * 0.1, 2)  # tax
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_order_items 
                   (order_id, product_id, quantity, unit_price, discount, tax_amount)
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
                    'location': fake.city(),
                    'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
                    'os': random.choice(['Windows', 'MacOS', 'Linux', 'iOS', 'Android'])
                }
                transactions.append((
                    fake.uuid4(),
                    random.randint(1, 50000),
                    random.choice(transaction_types),
                    round(random.uniform(1.00, 10000.00), 2),
                    random.choice(['USD', 'EUR', 'GBP']),
                    random.choice(statuses),
                    fake.date_time_between(start_date='-6m', end_date='now'),
                    json.dumps(metadata),
                    fake.sentence(),
                    f"REF{i+j:08d}"
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_transactions 
                   (transaction_id, user_id, transaction_type, amount, currency, status, 
                    created_at, metadata, description, reference_number)
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
        endpoints = ['/api/users', '/api/orders', '/api/products', '/api/reports', '/api/analytics']
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        
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
                    random.randint(10, 5000),
                    random.choice(endpoints),
                    random.choice(methods),
                    random.choice([200, 201, 400, 401, 403, 404, 500, 503])
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_logs 
                   (log_level, message, user_id, ip_address, user_agent, created_at, 
                    request_duration, endpoint, http_method, response_code)
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
                    random.choice([True, False]),
                    random.randint(1, 50)
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_sessions 
                   (user_id, session_token, ip_address, user_agent, started_at, 
                    last_activity, is_active, page_views)
                   VALUES %s""",
                sessions
            )
            self.conn.commit()
            
            if (i + batch_size) % 10000 == 0:
                print(f"  Inserted {i + batch_size:,} sessions...")
        
        print(f"✓ Inserted {count:,} sessions")
    
    def populate_analytics(self, count=200000):
        """Populate analytics table"""
        print(f"\nPopulating test_analytics with {count:,} records...")
        
        event_types = ['page_view', 'click', 'form_submit', 'purchase', 'search', 'download']
        devices = ['desktop', 'mobile', 'tablet']
        browsers = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']
        
        batch_size = 2000
        for i in range(0, count, batch_size):
            analytics = []
            for j in range(batch_size):
                if i + j >= count:
                    break
                event_data = {
                    'duration': random.randint(1, 300),
                    'scroll_depth': random.randint(0, 100),
                    'clicks': random.randint(0, 20)
                }
                analytics.append((
                    random.choice(event_types),
                    random.randint(1, 50000),
                    random.randint(1, 30000),
                    json.dumps(event_data),
                    fake.date_time_between(start_date='-30d', end_date='now'),
                    fake.url(),
                    fake.url() if random.random() > 0.5 else None,
                    random.choice(devices),
                    random.choice(browsers)
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_analytics 
                   (event_type, user_id, session_id, event_data, created_at, 
                    page_url, referrer, device_type, browser)
                   VALUES %s""",
                analytics
            )
            self.conn.commit()
            
            if (i + batch_size) % 50000 == 0:
                print(f"  Inserted {i + batch_size:,} analytics events...")
        
        print(f"✓ Inserted {count:,} analytics events")
    
    def populate_audit_log(self, count=50000):
        """Populate audit log table"""
        print(f"\nPopulating test_audit_log with {count:,} records...")
        
        tables = ['test_users', 'test_orders', 'test_products', 'test_customers']
        operations = ['INSERT', 'UPDATE', 'DELETE']
        
        batch_size = 1000
        for i in range(0, count, batch_size):
            audits = []
            for j in range(batch_size):
                if i + j >= count:
                    break
                audits.append((
                    random.choice(tables),
                    random.choice(operations),
                    random.randint(1, 50000),
                    json.dumps({'old': 'value1'}),
                    json.dumps({'new': 'value2'}),
                    fake.date_time_between(start_date='-90d', end_date='now')
                ))
            
            execute_values(
                self.cursor,
                """INSERT INTO test_audit_log 
                   (table_name, operation, user_id, old_values, new_values, created_at)
                   VALUES %s""",
                audits
            )
            self.conn.commit()
            
            if (i + batch_size) % 10000 == 0:
                print(f"  Inserted {i + batch_size:,} audit records...")
        
        print(f"✓ Inserted {count:,} audit records")
    
    def create_stale_statistics(self):
        """Simulate stale statistics (Issue #6)"""
        print("\n" + "="*80)
        print("CREATING STALE STATISTICS")
        print("="*80)
        
        print("\nDisabling autovacuum for test tables...")
        tables = [
            'test_users', 'test_customers', 'test_products', 'test_orders',
            'test_order_items', 'test_transactions', 'test_logs', 'test_sessions',
            'test_analytics', 'test_audit_log'
        ]
        
        for table in tables:
            self.execute_sql(f"""
                ALTER TABLE {table} SET (
                    autovacuum_enabled = false,
                    toast.autovacuum_enabled = false
                );
            """)
        
        print("✓ Autovacuum disabled for all test tables")
        print("✓ Statistics will become stale as data changes")
    
    def populate_all_tables(self):
        """Populate all test tables with data"""
        print("\n" + "="*80)
        print("POPULATING TEST DATA")
        print("="*80)
        
        self.populate_users(50000)
        self.populate_customers(20000)
        self.populate_products(10000)
        self.populate_orders(100000)
        self.populate_order_items(250000)
        self.populate_transactions(150000)
        self.populate_logs(500000)
        self.populate_sessions(30000)
        self.populate_analytics(200000)
        self.populate_audit_log(50000)
        
        print("\n✓ All tables populated successfully")
        print(f"\nTotal records created: ~1,360,000")
    
    def get_problematic_queries(self):
        """Get comprehensive list of problematic queries"""
        return {
            "missing_index": [
                {
                    "name": "Missing index on email",
                    "sql": "SELECT * FROM test_users WHERE email = 'user@example.com'",
                    "description": "Missing index on email column causes full table scan"
                },
                {
                    "name": "Missing index on customer_id",
                    "sql": "SELECT * FROM test_orders WHERE customer_id = 12345",
                    "description": "Missing index on foreign key"
                },
                {
                    "name": "Missing index on department",
                    "sql": "SELECT * FROM test_users WHERE department = 'Engineering'",
                    "description": "Missing index on frequently queried column"
                }
            ],
            "inefficient_index": [
                {
                    "name": "Low selectivity index",
                    "sql": "SELECT * FROM test_customers WHERE status = 'active'",
                    "description": "Index on status has low selectivity (90% active)"
                },
                {
                    "name": "Wrong column order in composite index",
                    "sql": "SELECT * FROM test_customers WHERE country = 'USA' AND city = 'New York'",
                    "description": "Index is (city, country) but should be (country, city)"
                }
            ],
            "poor_join_strategy": [
                {
                    "name": "Multiple joins without indexes",
                    "sql": """
                    SELECT u.*, o.*, p.*, oi.*
                    FROM test_users u
                    JOIN test_orders o ON u.id = o.user_id
                    JOIN test_order_items oi ON o.id = oi.order_id
                    JOIN test_products p ON oi.product_id = p.id
                    WHERE u.status = 'active'
                    """,
                    "description": "Multiple joins without proper indexes"
                },
                {
                    "name": "Cross join creating cartesian product",
                    "sql": """
                    SELECT * FROM test_products p, test_customers c
                    WHERE p.category = 'Electronics'
                    """,
                    "description": "Implicit cross join without proper join condition"
                }
            ],
            "full_table_scan": [
                {
                    "name": "LIKE with leading wildcard",
                    "sql": "SELECT * FROM test_logs WHERE message LIKE '%error%'",
                    "description": "Full table scan on 500K rows"
                },
                {
                    "name": "Range query without index",
                    "sql": "SELECT * FROM test_transactions WHERE amount > 1000",
                    "description": "Full scan without index on amount"
                },
                {
                    "name": "Date range without index",
                    "sql": "SELECT * FROM test_orders WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31'",
                    "description": "Full scan on date column"
                }
            ],
            "suboptimal_pattern": [
                {
                    "name": "SELECT * anti-pattern",
                    "sql": "SELECT * FROM test_users WHERE id > 100",
                    "description": "Selecting all columns unnecessarily"
                },
                {
                    "name": "Unnecessary DISTINCT",
                    "sql": """
                    SELECT DISTINCT u.username, u.email 
                    FROM test_users u 
                    JOIN test_sessions s ON u.id = s.user_id
                    """,
                    "description": "DISTINCT used when not needed"
                },
                {
                    "name": "Multiple OR conditions",
                    "sql": """
                    SELECT * FROM test_orders 
                    WHERE status = 'pending' OR status = 'processing' 
                       OR status = 'shipped' OR status = 'delivered'
                    """,
                    "description": "Should use IN clause instead"
                },
                {
                    "name": "Correlated subquery",
                    "sql": """
                    SELECT u.*, 
                           (SELECT COUNT(*) FROM test_orders WHERE user_id = u.id) as order_count
                    FROM test_users u
                    """,
                    "description": "Correlated subquery executes for each row"
                },
                {
                    "name": "NOT IN with subquery",
                    "sql": "SELECT * FROM test_users WHERE email NOT IN (SELECT email FROM test_customers)",
                    "description": "NOT IN can be slow and has NULL issues"
                },
                {
                    "name": "Function on indexed column",
                    "sql": "SELECT * FROM test_users WHERE UPPER(email) = 'TEST@EXAMPLE.COM'",
                    "description": "Function prevents index usage"
                },
                {
                    "name": "UNION instead of UNION ALL",
                    "sql": """
                    SELECT user_id FROM test_orders
                    UNION
                    SELECT user_id FROM test_sessions
                    """,
                    "description": "UNION removes duplicates unnecessarily"
                }
            ],
            "stale_statistics": [
                {
                    "name": "Query on table with stale stats",
                    "sql": "SELECT * FROM test_audit_log WHERE table_name = 'test_users'",
                    "description": "Table statistics not updated, causing poor query plans"
                }
            ],
            "wrong_cardinality": [
                {
                    "name": "Query on skewed data",
                    "sql": "SELECT * FROM test_customers WHERE status = 'inactive'",
                    "description": "Only 10% inactive but optimizer may not know"
                }
            ],
            "orm_generated": [
                {
                    "name": "Excessive JOINs",
                    "sql": """
                    SELECT u.*, s.*, o.*, c.*, p.*, oi.*
                    FROM test_users u
                    LEFT JOIN test_sessions s ON u.id = s.user_id
                    LEFT JOIN test_orders o ON u.id = o.user_id
                    LEFT JOIN test_customers c ON o.customer_id = c.id
                    LEFT JOIN test_order_items oi ON o.id = oi.order_id
                    LEFT JOIN test_products p ON oi.product_id = p.id
                    """,
                    "description": "ORM eager loading with too many joins"
                },
                {
                    "name": "N+1 query pattern",
                    "sql": "SELECT * FROM test_users WHERE id = 1",
                    "description": "Would be executed many times (N+1 problem)"
                },
                {
                    "name": "SELECT * with multiple JOINs",
                    "sql": """
                    SELECT * FROM test_users u
                    JOIN test_orders o ON u.id = o.user_id
                    JOIN test_customers c ON o.customer_id = c.id
                    """,
                    "description": "ORM selecting all columns from all tables"
                }
            ],
            "high_io_workload": [
                {
                    "name": "Large dataset without indexes",
                    "sql": """
                    SELECT t.*, u.username, u.email
                    FROM test_transactions t
                    JOIN test_users u ON t.user_id = u.id
                    WHERE t.created_at > NOW() - INTERVAL '30 days'
                    ORDER BY t.amount DESC
                    """,
                    "description": "Large dataset with JSONB and TEXT columns"
                },
                {
                    "name": "Query with large result set",
                    "sql": "SELECT * FROM test_logs WHERE log_level IN ('ERROR', 'CRITICAL', 'WARNING')",
                    "description": "Returns large result set without pagination"
                }
            ],
            "inefficient_reporting": [
                {
                    "name": "Multiple aggregations without LIMIT",
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
                    "description": "Multiple aggregations without pagination"
                },
                {
                    "name": "Multiple window functions",
                    "sql": """
                    SELECT 
                        user_id,
                        COUNT(*) as session_count,
                        ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank,
                        DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) as dense_rank,
                        LAG(COUNT(*)) OVER (ORDER BY COUNT(*) DESC) as prev_count,
                        LEAD(COUNT(*)) OVER (ORDER BY COUNT(*) DESC) as next_count
                    FROM test_sessions
                    GROUP BY user_id
                    """,
                    "description": "Multiple window functions without pagination"
                },
                {
                    "name": "Complex analytics query",
                    "sql": """
                    SELECT 
                        event_type,
                        device_type,
                        browser,
                        COUNT(*) as event_count,
                        COUNT(DISTINCT user_id) as unique_users,
                        AVG(CAST(event_data->>'duration' AS INTEGER)) as avg_duration
                    FROM test_analytics
                    WHERE created_at > NOW() - INTERVAL '7 days'
                    GROUP BY event_type, device_type, browser
                    ORDER BY event_count DESC
                    """,
                    "description": "Complex analytics without indexes or materialized views"
                },
                {
                    "name": "Report with subqueries",
                    "sql": """
                    SELECT 
                        u.username,
                        (SELECT COUNT(*) FROM test_orders WHERE user_id = u.id) as total_orders,
                        (SELECT SUM(total_amount) FROM test_orders WHERE user_id = u.id) as total_spent,
                        (SELECT COUNT(*) FROM test_sessions WHERE user_id = u.id) as total_sessions
                    FROM test_users u
                    WHERE u.status = 'active'
                    """,
                    "description": "Multiple correlated subqueries in report"
                }
            ]
        }
    
    def execute_test_query(self, query_name, sql, description):
        """Execute a test query and measure performance"""
        print(f"\n  Testing: {query_name}")
        print(f"  Description: {description}")
        
        try:
            start_time = time.time()
            self.cursor.execute(f"EXPLAIN ANALYZE {sql}")
            result = self.cursor.fetchall()
            execution_time = time.time() - start_time
            
            print(f"  ✓ Execution time: {execution_time:.3f}s")
            
            self.query_results.append({
                "name": query_name,
                "description": description,
                "execution_time": execution_time,
                "success": True
            })
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.query_results.append({
                "name": query_name,
                "description": description,
                "error": str(e),
                "success": False
            })
    
    def test_all_queries(self):
        """Test all problematic queries"""
        print("\n" + "="*80)
        print("TESTING PROBLEMATIC QUERIES")
        print("="*80)
        
        queries = self.get_problematic_queries()
        
        for issue_type, query_list in queries.items():
            print(f"\n{issue_type.upper().replace('_', ' ')}:")
            print("-" * 80)
            
            for query in query_list:
                self.execute_test_query(
                    query["name"],
                    query["sql"],
                    query["description"]
                )
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "="*80)
        print("TEST DATABASE SUMMARY REPORT")
        print("="*80)
        
        # Table statistics
        tables = [
            'test_users', 'test_customers', 'test_products', 'test_orders',
            'test_order_items', 'test_transactions', 'test_logs', 'test_sessions',
            'test_analytics', 'test_audit_log'
        ]
        
        print("\n1. TABLE STATISTICS:")
        print("-" * 80)
        
        total_rows = 0
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            total_rows += count
            
            # Get table size
            self.cursor.execute(f"""
                SELECT pg_size_pretty(pg_total_relation_size('{table}'))
            """)
            size = self.cursor.fetchone()[0]
            
            print(f"  {table:25s}: {count:>10,} rows  ({size})")
        
        print("-" * 80)
        print(f"  {'TOTAL':25s}: {total_rows:>10,} rows")
        
        # Index information
        print("\n2. INDEX INFORMATION:")
        print("-" * 80)
        
        self.cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename LIKE 'test_%'
            ORDER BY tablename, indexname
        """)
        
        indexes = self.cursor.fetchall()
        print(f"  Total indexes: {len(indexes)}")
        
        for schema, table, index, definition in indexes:
            if 'pkey' not in index:  # Skip primary keys
                print(f"  {table}.{index}")
        
        # Issue types covered
        print("\n3. OPTIMIZATION ISSUES DEMONSTRATED:")
        print("-" * 80)
        
        issues = [
            ("1. Missing Indexes", "test_users.email, test_orders.customer_id, test_users.department"),
            ("2. Inefficient Indexes", "test_customers.status (low selectivity), wrong column order"),
            ("3. Poor Join Strategies", "Multiple tables without join indexes, cross joins"),
            ("4. Full Table Scans", "test_logs, test_transactions, LIKE patterns"),
            ("5. Suboptimal Patterns", "SELECT *, DISTINCT, OR chains, correlated subqueries"),
            ("6. Stale Statistics", "Autovacuum disabled on all test tables"),
            ("7. Wrong Cardinality", "test_customers.status (90/10 split)"),
            ("8. ORM-Generated SQL", "Excessive JOINs, N+1 patterns, SELECT *"),
            ("9. High I/O Workloads", "Large datasets with JSONB/TEXT, no indexes"),
            ("10. Inefficient Reporting", "Aggregations without LIMIT, window functions, complex analytics")
        ]
        
        for issue, description in issues:
            print(f"\n  {issue}")
            print(f"    → {description}")
        
        # Query test results
        if self.query_results:
            print("\n4. QUERY TEST RESULTS:")
            print("-" * 80)
            
            successful = sum(1 for r in self.query_results if r["success"])
            failed = len(self.query_results) - successful
            
            print(f"  Total queries tested: {len(self.query_results)}")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
            
            if successful > 0:
                avg_time = sum(r.get("execution_time", 0) for r in self.query_results if r["success"]) / successful
                print(f"  Average execution time: {avg_time:.3f}s")
        
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        
        print("\n1. Connect to the database in the AI SQL Optimizer application:")
        print(f"   Host: {DB_CONFIG['host']}")
        print(f"   Port: {DB_CONFIG['port']}")
        print(f"   Database: {DB_CONFIG['dbname']}")
        print(f"   User: {DB_CONFIG['user']}")
        
        print("\n2. Test queries from each issue category:")
        print("   - Copy queries from the test results above")
        print("   - Run them through the optimizer")
        print("   - Verify that issues are detected")
        
        print("\n3. Example queries to test:")
        
        print("\n   Missing Index:")
        print("   SELECT * FROM test_users WHERE email = 'user@example.com';")
        
        print("\n   Full Table Scan:")
        print("   SELECT * FROM test_logs WHERE message LIKE '%error%';")
        
        print("\n   Poor Join Strategy:")
        print("   SELECT u.*, o.*, p.* FROM test_users u")
        print("   JOIN test_orders o ON u.id = o.user_id")
        print("   JOIN test_order_items oi ON o.id = oi.order_id")
        print("   JOIN test_products p ON oi.product_id = p.id;")
        
        print("\n   Inefficient Reporting:")
        print("   SELECT DATE_TRUNC('day', created_at) as day, COUNT(*)")
        print("   FROM test_orders GROUP BY DATE_TRUNC('day', created_at);")
        
        print("\n" + "="*80)


def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("AI SQL OPTIMIZER PRO - ENHANCED TEST DATABASE GENERATOR")
    print("="*80)
    print(f"\nTarget Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    print(f"User: {DB_CONFIG['user']}")
    print("\nThis script will:")
    print("  1. Create 11 test tables with various optimization issues")
    print("  2. Populate tables with ~1.36 million records")
    print("  3. Disable autovacuum to create stale statistics")
    print("  4. Test problematic SQL queries")
    print("  5. Demonstrate all 10 SQL optimization issue types")
    print("\nEstimated time: 5-10 minutes")
    
    response = input("\nPress Enter to continue or type 'skip' to skip query testing: ")
    skip_tests = response.lower() == 'skip'
    
    generator = EnhancedTestDatabaseGenerator()
    
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
        
        # Test queries (optional)
        if not skip_tests:
            generator.test_all_queries()
        else:
            print("\n⏭️  Skipping query tests")
        
        # Generate summary report
        generator.generate_summary_report()
        
        print("\n" + "="*80)
        print("✅ TEST DATABASE CREATION COMPLETE")
        print("="*80)
        
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
