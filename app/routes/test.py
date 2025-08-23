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
            "1. Create wallet first: POST /wallet/create",
            "2. Then use any trading endpoints without private keys",
            "3. Check wallet status: GET /wallet/status"
        ],
        "wallet_routes": [
            "POST /wallet/create - Create new wallet (REQUIRED FIRST)",
            "POST /wallet/from-private-key - Import existing wallet",
            "GET /wallet/status - Check wallet initialization",
            "DELETE /wallet/clear - Clear wallet from memory"
        ],
        "health_routes": [
            "GET /health/ - Complete health check",
            "GET /health/rpc - RPC connection status", 
            "GET /health/network - Network information"
        ],
        "trading_routes": [
            "POST /trading/place-order - Place trading order",
            "POST /trading/close-trade - Close existing trade",
            "POST /trading/add-collateral - Add collateral to trade",
            "POST /trading/remove-collateral - Remove collateral from trade",
            "POST /trading/update-stop-loss - Update stop loss",
            "POST /trading/update-take-profit - Update take profit",
            "GET /trading/positions - Get open positions",
            "GET /trading/history - Get trade history",
            "GET /trading/track-order/{order_id} - Track order",
            "GET /trading/balances - Get wallet balances",
            "POST /trading/faucet - Request testnet USDC",
            "PUT /trading/slippage/{percentage} - Set slippage"
        ],
        "market_routes": [
            "GET /market/prices - Latest prices for all pairs",
            "GET /market/price/{from_currency}/{to_currency} - Specific pair price",
            "GET /market/pairs - Available trading pairs",
            "GET /market/pairs/detailed - Detailed pair information",
            "GET /market/overview - Market overview",
            "GET /market/status - Market status",
            "GET /market/currencies - Supported currencies"
        ],
        "notes": [
            "All trading endpoints require wallet to be created first",
            "Private key is stored in memory state management",
            "No need to pass private_key in request bodies"
        ]
    }