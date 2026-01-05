# Test Dashboard Connection Filter Fix
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Dashboard Connection Filter Tests" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: Get all dashboard stats (no filter)
Write-Host "Test 1: Get Dashboard Stats (All Connections)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/dashboard/stats" -Method GET -UseBasicParsing
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    $data = $response.Content | ConvertFrom-Json
    Write-Host "  Total Connections: $($data.total_connections)" -ForegroundColor White
    Write-Host "  Total Queries: $($data.total_queries_discovered)" -ForegroundColor White
    Write-Host "  Total Issues: $($data.total_detected_issues)" -ForegroundColor White
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Get connections list
Write-Host "Test 2: Get Connections List" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/connections" -Method GET -UseBasicParsing
    Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
    $connections = $response.Content | ConvertFrom-Json
    Write-Host "  Found $($connections.Count) connection(s)" -ForegroundColor White
    foreach ($conn in $connections) {
        Write-Host "    - ID: $($conn.id), Name: $($conn.name), Engine: $($conn.engine)" -ForegroundColor Gray
    }
    
    # Test 3: Get dashboard stats filtered by first connection
    if ($connections.Count -gt 0) {
        Write-Host ""
        $firstConnId = $connections[0].id
        Write-Host "Test 3: Get Dashboard Stats (Connection ID: $firstConnId)" -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "$baseUrl/api/dashboard/stats?connection_id=$firstConnId" -Method GET -UseBasicParsing
            Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
            $data = $response.Content | ConvertFrom-Json
            Write-Host "  Total Connections: $($data.total_connections)" -ForegroundColor White
            Write-Host "  Total Queries: $($data.total_queries_discovered)" -ForegroundColor White
            Write-Host "  Total Issues: $($data.total_detected_issues)" -ForegroundColor White
        } catch {
            Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Test 4: Get top queries filtered by connection
    if ($connections.Count -gt 0) {
        Write-Host ""
        $firstConnId = $connections[0].id
        Write-Host "Test 4: Get Top Queries (Connection ID: $firstConnId)" -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "$baseUrl/api/dashboard/top-queries?connection_id=$firstConnId`&limit=5" -Method GET -UseBasicParsing
            Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
            $queries = $response.Content | ConvertFrom-Json
            Write-Host "  Found $($queries.Count) queries" -ForegroundColor White
        } catch {
            Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Test 5: Get detection summary filtered by connection
    if ($connections.Count -gt 0) {
        Write-Host ""
        $firstConnId = $connections[0].id
        Write-Host "Test 5: Get Detection Summary (Connection ID: $firstConnId)" -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "$baseUrl/api/dashboard/detection-summary?connection_id=$firstConnId" -Method GET -UseBasicParsing
            Write-Host "✓ Status: $($response.StatusCode)" -ForegroundColor Green
            $summary = $response.Content | ConvertFrom-Json
            Write-Host "  Total Issues: $($summary.total_issues)" -ForegroundColor White
            Write-Host "  Critical: $($summary.critical_issues), High: $($summary.high_issues), Medium: $($summary.medium_issues), Low: $($summary.low_issues)" -ForegroundColor White
        } catch {
            Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
} catch {
    Write-Host "✗ Failed to get connections: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Tests Complete" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
