from __future__ import annotations

import base64
import json
import os
import secrets
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class SupabaseService:
    def __init__(self):
        self.url: str = os.environ.get("DATABASE_URL")
        self.key: str = os.environ.get("SUPABASE_ANON_KEY")

        if not self.url or not self.key:
            raise ValueError("Missing required Supabase environment variables")

        self.client: Client = create_client(self.url, self.key)


class _AESCipher:
    """AES-256-GCM encryption wrapper using random 96-bit nonces."""

    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("MASTER_KEY must decode to 32 bytes (256-bit)")
        self._aes = AESGCM(key)

    def enc(self, data: bytes) -> tuple[bytes, bytes, bytes]:
        nonce = secrets.token_bytes(12)
        ct = self._aes.encrypt(nonce, data, None)
        return ct[:-16], nonce, ct[-16:]  # ciphertext, nonce, tag

    def dec(self, ciphertext: bytes, nonce: bytes, tag: bytes) -> bytes:
        return self._aes.decrypt(nonce, ciphertext + tag, None)


class WalletService:
    """Wallet service for private key decryption."""

    def __init__(self) -> None:
        # Initialize Supabase service
        self.supabase_service = SupabaseService()

        # Initialize encryption
        master_b64 = os.getenv("MASTER_KEY")
        if not master_b64:
            raise RuntimeError("MASTER_KEY env variable not set")
        self.cipher = _AESCipher(base64.b64decode(master_b64))

    def export_wallet(self, user_id: str, chain: str) -> str:
        """Return decrypted private key for an existing ETH/SOL wallet."""
        user_id = self._ensure_user(user_id)
        chain = chain.upper()
        if chain not in {"ETH", "SOL"}:
            raise ValueError("chain must be ETH or SOL")

        chain_db = "ethereum" if chain == "ETH" else "solana"
        try:
            wallet = self._get_wallet_by_chain(user_id, chain_db)

            if not wallet:
                raise KeyError("wallet_not_found")

            # Decode the escaped hex sequences to get the actual JSON strings
            encrypted_priv_str = bytes.fromhex(
                wallet["encrypted_priv"].replace("\\x", "")
            ).decode("utf-8")
            nonce_str = bytes.fromhex(wallet["nonce"].replace("\\x", "")).decode(
                "utf-8"
            )
            tag_str = bytes.fromhex(wallet["tag"].replace("\\x", "")).decode("utf-8")

            # Now parse the JSON
            encrypted_priv_json = json.loads(encrypted_priv_str)
            nonce_json = json.loads(nonce_str)
            tag_json = json.loads(tag_str)

            # Convert Buffer data arrays to bytes
            ciphertext = bytes(encrypted_priv_json["data"])
            nonce = bytes(nonce_json["data"])
            tag = bytes(tag_json["data"])

            secret_bytes = self.cipher.dec(ciphertext, nonce, tag)

            if chain == "ETH":
                return "0x" + secret_bytes.hex()
            else:  # SOL
                return base64.b64encode(secret_bytes).decode()

        except KeyError:
            raise
        except Exception as exc:
            print(f"Unexpected error in export_wallet: {exc}")
            raise RuntimeError(f"Failed to export wallet: {exc}") from exc

    def _ensure_user(
        self,
        user_id: int,
    ) -> int:
        """Return users.id."""
        user = self._get_user_by_id(user_id)
        if not user:
            raise KeyError("user_not_found")
        return user["id"]

    def _get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by user ID."""
        users = (
            self.supabase_service.client.table("users")
            .select("*")
            .eq("id", user_id)
            .execute()
        )
        return users.data[0] if users.data else None

    def _get_wallet_by_chain(
        self, user_id: int, chain: str
    ) -> Optional[Dict[str, Any]]:
        """Get wallet by user ID and chain."""
        wallets = (
            self.supabase_service.client.table("wallets")
            .select("*")
            .eq("user_id", user_id)
            .eq("chain", chain)
            .execute()
        )
        return wallets.data[0] if wallets.data else None

    def debug_wallet_data(self, user_id: int, chain: str):
        """Debug helper to inspect wallet data"""
        user_id = self._ensure_user(user_id)
        chain_db = "ethereum" if chain.upper() == "ETH" else "solana"
        wallet = self._get_wallet_by_chain(user_id, chain_db)

        if wallet:
            print(f"encrypted_priv: {wallet['encrypted_priv']}")
            print(f"nonce: {wallet['nonce']}")
            print(f"tag: {wallet['tag']}")
            print(
                f"encrypted_priv length after hex decode: {len(bytes.fromhex(wallet['encrypted_priv'][2:]))}"
            )
            print(
                f"nonce length after hex decode: {len(bytes.fromhex(wallet['nonce'][2:]))}"
            )
            print(
                f"tag length after hex decode: {len(bytes.fromhex(wallet['tag'][2:]))}"
            )
            # Add this to debug
            print(f"MASTER_KEY present: {bool(os.getenv('MASTER_KEY'))}")
            print(
                f"MASTER_KEY length: {len(base64.b64decode(os.getenv('MASTER_KEY'))) if os.getenv('MASTER_KEY') else 0}"
            )


wallet_service = WalletService()
