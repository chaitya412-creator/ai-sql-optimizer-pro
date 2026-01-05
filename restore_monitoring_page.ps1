# Restore Monitoring Page from Git
# Restore Monitoring Page from Git
# This script restores the complete working version of Monitoring.tsx

Write-Host "Restoring Monitoring.tsx from git repository..." -ForegroundColor Cyan

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "Error: Not in a git repository!" -ForegroundColor Red
    exit 1
}

# Restore the file from the last commit
git checkout HEAD -- frontend/src/pages/Monitoring.tsx

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Successfully restored Monitoring.tsx" -ForegroundColor Green
    Write-Host ""
    Write-Host "The Monitoring page now includes:" -ForegroundColor Yellow
    Write-Host "  ✓ Issues Summary with severity counts" -ForegroundColor Green
    Write-Host "  ✓ Issues by Type breakdown" -ForegroundColor Green
    Write-Host "  ✓ Detected Issues List with filters" -ForegroundColor Green
    Write-Host "  ✓ Expandable issue details" -ForegroundColor Green
    Write-Host "  ✓ Empty state for no connections" -ForegroundColor Green
    Write-Host "  ✓ Real-time updates every 10 seconds" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Rebuild the frontend: cd frontend && npm run build" -ForegroundColor White
    Write-Host "2. Start the application: docker-compose up" -ForegroundColor White
    Write-Host "3. Navigate to the Monitoring page to see detected issues" -ForegroundColor White
} else {
    Write-Host "Error: Failed to restore file from git" -ForegroundColor Red
    Write-Host "The file may have been modified. Try:" -ForegroundColor Yellow
    Write-Host "  git status" -ForegroundColor White
    Write-Host "  git diff frontend/src/pages/Monitoring.tsx" -ForegroundColor White
    exit 1
}
