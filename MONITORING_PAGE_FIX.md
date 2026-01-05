# Monitoring Page Fix - Data Structure Alignment

## Issue
The monitoring page is not showing due to data structure mismatches between frontend and backend.

## Root Cause
- Backend schemas use different field names than frontend expects
- Missing fields in backend responses
- Type mismatches between frontend and backend

## Fix Plan

### 1. Update Backend Schemas (backend/app/models/schemas.py)
- [x] Identify mismatches
- [x] Update MonitoringStatus schema
- [x] Update QueryResponse schema with custom from_orm mapping
- [x] Update ConnectionResponse schema with db_type property

### 2. Update Backend API (backend/app/api/monitoring.py)
- [x] Update get_monitoring_status() to return correct field names
- [x] Verify all endpoints return correct structure

### 3. Update Monitoring Agent (backend/app/core/monitoring_agent.py)
- [x] Update get_status() method to return correct field names
- [x] Add active_connections count to status

### 4. Testing
- [ ] Test monitoring status endpoint
- [ ] Test queries endpoint
- [ ] Test monitoring page in browser

## Field Mappings

### MonitoringStatus
| Backend (Old) | Frontend (Expected) |
|--------------|---------------------|
| enabled | (remove) |
| running | is_running |
| last_run | last_poll_time |
| next_run | next_poll_time |
| queries_discovered_last_run | queries_discovered |
| (missing) | active_connections |

### QueryResponse
| Backend (Old) | Frontend (Expected) |
|--------------|---------------------|
| avg_exec_time_ms | avg_execution_time |
| total_exec_time_ms | total_execution_time |
| last_seen_at | last_seen |
| discovered_at | discovered_at (same) |

### ConnectionResponse
| Backend (Old) | Frontend (Expected) |
|--------------|---------------------|
| engine | db_type (alias) |
