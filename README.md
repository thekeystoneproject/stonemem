# stonemem

**Persistent memory for AI agents.**

![Rust](https://img.shields.io/badge/Built_with-Rust-dea584?style=flat-square) ![License](https://img.shields.io/badge/License-BSL_1.1-yellow?style=flat-square)

A compiled Rust server that gives AI agents persistent, searchable memory across sessions. Full-text search, deduplication, entity graphs, temporal scoring, and namespace isolation. Runs locally on port 3391, zero cloud dependencies.

Works with **Hermes**, **CrewAI**, **LangGraph**, **Haystack**, **OpenHands**, **MS Agent Framework**, and **Google ADK** out of the box.

## Install

```bash
brew install thekeystoneproject/tap/stonemem
```

Or download from [Releases](https://github.com/thekeystoneproject/stonemem/releases).

## Quick Start

```bash
stonemem serve
```

### With CrewAI

```python
from stonemem_crewai import StonememCrewAIMemory

crew = Crew(
    agents=[...],
    tasks=[...],
    memory=StonememCrewAIMemory(),
)
```

### With Hermes

```python
from stonemem_hermes import StonememProvider

# Register as a memory provider — stonemem handles the full lifecycle:
# initialization, prefetch, tool schemas, turn sync, pre-compression extraction
ctx.register_memory_provider("stonemem", StonememProvider)
```

### With LangGraph

```python
from stonemem_langgraph import StonememCheckpointer

graph = StateGraph(State)
graph.compile(checkpointer=StonememCheckpointer())
```

## REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/save` | POST | Save a memory with namespace, tags, and optional supersession |
| `/search` | POST | Full-text search with agent/namespace/tag filtering |
| `/recall` | POST | Contextual recall — returns formatted markdown for prompt injection |
| `/entity` | GET/POST | Entity graph queries and traversal |
| `/agent/register` | POST | Register an agent with role and session |
| `/agent/deregister` | POST | Deregister an agent |
| `/stats` | GET | Memory statistics and namespace breakdown |
| `/health` | GET | Server health check |

## Framework Adapters

Each adapter implements the framework's native memory interface and routes to stonemem's REST API. Not wrappers — full lifecycle integrations with tool schemas, auto-start, session management, and pre-compression hooks.

| Framework | Adapter | What it implements |
|-----------|---------|-------------------|
| [Hermes](adapters/hermes/) | `StonememProvider` | Full `MemoryProvider` — tool schemas, prefetch, turn sync, delegation hooks, pre-compression extraction |
| [CrewAI](adapters/crewai/) | `StonememCrewAIMemory` | `save`, `search`, `recall`, `get_context` — drop-in replacement for crew memory |
| [LangGraph](adapters/langgraph/) | `StonememCheckpointer` | Graph state checkpointing with cross-session persistence |
| [Haystack](adapters/haystack/) | `StonememDocumentStore` | Document store interface for pipeline memory |
| [OpenHands](adapters/openhands/) | `StonememAgentMemory` | Agent memory with session isolation |
| [MS Agent Framework](adapters/ms_agent/) | `StonememMemoryProvider` | Memory provider for MS agents |
| [Google ADK](adapters/google_adk/) | `StonememMemoryService` | Memory service with ADK lifecycle hooks |

All adapters are MIT licensed.

## Configuration

```toml
# ~/.stonemem/config.toml
host = "127.0.0.1"
port = 3391
data_dir = "~/.stonemem"
```

`STONEMEM_HOST`, `STONEMEM_PORT`, `STONEMEM_DATA_DIR` environment overrides.

## Pricing

| | Free | Pro ($9/mo) | Enterprise |
|---|------|-------------|------------|
| Memory entries | 10,000 | Unlimited | Unlimited |
| Namespaces | 1 | Unlimited | Unlimited |
| Full-text search | Yes | Yes | Yes |
| Deduplication | Yes | Yes | Yes |
| Entity graph | — | Yes | Yes |
| Temporal scoring | — | Yes | Yes |
| Shared namespaces | — | — | Yes |

```bash
stonemem activate SM-XXXX-XXXX-XXXX-XXXX
```

Get a key at [keystoneproject.dev](https://keystoneproject.dev).

## Stone Suite

| Server | Purpose |
|--------|---------|
| **stonemem** | Persistent agent memory |
| [stonemux](https://github.com/thekeystoneproject/stonemux) | Multi-agent coordination |
| [stonegate](https://github.com/thekeystoneproject/stonegate) | MCP tool gateway |

## License

Binary: [BSL 1.1](LICENSE). Adapters: [MIT](adapters/LICENSE).

[The Keystone Project](https://keystoneproject.dev)
