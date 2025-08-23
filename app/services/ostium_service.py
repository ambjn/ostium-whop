import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from eth_account import Account
from ostium_python_sdk import NetworkConfig, OstiumSDK

from app.utils.order_type import ORDER_TYPE

logger = logging.getLogger(__name__)
load_dotenv()


class OstiumService:
    def __init__(
        self,
        private_key: Optional[str] = None,
        verbose: bool = True,
        network_config: NetworkConfig = NetworkConfig.testnet(),
    ) -> None:
        self.verbose = verbose
        self.network_config = network_config
        self.logger = logger
        self.private_key = private_key
        self.address: Optional[str] = None
        self.rpc_url: str
        self.trader_address: Optional[str] = None
        self.account: Optional[Account] = None
        self.sdk: Optional[OstiumSDK] = None

        self._initialize_rpc()
        
        if self.private_key:
            self._initialize_wallet()
            self._initialize_sdk()
        else:
            self.logger.info("Initialized without private key - wallet operations not available")

    def _initialize_wallet(self) -> None:
        """Initialize wallet from private key."""
        if not self.private_key:
            raise ValueError("Private key is required for wallet operations")
            
        self.account = Account.from_key(self.private_key)
        self.address = self.account.address
            
        # Optional trader address for delegation
        self.trader_address = os.environ.get("TRADER_ADDRESS")

    def _patch_signed_transaction(self) -> None:
        """Monkey patch SignedTransaction to add raw_transaction property."""
        try:
            from eth_account.datastructures import SignedTransaction

            if not hasattr(SignedTransaction, 'raw_transaction'):
                def raw_transaction_property(self):
                    return getattr(self, 'rawTransaction', None)

                SignedTransaction.raw_transaction = property(raw_transaction_property)
                self.logger.info("Applied SignedTransaction compatibility patch")

        except Exception as e:
            self.logger.warning("Failed to apply SignedTransaction patch: %s", e)

    def _initialize_rpc(self) -> None:
        """Initialize RPC URL from environment."""
        self.rpc_url = os.environ.get("RPC_URL")
        if not self.rpc_url:
            raise ValueError("Missing RPC_URL environment variable")

    def _initialize_sdk(self) -> None:
        """Initialize Ostium SDK with private key."""
        if not self.private_key:
            raise ValueError("Private key is required for SDK initialization")

        try:
            self._patch_signed_transaction()

            self.sdk = OstiumSDK(
                network=self.network_config,
                private_key=self.private_key,
                rpc_url=self.rpc_url,
                verbose=self.verbose,
            )

            if self.verbose:
                self.check_rpc_status()

        except Exception as e:
            self.logger.error("Failed to initialize Ostium SDK: %s", e)
            raise

    def _require_sdk(self) -> None:
        """Ensure SDK is initialized for wallet operations."""
        if not self.sdk:
            raise ValueError("SDK not initialized - private key required for this operation")
    
    def _require_wallet(self) -> None:
        """Ensure wallet is initialized for wallet operations."""
        if not self.account or not self.address:
            raise ValueError("Wallet not initialized - private key required for this operation")

    def check_rpc_status(self) -> Optional[int]:
        try:
            block = self.get_block_number()
            if block is not None and self.verbose:
                self.logger.info("📦 Latest block: %s", block)
            return block
        except Exception as e:
            self.logger.error("❌ RPC check failed: %s", e)
            return None

    def get_block_number(self) -> Optional[int]:
        try:
            if not self.sdk:
                return None
            return self.sdk.w3.eth.get_block_number()
        except Exception as e:
            self.logger.error("Failed to get block number: %s", e)
            return None

    def is_healthy(self) -> bool:
        try:
            return self.check_rpc_status() is not None
        except Exception as e:
            self.logger.error("Health check failed: %s", e)
            return False

    async def get_faucet_usdc(self, address: str) -> Dict[str, Any]:
        if not address:
            return {"success": False, "error": "Address is required"}

        try:
            self._require_sdk()
            if self.sdk.faucet.can_request_tokens(address):
                amount = self.sdk.faucet.get_token_amount()
                self.logger.info("Eligible to receive %s USDC", amount / 1e6)

                receipt = self.sdk.faucet.request_tokens()
                self.logger.info("Tokens requested successfully")
                self.logger.info(
                    "Transaction hash: %s", receipt["transactionHash"].hex()
                )

                return {
                    "success": True,
                    "tx_hash": receipt["transactionHash"].hex(),
                    "amount": amount / 1e6,
                }
            else:
                next_time = self.sdk.faucet.get_next_request_time(address)
                next_time_str = datetime.fromtimestamp(next_time).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                self.logger.warning(
                    "Cannot request tokens yet. Try again at %s", next_time_str
                )
                return {"success": False, "next_request_time": next_time_str}

        except Exception as e:
            self.logger.error("Failed to request USDC from faucet: %s", e)
            return {"success": False, "error": str(e)}

    async def get_balances(
        self, address: str, refresh: bool = True
    ) -> Dict[str, float]:
        if not address:
            self.logger.error("Address is required for balance check")
            return {"eth": 0.0, "usdc": 0.0}

        try:
            self._require_sdk()
            eth_balance, usdc_balance = self.sdk.balance.get_balance(
                address=address, refresh=refresh
            )
            return {"eth": eth_balance, "usdc": usdc_balance}
        except Exception as e:
            self.logger.error("Failed to get balances for %s: %s", address, e)
            return {"eth": 0.0, "usdc": 0.0}

    async def get_latest_prices(self) -> Optional[List[Dict[str, Any]]]:
        try:
            if not self.sdk:
                self.logger.warning("SDK not initialized - attempting to create temporary SDK")
                temp_service = OstiumService(private_key="0x" + "0" * 64)
                return await temp_service.get_latest_prices()
            return await self.sdk.price.get_latest_prices()
        except Exception as e:
            self.logger.error("Failed to get latest prices: %s", e)
            return None

    async def get_price(
        self, from_currency: str, to_currency: str
    ) -> Optional[Dict[str, Any]]:
        if not from_currency or not to_currency:
            self.logger.error("Both from_currency and to_currency are required")
            return None

        try:
            if not self.sdk:
                self.logger.warning("SDK not initialized - attempting to create temporary SDK")
                temp_service = OstiumService(private_key="0x" + "0" * 64)
                return await temp_service.get_price(from_currency, to_currency)
            
            price, is_open, timestamp = await self.sdk.price.get_price(
                from_currency, to_currency
            )
            return {
                "price": price,
                "is_open": is_open,
                "timestamp": timestamp,
                "pair": f"{from_currency}/{to_currency}",
            }
        except Exception as e:
            self.logger.error(
                "Failed to get price for %s/%s: %s", from_currency, to_currency, e
            )
            return None

    async def get_pair_info(self) -> List[Dict[str, Any]]:
        try:
            if not self.sdk:
                self.logger.warning("SDK not initialized - attempting to create temporary SDK")
                temp_service = OstiumService(private_key="0x" + "0" * 64)
                return await temp_service.get_pair_info()
            return await self.sdk.subgraph.get_pairs()
        except Exception as e:
            self.logger.error("Failed to get pair info: %s", e)
            return []

    async def get_formatted_pairs_details(self) -> List[Dict[str, Any]]:
        try:
            if not self.sdk:
                self.logger.warning("SDK not initialized - attempting to create temporary SDK")
                temp_service = OstiumService(private_key="0x" + "0" * 64)
                return await temp_service.get_formatted_pairs_details()
            return await self.sdk.get_formatted_pairs_details()
        except Exception as e:
            self.logger.error("Failed to get formatted pair details: %s", e)
            return []

    def set_slippage_percentage(self, slippage_percentage: float) -> None:
        if slippage_percentage < 0 or slippage_percentage > 100:
            self.logger.warning("Slippage percentage should be between 0 and 100")

        self.sdk.ostium.set_slippage_percentage(slippage_percentage)
        self.logger.info("Slippage percentage set to: %.2f%%", slippage_percentage)

    async def place_order(
        self,
        price_from_currency: str,
        price_to_currency: str,
        collateral: float,
        leverage: int = 10,
        asset_type: int = 0,
        direction: bool = True,
        order_type: ORDER_TYPE = ORDER_TYPE.MARKET,
        take_profit_price: Optional[float] = 0,
        stop_loss_price: Optional[float] = 0,
        trader_address: Optional[str] = None,
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not price_from_currency or not price_to_currency:
            return {"success": False, "error": "Currency pair is required"}

        if collateral <= 0:
            return {"success": False, "error": "Collateral must be positive"}

        if leverage <= 0:
            return {"success": False, "error": "Leverage must be positive"}

        self.logger.info(
            "Placing %s order: %s/%s, collateral: %.2f USDC, leverage: %dx",
            "LONG" if direction else "SHORT",
            price_from_currency,
            price_to_currency,
            collateral,
            leverage,
        )

        trade_params = {
            "collateral": collateral,
            "leverage": leverage,
            "asset_type": asset_type,
            "direction": direction,
            "order_type": order_type.value if hasattr(order_type, 'value') else order_type,
            "tp": take_profit_price or 0,
            "sl": stop_loss_price or 0,
        }

        if trader_address or self.trader_address:
            trade_params["trader"] = trader_address or self.trader_address
            self.logger.info("Using delegated trading for: %s", trade_params["trader"])

        try:
            latest_price, _, _ = await self.sdk.price.get_price(
                price_from_currency, price_to_currency
            )

            self.logger.info(
                "Current %s/%s price: %.2f",
                price_from_currency,
                price_to_currency,
                latest_price,
            )

            execution_price = limit_price if order_type == ORDER_TYPE.LIMIT and limit_price else latest_price

            trade_result = self.sdk.ostium.perform_trade(
                trade_params, at_price=execution_price
            )

            receipt = trade_result["receipt"]
            order_id = trade_result["order_id"]

            self.logger.info("Order placed successfully!")

            self.logger.info("Transaction hash: %s", receipt["transactionHash"].hex())
            self.logger.info("Order ID: %s", order_id)

            trade_summary = await self.trade_data_points(
                from_currency=price_from_currency,
                to_currency=price_to_currency,
                collateral=collateral,
                leverage=leverage,
                direction=direction
            )

            self.logger.info("Trade Summary: %s", trade_summary)

            return {
                "success": True,
                "tx_hash": receipt["transactionHash"].hex(),
                "order_id": order_id,
                "price": latest_price,
                "pair": f"{price_from_currency}/{price_to_currency}",
            }

        except Exception as e:
            self.logger.error("Failed to place order: %s", e)
            return {"success": False, "error": str(e)}

    async def track_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        if not order_id:
            self.logger.error("Order ID is required for tracking")
            return None

        try:
            order_status = await self.sdk.subgraph.get_orders(order_id)
            self.logger.info("Order %s status retrieved", order_id)
            return order_status
        except Exception as e:
            self.logger.error("Failed to track order %s: %s", order_id, e)
            return None

    async def get_recent_history(
        self, address: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        target_address = address or self.address

        if limit <= 0:
            self.logger.warning("Limit must be positive, using default of 10")
            limit = 10

        try:
            return await self.sdk.subgraph.get_recent_history(target_address, limit)
        except Exception as e:
            self.logger.error(
                "Failed to get trade history for %s: %s", target_address, e
            )
            return []

    async def get_open_positions(self, address: Optional[str] = None) -> List[Dict[str, Any]]:
        target_address = address or self.address

        try:
            trades = await self.sdk.subgraph.get_open_trades(target_address)
            return trades
        except Exception as e:
            self.logger.error(
                "Failed to get open positions for %s: %s", target_address, e
            )
            return []

    async def close_trade(
        self,
        pair_id: Any,
        trade_index: Any,
        close_percentage: int = 100,
        trader_address: Optional[Any] = None,
    ) -> Dict[str, Any]:
        if not pair_id:
            return {"success": False, "error": "Trade ID is required"}

        try:
            positions = await self.get_open_positions()
            position_exists = False
            actual_pair_id = None
            actual_trade_index = None

            for pos in positions:
                pos_trade_id = str(pos.get("tradeID", ""))
                pos_pair_id = str(pos.get("pairId", ""))
                pair_info = pos.get("pair", {})
                nested_pair_id = str(pair_info.get("id", ""))

                if (pos_trade_id == str(pair_id) or
                    pos_pair_id == str(pair_id) or
                    nested_pair_id == str(pair_id)):
                    position_exists = True
                    actual_pair_id = nested_pair_id or pos.get("pairId", pair_id)
                    actual_trade_index = pos.get("index", trade_index)
                    self.logger.info("Found position - pair.id: %s, index: %s", actual_pair_id, actual_trade_index)
                    break

            if not position_exists:
                return {"success": False, "error": f"Position with ID {pair_id} not found or already closed"}

            if actual_pair_id is not None:
                pair_id = actual_pair_id
            if actual_trade_index is not None:
                trade_index = actual_trade_index

        except Exception as e:
            self.logger.warning("Could not validate position existence: %s", e)

        try:
            self.logger.info("Closing trade - pair_id: %s, trade_index: %s, close_percentage: %s",
                             pair_id, trade_index, close_percentage)

            pair_id_uint16 = min(max(int(pair_id) if pair_id is not None else 0, 0), 65535)
            trade_index_uint8 = min(max(int(trade_index) if trade_index is not None else 0, 0), 255)
            close_percentage_uint16 = min(max(int(close_percentage) if close_percentage is not None else 100, 0), 65535)

            self.logger.info("Converted arguments - pair_id: %s, trade_index: %s, close_percentage: %s",
                             pair_id_uint16, trade_index_uint8, close_percentage_uint16)

            close_result = self.sdk.ostium.close_trade(
                pair_id_uint16, trade_index_uint8, close_percentage_uint16
            )
            receipt = close_result["receipt"]
            order_id = close_result["order_id"]

            if not order_id:
                self.logger.error("Failed to get order ID from close trade transaction")
                return {"success": False, "error": "Failed to get order ID"}

            self.logger.info("Trade close order submitted with order ID: %s", order_id)
            self.logger.info("Transaction hash: %s", receipt["transactionHash"].hex())

            self.logger.info("Tracking order status...")

            result = await self.sdk.ostium.track_order_and_trade(self.sdk.subgraph, order_id)
            if result and result.get('order'):
                order = result['order']
                trade_id = result['order']['tradeID']

                pnl = 0.0
                if 'profitPercent' in order:
                    pnl = float(order.get('profitPercent', 0))
                elif 'amountSentToTrader' in order:
                    pnl = float(order.get('amountSentToTrader', 0))

                success_result = {
                    "success": True,
                    "tx_hash": receipt["transactionHash"].hex(),
                    "order_id": order_id,
                    "trade_id": trade_id,
                    "pnl": pnl,
                    "order_status": "Processed" if not order.get('isPending', True) else "Pending",
                    "cancelled": order.get('isCancelled', False),
                }

                if order.get('isCancelled', False):
                    success_result["cancel_reason"] = order.get('cancelReason', 'Unknown')
                    success_result["success"] = False
                    success_result["error"] = f"Order cancelled: {order.get('cancelReason', 'Unknown')}"
                else:
                    close_datapoints = await self.close_trade_datapoints(trade_data=result)
                    self.logger.info("Close Trade Datapoints: %s", close_datapoints)

                return success_result
            else:
                return {
                    "success": True,
                    "tx_hash": receipt["transactionHash"].hex(),
                    "order_id": order_id,
                    "trade_id": pair_id,
                    "note": "Order submitted successfully, but tracking failed"
                }
        except Exception as e:
            self.logger.error("Failed to close trade %s: %s", pair_id, e)
            return {"success": False, "error": str(e)}

    async def add_collateral(
        self,
        pairID: Any,
        index: Any,
        collateral: Any,
        trader_address: Optional[Any] = None,
    ):
        if not pairID:
            return {"success": False, "error": "Trade ID is required"}

        if collateral <= 0:
            return {"success": False, "error": "Collateral amount must be positive"}

        try:
            self.logger.info(
                "Adding %.2f USDC collateral to trade: %s", collateral, pairID
            )

            result = self.sdk.ostium.add_collateral(
                pairID=pairID,
                index=index,
                collateral=collateral,
                trader_address=trader_address,
            )
            receipt = result["receipt"]

            self.logger.info("Collateral added successfully!")
            self.logger.info("Transaction hash: %s", receipt["transactionHash"].hex())

            return {
                "success": True,
                "tx_hash": receipt["transactionHash"].hex(),
                "pairID": pairID,
                "collateral": collateral,
            }
        except Exception as e:
            self.logger.error("Failed to add collateral to trade %s: %s", pairID, e)
            return {"success": False, "error": str(e)}

    async def remove_collateral(
        self, pair_id: Any, trade_index: Any, remove_amount: Any
    ):
        if not pair_id:
            return {"success": False, "error": "Trade ID is required"}

        if remove_amount <= 0:
            return {"success": False, "error": "Collateral amount must be positive"}

        try:
            self.logger.info(
                "Removing %.2f USDC collateral from trade: %s", remove_amount, pair_id
            )

            result = await self.sdk.ostium.remove_collateral(
                pair_id=pair_id, trade_index=trade_index, remove_amount=remove_amount
            )
            receipt = result["receipt"]

            self.logger.info("Collateral removed successfully!")
            self.logger.info("Transaction hash: %s", receipt["transactionHash"].hex())

            return {
                "success": True,
                "tx_hash": receipt["transactionHash"].hex(),
                "trade_id": pair_id,
                "amount_removed": remove_amount,
            }
        except Exception as e:
            self.logger.error(
                "Failed to remove collateral from trade %s: %s", pair_id, e
            )
            return {"success": False, "error": str(e)}

    async def bot_get_balances(self, user_id: Optional[str] = None) -> str:
        try:
            address = self.address
            balances = await self.get_balances(address)

            return (
                f"💰 **Your Balances**\\n"
                f"ETH: {balances['eth']:.6f} ETH\\n"
                f"USDC: {balances['usdc']:.2f} USDC"
            )

        except Exception as e:
            return f"❌ Failed to get balances: {str(e)}"

    async def bot_get_positions(self, user_id: Optional[str] = None) -> str:
        try:
            positions = await self.get_open_positions()

            if not positions:
                return "📊 No open positions found"

            result = "📊 **Your Open Positions**\\n"

            currency_emojis = {
                "AUD": "🇦🇺",
                "EUR": "🇪🇺",
                "GBP": "🇬🇧",
                "NZD": "🇳🇿",
                "USD": "💵",
                "CAD": "🇨🇦",
                "CHF": "🇨🇭",
                "JPY": "🇯🇵",
                "MXN": "🇲🇽",
                "BTC": "₿",
                "ETH": "Ξ",
                "SOL": "◎",
                "CL": "🛢️",
                "HG": "🟫",
                "XAG": "🥈",
                "XAU": "🥇",
                "XPD": "💎",
                "XPT": "🥉",
                "DAX": "🇩🇪",
                "DJI": "🏛️",
                "FTSE": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
                "HSI": "🇭🇰",
                "NDX": "💻",
                "NIK": "🗾",
                "SPX": "📈",
                "AAPL": "🍎",
                "AMZN": "📦",
                "BABA": "🛒",
                "BYD": "🔋",
                "CRCL": "⭕",
                "GOOG": "🔍",
                "HOOD": "🏹",
                "META": "📘",
                "MSFT": "🪟",
                "NVDA": "🔥",
                "TSLA": "⚡",
            }

            for i, pos in enumerate(positions, 1):
                direction = "🟢 LONG" if pos.get("isBuy") else "🔴 SHORT"
                from_currency = pos["pair"]["from"]
                to_currency = pos["pair"]["to"]
                pair_emoji = currency_emojis.get(from_currency, "💹")
                pair = f"{from_currency}/{to_currency}"

                try:
                    leverage_val = float(pos.get('leverage', 0)) / 100
                    leverage = f"{leverage_val:.1f}x"
                except (ValueError, TypeError):
                    leverage = f"{pos.get('leverage', 'N/A')}x"

                try:
                    collateral_val = float(pos.get('collateral', 0)) / 1e6
                    collateral = f"{collateral_val:.2f} USDC"
                except (ValueError, TypeError):
                    collateral = f"{pos.get('collateral', 'N/A')} USDC"

                result += f"{i}. {pair_emoji} {direction} {pair} {leverage}\\n"
                result += f"   💵 Collateral: {collateral}\\n"
                result += f"   🆔 Trade ID: {pos.get('tradeID', 'N/A')}\\n"

            return result

        except Exception as e:
            return f"❌ Failed to get positions: {str(e)}"

    async def bot_get_prices(self, pair: Optional[str] = None) -> str:
        try:
            if pair:
                from_curr, to_curr = pair.split("/")
                price_data = await self.get_price(from_curr, to_curr)

                if not price_data:
                    return f"❌ Could not get price for {pair}"

                status = "🟢 OPEN" if price_data["is_open"] else "🔴 CLOSED"
                return (
                    f"💹 **{pair}**\\n"
                    f"Price: ${price_data['price']:,.2f}\\n"
                    f"Market: {status}"
                )
            else:
                prices = await self.get_latest_prices()

                if not prices:
                    return "❌ Could not get latest prices"

                result = "💹 **Latest Prices**\\n"

                for price_data in prices[:10]:
                    pair_name = f"{price_data['from']}/{price_data['to']}"
                    price, is_open, _ = await self.sdk.price.get_price(
                        price_data["from"], price_data["to"]
                    )
                    status = "🟢" if is_open else "🔴"
                    result += f"{status} {pair_name}: ${price:,.2f}\\n"

                return result

        except Exception as e:
            return f"❌ Failed to get prices: {str(e)}"

    def update_stop_loss(
        self,
        pair_id,
        index,
        stop_loss_price: float,
        trader_address: Optional[str] = None,
    ) -> bool:
        try:
            address = trader_address or self.trader_address or self.address
            return self.sdk.ostium.update_sl(
                pairID=pair_id,
                index=index,
                sl=stop_loss_price,
                trader_address=address,
            )
        except Exception as e:
            self.logger.error("Stop loss update failed: %s", e)
            return False

    def update_take_profit(
        self,
        pair_id,
        trade_index,
        take_profit_price: float,
        trader_address: Optional[str] = None,
    ) -> bool:
        try:
            address = trader_address or self.trader_address or self.address
            return self.sdk.ostium.update_tp(
                pair_id=pair_id,
                trade_index=trade_index,
                tp_price=take_profit_price,
                trader_address=address,
            )
        except Exception as e:
            self.logger.error("Take profit update failed: %s", e)
            return False

    def update_limit_order(
        self,
        pair_id,
        index,
        price,
        take_profit_price: float,
        set_loss_price: float,
    ) -> bool:
        try:
            return self.sdk.ostium.update_limit_order(
                pair_id=pair_id,
                index=index,
                pvt_key=self.private_key,
                price=price,
                tp=take_profit_price,
                sl=set_loss_price,
            )
        except Exception as e:
            self.logger.error("Limit order update failed: %s", e)
            return False

    def get_network_info(self) -> Dict[str, Any]:
        return {
            "network": (
                "testnet"
                if self.network_config == NetworkConfig.testnet()
                else "mainnet"
            ),
            "rpc_url": self.rpc_url,
            "address": self.address or "Not initialized",
            "delegation_enabled": self.trader_address is not None,
            "trader_address": self.trader_address,
            "wallet_initialized": self.address is not None,
        }

    async def trade_data_points(
        self,
        from_currency: str,
        to_currency: str,
        collateral: float,
        leverage: int,
        direction: bool
    ) -> Optional[Dict[str, Any]]:
        try:
            price_data = await self.get_price(from_currency, to_currency)
            if not price_data:
                return {
                    "success": False,
                    "error": f"Could not fetch current price for {from_currency}/{to_currency}",
                }

            price = float(price_data.get("price", 0))
            position_size = collateral * leverage

            if direction:  # Long
                liquidation_price = price * (1 - 1 / leverage)
            else:  # Short
                liquidation_price = price * (1 + 1 / leverage)

            return {
                "entry": round(price, 2),
                "size": round(position_size, 2),
                "liquidation": round(liquidation_price, 2),
                "direction": "LONG" if direction else "SHORT",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close_trade_datapoints(
        self,
        trade_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        try:
            trade = trade_data.get("trade", {})
            order = trade_data.get("order", {})

            trade_id = str(trade.get("tradeID") or order.get("tradeID"))
            entry_price = float(trade.get("openPrice", 0))
            close_price = float(trade.get("closePrice", 0))
            collateral = float(trade.get("collateral", 0))
            leverage = float(trade.get("leverage", 0))
            direction = bool(trade.get("isBuy", False))
            from_currency = trade.get("pair", {}).get("from", "")
            to_currency = trade.get("pair", {}).get("to", "")

            if not from_currency or not to_currency:
                return {
                    "success": False,
                    "error": "Missing currency pair information",
                }

            if not trade.get("isOpen", True):
                profit_loss_percentage = float(order.get("profitPercent") or trade.get("profitPercent") or 0)
                profit_loss = (profit_loss_percentage / 100.0) * collateral

                return {
                    "tradeID": trade_id,
                    "entry": round(entry_price, 2),
                    "exit_price": round(close_price, 2),
                    "current_price": round(close_price, 2),
                    "size": round(collateral * leverage, 2),
                    "liquidation": None,
                    "direction": "LONG" if direction else "SHORT",
                    "profit_loss": round(profit_loss, 2),
                    "profit_loss_percentage": round(profit_loss_percentage, 2),
                    "amount_sent_to_trader": float(order.get("amountSentToTrader", 0)),
                    "fees": {
                        "fundingFee": float(order.get("fundingFee", 0)),
                        "rolloverFee": float(order.get("rolloverFee", 0)),
                        "liquidationFee": float(order.get("liquidationFee", 0)),
                    },
                    "closed": True,
                    "success": True,
                }

            price_data = await self.get_price(from_currency, to_currency)
            if not price_data:
                return {
                    "success": False,
                    "error": f"Could not fetch current price for {from_currency}/{to_currency}",
                }

            exit_price = float(price_data.get("price", 0))
            position_size = collateral * leverage

            if leverage > 0:
                liquidation_price = (
                    entry_price * (1 - 0.9 / leverage)
                    if direction else entry_price * (1 + 0.9 / leverage)
                )
            else:
                liquidation_price = entry_price

            if direction:  # Long
                profit_loss = (exit_price - entry_price) / entry_price * position_size
            else:  # Short
                profit_loss = (entry_price - exit_price) / entry_price * position_size

            profit_loss_percentage = (profit_loss / collateral) * 100 if collateral > 0 else 0

            return {
                "tradeID": trade_id,
                "entry": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "current_price": round(exit_price, 2),
                "size": round(position_size, 2),
                "liquidation": round(liquidation_price, 2),
                "direction": "LONG" if direction else "SHORT",
                "profit_loss": round(profit_loss, 2),
                "profit_loss_percentage": round(profit_loss_percentage, 2),
                "closed": False,
                "success": True,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
