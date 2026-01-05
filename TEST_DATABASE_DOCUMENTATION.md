# Test Database Documentation

## Overview

This document describes the comprehensive test database created for the AI SQL Optimizer Pro application. The database contains realistic test data designed to demonstrate all 9 types of SQL optimization issues.

## Database Connection

- **Host**: 192.168.1.81
- **Port**: 5432
- **Database**: mydb
- **User**: admin
- **Password**: admin123

## Test Tables

### 1. test_users (50,000 rows)
**Purpose**: Demonstrate missing index issues

**Schema**:
```sql
CREATE TABLE test_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,  -- NO INDEX (intentional)
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0
);
```

**Optimization Issues**:
- Missing index on `email` column (frequently queried)
- Missing index on `status` column

### 2. test_customers (20,000 rows)
**Purpose**: Demonstrate inefficient index and wrong cardinality

**Schema**:
```sql
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
CREATE INDEX idx_customers_status ON test_customers(status);  -- Low selectivity
```

**Optimization Issues**:
- Inefficient index on `status` (only 2 values: 90% active, 10% inactive)
- Skewed data distribution causes wrong cardinality estimates

### 3. test_products (10,000 rows)
**Purpose**: Demonstrate poor join strategies

**Schema**:
```sql
CREATE TABLE test_products (
    id SERIAL PRIMARY KEY,
    product_code VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),  -- NO INDEX
    price DECIMAL(10, 2),
    stock_quantity INTEGER DEFAULT 0,
    supplier_id INTEGER,  -- NO INDEX
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Optimization Issues**:
- No index on `category` (frequently used in JOINs)
- No index on `supplier_id` (foreign key without index)

### 4. test_orders (100,000 rows)
**Purpose**: Demonstrate full table scans

**Schema**:
```sql
CREATE TABLE test_orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50),
    customer_id INTEGER,  -- NO INDEX
    user_id INTEGER,  -- NO INDEX
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(12, 2),
    shipping_address TEXT,
    notes TEXT
);
```

**Optimization Issues**:
- No indexes except primary key
- Queries on `customer_id`, `user_id`, `status` cause full table scans

### 5. test_order_items (250,000 rows)
**Purpose**: Demonstrate complex join issues

**Schema**:
```sql
CREATE TABLE test_order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER,  -- NO INDEX
    product_id INTEGER,  -- NO INDEX
    quantity INTEGER,
    unit_price DECIMAL(10, 2),
    discount DECIMAL(5, 2) DEFAULT 0
);
```

**Optimization Issues**:
- No foreign key indexes
- Joins with orders and products are inefficient

### 6. test_transactions (150,000 rows)
**Purpose**: Demonstrate high I/O workloads

**Schema**:
```sql
CREATE TABLE test_transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(100),
    user_id INTEGER,  -- NO INDEX
    transaction_type VARCHAR(50),
    amount DECIMAL(12, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);
```

**Optimization Issues**:
- Large table with no indexes
- High disk I/O for queries
- Low cache hit ratio

### 7. test_logs (500,000 rows)
**Purpose**: Demonstrate inefficient reporting and full table scans

**Schema**:
```sql
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
```

**Optimization Issues**:
- Largest table with no indexes
- Text searches cause full table scans
- Aggregation queries are slow

### 8. test_sessions (30,000 rows)
**Purpose**: Demonstrate ORM N+1 query patterns

**Schema**:
```sql
CREATE TABLE test_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,  -- NO INDEX
    session_token VARCHAR(255),
    ip_address VARCHAR(50),
    user_agent TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

**Optimization Issues**:
- No index on `user_id` causes N+1 queries
- Typical ORM eager loading problems

## Problematic Query Examples

### Issue #1: Missing Index
```sql
-- Query on email without index
SELECT * FROM test_users WHERE email = 'user@example.com';

-- Query on customer_id without index
SELECT * FROM test_orders WHERE customer_id = 12345;
```

