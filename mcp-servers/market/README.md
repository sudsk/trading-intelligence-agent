\# Trade MCP Server



Mock MCP server for demo/PoC that returns trade data from CSV files.



\## Quick Start



```bash

\# Install dependencies

pip install -r requirements.txt



\# Run server

python server.py

\# Server starts on http://localhost:3001

```



\## With Docker



```bash

\# Build

docker build -t trade-mcp .



\# Run

docker run -p 3001:8080 trade-mcp

```



\## Tools Available



\- `get\_client\_trades` - Get individual trades

\- `get\_trade\_summary` - Get aggregated statistics

\- `get\_position\_flips` - Count direction reversals



\## Test



```bash

\# Health check

curl http://localhost:3001/health



\# List tools

curl http://localhost:3001/tools



\# Call tool

curl -X POST http://localhost:3001/call\_tool \\

&nbsp; -H "Content-Type: application/json" \\

&nbsp; -d '{

&nbsp;   "tool\_name": "get\_trade\_summary",

&nbsp;   "arguments": {"client\_id": "ACME\_FX\_023", "days": 90}

&nbsp; }'

```



\## Production



In production, replace CSV reading with Oracle OMS queries. The MCP interface stays the same!

