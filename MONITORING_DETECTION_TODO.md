# Monitoring Detection Integration - TODO

## Objective
Integrate automatic performance issue detection into the monitoring system so all 9 types of issues are displayed on the Monitoring page.

## Tasks

### Backend Changes
- [ ] 1. Update `backend/app/core/monitoring_agent.py`
  - [ ] Add automatic query analysis after discovery
  - [ ] Call PlanAnalyzer for each discovered query
  - [ ] Store detected issues in Query.detected_issues
  - [ ] Store individual issues in QueryIssue table
  - [ ] Add configuration for auto-analysis

- [ ] 2. Update `backend/app/api/monitoring.py`
  - [ ] Add GET /api/monitoring/issues endpoint
  - [ ] Add GET /api/monitoring/issues/summary endpoint
  - [ ] Add filtering by severity, connection, issue type
  - [ ] Return aggregated statistics

- [ ] 3. Update `backend/app/models/schemas.py`
  - [ ] Add MonitoringIssuesSummary schema
  - [ ] Enhance QueryResponse with issue counts

### Frontend Changes
- [ ] 4. Update `frontend/src/services/api.ts`
  - [ ] Add getMonitoringIssues() function
  - [ ] Add getIssuesSummary() function

- [ ] 5. Update `frontend/src/types/index.ts`
  - [ ] Add DetectedIssue interface
  - [ ] Add IssuesSummary interface

- [ ] 6. Update `frontend/src/pages/Monitoring.tsx`
  - [ ] Add "Detected Issues Summary" section
  - [ ] Add issue count cards by severity
  - [ ] Add issue count by type
  - [ ] Add issue badges to query rows
  - [ ] Add expandable issue details
  - [ ] Add filtering by issue severity

### Testing
- [ ] 7. Test automatic analysis
- [ ] 8. Verify all 9 issue types are detected
- [ ] 9. Test UI display
- [ ] 10. Performance testing

## Progress
Started: [Current Time]
Status: In Progress
