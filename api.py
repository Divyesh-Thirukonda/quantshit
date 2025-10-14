from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from main import ArbitrageBot

app = FastAPI(title="Arbitrage Bot API", version="1.0.0")

# Global bot instance
bot = None

@app.on_event("startup")
async def startup_event():
    global bot
    bot = ArbitrageBot()

@app.get("/")
async def root():
    return {"message": "Arbitrage Bot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@app.post("/run-strategy")
async def run_strategy():
    """Manually trigger a strategy run"""
    try:
        bot.run_strategy_cycle()
        return {"success": True, "message": "Strategy cycle completed"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/markets")
async def get_markets():
    """Get current market data"""
    try:
        markets_data = bot.collect_market_data()
        return {"success": True, "data": markets_data}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)