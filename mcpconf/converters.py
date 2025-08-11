"""Format conversion utilities for different MCP client configurations."""

from typing import Any, Dict, List, Optional

from .schema import ServerEntry, TransportType


class FormatConverter:
    """Convert registry entries to various client configuration formats."""
    
    @staticmethod
    def to_claude_desktop(server: ServerEntry, server_id: str) -> Dict[str, Any]:
        """Convert server entry to Claude Desktop format."""
        result: Dict[str, Any] = {"mcpServers": {}}
        server_config: Dict[str, Any] = {}
        
        if server.config.transport == TransportType.STDIO:
            if server.config.command:
                server_config["command"] = server.config.command
            if server.config.args:
                server_config["args"] = server.config.args
            if server.config.env:
                server_config["env"] = server.config.env
        elif server.config.transport in [TransportType.HTTP, TransportType.HTTPS]:
            if server.config.url:
                server_config["url"] = server.config.url
            if server.config.headers:
                server_config["headers"] = server.config.headers
        
        result["mcpServers"][server_id] = server_config
        return result
    
    @staticmethod
    def to_github_mcp(server: ServerEntry, server_id: str) -> Dict[str, Any]:
        """Convert server entry to GitHub MCP format."""
        result: Dict[str, Any] = {"servers": {}}
        
        if server.config.transport in [TransportType.HTTP, TransportType.HTTPS]:
            server_config: Dict[str, Any] = {
                "type": "http",
                "url": server.config.url
            }
            if server.config.headers:
                server_config["headers"] = server.config.headers
            
            result["servers"][server_id] = server_config
        else:
            raise ValueError(f"GitHub MCP format only supports HTTP transport, got {server.config.transport}")
        
        return result
    
    @staticmethod
    def to_dxt_manifest(server: ServerEntry, server_id: str) -> Dict[str, Any]:
        """Convert server entry to DXT manifest format."""
        if server.config.transport != TransportType.STDIO:
            raise ValueError(f"DXT manifest only supports stdio transport, got {server.config.transport}")
        
        # Determine runtime type from command
        runtime_type = "node"
        if server.config.command in ["python", "python3", "uv", "uvx"]:
            runtime_type = "python"
        
        mcp_config: Dict[str, Any] = {}
        if server.config.command:
            mcp_config["command"] = server.config.command
        if server.config.args:
            mcp_config["args"] = server.config.args
        if server.config.env:
            mcp_config["env"] = server.config.env
        
        result: Dict[str, Any] = {
            "dxt_version": "1.0",
            "name": server_id,
            "display_name": server.name,
            "version": server.version,
            "description": server.description,
            "server": {
                "type": runtime_type,
                "mcp_config": mcp_config
            }
        }
        
        # Add optional fields
        if server.license:
            result["license"] = server.license
        if server.source_url:
            result["repository"] = server.source_url
        if server.capabilities:
            tools: List[Dict[str, str]] = []
            if server.capabilities.tools:
                for tool in server.capabilities.tools:
                    tools.append({
                        "name": tool,
                        "description": f"Tool: {tool}"
                    })
            if tools:
                result["tools"] = tools
        if server.compatibility:
            compat: Dict[str, Any] = {}
            if server.compatibility.claude_desktop:
                compat["claude_desktop"] = server.compatibility.claude_desktop
            if server.requirements and server.requirements.platforms:
                compat["platforms"] = server.requirements.platforms
            if compat:
                result["compatibility"] = compat
        
        return result
    
    @staticmethod
    def to_hosts_format(server: ServerEntry, server_id: str) -> str:
        """Convert server entry to Linux hosts file style format."""
        parts = [server_id, server.deployment.value, server.config.transport.value]
        
        # Add endpoint
        if server.config.transport == TransportType.STDIO and server.config.command:
            if server.config.args:
                endpoint = f"{server.config.command}:{':'.join(server.config.args)}"
            else:
                endpoint = server.config.command
        elif server.config.url:
            endpoint = server.config.url
        else:
            endpoint = "unknown"
        
        parts.append(endpoint)
        
        # Add options
        options = []
        
        # Check for auth in headers or environment
        has_auth = False
        if server.config.headers and "Authorization" in server.config.headers:
            auth_header = server.config.headers["Authorization"]
            if auth_header.startswith("Bearer"):
                options.append("auth=bearer")
            else:
                options.append("auth=key")
            has_auth = True
        elif server.config.env and any(key.endswith("KEY") or key.endswith("TOKEN") for key in server.config.env.keys()):
            options.append("auth=key")
            has_auth = True
        
        if server.config.env:
            env_vars = ",".join(server.config.env.keys())
            options.append(f"env={env_vars}")
        
        if server.security and server.security.sandbox:
            options.append("sandbox=true")
        
        if options:
            parts.append(" ".join(options))
        
        return " ".join(parts)
    
    @staticmethod
    def from_claude_desktop(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Convert Claude Desktop format to registry format."""
        servers: Dict[str, Dict[str, Any]] = {}
        
        if "mcpServers" not in config:
            return servers
        
        for server_id, server_config in config["mcpServers"].items():
            registry_entry = {
                "name": server_id.replace("-", " ").title(),
                "description": f"Imported from Claude Desktop configuration",
                "version": "1.0.0",
                "deployment": "local" if "command" in server_config else "remote",
                "config": {}
            }
            
            if "command" in server_config:
                registry_entry["config"]["transport"] = "stdio"
                registry_entry["config"]["command"] = server_config["command"]
                if "args" in server_config:
                    registry_entry["config"]["args"] = server_config["args"]
                if "env" in server_config:
                    registry_entry["config"]["env"] = server_config["env"]
            elif "url" in server_config:
                url = server_config["url"]
                registry_entry["config"]["transport"] = "https" if url.startswith("https") else "http"
                registry_entry["config"]["url"] = url
                if "headers" in server_config:
                    registry_entry["config"]["headers"] = server_config["headers"]
            
            servers[server_id] = registry_entry
        
        return servers