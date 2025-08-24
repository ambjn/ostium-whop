import os
from fastapi import FastAPI
from app.routes import health, trading, market, test
import uvicorn

app = FastAPI(title="Ostium Trading API", version="1.0.0")

app.include_router(health.router)
app.include_router(trading.router)
app.include_router(market.router)
app.include_router(test.router)


@app.get("/")
def root():
    """Root endpoint returning API status"""
    return {"message": "Ostium Trading API - Ready for trading!"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
