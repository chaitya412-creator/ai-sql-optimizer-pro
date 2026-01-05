# LLM Parsing Issue Diagnostic Script for Windows
# This script will help diagnose and fix the LLM parsing issue

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "LLM PARSING ISSUE DIAGNOSTIC TOOL" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Check Docker services status
Write-Host "Step 1: Checking Docker services..." -ForegroundColor Yellow
Write-Host "----------------------------------------`n"

try {
    $services = docker-compose ps
    Write-Host $services
    Write-Host "`n✓ Docker services checked`n" -ForegroundColor Green
} catch {
    Write-Host "✗ Error checking Docker services: $_`n" -ForegroundColor Red
}

# Step 2: Check Ollama logs (last 30 lines)
Write-Host "`nStep 2: Checking Ollama logs..." -ForegroundColor Yellow
Write-Host "----------------------------------------`n"

try {
    $ollamaLogs = docker-compose logs ollama --tail=30
    Write-Host $ollamaLogs
    Write-Host "`n✓ Ollama logs retrieved`n" -ForegroundColor Green
} catch {
    Write-Host "✗ Error getting Ollama logs: $_`n" -ForegroundColor Red
}

# Step 3: Check Backend logs (last 30 lines)
Write-Host "`nStep 3: Checking Backend logs..." -ForegroundColor Yellow
Write-Host "----------------------------------------`n"

try {
    $backendLogs = docker-compose logs backend --tail=30
    Write-Host $backendLogs
    Write-Host "`n✓ Backend logs retrieved`n" -ForegroundColor Green
} catch {
    Write-Host "✗ Error getting Backend logs: $_`n" -ForegroundColor Red
}

# Step 4: Test Ollama connectivity
Write-Host "`nStep 4: Testing Ollama connectivity..." -ForegroundColor Yellow
Write-Host "----------------------------------------`n"

try {
    $ollamaHealth = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -ErrorAction Stop
    Write-Host "✓ Ollama is accessible" -ForegroundColor Green
    Write-Host "Available models:" -ForegroundColor Cyan
    foreach ($model in $ollamaHealth.models) {
        Write-Host "  - $($model.name)" -ForegroundColor White
    }
    Write-Host ""
} catch {
    Write-Host "✗ Cannot connect to Ollama: $_" -ForegroundColor Red
    Write-Host "  Make sure Ollama is running on http://localhost:11434`n" -ForegroundColor Yellow
}

# Step 5: Run parsing test
Write-Host "`nStep 5: Running LLM parsing test..." -ForegroundColor Yellow
Write-Host "----------------------------------------`n"

try {
    python test_llm_parsing_fix.py
    Write-Host "`n✓ Parsing test completed`n" -ForegroundColor Green
} catch {
    Write-Host "✗ Error running parsing test: $_`n" -ForegroundColor Red
}

# Step 6: Recommendations
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RECOMMENDATIONS" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Based on the diagnostics above, try these fixes:`n" -ForegroundColor Yellow

Write-Host "1. Restart Backend Service:" -ForegroundColor White
Write-Host "   docker-compose restart backend`n" -ForegroundColor Gray

Write-Host "2. If Ollama is not accessible:" -ForegroundColor White
Write-Host "   docker-compose restart ollama`n" -ForegroundColor Gray

Write-Host "3. If models are missing:" -ForegroundColor White
Write-Host "   docker-compose exec ollama ollama pull sqlcoder:latest`n" -ForegroundColor Gray

Write-Host "4. Full restart (if needed):" -ForegroundColor White
Write-Host "   docker-compose down" -ForegroundColor Gray
Write-Host "   docker-compose up -d`n" -ForegroundColor Gray

Write-Host "5. Check backend logs in real-time:" -ForegroundColor White
Write-Host "   docker-compose logs -f backend`n" -ForegroundColor Gray

Write-Host "`nPress any key to continue..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
