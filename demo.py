#!/usr/bin/env python3
"""
Demo script showing mcpred functionality
"""

import json
import tempfile
from pathlib import Path

from mcpconf import MCPServerRegistry, RegistrySchema
from mcpconf.schema import ServerEntry, ServerConfig, TransportType, DeploymentType, Capabilities


def demo_basic_usage():
    """Demonstrate basic registry usage."""
    print("=== Basic Registry Usage ===")
    
    # Create empty registry
    registry = MCPServerRegistry()
    print(f"Created registry with {len(registry.list_servers())} servers")
    
    # Create a sample server
    weather_server = ServerEntry(
        name="Weather Service",
        description="Local weather data provider",
        version="1.2.3",
        deployment=DeploymentType.LOCAL,
        config=ServerConfig(
            transport=TransportType.STDIO,
            command="uv",
            args=["--directory", "/path/to/weather", "run", "weather.py"],
            env={"WEATHER_API_KEY": "${input:weather_key}"}
        ),
        capabilities=Capabilities(
            tools=["get_weather", "get_forecast"],
            resources=["weather://current", "weather://forecast/*"]
        ),
        license="MIT"
    )
    
    # Add server to registry
    registry.add_server("weather-local", weather_server)
    print(f"Added server. Registry now has {len(registry.list_servers())} servers")
    
    # List servers
    servers = registry.list_servers()
    print(f"Servers: {servers}")
    
    print()


def demo_format_conversion():
    """Demonstrate format conversion capabilities."""
    print("=== Format Conversion ===")
    
    # Load the complete example registry
    registry = MCPServerRegistry("examples/complete-registry.yaml")
    
    # Convert weather server to Claude Desktop format
    claude_config = registry.to_claude_desktop("weather-local")
    print("Claude Desktop format for weather-local:")
    print(json.dumps(claude_config, indent=2))
    print()
    
    # Convert remote server to GitHub MCP format
    try:
        github_config = registry.to_github_mcp("sentry-remote")
        print("GitHub MCP format for sentry-remote:")
        print(json.dumps(github_config, indent=2))
    except Exception as e:
        print(f"GitHub conversion error: {e}")
    print()
    
    # Convert to hosts format
    hosts_line = registry.to_hosts_format("weather-local")
    print("Hosts format for weather-local:")
    print(hosts_line)
    print()


def demo_claude_desktop_import():
    """Demonstrate importing from Claude Desktop configuration."""
    print("=== Claude Desktop Import ===")
    
    # Load example Claude Desktop config
    with open("examples/claude-desktop-import.json", "r") as f:
        claude_config = json.load(f)
    
    print("Original Claude Desktop config:")
    print(json.dumps(claude_config, indent=2))
    print()
    
    # Import into registry
    registry = MCPServerRegistry()
    count = registry.import_claude_desktop(claude_config)
    print(f"Imported {count} servers")
    
    # Show imported servers
    for server_id in registry.list_servers():
        server = registry.get_server(server_id)
        print(f"- {server_id}: {server.name} ({server.deployment.value}, {server.config.transport.value})")
    
    print()


def demo_search_and_filter():
    """Demonstrate search and filtering capabilities."""
    print("=== Search and Filtering ===")
    
    # Load complete registry
    registry = MCPServerRegistry("examples/complete-registry.yaml")
    
    # List all servers
    all_servers = registry.list_servers()
    print(f"Total servers: {len(all_servers)}")
    
    # Filter by deployment type
    local_servers = registry.list_servers(deployment="local")
    remote_servers = registry.list_servers(deployment="remote")
    print(f"Local servers: {len(local_servers)}")
    print(f"Remote servers: {len(remote_servers)}")
    
    # Search for weather-related servers
    weather_servers = registry.search_servers("weather")
    print(f"Weather servers: {weather_servers}")
    
    # Search for AWS servers
    aws_servers = registry.search_servers("aws")
    print(f"AWS servers: {aws_servers}")
    
    # List categories
    categories = registry.get_categories()
    print("Categories:")
    for category, servers in categories.items():
        print(f"  {category}: {len(servers)} servers")
    
    print()


def demo_validation():
    """Demonstrate validation capabilities."""
    print("=== Validation ===")
    
    # Create registry with valid and invalid servers
    registry = MCPServerRegistry()
    
    # Valid server
    valid_server = ServerEntry(
        name="Valid Server",
        description="A valid server configuration",
        version="1.0.0",
        deployment=DeploymentType.LOCAL,
        config=ServerConfig(
            transport=TransportType.STDIO,
            command="python",
            args=["server.py"]
        )
    )
    registry.add_server("valid-server", valid_server)
    
    # Validate servers
    for server_id in registry.list_servers():
        errors = registry.validate_server(server_id)
        if errors:
            print(f" {server_id}: {errors}")
        else:
            print(f" {server_id}: Valid")
    
    print()


def main():
    """Run all demos."""
    print(" mcpred Demo - MCP Server Registry Management\n")
    
    try:
        demo_basic_usage()
        demo_claude_desktop_import()
        demo_format_conversion()
        demo_search_and_filter()
        demo_validation()
        
        print(" Demo completed successfully!")
        
    except Exception as e:
        print(f" Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
