# ✅ Verified Working Queries for Test Database

These queries have been confirmed to work with the test database and will trigger issue detection in the AI SQL Optimizer.

## Database Connection
```
Host: 192.168.1.81
Port: 5432
Database: mydb
User: admin
Password: admin123
```

---

## ✅ 1. Missing Index Issues

### Query 1: Missing index on email
```sql
SELECT * FROM test_users WHERE email = 'user@example.com';
```
**Expected Detection:**
- ✅ Sequential Scan detected
- ✅ Missing index recommendation
- ✅ Severity: High
- ✅ Recommendation: `CREATE INDEX idx_users_email ON test_users(email);`

### Query 2: Missing index on foreign key
```sql
SELECT * FROM test_orders WHERE customer_id = 12345;
```
**Expected Detection:**
- ✅ Sequential Scan detected
- ✅ Missing index on customer_id
- ✅ Recommendation: `CREATE INDEX idx_orders_customer_id ON test_orders(customer_id);`

### Query 3: Missing index on filter column
```sql
SELECT * FROM test_users WHERE department = 'Engineering';
```
**Expected Detection:**
- ✅ Sequential Scan detected
- ✅ Missing index on department
- ✅ Recommendation: `CREATE INDEX idx_users_department ON test_users(department);`

---

## ✅ 2. Inefficient Index Issues

### Query 1: Low selectivity index
```sql
SELECT * FROM test_customers WHERE status = 'active';
```
**Expected Detection:**
- ✅ Low selectivity warning (90% of rows are active)
- ✅ Index exists but not effective
- ✅ Severity: Medium

### Query 2: Wrong column order in composite index
```sql
SELECT * FROM test_customers WHERE country = 'USA' AND city = 'New York';
```
**Expected Detection:**
- ✅ Composite index has wrong column order
- ✅ Current: (city, country)
- ✅ Recommended: (country, city)

---

## ✅ 3. Poor Join Strategy Issues

### Query 1: Multiple joins without indexes
```sql
SELECT u.username, o.order_number, p.name, oi.quantity
FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_order_items oi ON o.id = oi.order_id
JOIN test_products p ON oi.product_id = p.id
WHERE u.status = 'active'
LIMIT 100;
```
**Expected Detection:**
- ✅ Nested Loop joins detected
- ✅ Missing indexes on join columns
- ✅ Severity: High
- ✅ Recommendations: Add indexes on user_id, order_id, product_id

### Query 2: Cross join (cartesian product)
```sql
SELECT * FROM test_products p, test_customers c
WHERE p.category = 'Electronics'
LIMIT 100;
```
**Expected Detection:**
- ✅ Cartesian product detected
- ✅ Missing proper join condition
- ✅ Severity: High

---

## ✅ 4. Full Table Scan Issues

### Query 1: LIKE with leading wildcard
```sql
SELECT * FROM test_logs WHERE message LIKE '%error%' LIMIT 100;
```
**Expected Detection:**
- ✅ Sequential scan on large table (500K rows)
- ✅ Leading wildcard prevents index usage
- ✅ Recommendation: Use full-text search

### Query 2: Range query without index
```sql
SELECT * FROM test_transactions WHERE amount > 1000 LIMIT 100;
```
**Expected Detection:**
- ✅ Sequential scan detected
- ✅ No index on amount column
- ✅ Recommendation: `CREATE INDEX idx_transactions_amount ON test_transactions(amount);`

### Query 3: Date range without index
```sql
SELECT * FROM test_orders 
WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31'
LIMIT 100;
```
**Expected Detection:**
- ✅ Sequential scan on date column
- ✅ No index on order_date
- ✅ Recommendation: `CREATE INDEX idx_orders_date ON test_orders(order_date);`

---

## ✅ 5. Suboptimal Query Pattern Issues

### Query 1: SELECT * anti-pattern
```sql
SELECT * FROM test_users WHERE id > 100 LIMIT 10;
```
**Expected Detection:**
- ✅ SELECT * detected
- ✅ Severity: Medium
- ✅ Recommendation: Specify only required columns
- ✅ Example: `SELECT id, username, email FROM test_users WHERE id > 100 LIMIT 10;`

### Query 2: Correlated subquery
```sql
SELECT u.username, u.email,
       (SELECT COUNT(*) FROM test_orders WHERE user_id = u.id) as order_count
FROM test_users u
LIMIT 100;
```
**Expected Detection:**
- ✅ Correlated subquery detected
- ✅ Executes for each row
- ✅ Severity: High
- ✅ Recommendation: Use JOIN instead

### Query 3: Function on indexed column
```sql
SELECT * FROM test_users WHERE UPPER(email) = 'TEST@EXAMPLE.COM';
```
**Expected Detection:**
- ✅ Function on column prevents index usage
- ✅ Severity: High
- ✅ Recommendation: Move function to comparison value or create functional index

