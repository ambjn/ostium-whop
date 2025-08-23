import secrets
from eth_account import Account


class WalletService:

    @staticmethod
    def create_wallet():
        private_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(private_key)
        return {"address": account.address, "private_key": private_key}

    @staticmethod
    def get_wallet_from_private_key(private_key: str):
        account = Account.from_key(private_key)
        return {"address": account.address, "private_key": private_key}
