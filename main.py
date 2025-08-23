from fastapi import FastAPI
from app.routes import wallet, health, trading, market, test

app = FastAPI(title="Ostium Trading API", version="1.0.0")

app.include_router(wallet.router)
app.include_router(health.router)
app.include_router(trading.router)
app.include_router(market.router)
app.include_router(test.router)


@app.get("/")
def root():
    """Root endpoint returning API status"""
    return {"message": "Ostium Trading API - Ready for trading!"}
