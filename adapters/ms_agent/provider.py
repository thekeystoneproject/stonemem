"""
stonemem Memory Adapter for Microsoft Agent Framework (AutoGen).
MIT Licensed — Blink Authority, Inc.

Implements a memory backend compatible with AutoGen's agent memory interface,
routing all operations to the stonemem REST API on localhost:3391.

Usage:
    from stonemem_msagent import StonememAutoGenMemory
    memory = StonememAutoGenMemory()
    agent = AssistantAgent("assistant", memory=memory)
"""

import os
import json
import httpx

STONEMEM_URL = os.getenv("STONEMEM_URL", "http://127.0.0.1:3391")


class StonememAutoGenMemory:
    """AutoGen-compatible memory backend powered by stonemem."""

    def __init__(self, agent_id: str = "autogen", namespace: str = "default", url: str = None):
        self._url = url or STONEMEM_URL
        self._client = httpx.Client(base_url=self._url, timeout=10.0)
        self._agent_id = agent_id
        self._namespace = namespace
        self._register()

    def _register(self):
        try:
            self._client.post("/agent/register", json={
                "agent_id": self._agent_id,
                "role": "autogen-agent",
            })
        except Exception:
            pass

    def add(self, content: str, metadata: dict = None) -> dict:
        """Add a memory record. Called after each conversation turn."""
        tags = []
        if metadata:
            tags = metadata.get("tags", [])
            if metadata.get("role"):
                tags.append(f"role:{metadata['role']}")

        try:
            r = self._client.post("/save", json={
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "content": content,
                "tags": tags,
            })
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            return {"error": str(e)}
        return {}

    def query(self, query: str, limit: int = 5, **kwargs) -> list:
        """Query memory for relevant records."""
        try:
            r = self._client.post("/search", json={
                "query": query,
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "limit": limit,
                "tags": kwargs.get("tags", []),
            })
            if r.status_code == 200:
                return [
                    {"content": res["content"], "score": res["score"], "id": res["id"]}
                    for res in r.json().get("results", [])
                ]
        except Exception:
            pass
        return []

    def get_context(self, query: str, limit: int = 5) -> str:
        """Get formatted context for injection into agent prompt."""
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

    def update(self, record_id: int, content: str, metadata: dict = None) -> dict:
        """Update a memory record by superseding it."""
        return self.add(content, metadata={"supersedes": record_id, **(metadata or {})})

    def clear(self) -> None:
        """Clear is a no-op — stonemem preserves all history."""
        pass

    def record_conversation(self, sender: str, recipient: str, message: str) -> dict:
        """Record a conversation message between agents."""
        return self.add(
            content=f"{sender} → {recipient}: {message}",
            metadata={"tags": ["conversation", f"from:{sender}", f"to:{recipient}"]},
        )

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
