# 422 Error Fix - Field Name Mismatches

## Problem
The application was experiencing 422 (Unprocessable Entity) errors due to field name mismatches between the frontend TypeScript types and backend Pydantic schemas.

## Root Cause
The frontend was sending API requests with field names that didn't match what the backend expected, causing Pydantic validation to fail with 422 errors.

## Issues Identified

### 1. Connection API Mismatches
**Frontend (before fix):**
- `db_type` → Backend expected: `engine`
- `is_active` → Backend returned: `monitoring_enabled`
- Missing fields: `ssl_enabled`, `last_monitored_at`

### 2. Optimizer API Mismatches
**Frontend (before fix):**
- `analyze` → Backend expected: `include_execution_plan`
- `original_query` → Backend returned: `original_sql`
- `optimized_query` → Backend returned: `optimized_sql`
- `estimated_improvement` → Backend returned: `estimated_improvement_pct`
- `recommendations` was array → Backend returns: string

## Files Modified

### 1. `frontend/src/types/index.ts`
**Changes:**
- Updated `Connection` interface:
  - `db_type` → `engine`
  - `is_active` → `monitoring_enabled`
  - Added: `ssl_enabled`, `last_monitored_at`
  
- Updated `ConnectionCreate` interface:
  - `db_type` → `engine`
  - Added: `ssl_enabled`, `monitoring_enabled` (optional)

- Updated `OptimizationRequest` interface:
  - `analyze` → `include_execution_plan`
  - Added: `query_id` (optional)

- Updated `OptimizationResult` interface:
  - `original_query` → `original_sql`
  - `optimized_query` → `optimized_sql`
  - `estimated_improvement` → `estimated_improvement_pct`
  - `recommendations` type: `string[]` → `string`
  - Added: `id`, `query_id`, `connection_id`, `status`, `created_at`, `applied_at`, `validated_at`

### 2. `frontend/src/pages/Connections.tsx`
**Changes:**
- Updated form state to use `engine` instead of `db_type`
- Added `ssl_enabled` and `monitoring_enabled` to form data
- Renamed `getDbTypeColor()` → `getEngineColor()`
- Updated all references from `conn.db_type` → `conn.engine`
- Updated status indicator from `conn.is_active` → `conn.monitoring_enabled`
- Changed label from "Database Type" to "Database Engine"

### 3. `frontend/src/pages/Optimizer.tsx`
**Changes:**
- Renamed state variable: `analyze` → `includeExecutionPlan`
- Updated API call to use `include_execution_plan` instead of `analyze`
- Updated connection filter from `c.is_active` → `c.monitoring_enabled`
- Updated display references:
  - `result.original_query` → `result.original_sql`
  - `result.optimized_query` → `result.optimized_sql`
  - `result.estimated_improvement` → `result.estimated_improvement_pct`
- Changed recommendations rendering from array mapping to string display
- Updated connection selector to show `conn.engine` instead of `conn.db_type`
- Added `PlanIssue` type import for proper TypeScript typing

## Backend Schema Reference

The backend uses these Pydantic schemas (from `backend/app/models/schemas.py`):

```python
class ConnectionCreate(BaseModel):
    name: str
    engine: DatabaseEngine  # "postgresql" | "mysql" | "oracle" | "mssql"
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_enabled: bool = False
    monitoring_enabled: bool = True

class OptimizationRequest(BaseModel):
    query_id: Optional[int] = None
    connection_id: int
    sql_query: str
    include_execution_plan: bool = True
```

## Testing Recommendations

1. **Test Connection Creation:**
   - Create a new database connection
   - Verify all fields are sent correctly
   - Check that the connection is saved successfully

2. **Test Query Optimization:**
   - Select a connection
   - Enter a SQL query
   - Toggle "Include execution plan analysis"
   - Verify optimization results display correctly

3. **Test Connection Display:**
   - Verify connection cards show correct engine type
   - Check monitoring status indicator works
   - Test connection test functionality

## Result

All 422 validation errors should now be resolved. The frontend now sends API requests with field names that exactly match the backend Pydantic schema expectations.
