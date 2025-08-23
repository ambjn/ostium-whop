from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.services.wallet import WalletService
from app.state import state_manager

router = APIRouter(prefix="/wallet", tags=["wallet"])


class CreateWalletResponse(BaseModel):
    address: str
    private_key: str


class PrivateKeyRequest(BaseModel):
    private_key: str


@router.post("/create", response_model=CreateWalletResponse)
async def create_wallet() -> CreateWalletResponse:
    """Create a new wallet with random private key and store in state"""
    try:
        wallet_data = WalletService.create_wallet()
        
        # Store in state management
        state_manager.set_wallet(
            private_key=wallet_data["private_key"],
            address=wallet_data["address"]
        )
        
        # Return only address and private_key (don't expose private key in response)
        return CreateWalletResponse(
            address=wallet_data["address"],
            private_key=wallet_data["private_key"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create wallet: {str(e)}")


@router.post("/from-private-key", response_model=CreateWalletResponse)
async def get_wallet_from_private_key(request: PrivateKeyRequest) -> CreateWalletResponse:
    """Import wallet from private key and store in state"""
    try:
        wallet_data = WalletService.get_wallet_from_private_key(request.private_key)
        
        # Store in state management
        state_manager.set_wallet(
            private_key=wallet_data["private_key"],
            address=wallet_data["address"]
        )
        
        return CreateWalletResponse(**wallet_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid private key: {str(e)}")


@router.get("/status")
async def get_wallet_status() -> Dict[str, Any]:
    """Get current wallet status"""
    try:
        wallet_info = state_manager.get_wallet_info()
        return {
            "initialized": wallet_info["is_initialized"],
            "address": wallet_info["address"],
            "message": "Wallet ready for trading" if wallet_info["is_initialized"] else "Please create wallet first"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get wallet status: {str(e)}")


@router.delete("/clear")
async def clear_wallet() -> Dict[str, str]:
    """Clear wallet from state"""
    try:
        state_manager.clear_wallet()
        return {"message": "Wallet cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear wallet: {str(e)}")