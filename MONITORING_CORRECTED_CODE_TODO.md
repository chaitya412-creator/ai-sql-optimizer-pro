# Monitoring Page - Generate Corrected Code Feature

## Task
Add "Generate Corrected Code" functionality in the Monitoring page's Detected Performance Issues section using olmo-3:latest model from http://192.168.1.81:11434

## Implementation Plan

### Backend Changes
- [x] Update `backend/app/config.py` - Add OLLAMA_CODE_GENERATION_MODEL setting
- [x] Update `backend/app/core/ollama_client.py` - Add generate_corrected_code() method
- [x] Update `backend/app/api/monitoring.py` - Add new endpoint for code generation

### Frontend Changes
- [x] Update `frontend/src/services/api.ts` - Add API method
- [x] Update `frontend/src/pages/Monitoring.tsx` - Add UI components

### Testing
- [ ] Test endpoint with actual issues
- [ ] Verify olmo-3:latest model availability
- [ ] Test UI interaction

## Progress
- Status: ✅ IMPLEMENTATION COMPLETE
- Backend endpoint: POST /api/monitoring/issues/{issue_id}/generate-corrected-code
- Frontend: Button and display added to Monitoring page

## Implementation Summary

### What Was Added:

**Backend:**
1. Configuration setting for olmo-3:latest model
2. `generate_corrected_code()` method in OllamaClient
3. New API endpoint: `/api/monitoring/issues/{issue_id}/generate-corrected-code`

**Frontend:**
1. API client method `generateCorrectedCode(issueId)`
2. State management for corrected code, loading, and copy status
3. "Generate Corrected Code (olmo-3)" button in issue details
4. Beautiful display of corrected code with:
   - Syntax-highlighted code block
   - Explanation of changes
   - List of changes made
   - Copy to clipboard functionality

### How It Works:
1. User expands an issue in the Monitoring page
2. Clicks "Generate Corrected Code (olmo-3)" button
3. Backend calls olmo-3:latest model with issue details and recommendations
4. AI generates corrected SQL code addressing all recommendations
5. Frontend displays the corrected code with explanation
6. User can copy the code to clipboard

### Next Steps (Testing):
- Test with actual performance issues
- Verify olmo-3:latest model is available at http://192.168.1.81:11434
- Test UI interaction and code generation
