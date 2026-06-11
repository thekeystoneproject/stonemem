"""
stonemem Memory Adapter for Google Agent Development Kit (ADK).
MIT Licensed — Blink Authority, Inc.

Implements a memory service compatible with Google ADK's memory/session
interface, routing all operations to the stonemem REST API on localhost:3391.

Usage:
    from stonemem_google_adk import StonememGoogleADKMemory
    memory = StonememGoogleADKMemory()
    memory.save_session_state(session_id, state)
    context = memory.load_memory(query="user preferences")
"""

from __future__ import annotations

import os
import json
import httpx

STONEMEM_URL = os.getenv("STONEMEM_URL", "http://127.0.0.1:3391")


class StonememGoogleADKMemory:
    """Google ADK-compatible memory service backed by stonemem."""

    def __init__(self, agent_id: str = "google-adk", namespace: str = "default", url: str = None):
        self._url = url or STONEMEM_URL
        self._client = httpx.Client(base_url=self._url, timeout=10.0)
        self._agent_id = agent_id
        self._namespace = namespace
        self._register()

    def _register(self):
        try:
            self._client.post("/agent/register", json={
                "agent_id": self._agent_id,
                "role": "google-adk-agent",
            })
        except Exception:
            pass

    def save_session_state(self, session_id: str, state: dict) -> dict:
        """Save session state as a memory entry."""
        content = json.dumps({
            "type": "session_state",
            "session_id": session_id,
            "state": state,
        })

        try:
            r = self._client.post("/save", json={
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "content": content,
                "tags": ["session", f"session:{session_id}"],
            })
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            return {"error": str(e)}
        return {}

    def load_session_state(self, session_id: str) -> dict | None:
        """Load the most recent session state."""
        try:
            r = self._client.post("/search", json={
                "query": f"session_state session:{session_id}",
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "limit": 1,
                "tags": [f"session:{session_id}"],
            })
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    data = json.loads(results[0]["content"])
                    return data.get("state")
        except Exception:
            pass
        return None

    def save_memory(self, content: str, tags: list = None) -> dict:
        """Save a long-term memory entry."""
        try:
            r = self._client.post("/save", json={
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "content": content,
                "tags": (tags or []) + ["memory"],
            })
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            return {"error": str(e)}
        return {}

    def load_memory(self, query: str, limit: int = 5) -> str:
        """Load relevant memory context for a query."""
        try:
            r = self._client.post("/recall", json={
                "query": query,
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "limit": limit,
            })
            if r.status_code == 200:
                return r.json().get("context", "")
        except Exception:
            pass
        return ""

    def search_memory(self, query: str, limit: int = 10, tags: list = None) -> list:
        """Search memory with optional tag filters."""
        try:
            r = self._client.post("/search", json={
                "query": query,
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "limit": limit,
                "tags": tags or [],
            })
            if r.status_code == 200:
                return r.json().get("results", [])
        except Exception:
            pass
        return []

    def get_entities(self, query: str) -> list:
        """Query the entity knowledge graph."""
        try:
            r = self._client.post("/entity/query", json={
                "query": query,
                "limit": 10,
            })
            if r.status_code == 200:
                return r.json().get("entities", [])
        except Exception:
            pass
        return []

    def tool_definitions(self) -> list:
        """Return tool definitions for Google ADK function calling."""
        return [
            {
                "name": "stonemem_search",
                "description": "Search institutional memory for past knowledge and facts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "stonemem_save",
                "description": "Save important knowledge for future recall.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["content"],
                },
            },
        ]

    def handle_tool_call(self, name: str, args: dict) -> str:
        """Handle a tool call from the agent."""
        if name == "stonemem_search":
            results = self.search_memory(args["query"], limit=args.get("limit", 5))
            return json.dumps(results)
        elif name == "stonemem_save":
            result = self.save_memory(args["content"], tags=args.get("tags", []))
            return json.dumps(result)
        return json.dumps({"error": f"Unknown tool: {name}"})

    def close(self):
        try:
            self._client.post("/agent/deregister", json={"agent_id": self._agent_id})
        except Exception:
            pass
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
