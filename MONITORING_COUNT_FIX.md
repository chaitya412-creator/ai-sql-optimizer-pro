# Monitoring Page Count Inconsistency Fix

## Issue
The Monitoring page displayed inconsistent query counts:
- **Top Card**: "Queries Discovered: 103"
- **Bottom Section**: "Discovered Queries: 100 queries found"

## Root Cause
The inconsistency was caused by two different data sources:

1. **Top Card (103)**: Used `status?.queries_discovered` from `/monitoring/status` endpoint
   - Backend calculates: `db.query(Query).count()` - returns ALL queries in database

2. **Bottom Section (100)**: Used `queries.length` from the queries array
   - Backend endpoint has default `limit: int = 100` parameter
   - Only returns first 100 queries even though 103 exist in database

## Solution
Updated `frontend/src/pages/Monitoring.tsx` to use the same data source for both displays.

### Changes Made

**File: `frontend/src/pages/Monitoring.tsx`**

1. **Line 177** - Fixed query count display:
   ```typescript
   // Before:
   {queries.length} queries found
   
   // After:
   {status?.queries_discovered || 0} queries found
   ```

2. **Line 189** - Fixed TypeScript error (bonus fix):
   ```typescript
   // Before:
   {conn.name} ({conn.db_type})
   
   // After:
   {conn.name} ({conn.engine})
   ```

## Result
Both the top card and bottom section now consistently display the total count of discovered queries (103), while the table still shows the limited results (100 queries) for performance reasons.

### Before:
- Top: "Queries Discovered: 103"
- Bottom: "100 queries found"

### After:
- Top: "Queries Discovered: 103"
- Bottom: "103 queries found"

## Technical Details
- The status endpoint provides the accurate total count from the database
- The queries endpoint returns a paginated/limited subset for display performance
- Users now see the correct total count while viewing a limited set in the table

## Testing
To verify the fix:
1. Navigate to the Monitoring page
2. Check that both the top card and bottom section show the same total count
3. Verify the table displays the limited results correctly

## Files Modified
- `frontend/src/pages/Monitoring.tsx`

## Date
December 16, 2025
