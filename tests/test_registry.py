"""Tests for registry management functionality."""

import pytest
import tempfile
import json
import yaml
from pathlib import Path

from mcpred.registry import MCPServerRegistry
from mcpred.schema import ServerEntry, ServerConfig, TransportType, DeploymentType


class TestMCPServerRegistry:
    """Test registry management functionality."""
    
    @pytest.fixture
    def sample_server(self):
        """Create a sample server entry for testing."""
        return ServerEntry(
            name="Test Server",
            description="Test description",
            version="1.0.0",
            deployment=DeploymentType.LOCAL,
            config=ServerConfig(
                transport=TransportType.STDIO,
                command="python",
                args=["server.py"]
            )
        )
    
    @pytest.fixture
    def sample_registry_data(self):
        """Create sample registry data."""
        return {
            "version": "1.0",
            "servers": {
                "test-server": {
                    "name": "Test Server",
                    "description": "Test description",
                    "version": "1.0.0",
                    "deployment": "local",
                    "config": {
                        "transport": "stdio",
                        "command": "python",
                        "args": ["server.py"]
                    }
                },
                "remote-server": {
                    "name": "Remote Server",
                    "description": "Remote test server",
                    "version": "2.0.0",
                    "deployment": "remote",
                    "config": {
                        "transport": "https",
                        "url": "https://api.example.com/mcp"
                    }
                }
            },
            "categories": {
                "test": ["test-server", "remote-server"]
            }
        }
    
    def test_init_empty_registry(self):
        """Test initializing empty registry."""
        registry = MCPServerRegistry()
        assert registry.registry is not None
        assert registry.registry.version == "1.0"
        assert len(registry.registry.servers) == 0
    
    def test_init_with_nonexistent_file(self):
        """Test initializing with non-existent file."""
        registry = MCPServerRegistry("nonexistent.yaml")
        assert registry.registry is not None
        assert registry.registry.version == "1.0"
        assert len(registry.registry.servers) == 0
    
    def test_load_registry_yaml(self, sample_registry_data):
        """Test loading registry from YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_registry_data, f)
            f.flush()
            
            registry = MCPServerRegistry(f.name)
            assert len(registry.registry.servers) == 2
            assert "test-server" in registry.registry.servers
            assert "remote-server" in registry.registry.servers
            
            Path(f.name).unlink()  # Clean up
    
    def test_load_registry_json(self, sample_registry_data):
        """Test loading registry from JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_registry_data, f)
            f.flush()
            
            registry = MCPServerRegistry(f.name)
            assert len(registry.registry.servers) == 2
            assert "test-server" in registry.registry.servers
            
            Path(f.name).unlink()  # Clean up
    
    def test_save_registry_yaml(self, sample_server):
        """Test saving registry to YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            registry = MCPServerRegistry()
            registry.add_server("test-server", sample_server)
            registry.save_registry(f.name)
            
            # Verify file was created and contains expected data
            with open(f.name, 'r') as read_f:
                data = yaml.safe_load(read_f)
                assert data["version"] == "1.0"
                assert "test-server" in data["servers"]
                assert data["servers"]["test-server"]["name"] == "Test Server"
            
            Path(f.name).unlink()  # Clean up
    
    def test_save_registry_json(self, sample_server):
        """Test saving registry to JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            registry = MCPServerRegistry()
            registry.add_server("test-server", sample_server)
            registry.save_registry(f.name)
            
            # Verify file was created and contains expected data
            with open(f.name, 'r') as read_f:
                data = json.load(read_f)
                assert data["version"] == "1.0"
                assert "test-server" in data["servers"]
            
            Path(f.name).unlink()  # Clean up
    
    def test_add_server(self, sample_server):
        """Test adding server to registry."""
        registry = MCPServerRegistry()
        registry.add_server("test-server", sample_server)
        
        assert len(registry.registry.servers) == 1
        assert "test-server" in registry.registry.servers
        assert registry.registry.servers["test-server"] == sample_server
    
    def test_remove_server_success(self, sample_server):
        """Test removing existing server."""
        registry = MCPServerRegistry()
        registry.add_server("test-server", sample_server)
        
        result = registry.remove_server("test-server")
        assert result is True
        assert len(registry.registry.servers) == 0
        assert "test-server" not in registry.registry.servers
    
    def test_remove_server_not_found(self):
        """Test removing non-existent server."""
        registry = MCPServerRegistry()
        result = registry.remove_server("nonexistent")
        assert result is False
    
    def test_get_server_success(self, sample_server):
        """Test getting existing server."""
        registry = MCPServerRegistry()
        registry.add_server("test-server", sample_server)
        
        server = registry.get_server("test-server")
        assert server == sample_server
    
    def test_get_server_not_found(self):
        """Test getting non-existent server."""
        registry = MCPServerRegistry()
        server = registry.get_server("nonexistent")
        assert server is None
    
    def test_list_servers_all(self, sample_registry_data):
        """Test listing all servers."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_registry_data, f)
            f.flush()
            
            registry = MCPServerRegistry(f.name)
            servers = registry.list_servers()
            assert sorted(servers) == ["remote-server", "test-server"]
            
            Path(f.name).unlink()  # Clean up
    
    def test_list_servers_by_deployment(self, sample_registry_data):
        """Test listing servers filtered by deployment type."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_registry_data, f)
            f.flush()
            
            registry = MCPServerRegistry(f.name)
            local_servers = registry.list_servers(deployment="local")
            assert local_servers == ["test-server"]
            
            remote_servers = registry.list_servers(deployment="remote")
            assert remote_servers == ["remote-server"]
            
            Path(f.name).unlink()  # Clean up
    
    def test_list_servers_by_category(self, sample_registry_data):
        """Test listing servers filtered by category."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_registry_data, f)
            f.flush()
            
            registry = MCPServerRegistry(f.name)
            test_servers = registry.list_servers(category="test")
            assert sorted(test_servers) == ["remote-server", "test-server"]
            
            Path(f.name).unlink()  # Clean up
    
    def test_search_servers(self, sample_registry_data):
        """Test searching servers."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_registry_data, f)
            f.flush()
            
            registry = MCPServerRegistry(f.name)
            
            # Search by name
            results = registry.search_servers("Remote")
            assert results == ["remote-server"]
            
            # Search by description
            results = registry.search_servers("Test description")
            assert results == ["test-server"]
            
            # Search by ID
            results = registry.search_servers("test-server")
            assert results == ["test-server"]
            
            # No matches
            results = registry.search_servers("nonexistent")
            assert results == []
            
            Path(f.name).unlink()  # Clean up
    
    def test_get_categories(self, sample_registry_data):
        """Test getting categories."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_registry_data, f)
            f.flush()
            
            registry = MCPServerRegistry(f.name)
            categories = registry.get_categories()
            assert categories == {"test": ["test-server", "remote-server"]}
            
            Path(f.name).unlink()  # Clean up
    
    def test_add_to_category(self, sample_server):
        """Test adding server to category."""
        registry = MCPServerRegistry()
        registry.add_server("test-server", sample_server)
        registry.add_to_category("new-category", "test-server")
        
        categories = registry.get_categories()
        assert categories == {"new-category": ["test-server"]}
    
    def test_remove_from_category(self, sample_registry_data):
        """Test removing server from category."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_registry_data, f)
            f.flush()
            
            registry = MCPServerRegistry(f.name)
            result = registry.remove_from_category("test", "test-server")
            assert result is True
            
            categories = registry.get_categories()
            assert categories == {"test": ["remote-server"]}
            
            Path(f.name).unlink()  # Clean up
    
    def test_import_claude_desktop(self):
        """Test importing from Claude Desktop configuration."""
        claude_config = {
            "mcpServers": {
                "weather": {
                    "command": "python",
                    "args": ["weather.py"],
                    "env": {"API_KEY": "secret"}
                },
                "sentry": {
                    "url": "https://mcp.sentry.dev/mcp"
                }
            }
        }
        
        registry = MCPServerRegistry()
        count = registry.import_claude_desktop(claude_config)
        
        assert count == 2
        assert len(registry.registry.servers) == 2
        assert "weather" in registry.registry.servers
        assert "sentry" in registry.registry.servers
    
    def test_validate_server_valid(self, sample_server):
        """Test validating valid server."""
        registry = MCPServerRegistry()
        registry.add_server("test-server", sample_server)
        
        errors = registry.validate_server("test-server")
        assert errors == {}
    
    def test_validate_server_not_found(self):
        """Test validating non-existent server."""
        registry = MCPServerRegistry()
        errors = registry.validate_server("nonexistent")
        assert "server" in errors