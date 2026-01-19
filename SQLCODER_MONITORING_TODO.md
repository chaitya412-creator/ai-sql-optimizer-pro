# SQLCoder Integration for Monitoring Page - Implementation TODO

## Objective
Use sqlcoder:latest to generate corrected queries beside the original query in the monitoring page.

## Implementation Steps

### Backend Changes
- [x] Add new endpoint `/api/monitoring/queries/{query_id}/generate-optimized-query` in `backend/app/api/monitoring.py`
- [x] Use `OllamaClient.optimize_query()` with sqlcoder:latest model
- [x] Return optimized SQL, explanation, and recommendations

### Frontend Changes
- [x] Add `generateOptimizedQuery()` method in `frontend/src/services/api.ts`
- [x] Export the method for use in components
- [x] Update `frontend/src/pages/Monitoring.tsx`:
  - [x] Add state management (optimizedQueries, generatingOptimized, expandedQueries)
  - [x] Add handler functions (handleGenerateOptimizedQuery, toggleQueryExpansion)
  - [x] Add "Optimize (sqlcoder)" button for each discovered query
  - [x] Display optimized query beside original query in expandable section
  - [x] Show explanation and recommendations
  - [x] Add copy functionality for optimized queries
  - [x] Fix TypeScript errors (use correct property names from Query type)

### Testing
- [ ] Test backend endpoint with sample queries
- [ ] Verify sqlcoder:latest model is available
- [ ] Test UI with different query types
- [ ] Test error handling
- [ ] End-to-end testing

## Status
✅ Implementation Complete - Ready for Testing