### Query 4: Multiple OR conditions
```sql
SELECT * FROM test_orders 
WHERE status = 'pending' OR status = 'processing' 
   OR status = 'shipped' OR status = 'delivered'
LIMIT 100;
```
**Expected Detection:**
- ✅ Multiple OR conditions detected
- ✅ Recommendation: Use IN clause
- ✅ Better: `WHERE status IN ('pending', 'processing', 'shipped', 'delivered')`

---

## ✅ 6. ORM-Generated SQL Issues

### Query 1: Excessive JOINs
```sql
SELECT u.*, s.*, o.*, c.*
FROM test_users u
LEFT JOIN test_sessions s ON u.id = s.user_id
LEFT JOIN test_orders o ON u.id = o.user_id
LEFT JOIN test_customers c ON o.customer_id = c.id
LIMIT 10;
```
**Expected Detection:**
- ✅ Excessive JOINs detected (4+ tables)
- ✅ ORM eager loading pattern
- ✅ Severity: Medium
- ✅ Recommendation: Use lazy loading or reduce joins

### Query 2: SELECT * with multiple JOINs
```sql
SELECT * FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_customers c ON o.customer_id = c.id
LIMIT 100;
```
**Expected Detection:**
- ✅ SELECT * with JOINs detected
- ✅ Over-fetching data
- ✅ Recommendation: Specify needed columns from each table

---

## ✅ 7. High I/O Workload Issues

### Query 1: Large dataset with JSONB/TEXT columns
```sql
SELECT t.*, u.username, u.email
FROM test_transactions t
JOIN test_users u ON t.user_id = u.id
WHERE t.created_at > NOW() - INTERVAL '30 days'
ORDER BY t.amount DESC
LIMIT 100;
```
**Expected Detection:**
- ✅ High I/O workload (JSONB metadata column)
- ✅ Large TEXT columns (description)
- ✅ Recommendation: Add indexes, reduce selected columns

### Query 2: Query with large result set
```sql
SELECT * FROM test_logs 
WHERE log_level IN ('ERROR', 'CRITICAL', 'WARNING')
LIMIT 1000;
```
**Expected Detection:**
- ✅ Large result set without proper filtering
- ✅ Sequential scan on 500K rows
- ✅ Recommendation: Add pagination, reduce LIMIT

---

## ✅ 8. Inefficient Reporting Queries

### Query 1: Multiple aggregations without LIMIT
```sql
SELECT 
    DATE_TRUNC('day', order_date) as day,
    COUNT(*) as total_orders,
    SUM(total_amount) as revenue,
    AVG(total_amount) as avg_order,
    MAX(total_amount) as max_order,
    MIN(total_amount) as min_order
FROM test_orders
GROUP BY DATE_TRUNC('day', order_date)
ORDER BY day DESC;
```
**Expected Detection:**
- ✅ Multiple aggregations detected
- ✅ Missing LIMIT clause
- ✅ Recommendation: Add LIMIT for pagination

### Query 2: Complex analytics
```sql
SELECT 
    department,
    status,
    COUNT(*) as user_count,
    AVG(salary) as avg_salary,
    MAX(salary) as max_salary,
    MIN(salary) as min_salary
FROM test_users
GROUP BY department, status
ORDER BY user_count DESC;
```
**Expected Detection:**
- ✅ Complex aggregation query
- ✅ Multiple GROUP BY columns
- ✅ Recommendation: Add LIMIT, consider materialized view

---

## 🎯 Quick Test Workflow

1. **Connect to database** in AI SQL Optimizer
2. **Copy any query** from above
3. **Paste into optimizer**
4. **Click "Analyze Query"**
5. **Verify detection** matches expected results

---

## ✅ Verification Checklist

Test each category to ensure all 8 issue types are detected:

- [ ] Missing Index (3 queries)
- [ ] Inefficient Index (2 queries)
- [ ] Poor Join Strategy (2 queries)
- [ ] Full Table Scan (3 queries)
- [ ] Suboptimal Patterns (4 queries)
- [ ] ORM-Generated SQL (2 queries)
- [ ] High I/O Workload (2 queries)
- [ ] Inefficient Reporting (2 queries)

**Total: 20 verified working queries**

---

## 📊 Expected Results Summary

All queries should show:
- ✅ Issue type detected
- ✅ Severity level (Critical/High/Medium/Low)
- ✅ Clear description of the problem
- ✅ Actionable recommendations
- ✅ Example SQL for fixes (where applicable)

---

## 🎉 Success!

If you see issues detected for these queries, your test database is working perfectly and the AI SQL Optimizer is correctly identifying all optimization opportunities!
