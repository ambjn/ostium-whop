from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.ostium_service import OstiumService

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    rpc_connected: bool
    latest_block: Optional[int]
    network_info: Dict[str, Any]


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check Ostium service health and connectivity"""
    try:
        ostium_service = OstiumService()
        is_healthy = ostium_service.is_healthy()
        latest_block = ostium_service.get_block_number()
        network_info = ostium_service.get_network_info()
        
        return HealthResponse(
            status="healthy" if is_healthy else "unhealthy",
            rpc_connected=is_healthy,
            latest_block=latest_block,
            network_info=network_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/rpc")
async def rpc_status() -> Dict[str, Any]:
    """Check RPC connection status"""
    try:
        ostium_service = OstiumService()
        block_number = ostium_service.check_rpc_status()
        return {
            "connected": block_number is not None,
            "latest_block": block_number,
            "rpc_url": ostium_service.rpc_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RPC check failed: {str(e)}")


@router.get("/network")
async def network_info() -> Dict[str, Any]:
    """Get network configuration information"""
    try:
        ostium_service = OstiumService()
        return ostium_service.get_network_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network info: {str(e)}")