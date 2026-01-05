# Complete Setup Instructions for Test Data Population

## Overview
This guide provides step-by-step instructions to populate your PostgreSQL database with comprehensive test data showing:
- **17 optimizations** with detected issues
- **All 10 issue types** represented  
- **20 total issues** across various severity levels

## Prerequisites

✅ PostgreSQL database running at `192.168.1.81:5432`  
✅ Database name: `mydb`  
✅ Credentials: `admin` / `admin123`  
✅ Python 3.11+ installed  
✅ Required Python packages installed

## Step-by-Step Instructions

### Step 1: Install Required Dependencies

```bash
pip install sqlalchemy psycopg2-binary
```

### Step 2: Initialize Database Schema

Run this command to create all required tables in your PostgreSQL database:

```bash
python init_postgres_schema.py
```

**Expected Output:**
```
================================================================================
POSTGRESQL DATABASE SCHEMA INITIALIZATION
================================================================================

Database: 192.168.1.81:5432/mydb
User: admin
================================================================================

✓ Connected to PostgreSQL
  Version: PostgreSQL 15.x

Creating database tables...

✓ Created 4 tables:
  • connections
  • optimizations
  • queries
  • query_issues

================================================================================
✅ SCHEMA INITIALIZATION COMPLETE
================================================================================
```

### Step 3: Populate Test Data

Run this command to populate the database with comprehensive test data:

```bash
python populate_test_data_auto.py
```

**Expected Output:**
```
================================================================================
COMPREHENSIVE TEST DATA POPULATION (AUTO)
================================================================================

Database: PostgreSQL at 192.168.1.81:5432
Database Name: mydb
User: admin

Populating: 17 optimizations, 10 issue types, 20 total issues
================================================================================

✓ Connected to PostgreSQL database
✓ Using connection: Test PostgreSQL (ID: 1)

Clearing existing test data...
✓ Cleared 0 existing optimizations

Creating 17 optimizations...

✓ # 1: missing_index              (critical) - 2 issue(s)
✓ # 2: missing_index              (high    ) - 1 issue(s)
✓ # 3: inefficient_index          (high    ) - 1 issue(s)
✓ # 4: inefficient_index          (medium  ) - 1 issue(s)
✓ # 5: poor_join_strategy         (critical) - 1 issue(s)
✓ # 6: poor_join_strategy         (high    ) - 1 issue(s)
✓ # 7: full_table_scan            (critical) - 2 issue(s)
✓ # 8: full_table_scan            (high    ) - 1 issue(s)
✓ # 9: suboptimal_pattern         (medium  ) - 2 issue(s)
✓ #10: suboptimal_pattern         (medium  ) - 1 issue(s)
✓ #11: suboptimal_pattern         (low     ) - 1 issue(s)
✓ #12: stale_statistics           (medium  ) - 1 issue(s)
✓ #13: wrong_cardinality          (high    ) - 1 issue(s)
✓ #14: wrong_cardinality          (medium  ) - 1 issue(s)
✓ #15: orm_generated              (critical) - 1 issue(s)
✓ #16: orm_generated              (high    ) - 1 issue(s)
✓ #17: high_io_workload           (high    ) - 1 issue(s)

================================================================================
SUMMARY
================================================================================

✓ Created 17 optimizations

Issue Types (10/10):
  • Effi Client Index                     : 2
  • Full Table Scan                       : 3
  • High Io Workload                      : 1
  • Inefficient Reporting                 : 1
  • Missing Index                         : 3
  • Orm Generated                         : 2
  • Poor Join Strategy                    : 2
  • Stale Statistics                      : 1
  • Suboptimal Pattern                    : 3
  • Wrong Cardinality                     : 2

Severity Distribution:
  • Critical    : 4
  • High        : 7
  • Medium      : 8
  • Low         : 1

✓ Total issues: 20

================================================================================
✅ SUCCESS - Data populated!
================================================================================
```

### Step 4: Verify the Data

Run this command to verify all data was created correctly:

```bash
python verify_comprehensive_data.py
```

