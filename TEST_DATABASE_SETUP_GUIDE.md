# Test Database Setup Guide

## Overview

This guide explains how to set up a comprehensive test database with all 10 SQL optimization issues for testing the AI SQL Optimizer Pro.

## Database Configuration

**Target Database:**
- Host: `192.168.1.81`
- Port: `5432`
- Database: `mydb`
- User: `admin`
- Password: `admin123`

## What Gets Created

### Tables (11 total)
1. **test_users** (50,000 rows) - Missing indexes on email, department, salary
2. **test_customers** (20,000 rows) - Inefficient indexes, skewed data distribution
3. **test_products** (10,000 rows) - No join indexes
4. **test_orders** (100,000 rows) - Full table scan scenarios
5. **test_order_items** (250,000 rows) - Complex join scenarios
6. **test_transactions** (150,000 rows) - High I/O workloads with JSONB
7. **test_logs** (500,000 rows) - Reporting query scenarios
8. **test_reports** - Report metadata
9. **test_sessions** (30,000 rows) - ORM N+1 patterns
10. **test_analytics** (200,000 rows) - Complex analytics queries
11. **test_audit_log** (50,000 rows) - Stale statistics

**Total Records:** ~1,360,000

### Optimization Issues Demonstrated

#### 1. Missing Indexes
- `test_users.email` - No index on frequently queried column
- `test_orders.customer_id` - No index on foreign key
- `test_users.department` - No index on filter column

**Test Query:**
```sql
SELECT * FROM test_users WHERE email = 'user@example.com';
```

#### 2. Inefficient Indexes
- `test_customers.status` - Low selectivity (90% active, 10% inactive)
- `test_customers(city, country)` - Wrong column order in composite index

**Test Query:**
```sql
SELECT * FROM test_customers WHERE status = 'active';
```

#### 3. Poor Join Strategies
- Multiple tables without join indexes
- Cross joins creating cartesian products

**Test Query:**
```sql
SELECT u.*, o.*, p.*, oi.*
FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_order_items oi ON o.id = oi.order_id
JOIN test_products p ON oi.product_id = p.id
WHERE u.status = 'active';
```

#### 4. Full Table Scans
- LIKE with leading wildcards
- Range queries without indexes
- Date range queries without indexes

**Test Query:**
```sql
SELECT * FROM test_logs WHERE message LIKE '%error%';
```

#### 5. Suboptimal Query Patterns
- SELECT * anti-pattern
- Unnecessary DISTINCT
- Multiple OR conditions (should use IN)
- Correlated subqueries
- NOT IN with subqueries
- Functions on indexed columns
- UNION instead of UNION ALL

**Test Queries:**
```sql
-- SELECT * anti-pattern
SELECT * FROM test_users WHERE id > 100;

-- Multiple OR conditions
SELECT * FROM test_orders 
WHERE status = 'pending' OR status = 'processing' 
   OR status = 'shipped' OR status = 'delivered';

-- Correlated subquery
SELECT u.*, 
       (SELECT COUNT(*) FROM test_orders WHERE user_id = u.id) as order_count
FROM test_users u;

-- Function on indexed column
SELECT * FROM test_users WHERE UPPER(email) = 'TEST@EXAMPLE.COM';
```

#### 6. Stale Statistics
- Autovacuum disabled on all test tables
- Statistics not updated after data changes

**Test Query:**
```sql
SELECT * FROM test_audit_log WHERE table_name = 'test_users';
```

#### 7. Wrong Cardinality Estimates
- Skewed data distribution (90% active, 10% inactive)
- Optimizer may not have accurate statistics

**Test Query:**
```sql
SELECT * FROM test_customers WHERE status = 'inactive';
```

#### 8. ORM-Generated SQL
- Excessive JOINs from eager loading
- N+1 query patterns
- SELECT * with multiple JOINs

**Test Queries:**
```sql
-- Excessive JOINs
SELECT u.*, s.*, o.*, c.*, p.*, oi.*
FROM test_users u
LEFT JOIN test_sessions s ON u.id = s.user_id
LEFT JOIN test_orders o ON u.id = o.user_id
LEFT JOIN test_customers c ON o.customer_id = c.id
LEFT JOIN test_order_items oi ON o.id = oi.order_id
LEFT JOIN test_products p ON oi.product_id = p.id;

-- N+1 pattern (would be executed many times)
SELECT * FROM test_users WHERE id = 1;
```

#### 9. High I/O Workloads
- Large datasets without indexes
- JSONB and TEXT columns
- Large result sets without pagination

**Test Query:**
```sql
SELECT t.*, u.username, u.email
FROM test_transactions t
JOIN test_users u ON t.user_id = u.id
WHERE t.created_at > NOW() - INTERVAL '30 days'
ORDER BY t.amount DESC;
```

#### 10. Inefficient Reporting Queries
- Multiple aggregations without LIMIT
- Multiple window functions without pagination
- Complex analytics without indexes
- Multiple correlated subqueries

