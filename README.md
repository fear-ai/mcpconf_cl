# mcpconf - MCP Server Registry and Configuration Management

**Production Ready v1.0.0** - A unified registry and configuration management tool for Model Context Protocol (MCP) servers, providing standardized format conversion and server management capabilities.

**61 Tests Passing** | **AWS Integration Validated** | **All Major Formats Supported**

## Features

- **Unified Registry Format**: YAML/JSON-based registry schema supporting all MCP server types
- **Format Conversion**: Convert between Claude Desktop, GitHub MCP, DXT manifest, and hosts file formats  
- **Server Management**: List, search, validate, and manage MCP server configurations
- **Category Organization**: Group servers by functionality or domain
- **Import/Export**: Import existing Claude Desktop configurations
- **CLI Interface**: Comprehensive command-line tool for registry operations

## Installation

```bash
pip install mcpconf
```

For development:
```bash
git clone <repo-url>
cd mcpconf
pip install -e .[dev]
```

## Quick Start

### Create a Registry

```yaml
# mcp-registry.yaml
version: "1.0"
servers:
  weather-local:
    name: "Weather Service"
    description: "Local weather data provider"
    version: "1.2.3"
    license: "MIT"
    deployment: local
    config:
      transport: stdio
      command: "uv"
      args: ["--directory", "/path/to/weather", "run", "weather.py"]
      env:
        WEATHER_API_KEY: "${input:weather_key}"
    capabilities:
      tools: ["get_weather", "get_forecast"]
    requirements:
      platforms: ["linux", "darwin", "win32"]
      runtimes:
        python: ">=3.8.0 <4"
    security:
      requires_auth: true
      sandbox: true
```

### CLI Usage

```bash
# List all servers
mcpconf list

# Show server details
mcpconf show weather-local

# Search servers
mcpconf search weather

# Convert to Claude Desktop format
mcpconf convert weather-local claude -o claude-config.json

# Import from Claude Desktop
mcpconf import ~/.config/claude/claude_desktop_config.json --save

# Validate configurations
mcpconf validate
```

## Registry Format

The mcpconf package uses a unified YAML/JSON registry format supporting all MCP server types. For complete format specification and examples, see [MCP_REGISTRY.md](MCP_REGISTRY.md).

### Quick Schema Reference

```yaml
version: "1.0"
servers:
  server-id:
    name: "Server Name"
    description: "Server description" 
    deployment: local|remote|hybrid
    config:
      transport: stdio|http|https|websocket
      # Transport-specific configuration
    capabilities: # Optional metadata
    requirements: # Platform/runtime requirements  
    security:     # Authentication & permissions
```

## Python API

### Basic Usage

```python
from mcpconf import MCPServerRegistry, RegistrySchema

# Load registry
registry = MCPServerRegistry("mcp-registry.yaml")

# List servers
servers = registry.list_servers(deployment="local")

# Get server details
server = registry.get_server("weather-local")
print(f"Transport: {server.config.transport.value}")

# Search servers
results = registry.search_servers("weather")

# Validate server
errors = registry.validate_server("weather-local")
if errors:
    print("Validation errors:", errors)
```

### Creating Server Entries

```python
from mcpconf.schema import ServerEntry, ServerConfig, TransportType, DeploymentType

server = ServerEntry(
    name="My Weather Server",
    description="Custom weather provider",
    version="1.0.0",
    deployment=DeploymentType.LOCAL,
    config=ServerConfig(
        transport=TransportType.STDIO,
        command="python",
        args=["weather_server.py"]
    )
)

registry.add_server("my-weather", server)
registry.save_registry()
```

## CLI Commands

### Server Management

```bash
# List servers with filters
mcpconf list                           # All servers
mcpconf list --deployment local        # Local servers only
mcpconf list --category weather        # Weather category
mcpconf list --detailed               # Detailed view

# Show server information
mcpconf show weather-local

# Search servers
mcpconf search "file system"
mcpconf search git
```

### Configuration Export

```bash
# Convert to different formats
mcpconf convert weather-local claude -o claude.json
mcpconf convert sentry-api github -o github.json
mcpconf convert fs-tools dxt -o manifest.json
mcpconf convert cli-server hosts      # Output to stdout
```

### Import and Validation

```bash
# Import from Claude Desktop
mcpconf import ~/.config/claude/claude_desktop_config.json --save

# Validate configurations
mcpconf validate                      # All servers
mcpconf validate weather-local        # Specific server
```

### Categories

```bash
# List categories
mcpconf categories

# Add to category (programmatically via Python API)
```

## Examples and Documentation

- **Example Registry**: See [examples/complete-registry.yaml](examples/complete-registry.yaml) - 15 server configurations with AWS integration
- **Format Specification**: Complete registry format documentation in [MCP_REGISTRY.md](MCP_REGISTRY.md)
- **Interactive Demo**: Run `python demo.py` to see all features in action

## Migration from Existing Formats

```bash
# Import from Claude Desktop
mcpconf import ~/.config/claude/claude_desktop_config.json --save

# Export to any format
mcpconf convert server-name claude -o claude-config.json
mcpconf convert server-name github -o github-mcp.json
```

## Development

### Running Tests

```bash
pytest tests/
pytest --cov=mcpconf tests/           # With coverage
```

### Code Quality

```bash
black mcpconf/                        # Format code
isort mcpconf/                        # Sort imports
mypy mcpconf/                         # Type checking
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure code quality checks pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.