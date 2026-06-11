"""
stonemem Memory Adapter for CrewAI.
MIT Licensed — Blink Authority, Inc.

Implements CrewAI's memory interface, routing storage and retrieval
to the stonemem REST API on localhost:3391.

Usage:
    from stonemem_crewai import StonememCrewAIMemory
    crew = Crew(
        agents=[...],
        tasks=[...],
        memory=StonememCrewAIMemory(),
    )
"""

import os
import json
import httpx

STONEMEM_URL = os.getenv("STONEMEM_URL", "http://127.0.0.1:3391")


class StonememCrewAIMemory:
    """CrewAI-compatible memory backend powered by stonemem."""

    def __init__(self, agent_id: str = "crewai", namespace: str = "default", url: str = None):
        self._url = url or STONEMEM_URL
        self._client = httpx.Client(base_url=self._url, timeout=10.0)
        self._agent_id = agent_id
        self._namespace = namespace
        self._register()

    def _register(self):
        try:
            self._client.post("/agent/register", json={
                "agent_id": self._agent_id,
                "role": "crewai-agent",
            })
        except Exception:
            pass

    def save(self, content: str, metadata: dict = None) -> dict:
        """Save a memory entry. Called by CrewAI after task execution."""
        tags = []
        if metadata:
            tags = metadata.get("tags", [])
            if "task" in metadata:
                tags.append("task")
            if "agent" in metadata:
                tags.append(f"agent:{metadata['agent']}")

        try:
            r = self._client.post("/save", json={
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "content": content,
                "tags": tags,
                "supersedes": metadata.get("supersedes") if metadata else None,
            })
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            return {"error": str(e)}
        return {"error": f"HTTP {r.status_code}"}

    def search(self, query: str, limit: int = 5, **kwargs) -> list:
        """Search memory. Called by CrewAI for context retrieval."""
        try:
            r = self._client.post("/search", json={
                "query": query,
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "limit": limit,
                "tags": kwargs.get("tags", []),
            })
            if r.status_code == 200:
                return r.json().get("results", [])
        except Exception:
            pass
        return []

    def recall(self, query: str, limit: int = 5) -> str:
        """Recall context for a query. Returns formatted markdown."""
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
        """Get formatted context for a query. Used by CrewAI for prompt injection."""
        return self.recall(query, limit=limit)

    def reset(self) -> None:
        """Reset is a no-op — stonemem preserves history."""
        pass

    def close(self):
        """Deregister and close the HTTP client."""
        try:
            self._client.post("/agent/deregister", json={
                "agent_id": self._agent_id,
            })
        except Exception:
            pass
        self._client.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
