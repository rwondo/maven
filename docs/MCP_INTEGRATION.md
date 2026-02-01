# MCP Server Integration Guide

This guide explains how to integrate custom MCP (Model Context Protocol) servers with MAVEN, allowing the hallucination detection models to use external tools for verification.

## What is MCP?

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open protocol that standardizes how AI applications connect to external data sources and tools. MAVEN supports MCP servers to enhance hallucination detection with real-world verification.

## Why Use MCP with MAVEN?

When MAVEN's models verify an AI response, they can use MCP tools to:

- **Verify facts** via Wikipedia, knowledge bases, or custom databases
- **Check calculations** using calculator tools
- **Validate citations** by searching academic databases
- **Cross-reference data** against authoritative sources

This transforms hallucination detection from pure LLM reasoning to **grounded verification**.

## Quick Start

```python
from maven import HallucinationDetector

# Initialize with MCP servers
detector = HallucinationDetector(
    models=["together/llama-3.1-8b", "together/qwen-2.5-7b"],
    mcp_servers=[
        {
            "name": "wikipedia",
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-wikipedia"]
        }
    ]
)

# Models can now use Wikipedia to verify facts
report = detector.detect(
    query="When was the Eiffel Tower built?",
    answer="The Eiffel Tower was completed in 1889.",
    domain="general"
)
```

## MCP Server Types

MAVEN supports two types of MCP servers:

### 1. Stdio Servers (Recommended)

Stdio servers communicate via stdin/stdout using JSON-RPC. Most MCP servers use this pattern.

```python
mcp_servers=[
    {
        "name": "wikipedia",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-wikipedia"]
    }
]
```

**Configuration Options:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique identifier for the server |
| `type` | string | Yes | Must be `"stdio"` |
| `command` | string | Yes | Command to start the server |
| `args` | list | No | Command-line arguments |
| `env` | dict | No | Environment variables |

### 2. HTTP Servers

HTTP servers expose a REST API for tool calls.

```python
mcp_servers=[
    {
        "name": "my-api",
        "type": "http",
        "url": "http://localhost:8080",
        "api_key": "your-api-key"  # Optional
    }
]
```

**Configuration Options:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique identifier for the server |
| `type` | string | Yes | Must be `"http"` |
| `url` | string | Yes | Base URL of the HTTP server |
| `api_key` | string | No | API key for authentication |
| `headers` | dict | No | Additional HTTP headers |

## Available MCP Servers

### Official MCP Servers

```python
# Wikipedia - Fact verification
{
    "name": "wikipedia",
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-wikipedia"]
}

# Brave Search - Web search
{
    "name": "brave-search",
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@anthropic/server-brave-search"],
    "env": {"BRAVE_API_KEY": "your-key"}
}

# Filesystem - Read local files
{
    "name": "filesystem",
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
}
```

### Community MCP Servers

