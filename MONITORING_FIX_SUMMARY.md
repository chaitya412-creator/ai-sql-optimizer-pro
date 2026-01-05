# Monitoring Page Fix - Complete Summary

## Problem
The monitoring page was not displaying due to data structure mismatches between the frontend and backend APIs.

## Root Cause Analysis
The frontend TypeScript types expected different field names than what the backend Pydantic schemas were providing:

### 1. MonitoringStatus Mismatch
- Frontend expected: `is_running`, `last_poll_time`, `next_poll_time`, `queries_discovered`, `active_connections`
- Backend provided: `enabled`, `running`, `last_run`, `next_run`, `queries_discovered_last_run`
- Missing: `active_connections` field

### 2. QueryResponse Mismatch
- Frontend expected: `avg_execution_time`, `total_execution_time`, `last_seen`
- Backend provided: `avg_exec_time_ms`, `total_exec_time_ms`, `last_seen_at`
- Database model used: `avg_exec_time_ms`, `total_exec_time_ms`, `last_seen_at`

### 3. ConnectionResponse Mismatch
- Frontend sometimes referenced: `db_type`
- Backend provided: `engine`

## Solution Implemented

### 1. Updated Backend Schemas (`backend/app/models/schemas.py`)

#### MonitoringStatus Schema
```python
class MonitoringStatus(BaseModel):
    """Monitoring agent status"""
    is_running: bool                          # Changed from 'running'
    last_poll_time: Optional[datetime] = None # Changed from 'last_run'
    next_poll_time: Optional[datetime] = None # Changed from 'next_run'
    interval_minutes: int
    queries_discovered: int                   # Changed from 'queries_discovered_last_run'
    active_connections: int                   # NEW FIELD
```

#### QueryResponse Schema
```python
class QueryResponse(BaseModel):
    """Query response"""
    id: int
    connection_id: int
    query_hash: str
    sql_text: str
    avg_execution_time: float      # Changed from 'avg_exec_time_ms'
    total_execution_time: float    # Changed from 'total_exec_time_ms'
    calls: int
    rows_returned: Optional[int] = None
    buffer_hits: Optional[int] = None
    buffer_reads: Optional[int] = None
    discovered_at: datetime
    last_seen: datetime            # Changed from 'last_seen_at'
    optimized: bool
    
    @classmethod
    def from_orm(cls, obj):
        """Custom ORM mapping to handle field name differences"""
        return cls(
            id=obj.id,
            connection_id=obj.connection_id,
            query_hash=obj.query_hash,
            sql_text=obj.sql_text,
            avg_execution_time=obj.avg_exec_time_ms,      # Map from DB field
            total_execution_time=obj.total_exec_time_ms,  # Map from DB field
            calls=obj.calls,
            rows_returned=obj.rows_returned,
            buffer_hits=obj.buffer_hits,
            buffer_reads=obj.buffer_reads,
            discovered_at=obj.discovered_at,
            last_seen=obj.last_seen_at,                   # Map from DB field
            optimized=obj.optimized
        )
```

#### ConnectionResponse Schema
```python
class ConnectionResponse(BaseModel):
    """Connection response"""
    # ... existing fields ...
    
    @property
    def db_type(self) -> str:
        """Alias for engine field to match frontend expectations"""
        return self.engine
```

### 2. Updated Monitoring Agent (`backend/app/core/monitoring_agent.py`)

```python
def get_status(self) -> Dict[str, Any]:
    """Get monitoring agent status"""
    next_run = None
    if self.scheduler.running:
        jobs = self.scheduler.get_jobs()
        if jobs:
            next_run = jobs[0].next_run_time
    
    # Get active connections count
    db = SessionLocal()
    try:
        active_connections = db.query(Connection).filter(
            Connection.monitoring_enabled == True
        ).count()
    finally:
        db.close()
    
    return {
        "is_running": self.is_running(),              # Changed from 'running'
        "last_poll_time": self.last_run,              # Changed from 'last_run'
        "next_poll_time": next_run,                   # Changed from 'next_run'
        "interval_minutes": settings.MONITORING_INTERVAL_MINUTES,
        "queries_discovered": self.queries_discovered_last_run,  # Changed field name
        "active_connections": active_connections      # NEW FIELD
    }
```

### 3. Updated Monitoring API (`backend/app/api/monitoring.py`)

```python
@router.get("/status", response_model=MonitoringStatus)
async def get_monitoring_status():
    """Get monitoring agent status"""
    try:
        if not monitoring_agent:
            return MonitoringStatus(
                is_running=False,              # Updated field names
                last_poll_time=None,
                next_poll_time=None,
                interval_minutes=0,
                queries_discovered=0,
                active_connections=0           # NEW FIELD
            )
        
        status_data = monitoring_agent.get_status()
        return MonitoringStatus(**status_data)
    # ... error handling ...
```

## Files Modified

1. ✅ `backend/app/models/schemas.py` - Updated schema definitions
2. ✅ `backend/app/core/monitoring_agent.py` - Updated get_status() method
3. ✅ `backend/app/api/monitoring.py` - Updated default status response
4. ✅ `MONITORING_PAGE_FIX.md` - Tracking document
5. ✅ `test_monitoring_fix.py` - Test script for verification

## Testing

### Manual Testing Steps

1. **Start the backend:**
   ```bash
   cd backend
   python main.py
   ```

2. **Run the test script:**
   ```bash
   python test_monitoring_fix.py
   ```

3. **Test in browser:**
   - Navigate to `http://localhost:3000/monitoring`
   - Verify the page loads without errors
   - Check that status cards display correctly
   - Verify queries table renders properly

### Expected Results

- ✅ Monitoring status endpoint returns correct field names
- ✅ Queries endpoint returns data with correct field names
- ✅ Frontend can parse the API responses without errors
- ✅ Monitoring page displays all components correctly
- ✅ No console errors in browser developer tools

## Benefits

1. **Data Consistency**: Frontend and backend now use consistent field names
2. **Type Safety**: Proper mapping between database models and API responses
3. **Maintainability**: Clear separation between database schema and API contract
4. **Backward Compatibility**: Custom `from_orm` method handles field mapping transparently

## Next Steps

1. Test the monitoring page in the browser
2. Verify all monitoring features work correctly:
   - Start/Stop monitoring
   - Trigger manual monitoring
   - Filter queries by connection
   - View query details
3. Consider adding similar field mapping for other endpoints if needed

## Notes

- The database model (`Query`) still uses the original field names (`avg_exec_time_ms`, etc.)
- The Pydantic schema handles the mapping transparently via `from_orm()`
- This approach maintains database schema stability while providing a clean API interface
- No database migrations are required
