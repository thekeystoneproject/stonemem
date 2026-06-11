# stonemem

**Institutional memory for AI agents.**

A compiled Rust MCP server that gives any AI agent platform persistent, structured memory across sessions. Full-text search, entity graphs, temporal scoring, supersession chains — framework-independent and local-first.

![Rust](https://img.shields.io/badge/Built_with-Rust-dea584?style=flat-square) ![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square) ![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-blue?style=flat-square)

## Install

```bash
brew install thekeystoneproject/tap/stonemem
```

Or download the binary from [keystoneproject.dev](https://keystoneproject.dev).

## Quickstart

```bash
# Start the server
stonemem serve

# Activate your license key
stonemem activate SM-XXXX-XXXX-XXXX-XXXX
```

Point any MCP-compatible agent platform at `127.0.0.1:3391`. That's it.

## Configuration

```toml
# ~/.stonemem/config.toml
host = "127.0.0.1"
port = 3391
data_dir = "~/.stonemem"
```

Environment overrides: `STONEMEM_HOST`, `STONEMEM_PORT`, `STONEMEM_DATA_DIR`.

## Features

- **Full-text search** with BM25 ranking
- **Entity extraction** and relationship graph
- **Temporal scoring** — recent knowledge ranked higher
- **Supersession chains** — new facts replace outdated ones
- **Namespace isolation** per agent + shared namespaces
- **Auto-deduplication** across sessions

## Works with

Any platform that speaks MCP connects directly:

- Claude Code / Claude Desktop
- Hermes
- CrewAI
- LangGraph
- OpenHands
- Haystack
- Google ADK
- Microsoft Agent Framework

## Pricing

|                   | Free    | Pro ($9/mo) | Enterprise ($49/mo) |
| ----------------- | ------- | ----------- | ------------------- |
| Memory entries    | 10,000  | Unlimited   | Unlimited           |
| Namespaces        | 1       | Unlimited   | Unlimited           |
| Full-text search  | Yes     | Yes         | Yes                 |
| Deduplication     | Yes     | Yes         | Yes                 |
| Entity graph      | —       | Yes         | Yes                 |
| Temporal scoring  | —       | Yes         | Yes                 |
| Shared namespaces | —       | —           | Yes                 |

Get a key at [keystoneproject.dev](https://keystoneproject.dev).

## Data ownership

Your data stays on your machine, in open SQLite databases you own. No cloud dependency. No vendor lock-in.

## Documentation

Full documentation at [keystoneproject.dev/docs](https://keystoneproject.dev/docs/).

## Stone Suite

stonemem is part of the Stone suite — three compiled Rust MCP servers for AI agent infrastructure:

- **stonemem** — Institutional memory *(this repo)*
- **[stonemux](https://github.com/thekeystoneproject/stonemux)** — Multi-agent coordination
- **[stonegate](https://github.com/thekeystoneproject/stonegate)** — Universal tool gateway

## License

[Proprietary](LICENSE) — Copyright (c) 2026 The Keystone Project, Inc. All rights reserved.
