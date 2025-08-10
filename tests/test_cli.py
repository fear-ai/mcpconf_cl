"""Tests for CLI functionality."""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch
from io import StringIO

from mcpconf.cli import main


class TestCLI:
    """Test CLI command functionality."""
    
    @pytest.fixture
    def sample_registry_file(self):
        """Create a temporary registry file for testing."""
        registry_data = {
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
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(registry_data, f)
            f.flush()
            yield f.name
            Path(f.name).unlink()  # Clean up
    
    def test_list_command(self, sample_registry_file):
        """Test list command."""
        with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'list']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                assert "test-server" in output
                assert "remote-server" in output
                assert "NAME" in output  # Header
    
    def test_list_command_deployment_filter(self, sample_registry_file):
        """Test list command with deployment filter."""
        with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'list', '--deployment', 'local']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                assert "test-server" in output
                assert "remote-server" not in output
    
    def test_list_command_detailed(self, sample_registry_file):
        """Test list command with detailed output."""
        with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'list', '--detailed']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                assert "Server: test-server" in output
                assert "Name: Test Server" in output
                assert "Transport: stdio" in output
    
    def test_show_command(self, sample_registry_file):
        """Test show command."""
        with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'show', 'test-server']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                assert "Server: test-server" in output
                assert "Name: Test Server" in output
                assert "Description: Test description" in output
                assert "Configuration:" in output
                assert "Command: python" in output
    
    def test_show_command_not_found(self, sample_registry_file):
        """Test show command for non-existent server."""
        with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'show', 'nonexistent']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with pytest.raises(SystemExit):
                    main()
                output = fake_out.getvalue()
                assert "not found" in output
    
    def test_search_command(self, sample_registry_file):
        """Test search command."""
        with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'search', 'Remote']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                assert "Found 1 servers" in output
                assert "remote-server" in output
                assert "test-server" not in output
    
    def test_search_command_no_results(self, sample_registry_file):
        """Test search command with no results."""
        with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'search', 'nonexistent']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                assert "No servers found matching" in output
    
    def test_convert_command_claude(self, sample_registry_file):
        """Test convert command to Claude Desktop format."""
        with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'convert', 'test-server', 'claude']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                config = json.loads(output)
                assert "mcpServers" in config
                assert "test-server" in config["mcpServers"]
                assert config["mcpServers"]["test-server"]["command"] == "python"
    
    def test_convert_command_with_output_file(self, sample_registry_file):
        """Test convert command with output file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_file:
            with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'convert', 'test-server', 'claude', '--output', output_file.name]):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    output = fake_out.getvalue()
                    assert f"Configuration written to {output_file.name}" in output
                
                # Verify output file contents
                with open(output_file.name, 'r') as f:
                    config = json.load(f)
                    assert "mcpServers" in config
            
            Path(output_file.name).unlink()  # Clean up
    
    def test_convert_command_hosts_format(self, sample_registry_file):
        """Test convert command to hosts format."""
        with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'convert', 'test-server', 'hosts']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue().strip()
                assert output.startswith("test-server local stdio")
    
    def test_validate_command_specific_server(self, sample_registry_file):
        """Test validate command for specific server."""
        with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'validate', 'test-server']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                assert "is valid" in output
    
    def test_validate_command_all_servers(self, sample_registry_file):
        """Test validate command for all servers."""
        with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'validate']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                assert "All servers are valid" in output
    
    def test_import_command(self):
        """Test import command."""
        claude_config = {
            "mcpServers": {
                "weather": {
                    "command": "python",
                    "args": ["weather.py"]
                }
            }
        }
        
        # Create temporary Claude config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as claude_file:
            json.dump(claude_config, claude_file)
            claude_file.flush()
            
            # Create temporary registry file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as registry_file:
                with patch('sys.argv', ['mcpconf', '--registry', registry_file.name, 'import', claude_file.name]):
                    with patch('sys.stdout', new=StringIO()) as fake_out:
                        main()
                        output = fake_out.getvalue()
                        assert "Imported 1 servers" in output
                        assert "not saved" in output
            
            Path(claude_file.name).unlink()  # Clean up
            Path(registry_file.name).unlink()  # Clean up
    
    def test_import_command_with_save(self):
        """Test import command with save option."""
        claude_config = {
            "mcpServers": {
                "weather": {
                    "command": "python",
                    "args": ["weather.py"]
                }
            }
        }
        
        # Create temporary Claude config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as claude_file:
            json.dump(claude_config, claude_file)
            claude_file.flush()
            
            # Create temporary registry file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as registry_file:
                with patch('sys.argv', ['mcpconf', '--registry', registry_file.name, 'import', claude_file.name, '--save']):
                    with patch('sys.stdout', new=StringIO()) as fake_out:
                        main()
                        output = fake_out.getvalue()
                        assert "Imported 1 servers and saved" in output
                
                # Verify registry file was updated
                with open(registry_file.name, 'r') as f:
                    registry_data = yaml.safe_load(f)
                    assert "weather" in registry_data["servers"]
            
            Path(claude_file.name).unlink()  # Clean up
            Path(registry_file.name).unlink()  # Clean up
    
    def test_categories_command_empty(self, sample_registry_file):
        """Test categories command with no categories."""
        with patch('sys.argv', ['mcpconf', '--registry', sample_registry_file, 'categories']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                assert "No categories defined" in output
    
    def test_no_command_shows_help(self):
        """Test that running without command shows help."""
        with patch('sys.argv', ['mcpconf']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with pytest.raises(SystemExit):
                    main()
                output = fake_out.getvalue()
                assert "usage:" in output or "Available commands:" in output