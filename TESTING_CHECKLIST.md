# Test Database Generator - Testing Checklist

Complete this checklist step-by-step to verify the test database generator works correctly.

## Pre-Testing Setup

### ☐ 1. Verify Prerequisites

```bash
# Check Python version (must be 3.7+)
python --version

# Check PostgreSQL client (optional but helpful)
psql --version
```

**Expected**: Python 3.7+ and optionally psql installed

---

### ☐ 2. Install Dependencies

```bash
# Install required packages
pip install -r test_database_requirements.txt
```

**Expected Output**:
```
Successfully installed psycopg2-binary-2.9.x Faker-18.x.x
```

**If Error**: Try `pip install psycopg2-binary Faker` directly

---

### ☐ 3. Test Database Connectivity (Manual)

```bash
# Test connection with psql
psql -h 192.168.1.81 -p 5432 -U admin -d mydb
```

**Expected**: Successfully connect and see `mydb=>` prompt

**If Connection Fails**:
- [ ] Check if PostgreSQL is running
- [ ] Verify firewall allows port 5432
- [ ] Confirm credentials are correct
- [ ] Test from same network as database

---

## Phase 1: Script Validation

### ☐ 4. Dry Run Check

Open `create_test_database.py` and verify:
- [ ] DB_CONFIG has correct connection details
- [ ] No syntax errors (run `python -m py_compile create_test_database.py`)

**Expected**: No compilation errors

---

### ☐ 5. Run Script (First Time)

```bash
python create_test_database.py
```

**Monitor for**:
- [ ] Connection success message
- [ ] Table creation messages (1-10)
- [ ] Data population progress
- [ ] No Python exceptions
- [ ] Summary report at end

**Expected Duration**: 5-10 minutes

**Record Results**:
```
Connection: [ SUCCESS / FAILED ]
Tables Created: [ X / 9 ]
Rows Inserted: [ ~X,XXX,XXX ]
Errors: [ NONE / LIST ERRORS ]
```

---

### ☐ 6. Verify Table Creation

```sql
-- Connect to database
psql -h 192.168.1.81 -p 5432 -U admin -d mydb

-- List all test tables
\dt test_*

-- Expected: 9 tables listed
-- test_customers, test_logs, test_order_items, test_orders,
-- test_products, test_reports, test_sessions, test_transactions, test_users
```

**Checklist**:
- [ ] test_users exists
- [ ] test_customers exists
- [ ] test_products exists
- [ ] test_orders exists
- [ ] test_order_items exists
- [ ] test_transactions exists
- [ ] test_logs exists
- [ ] test_sessions exists
- [ ] test_reports exists (may be empty)

---

### ☐ 7. Verify Row Counts

```sql
-- Check row counts for each table
SELECT 'test_users' as table_name, COUNT(*) as row_count FROM test_users
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
SELECT 'test_sessions', COUNT(*) FROM test_sessions;
```

**Expected Row Counts**:
- [ ] test_users: ~50,000
- [ ] test_customers: ~20,000
- [ ] test_products: ~10,000
- [ ] test_orders: ~100,000
- [ ] test_order_items: ~250,000
- [ ] test_transactions: ~150,000
- [ ] test_logs: ~500,000
- [ ] test_sessions: ~30,000

**Total**: ~1,110,000 rows

---

### ☐ 8. Verify Data Quality

```sql
-- Check for NULL values where they shouldn't be
SELECT COUNT(*) FROM test_users WHERE email IS NULL;
-- Expected: 0

SELECT COUNT(*) FROM test_products WHERE name IS NULL;
-- Expected: 0

-- Check data variety
SELECT DISTINCT status FROM test_users;
-- Expected: active, inactive, suspended

SELECT DISTINCT status FROM test_customers;
-- Expected: active, inactive

-- Check skewed distribution (90/10 split)
SELECT status, COUNT(*), 
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM test_customers
GROUP BY status;
-- Expected: active ~90%, inactive ~10%
```

**Checklist**:
- [ ] No unexpected NULL values
- [ ] Data has variety (not all same values)
- [ ] Skewed distribution is correct
- [ ] Timestamps are realistic

---

## Phase 2: Query Testing

### ☐ 9. Test Missing Index Query

```sql
-- This should be slow (no index on email)
EXPLAIN ANALYZE
SELECT * FROM test_users WHERE email = 'user@example.com';
```

**Expected**:
- [ ] Shows "Seq Scan" in plan
- [ ] Execution time > 50ms
- [ ] Scans all ~50,000 rows

**Record**: Execution time: _____ ms

---

### ☐ 10. Test Full Table Scan Query

```sql
-- This should be very slow (500K rows, no index)
EXPLAIN ANALYZE
SELECT * FROM test_logs WHERE message LIKE '%error%';
```

**Expected**:
- [ ] Shows "Seq Scan" in plan
- [ ] Execution time > 500ms
- [ ] Scans all ~500,000 rows

**Record**: Execution time: _____ ms

