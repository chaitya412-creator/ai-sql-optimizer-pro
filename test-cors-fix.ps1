# PowerShell script to restart backend and test CORS fix

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CORS Fix - Restart and Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop backend
Write-Host "Step 1: Stopping backend service..." -ForegroundColor Yellow
docker-compose down backend
Write-Host "✓ Backend stopped" -ForegroundColor Green
Write-Host ""

# Step 2: Start backend
Write-Host "Step 2: Starting backend service..." -ForegroundColor Yellow
docker-compose up -d backend
Write-Host "✓ Backend started" -ForegroundColor Green
Write-Host ""

# Step 3: Wait for backend to be ready
Write-Host "Step 3: Waiting for backend to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

$maxAttempts = 12
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts -and -not $backendReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            Write-Host "✓ Backend is ready!" -ForegroundColor Green
        }
    }
    catch {
        $attempt++
        Write-Host "  Waiting... (attempt $attempt/$maxAttempts)" -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
}

if (-not $backendReady) {
    Write-Host "✗ Backend failed to start. Check logs with: docker-compose logs backend" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Run CORS tests
Write-Host "Step 4: Running CORS tests..." -ForegroundColor Yellow
Write-Host ""
python test_cors_fix.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Testing Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Check the test results above" -ForegroundColor White
Write-Host "2. Start your frontend: cd frontend; npm run dev" -ForegroundColor White
Write-Host "3. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "4. Check browser console for CORS errors (should be none)" -ForegroundColor White
Write-Host ""
Write-Host "To view backend logs: docker-compose logs -f backend" -ForegroundColor Gray
Write-Host ""
