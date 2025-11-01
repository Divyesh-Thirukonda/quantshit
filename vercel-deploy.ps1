# Quick Vercel Deploy Script
Write-Host "Quantshit - Vercel Deployment" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit - ready for Vercel deployment"
}

# Check if Vercel CLI is installed
try {
    $null = vercel --version
    Write-Host "SUCCESS: Vercel CLI found" -ForegroundColor Green
} catch {
    Write-Host "Installing Vercel CLI..." -ForegroundColor Yellow
    npm install -g vercel
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install Vercel CLI" -ForegroundColor Red
        Write-Host "Please install manually: npm install -g vercel" -ForegroundColor Yellow
        exit 1
    }
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "SUCCESS: Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Node.js not found" -ForegroundColor Red
    Write-Host "Please install Node.js from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Ready to deploy!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Setup Supabase (see VERCEL_DEPLOY.md)" -ForegroundColor White
Write-Host "2. Run: vercel" -ForegroundColor White
Write-Host "3. Configure environment variables in Vercel dashboard" -ForegroundColor White
Write-Host ""
Write-Host "Full guide: VERCEL_DEPLOY.md" -ForegroundColor Yellow