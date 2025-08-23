# Trading API Documentation

## Overview

The Trading API provides comprehensive endpoints for cryptocurrency and forex trading on the Ostium platform. The API follows a state-managed workflow where you must create a wallet first before performing any trading operations.

## Authentication & Workflow

### Required Workflow
1. **Create Wallet**: Call `/wallet/create` to initialize a wallet
2. **Trade**: Use any trading endpoint - private key is automatically managed
3. **Monitor**: Check positions, balances, and trade history

### State Management
- Private keys are stored in memory state management
- No need to pass private keys in request bodies
- Wallet must be initialized before any trading operations

---

## Wallet Management

### Create New Wallet
**POST** `/wallet/create`

Creates a new wallet with a random private key and stores it in state management.

**Response:**
```json
{
  "address": "0x742d35Cc6634C0532925a3b8D238D2a8a8D8fF7C",
  "private_key": "0x1234567890abcdef..."
}
```

### Import Existing Wallet
**POST** `/wallet/from-private-key`

Imports a wallet from an existing private key.

**Request Body:**
```json
{
  "private_key": "0x1234567890abcdef..."
}
```

**Response:**
```json
{
  "address": "0x742d35Cc6634C0532925a3b8D238D2a8a8D8fF7C",
  "private_key": "0x1234567890abcdef..."
}
```

### Check Wallet Status
**GET** `/wallet/status`

Returns the current wallet initialization status.

**Response:**
```json
{
  "initialized": true,
  "address": "0x742d35Cc6634C0532925a3b8D238D2a8a8D8fF7C",
  "message": "Wallet ready for trading"
}
```

### Clear Wallet
**DELETE** `/wallet/clear`

Clears the wallet from memory state.

**Response:**
```json
{
  "message": "Wallet cleared successfully"
}
```

---

## Trading Operations

### Place Order
**POST** `/trading/place-order`

Places a new trading order (market or limit).

**Request Body:**
```json
{
  "price_from_currency": "BTC",
  "price_to_currency": "USD",
  "collateral": 100.0,
  "leverage": 10,
  "asset_type": 0,
  "direction": true,
  "order_type": "MARKET",
  "take_profit_price": 45000.0,
  "stop_loss_price": 38000.0,
  "trader_address": null,
  "limit_price": null
}
```

**Parameters:**
- `price_from_currency` (string): Base currency (e.g., "BTC", "ETH")
- `price_to_currency` (string): Quote currency (e.g., "USD", "EUR")
- `collateral` (float): Collateral amount in USDC
- `leverage` (int): Leverage multiplier (default: 10)
- `asset_type` (int): Asset type identifier (default: 0)
- `direction` (bool): true for LONG, false for SHORT
- `order_type` (string): "MARKET" or "LIMIT"
- `take_profit_price` (float, optional): Take profit price
- `stop_loss_price` (float, optional): Stop loss price
- `trader_address` (string, optional): Delegated trader address
- `limit_price` (float, optional): Limit price for LIMIT orders

**Response:**
```json
{
  "success": true,
  "tx_hash": "0xabc123...",
  "order_id": "12345",
  "price": 42000.0,
  "pair": "BTC/USD"
}
```

### Close Trade
**POST** `/trading/close-trade`

Closes an existing trading position.

**Request Body:**
```json
{
  "pair_id": "1",
  "trade_index": "0",
  "close_percentage": 100,
  "trader_address": null
}
```

**Parameters:**
- `pair_id` (string): Trading pair ID
- `trade_index` (string): Trade index
- `close_percentage` (int): Percentage to close (1-100, default: 100)
- `trader_address` (string, optional): Delegated trader address

**Response:**
```json
{
  "success": true,
  "tx_hash": "0xdef456...",
  "order_id": "12346",
  "trade_id": "1",
  "pnl": 150.75,
  "order_status": "Processed"
}
```

### Add Collateral
**POST** `/trading/add-collateral`

Adds collateral to an existing trading position.

**Request Body:**
```json
{
  "pair_id": "1",
  "index": "0",
  "collateral": 50.0,
  "trader_address": null
}
```

**Response:**
```json
{
  "success": true,
  "tx_hash": "0xghi789...",
  "pairID": "1",
  "collateral": 50.0
}
```

### Remove Collateral
**POST** `/trading/remove-collateral`

Removes collateral from an existing trading position.

**Request Body:**
```json
{
  "pair_id": "1",
  "trade_index": "0",
  "remove_amount": 25.0
}
```

**Response:**
```json
{
  "success": true,
  "tx_hash": "0xjkl012...",
  "trade_id": "1",
  "amount_removed": 25.0
}
```

### Update Stop Loss
**POST** `/trading/update-stop-loss`

Updates the stop loss price for an existing position.

**Request Body:**
```json
{
  "pair_id": "1",
  "index": "0",
  "stop_loss_price": 39000.0,
  "trader_address": null
}
```

