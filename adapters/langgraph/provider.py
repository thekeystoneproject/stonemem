"""
stonemem Memory Adapter for LangGraph.
MIT Licensed — Blink Authority, Inc.

Implements a LangGraph-compatible checkpointer and memory store
that routes to the stonemem REST API on localhost:3391.

Usage:
    from stonemem_langgraph import StonememCheckpointer
    checkpointer = StonememCheckpointer()
    graph = StateGraph(State)
    graph.compile(checkpointer=checkpointer)
"""

from __future__ import annotations

import os
import json
import hashlib
import httpx

STONEMEM_URL = os.getenv("STONEMEM_URL", "http://127.0.0.1:3391")


class StonememCheckpointer:
    """LangGraph-compatible checkpointer backed by stonemem."""

    def __init__(self, agent_id: str = "langgraph", namespace: str = "default", url: str = None):
        self._url = url or STONEMEM_URL
        self._client = httpx.Client(base_url=self._url, timeout=10.0)
        self._agent_id = agent_id
        self._namespace = namespace
        self._register()

    def _register(self):
        try:
            self._client.post("/agent/register", json={
                "agent_id": self._agent_id,
                "role": "langgraph-checkpointer",
            })
        except Exception:
            pass

    def put(self, config: dict, checkpoint: dict, metadata: dict = None) -> dict:
        """Save a checkpoint. Called by LangGraph after each node execution."""
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        content = json.dumps({
            "type": "checkpoint",
            "thread_id": thread_id,
            "checkpoint": checkpoint,
            "metadata": metadata or {},
        })
        tags = ["checkpoint", f"thread:{thread_id}"]

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

    def get(self, config: dict) -> dict | None:
        """Retrieve the latest checkpoint for a thread."""
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        try:
            r = self._client.post("/search", json={
                "query": f"checkpoint thread:{thread_id}",
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "limit": 1,
                "tags": [f"thread:{thread_id}"],
            })
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    data = json.loads(results[0]["content"])
                    return data.get("checkpoint")
        except Exception:
            pass
        return None

    def list(self, config: dict, limit: int = 10) -> list:
        """List checkpoints for a thread."""
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        try:
            r = self._client.post("/search", json={
                "query": f"checkpoint thread:{thread_id}",
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "limit": limit,
                "tags": [f"thread:{thread_id}"],
            })
            if r.status_code == 200:
                return r.json().get("results", [])
        except Exception:
            pass
        return []

    def save_memory(self, key: str, value: str, tags: list = None) -> dict:
        """Save a long-term memory entry (cross-thread)."""
        try:
            r = self._client.post("/save", json={
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "content": f"[{key}] {value}",
                "tags": (tags or []) + ["memory", f"key:{key}"],
            })
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return {}

    def search_memory(self, query: str, limit: int = 5, tags: list = None) -> list:
        """Search long-term memory entries."""
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

    def recall_memory(self, query: str, limit: int = 5) -> str:
        """Recall long-term memory context."""
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

    def close(self):
        try:
            self._client.post("/agent/deregister", json={"agent_id": self._agent_id})
        except Exception:
            pass
        self._client.close()
