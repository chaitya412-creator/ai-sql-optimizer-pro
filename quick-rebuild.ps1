# Quick Docker Rebuild Script
# Optimized for fast rebuilds after fixing 1+ hour build issue

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Docker Quick Rebuild Script" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Stop existing containers
Write-Host "Step 1: Stopping existing containers..." -ForegroundColor Yellow
docker-compose down
Write-Host "✓ Containers stopped" -ForegroundColor Green
Write-Host ""

# Optional: Clear build cache for clean build
Write-Host "Step 2: Do you want to clear Docker build cache? (Recommended for first rebuild)" -ForegroundColor Yellow
Write-Host "This ensures a completely clean build. (y/n): " -NoNewline
$clearCache = Read-Host

if ($clearCache -eq 'y' -or $clearCache -eq 'Y') {
    Write-Host "Clearing Docker build cache..." -ForegroundColor Yellow
    docker builder prune -f
    Write-Host "✓ Build cache cleared" -ForegroundColor Green
}
Write-Host ""

# Rebuild backend with timing
Write-Host "Step 3: Building backend image (should take 3-5 minutes)..." -ForegroundColor Yellow
$startTime = Get-Date

docker-compose build --no-cache backend

$endTime = Get-Date
$duration = $endTime - $startTime
Write-Host "✓ Backend built successfully in $($duration.Minutes)m $($duration.Seconds)s" -ForegroundColor Green
Write-Host ""

# Start services
Write-Host "Step 4: Starting services..." -ForegroundColor Yellow
docker-compose up -d
Write-Host "✓ Services started" -ForegroundColor Green
Write-Host ""

# Wait for backend to be ready
Write-Host "Step 5: Waiting for backend to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check health
Write-Host "Step 6: Checking service health..." -ForegroundColor Yellow
$maxAttempts = 10
$attempt = 0
$healthy = $false

while ($attempt -lt $maxAttempts -and -not $healthy) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            Write-Host "✓ Backend is healthy and responding!" -ForegroundColor Green
        }
    }
    catch {
        $attempt++
        Write-Host "Waiting for backend... (attempt $attempt/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

if (-not $healthy) {
    Write-Host "⚠ Backend may not be fully ready yet. Check logs with: docker-compose logs backend" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Rebuild Complete!" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Build time: $($duration.Minutes)m $($duration.Seconds)s" -ForegroundColor White
Write-Host "Expected: 3-5 minutes (vs 60+ minutes before optimization)" -ForegroundColor White
Write-Host ""
Write-Host "Services:" -ForegroundColor White
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor White
Write-Host "  View logs:    docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "  Stop all:     docker-compose down" -ForegroundColor Gray
Write-Host "  Restart:      docker-compose restart" -ForegroundColor Gray
Write-Host ""
