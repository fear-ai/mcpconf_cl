"""Tests for schema validation and parsing."""

import pytest

from mcpconf.schema import (
    Capabilities,
    Compatibility,
    DeploymentType,
    RegistrySchema,
    Requirements,
    Security,
    ServerConfig,
    ServerEntry,
    TransportType,
)


class TestRegistrySchema:
    """Test schema validation and parsing functionality."""
    
    def test_validate_server_entry_valid(self):
        """Test validation of valid server entry."""
        data = {
            "name": "Test Server",
            "description": "Test description",
            "version": "1.0.0",
            "deployment": "local",
            "config": {
                "transport": "stdio",
                "command": "python",
                "args": ["server.py"]
            }
        }
        
        errors = RegistrySchema.validate_server_entry(data)
        assert errors == {}
    
    def test_validate_server_entry_missing_required(self):
        """Test validation with missing required fields."""
        data = {
            "name": "Test Server",
            # Missing description, version, deployment, config
        }
        
        errors = RegistrySchema.validate_server_entry(data)
        assert "description" in errors
        assert "version" in errors
        assert "deployment" in errors
        assert "config" in errors
    
    def test_validate_server_entry_invalid_deployment(self):
        """Test validation with invalid deployment type."""
        data = {
            "name": "Test Server",
            "description": "Test description", 
            "version": "1.0.0",
            "deployment": "invalid",
            "config": {"transport": "stdio", "command": "python"}
        }
        
        errors = RegistrySchema.validate_server_entry(data)
        assert "deployment" in errors
    
    def test_validate_server_entry_invalid_transport(self):
        """Test validation with invalid transport type."""
        data = {
            "name": "Test Server",
            "description": "Test description",
            "version": "1.0.0", 
            "deployment": "local",
            "config": {"transport": "invalid"}
        }
        
        errors = RegistrySchema.validate_server_entry(data)
        assert "config.transport" in errors
    
    def test_validate_server_entry_stdio_missing_command(self):
        """Test validation for stdio transport without command."""
        data = {
            "name": "Test Server",
            "description": "Test description",
            "version": "1.0.0",
            "deployment": "local", 
            "config": {"transport": "stdio"}
        }
        
        errors = RegistrySchema.validate_server_entry(data)
        assert "config.command" in errors
    
    def test_validate_server_entry_http_missing_url(self):
        """Test validation for HTTP transport without URL."""
        data = {
            "name": "Test Server",
            "description": "Test description",
            "version": "1.0.0",
            "deployment": "remote",
            "config": {"transport": "http"}
        }
        
        errors = RegistrySchema.validate_server_entry(data)
        assert "config.url" in errors
    
    def test_parse_server_entry_minimal(self):
        """Test parsing minimal server entry."""
        data = {
            "name": "Test Server",
            "description": "Test description",
            "version": "1.0.0",
            "deployment": "local",
            "config": {
                "transport": "stdio",
                "command": "python",
                "args": ["server.py"]
            }
        }
        
        server = RegistrySchema.parse_server_entry(data)
        assert server.name == "Test Server"
        assert server.description == "Test description"
        assert server.version == "1.0.0"
        assert server.deployment == DeploymentType.LOCAL
        assert server.config.transport == TransportType.STDIO
        assert server.config.command == "python"
        assert server.config.args == ["server.py"]
    
    def test_parse_server_entry_full(self):
        """Test parsing full server entry with all optional fields."""
        data = {
            "name": "Full Server",
            "description": "Full description",
            "version": "2.1.0",
            "license": "MIT",
            "source_url": "https://github.com/example/server",
            "deployment": "local",
            "config": {
                "transport": "stdio",
                "command": "python",
                "args": ["server.py"],
                "env": {"KEY": "value"},
                "working_dir": "/path",
                "timeout": 60
            },
            "capabilities": {
                "tools": ["tool1", "tool2"],
                "resources": ["res1", "res2"],
                "prompts": ["prompt1"]
            },
            "requirements": {
                "platforms": ["linux", "darwin"],
                "runtimes": {"python": ">=3.8"},
                "dependencies": ["requests"],
                "network": True
            },
            "security": {
                "requires_auth": True,
                "permissions": ["fs.read"],
                "sandbox": True
            },
            "compatibility": {
                "claude_desktop": ">=0.10.0",
                "mcpconf": ">=1.0.0"
            }
        }
        
        server = RegistrySchema.parse_server_entry(data)
        assert server.license == "MIT"
        assert server.source_url == "https://github.com/example/server"
        assert server.config.env == {"KEY": "value"}
        assert server.config.working_dir == "/path"
        assert server.config.timeout == 60
        assert server.capabilities.tools == ["tool1", "tool2"]
        assert server.capabilities.resources == ["res1", "res2"]
        assert server.capabilities.prompts == ["prompt1"]
        assert server.requirements.platforms == ["linux", "darwin"]
        assert server.requirements.runtimes == {"python": ">=3.8"}
        assert server.requirements.dependencies == ["requests"]
        assert server.requirements.network is True
        assert server.security.requires_auth is True
        assert server.security.permissions == ["fs.read"]
        assert server.security.sandbox is True
        assert server.compatibility.claude_desktop == ">=0.10.0"
        assert server.compatibility.mcpconf == ">=1.0.0"
    
    def test_parse_registry_valid(self):
        """Test parsing valid registry."""
        data = {
            "version": "1.0",
            "servers": {
                "test-server": {
                    "name": "Test Server",
                    "description": "Test description", 
                    "version": "1.0.0",
                    "deployment": "local",
                    "config": {
                        "transport": "stdio",
                        "command": "python"
                    }
                }
            },
            "categories": {
                "test": ["test-server"]
            }
        }
        
        registry = RegistrySchema.parse_registry(data)
        assert registry.version == "1.0"
        assert len(registry.servers) == 1
        assert "test-server" in registry.servers
        assert registry.categories == {"test": ["test-server"]}
    
    def test_parse_registry_missing_version(self):
        """Test parsing registry without version."""
        data = {"servers": {}}
        
        with pytest.raises(ValueError, match="Registry version is required"):
            RegistrySchema.parse_registry(data)
    
    def test_parse_registry_missing_servers(self):
        """Test parsing registry without servers."""
        data = {"version": "1.0"}
        
        with pytest.raises(ValueError, match="Servers section is required"):
            RegistrySchema.parse_registry(data)
    
    def test_parse_registry_invalid_server(self):
        """Test parsing registry with invalid server."""
        data = {
            "version": "1.0",
            "servers": {
                "bad-server": {
                    "name": "Bad Server"
                    # Missing required fields
                }
            }
        }
        
        with pytest.raises(ValueError, match="Validation errors for server"):
            RegistrySchema.parse_registry(data)