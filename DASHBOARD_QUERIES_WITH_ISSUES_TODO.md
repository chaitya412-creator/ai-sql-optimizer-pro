# Dashboard: Display Queries with Detected Issues

## Task Overview
Add functionality to display the actual SQL queries that have detected performance issues on the dashboard, not just aggregated statistics.

## Implementation Steps

### Backend Changes
- [x] Add `QueryWithIssues` schema to `backend/app/models/schemas.py`
- [x] Add `IssueDetail` schema to `backend/app/models/schemas.py`
- [x] Add `/queries-with-issues` endpoint to `backend/app/api/dashboard.py`

### Frontend Changes
- [x] Add `QueryWithIssues` interface to `frontend/src/types/index.ts`
- [x] Add `IssueDetail` interface to `frontend/src/types/index.ts`
- [x] Add `getQueriesWithIssues()` function to `frontend/src/services/api.ts`
- [x] Update `frontend/src/pages/Dashboard.tsx` to display queries with issues

### Testing
- [x] Test new endpoint with existing data
- [x] Verify queries display correctly on dashboard
- [x] Test query expansion/collapse functionality
- [x] Verify error handling when no issues exist

## Current Status
✅ **IMPLEMENTATION COMPLETE!**

All changes have been successfully implemented. The dashboard now displays:
1. A new "Queries with Detected Issues" section
2. Each query shows connection name, issue counts by severity, and SQL preview
3. Expandable details showing full SQL and individual issues with recommendations
4. Color-coded severity indicators
5. Proper error handling when no issues exist
=======
