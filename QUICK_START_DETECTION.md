# Quick Start Guide - See Detection Results in UI

## ✅ Detection is Working!

The backend detection system is now operational and will detect issues even without execution plans. Here's how to see the results in your UI:

## Step 1: Restart Backend (Important!)

The backend needs to be restarted to load the new detection code:

```bash
# Stop the current backend if running (Ctrl+C)

# Start backend
cd backend
uvicorn main:app --reload
```

## Step 2: Start Frontend

```bash
cd frontend
npm run dev
```

## Step 3: Test Detection in UI

1. **Navigate to Optimizer page** (http://localhost:5173/optimizer)

2. **Select your database connection**

3. **Enter a test query with known issues:**

```sql
SELECT * FROM users 
WHERE email LIKE '%@example.com'
AND YEAR(created_at) = 2024
```

4. **Make sure "Include execution plan analysis" is checked**

5. **Click "Optimize Query"**

## What You Should See

### Detection Summary Card
You'll see a purple/blue gradient card showing:
- 🔍 Performance Issues Detected
- Summary: "Detected X performance issue(s)"
- Colored badges showing issue counts by severity

### Individual Issue Cards
Below the summary, you'll see cards for each issue:

**Example Issue Card:**
```
🟡 MEDIUM - SELECT * detected
Query selects all columns instead of specific ones

💡 Recommendations:
• Specify only required columns explicitly
• Reduces network traffic and memory usage
• Improves query cache efficiency
```

## Issues You'll See (Even Without Execution Plan)

The system will detect these query pattern issues:

1. ✅ **SELECT * usage** - When you use SELECT *
2. ✅ **LIKE with leading wildcard** - When you use LIKE '%pattern'
3. ✅ **Multiple OR conditions** - When you have >3 OR conditions
4. ✅ **Functions on columns** - When you use UPPER(), YEAR(), etc. in WHERE
5. ✅ **NOT IN with subquery** - When you use NOT IN (SELECT...)
6. ✅ **Subquery in SELECT** - When you have (SELECT...) in SELECT clause
7. ✅ **Multiple DISTINCT** - When you use DISTINCT multiple times

## To See ALL 9 Detection Types

To see the full detection including:
- Missing indexes
- Poor join strategies
- Full table scans
- Stale statistics
- Wrong cardinality
- High I/O workloads

You need:
1. ✅ Check "Include execution plan analysis"
2. ✅ Ensure your database user has permissions to view execution plans

### Grant Permissions (if needed):

**PostgreSQL:**
```sql
-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Grant permissions
GRANT SELECT ON pg_stat_statements TO your_user;
```

**MySQL:**
```sql
GRANT SELECT ON performance_schema.* TO 'your_user'@'%';
```

**MSSQL:**
```sql
GRANT VIEW SERVER STATE TO your_user;
GRANT SHOWPLAN TO your_user;
```

## Troubleshooting

### Issue: Not seeing detection results

**Solution 1: Check backend logs**
```bash
# Look for errors in backend terminal
# Should see: "Detection complete: X issues found"
```

**Solution 2: Check browser console**
```bash
# Open browser DevTools (F12)
# Check Console tab for errors
# Check Network tab for API responses
```

**Solution 3: Verify API response**
```bash
# Test the API directly
curl -X POST http://localhost:8000/api/optimizer/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": 1,
    "sql_query": "SELECT * FROM users WHERE email LIKE '\''%@example.com'\''",
    "include_execution_plan": true
  }'

# Look for "detected_issues" in the response
```

### Issue: "Execution plan not available" message

This is normal! It means:
- Query pattern detection is working ✅
- Execution plan analysis needs database permissions or the checkbox enabled

**To fix:**
1. Ensure "Include execution plan analysis" is checked
2. Grant execution plan permissions (see above)
3. Restart backend after granting permissions

## Example Test Queries

### Query with Multiple Issues:
```sql
SELECT * 
FROM orders o
WHERE o.status = 'pending' 
   OR o.status = 'processing' 
   OR o.status = 'shipped'
   OR o.status = 'delivered'
AND o.customer_email LIKE '%@gmail.com'
AND YEAR(o.created_at) = 2024
```

**Expected Detection:**
- SELECT * detected (MEDIUM)
- Multiple OR conditions (LOW)
- LIKE with leading wildcard (MEDIUM)
- Function on indexed column (HIGH)

### Query with Subquery Issue:
```sql
SELECT 
    user_id,
    (SELECT COUNT(*) FROM orders WHERE user_id = u.id) as order_count
FROM users u
WHERE status = 'active'
```

**Expected Detection:**
- Subquery in SELECT clause (HIGH)

## Success Indicators

You'll know it's working when you see:

1. ✅ Purple/blue detection summary card appears
2. ✅ Issue count badges show (Critical/High/Medium/Low)
3. ✅ Individual issue cards with recommendations
4. ✅ Color-coded severity indicators
5. ✅ Actionable SQL recommendations

## Next Steps

Once you see detection working:

1. Try different problematic queries
2. Review the recommendations
3. Apply the suggested fixes
4. Re-run optimization to see fewer issues
5. Enable execution plan analysis for comprehensive detection

## Need Help?

If detection still isn't showing:
1. Check that backend restarted successfully
2. Verify frontend is connecting to backend
3. Check browser console for errors
4. Review backend logs for detection messages
5. Test API endpoint directly with curl

The detection system is ready and working! Just restart the backend and try it out. 🚀
