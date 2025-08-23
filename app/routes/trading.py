from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.services.ostium_service import OstiumService
from app.utils.order_type import ORDER_TYPE

router = APIRouter(prefix="/trading", tags=["trading"])

ostium_service = OstiumService()


class PlaceOrderRequest(BaseModel):
    price_from_currency: str
    price_to_currency: str
    collateral: float
    leverage: int = 10
    asset_type: int = 0
    direction: bool = True
    order_type: str = "MARKET"
    take_profit_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    trader_address: Optional[str] = None
    limit_price: Optional[float] = None


class CloseTradeRequest(BaseModel):
    pair_id: str
    trade_index: str
    close_percentage: int = 100
    trader_address: Optional[str] = None


class AddCollateralRequest(BaseModel):
    pair_id: str
    index: str
    collateral: float
    trader_address: Optional[str] = None


class RemoveCollateralRequest(BaseModel):
    pair_id: str
    trade_index: str
    remove_amount: float


class UpdateStopLossRequest(BaseModel):
    pair_id: str
    index: str
    stop_loss_price: float
    trader_address: Optional[str] = None


class UpdateTakeProfitRequest(BaseModel):
    pair_id: str
    trade_index: str
    take_profit_price: float
    trader_address: Optional[str] = None


class FaucetRequest(BaseModel):
    address: str


@router.post("/place-order")
async def place_order(request: PlaceOrderRequest) -> Dict[str, Any]:
    """Place a new trading order"""
    try:
        order_type_enum = ORDER_TYPE.LIMIT if request.order_type.upper() == "LIMIT" else ORDER_TYPE.MARKET
        
        result = await ostium_service.place_order(
            price_from_currency=request.price_from_currency,
            price_to_currency=request.price_to_currency,
            collateral=request.collateral,
            leverage=request.leverage,
            asset_type=request.asset_type,
            direction=request.direction,
            order_type=order_type_enum,
            take_profit_price=request.take_profit_price or 0,
            stop_loss_price=request.stop_loss_price or 0,
            trader_address=request.trader_address,
            limit_price=request.limit_price
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place order: {str(e)}")


@router.post("/close-trade")
async def close_trade(request: CloseTradeRequest) -> Dict[str, Any]:
    """Close an existing trade"""
    try:
        result = await ostium_service.close_trade(
            pair_id=request.pair_id,
            trade_index=request.trade_index,
            close_percentage=request.close_percentage,
            trader_address=request.trader_address
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close trade: {str(e)}")


@router.post("/add-collateral")
async def add_collateral(request: AddCollateralRequest) -> Dict[str, Any]:
    """Add collateral to an existing trade"""
    try:
        result = await ostium_service.add_collateral(
            pairID=request.pair_id,
            index=request.index,
            collateral=request.collateral,
            trader_address=request.trader_address
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add collateral: {str(e)}")


@router.post("/remove-collateral")
async def remove_collateral(request: RemoveCollateralRequest) -> Dict[str, Any]:
    """Remove collateral from an existing trade"""
    try:
        result = await ostium_service.remove_collateral(
            pair_id=request.pair_id,
            trade_index=request.trade_index,
            remove_amount=request.remove_amount
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove collateral: {str(e)}")


@router.post("/update-stop-loss")
async def update_stop_loss(request: UpdateStopLossRequest) -> Dict[str, bool]:
    """Update stop loss for an existing trade"""
    try:
        result = ostium_service.update_stop_loss(
            pair_id=request.pair_id,
            index=request.index,
            stop_loss_price=request.stop_loss_price,
            trader_address=request.trader_address
        )
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update stop loss: {str(e)}")


@router.post("/update-take-profit")
async def update_take_profit(request: UpdateTakeProfitRequest) -> Dict[str, bool]:
    """Update take profit for an existing trade"""
    try:
        result = ostium_service.update_take_profit(
            pair_id=request.pair_id,
            trade_index=request.trade_index,
            take_profit_price=request.take_profit_price,
            trader_address=request.trader_address
        )
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update take profit: {str(e)}")


@router.get("/positions")
async def get_positions(address: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get open trading positions"""
    try:
        positions = await ostium_service.get_open_positions(address)
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {str(e)}")


@router.get("/history")
async def get_trade_history(address: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent trade history"""
    try:
        history = await ostium_service.get_recent_history(address, limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trade history: {str(e)}")


@router.get("/track-order/{order_id}")
async def track_order(order_id: str) -> Dict[str, Any]:
    """Track an order by ID"""
    try:
        result = await ostium_service.track_order(order_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track order: {str(e)}")


@router.get("/balances")
async def get_balances(address: Optional[str] = None, refresh: bool = True) -> Dict[str, float]:
    """Get wallet balances (ETH and USDC)"""
    try:
        target_address = address or ostium_service.address
        balances = await ostium_service.get_balances(target_address, refresh)
        return balances
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get balances: {str(e)}")


@router.post("/faucet")
async def get_faucet_usdc(request: FaucetRequest) -> Dict[str, Any]:
    """Request USDC from testnet faucet"""
    try:
        result = await ostium_service.get_faucet_usdc(request.address)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to request faucet USDC: {str(e)}")


@router.put("/slippage/{slippage_percentage}")
async def set_slippage(slippage_percentage: float) -> Dict[str, str]:
    """Set slippage percentage for trades"""
    try:
        ostium_service.set_slippage_percentage(slippage_percentage)
        return {"message": f"Slippage percentage set to {slippage_percentage}%"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set slippage: {str(e)}")