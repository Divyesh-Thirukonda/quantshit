#!/bin/bash

echo "🚀 Setting up Arbitrage Bot for Vercel deployment"
echo "=================================================="

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✅ Python $python_version detected"

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before running the bot"
else
    echo "✅ .env file already exists"
fi

# Test the bot
echo "🧪 Testing bot functionality..."
python test_bot.py

if [ $? -eq 0 ]; then
    echo "✅ Bot test passed"
else
    echo "❌ Bot test failed"
    exit 1
fi

# Run demo
echo "🎭 Running demo with mock data..."
python demo.py

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Test locally: python main.py --once"
echo "3. Deploy to Vercel: vercel"
echo ""
echo "For Vercel deployment:"
echo "- Install Vercel CLI: npm i -g vercel"
echo "- Run: vercel"
echo "- Set environment variables in Vercel dashboard"