# Quick Test Queries Reference

Quick reference for testing all 10 SQL optimization issues in the AI SQL Optimizer.

## Database Connection
```
Host: 192.168.1.81
Port: 5432
Database: mydb
User: admin
Password: admin123
```

---

## 1. Missing Index

```sql
-- Test 1: Missing index on email
SELECT * FROM test_users WHERE email = 'user@example.com';

-- Test 2: Missing index on foreign key
SELECT * FROM test_orders WHERE customer_id = 12345;

-- Test 3: Missing index on filter column
SELECT * FROM test_users WHERE department = 'Engineering';
```

**Expected:** Sequential scan, high cost, recommendation to add index

---

## 2. Inefficient Index

```sql
-- Test 1: Low selectivity index (90% active)
SELECT * FROM test_customers WHERE status = 'active';

-- Test 2: Wrong column order in composite index
SELECT * FROM test_customers WHERE country = 'USA' AND city = 'New York';
```

**Expected:** Bitmap scan, low selectivity warning, index not effective

---

## 3. Poor Join Strategy

```sql
-- Test 1: Multiple joins without indexes
SELECT u.username, o.order_number, p.name, oi.quantity
FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_order_items oi ON o.id = oi.order_id
JOIN test_products p ON oi.product_id = p.id
WHERE u.status = 'active'
LIMIT 100;

-- Test 2: Cross join (cartesian product)
SELECT * FROM test_products p, test_customers c
WHERE p.category = 'Electronics'
LIMIT 100;
```

**Expected:** Nested loop joins, high cost, recommendation for join indexes

---

## 4. Full Table Scan

```sql
-- Test 1: LIKE with leading wildcard
SELECT * FROM test_logs WHERE message LIKE '%error%' LIMIT 100;

-- Test 2: Range query without index
SELECT * FROM test_transactions WHERE amount > 1000 LIMIT 100;

-- Test 3: Date range without index
SELECT * FROM test_orders 
WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31'
LIMIT 100;
```

**Expected:** Sequential scan on large tables, recommendation for indexes

---

## 5. Suboptimal Query Patterns

```sql
-- Test 1: SELECT * anti-pattern
SELECT * FROM test_users WHERE id > 100 LIMIT 10;

-- Test 2: Unnecessary DISTINCT
SELECT DISTINCT u.username, u.email 
FROM test_users u 
JOIN test_sessions s ON u.id = s.user_id
LIMIT 100;

-- Test 3: Multiple OR conditions (should use IN)
SELECT * FROM test_orders 
WHERE status = 'pending' OR status = 'processing' 
   OR status = 'shipped' OR status = 'delivered'
LIMIT 100;

-- Test 4: Correlated subquery
SELECT u.username, u.email,
       (SELECT COUNT(*) FROM test_orders WHERE user_id = u.id) as order_count
FROM test_users u
LIMIT 100;

-- Test 5: NOT IN with subquery
SELECT * FROM test_users 
WHERE email NOT IN (SELECT contact_name FROM test_customers)
LIMIT 100;

-- Test 6: Function on indexed column
SELECT * FROM test_users WHERE UPPER(email) = 'TEST@EXAMPLE.COM';

-- Test 7: UNION instead of UNION ALL
SELECT user_id FROM test_orders LIMIT 100
UNION
SELECT user_id FROM test_sessions LIMIT 100;
```

**Expected:** Detection of anti-patterns, recommendations for better approaches

---

## 6. Stale Statistics

```sql
-- Test: Query on table with stale statistics
SELECT * FROM test_audit_log WHERE table_name = 'test_users' LIMIT 100;

-- Check statistics age
SELECT 
    schemaname,
    tablename,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE tablename LIKE 'test_%';
```

**Expected:** Warning about stale statistics, recommendation to run ANALYZE

---

## 7. Wrong Cardinality Estimates

```sql
-- Test: Query on skewed data (only 10% inactive)
SELECT * FROM test_customers WHERE status = 'inactive';

-- Compare with majority case
SELECT * FROM test_customers WHERE status = 'active' LIMIT 100;
```

**Expected:** Inaccurate row estimates, poor query plan choices

---

## 8. ORM-Generated SQL

```sql
-- Test 1: Excessive JOINs (ORM eager loading)
SELECT u.*, s.*, o.*, c.*, p.*
FROM test_users u
LEFT JOIN test_sessions s ON u.id = s.user_id
LEFT JOIN test_orders o ON u.id = o.user_id
LEFT JOIN test_customers c ON o.customer_id = c.id
LEFT JOIN test_products p ON p.id IN (
    SELECT product_id FROM test_order_items WHERE order_id = o.id LIMIT 1
)
LIMIT 10;

-- Test 2: N+1 query pattern (simulate by running multiple times)
SELECT * FROM test_users WHERE id = 1;
SELECT * FROM test_users WHERE id = 2;
SELECT * FROM test_users WHERE id = 3;

-- Test 3: SELECT * with multiple JOINs
SELECT * FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_customers c ON o.customer_id = c.id
LIMIT 100;
```

