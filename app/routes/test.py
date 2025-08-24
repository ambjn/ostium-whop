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
        "workflow": [
            "1. All trading endpoints require user_id parameter",
            "2. Private keys are retrieved from wallet service using user_id",
            "3. No wallet creation endpoints - use external wallet management"
        ],
        "health_routes": [
            "GET /health/ - Complete health check",
            "GET /health/rpc - RPC connection status", 
            "GET /health/network - Network information"
        ],
        "trading_routes": [
            "POST /trading/place-order - Place trading order (requires user_id in body)",
            "POST /trading/close-trade - Close existing trade (requires user_id in body)",
            "POST /trading/add-collateral - Add collateral to trade (requires user_id in body)",
            "POST /trading/remove-collateral - Remove collateral from trade (requires user_id in body)",
            "POST /trading/update-stop-loss - Update stop loss (requires user_id in body)",
            "POST /trading/update-take-profit - Update take profit (requires user_id in body)",
            "GET /trading/positions?user_id={id} - Get open positions",
            "GET /trading/history?user_id={id} - Get trade history",
            "GET /trading/track-order/{order_id}?user_id={id} - Track order",
            "GET /trading/balances?user_id={id} - Get wallet balances",
            "POST /trading/faucet - Request testnet USDC (requires user_id in body)",
            "PUT /trading/slippage/{percentage}?user_id={id} - Set slippage"
        ],
        "market_routes": [
            "GET /market/prices?user_id={id} - Latest prices for all pairs",
            "GET /market/price/{from_currency}/{to_currency}?user_id={id} - Specific pair price",
            "GET /market/pairs?user_id={id} - Available trading pairs",
            "GET /market/pairs/detailed?user_id={id} - Detailed pair information",
            "GET /market/overview?user_id={id} - Market overview",
            "GET /market/status?user_id={id} - Market status",
            "GET /market/currencies?user_id={id} - Supported currencies"
        ],
        "authentication": {
            "method": "User ID based authentication",
            "description": "All trading and market endpoints require user_id parameter",
            "private_key_source": "Retrieved from wallet service using user_id",
            "supported_chains": ["ETH"]
        },
        "notes": [
            "All trading and market endpoints require user_id parameter",
            "Private keys are retrieved from encrypted wallet service",
            "POST endpoints: user_id in request body",
            "GET/PUT endpoints: user_id as query parameter",
            "No wallet management endpoints - handled externally"
        ]
    }