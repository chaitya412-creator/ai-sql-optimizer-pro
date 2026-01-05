# Monitoring Page Issues Display - Implementation TODO

## Objective
Fix the Monitoring page to display detected performance issues (missing indexes, poor joins, full table scans, stale statistics, etc.) and handle the "no connections" state properly.

## Implementation Steps

### Phase 1: Update Monitoring Page UI ✅
- [ ] Add state management for issues data
- [ ] Add API calls to fetch issues summary and detailed issues
- [ ] Add Issues Summary section with severity counts
- [ ] Add Issues by Type display
- [ ] Add Recent Critical Issues preview
- [ ] Add Detected Issues table with filters
- [ ] Add empty state handling for no connections
- [ ] Add loading and error states

### Phase 2: Testing
- [ ] Test with no connections (empty state)
- [ ] Test with connections but no issues
- [ ] Test with connections and detected issues
- [ ] Test filtering by connection, severity, and issue type
- [ ] Test real-time updates (10-second refresh)
- [ ] Test error handling

## Files to Modify
- `frontend/src/pages/Monitoring.tsx` - Main implementation

## API Endpoints Used
- `GET /api/monitoring/issues/summary` - Get issues overview
- `GET /api/monitoring/issues` - Get detailed issues list
- `GET /api/connections` - Get connections list (already used)

## Expected Outcome
The Monitoring page will display:
1. Issues Summary with counts by severity (Critical, High, Medium, Low)
2. Issues by Type breakdown (missing indexes, poor joins, full scans, etc.)
3. Recent Critical Issues preview
4. Comprehensive Detected Issues table with filters
5. Proper empty state when no connections exist
6. Real-time updates every 10 seconds
