# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-02-05

### Added
- MCP server for direct tool calling (`keep-mcp` command)
- MCP tools: `keep_send`, `keep_discover`, `keep_discover_agents`, `keep_listen`, `keep_ensure_server`
- Optional MCP dependency: `pip install keep-protocol[mcp]`
- Entry point: `python -m keep.mcp` or `keep-mcp` CLI

### Performance
- MCP tools achieve <60ms latency vs 80-150s with skill-based approach (118x faster)

### Changed
- Minimum Python version raised to 3.10 (MCP SDK requirement)

## [0.4.0] - 2026-02-01

### Added
- `ensure_server()` convenience function for auto-starting keep server
- Docker support with multi-arch image
- Go fallback for server startup when Docker unavailable
- Server discovery methods: `discover()`, `discover_agents()`

### Fixed
- pytest fixture scope errors in CI
- go vet scope issues

## [0.3.0] - 2026-01-25

### Added
- Initial Python SDK release (`KeepClient`)
- Ed25519 signed packets over TCP + Protobuf
- Agent registration and routing
- Scar/memory data exchange support
- Go server implementation

### Features
- Send/receive signed packets between agents
- Server-side agent routing by identity
- TTL and fee fields for packet metadata
