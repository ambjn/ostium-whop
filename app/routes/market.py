from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.services.ostium_service import OstiumService

router = APIRouter(prefix="/market", tags=["market"])

ostium_service = OstiumService()


class PriceResponse(BaseModel):
    price: float
    is_open: bool
    timestamp: Any
    pair: str


@router.get("/prices")
async def get_latest_prices() -> List[Dict[str, Any]]:
    """Get latest prices for all trading pairs"""
    try:
        prices = await ostium_service.get_latest_prices()
        if not prices:
            raise HTTPException(status_code=404, detail="No price data available")
        return prices
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get latest prices: {str(e)}")


@router.get("/price/{from_currency}/{to_currency}")
async def get_price(from_currency: str, to_currency: str) -> PriceResponse:
    """Get price for a specific trading pair"""
    try:
        price_data = await ostium_service.get_price(from_currency, to_currency)
        if not price_data:
            raise HTTPException(status_code=404, detail=f"Price not found for {from_currency}/{to_currency}")
        return PriceResponse(**price_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get price: {str(e)}")


@router.get("/pairs")
async def get_trading_pairs() -> List[Dict[str, Any]]:
    """Get available trading pairs information"""
    try:
        pairs = await ostium_service.get_pair_info()
        return pairs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trading pairs: {str(e)}")


@router.get("/pairs/detailed")
async def get_detailed_pairs() -> List[Dict[str, Any]]:
    """Get detailed information about trading pairs"""
    try:
        pairs = await ostium_service.get_formatted_pairs_details()
        return pairs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get detailed pairs: {str(e)}")


@router.get("/overview")
async def get_market_overview() -> Dict[str, Any]:
    """Get market overview with key metrics"""
    try:
        prices = await ostium_service.get_latest_prices()
        pairs = await ostium_service.get_pair_info()
        
        if not prices:
            prices = []
        if not pairs:
            pairs = []
            
        overview = {
            "total_pairs": len(pairs),
            "total_prices": len(prices),
            "latest_prices": prices[:10] if prices else [],
            "available_pairs": [f"{pair.get('from', '')}/{pair.get('to', '')}" for pair in pairs[:20]]
        }
        
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market overview: {str(e)}")


@router.get("/status")
async def get_market_status() -> Dict[str, Any]:
    """Get market status information"""
    try:
        network_info = ostium_service.get_network_info()
        is_healthy = ostium_service.is_healthy()
        
        return {
            "market_open": is_healthy,
            "network": network_info.get("network", "unknown"),
            "rpc_connected": is_healthy,
            "address": network_info.get("address", ""),
            "delegation_enabled": network_info.get("delegation_enabled", False)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market status: {str(e)}")


@router.get("/currencies")
async def get_supported_currencies() -> Dict[str, List[str]]:
    """Get list of supported currencies"""
    try:
        pairs = await ostium_service.get_pair_info()
        
        from_currencies = set()
        to_currencies = set()
        
        for pair in pairs:
            if pair.get("from"):
                from_currencies.add(pair["from"])
            if pair.get("to"):
                to_currencies.add(pair["to"])
        
        return {
            "from_currencies": sorted(list(from_currencies)),
            "to_currencies": sorted(list(to_currencies)),
            "all_currencies": sorted(list(from_currencies.union(to_currencies)))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get supported currencies: {str(e)}")