**Test Queries:**
```sql
-- Multiple aggregations
SELECT 
    DATE_TRUNC('day', created_at) as day,
    COUNT(*) as total_orders,
    SUM(total_amount) as revenue,
    AVG(total_amount) as avg_order,
    MAX(total_amount) as max_order,
    MIN(total_amount) as min_order
FROM test_orders
GROUP BY DATE_TRUNC('day', created_at);

-- Multiple window functions
SELECT 
    user_id,
    COUNT(*) as session_count,
    ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank,
    DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) as dense_rank,
    LAG(COUNT(*)) OVER (ORDER BY COUNT(*) DESC) as prev_count,
    LEAD(COUNT(*)) OVER (ORDER BY COUNT(*) DESC) as next_count
FROM test_sessions
GROUP BY user_id;

-- Complex analytics
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
ORDER BY event_count DESC;
```

## Setup Instructions

### Prerequisites

1. Python 3.8 or higher
2. Required Python packages:
   ```bash
   pip install psycopg2-binary faker
   ```
3. PostgreSQL database accessible at 192.168.1.81:5432
4. Database user with CREATE TABLE permissions

### Option 1: Quick Setup (Recommended)

Run the quick setup script:

```bash
python setup_test_database.py
```

This will:
- Create all tables
- Populate with data
- Configure stale statistics
- Skip query testing for faster setup

### Option 2: Full Setup with Query Testing

Run the enhanced script directly:

```bash
python create_test_database_enhanced.py
```

When prompted:
- Press Enter to include query testing
- Type 'skip' to skip query testing

### Option 3: Original Script

Run the original test database script:

```bash
python create_test_database.py
```

## Verification

After setup, verify the database:

```sql
-- Check table counts
SELECT 
    'test_users' as table_name, COUNT(*) as row_count FROM test_users
UNION ALL
SELECT 'test_customers', COUNT(*) FROM test_customers
UNION ALL
SELECT 'test_products', COUNT(*) FROM test_products
UNION ALL
SELECT 'test_orders', COUNT(*) FROM test_orders
UNION ALL
SELECT 'test_order_items', COUNT(*) FROM test_order_items
UNION ALL
SELECT 'test_transactions', COUNT(*) FROM test_transactions
UNION ALL
SELECT 'test_logs', COUNT(*) FROM test_logs
UNION ALL
SELECT 'test_sessions', COUNT(*) FROM test_sessions
UNION ALL
SELECT 'test_analytics', COUNT(*) FROM test_analytics
UNION ALL
SELECT 'test_audit_log', COUNT(*) FROM test_audit_log;

-- Check indexes
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename LIKE 'test_%'
ORDER BY tablename, indexname;

-- Verify autovacuum is disabled
SELECT 
    relname,
    reloptions
FROM pg_class
WHERE relname LIKE 'test_%'
AND relkind = 'r';
```

## Testing with AI SQL Optimizer

### 1. Connect to Database

In the AI SQL Optimizer application:
- Host: `192.168.1.81`
- Port: `5432`
- Database: `mydb`
- User: `admin`
- Password: `admin123`

### 2. Test Each Issue Type

Copy and paste the test queries from each section above into the optimizer and verify that:
- Issues are detected correctly
- Recommendations are provided
- Execution plans show the problems

### 3. Expected Detections

For each query, the optimizer should detect:

| Query Type | Expected Issues |
|------------|----------------|
| Missing Index | Sequential scan, high cost |
| Inefficient Index | Low selectivity, bitmap scan |
| Poor Joins | Nested loop on large dataset |
| Full Table Scan | Sequential scan on 500K+ rows |
| Suboptimal Patterns | Anti-patterns detected |
| Stale Statistics | Inaccurate row estimates |
| Wrong Cardinality | Incorrect row estimates |
| ORM Issues | Excessive joins, N+1 pattern |
| High I/O | High buffer reads, low cache hit ratio |
| Inefficient Reporting | Missing LIMIT, complex aggregations |

## Cleanup

To remove all test tables:

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
DROP TABLE IF EXISTS test_analytics CASCADE;
DROP TABLE IF EXISTS test_audit_log CASCADE;
```

## Troubleshooting

### Connection Issues

If you can't connect to the database:
1. Verify the database is running: `pg_isready -h 192.168.1.81 -p 5432`
2. Check firewall rules allow connections to port 5432
3. Verify user credentials are correct
4. Check `pg_hba.conf` allows connections from your IP

### Permission Issues

If you get permission errors:
```sql
-- Grant necessary permissions
GRANT CREATE ON DATABASE mydb TO admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
```

### Memory Issues

If the script runs out of memory:
- Reduce batch sizes in the populate methods
- Run table population one at a time
- Increase available system memory

### Slow Performance

If data population is slow:
- Check network latency to database server
- Verify database has sufficient resources
- Consider running on the database server directly

## Performance Expectations

- **Setup Time:** 5-10 minutes
- **Database Size:** ~500 MB - 1 GB
- **Query Execution Times:**
  - Fast queries (with indexes): < 100ms
  - Slow queries (without indexes): 1-10 seconds
  - Very slow queries (full scans): 10-30 seconds

## Next Steps

After setting up the test database:

1. **Test Detection:** Run queries through the optimizer to verify all 10 issue types are detected
2. **Test Recommendations:** Verify that appropriate recommendations are provided
3. **Test Fixes:** Apply recommended fixes and verify performance improvements
4. **Test Monitoring:** Use the monitoring features to track query performance over time
5. **Test Dashboard:** Verify dashboard displays detected issues correctly

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Query Optimization Best Practices](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Index Types in PostgreSQL](https://www.postgresql.org/docs/current/indexes-types.html)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the test database script comments
3. Verify database connectivity and permissions
4. Check application logs for detailed error messages
