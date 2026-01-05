# 404 Error Fix - Missing API Endpoints

## Problem
The frontend was calling API endpoints that didn't exist in the backend, resulting in "Request failed with status code 404" errors.

## Missing Endpoints Identified

### Dashboard API (`/api/dashboard`)
1. ❌ `GET /top-queries` - Frontend expected but backend didn't have it
2. ❌ `GET /performance-trends` - Frontend expected but backend didn't have it

### Monitoring API (`/api/monitoring`)
3. ❌ `POST /start` - Frontend expected but backend didn't have it
4. ❌ `POST /stop` - Frontend expected but backend didn't have it

## Solution Implemented

### 1. Added Response Schemas (`backend/app/models/schemas.py`)
```python
class TopQuery(BaseModel):
    """Top query for dashboard"""
    id: int
    connection_name: str
    sql_text: str
    avg_execution_time: float
    total_execution_time: float
    calls: int
    severity: str  # 'low', 'medium', 'high'

class PerformanceTrend(BaseModel):
    """Performance trend data point"""
    timestamp: str
    avg_time: float
    slow_queries: int
    total_queries: int
```

### 2. Dashboard API Endpoints (`backend/app/api/dashboard.py`)

#### `GET /api/dashboard/top-queries`
- Returns top N queries ordered by total execution time
- Includes connection name and severity classification
- Supports `limit` query parameter (default: 10)
- Severity levels:
  - **High**: avg execution time > 5 seconds
  - **Medium**: avg execution time > 1 second
  - **Low**: avg execution time ≤ 1 second

#### `GET /api/dashboard/performance-trends`
- Returns time-series performance data
- Groups queries by hour
- Supports `hours` query parameter (default: 24)
- Returns metrics:
  - `timestamp`: ISO format timestamp
  - `avg_time`: Average execution time for the hour
  - `slow_queries`: Count of queries > 1 second
  - `total_queries`: Total queries in that hour

### 3. Monitoring API Endpoints (`backend/app/api/monitoring.py`)

#### `POST /api/monitoring/start`
- Starts the monitoring agent
- Checks if agent is already running
- Returns success message
- Logs action for audit trail

#### `POST /api/monitoring/stop`
- Stops the monitoring agent
- Checks if agent is running before stopping
- Returns success message
- Logs action for audit trail

## Files Modified

1. **backend/app/models/schemas.py**
   - Added `TopQuery` schema
   - Added `PerformanceTrend` schema

2. **backend/app/api/dashboard.py**
   - Added `get_top_queries()` endpoint
   - Added `get_performance_trends()` endpoint
   - Added imports for `List`, `datetime`, `timedelta`

3. **backend/app/api/monitoring.py**
   - Added `start_monitoring()` endpoint
   - Added `stop_monitoring()` endpoint

## API Endpoint Summary

### Dashboard Endpoints
- ✅ `GET /api/dashboard/stats` - Get overall statistics
- ✅ `GET /api/dashboard/top-queries` - Get top slow queries (NEW)
- ✅ `GET /api/dashboard/performance-trends` - Get time-series data (NEW)
- ✅ `GET /api/dashboard/recent-activity` - Get recent optimizations

### Monitoring Endpoints
- ✅ `GET /api/monitoring/status` - Get monitoring status
- ✅ `POST /api/monitoring/start` - Start monitoring (NEW)
- ✅ `POST /api/monitoring/stop` - Stop monitoring (NEW)
- ✅ `POST /api/monitoring/trigger` - Trigger manual monitoring cycle
- ✅ `GET /api/monitoring/queries` - Get discovered queries
- ✅ `GET /api/monitoring/queries/{id}` - Get query details

## Testing

To test the fix:

1. **Start the backend:**
   ```bash
   cd backend
   python main.py
   ```

2. **Test endpoints manually:**
   ```bash
   # Test top queries
   curl http://localhost:8000/api/dashboard/top-queries?limit=5
   
   # Test performance trends
   curl http://localhost:8000/api/dashboard/performance-trends?hours=12
   
   # Test monitoring start
   curl -X POST http://localhost:8000/api/monitoring/start
   
   # Test monitoring stop
   curl -X POST http://localhost:8000/api/monitoring/stop
   ```

3. **Test with frontend:**
   - Navigate to Dashboard page - should load without 404 errors
   - Navigate to Monitoring page - start/stop buttons should work
   - Check browser console for any remaining errors

## Expected Behavior

### Before Fix
- Frontend calls to `/api/dashboard/top-queries` → 404 Error
- Frontend calls to `/api/dashboard/performance-trends` → 404 Error
- Frontend calls to `/api/monitoring/start` → 404 Error
- Frontend calls to `/api/monitoring/stop` → 404 Error

### After Fix
- All endpoints return proper responses
- Dashboard displays top queries and performance trends
- Monitoring controls (start/stop) work correctly
- No 404 errors in browser console

## Notes

- The performance trends endpoint returns empty data points if no queries exist in the time range
- Severity classification is based on average execution time thresholds
- Monitoring start/stop endpoints check agent state before performing actions
- All endpoints include proper error handling and logging

## Related Files
- Frontend API client: `frontend/src/services/api.ts`
- Frontend types: `frontend/src/types/index.ts`
- Backend main: `backend/main.py`
