"""
In-memory state management for wallet and private key storage
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
import threading


@dataclass
class WalletState:
    private_key: Optional[str] = None
    address: Optional[str] = None
    is_initialized: bool = False


class StateManager:
    """Thread-safe singleton state manager"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StateManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized') or not self._initialized:
            self._wallet_state = WalletState()
            self._state_lock = threading.RLock()
            self._initialized = True
    
    def set_wallet(self, private_key: str, address: str) -> None:
        """Set wallet private key and address in state"""
        with self._state_lock:
            self._wallet_state.private_key = private_key
            self._wallet_state.address = address
            self._wallet_state.is_initialized = True
    
    def get_private_key(self) -> Optional[str]:
        """Get stored private key"""
        with self._state_lock:
            return self._wallet_state.private_key
    
    def get_address(self) -> Optional[str]:
        """Get stored wallet address"""
        with self._state_lock:
            return self._wallet_state.address
    
    def is_wallet_initialized(self) -> bool:
        """Check if wallet is initialized"""
        with self._state_lock:
            return self._wallet_state.is_initialized
    
    def clear_wallet(self) -> None:
        """Clear wallet state"""
        with self._state_lock:
            self._wallet_state.private_key = None
            self._wallet_state.address = None
            self._wallet_state.is_initialized = False
    
    def get_wallet_info(self) -> Dict[str, Any]:
        """Get wallet information"""
        with self._state_lock:
            return {
                "address": self._wallet_state.address,
                "is_initialized": self._wallet_state.is_initialized
            }


# Global state manager instance
state_manager = StateManager()


def require_wallet_initialized():
    """Decorator to ensure wallet is initialized before function execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not state_manager.is_wallet_initialized():
                raise ValueError("Wallet not initialized. Please call /wallet/create first.")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_current_private_key() -> str:
    """Get current private key from state, raise error if not initialized"""
    private_key = state_manager.get_private_key()
    if not private_key:
        raise ValueError("Wallet not initialized. Please call /wallet/create first.")
    return private_key


def get_current_address() -> str:
    """Get current address from state, raise error if not initialized"""
    address = state_manager.get_address()
    if not address:
        raise ValueError("Wallet not initialized. Please call /wallet/create first.")
    return address