# CORS Fix TODO

## Tasks to Complete

- [x] Enhance CORS configuration in backend/main.py
  - [x] Add expose_headers configuration
  - [x] Add max_age for preflight caching
  - [x] Ensure all necessary headers are allowed
  
- [x] Improve error handling in backend/app/api/monitoring.py
  - [x] Add better error handling in get_discovered_queries
  - [x] Add database session validation
  - [x] Add detailed logging for debugging
  
- [ ] Test the fixes
  - [ ] Restart backend service
  - [ ] Test CORS headers
  - [ ] Verify frontend requests work

## Current Status
Implementation complete. Ready for testing.

## Changes Made

### backend/main.py
- Enhanced CORS middleware with explicit headers configuration
- Added expose_headers for Content-Length, Content-Type, X-Request-ID
- Added max_age=3600 for preflight caching
- Specified explicit HTTP methods instead of wildcard
- Added logging for CORS origins

### backend/app/api/monitoring.py
- Added detailed logging in get_discovered_queries endpoint
- Added database session validation
- Improved error handling with exc_info=True for better debugging
- Added debug logs for filtering operations
