# Claude Code Instructions - mcpconf Project

mcpconf is a production-ready MCP Server Registry and Configuration Management tool

- CLI command is `mcpconf` with entry point `mcpconf.cli:main`
- Follow existing patterns in mcpconf, use existing imports and libraries (PyYAML for YAML handling) and type annotations
- Validate against real-world server configurations
- Provide clear, actionable error messages

## Development Workflow
1. Review
- README.md: User-focused installation and usage
- MCP_REGISTRY.md: Complete technical specification and implementation details  
- STATUS.md: Project status, completed tasks, and roadmap
2. Review existing code before making changes
3. Test to verify current working state: `python -m pytest tests/ -v`
4. Update documentation if functionality changed
