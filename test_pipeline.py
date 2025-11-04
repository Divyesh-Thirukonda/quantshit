"""
Trading Pipeline Runner - Execute the complete arbitrage trading pipeline

This script demonstrates how to run the complete trading pipeline:
1. Scan markets and find matches
2. Detect arbitrage opportunities  
3. Portfolio management and position sizing
4. Execute trades (paper trading)

Can be used for testing or as a cron job.
"""

import asyncio
import httpx
import time
from datetime import datetime
import json

API_BASE_URL = "http://localhost:8000"  # Change to your deployed URL

async def run_pipeline():
    """Run the complete trading pipeline"""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("🚀 Starting Quantshit Trading Pipeline")
        print("=" * 50)
        
        # Step 1: Scan Markets
        print("\n📊 Step 1: Scanning markets and finding matches...")
        try:
            response = await client.post(f"{API_BASE_URL}/pipeline/scan-markets")
            scan_result = response.json()
            
            if scan_result["success"]:
                print(f"✅ Markets scanned successfully!")
                print(f"   - Kalshi markets: {scan_result['summary']['kalshi_markets']}")
                print(f"   - Polymarket markets: {scan_result['summary']['polymarket_markets']}")
                print(f"   - Total matches: {scan_result['summary']['total_matches']}")
                print(f"   - High confidence matches: {scan_result['summary']['high_confidence_matches']}")
            else:
                print(f"❌ Market scan failed: {scan_result['error']}")
                return
                
        except Exception as e:
            print(f"❌ Market scan error: {e}")
            return
            
        time.sleep(2)  # Brief pause between steps
        
        # Step 2: Detect Opportunities
        print("\n🎯 Step 2: Detecting arbitrage opportunities...")
        try:
            response = await client.post(
                f"{API_BASE_URL}/pipeline/detect-opportunities",
                params={"min_spread": 0.02, "max_opportunities": 20}
            )
            opportunities_result = response.json()
            
            if opportunities_result["success"]:
                print(f"✅ Opportunities detected successfully!")
                summary = opportunities_result['summary']
                print(f"   - Total opportunities: {summary['total_opportunities']}")
                print(f"   - Above threshold: {summary['filtered_opportunities']}")
                print(f"   - Top opportunities: {summary['top_opportunities']}")
                print(f"   - Best spread: {summary['best_spread']:.1%}")
                print(f"   - Average spread: {summary['average_spread']:.1%}")
                
                # Show top 3 opportunities
                if opportunities_result['opportunities']:
                    print("\n   Top 3 Opportunities:")
                    for i, opp in enumerate(opportunities_result['opportunities'][:3]):
                        print(f"   {i+1}. {opp['market_pair']['kalshi'][:40]}...")
                        print(f"      Spread: {opp['spread']['percentage']:.1%} | Profit: ${opp['expected_profit']:.2f}")
                        
            else:
                print(f"❌ Opportunity detection failed: {opportunities_result['error']}")
                return
                
        except Exception as e:
            print(f"❌ Opportunity detection error: {e}")
            return
            
        time.sleep(2)
        
        # Step 3: Portfolio Management
        print("\n💼 Step 3: Portfolio management and position sizing...")
        try:
            response = await client.post(
                f"{API_BASE_URL}/pipeline/portfolio-management",
                params={"max_position_size": 1000, "max_total_exposure": 10000}
            )
            portfolio_result = response.json()
            
            if portfolio_result["success"]:
                print(f"✅ Portfolio management completed!")
                portfolio = portfolio_result['portfolio_status']
                print(f"   - Portfolio value: ${portfolio['total_value']:,.2f}")
                print(f"   - Cash balance: ${portfolio['cash_balance']:,.2f}")
                print(f"   - Current positions: ${portfolio['positions_value']:,.2f}")
                print(f"   - Unrealized P&L: ${portfolio['unrealized_pnl']:,.2f}")
                
                risk = portfolio_result['risk_analysis']
                print(f"   - Portfolio utilization: {risk['utilization_percentage']:.1f}%")
                print(f"   - Risk level: {risk['risk_level']}")
                print(f"   - Recommendations: {len(portfolio_result['recommendations'])} positions")
                
            else:
                print(f"❌ Portfolio management failed: {portfolio_result['error']}")
                return
                
        except Exception as e:
            print(f"❌ Portfolio management error: {e}")
            return
            
        time.sleep(2)
        
        # Step 4: Execute Trades
        print("\n⚡ Step 4: Executing trades (paper trading)...")
        try:
            response = await client.post(
                f"{API_BASE_URL}/pipeline/execute-trades",
                params={"paper_trading": True}
            )
            execution_result = response.json()
            
            if execution_result["success"]:
                print(f"✅ Trade execution completed!")
                summary = execution_result['execution_summary']
                print(f"   - Mode: {execution_result['trading_mode']} trading")
                print(f"   - Total trades: {summary['total_trades']}")
                print(f"   - Successful: {summary['successful_trades']}")
                print(f"   - Total volume: ${summary['total_volume']:,.2f}")
                print(f"   - Expected profit: ${summary['expected_profit']:,.2f}")
                
                # Show executed trades
                if execution_result['executed_trades']:
                    print("\n   Executed Trades:")
                    for trade in execution_result['executed_trades']:
                        print(f"   - {trade['action']} {trade['quantity']} @ ${trade['price']} on {trade['platform']}")
                        
            else:
                print(f"❌ Trade execution failed: {execution_result['error']}")
                return
                
        except Exception as e:
            print(f"❌ Trade execution error: {e}")
            return
        
        print("\n🎉 Pipeline completed successfully!")
        print("=" * 50)

