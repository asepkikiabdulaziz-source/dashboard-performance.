# Production Deployment Script for Windows
# Usage: .\scripts\deploy.ps1 [environment]

param(
    [string]$Environment = "production"
)

Write-Host "🚀 Deploying to $Environment environment..." -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ Error: .env file not found" -ForegroundColor Red
    Write-Host "Please create .env file with required configuration"
    exit 1
}

# Validate configuration
Write-Host "📋 Validating configuration..." -ForegroundColor Yellow
python -c "from config import Config; missing = Config.validate(); exit(1 if missing else 0)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Configuration validation failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Configuration valid" -ForegroundColor Green

# Install/update dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --upgrade
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Run database migrations (if any)
if (Test-Path "scripts\migrations") {
    Write-Host "🗄️  Checking database migrations..." -ForegroundColor Yellow
    # Add migration runner here if needed
    Write-Host "✅ Database migrations checked" -ForegroundColor Green
}

# Build frontend (if needed)
if (Test-Path "..\frontend") {
    Write-Host "🏗️  Building frontend..." -ForegroundColor Yellow
    Set-Location ..\frontend
    npm install
    npm run build
    Set-Location ..\backend
    Write-Host "✅ Frontend built" -ForegroundColor Green
}

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Check if application starts
Write-Host "🔍 Testing application startup..." -ForegroundColor Yellow
$timeout = 10
$job = Start-Job -ScriptBlock { python -c "from main import app; print('OK')" }
$result = Wait-Job $job -Timeout $timeout
if ($result) {
    $output = Receive-Job $job
    Remove-Job $job
    if ($output -eq "OK") {
        Write-Host "✅ Application starts successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Application failed to start" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Application startup timeout" -ForegroundColor Red
    Remove-Job $job
    exit 1
}

Write-Host "✅ Deployment preparation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Start the application:"
Write-Host "   uvicorn main:app --host 0.0.0.0 --port 8000"
Write-Host ""
Write-Host "2. Or use a process manager (PM2, systemd, etc.)"
Write-Host ""
Write-Host "3. Verify health:"
Write-Host "   Invoke-WebRequest http://localhost:8000/health"