**Response:**
```json
{
  "success": true
}
```

### Update Take Profit
**POST** `/trading/update-take-profit`

Updates the take profit price for an existing position.

**Request Body:**
```json
{
  "pair_id": "1",
  "trade_index": "0",
  "take_profit_price": 46000.0,
  "trader_address": null
}
```

**Response:**
```json
{
  "success": true
}
```

---

## Account Management

### Get Balances
**GET** `/trading/balances?address={address}&refresh={refresh}`

Retrieves wallet balances for ETH and USDC.

**Query Parameters:**
- `address` (string, optional): Wallet address (defaults to current wallet)
- `refresh` (bool, optional): Refresh balance data (default: true)

**Response:**
```json
{
  "eth": 1.5,
  "usdc": 1000.50
}
```

### Request Faucet USDC
**POST** `/trading/faucet`

Requests testnet USDC from the faucet.

**Request Body:**
```json
{
  "address": "0x742d35Cc6634C0532925a3b8D238D2a8a8D8fF7C"
}
```

**Response:**
```json
{
  "success": true,
  "tx_hash": "0xmno345...",
  "amount": 1000.0
}
```

### Set Slippage
**PUT** `/trading/slippage/{slippage_percentage}`

Sets the slippage percentage for trades.

**Path Parameters:**
- `slippage_percentage` (float): Slippage percentage (0-100)

**Response:**
```json
{
  "message": "Slippage percentage set to 1.5%"
}
```

---

## Position Management

### Get Open Positions
**GET** `/trading/positions?address={address}`

Retrieves all open trading positions.

**Query Parameters:**
- `address` (string, optional): Wallet address (defaults to current wallet)

**Response:**
```json
[
  {
    "tradeID": "123",
    "pair": {
      "from": "BTC",
      "to": "USD",
      "id": "1"
    },
    "isBuy": true,
    "leverage": 1000,
    "collateral": "100000000",
    "index": 0,
    "openPrice": "42000.00",
    "currentPrice": "43000.00"
  }
]
```

### Get Trade History
**GET** `/trading/history?address={address}&limit={limit}`

Retrieves recent trading history.

**Query Parameters:**
- `address` (string, optional): Wallet address (defaults to current wallet)
- `limit` (int, optional): Number of trades to return (default: 10)

**Response:**
```json
[
  {
    "tradeID": "123",
    "pair": "BTC/USD",
    "direction": "LONG",
    "openPrice": 42000.0,
    "closePrice": 43000.0,
    "pnl": 150.75,
    "timestamp": "2024-01-15T10:30:00Z"
  }
]
```

### Track Order
**GET** `/trading/track-order/{order_id}`

Tracks the status of a specific order.

**Path Parameters:**
- `order_id` (string): Order ID to track

**Response:**
```json
{
  "orderId": "12345",
  "status": "executed",
  "tradeID": "123",
  "executionPrice": 42150.0,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Error Handling

All endpoints return appropriate HTTP status codes and error messages:

### Common Error Responses

**400 Bad Request** - Invalid request parameters
```json
{
  "detail": "Invalid private key: Invalid private key format"
}
```

**404 Not Found** - Resource not found
```json
{
  "detail": "Order not found"
}
```

**500 Internal Server Error** - Wallet not initialized
```json
{
  "detail": "Wallet not initialized. Please call /wallet/create first."
}
```

**500 Internal Server Error** - Trading operation failed
```json
{
  "detail": "Failed to place order: Insufficient balance"
}
```

---

## Examples

### Complete Trading Workflow

```bash
# 1. Create wallet
curl -X POST "http://localhost:8000/wallet/create"

# 2. Check status
curl -X GET "http://localhost:8000/wallet/status"

# 3. Get testnet USDC
curl -X POST "http://localhost:8000/trading/faucet" \
  -H "Content-Type: application/json" \
  -d '{"address": "0x742d35Cc6634C0532925a3b8D238D2a8a8D8fF7C"}'

# 4. Check balances
curl -X GET "http://localhost:8000/trading/balances"

# 5. Place a long BTC/USD order
curl -X POST "http://localhost:8000/trading/place-order" \
  -H "Content-Type: application/json" \
  -d '{
    "price_from_currency": "BTC",
    "price_to_currency": "USD",
    "collateral": 100.0,
    "leverage": 10,
    "direction": true,
    "order_type": "MARKET"
  }'

# 6. Check positions
curl -X GET "http://localhost:8000/trading/positions"

# 7. Close position (if needed)
curl -X POST "http://localhost:8000/trading/close-trade" \
  -H "Content-Type: application/json" \
  -d '{
    "pair_id": "1",
    "trade_index": "0",
    "close_percentage": 100
  }'
```

---

## Rate Limits

No explicit rate limits are enforced by the API, but blockchain transaction limits may apply based on network conditions.

## Support

For technical support or questions about the Trading API, please refer to the main application documentation or contact the development team.

---

*Last updated: January 2024*