Find more at [MCP Servers Directory](https://github.com/modelcontextprotocol/servers).

## Building a Custom MCP Server

### Python Example

Create a custom MCP server for your domain-specific verification needs:

```python
# my_verification_server.py
import json
import sys

def handle_request(request):
    """Handle incoming MCP requests."""
    method = request.get("method")
    params = request.get("params", {})

    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "verify_medical_claim",
                    "description": "Verify a medical claim against trusted sources",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "claim": {"type": "string", "description": "The medical claim to verify"}
                        },
                        "required": ["claim"]
                    }
                }
            ]
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "verify_medical_claim":
            claim = arguments.get("claim", "")
            # Your verification logic here
            result = verify_against_medical_database(claim)
            return {"content": [{"type": "text", "text": result}]}

    return {"error": "Unknown method"}

def verify_against_medical_database(claim):
    """Your custom verification logic."""
    # Connect to your medical database, API, etc.
    # Return verification result
    return f"Verification result for: {claim}"

def main():
    """Main loop for stdio MCP server."""
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = handle_request(request)
            response["id"] = request.get("id")
            print(json.dumps(response), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)

if __name__ == "__main__":
    main()
```

Use it with MAVEN:

```python
detector = HallucinationDetector(
    models=["together/llama-3.1-8b", "together/qwen-2.5-7b"],
    mcp_servers=[
        {
            "name": "medical-verifier",
            "type": "stdio",
            "command": "python",
            "args": ["my_verification_server.py"]
        }
    ]
)
```

### HTTP Server Example

```python
# my_http_server.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/tools", methods=["GET"])
def list_tools():
    return jsonify({
        "tools": [
            {
                "name": "verify_citation",
                "description": "Verify an academic citation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "citation": {"type": "string"}
                    }
                }
            }
        ]
    })

@app.route("/tools/<tool_name>", methods=["POST"])
def call_tool(tool_name):
    data = request.json

    if tool_name == "verify_citation":
        citation = data.get("citation", "")
        # Your verification logic
        result = check_citation_database(citation)
        return jsonify({"result": result})

    return jsonify({"error": "Unknown tool"}), 404

def check_citation_database(citation):
    # Your logic here
    return f"Citation check result: {citation}"

if __name__ == "__main__":
    app.run(port=8080)
```

Use with MAVEN:

```python
detector = HallucinationDetector(
    models=["together/llama-3.1-8b", "together/qwen-2.5-7b"],
    mcp_servers=[
        {
            "name": "citation-checker",
            "type": "http",
            "url": "http://localhost:8080"
        }
    ]
)
```

## How Models Use MCP Tools

When verifying responses, MAVEN's models can request tool calls using this format:

```
USE_TOOL: wikipedia:search
QUERY: Eiffel Tower construction date
```

MAVEN automatically:
1. Parses tool call requests from model outputs
2. Routes calls to the appropriate MCP server
3. Returns results back to the model for analysis
4. Includes tool results in the verification trace

## Domain-Specific Configurations

### Medical Verification

```python
detector = HallucinationDetector(
    models=["together/llama-3.1-8b", "together/qwen-2.5-7b"],
    mcp_servers=[
        # PubMed for medical literature
        {
            "name": "pubmed",
            "type": "stdio",
            "command": "python",
            "args": ["pubmed_mcp_server.py"]
        },
        # Drug database
        {
            "name": "drug-db",
            "type": "http",
            "url": "https://api.drugbank.com",
            "api_key": "your-key"
        }
    ]
)

report = detector.detect(
    query="What are the side effects of metformin?",
    answer=ai_response,
    domain="medical"  # Activates medical-specific prompts
)
```

### Legal Verification

```python
detector = HallucinationDetector(
    models=["together/llama-3.1-8b", "together/qwen-2.5-7b"],
    mcp_servers=[
        # Case law database
        {
            "name": "case-law",
            "type": "http",
            "url": "https://api.courtlistener.com"
        },
        # Statute lookup
        {
            "name": "statutes",
            "type": "stdio",
            "command": "python",
            "args": ["statute_lookup_server.py"]
        }
    ]
)

report = detector.detect(
    query="What is the statute of limitations for breach of contract?",
    answer=ai_response,
    domain="legal"
)
```

### Financial Verification

```python
detector = HallucinationDetector(
    models=["together/llama-3.1-8b", "together/qwen-2.5-7b"],
    mcp_servers=[
        # SEC filings
        {
            "name": "sec-filings",
            "type": "http",
            "url": "https://api.sec.gov"
        },
        # Market data
        {
            "name": "market-data",
            "type": "stdio",
            "command": "python",
            "args": ["market_data_server.py"]
        }
    ]
)

report = detector.detect(
    query="What is Apple's current P/E ratio?",
    answer=ai_response,
    domain="financial"
)
```

## Advanced: MCPServerRegistry

For programmatic control over MCP servers:

```python
from maven import MCPServerRegistry, StdioMCPServer, HTTPMCPServer, create_mcp_server

# Create registry
registry = MCPServerRegistry()

# Add servers programmatically
wiki_server = StdioMCPServer(
    name="wikipedia",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-wikipedia"]
)
registry.register_server(wiki_server)

# Or use factory function
http_server = create_mcp_server("http", "my-api", {
    "url": "http://localhost:8080",
    "api_key": "secret"
})
registry.register_server(http_server)

# List available tools
tools = registry.get_all_tools()
print(f"Available tools: {[t['name'] for t in tools]}")

# Execute a tool directly
result = registry.execute_tool("wikipedia:search", {"query": "Python programming"})
```

## Troubleshooting

### Server Not Starting

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check if command exists
import subprocess
result = subprocess.run(["npx", "--version"], capture_output=True)
print(result.stdout.decode())
```

### Tool Calls Not Working

Ensure your MCP server:
1. Responds to `tools/list` with available tools
2. Handles `tools/call` with proper input schema
3. Returns results in the expected format

### Performance Issues

- Use HTTP servers for high-volume verification
- Consider caching frequent lookups
- Set appropriate timeouts in your server

## Best Practices

1. **Use domain-specific tools**: Match tools to your verification domain
2. **Validate tool results**: Don't blindly trust tool outputs
3. **Handle failures gracefully**: MCP servers may be unavailable
4. **Log tool usage**: Track which tools are most valuable
5. **Rate limit external APIs**: Respect API quotas

## Example: Complete Medical Verification Setup

```python
from maven import HallucinationDetector

# Production-ready medical verification
detector = HallucinationDetector(
    models=[
        "together/llama-3.3-70b",  # Larger model for accuracy
        "together/qwen-2.5-72b",
    ],
    mcp_servers=[
        # Wikipedia for general facts
        {
            "name": "wikipedia",
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-wikipedia"]
        },
        # Custom medical database
        {
            "name": "medical-db",
            "type": "http",
            "url": "https://your-medical-api.com",
            "api_key": "your-key"
        }
    ],
    rate_limit_delay=1.0  # Respect API limits
)

# Verify medical advice
report = detector.detect(
    query="Is aspirin safe during pregnancy?",
    answer="Aspirin is generally safe during pregnancy according to...",
    domain="medical"
)

if report.risk_level in ["CRITICAL", "HIGH"]:
    print(f"⚠️ High risk detected: {report.flags}")
    print(f"Tool verification results: {report.fact_checks}")
else:
    print(f"✓ Response verified: {report.confidence_score}% confidence")
```

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers)
- [MAVEN API Reference](docs/API.md)
- [MAVEN Architecture](docs/ARCHITECTURE.md)
