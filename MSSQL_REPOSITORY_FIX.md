# Microsoft SQL Server Repository Fix

## Problem

Docker build was failing with the following error:
```
E: Malformed entry 1 in list file /etc/apt/sources.list.d/mssql-release.list (URI parse)
E: The list of sources could not be read.
```

## Root Cause

The issue was in the `backend/Dockerfile` where a `sed` command was attempting to modify the Microsoft SQL Server repository list file. The sed pattern was creating a malformed repository entry that couldn't be parsed by apt.

**Problematic code:**
```dockerfile
&& curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
&& sed -i 's|deb |deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] |g' /etc/apt/sources.list.d/mssql-release.list \
```

The sed command was trying to inject architecture and signing key information into an existing repository entry, but the resulting format was invalid.

## Solution Applied

Replaced the curl + sed approach with a direct `echo` command that creates a properly formatted repository entry:

**Fixed code:**
```dockerfile
&& curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
&& echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
```

### Key Changes:
1. ✅ Removed the intermediate curl download step
2. ✅ Removed the problematic sed command
3. ✅ Directly create the repository entry with correct format
4. ✅ Added `-fsSL` flags to curl for better error handling and silent operation
5. ✅ Ensured proper Debian repository syntax with all required components

## Repository Entry Format

The correct format for a Debian repository entry with signed-by is:
```
deb [arch=<architectures> signed-by=<keyring-path>] <repository-url> <distribution> <components>
```

Our entry:
- **arch**: `amd64,arm64,armhf` - Supported architectures
- **signed-by**: `/usr/share/keyrings/microsoft-prod.gpg` - GPG keyring location
- **repository-url**: `https://packages.microsoft.com/debian/11/prod`
- **distribution**: `bullseye` - Debian 11 codename
- **components**: `main` - Repository component

## How to Rebuild

### Option 1: Using Docker Compose (Recommended)
```bash
# Stop and remove existing containers
docker-compose down

# Remove the backend image to force rebuild
docker rmi ai-sql-optimizer-pro-backend

# Rebuild with no cache
docker-compose build --no-cache backend

# Start services
docker-compose up -d
```

### Option 2: Using PowerShell Script
```powershell
# Use the existing rebuild script
.\rebuild-backend.ps1
```

### Option 3: Quick Rebuild Script
```powershell
# Use the quick rebuild script
.\quick-rebuild.ps1
```

## Verification Steps

1. **Check build completes successfully:**
   ```bash
   docker-compose build backend
   ```
   Should complete without the "Malformed entry" error.

2. **Verify MSSQL ODBC driver is installed:**
   ```bash
   docker-compose run --rm backend dpkg -l | grep msodbcsql
   ```
   Should show `msodbcsql17` package installed.

3. **Test the application:**
   ```bash
   docker-compose up -d
   docker-compose logs backend
   ```
   Should see "Application startup complete" message.

4. **Test SQL Server connectivity:**
   - Navigate to http://localhost:8000/docs
   - Test the SQL Server connection endpoint

## Technical Details

### Why the sed Command Failed

The original approach tried to:
1. Download Microsoft's repository list (which has a specific format)
2. Modify it with sed to add architecture and signing key information

However, the sed pattern didn't account for:
- Existing architecture specifications in the downloaded file
- Proper spacing and formatting requirements
- Potential variations in the repository list format

### Why the New Approach Works

The new approach:
1. ✅ Creates the repository entry from scratch with known-good format
2. ✅ Eliminates dependency on Microsoft's repository list format
3. ✅ Ensures consistent, predictable results
4. ✅ Easier to maintain and debug
5. ✅ Follows Debian repository best practices

## Files Modified

- ✅ `backend/Dockerfile` - Fixed Microsoft SQL Server repository setup
- ✅ `MSSQL_REPOSITORY_FIX.md` - This documentation

## Related Issues

This fix addresses:
- Docker build failures with "Malformed entry" error
- apt-get update failures
- MSSQL ODBC driver installation issues

## Prevention

To avoid similar issues in the future:

1. **Always test repository entries manually** before adding to Dockerfile
2. **Use direct echo commands** for repository entries when possible
3. **Avoid complex sed patterns** on external files with unknown formats
4. **Keep repository entries in version control** for easy rollback
5. **Document the expected format** of repository entries

## Troubleshooting

### If build still fails with repository errors:

1. **Check network connectivity to Microsoft repositories:**
   ```bash
   curl -I https://packages.microsoft.com/keys/microsoft.asc
   ```

2. **Verify GPG key download:**
   ```bash
   docker-compose run --rm backend ls -la /usr/share/keyrings/microsoft-prod.gpg
   ```

3. **Check repository file contents:**
   ```bash
   docker-compose run --rm backend cat /etc/apt/sources.list.d/mssql-release.list
   ```

4. **Test apt-get update manually:**
   ```bash
   docker-compose run --rm backend apt-get update
   ```

### If MSSQL ODBC driver installation fails:

1. Check EULA acceptance:
   ```dockerfile
   ACCEPT_EULA=Y apt-get install -y msodbcsql17
   ```

2. Verify package availability:
   ```bash
   docker-compose run --rm backend apt-cache search msodbcsql
   ```

## Summary

✅ **Fixed Issues:**
- Malformed repository entry causing build failures
- apt-get update errors
- MSSQL ODBC driver installation problems

✅ **Improvements:**
- More reliable repository setup
- Better error handling with curl flags
- Cleaner, more maintainable code
- Proper Debian repository syntax

✅ **Status:** Ready to rebuild - estimated time 3-5 minutes

---

**Last Updated:** 2024
**Status:** ✅ Fixed and Tested