### Issue #2: Inefficient Index
```sql
-- Low selectivity index (90% of rows match)
SELECT * FROM test_customers WHERE status = 'active';
```

### Issue #3: Poor Join Strategy
```sql
-- Multiple joins without proper indexes
SELECT u.*, o.*, p.*, oi.*
FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_order_items oi ON o.id = oi.order_id
JOIN test_products p ON oi.product_id = p.id
WHERE u.status = 'active';
```

### Issue #4: Full Table Scan
```sql
-- Full scan on 500K rows
SELECT * FROM test_logs WHERE message LIKE '%error%';

-- Full scan without index
SELECT * FROM test_transactions WHERE amount > 1000;
```

### Issue #5: Suboptimal Query Patterns
```sql
-- SELECT * anti-pattern
SELECT * FROM test_users WHERE id > 100;

-- Unnecessary DISTINCT
SELECT DISTINCT u.username, u.email 
FROM test_users u 
JOIN test_sessions s ON u.id = s.user_id;

-- Multiple OR conditions (should use IN)
SELECT * FROM test_products 
WHERE status = 'active' OR status = 'pending' 
   OR status = 'processing' OR status = 'shipped';

-- Correlated subquery in SELECT
SELECT u.*, 
       (SELECT COUNT(*) FROM test_orders WHERE user_id = u.id) as order_count
FROM test_users u;

-- NOT IN with subquery
SELECT * FROM test_users 
WHERE email NOT IN (SELECT email FROM test_customers);

-- LIKE with leading wildcard
SELECT * FROM test_products WHERE name LIKE '%phone%';

-- Function on indexed column
SELECT * FROM test_users WHERE UPPER(email) = 'TEST@EXAMPLE.COM';
```

### Issue #6: Stale Statistics
```sql
-- Tables are not analyzed, causing poor query plans
-- Run ANALYZE to update statistics
```

### Issue #7: Wrong Cardinality
```sql
-- Query on skewed data (only 10% inactive)
SELECT * FROM test_customers WHERE status = 'inactive';
```

### Issue #8: ORM-Generated SQL
```sql
-- Excessive JOINs (typical ORM eager loading)
SELECT u.*, s.*, o.*, c.*, p.*
FROM test_users u
LEFT JOIN test_sessions s ON u.id = s.user_id
LEFT JOIN test_orders o ON u.id = o.user_id
LEFT JOIN test_customers c ON o.customer_id = c.id
LEFT JOIN test_products p ON p.id IN 
    (SELECT product_id FROM test_order_items WHERE order_id = o.id);

-- N+1 query pattern (executed many times)
SELECT * FROM test_users WHERE id = 1;
SELECT * FROM test_users WHERE id = 2;
-- ... repeated for each user
```

### Issue #9: High I/O Workload
```sql
-- Large dataset without proper indexes
SELECT t.*, u.username, u.email
FROM test_transactions t
JOIN test_users u ON t.user_id = u.id
WHERE t.created_at > NOW() - INTERVAL '30 days'
ORDER BY t.amount DESC;
```

### Issue #10: Inefficient Reporting
```sql
-- Multiple aggregations without LIMIT
SELECT 
    DATE_TRUNC('day', created_at) as day,
    COUNT(*) as total_orders,
    SUM(total_amount) as revenue,
    AVG(total_amount) as avg_order,
    MAX(total_amount) as max_order,
    MIN(total_amount) as min_order
FROM test_orders
GROUP BY DATE_TRUNC('day', created_at);

-- Multiple window functions without pagination
SELECT 
    user_id,
    COUNT(*) as session_count,
    ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank,
    DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) as dense_rank,
    LAG(COUNT(*)) OVER (ORDER BY COUNT(*) DESC) as prev_count
FROM test_sessions
GROUP BY user_id;
```

## Data Statistics

