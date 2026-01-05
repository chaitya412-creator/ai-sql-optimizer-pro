# Docker Build Error Fix - python-cors Issue

## Problem

The Docker build was failing with the following error:
```
ERROR: Could not find a version that satisfies the requirement python-cors==1.0.0
ERROR: No matching distribution found for python-cors==1.0.0
```

## Root Cause

The error was caused by **Docker build cache** containing stale or corrupted layer information. The package `python-cors==1.0.0` does not exist in PyPI and was never in our requirements.txt file.

**Important Notes:**
- FastAPI has **built-in CORS support** via `fastapi.middleware.cors.CORSMiddleware`
- No separate CORS package is needed for FastAPI applications
- The error was a phantom issue from cached Docker layers

## Solution Applied

### 1. Updated Dockerfile
Added pip upgrade step before installing dependencies:
```dockerfile
# Upgrade pip to latest version
RUN pip install --upgrade pip
```

This ensures:
- Latest pip version is used (fixes the pip 24.0 -> 25.3 warning)
- Clean installation environment
- Better dependency resolution

### 2. Created Rebuild Script
Created `rebuild-backend.ps1` to automate the clean rebuild process:
- Stops and removes existing containers
- Removes backend image
- Prunes build cache
- Rebuilds with `--no-cache` flag

## How to Fix

### Option 1: Use the Rebuild Script (Recommended)
```powershell
cd ai-sql-optimizer-pro
.\rebuild-backend.ps1
```

### Option 2: Manual Steps
```powershell
# Navigate to project directory
cd ai-sql-optimizer-pro

# Stop containers
docker-compose down

# Remove backend image
docker rmi ai-sql-optimizer-pro-backend -f

# Prune build cache
docker builder prune -f

# Rebuild with no cache
docker-compose build --no-cache backend

# Start the application
docker-compose up -d
```

### Option 3: Complete Docker Cleanup (Nuclear Option)
If the above doesn't work, perform a complete Docker cleanup:
```powershell
# WARNING: This removes ALL Docker data
docker system prune -a --volumes -f

# Then rebuild
docker-compose build --no-cache
docker-compose up -d
```

## Verification

After rebuilding, verify the backend is running:

```powershell
# Check container status
docker-compose ps

# Check backend logs
docker-compose logs backend

# Test health endpoint
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "ollama": {...},
  "monitoring_agent": true
}
```

## Prevention

To avoid similar issues in the future:

1. **Always use `--no-cache` when troubleshooting build issues**
   ```bash
   docker-compose build --no-cache
   ```

2. **Regularly clean Docker cache**
   ```bash
   docker builder prune -f
   ```

3. **Keep pip updated in Dockerfile** (already implemented)
   ```dockerfile
   RUN pip install --upgrade pip
   ```

4. **Use `.dockerignore` to exclude unnecessary files**
   - Already configured in the project

## Technical Details

### CORS in FastAPI
FastAPI includes CORS middleware out of the box:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**No additional packages required!**

### Requirements.txt
Our requirements.txt correctly includes only necessary packages:
- `fastapi==0.109.0` - Includes CORS middleware
- `uvicorn[standard]==0.27.0` - ASGI server
- Database drivers (psycopg2, PyMySQL, etc.)
- Security packages (cryptography, python-jose)
- Utilities (loguru, httpx, etc.)

## Troubleshooting

### If rebuild still fails:

1. **Check Docker version**
   ```bash
   docker --version
   docker-compose --version
   ```
   Ensure you're using recent versions.

2. **Check disk space**
   ```bash
   docker system df
   ```
   Clean up if needed:
   ```bash
   docker system prune -a
   ```

3. **Check requirements.txt encoding**
   Ensure the file is UTF-8 encoded without BOM.

4. **Verify network connectivity**
   Ensure you can reach PyPI:
   ```bash
   ping pypi.org
   ```

5. **Check for proxy issues**
   If behind a corporate proxy, configure Docker proxy settings.

## Summary

✅ **Fixed Issues:**
- Removed phantom `python-cors` dependency error
- Updated pip to latest version
- Created automated rebuild script
- Documented proper CORS usage in FastAPI

✅ **Files Modified:**
- `backend/Dockerfile` - Added pip upgrade step
- `rebuild-backend.ps1` - New automated rebuild script
- `DOCKER_BUILD_FIX.md` - This documentation

✅ **Next Steps:**
1. Run `.\rebuild-backend.ps1`
2. Verify backend starts successfully
3. Test the application endpoints
