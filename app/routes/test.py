from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/test", tags=["test"])


@router.get("/ping")
async def ping() -> Dict[str, str]:
    """Simple ping endpoint to test API connectivity"""
    return {"status": "pong", "message": "API is working"}


@router.get("/routes")
async def list_routes() -> Dict[str, Any]:
    """List all available API routes"""
    return {
        "wallet_routes": [
            "POST /wallet/create",
            "POST /wallet/from-private-key"
        ],
        "health_routes": [
            "GET /health/",
            "GET /health/rpc", 
            "GET /health/network"
        ],
        "trading_routes": [
            "POST /trading/place-order",
            "POST /trading/close-trade",
            "POST /trading/add-collateral",
            "POST /trading/remove-collateral",
            "POST /trading/update-stop-loss",
            "POST /trading/update-take-profit",
            "GET /trading/positions",
            "GET /trading/history",
            "GET /trading/track-order/{order_id}",
            "GET /trading/balances",
            "POST /trading/faucet",
            "PUT /trading/slippage/{percentage}"
        ],
        "market_routes": [
            "GET /market/prices",
            "GET /market/price/{from_currency}/{to_currency}",
            "GET /market/pairs",
            "GET /market/pairs/detailed",
            "GET /market/overview",
            "GET /market/status",
            "GET /market/currencies"
        ]
    }