---

### ☐ 11. Test Poor Join Query

```sql
-- This should be slow (multiple joins without indexes)
EXPLAIN ANALYZE
SELECT u.username, o.order_number, p.name
FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_order_items oi ON o.id = oi.order_id
JOIN test_products p ON oi.product_id = p.id
LIMIT 100;
```

**Expected**:
- [ ] Shows "Nested Loop" or "Hash Join"
- [ ] Execution time > 1000ms
- [ ] Multiple sequential scans

**Record**: Execution time: _____ ms

---

### ☐ 12. Test Suboptimal Pattern Query

```sql
-- Function on column prevents index use
EXPLAIN ANALYZE
SELECT * FROM test_users WHERE UPPER(email) = 'TEST@EXAMPLE.COM';
```

**Expected**:
- [ ] Shows "Seq Scan" with filter
- [ ] Cannot use index (even if one existed)

---

### ☐ 13. Test Inefficient Reporting Query

```sql
-- Multiple aggregations without LIMIT
EXPLAIN ANALYZE
SELECT 
    DATE_TRUNC('day', created_at) as day,
    COUNT(*) as total_orders,
    SUM(total_amount) as revenue,
    AVG(total_amount) as avg_order
FROM test_orders
GROUP BY DATE_TRUNC('day', created_at);
```

**Expected**:
- [ ] Processes all 100,000 orders
- [ ] Execution time > 500ms
- [ ] Returns many rows (365+ days)

**Record**: Execution time: _____ ms

---

## Phase 3: Application Integration

### ☐ 14. Add Database Connection in Application

1. Open AI SQL Optimizer Pro
2. Navigate to Connections page
3. Click "Add Connection"
4. Enter details:
   - Name: Test Database
   - Engine: PostgreSQL
   - Host: 192.168.1.81
   - Port: 5432
   - Database: mydb
   - Username: admin
   - Password: admin123
5. Click "Test Connection"
6. Click "Save"

**Expected**:
- [ ] Connection test succeeds
- [ ] Connection appears in list
- [ ] Status shows "Connected"

---

### ☐ 15. Test Query Optimization (Missing Index)

1. Go to Optimizer page
2. Select "Test Database" connection
3. Paste query:
   ```sql
   SELECT * FROM test_users WHERE email = 'user@example.com';
   ```
4. Enable "Include execution plan analysis"
5. Click "Optimize Query"

**Expected Detection**:
- [ ] Issue Type: "missing_index"
- [ ] Severity: HIGH or MEDIUM
- [ ] Affected Objects: test_users
- [ ] Recommendation includes: CREATE INDEX on email

---

### ☐ 16. Test Query Optimization (Full Table Scan)

Paste query:
```sql
SELECT * FROM test_logs WHERE message LIKE '%error%';
```

**Expected Detection**:
- [ ] Issue Type: "full_table_scan"
- [ ] Severity: HIGH
- [ ] Affected Objects: test_logs
- [ ] Recommendation includes: index or full-text search

---

### ☐ 17. Test Query Optimization (Poor Join)

Paste query:
```sql
SELECT u.*, o.*, p.*
FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_order_items oi ON o.id = oi.order_id
JOIN test_products p ON oi.product_id = p.id;
```

**Expected Detection**:
- [ ] Issue Type: "poor_join_strategy"
- [ ] Severity: HIGH or MEDIUM
- [ ] Multiple issues detected
- [ ] Recommendations include: add indexes on join columns

---

### ☐ 18. Test Query Optimization (Suboptimal Pattern)

Paste query:
```sql
SELECT * FROM test_users WHERE UPPER(email) = 'TEST@EXAMPLE.COM';
```

**Expected Detection**:
- [ ] Issue Type: "suboptimal_pattern"
- [ ] Title mentions: "Function on indexed column"
- [ ] Recommendation: Move function to comparison value

---

### ☐ 19. Test Query Optimization (SELECT *)

Paste query:
```sql
SELECT * FROM test_users WHERE id > 100;
```

**Expected Detection**:
- [ ] Issue Type: "suboptimal_pattern"
- [ ] Title mentions: "SELECT *"
- [ ] Recommendation: Specify columns explicitly

---

### ☐ 20. Test Query Optimization (Inefficient Reporting)

Paste query:
```sql
SELECT 
    DATE_TRUNC('day', created_at) as day,
    COUNT(*) as total_orders,
    SUM(total_amount) as revenue
FROM test_orders
GROUP BY DATE_TRUNC('day', created_at);
```

**Expected Detection**:
- [ ] Issue Type: "inefficient_reporting"
- [ ] Title mentions: "Missing pagination" or "Multiple aggregations"
- [ ] Recommendation: Add LIMIT clause

---

## Phase 4: Performance Validation

### ☐ 21. Apply Recommended Indexes

