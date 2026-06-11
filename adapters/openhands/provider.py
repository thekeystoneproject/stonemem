"""
stonemem Memory Adapter for OpenHands (formerly OpenDevin).
MIT Licensed — Blink Authority, Inc.

Implements OpenHands' memory/knowledge interface, routing operations
to the stonemem REST API on localhost:3391.

Usage:
    from stonemem_openhands import StonememOpenHandsMemory
    memory = StonememOpenHandsMemory()
    memory.add("User prefers Rust", tags=["preference"])
    results = memory.search("language preference")
"""

import os
import json
import httpx

STONEMEM_URL = os.getenv("STONEMEM_URL", "http://127.0.0.1:3391")


class StonememOpenHandsMemory:
    """OpenHands-compatible memory backend powered by stonemem."""

    def __init__(self, agent_id: str = "openhands", namespace: str = "default", url: str = None):
        self._url = url or STONEMEM_URL
        self._client = httpx.Client(base_url=self._url, timeout=10.0)
        self._agent_id = agent_id
        self._namespace = namespace
        self._register()

    def _register(self):
        try:
            self._client.post("/agent/register", json={
                "agent_id": self._agent_id,
                "role": "openhands-agent",
            })
        except Exception:
            pass

    def add(self, content: str, tags: list = None, supersedes: int = None) -> dict:
        """Add a memory entry."""
        try:
            r = self._client.post("/save", json={
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "content": content,
                "tags": tags or [],
                "supersedes": supersedes,
            })
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            return {"error": str(e)}
        return {}

    def search(self, query: str, limit: int = 5, tags: list = None) -> list:
        """Search memory entries."""
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

    def recall(self, query: str, limit: int = 5) -> str:
        """Recall context for a query, formatted as markdown."""
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

    def get_context(self, query: str, limit: int = 5) -> str:
        """Get formatted context for prompt injection."""
        return self.recall(query, limit=limit)

    def get_entities(self, query: str, entity_type: str = None) -> list:
        """Query the entity graph."""
        try:
            payload = {"query": query, "limit": 10}
            if entity_type:
                payload["entity_type"] = entity_type
            r = self._client.post("/entity/query", json=payload)
            if r.status_code == 200:
                return r.json().get("entities", [])
        except Exception:
            pass
        return []

    def add_observation(self, task: str, result: str) -> dict:
        """Record a task observation (for agent delegation patterns)."""
        return self.add(
            content=f"Task observation:\nTask: {task}\nResult: {result}",
            tags=["observation", "task"],
        )

    def get_stats(self) -> dict:
        """Get memory statistics."""
        try:
            r = self._client.get("/stats")
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return {}

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