async def test_dashboard_endpoints():
    """Test the dashboard endpoints"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n📊 Testing Dashboard Endpoints")
        print("=" * 30)
        
        # Test overview
        try:
            response = await client.get(f"{API_BASE_URL}/dashboard/overview")
            overview = response.json()
            if overview["success"]:
                print("✅ Dashboard overview working")
                portfolio = overview["data"]["portfolio"]
                print(f"   Portfolio value: ${portfolio['total_value']:,.2f}")
                print(f"   Daily P&L: ${portfolio['daily_pnl']:,.2f} ({portfolio['daily_pnl_percentage']:.1f}%)")
            else:
                print("❌ Dashboard overview failed")
        except Exception as e:
            print(f"❌ Dashboard overview error: {e}")
        
        # Test opportunities
        try:
            response = await client.get(f"{API_BASE_URL}/dashboard/opportunities")
            opportunities = response.json()
            if opportunities["success"]:
                print(f"✅ Dashboard opportunities working ({opportunities['total_count']} opportunities)")
            else:
                print("❌ Dashboard opportunities failed")
        except Exception as e:
            print(f"❌ Dashboard opportunities error: {e}")
        
        # Test positions
        try:
            response = await client.get(f"{API_BASE_URL}/dashboard/positions")
            positions = response.json()
            if positions["success"]:
                print(f"✅ Dashboard positions working ({positions['summary']['total_positions']} positions)")
            else:
                print("❌ Dashboard positions failed")
        except Exception as e:
            print(f"❌ Dashboard positions error: {e}")

async def main():
    """Main function"""
    print("🤖 Quantshit Trading Pipeline Test")
    print(f"🌐 API URL: {API_BASE_URL}")
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test API health first
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                print("✅ API is healthy")
            else:
                print("❌ API health check failed")
                return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("💡 Make sure the API server is running:")
        print("   python -m uvicorn api.app:app --reload")
        return
    
    # Run the pipeline
    await run_pipeline()
    
    # Test dashboard endpoints
    await test_dashboard_endpoints()
    
    print(f"\n✨ Pipeline test completed at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())