**Expected:** Detection of ORM anti-patterns, recommendations for optimization

---

## 9. High I/O Workload

```sql
-- Test 1: Large dataset with JSONB/TEXT columns
SELECT t.*, u.username, u.email
FROM test_transactions t
JOIN test_users u ON t.user_id = u.id
WHERE t.created_at > NOW() - INTERVAL '30 days'
ORDER BY t.amount DESC
LIMIT 100;

-- Test 2: Query with large result set
SELECT * FROM test_logs 
WHERE log_level IN ('ERROR', 'CRITICAL', 'WARNING')
LIMIT 1000;

-- Test 3: JSONB query without index
SELECT * FROM test_transactions
WHERE metadata->>'device' = 'mobile'
LIMIT 100;
```

**Expected:** High buffer reads, low cache hit ratio, I/O warnings

---

## 10. Inefficient Reporting Queries

```sql
-- Test 1: Multiple aggregations without LIMIT
SELECT 
    DATE_TRUNC('day', created_at) as day,
    COUNT(*) as total_orders,
    SUM(total_amount) as revenue,
    AVG(total_amount) as avg_order,
    MAX(total_amount) as max_order,
    MIN(total_amount) as min_order
FROM test_orders
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY day DESC;

-- Test 2: Multiple window functions
SELECT 
    user_id,
    COUNT(*) as session_count,
    ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank,
    DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) as dense_rank,
    LAG(COUNT(*)) OVER (ORDER BY COUNT(*) DESC) as prev_count,
    LEAD(COUNT(*)) OVER (ORDER BY COUNT(*) DESC) as next_count
FROM test_sessions
GROUP BY user_id
ORDER BY session_count DESC;

-- Test 3: Complex analytics query
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

-- Test 4: Report with multiple correlated subqueries
SELECT 
    u.username,
    u.email,
    (SELECT COUNT(*) FROM test_orders WHERE user_id = u.id) as total_orders,
    (SELECT SUM(total_amount) FROM test_orders WHERE user_id = u.id) as total_spent,
    (SELECT COUNT(*) FROM test_sessions WHERE user_id = u.id) as total_sessions
FROM test_users u
WHERE u.status = 'active'
LIMIT 100;
```

**Expected:** Missing LIMIT warnings, complex aggregation warnings, recommendations for optimization

---

## Verification Queries

```sql
-- Check table row counts
SELECT 
    'test_users' as table_name, COUNT(*) as rows FROM test_users
UNION ALL SELECT 'test_customers', COUNT(*) FROM test_customers
UNION ALL SELECT 'test_products', COUNT(*) FROM test_products
UNION ALL SELECT 'test_orders', COUNT(*) FROM test_orders
UNION ALL SELECT 'test_order_items', COUNT(*) FROM test_order_items
UNION ALL SELECT 'test_transactions', COUNT(*) FROM test_transactions
UNION ALL SELECT 'test_logs', COUNT(*) FROM test_logs
UNION ALL SELECT 'test_sessions', COUNT(*) FROM test_sessions
UNION ALL SELECT 'test_analytics', COUNT(*) FROM test_analytics
UNION ALL SELECT 'test_audit_log', COUNT(*) FROM test_audit_log;

-- Check indexes
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename LIKE 'test_%'
ORDER BY tablename, indexname;

-- Check autovacuum status
SELECT 
    relname,
    reloptions
FROM pg_class
WHERE relname LIKE 'test_%'
AND relkind = 'r'
ORDER BY relname;
```

---

## Testing Workflow

1. **Connect** to database in AI SQL Optimizer
2. **Copy** a test query from above
3. **Paste** into the optimizer
4. **Click** "Analyze Query"
5. **Verify** issues are detected
6. **Review** recommendations
7. **Repeat** for all issue types

---

## Expected Detection Summary

| Issue Type | Test Queries | Expected Detections |
|------------|--------------|---------------------|
| Missing Index | 3 | Sequential scans, missing index recommendations |
| Inefficient Index | 2 | Low selectivity, wrong column order |
| Poor Joins | 2 | Nested loops, cartesian products |
| Full Table Scan | 3 | Sequential scans on large tables |
| Suboptimal Patterns | 7 | Various anti-patterns detected |
| Stale Statistics | 1 | Statistics age warning |
| Wrong Cardinality | 1 | Inaccurate row estimates |
| ORM Issues | 3 | Excessive joins, N+1 patterns |
| High I/O | 3 | High buffer reads, I/O warnings |
| Inefficient Reporting | 4 | Missing LIMIT, complex aggregations |

**Total Test Queries:** 29

---

## Quick Tips

- Always use `LIMIT` when testing to avoid long-running queries
- Use `EXPLAIN ANALYZE` to see actual execution plans
- Compare execution times before and after applying fixes
- Test on a copy of production data when possible
- Monitor query performance over time

---

## Cleanup

```sql
-- Remove all test tables when done
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
