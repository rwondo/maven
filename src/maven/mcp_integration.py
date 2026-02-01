"""MCP (Model Context Protocol) Server Integration for MAVEN.

This module allows MAVEN to connect to any MCP server for external tool access.
Users can configure their own MCP servers for domain-specific verification.

Examples:
    - Wikipedia MCP server for general fact-checking
    - PubMed MCP server for medical paper verification
    - LexisNexis MCP server for legal case verification
    - WolframAlpha MCP server for advanced calculations
    - Custom domain-specific verification servers
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MCPServer(ABC):
    """Base class for MCP server connections."""

    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        self.config = config
        self.tools: dict[str, dict[str, Any]] = {}

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the MCP server.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def discover_tools(self) -> list[dict[str, Any]]:
        """Discover available tools from the server.

        Returns:
            List of tool definitions with name, description, parameters
        """
        pass

    @abstractmethod
    def execute_tool(self, tool_name: str, params: dict[str, Any]) -> str:
        """Execute a tool on the MCP server.

        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool

        Returns:
            Tool execution result as string
        """
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the MCP server."""
        pass


class StdioMCPServer(MCPServer):
    """MCP server that communicates via stdio (standard input/output).

    This is the standard MCP protocol using JSON-RPC over stdio.
    """

    def __init__(self, name: str, config: dict[str, Any]):
        super().__init__(name, config)
        self.process = None
        self.command = config.get("command")
        self.args = config.get("args", [])

    def connect(self) -> bool:
        """Start the MCP server process and connect via stdio."""
        try:
            import subprocess

            # Start the MCP server process
            self.process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            logger.info(f"Connected to MCP server: {self.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.name}: {e}")
            return False

    def discover_tools(self) -> list[dict[str, Any]]:
        """Discover tools by sending 'tools/list' request."""
        try:
            import json

            # Send tools/list request
            request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()

            # Read response
            response_line = self.process.stdout.readline()
            response = json.loads(response_line)

            if "result" in response and "tools" in response["result"]:
                tools = response["result"]["tools"]
                for tool in tools:
                    self.tools[tool["name"]] = tool
                logger.info(f"Discovered {len(tools)} tools from {self.name}")
                return tools

            return []

        except Exception as e:
            logger.error(f"Failed to discover tools from {self.name}: {e}")
            return []

    def execute_tool(self, tool_name: str, params: dict[str, Any]) -> str:
        """Execute tool by sending 'tools/call' request."""
        try:
            import json

            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": params},
            }

            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()

            response_line = self.process.stdout.readline()
            response = json.loads(response_line)

            if "result" in response:
                # MCP tool results are typically in content array
                content = response["result"].get("content", [])
                if content and isinstance(content, list):
                    # Extract text from content array
                    return "\n".join(
                        item.get("text", str(item)) for item in content if isinstance(item, dict)
                    )
                return str(response["result"])

            if "error" in response:
                return f"Error: {response['error'].get('message', 'Unknown error')}"

            return "No result returned"

        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name} on {self.name}: {e}")
            return f"Error: {str(e)}"

    def disconnect(self):
        """Terminate the MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            logger.info(f"Disconnected from MCP server: {self.name}")


class HTTPMCPServer(MCPServer):
    """MCP server that communicates via HTTP/REST API.

    For MCP servers that expose HTTP endpoints instead of stdio.
    """

    def __init__(self, name: str, config: dict[str, Any]):
        super().__init__(name, config)
        self.base_url = config.get("url")
        self.headers = config.get("headers", {})
        self.api_key = config.get("api_key")

        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def connect(self) -> bool:
        """Test connection to HTTP MCP server."""
        try:
            import requests

            response = requests.get(f"{self.base_url}/health", headers=self.headers, timeout=5)

            if response.status_code == 200:
                logger.info(f"Connected to HTTP MCP server: {self.name}")
                return True

            logger.error(f"HTTP MCP server {self.name} returned {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"Failed to connect to HTTP MCP server {self.name}: {e}")
            return False

    def discover_tools(self) -> list[dict[str, Any]]:
        """Discover tools via HTTP GET /tools endpoint."""
        try:
            import requests

            response = requests.get(f"{self.base_url}/tools", headers=self.headers, timeout=10)

            if response.status_code == 200:
                tools = response.json().get("tools", [])
                for tool in tools:
                    self.tools[tool["name"]] = tool
                logger.info(f"Discovered {len(tools)} tools from HTTP server {self.name}")
                return tools

            return []

        except Exception as e:
            logger.error(f"Failed to discover tools from HTTP server {self.name}: {e}")
            return []

    def execute_tool(self, tool_name: str, params: dict[str, Any]) -> str:
        """Execute tool via HTTP POST /tools/{tool_name} endpoint."""
        try:
            import requests

            response = requests.post(
                f"{self.base_url}/tools/{tool_name}", json=params, headers=self.headers, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("result", str(result))

            return f"Error: HTTP {response.status_code}"

        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name} via HTTP: {e}")
            return f"Error: {str(e)}"


class MCPServerRegistry:
    """Registry for managing multiple MCP servers."""

    def __init__(self):
        self.servers: dict[str, MCPServer] = {}
        self.all_tools: dict[str, tuple[MCPServer, str]] = {}  # tool_name -> (server, tool_name)

    def register_server(self, server: MCPServer) -> bool:
        """Register and connect to an MCP server.

        Args:
            server: MCP server instance

        Returns:
            True if registration successful
        """
        if not server.connect():
            logger.error(f"Failed to connect to server: {server.name}")
            return False

        # Discover tools
        tools = server.discover_tools()

        # Register tools in global registry
        for tool in tools:
            tool_name = tool["name"]
            # Prefix tool name with server name to avoid conflicts
            full_tool_name = f"{server.name}:{tool_name}"
            self.all_tools[full_tool_name] = (server, tool_name)
            # Also register without prefix for convenience
            if tool_name not in self.all_tools:
                self.all_tools[tool_name] = (server, tool_name)

        self.servers[server.name] = server
        logger.info(f"Registered MCP server: {server.name} with {len(tools)} tools")
        return True

    def execute_tool(self, tool_name: str, params: dict[str, Any]) -> str:
        """Execute a tool from any registered server.

        Args:
            tool_name: Name of the tool (can be prefixed with server name)
            params: Tool parameters

        Returns:
            Tool execution result
        """
        if tool_name not in self.all_tools:
            return f"Error: Tool '{tool_name}' not found in any registered server"

        server, actual_tool_name = self.all_tools[tool_name]
        return server.execute_tool(actual_tool_name, params)

    def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools from all servers."""
        tools = []
        for tool_name, (server, _) in self.all_tools.items():
            if ":" in tool_name:  # Skip prefixed duplicates
                continue
            tool_info = server.tools.get(tool_name, {})
            tools.append(
                {
                    "name": tool_name,
                    "server": server.name,
                    "description": tool_info.get("description", ""),
                    "full_name": f"{server.name}:{tool_name}",
                }
            )
        return tools

    def get_tools_description(self) -> str:
        """Get formatted description of all available tools."""
        descriptions = []
        for tool in self.list_tools():
            descriptions.append(f"- {tool['name']} ({tool['server']}): {tool['description']}")
        return "\n".join(descriptions)

    def disconnect_all(self):
        """Disconnect from all MCP servers."""
        for server in self.servers.values():
            server.disconnect()
        self.servers.clear()
        self.all_tools.clear()


def create_mcp_server(server_type: str, name: str, config: dict[str, Any]) -> Optional[MCPServer]:
    """Factory function to create MCP server instances.

    Args:
        server_type: Type of server ("stdio" or "http")
        name: Name for the server
        config: Server configuration

    Returns:
        MCP server instance or None if type unknown
    """
    if server_type == "stdio":
        return StdioMCPServer(name, config)
    elif server_type == "http":
        return HTTPMCPServer(name, config)
    else:
        logger.error(f"Unknown MCP server type: {server_type}")
        return None


if __name__ == "__main__":
    # Example usage
    print("MAVEN MCP Integration")
    print("=" * 70)

    # Example 1: Stdio MCP server (typical MCP setup)
    print("\nExample 1: Connecting to stdio MCP server")
    print("Config:")
    print(
        {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-wikipedia"],
        }
    )

    # Example 2: HTTP MCP server
    print("\nExample 2: Connecting to HTTP MCP server")
    print("Config:")
    print({"type": "http", "url": "https://api.example.com/mcp", "api_key": "your-api-key"})

    print("\n" + "=" * 70)
    print("See example_mcp_config.py for complete usage examples")