**Expected Output:**
```
================================================================================
VERIFICATION REPORT
================================================================================

✓ Total optimizations with detected issues: 17

Optimization Details:
--------------------------------------------------------------------------------
 1. ID   1: 2 issue(s) - missing_index
 2. ID   2: 1 issue(s) - missing_index
 3. ID   3: 1 issue(s) - inefficient_index
 ... (continues for all 17)

================================================================================
ISSUE TYPE DISTRIBUTION
================================================================================

Issue types found: 10/10
  ✓ Missing Index                        :  3 issue(s)
  ✓ Inefficient Index                    :  2 issue(s)
  ✓ Poor Join Strategy                   :  2 issue(s)
  ✓ Full Table Scan                      :  3 issue(s)
  ✓ Suboptimal Pattern                   :  3 issue(s)
  ✓ Stale Statistics                     :  1 issue(s)
  ✓ Wrong Cardinality                    :  2 issue(s)
  ✓ Orm Generated                        :  2 issue(s)
  ✓ High Io Workload                     :  1 issue(s)
  ✓ Inefficient Reporting                :  1 issue(s)

================================================================================
SEVERITY DISTRIBUTION
================================================================================

  • Critical    :  4 issues
  • High        :  7 issues
  • Medium      :  8 issues
  • Low         :  1 issues

✓ Total issues: 20

================================================================================
VERIFICATION SUMMARY
================================================================================

✅ Optimizations        : 17/17
✅ Issue Types          : 10/10
✅ Total Issues         : 20/20

✅ All verification checks passed!

Your dashboard should now display:
  • 17 optimizations with detected issues
  • All 10 issue types represented
  • 20 total issues across various severity levels
```

### Step 5: View in Dashboard

1. **Restart your backend server** (if running):
   ```bash
   docker-compose restart backend
   ```

2. **Open your browser** and navigate to the dashboard

3. **Verify the display** shows:
   - Performance Issues Detected: **20 issues** across **17 optimized queries**
   - Issues by Type: All **10 issue types** with their counts
   - Queries with Detected Issues: **17 queries** listed

## Expected Dashboard Display

### Performance Issues Detected Section
```
Found 20 performance issues across 17 optimized queries

4 Critical    7 High    8 Medium    1 Low
```

### Issues by Type Section
```
Missing Index              3    (1 Critical, 1 High, 1 Medium)
Inefficient Index          2    (1 High, 1 Medium)
Poor Join Strategy         2    (1 Critical, 1 High)
Full Table Scan            3    (2 Critical, 1 High)
Suboptimal Pattern         3    (2 Medium, 1 Low)
Stale Statistics           1    (1 Medium)
Wrong Cardinality          2    (1 High, 1 Medium)
ORM Generated              2    (1 Critical, 1 High)
High IO Workload           1    (1 High)
Inefficient Reporting      1    (1 Medium)
```

### Queries with Detected Issues Section
Lists all 17 queries with their issue counts and severity badges.

## Troubleshooting

### Issue: "relation 'connections' does not exist"

**Solution:** Run Step 2 first to initialize the database schema:
```bash
python init_postgres_schema.py
```

### Issue: "Connection refused"

**Solution:** Verify PostgreSQL is running and accessible:
```bash
psql -h 192.168.1.81 -p 5432 -U admin -d mydb
```

### Issue: "ModuleNotFoundError: No module named 'psycopg2'"

**Solution:** Install the PostgreSQL adapter:
```bash
pip install psycopg2-binary
```

### Issue: "Permission denied"

**Solution:** Ensure the admin user has proper permissions:
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;
```

## Files Created

1. **init_postgres_schema.py** - Initializes database schema
2. **populate_test_data_auto.py** - Populates test data (automatic, no prompts)
3. **populate_comprehensive_test_data.py** - Populates test data (with prompts)
4. **verify_comprehensive_data.py** - Verifies data was created correctly
5. **POPULATE_TEST_DATA_GUIDE.md** - Detailed guide
6. **COMPLETE_SETUP_INSTRUCTIONS.md** - This file

## Quick Command Reference

```bash
# Full setup sequence
python init_postgres_schema.py
python populate_test_data_auto.py
python verify_comprehensive_data.py

# Clean and repopulate
python populate_test_data_auto.py  # Automatically clears old data

# Verify only
python verify_comprehensive_data.py
```

## Support

If you encounter any issues:
1. Check error messages in the console output
2. Verify database connectivity with `psql`
3. Ensure all dependencies are installed
4. Review the verification script output
5. Check backend server logs for API errors

---

**Last Updated:** 2024  
**Database:** PostgreSQL at 192.168.1.81:5432/mydb  
**Target:** 17 optimizations, 10 issue types, 20 total issues
