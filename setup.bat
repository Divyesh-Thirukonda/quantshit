@echo off
echo Setting up Arbitrage Bot for Vercel deployment
echo ==================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Show Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo ✅ Python %python_version% detected

REM Install dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed successfully

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your API keys before running the bot
) else (
    echo ✅ .env file already exists
)

REM Test the bot
echo Testing bot functionality...
python test_bot.py

if errorlevel 1 (
    echo ❌ Bot test failed
    pause
    exit /b 1
)
echo ✅ Bot test passed

REM Run demo
echo 🎭 Running demo with mock data...
python demo.py

echo.
echo 🎉 Setup completed successfully!
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Test locally: python main.py --once
echo 3. Deploy to Vercel: vercel
echo.
echo For Vercel deployment:
echo - Install Vercel CLI: npm i -g vercel
echo - Run: vercel
echo - Set environment variables in Vercel dashboard
pause