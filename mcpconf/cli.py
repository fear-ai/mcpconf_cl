"""Command-line interface for MCP server registry management."""

import argparse
import sys
import json
import yaml
from pathlib import Path
from typing import Optional

from .registry import MCPServerRegistry
from .schema import RegistrySchema, ServerEntry


def format_server_info(server_id: str, server: ServerEntry, detailed: bool = False) -> str:
    """Format server information for display."""
    if not detailed:
        return f"{server_id:20} {server.deployment.value:8} {server.config.transport.value:8} {server.description}"
    
    lines = [
        f"Server: {server_id}",
        f"Name: {server.name}",
        f"Description: {server.description}",
        f"Version: {server.version}",
        f"Deployment: {server.deployment.value}",
        f"Transport: {server.config.transport.value}",
    ]
    
    if server.license:
        lines.append(f"License: {server.license}")
    if server.source_url:
        lines.append(f"Source: {server.source_url}")
    
    # Configuration details
    lines.append("\nConfiguration:")
    if server.config.command:
        lines.append(f"  Command: {server.config.command}")
    if server.config.args:
        lines.append(f"  Args: {' '.join(server.config.args)}")
    if server.config.url:
        lines.append(f"  URL: {server.config.url}")
    if server.config.env:
        lines.append("  Environment:")
        for key, value in server.config.env.items():
            lines.append(f"    {key}: {value}")
    
    # Capabilities
    if server.capabilities:
        lines.append("\nCapabilities:")
        if server.capabilities.tools:
            lines.append(f"  Tools: {', '.join(server.capabilities.tools)}")
        if server.capabilities.resources:
            lines.append(f"  Resources: {', '.join(server.capabilities.resources)}")
        if server.capabilities.prompts:
            lines.append(f"  Prompts: {', '.join(server.capabilities.prompts)}")
    
    # Requirements
    if server.requirements:
        lines.append("\nRequirements:")
        if server.requirements.platforms:
            lines.append(f"  Platforms: {', '.join(server.requirements.platforms)}")
        if server.requirements.runtimes:
            for runtime, version in server.requirements.runtimes.items():
                lines.append(f"  {runtime}: {version}")
    
    return "\n".join(lines)


def cmd_list(args) -> None:
    """List servers command."""
    registry = MCPServerRegistry(args.registry)
    servers = registry.list_servers(deployment=args.deployment, category=args.category)
    
    if not servers:
        print("No servers found.")
        return
    
    if not args.detailed:
        print(f"{'NAME':<20} {'DEPLOY':<8} {'TRANSPORT':<10} {'DESCRIPTION'}")
        print("-" * 70)
    
    for server_id in servers:
        server = registry.get_server(server_id)
        if server:
            print(format_server_info(server_id, server, args.detailed))
            if args.detailed and server_id != servers[-1]:
                print()


def cmd_show(args) -> None:
    """Show server details command."""
    registry = MCPServerRegistry(args.registry)
    server = registry.get_server(args.server)
    
    if not server:
        print(f"Server '{args.server}' not found.")
        sys.exit(1)
    
    print(format_server_info(args.server, server, detailed=True))


def cmd_search(args) -> None:
    """Search servers command."""
    registry = MCPServerRegistry(args.registry)
    results = registry.search_servers(args.query)
    
    if not results:
        print(f"No servers found matching '{args.query}'.")
        return
    
    print(f"Found {len(results)} servers:")
    print(f"{'NAME':<20} {'DEPLOY':<8} {'TRANSPORT':<10} {'DESCRIPTION'}")
    print("-" * 70)
    
    for server_id in results:
        server = registry.get_server(server_id)
        if server:
            print(format_server_info(server_id, server))


