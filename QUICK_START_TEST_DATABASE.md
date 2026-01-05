# Quick Start: Test Database Setup

This guide will help you quickly set up the test database with comprehensive SQL optimization test data.

## Prerequisites

- Python 3.7 or higher
- Access to PostgreSQL database at 192.168.1.81:5432
- Database credentials (provided in the script)

## Installation

### Step 1: Install Dependencies

```bash
pip install -r test_database_requirements.txt
```

Or install manually:
```bash
pip install psycopg2-binary Faker
```

### Step 2: Verify Database Connection

Make sure you can connect to the PostgreSQL database:
```bash
psql -h 192.168.1.81 -p 5432 -U admin -d mydb
```

## Running the Script

### Option 1: Run Directly

```bash
python create_test_database.py
```

The script will:
1. Connect to the database
2. Drop existing test tables (if any)
3. Create 9 test tables
4. Populate with ~1.1 million records
5. Generate summary report

**Estimated Time**: 5-10 minutes depending on network speed

### Option 2: Run with Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r test_database_requirements.txt

# Run script
python create_test_database.py
```

## What Gets Created

### Tables (1,110,000 total rows)

1. **test_users** (50,000 rows) - Missing index on email
2. **test_customers** (20,000 rows) - Inefficient index, skewed data
3. **test_products** (10,000 rows) - No join indexes
4. **test_orders** (100,000 rows) - Full table scan scenarios
5. **test_order_items** (250,000 rows) - Complex join issues
6. **test_transactions** (150,000 rows) - High I/O workloads
7. **test_logs** (500,000 rows) - Inefficient reporting
8. **test_sessions** (30,000 rows) - ORM N+1 patterns

### Optimization Issues Demonstrated

✅ Missing indexes  
✅ Inefficient indexes  
✅ Poor join strategies  
✅ Full table scans  
✅ Suboptimal query patterns  
✅ Stale statistics  
✅ Wrong cardinality estimates  
✅ ORM-generated SQL  
✅ High I/O workloads  
✅ Inefficient reporting  

## Testing the Data

### 1. Connect in Application

Open AI SQL Optimizer Pro and add connection:
- **Name**: Test Database
- **Engine**: PostgreSQL
- **Host**: 192.168.1.81
- **Port**: 5432
- **Database**: mydb
- **Username**: admin
- **Password**: admin123

### 2. Test Queries

Try these queries in the Optimizer:

**Missing Index:**
```sql
SELECT * FROM test_users WHERE email = 'user@example.com';
```

**Full Table Scan:**
```sql
SELECT * FROM test_logs WHERE message LIKE '%error%';
```

**Poor Join Strategy:**
```sql
SELECT u.*, o.*, p.* 
FROM test_users u
JOIN test_orders o ON u.id = o.user_id
JOIN test_order_items oi ON o.id = oi.order_id
JOIN test_products p ON oi.product_id = p.id;
```

**Suboptimal Pattern:**
```sql
SELECT * FROM test_users WHERE UPPER(email) = 'TEST@EXAMPLE.COM';
```

**Inefficient Reporting:**
```sql
SELECT 
    DATE_TRUNC('day', created_at) as day,
    COUNT(*) as total_orders,
    SUM(total_amount) as revenue
FROM test_orders
GROUP BY DATE_TRUNC('day', created_at);
```

### 3. Verify Detection

The optimizer should detect and report:
- Issue type
- Severity level
- Affected objects
- Recommendations
- Performance metrics

## Troubleshooting

### Connection Failed

**Error**: `Connection failed: could not connect to server`

**Solution**:
- Verify database is running
- Check firewall settings
- Confirm host/port are correct
- Test with psql first

### Permission Denied

**Error**: `permission denied to create table`

**Solution**:
- Ensure user has CREATE TABLE privileges
- Grant permissions: `GRANT CREATE ON DATABASE mydb TO admin;`

### Out of Memory

**Error**: `out of memory`

**Solution**:
- Reduce batch sizes in the script
- Increase PostgreSQL memory settings
- Run on a machine with more RAM

### Slow Performance

**Issue**: Script takes too long

**Solution**:
- Check network latency to database
- Reduce row counts in populate methods
- Run during off-peak hours

## Customization

### Modify Row Counts

Edit `create_test_database.py`:

```python
def populate_all_tables(self):
    self.populate_users(50000)      # Change to 10000 for faster testing
    self.populate_customers(20000)   # Change to 5000
    self.populate_products(10000)    # Change to 2000
    # ... etc
```

### Change Database Connection

Edit `DB_CONFIG` in `create_test_database.py`:

```python
DB_CONFIG = {
    "dbname": "your_database",
    "user": "your_user",
    "password": "your_password",
    "host": "your_host",
    "port": 5432
}
```

## Cleanup

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

Or run:
```bash
psql -h 192.168.1.81 -p 5432 -U admin -d mydb -c "
DROP TABLE IF EXISTS test_order_items CASCADE;
DROP TABLE IF EXISTS test_orders CASCADE;
DROP TABLE IF EXISTS test_products CASCADE;
DROP TABLE IF EXISTS test_customers CASCADE;
DROP TABLE IF EXISTS test_users CASCADE;
DROP TABLE IF EXISTS test_transactions CASCADE;
DROP TABLE IF EXISTS test_logs CASCADE;
DROP TABLE IF EXISTS test_reports CASCADE;
DROP TABLE IF EXISTS test_sessions CASCADE;
"
```

## Next Steps

1. ✅ Run the script to create test data
2. ✅ Connect to database in the application
3. ✅ Test problematic queries
4. ✅ Verify issue detection
5. ✅ Apply recommended optimizations
6. ✅ Compare performance before/after

## Documentation

- **Full Documentation**: See `TEST_DATABASE_DOCUMENTATION.md`
- **Script Source**: See `create_test_database.py`
- **Query Examples**: See documentation for 20+ problematic queries

## Support

If you encounter issues:
1. Check PostgreSQL logs
2. Verify Python version (3.7+)
3. Ensure all dependencies are installed
4. Review error messages carefully
5. Check database permissions

## Performance Expectations

### Script Execution Time
- Small dataset (100K rows): 1-2 minutes
- Medium dataset (500K rows): 3-5 minutes
- Full dataset (1.1M rows): 5-10 minutes

### Query Performance (Before Optimization)
- Simple queries: 100-500ms
- Complex joins: 1-5 seconds
- Full table scans: 2-10 seconds
- Reporting queries: 5-20 seconds

### Query Performance (After Optimization)
- Simple queries: 1-10ms (100x faster)
- Complex joins: 50-200ms (20x faster)
- Optimized scans: 10-100ms (50x faster)
- Optimized reports: 100-500ms (50x faster)

---

**Ready to start?** Run `python create_test_database.py` now!
