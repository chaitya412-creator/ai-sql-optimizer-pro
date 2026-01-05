# Fix Microsoft SQL Server Repository Malformed Entry Error

## Tasks:
- [x] Identified the issue: sed command creating malformed repository entry
- [x] Fixed backend/Dockerfile to use direct echo command for repository entry
- [x] Removed problematic sed pattern
- [x] Created proper Debian repository format with signing key
- [x] Created documentation (MSSQL_REPOSITORY_FIX.md)
- [x] Task completed - Ready for user to rebuild containers

## Issue Fixed:
✅ **Error:** "Malformed entry 1 in list file /etc/apt/sources.list.d/mssql-release.list (URI parse)"

## Solution Applied:
Replaced the curl + sed approach with a direct echo command that creates a properly formatted repository entry:
```dockerfile
&& curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
&& echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
```

## Files Modified:
- ✅ backend/Dockerfile - Fixed repository setup
- ✅ MSSQL_REPOSITORY_FIX.md - Detailed documentation
- ✅ TODO.md - Updated task tracking

## Next Steps for User:
1. **Rebuild Docker containers:**
   ```bash
   docker-compose down
   docker rmi ai-sql-optimizer-pro-backend
   docker-compose build --no-cache backend
   docker-compose up -d
   ```

2. **Or use the rebuild script:**
   ```powershell
   .\rebuild-backend.ps1
   ```

3. **Or use the quick rebuild script:**
   ```powershell
   .\quick-rebuild.ps1
   ```

4. **Verify the build completes successfully** (should take 3-5 minutes)

5. **Test the application:**
   - Check logs: `docker-compose logs backend`
   - Test health endpoint: http://localhost:8000/health
   - Test SQL Server connections via API docs: http://localhost:8000/docs

## Expected Result:
✅ Docker build completes without "Malformed entry" error
✅ MSSQL ODBC Driver 17 installs successfully
✅ Application starts and runs normally
✅ SQL Server database connections work properly

## Technical Details:
The fix replaces the problematic sed command that was modifying Microsoft's repository list with a direct creation of a properly formatted Debian repository entry. This ensures:
- Correct syntax for apt repository with signed-by directive
- Proper architecture specifications (amd64, arm64, armhf)
- Valid URI format that apt can parse
- Consistent and predictable results

For more details, see: MSSQL_REPOSITORY_FIX.md
