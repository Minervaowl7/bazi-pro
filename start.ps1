$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendPort = 8711
$FrontendPort = 3000

$PythonExe = $null
foreach ($cmd in @("python", "py", "python3")) {
    try { $found = Get-Command $cmd -ErrorAction Stop; $PythonExe = $found.Source; break } catch {}
}
if (-not $PythonExe) {
    Write-Host "  ERROR: Python not found in PATH!" -ForegroundColor Red
    Write-Host "  Please install Python 3.10+ and add to PATH." -ForegroundColor Red
    Read-Host "Press Enter to exit"; exit 1
}

$PnpmExe = $null
foreach ($cmd in @("pnpm", "npx")) {
    try { $found = Get-Command $cmd -ErrorAction Stop; $PnpmExe = $found.Source; break } catch {}
}
if (-not $PnpmExe) {
    Write-Host "  ERROR: pnpm/npx not found in PATH!" -ForegroundColor Red
    Write-Host "  Please install Node.js and pnpm." -ForegroundColor Red
    Read-Host "Press Enter to exit"; exit 1
}

Write-Host ""
Write-Host "  ======================================" -ForegroundColor Cyan
Write-Host "       Bazi-Pro Quick Start" -ForegroundColor Cyan
Write-Host "  ======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Python: $PythonExe" -ForegroundColor DarkGray
Write-Host "  pnpm:   $PnpmExe" -ForegroundColor DarkGray
Write-Host ""

Write-Host "  [1/4] Checking ports..." -ForegroundColor Yellow
$ports = @($BackendPort, $FrontendPort)
foreach ($port in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
    if ($conn) {
        $procId = $conn.OwningProcess[0]
        Write-Host "  ! Port ${port} in use (PID $procId), killing..." -ForegroundColor Red
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 1

Write-Host "  [2/4] Starting backend (http://127.0.0.1:${BackendPort}) ..." -ForegroundColor Yellow
$backendProc = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m", "uvicorn", "server.app:app", "--host", "127.0.0.1", "--port", $BackendPort `
    -WorkingDirectory $Root `
    -PassThru -WindowStyle Normal

Write-Host "  [3/4] Waiting for backend..." -ForegroundColor Yellow
$retries = 0
$maxRetries = 15
while ($retries -lt $maxRetries) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:${BackendPort}/" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { break }
    } catch {}
    $retries++
    Write-Host "  ... waiting ($retries/$maxRetries)" -ForegroundColor DarkGray
    Start-Sleep -Seconds 1
}
if ($retries -ge $maxRetries) {
    Write-Host "  ! Backend startup timeout, check logs" -ForegroundColor Red
} else {
    Write-Host "  OK Backend ready" -ForegroundColor Green
}

Write-Host "  [4/4] Starting frontend (http://localhost:${FrontendPort}) ..." -ForegroundColor Yellow
$frontendProc = Start-Process -FilePath "cmd" `
    -ArgumentList "/c", "cd /d `"$Root\frontend`" && `"$PnpmExe`" dev" `
    -PassThru -WindowStyle Normal

Start-Sleep -Seconds 5
Write-Host "  Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:${FrontendPort}"

Write-Host ""
Write-Host "  --------------------------------------" -ForegroundColor DarkGray
Write-Host "   Backend:  http://127.0.0.1:${BackendPort}" -ForegroundColor White
Write-Host "   Frontend: http://localhost:${FrontendPort}" -ForegroundColor White
Write-Host "   API Docs: http://127.0.0.1:${BackendPort}/docs" -ForegroundColor White
Write-Host "  --------------------------------------" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services" -ForegroundColor DarkGray
Write-Host ""

try {
    while ($true) {
        $bp = Get-Process -Id $backendProc.Id -ErrorAction SilentlyContinue
        $fp = Get-Process -Id $frontendProc.Id -ErrorAction SilentlyContinue
        if (-not $bp -and -not $fp) {
            Write-Host "  Both services have exited" -ForegroundColor Yellow
            break
        }
        Start-Sleep -Seconds 5
    }
} finally {
    Write-Host "  Stopping services..." -ForegroundColor Yellow
    Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue
    Write-Host "  Stopped" -ForegroundColor Green
}
