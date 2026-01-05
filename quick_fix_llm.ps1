# Quick Fix Script for LLM Parsing Issue
Write-Host "`n=== LLM Parsing Issue - Quick Fix ===" -ForegroundColor Cyan

# Step 1: Restart backend to apply any code changes
Write-Host "`n1. Restarting backend service..." -ForegroundColor Yellow
docker-compose restart backend
Start-Sleep -Seconds 5
Write-Host "   Backend restarted" -ForegroundColor Green

# Step 2: Check if Ollama is running
Write-Host "`n2. Checking Ollama status..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 5
    Write-Host "   Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "   Ollama is not accessible, restarting..." -ForegroundColor Red
    docker-compose restart ollama
    Start-Sleep -Seconds 10
}

# Step 3: Test the parsing
Write-Host "`n3. Testing LLM parsing..." -ForegroundColor Yellow
python test_llm_parsing_fix.py

Write-Host "`n=== Fix Complete ===" -ForegroundColor Cyan
Write-Host "Try optimizing a query in the UI now.`n" -ForegroundColor Green
