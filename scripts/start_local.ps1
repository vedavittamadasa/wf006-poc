# WF-006 Local Development Runner (PowerShell)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  WF-006 Local Runner (Windows PowerShell)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Check Python
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    Write-Error "Python not found in PATH. Please install Python 3.12+."
    exit 1
}

Write-Host "[1/2] Executing complete local test suite..." -ForegroundColor Yellow
python "$ScriptDir\run_local.py"

Write-Host "`nTo keep services running interactively for testing via Swagger UI:" -ForegroundColor Green
Write-Host "  python $ScriptDir\run_local.py --keep-running" -ForegroundColor White
