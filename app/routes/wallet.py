from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.services.wallet import WalletService

router = APIRouter(prefix="/wallet", tags=["wallet"])


class CreateWalletResponse(BaseModel):
    address: str
    private_key: str


class PrivateKeyRequest(BaseModel):
    private_key: str


@router.post("/create", response_model=CreateWalletResponse)
async def create_wallet() -> CreateWalletResponse:
    """Create a new wallet with random private key"""
    try:
        wallet_data = WalletService.create_wallet()
        return CreateWalletResponse(**wallet_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create wallet: {str(e)}")


@router.post("/from-private-key", response_model=CreateWalletResponse)
async def get_wallet_from_private_key(request: PrivateKeyRequest) -> CreateWalletResponse:
    """Get wallet address from private key"""
    try:
        wallet_data = WalletService.get_wallet_from_private_key(request.private_key)
        return CreateWalletResponse(**wallet_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid private key: {str(e)}")