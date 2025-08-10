# mcpconf - MCP Server Registry and Configuration Management

A unified registry and configuration management tool for Model Context Protocol (MCP) servers, providing standardized format conversion and server management capabilities.

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

### Server Entry Schema

```yaml
servers:
  server-id:
    # Required fields
    name: "Display Name"
    description: "Server description"
    version: "1.0.0"
    deployment: local|remote|hybrid
    config:
      transport: stdio|http|https|websocket
      # Transport-specific config...
    
    # Optional fields
    license: "MIT"
    source_url: "https://github.com/example/server"
    capabilities:
      tools: ["tool1", "tool2"]
      resources: ["resource://pattern/*"]
      prompts: ["prompt-name"]
    requirements:
      platforms: ["linux", "darwin", "win32"]
      runtimes:
        python: ">=3.8.0"
      dependencies: ["requests", "pydantic"]
    security:
      requires_auth: true
      permissions: ["network.http", "fs.read:/data"]
      sandbox: true
    compatibility:
      claude_desktop: ">=0.10.0"
      mcpred: ">=1.0.0"
```

### Transport Types

**STDIO Transport:**
```yaml
config:
  transport: stdio
  command: "python"
  args: ["server.py"]
  env:
    API_KEY: "${input:key}"
  working_dir: "/path/to/server"
```

**HTTP Transport:**
```yaml
config:
  transport: https
  url: "https://api.example.com/mcp"
  headers:
    Authorization: "Bearer ${input:token}"
  timeout: 30
```

## Format Conversion

### Claude Desktop Format

```python
from mcpconf import MCPServerRegistry

registry = MCPServerRegistry("registry.yaml")
config = registry.to_claude_desktop("weather-local")
# Outputs:
# {
#   "mcpServers": {
#     "weather-local": {
#       "command": "uv",
#       "args": ["--directory", "/path/to/weather", "run", "weather.py"],
#       "env": {"WEATHER_API_KEY": "${input:weather_key}"}
#     }
#   }
# }
```

### GitHub MCP Format

```python
config = registry.to_github_mcp("sentry-remote")
# Outputs:
# {
#   "servers": {
#     "sentry-remote": {
#       "type": "http",
#       "url": "https://mcp.sentry.dev/mcp",
#       "headers": {"Authorization": "Bearer ${input:token}"}
#     }
#   }
# }
```

### DXT Manifest Format

```python
manifest = registry.to_dxt_manifest("filesystem-tools")
# Outputs complete DXT manifest with metadata, tools, and compatibility info
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

## Example Registry Files

### Complete Server Registry

See [examples/complete-registry.yaml](examples/complete-registry.yaml) for a comprehensive example with multiple server types, categories, and configurations.

### Category Organization

```yaml
version: "1.0"
categories:
  weather:
    - weather-local
    - openweather-api
  development:
    - filesystem-tools
    - git-integration
  ai:
    - openai-api
    - local-llm
servers:
  # Server definitions...
```

## Migration from Existing Formats

### From Claude Desktop

```bash
# Import existing configuration
mcpconf import ~/.config/claude/claude_desktop_config.json --save

# Convert back to Claude Desktop format
mcpconf convert imported-server claude -o new-config.json
```

### From GitHub MCP

GitHub MCP format can be manually converted to registry format, focusing on HTTP transport servers.

### From DXT Manifests

DXT manifests contain rich metadata that maps well to the registry format, particularly for local STDIO servers.

## Development

### Running Tests

```bash
pytest tests/
pytest --cov=mcpred tests/           # With coverage
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