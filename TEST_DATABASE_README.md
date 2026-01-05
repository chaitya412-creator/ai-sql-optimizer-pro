# AI SQL Optimizer Pro - Test Database

Comprehensive test database for demonstrating all 9 SQL optimization issue types.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r test_database_requirements.txt

# Run the generator
python create_test_database.py
```

**Time Required**: 5-10 minutes  
**Data Created**: ~1.1 million records across 9 tables

## 📊 What's Included

### Test Tables

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

### Optimization Issues Covered

✅ **1. Missing Indexes** - Queries on unindexed columns  
✅ **2. Inefficient Indexes** - Low selectivity indexes  
✅ **3. Poor Join Strategies** - Nested loops on large datasets  
✅ **4. Full Table Scans** - Queries without proper indexes  
✅ **5. Suboptimal Patterns** - SELECT *, DISTINCT abuse, OR chains  
✅ **6. Stale Statistics** - Outdated table statistics  
✅ **7. Wrong Cardinality** - Skewed data distribution  
✅ **8. ORM-Generated SQL** - N+1 queries, excessive JOINs  
✅ **9. High I/O Workloads** - Low cache hit ratios  
✅ **10. Inefficient Reporting** - Missing pagination, window functions  

## 🎯 Example Queries

### Missing Index
```sql
SELECT * FROM test_users WHERE email = 'user@example.com';
```
**Expected**: Detection of missing index on email column

### Full Table Scan
```sql
SELECT * FROM test_logs WHERE message LIKE '%error%';
```
**Expected**: Detection of full table scan on 500K rows

### Poor Join Strategy
```sql
SELECT u.*, o.*, p.* 
FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_order_items oi ON o.id = oi.order_id
JOIN test_products p ON oi.product_id = p.id;
```
**Expected**: Detection of inefficient nested loop joins

### Suboptimal Pattern
```sql
SELECT * FROM test_users WHERE UPPER(email) = 'TEST@EXAMPLE.COM';
```
**Expected**: Detection of function on indexed column

### Inefficient Reporting
```sql
SELECT 
    DATE_TRUNC('day', created_at) as day,
    COUNT(*) as total_orders,
    SUM(total_amount) as revenue
FROM test_orders
GROUP BY DATE_TRUNC('day', created_at);
```
**Expected**: Detection of missing LIMIT clause

## 📁 Files

- **`create_test_database.py`** - Main script to generate test data
- **`TEST_DATABASE_DOCUMENTATION.md`** - Complete documentation
- **`QUICK_START_TEST_DATABASE.md`** - Quick start guide
- **`test_database_requirements.txt`** - Python dependencies

## 🔧 Database Connection

```
Host: 192.168.1.81
Port: 5432
Database: mydb
User: admin
Password: admin123
```

## 📈 Performance Expectations

### Before Optimization
- Simple queries: 100-500ms
- Complex joins: 1-5 seconds
- Full table scans: 2-10 seconds
- Reporting queries: 5-20 seconds

### After Optimization
- Simple queries: 1-10ms (**100x faster**)
- Complex joins: 50-200ms (**20x faster**)
- Optimized scans: 10-100ms (**50x faster**)
- Optimized reports: 100-500ms (**50x faster**)

## 🧪 Testing Workflow

1. **Run Script**: Generate test data
   ```bash
   python create_test_database.py
   ```

2. **Connect**: Add database connection in the application
   - Go to Connections page
   - Add PostgreSQL connection with above credentials

3. **Test Queries**: Run problematic queries through optimizer
   - Copy queries from documentation
   - Enable execution plan analysis
   - Review detected issues

4. **Apply Fixes**: Implement recommended optimizations
   - Create suggested indexes
   - Rewrite queries
   - Update statistics

5. **Verify**: Compare performance before/after
   - Check execution times
   - Review query plans
   - Validate improvements

## 🛠️ Recommended Index Fixes

```sql
-- Fix missing indexes
CREATE INDEX idx_users_email ON test_users(email);
CREATE INDEX idx_orders_customer_id ON test_orders(customer_id);
CREATE INDEX idx_orders_user_id ON test_orders(user_id);
CREATE INDEX idx_order_items_order_id ON test_order_items(order_id);
CREATE INDEX idx_order_items_product_id ON test_order_items(product_id);
CREATE INDEX idx_transactions_user_id ON test_transactions(user_id);
CREATE INDEX idx_sessions_user_id ON test_sessions(user_id);

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

## 🧹 Cleanup

To remove all test data:

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

## 📚 Documentation

- **Quick Start**: `QUICK_START_TEST_DATABASE.md`
- **Full Documentation**: `TEST_DATABASE_DOCUMENTATION.md`
- **20+ Query Examples**: See documentation for complete list

## ⚠️ Troubleshooting

### Connection Failed
- Verify database is running
- Check firewall settings
- Test with psql first

### Permission Denied
- Ensure user has CREATE TABLE privileges
- Grant: `GRANT CREATE ON DATABASE mydb TO admin;`

### Slow Performance
- Check network latency
- Reduce row counts for faster testing
- Run during off-peak hours

## 🎓 Learning Objectives

After using this test database, you will understand:

1. How to identify missing indexes
2. When indexes are inefficient
3. How join strategies affect performance
4. Why full table scans are problematic
5. Common SQL anti-patterns to avoid
6. Impact of stale statistics
7. How data distribution affects queries
8. ORM performance pitfalls
9. I/O optimization techniques
10. Efficient reporting query patterns

## 🤝 Contributing

To add more test scenarios:
1. Edit `create_test_database.py`
2. Add new tables or queries
3. Update documentation
4. Test thoroughly

## 📝 License

Part of AI SQL Optimizer Pro project.

---

**Ready to test?** Run `python create_test_database.py` now!

For detailed instructions, see `QUICK_START_TEST_DATABASE.md`
