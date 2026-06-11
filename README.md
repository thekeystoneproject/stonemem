# stonemem

**Institutional memory engine for AI agents.**

![Rust](https://img.shields.io/badge/Built_with-Rust-dea584?style=flat-square) ![MCP](https://img.shields.io/badge/MCP-compatible-blue?style=flat-square) ![Platforms](https://img.shields.io/badge/Adapters-7_platforms-green?style=flat-square) ![License](https://img.shields.io/badge/License-BSL_1.1-yellow?style=flat-square)

stonemem gives any AI agent framework persistent, searchable, institutional memory. Save context, recall it later, deduplicate automatically, and build entity graphs across sessions. One binary, zero dependencies, works with every major agent platform.

## Install

```bash
brew install thekeystoneproject/tap/stonemem
```

Or download the binary from [Releases](https://github.com/thekeystoneproject/stonemem/releases).

## Quick Start

```bash
# Start the server
stonemem serve

# Save a memory
curl -X POST http://127.0.0.1:3391/save \
  -H "Content-Type: application/json" \
  -d '{"namespace": "default", "content": "The API uses JWT tokens with 24h TTL", "tags": ["auth", "api"]}'

# Search memories
curl "http://127.0.0.1:3391/search?q=JWT+tokens&namespace=default"

# Check status
curl http://127.0.0.1:3391/health
```

## Adapters

MIT-licensed adapters for every major AI agent framework. Drop in and go.

| Platform | Directory | Description |
|----------|-----------|-------------|
| [Hermes](adapters/hermes/) | `adapters/hermes/` | Agent memory provider |
| [CrewAI](adapters/crewai/) | `adapters/crewai/` | Crew memory backend |
| [LangGraph](adapters/langgraph/) | `adapters/langgraph/` | State checkpointer |
| [Haystack](adapters/haystack/) | `adapters/haystack/` | Document store |
| [OpenHands](adapters/openhands/) | `adapters/openhands/` | Agent memory |
| [MS Agent Framework](adapters/ms_agent/) | `adapters/ms_agent/` | Memory provider |
| [Google ADK](adapters/google_adk/) | `adapters/google_adk/` | Memory service |

Each adapter is a thin Python shim (~150 LOC) that implements the platform's memory interface and routes all operations to the stonemem REST API.

## Configuration

```toml
# ~/.stonemem/config.toml
host = "127.0.0.1"
port = 3391
data_dir = "~/.stonemem"
```

Environment overrides: `STONEMEM_HOST`, `STONEMEM_PORT`, `STONEMEM_DATA_DIR`

## Pricing

| Feature | Free | Pro ($9/mo) | Enterprise |
|---------|------|-------------|------------|
| Memory entries | 10,000 | Unlimited | Unlimited |
| Namespaces | 1 | Unlimited | Unlimited |
| Full-text search | Yes | Yes | Yes |
| Deduplication | Yes | Yes | Yes |
| Entity graph | — | Yes | Yes |
| Temporal scoring | — | Yes | Yes |
| Shared namespaces | — | — | Yes |

Get a license key at [keystoneproject.dev](https://keystoneproject.dev).

## Links

- [keystoneproject.dev](https://keystoneproject.dev) — Product site and docs
- [stonegate](https://github.com/thekeystoneproject/stonegate) — MCP tool gateway
- [stonemux](https://github.com/thekeystoneproject/stonemux) — Multi-agent coordination

## License

The stonemem binary is licensed under [BSL 1.1](LICENSE). Adapters are [MIT licensed](adapters/LICENSE).

Built by [The Keystone Project](https://keystoneproject.dev).