```sql
-- Apply the recommended indexes
CREATE INDEX idx_users_email ON test_users(email);
CREATE INDEX idx_orders_customer_id ON test_orders(customer_id);
CREATE INDEX idx_orders_user_id ON test_orders(user_id);
CREATE INDEX idx_order_items_order_id ON test_order_items(order_id);
CREATE INDEX idx_order_items_product_id ON test_order_items(product_id);
CREATE INDEX idx_transactions_user_id ON test_transactions(user_id);
CREATE INDEX idx_sessions_user_id ON test_sessions(user_id);

-- Update statistics
ANALYZE test_users;
ANALYZE test_orders;
ANALYZE test_order_items;
ANALYZE test_transactions;
ANALYZE test_sessions;
```

**Expected**:
- [ ] All indexes created successfully
- [ ] ANALYZE completes without errors

---

### ☐ 22. Re-test Query Performance

```sql
-- Test 1: Missing index query (now with index)
EXPLAIN ANALYZE
SELECT * FROM test_users WHERE email = 'user@example.com';
```

**Expected After Index**:
- [ ] Shows "Index Scan" instead of "Seq Scan"
- [ ] Execution time < 5ms (100x faster)

**Record**: 
- Before: _____ ms
- After: _____ ms
- Improvement: _____x

---

```sql
-- Test 2: Join query (now with indexes)
EXPLAIN ANALYZE
SELECT u.username, o.order_number, p.name
FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_order_items oi ON o.id = oi.order_id
JOIN test_products p ON oi.product_id = p.id
LIMIT 100;
```

**Expected After Indexes**:
- [ ] Uses index scans instead of sequential scans
- [ ] Execution time < 100ms (10-50x faster)

**Record**: 
- Before: _____ ms
- After: _____ ms
- Improvement: _____x

---

## Phase 5: Edge Cases & Cleanup

### ☐ 23. Test Re-running Script

```bash
# Run the script again (should drop and recreate tables)
python create_test_database.py
```

**Expected**:
- [ ] Successfully drops existing tables
- [ ] Recreates all tables
- [ ] Repopulates data
- [ ] No errors about existing objects

---

### ☐ 24. Test Cleanup

```sql
-- Clean up test data
DROP TABLE IF EXISTS test_order_items CASCADE;
DROP TABLE IF EXISTS test_orders CASCADE;
DROP TABLE IF EXISTS test_products CASCADE;
DROP TABLE IF EXISTS test_customers CASCADE;
DROP TABLE IF EXISTS test_users CASCADE;
DROP TABLE IF EXISTS test_transactions CASCADE;
DROP TABLE IF EXISTS test_logs CASCADE;
DROP TABLE IF EXISTS test_reports CASCADE;
DROP TABLE IF EXISTS test_sessions CASCADE;

-- Verify cleanup
\dt test_*
```

**Expected**:
- [ ] All test tables dropped
- [ ] No test_* tables remain
- [ ] No errors

---

## Final Verification

### ☐ 25. Summary Checklist

**Script Execution**:
- [ ] Script runs without errors
- [ ] All 9 tables created
- [ ] ~1.1M rows inserted
- [ ] Summary report generated

**Data Quality**:
- [ ] Row counts match expectations
- [ ] No unexpected NULL values
- [ ] Data has realistic variety
- [ ] Skewed distribution is correct

**Query Performance**:
- [ ] Slow queries identified (before optimization)
- [ ] Fast queries achieved (after optimization)
- [ ] 10-100x performance improvement

**Issue Detection**:
- [ ] Missing index issues detected
- [ ] Full table scan issues detected
- [ ] Poor join strategy issues detected
- [ ] Suboptimal pattern issues detected
- [ ] Inefficient reporting issues detected

**Application Integration**:
- [ ] Database connection works
- [ ] Optimizer detects all issue types
- [ ] Recommendations are accurate
- [ ] Performance comparison shows improvement

---

## Test Results Summary

**Date**: _______________  
**Tester**: _______________  
**Duration**: _______________

**Overall Status**: [ PASS / FAIL / PARTIAL ]

**Issues Found**:
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

**Performance Improvements**:
- Missing Index Query: _____x faster
- Join Query: _____x faster
- Full Table Scan: _____x faster

**Recommendations**:
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

---

## Troubleshooting Guide

### Issue: Connection Timeout
**Solution**: 
- Check firewall settings
- Verify PostgreSQL allows remote connections
- Test with psql first

### Issue: Permission Denied
**Solution**:
- Grant CREATE privileges: `GRANT CREATE ON DATABASE mydb TO admin;`
- Check user has necessary permissions

### Issue: Out of Memory
**Solution**:
- Reduce row counts in script
- Increase PostgreSQL memory settings
- Run on machine with more RAM

### Issue: Slow Performance
**Solution**:
- Check network latency
- Run during off-peak hours
- Reduce batch sizes

### Issue: Data Not Realistic
**Solution**:
- Verify Faker library is installed correctly
- Check random seed is set (42)
- Review data generation logic

---

**After completing this checklist, you can confidently use the test database for SQL optimization testing!**
