"""Core registry implementation for MCP server management."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml  # type: ignore[import-untyped]

from .converters import FormatConverter
from .schema import DeploymentType, Registry, RegistrySchema, ServerEntry


class MCPServerRegistry:
    """Main registry class for managing MCP server configurations."""
    
    def __init__(self, registry_path: Optional[Union[str, Path]] = None):
        """Initialize registry from file or create empty registry."""
        self.registry_path = Path(registry_path) if registry_path else None
        self.registry = None
        
        if self.registry_path and self.registry_path.exists():
            self.load_registry()
        else:
            self.registry = Registry(version="1.0", servers={})
    
    def load_registry(self, registry_path: Optional[Union[str, Path]] = None) -> None:
        """Load registry from file."""
        if registry_path:
            self.registry_path = Path(registry_path)
        
        if not self.registry_path or not self.registry_path.exists():
            raise FileNotFoundError(f"Registry file not found: {self.registry_path}")
        
        self.registry = RegistrySchema.load_from_file(str(self.registry_path))
    
    def save_registry(self, registry_path: Optional[Union[str, Path]] = None) -> None:
        """Save registry to file."""
        if registry_path:
            self.registry_path = Path(registry_path)
        
        if not self.registry_path:
            raise ValueError("No registry path specified")
        
        # Ensure directory exists
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict for serialization
        data = self._registry_to_dict()
        
        # Save as YAML or JSON based on extension
        if self.registry_path.suffix in ['.yaml', '.yml']:
            with open(self.registry_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
        else:
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    def add_server(self, server_id: str, server: ServerEntry) -> None:
        """Add or update server in registry."""
        if not self.registry:
            self.registry = Registry(version="1.0", servers={})
        
        self.registry.servers[server_id] = server
    
    def remove_server(self, server_id: str) -> bool:
        """Remove server from registry. Returns True if server was removed."""
        if not self.registry or server_id not in self.registry.servers:
            return False
        
        del self.registry.servers[server_id]
        return True
    
    def get_server(self, server_id: str) -> Optional[ServerEntry]:
        """Get server configuration by ID."""
        if not self.registry:
            return None
        
        return self.registry.servers.get(server_id)
    
    def list_servers(self, deployment: Optional[str] = None, category: Optional[str] = None) -> List[str]:
        """List available servers, optionally filtered by deployment type or category."""
        if not self.registry:
            return []
        
        servers = list(self.registry.servers.keys())
        
        # Filter by deployment type
        if deployment:
            try:
                dep_type = DeploymentType(deployment)
                servers = [sid for sid in servers 
                          if self.registry.servers[sid].deployment == dep_type]
            except ValueError:
                return []
        
        # Filter by category
        if category and self.registry.categories:
            category_servers = self.registry.categories.get(category, [])
            servers = [sid for sid in servers if sid in category_servers]
        
        return sorted(servers)
    
    def search_servers(self, query: str) -> List[str]:
        """Search servers by name, description, or capabilities."""
        if not self.registry:
            return []
        
        query = query.lower()
        results = []
        
        for server_id, server in self.registry.servers.items():
            # Search in name and description
            if (query in server.name.lower() or 
                query in server.description.lower() or
                query in server_id.lower()):
                results.append(server_id)
                continue
            
            # Search in capabilities
            if server.capabilities:
                if server.capabilities.tools and any(query in tool.lower() for tool in server.capabilities.tools):
                    results.append(server_id)
                    continue
                if server.capabilities.resources and any(query in res.lower() for res in server.capabilities.resources):
                    results.append(server_id)
                    continue
                if server.capabilities.prompts and any(query in prompt.lower() for prompt in server.capabilities.prompts):
                    results.append(server_id)
                    continue
        
        return sorted(results)
    
    def get_categories(self) -> Dict[str, List[str]]:
        """Get all categories and their servers."""
        if not self.registry or not self.registry.categories:
            return {}
        
        return dict(self.registry.categories)
    
    def add_to_category(self, category: str, server_id: str) -> None:
        """Add server to category."""
        if not self.registry:
            return
        
        if not self.registry.categories:
            self.registry.categories = {}
        
        if category not in self.registry.categories:
            self.registry.categories[category] = []
        
        if server_id not in self.registry.categories[category]:
            self.registry.categories[category].append(server_id)
    
    def remove_from_category(self, category: str, server_id: str) -> bool:
        """Remove server from category. Returns True if removed."""
        if (not self.registry or not self.registry.categories or 
            category not in self.registry.categories):
            return False
        
        if server_id in self.registry.categories[category]:
            self.registry.categories[category].remove(server_id)
            
            # Remove category if empty
            if not self.registry.categories[category]:
                del self.registry.categories[category]
            
            return True
        
        return False
    
    def to_claude_desktop(self, server_id: str) -> Dict:
        """Convert server config to Claude Desktop format."""
        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Server '{server_id}' not found")
        
        return FormatConverter.to_claude_desktop(server, server_id)
    
    def to_github_mcp(self, server_id: str) -> Dict:
        """Convert server config to GitHub MCP format."""
        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Server '{server_id}' not found")
        
        return FormatConverter.to_github_mcp(server, server_id)
    
    def to_dxt_manifest(self, server_id: str) -> Dict:
        """Convert server config to DXT manifest format."""
        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Server '{server_id}' not found")
        
        return FormatConverter.to_dxt_manifest(server, server_id)
    
    def to_hosts_format(self, server_id: str) -> str:
        """Convert server config to Linux hosts file format."""
        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Server '{server_id}' not found")
        
        return FormatConverter.to_hosts_format(server, server_id)
    
    def import_claude_desktop(self, config: Dict) -> int:
        """Import servers from Claude Desktop configuration. Returns count of imported servers."""
        imported_servers = FormatConverter.from_claude_desktop(config)
        
        for server_id, server_data in imported_servers.items():
            # Create ServerEntry from converted data
            errors = RegistrySchema.validate_server_entry(server_data)
            if errors:
                print(f"Warning: Skipping server '{server_id}' due to validation errors: {errors}")
                continue
            
            server = RegistrySchema.parse_server_entry(server_data)
            self.add_server(server_id, server)
        
        return len(imported_servers)
    
    def validate_server(self, server_id: str) -> Dict[str, str]:
        """Validate server configuration and return any errors."""
        server = self.get_server(server_id)
        if not server:
            return {"server": "Server not found"}
        
        # Convert back to dict for validation
        server_dict = self._server_to_dict(server)
        return RegistrySchema.validate_server_entry(server_dict)
    
    def _registry_to_dict(self) -> Dict:
        """Convert registry object to dictionary for serialization."""
        if not self.registry:
            return {"version": "1.0", "servers": {}}
        
        data = {
            "version": self.registry.version,
            "servers": {}
        }
        
        for server_id, server in self.registry.servers.items():
            data["servers"][server_id] = self._server_to_dict(server)  # type: ignore[index]
        
        if self.registry.categories:
            data["categories"] = dict(self.registry.categories)
        
        return data
    
    def _server_to_dict(self, server: ServerEntry) -> Dict:
        """Convert ServerEntry to dictionary."""
        result: Dict[str, Any] = {
            "name": server.name,
            "description": server.description,
            "version": server.version,
            "deployment": server.deployment.value,
            "config": {
                "transport": server.config.transport.value
            }
        }
        
        # Add optional config fields
        if server.config.command:
            result["config"]["command"] = server.config.command
        if server.config.args:
            result["config"]["args"] = server.config.args
        if server.config.url:
            result["config"]["url"] = server.config.url
        if server.config.headers:
            result["config"]["headers"] = server.config.headers
        if server.config.env:
            result["config"]["env"] = server.config.env
        if server.config.working_dir:
            result["config"]["working_dir"] = server.config.working_dir
        if server.config.timeout != 30:
            result["config"]["timeout"] = server.config.timeout
        
        # Add optional top-level fields
        if server.license:
            result["license"] = server.license
        if server.source_url:
            result["source_url"] = server.source_url
        
        if server.capabilities:
            caps = {}
            if server.capabilities.tools:
                caps["tools"] = server.capabilities.tools
            if server.capabilities.resources:
                caps["resources"] = server.capabilities.resources
            if server.capabilities.prompts:
                caps["prompts"] = server.capabilities.prompts
            if caps:
                result["capabilities"] = caps
        
        if server.requirements:
            reqs: Dict[str, Any] = {}
            if server.requirements.platforms:
                reqs["platforms"] = server.requirements.platforms
            if server.requirements.runtimes:
                reqs["runtimes"] = server.requirements.runtimes
            if server.requirements.dependencies:
                reqs["dependencies"] = server.requirements.dependencies
            if server.requirements.network is not None:
                reqs["network"] = server.requirements.network
            if reqs:
                result["requirements"] = reqs
        
        if server.security:
            sec: Dict[str, Any] = {}
            if server.security.requires_auth:
                sec["requires_auth"] = server.security.requires_auth
            if server.security.permissions:
                sec["permissions"] = server.security.permissions
            if server.security.sandbox:
                sec["sandbox"] = server.security.sandbox
            if sec:
                result["security"] = sec
        
        if server.compatibility:
            compat = {}
            if server.compatibility.claude_desktop:
                compat["claude_desktop"] = server.compatibility.claude_desktop
            if server.compatibility.mcpconf:
                compat["mcpconf"] = server.compatibility.mcpconf
            if compat:
                result["compatibility"] = compat
        
        return result