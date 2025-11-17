# Quick Start Script for Windows PowerShell
# Run this to start the entire application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Visibility Score Tracker - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating from template..." -ForegroundColor Yellow
    Copy-Item "config\.env.example" -Destination ".env"
    Write-Host "✓ Created .env file" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Edit .env and add your API keys!" -ForegroundColor Red
    Write-Host "Press any key to open .env file..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    notepad .env
    Write-Host ""
    Write-Host "After adding your API keys, press any key to continue..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Check if Docker is installed
Write-Host "Checking for Docker..." -ForegroundColor Cyan
try {
    docker --version | Out-Null
    $hasDocker = $true
    Write-Host "✓ Docker found" -ForegroundColor Green
} catch {
    $hasDocker = $false
    Write-Host "✗ Docker not found" -ForegroundColor Red
}

Write-Host ""

if ($hasDocker) {
    Write-Host "Starting with Docker (recommended)..." -ForegroundColor Cyan
    Write-Host ""
    
    # Start Docker Compose
    docker-compose up -d
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ Application Started Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access the application at:" -ForegroundColor Cyan
    Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
    Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
    Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "To view logs:" -ForegroundColor Cyan
    Write-Host "  docker-compose logs -f" -ForegroundColor White
    Write-Host ""
    Write-Host "To stop:" -ForegroundColor Cyan
    Write-Host "  docker-compose down" -ForegroundColor White
    Write-Host ""
    
} else {
    Write-Host "Docker not available. Please install Docker Desktop or follow manual setup in SETUP_GUIDE.md" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Download Docker Desktop:" -ForegroundColor Cyan
    Write-Host "  https://www.docker.com/products/docker-desktop" -ForegroundColor White
    Write-Host ""
}

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
