"""Registry schema validation and structure definitions."""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import json
import yaml


class DeploymentType(Enum):
    LOCAL = "local"
    REMOTE = "remote"
    HYBRID = "hybrid"


class TransportType(Enum):
    STDIO = "stdio"
    HTTP = "http"
    HTTPS = "https"
    WEBSOCKET = "websocket"


@dataclass
class ServerConfig:
    transport: TransportType
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    env: Optional[Dict[str, str]] = None
    working_dir: Optional[str] = None
    timeout: Optional[int] = 30


@dataclass
class Capabilities:
    tools: Optional[List[str]] = None
    resources: Optional[List[str]] = None
    prompts: Optional[List[str]] = None


@dataclass
class Requirements:
    platforms: Optional[List[str]] = None
    runtimes: Optional[Dict[str, str]] = None
    dependencies: Optional[List[str]] = None
    network: Optional[bool] = None


@dataclass
class Security:
    requires_auth: bool = False
    permissions: Optional[List[str]] = None
    sandbox: bool = False


@dataclass
class Compatibility:
    claude_desktop: Optional[str] = None
    mcpconf: Optional[str] = None


@dataclass
class ServerEntry:
    name: str
    description: str
    version: str
    deployment: DeploymentType
    config: ServerConfig
    license: Optional[str] = None
    source_url: Optional[str] = None
    capabilities: Optional[Capabilities] = None
    requirements: Optional[Requirements] = None
    security: Optional[Security] = None
    compatibility: Optional[Compatibility] = None


@dataclass
class Registry:
    version: str
    servers: Dict[str, ServerEntry]
    categories: Optional[Dict[str, List[str]]] = None


class RegistrySchema:
    """Schema validation and parsing for MCP server registry."""
    
    REQUIRED_FIELDS = ["name", "description", "version", "deployment", "config"]
    
    @classmethod
    def validate_server_entry(cls, data: Dict[str, Any]) -> Dict[str, str]:
        """Validate server entry and return validation errors."""
        errors = {}
        
        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in data:
                errors[field] = f"Required field '{field}' is missing"
        
        # Validate deployment type
        if "deployment" in data:
            try:
                DeploymentType(data["deployment"])
            except ValueError:
                errors["deployment"] = f"Invalid deployment type: {data['deployment']}"
        
        # Validate transport type in config
        if "config" in data and isinstance(data["config"], dict):
            if "transport" not in data["config"]:
                errors["config.transport"] = "Transport type is required in config"
            else:
                try:
                    TransportType(data["config"]["transport"])
                except ValueError:
                    errors["config.transport"] = f"Invalid transport type: {data['config']['transport']}"
            
            # Validate transport-specific requirements
            transport = data["config"].get("transport")
            if transport == "stdio" and "command" not in data["config"]:
                errors["config.command"] = "Command is required for stdio transport"
            elif transport in ["http", "https"] and "url" not in data["config"]:
                errors["config.url"] = "URL is required for HTTP transport"
        
        return errors
    
    @classmethod
    def parse_server_entry(cls, data: Dict[str, Any]) -> ServerEntry:
        """Parse validated data into ServerEntry object."""
        config_data = data["config"]
        config = ServerConfig(
            transport=TransportType(config_data["transport"]),
            command=config_data.get("command"),
            args=config_data.get("args"),
            url=config_data.get("url"),
            headers=config_data.get("headers"),
            env=config_data.get("env"),
            working_dir=config_data.get("working_dir"),
            timeout=config_data.get("timeout", 30)
        )
        
        capabilities = None
        if "capabilities" in data:
            cap_data = data["capabilities"]
            capabilities = Capabilities(
                tools=cap_data.get("tools"),
                resources=cap_data.get("resources"),
                prompts=cap_data.get("prompts")
            )
        
        requirements = None
        if "requirements" in data:
            req_data = data["requirements"]
            requirements = Requirements(
                platforms=req_data.get("platforms"),
                runtimes=req_data.get("runtimes"),
                dependencies=req_data.get("dependencies"),
                network=req_data.get("network")
            )
        
        security = None
        if "security" in data:
            sec_data = data["security"]
            security = Security(
                requires_auth=sec_data.get("requires_auth", False),
                permissions=sec_data.get("permissions"),
                sandbox=sec_data.get("sandbox", False)
            )
        
        compatibility = None
        if "compatibility" in data:
            compat_data = data["compatibility"]
            compatibility = Compatibility(
                claude_desktop=compat_data.get("claude_desktop"),
                mcpconf=compat_data.get("mcpconf")
            )
        
        return ServerEntry(
            name=data["name"],
            description=data["description"],
            version=data["version"],
            deployment=DeploymentType(data["deployment"]),
            config=config,
            license=data.get("license"),
            source_url=data.get("source_url"),
            capabilities=capabilities,
            requirements=requirements,
            security=security,
            compatibility=compatibility
        )
    
    @classmethod
    def parse_registry(cls, data: Dict[str, Any]) -> Registry:
        """Parse registry data and validate all server entries."""
        if "version" not in data:
            raise ValueError("Registry version is required")
        
        if "servers" not in data:
            raise ValueError("Servers section is required")
        
        servers = {}
        for server_id, server_data in data["servers"].items():
            errors = cls.validate_server_entry(server_data)
            if errors:
                error_msg = f"Validation errors for server '{server_id}': "
                error_msg += ", ".join([f"{k}: {v}" for k, v in errors.items()])
                raise ValueError(error_msg)
            
            servers[server_id] = cls.parse_server_entry(server_data)
        
        return Registry(
            version=data["version"],
            servers=servers,
            categories=data.get("categories")
        )
    
    @classmethod
    def load_from_file(cls, file_path: str) -> Registry:
        """Load registry from YAML or JSON file."""
        with open(file_path, 'r') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        # Handle empty files
        if data is None:
            data = {"version": "1.0", "servers": {}}
        
        return cls.parse_registry(data)