def cmd_convert(args) -> None:
    """Convert server configuration command."""
    registry = MCPServerRegistry(args.registry)
    
    try:
        if args.format == "claude":
            result = registry.to_claude_desktop(args.server)
        elif args.format == "github":
            result = registry.to_github_mcp(args.server)
        elif args.format == "dxt":
            result = registry.to_dxt_manifest(args.server)
        elif args.format == "hosts":
            result = registry.to_hosts_format(args.server)
            print(result)
            return
        else:
            print(f"Unknown format: {args.format}")
            sys.exit(1)
        
        if args.output:
            with open(args.output, 'w') as f:
                if args.output.endswith('.yaml') or args.output.endswith('.yml'):
                    yaml.dump(result, f, default_flow_style=False, indent=2)
                else:
                    json.dump(result, f, indent=2)
            print(f"Configuration written to {args.output}")
        else:
            print(json.dumps(result, indent=2))
    
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_validate(args) -> None:
    """Validate server configuration command."""
    registry = MCPServerRegistry(args.registry)
    
    if args.server:
        # Validate specific server
        errors = registry.validate_server(args.server)
        if errors:
            print(f"Validation errors for '{args.server}':")
            for field, error in errors.items():
                print(f"  {field}: {error}")
            sys.exit(1)
        else:
            print(f"Server '{args.server}' is valid.")
    else:
        # Validate all servers
        all_valid = True
        for server_id in registry.list_servers():
            errors = registry.validate_server(server_id)
            if errors:
                all_valid = False
                print(f"Validation errors for '{server_id}':")
                for field, error in errors.items():
                    print(f"  {field}: {error}")
        
        if all_valid:
            print("All servers are valid.")
        else:
            sys.exit(1)


def cmd_categories(args) -> None:
    """List categories command."""
    registry = MCPServerRegistry(args.registry)
    categories = registry.get_categories()
    
    if not categories:
        print("No categories defined.")
        return
    
    for category, servers in categories.items():
        print(f"{category}: {', '.join(servers)}")


def cmd_import(args) -> None:
    """Import from Claude Desktop configuration command."""
    if not Path(args.config).exists():
        print(f"Configuration file not found: {args.config}")
        sys.exit(1)
    
    with open(args.config, 'r') as f:
        if args.config.endswith('.yaml') or args.config.endswith('.yml'):
            config = yaml.safe_load(f)
        else:
            config = json.load(f)
    
    # Initialize registry, creating empty if file doesn't exist
    registry = MCPServerRegistry()
    if Path(args.registry).exists():
        registry.load_registry(args.registry)
    registry.registry_path = Path(args.registry)
    
    count = registry.import_claude_desktop(config)
    
    if args.save:
        registry.save_registry()
        print(f"Imported {count} servers and saved to registry.")
    else:
        print(f"Imported {count} servers (not saved, use --save to persist).")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Server Registry Management",
        prog="mcpconf"
    )
    parser.add_argument(
        "--registry", "-r",
        default="mcp-registry.yaml",
        help="Registry file path (default: mcp-registry.yaml)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List servers")
    list_parser.add_argument("--deployment", choices=["local", "remote", "hybrid"], help="Filter by deployment type")
    list_parser.add_argument("--category", help="Filter by category")
    list_parser.add_argument("--detailed", "-d", action="store_true", help="Show detailed information")
    list_parser.set_defaults(func=cmd_list)
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show server details")
    show_parser.add_argument("server", help="Server ID to show")
    show_parser.set_defaults(func=cmd_show)
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search servers")
    search_parser.add_argument("query", help="Search query")
    search_parser.set_defaults(func=cmd_search)
    
    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert server configuration")
    convert_parser.add_argument("server", help="Server ID to convert")
    convert_parser.add_argument("format", choices=["claude", "github", "dxt", "hosts"], help="Target format")
    convert_parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    convert_parser.set_defaults(func=cmd_convert)
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate server configuration")
    validate_parser.add_argument("server", nargs="?", help="Server ID to validate (default: all)")
    validate_parser.set_defaults(func=cmd_validate)
    
    # Categories command
    categories_parser = subparsers.add_parser("categories", help="List categories")
    categories_parser.set_defaults(func=cmd_categories)
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import from Claude Desktop configuration")
    import_parser.add_argument("config", help="Claude Desktop configuration file")
    import_parser.add_argument("--save", action="store_true", help="Save to registry after import")
    import_parser.set_defaults(func=cmd_import)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()