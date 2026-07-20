# =====================================================
# AI Consulting Firm - Verification Script
# =====================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " AI Consulting Firm Verification"
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Ensure we're running from the project root
if (!(Test-Path "app")) {
    Write-Host "❌ Please run this script from the project root." -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Running isort..." -ForegroundColor Yellow
python -m isort .

Write-Host ""
Write-Host "[2/4] Running black..." -ForegroundColor Yellow
python -m black .

Write-Host ""
Write-Host "[3/4] Running mypy..." -ForegroundColor Yellow
python -m mypy app

Write-Host ""
Write-Host "[4/4] Running pytest..." -ForegroundColor Yellow
python -m pytest tests -q

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host " All verification checks passed!"
Write-Host "==========================================" -ForegroundColor Green