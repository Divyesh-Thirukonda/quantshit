# AWS Setup Assistant
Write-Host "🔑 AWS Credentials Setup" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host ""

Write-Host "To deploy to AWS, you need:" -ForegroundColor Yellow
Write-Host "1. AWS Access Key ID" -ForegroundColor White
Write-Host "2. AWS Secret Access Key" -ForegroundColor White
Write-Host "3. Default region (recommend: us-east-1)" -ForegroundColor White
Write-Host "4. Output format (recommend: json)" -ForegroundColor White
Write-Host ""

Write-Host "📍 Get your credentials from:" -ForegroundColor Cyan
Write-Host "   https://console.aws.amazon.com/iam/home#/security_credentials" -ForegroundColor Blue
Write-Host ""
Write-Host "🆕 If you don't have AWS account:" -ForegroundColor Cyan
Write-Host "   1. Go to https://aws.amazon.com/" -ForegroundColor Blue
Write-Host "   2. Click 'Create AWS Account'" -ForegroundColor Blue
Write-Host "   3. Follow the signup process (requires credit card)" -ForegroundColor Blue
Write-Host ""

$continue = Read-Host "Do you have your AWS credentials ready? (y/n)"

if ($continue -eq "y" -or $continue -eq "Y") {
    Write-Host ""
    Write-Host "🚀 Starting AWS configuration..." -ForegroundColor Green
    aws configure
    
    Write-Host ""
    Write-Host "✅ Testing AWS connection..." -ForegroundColor Yellow
    try {
        $accountId = aws sts get-caller-identity --query Account --output text 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ AWS configured successfully! Account ID: $accountId" -ForegroundColor Green
        } else {
            Write-Host "❌ AWS configuration failed. Please check your credentials." -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ AWS configuration test failed." -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "📋 Please get your AWS credentials first, then run this script again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Steps to get credentials:" -ForegroundColor Cyan
    Write-Host "1. Sign in to AWS Console: https://console.aws.amazon.com/" -ForegroundColor White
    Write-Host "2. Go to IAM > Security credentials" -ForegroundColor White
    Write-Host "3. Create new access key" -ForegroundColor White
    Write-Host "4. Download the credentials file" -ForegroundColor White
}