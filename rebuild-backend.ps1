# PowerShell script to rebuild backend with clean cache

Write-Host "🧹 Cleaning Docker build cache..." -ForegroundColor Yellow

# Stop and remove existing containers
docker-compose down

# Remove backend image
docker rmi ai-sql-optimizer-pro-backend -f 2>$null

# Prune build cache
docker builder prune -f

Write-Host "🔨 Building backend with no cache..." -ForegroundColor Cyan
docker-compose build --no-cache backend

if ($LASTEXITCODE -eq 0) {
    Write-Host "Backend rebuilt successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To start the application, run:" -ForegroundColor Yellow
    Write-Host "  docker-compose up -d" -ForegroundColor White
} else {
    Write-Host "Build failed. Please check the error messages above." -ForegroundColor Red
    exit 1
}
