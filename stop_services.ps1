Write-Host "Stopping BAPE Services..." -ForegroundColor Yellow

$ports = @(8000, 3001)

foreach ($port in $ports) {
    # Get PIDs listening on the port
    $pids = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

    if ($pids) {
        foreach ($pid_val in $pids) {
            Write-Host "Killing process on port $port (PID: $pid_val)..." -ForegroundColor Red
            try {
                Stop-Process -Id $pid_val -Force -ErrorAction SilentlyContinue
                Write-Host "Process $pid_val killed." -ForegroundColor Green
            } catch {
                Write-Host "Failed to kill process $pid_val." -ForegroundColor Red
            }
        }
    } else {
        Write-Host "No process found on port $port." -ForegroundColor Gray
    }
}

Write-Host "Services stopped." -ForegroundColor Green
