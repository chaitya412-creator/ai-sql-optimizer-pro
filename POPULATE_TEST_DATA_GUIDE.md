# Comprehensive Test Data Population Guide

This guide will help you populate your PostgreSQL database with comprehensive test data showing:
- **17 optimizations** with detected issues
- **All 10 issue types** represented
- **20 total issues** across various severity levels

## Prerequisites

1. PostgreSQL database running at `192.168.1.81:5432`
2. Database name: `mydb`
3. Credentials: `admin` / `admin123`
4. Python environment with required dependencies installed

## Quick Start

### Step 1: Install Dependencies (if needed)

```bash
pip install sqlalchemy psycopg2-binary
```

### Step 2: Run the Population Script

```bash
python populate_comprehensive_test_data.py
```

The script will:
1. Connect to your PostgreSQL database
2. Clear any existing test data
3. Create 17 optimizations with detected issues
4. Populate all 10 issue types with 20 total issues

### Step 3: Verify the Data

```bash
python verify_comprehensive_data.py
```

This will verify that:
- ✅ 17 optimizations were created
- ✅ All 10 issue types are present
- ✅ 20 total issues exist with proper severity distribution

### Step 4: View in Dashboard

1. Restart your backend server (if running)
2. Open your browser and navigate to the dashboard
3. You should now see:
   - **Performance Issues Detected**: 20 issues across 17 optimized queries
   - **Issues by Type**: All 10 issue types with their counts
   - **Queries with Detected Issues**: 17 queries listed

## Expected Results

### Issue Type Distribution

| Issue Type | Count |
|------------|-------|
| Missing Index | 3 |
| Inefficient Index | 2 |
| Poor Join Strategy | 2 |
| Full Table Scan | 3 |
| Suboptimal Pattern | 3 |
| Stale Statistics | 1 |
| Wrong Cardinality | 2 |
| ORM Generated | 2 |
| High IO Workload | 1 |
| Inefficient Reporting | 1 |
| **Total** | **20** |

### Severity Distribution

| Severity | Count |
|----------|-------|
| Critical | 4 |
| High | 7 |
| Medium | 8 |
| Low | 1 |
| **Total** | **20** |

## Troubleshooting

### Connection Error

If you get a connection error:
```
❌ Failed to connect to database: ...
```

**Solution**: Verify your database is running and accessible:
```bash
psql -h 192.168.1.81 -p 5432 -U admin -d mydb
```

### Import Error

If you get an import error:
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Solution**: Install the PostgreSQL adapter:
```bash
pip install psycopg2-binary
```

### Permission Error

If you get a permission error:
```
❌ Error: permission denied for table optimizations
```

**Solution**: Ensure the `admin` user has proper permissions:
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
```

## What Gets Created

### 17 Optimizations

Each optimization includes:
- Original SQL query with performance issues
- Optimized SQL query with improvements
- Detailed explanation of changes
- Specific recommendations
- Estimated improvement percentage
- Detected issues in JSON format

### Sample Optimization

```json
{
  "id": 1,
  "original_sql": "SELECT * FROM users WHERE email = 'user@example.com'",
  "optimized_sql": "SELECT id, username, email FROM users WHERE email = 'user@example.com'",
  "explanation": "Added index on email column and specified required columns",
  "recommendations": "CREATE INDEX idx_users_email ON users(email);",
  "estimated_improvement_pct": 85.5,
  "detected_issues": {
    "issues": [
      {
        "issue_type": "missing_index",
        "severity": "critical",
        "title": "Missing index on frequently queried column",
        "description": "Sequential scan on large table without proper indexing",
        "affected_objects": ["users.email"],
        "recommendations": ["CREATE INDEX idx_users_email ON users(email);"]
      }
    ],
    "total_issues": 2,
    "critical_issues": 2
  }
}
```

## Cleaning Up

To remove all test data and start fresh:

```bash
python populate_comprehensive_test_data.py
```

The script automatically clears existing data before creating new test data.

## Next Steps

After populating the data:

1. **Explore the Dashboard**: Navigate through different sections to see all issue types
2. **Test Filtering**: Try filtering by severity or issue type
3. **View Details**: Click on individual queries to see detailed issue information
4. **Test Optimization**: Try the "Optimize Queries" button to see the optimization flow

## Support

If you encounter any issues:
1. Check the error messages in the console
2. Verify database connectivity
3. Ensure all dependencies are installed
4. Review the verification script output

---

**Created**: 2024
**Database**: PostgreSQL 
**Connection**: 192.168.1.81:5432/mydb
