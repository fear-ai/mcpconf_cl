"""Tests for format conversion utilities."""

import pytest

from mcpconf.converters import FormatConverter
from mcpconf.schema import (
    Capabilities,
    DeploymentType,
    ServerConfig,
    ServerEntry,
    TransportType,
)


class TestFormatConverter:
    """Test format conversion functionality."""
    
    def test_to_claude_desktop_stdio(self):
        """Test conversion to Claude Desktop format for stdio transport."""
        server = ServerEntry(
            name="Test Server",
            description="Test description",
            version="1.0.0",
            deployment=DeploymentType.LOCAL,
            config=ServerConfig(
                transport=TransportType.STDIO,
                command="python",
                args=["server.py"],
                env={"API_KEY": "secret"}
            )
        )
        
        result = FormatConverter.to_claude_desktop(server, "test-server")
        expected = {
            "mcpServers": {
                "test-server": {
                    "command": "python",
                    "args": ["server.py"],
                    "env": {"API_KEY": "secret"}
                }
            }
        }
        
        assert result == expected
    
    def test_to_claude_desktop_http(self):
        """Test conversion to Claude Desktop format for HTTP transport."""
        server = ServerEntry(
            name="Test Server",
            description="Test description", 
            version="1.0.0",
            deployment=DeploymentType.REMOTE,
            config=ServerConfig(
                transport=TransportType.HTTPS,
                url="https://api.example.com/mcp",
                headers={"Authorization": "Bearer token"}
            )
        )
        
        result = FormatConverter.to_claude_desktop(server, "test-server")
        expected = {
            "mcpServers": {
                "test-server": {
                    "url": "https://api.example.com/mcp",
                    "headers": {"Authorization": "Bearer token"}
                }
            }
        }
        
        assert result == expected
    
    def test_to_github_mcp_success(self):
        """Test conversion to GitHub MCP format for HTTP transport.""" 
        server = ServerEntry(
            name="Test Server",
            description="Test description",
            version="1.0.0", 
            deployment=DeploymentType.REMOTE,
            config=ServerConfig(
                transport=TransportType.HTTP,
                url="https://api.example.com/mcp",
                headers={"Authorization": "Bearer token"}
            )
        )
        
        result = FormatConverter.to_github_mcp(server, "test-server")
        expected = {
            "servers": {
                "test-server": {
                    "type": "http",
                    "url": "https://api.example.com/mcp",
                    "headers": {"Authorization": "Bearer token"}
                }
            }
        }
        
        assert result == expected
    
    def test_to_github_mcp_invalid_transport(self):
        """Test GitHub MCP conversion with invalid transport type."""
        server = ServerEntry(
            name="Test Server", 
            description="Test description",
            version="1.0.0",
            deployment=DeploymentType.LOCAL,
            config=ServerConfig(
                transport=TransportType.STDIO,
                command="python"
            )
        )
        
        with pytest.raises(ValueError, match="GitHub MCP format only supports HTTP transport"):
            FormatConverter.to_github_mcp(server, "test-server")
    
    def test_to_dxt_manifest_python(self):
        """Test conversion to DXT manifest format for Python server."""
        server = ServerEntry(
            name="Test Python Server",
            description="Python-based server",
            version="1.2.3",
            deployment=DeploymentType.LOCAL,
            config=ServerConfig(
                transport=TransportType.STDIO,
                command="python",
                args=["server.py"],
                env={"DEBUG": "true"}
            ),
            capabilities=Capabilities(
                tools=["tool1", "tool2"]
            ),
            license="MIT"
        )
        
        result = FormatConverter.to_dxt_manifest(server, "test-server")
        assert result["dxt_version"] == "1.0"
        assert result["name"] == "test-server"
        assert result["display_name"] == "Test Python Server"
        assert result["version"] == "1.2.3"
        assert result["description"] == "Python-based server"
        assert result["license"] == "MIT"
        assert result["server"]["type"] == "python"
        assert result["server"]["mcp_config"]["command"] == "python"
        assert result["server"]["mcp_config"]["args"] == ["server.py"]
        assert result["server"]["mcp_config"]["env"] == {"DEBUG": "true"}
        assert len(result["tools"]) == 2
        assert result["tools"][0]["name"] == "tool1"
    
    def test_to_dxt_manifest_node(self):
        """Test conversion to DXT manifest format for Node server."""
        server = ServerEntry(
            name="Test Node Server", 
            description="Node.js server",
            version="2.0.0",
            deployment=DeploymentType.LOCAL,
            config=ServerConfig(
                transport=TransportType.STDIO,
                command="node",
                args=["server.js"]
            )
        )
        
        result = FormatConverter.to_dxt_manifest(server, "test-server")
        assert result["server"]["type"] == "node"
    
    def test_to_dxt_manifest_invalid_transport(self):
        """Test DXT manifest conversion with invalid transport type."""
        server = ServerEntry(
            name="Test Server",
            description="Test description",
            version="1.0.0",
            deployment=DeploymentType.REMOTE,
            config=ServerConfig(
                transport=TransportType.HTTP,
                url="https://api.example.com"
            )
        )
        
        with pytest.raises(ValueError, match="DXT manifest only supports stdio transport"):
            FormatConverter.to_dxt_manifest(server, "test-server")
    
    def test_to_hosts_format_stdio(self):
        """Test conversion to hosts file format for stdio transport."""
        server = ServerEntry(
            name="Test Server",
            description="Test description",
            version="1.0.0",
            deployment=DeploymentType.LOCAL,
            config=ServerConfig(
                transport=TransportType.STDIO,
                command="python",
                args=["server.py"],
                env={"API_KEY": "secret"}
            )
        )
        
        result = FormatConverter.to_hosts_format(server, "test-server")
        expected = "test-server local stdio python:server.py auth=key env=API_KEY"
        assert result == expected
    
    def test_to_hosts_format_http(self):
        """Test conversion to hosts file format for HTTP transport."""
        server = ServerEntry(
            name="Test Server",
            description="Test description",
            version="1.0.0",
            deployment=DeploymentType.REMOTE,
            config=ServerConfig(
                transport=TransportType.HTTPS,
                url="https://api.example.com/mcp",
                headers={"Authorization": "Bearer token"}
            )
        )
        
        result = FormatConverter.to_hosts_format(server, "test-server")
        expected = "test-server remote https https://api.example.com/mcp auth=bearer"
        assert result == expected
    
    def test_from_claude_desktop_stdio(self):
        """Test conversion from Claude Desktop format with stdio transport."""
        config = {
            "mcpServers": {
                "weather": {
                    "command": "python",
                    "args": ["weather.py"],
                    "env": {"API_KEY": "secret"}
                }
            }
        }
        
        result = FormatConverter.from_claude_desktop(config)
        assert "weather" in result
        
        server_data = result["weather"]
        assert server_data["name"] == "Weather"
        assert server_data["deployment"] == "local"
        assert server_data["config"]["transport"] == "stdio"
        assert server_data["config"]["command"] == "python"
        assert server_data["config"]["args"] == ["weather.py"]
        assert server_data["config"]["env"] == {"API_KEY": "secret"}
    
    def test_from_claude_desktop_http(self):
        """Test conversion from Claude Desktop format with HTTP transport."""
        config = {
            "mcpServers": {
                "sentry": {
                    "url": "https://mcp.sentry.dev/mcp"
                }
            }
        }
        
        result = FormatConverter.from_claude_desktop(config)
        assert "sentry" in result
        
        server_data = result["sentry"]
        assert server_data["name"] == "Sentry"
        assert server_data["deployment"] == "remote"
        assert server_data["config"]["transport"] == "https"
        assert server_data["config"]["url"] == "https://mcp.sentry.dev/mcp"
    
    def test_from_claude_desktop_empty(self):
        """Test conversion from empty Claude Desktop config."""
        config = {}
        result = FormatConverter.from_claude_desktop(config)
        assert result == {}
        
        config = {"mcpServers": {}}
        result = FormatConverter.from_claude_desktop(config)
        assert result == {}