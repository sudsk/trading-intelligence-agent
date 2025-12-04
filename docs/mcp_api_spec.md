# MCP Server API Specification

## Overview
The Model Context Protocol (MCP) servers in this project expose a **Tool Calling Interface** over HTTP. Unlike standard REST APIs that expose resources (e.g., `GET /users/1`), these servers expose *functions* (tools) that can be called by agents.

## Base Protocol
All MCP servers follow this common interface:

### 1. Call Tool
**Endpoint**: `POST /call_tool`
**Description**: Execute a specific tool.

**Request Body**:
```json
{
  "tool_name": "string",
  "arguments": {
    "arg1": "value1",
    "arg2": "value2"
  }
}
```

**Response Body**:
```json
{
  "result": {
    "key": "value"
  },
  "error": null
}
```

### 2. List Tools
**Endpoint**: `GET /tools`
**Description**: Returns a list of available tools and their descriptions.

### 3. Health Check
**Endpoint**: `GET /health`
**Description**: Returns service health status.

---

## Service Definitions

### 1. Trade MCP Server
**Port**: 3001

#### `get_client_trades`
Get historical trades for a client.
- **Arguments**:
  - `client_id` (str): Client identifier
  - `days` (int, optional): Lookback period (default: 30)
- **Returns**: `{'trades': [List of trade objects]}`

#### `get_open_positions`
Get currently open positions.
- **Arguments**:
  - `client_id` (str): Client identifier
- **Returns**: `{'positions': [List of position objects]}`

### 2. Risk MCP Server
**Port**: 3002

#### `get_client_positions`
Get current positions (risk view).
- **Arguments**:
  - `client_id` (str): Client identifier
- **Returns**: `{'positions': [List of position objects]}`

#### `get_risk_metrics`
Get calculated risk metrics (VaR, leverage, etc.).
- **Arguments**:
  - `client_id` (str): Client identifier
- **Returns**: `{'metrics': {Map of metric names to values}}`

#### `get_features`
Get behavioral features for segmentation.
- **Arguments**:
  - `client_id` (str): Client identifier
  - `days` (int, optional): Lookback days (default: 90)
- **Returns**: `{'features': {Map of feature names to values}}`

### 3. Market MCP Server
**Port**: 3003

#### `get_market_bars`
Get historical OHLCV data.
- **Arguments**:
  - `instruments` (List[str]): List of symbols (e.g., ["EURUSD", "GBPUSD"])
  - `start_date` (str, optional): ISO date string
  - `end_date` (str, optional): ISO date string
- **Returns**: `{'bars': [List of bar objects], 'count': int}`

#### `get_current_prices`
Get latest market prices.
- **Arguments**:
  - `instruments` (List[str]): List of symbols
- **Returns**: `{'prices': {symbol: price}}`

#### `get_correlations`
Get correlation matrix for instruments.
- **Arguments**:
  - `instruments` (List[str]): List of symbols
  - `days` (int, optional): Lookback days (default: 30)
- **Returns**: `{'correlations': {symbol1: {symbol2: correlation}}}`

### 4. News MCP Server
**Port**: 3004

#### `get_headlines`
Get financial news headlines.
- **Arguments**:
  - `instruments` (List[str]): List of related symbols
  - `hours` (int, optional): Lookback hours (default: 72)
- **Returns**: `{'headlines': [List of headline objects], 'count': int}`

#### `get_sentiment`
Get specific sentiment analysis for headlines.
- **Arguments**:
  - `headline_ids` (List[str]): List of headline IDs
- **Returns**: `{'sentiments': {headline_id: {sentiment, score}}}`

#### `get_macro_events`
Get upcoming economic calendar events.
- **Arguments**:
  - `days` (int, optional): Days ahead (default: 7)
- **Returns**: `{'events': [List of event objects]}`

### 5. Client MCP Server
**Port**: 3005

#### `list_clients`
Search and filter clients.
- **Arguments**:
  - `search` (str, optional): Search by name or ID
  - `segment` (str, optional): Filter by segment
  - `rm` (str, optional): Filter by Relationship Manager
- **Returns**: `{'clients': [List of client objects]}`

#### `get_client_metadata`
Get detailed client profile.
- **Arguments**:
  - `client_id` (str): Client identifier
- **Returns**: `{'client': {Client object}}`

#### `log_action`
Log a CRM action for a client.
- **Arguments**:
  - `client_id` (str): Client identifier
  - `action_type` (str): Type of action
  - `title` (str): Action title
  - `description` (str, optional): Details
- **Returns**: `{'action_id': str, 'status': str}`
