# Complete Setup Script - Runs all steps in sequence
# This script will initialize schema, populate data, and verify results

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "COMPREHENSIVE TEST DATA SETUP - AUTOMATED" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Initialize Schema
Write-Host "Step 1: Initializing Database Schema..." -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Gray
python init_postgres_schema.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Schema initialization failed!" -ForegroundColor Red
    exit 1
}
Write-Host "`n✅ Schema initialization complete!" -ForegroundColor Green

# Step 2: Populate Test Data
Write-Host "`nStep 2: Populating Test Data..." -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Gray
python populate_test_data_auto.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Data population failed!" -ForegroundColor Red
    exit 1
}
Write-Host "`n✅ Data population complete!" -ForegroundColor Green

# Step 3: Verify Data
Write-Host "`nStep 3: Verifying Data..." -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Gray
python verify_comprehensive_data.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Data verification failed!" -ForegroundColor Red
    exit 1
}
Write-Host "`n✅ Data verification complete!" -ForegroundColor Green

# Final Summary
Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "✅ ALL SETUP STEPS COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Restart your backend server (if running)" -ForegroundColor White
Write-Host "2. Open your browser and navigate to the dashboard" -ForegroundColor White
Write-Host "3. Verify the dashboard displays:" -ForegroundColor White
Write-Host "   • 20 performance issues across 17 optimized queries" -ForegroundColor White
Write-Host "   • All 10 issue types in 'Issues by Type' section" -ForegroundColor White
Write-Host "   • 17 queries in 'Queries with Detected Issues' section" -ForegroundColor White
Write-Host ""