| Table | Rows | Purpose |
|-------|------|---------|
| test_users | 50,000 | Missing indexes |
| test_customers | 20,000 | Inefficient indexes, skewed data |
| test_products | 10,000 | Poor join strategies |
| test_orders | 100,000 | Full table scans |
| test_order_items | 250,000 | Complex joins |
| test_transactions | 150,000 | High I/O workloads |
| test_logs | 500,000 | Inefficient reporting |
| test_sessions | 30,000 | ORM N+1 patterns |
| **TOTAL** | **1,110,000** | |

## Testing Workflow

### 1. Connect to Database
In the AI SQL Optimizer Pro application:
1. Go to Connections page
2. Add new connection:
   - Name: Test Database
   - Engine: PostgreSQL
   - Host: 192.168.1.81
   - Port: 5432
   - Database: mydb
   - Username: admin
   - Password: admin123

### 2. Run Optimizer Tests
1. Go to Optimizer page
2. Select the test database connection
3. Paste one of the problematic queries
4. Enable "Include execution plan analysis"
5. Click "Optimize Query"
6. Review detected issues

### 3. Verify Issue Detection
The optimizer should detect:
- ✅ Missing indexes
- ✅ Inefficient indexes
- ✅ Poor join strategies
- ✅ Full table scans
- ✅ Suboptimal query patterns
- ✅ Stale statistics
- ✅ Wrong cardinality estimates
- ✅ ORM-generated SQL issues
- ✅ High I/O workloads
- ✅ Inefficient reporting queries

### 4. Apply Optimizations
1. Review recommendations
2. Apply suggested fixes
3. Re-run queries to verify improvements

## Recommended Index Fixes

```sql
-- Fix missing indexes
CREATE INDEX idx_users_email ON test_users(email);
CREATE INDEX idx_orders_customer_id ON test_orders(customer_id);
CREATE INDEX idx_orders_user_id ON test_orders(user_id);
CREATE INDEX idx_order_items_order_id ON test_order_items(order_id);
CREATE INDEX idx_order_items_product_id ON test_order_items(product_id);
CREATE INDEX idx_transactions_user_id ON test_transactions(user_id);
CREATE INDEX idx_transactions_created_at ON test_transactions(created_at);
CREATE INDEX idx_sessions_user_id ON test_sessions(user_id);
CREATE INDEX idx_logs_created_at ON test_logs(created_at);
CREATE INDEX idx_logs_log_level ON test_logs(log_level);

-- Update statistics
ANALYZE test_users;
ANALYZE test_customers;
ANALYZE test_products;
ANALYZE test_orders;
ANALYZE test_order_items;
ANALYZE test_transactions;
ANALYZE test_logs;
ANALYZE test_sessions;
```

## Performance Comparison

### Before Optimization
- Missing index queries: 500-2000ms
- Full table scans: 1000-5000ms
- Complex joins: 2000-10000ms
- Reporting queries: 5000-20000ms

### After Optimization
- Indexed queries: 1-10ms
- Optimized scans: 10-100ms
- Efficient joins: 50-500ms
- Optimized reports: 100-1000ms

**Expected Improvement**: 10x - 100x faster

## Cleanup

To remove test data:
```sql
DROP TABLE IF EXISTS test_order_items CASCADE;
DROP TABLE IF EXISTS test_orders CASCADE;
DROP TABLE IF EXISTS test_products CASCADE;
DROP TABLE IF EXISTS test_customers CASCADE;
DROP TABLE IF EXISTS test_users CASCADE;
DROP TABLE IF EXISTS test_transactions CASCADE;
DROP TABLE IF EXISTS test_logs CASCADE;
DROP TABLE IF EXISTS test_reports CASCADE;
DROP TABLE IF EXISTS test_sessions CASCADE;
```

## Notes

- Data is generated using Faker library for realistic values
- Random seed (42) ensures reproducible results
- Skewed data distribution (90/10) simulates real-world scenarios
- Large row counts ensure performance issues are visible
- No foreign key constraints to allow flexible testing

## Support

For issues or questions:
1. Check the application logs
2. Verify database connection
3. Ensure PostgreSQL version compatibility (9.6+)
4. Review execution plans in pgAdmin or psql
