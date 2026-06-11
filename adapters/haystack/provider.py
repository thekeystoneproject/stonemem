"""
stonemem Memory Adapter for Haystack.
MIT Licensed — Blink Authority, Inc.

Implements a Haystack-compatible DocumentStore that routes storage
and retrieval to the stonemem REST API on localhost:3391.

Usage:
    from stonemem_haystack import StonememDocumentStore
    store = StonememDocumentStore()
    store.write_documents([Document(content="...")])
    results = store.filter_documents(filters={"query": "search term"})
"""

import os
import json
import hashlib
from dataclasses import dataclass, field
from typing import Any
import httpx

STONEMEM_URL = os.getenv("STONEMEM_URL", "http://127.0.0.1:3391")


@dataclass
class Document:
    content: str
    id: str = ""
    meta: dict = field(default_factory=dict)
    score: float = 0.0


class StonememDocumentStore:
    """Haystack-compatible document store backed by stonemem."""

    def __init__(self, agent_id: str = "haystack", namespace: str = "default", url: str = None):
        self._url = url or STONEMEM_URL
        self._client = httpx.Client(base_url=self._url, timeout=10.0)
        self._agent_id = agent_id
        self._namespace = namespace
        self._register()

    def _register(self):
        try:
            self._client.post("/agent/register", json={
                "agent_id": self._agent_id,
                "role": "haystack-store",
            })
        except Exception:
            pass

    def count_documents(self) -> int:
        """Return the number of documents in the store."""
        try:
            r = self._client.get("/stats")
            if r.status_code == 200:
                return r.json().get("entry_count", 0)
        except Exception:
            pass
        return 0

    def write_documents(self, documents: list, policy: str = "overwrite") -> int:
        """Write documents to the store. Returns number written."""
        written = 0
        for doc in documents:
            content = doc.content if isinstance(doc, Document) else doc.get("content", str(doc))
            tags = []
            meta = doc.meta if isinstance(doc, Document) else doc.get("meta", {})
            if meta:
                tags = meta.get("tags", [])

            try:
                r = self._client.post("/save", json={
                    "agent_id": self._agent_id,
                    "namespace": self._namespace,
                    "content": content,
                    "tags": tags,
                })
                if r.status_code == 200:
                    written += 1
            except Exception:
                pass
        return written

    def filter_documents(self, filters: dict = None) -> list:
        """Filter documents by query and metadata."""
        if not filters:
            filters = {}

        query = filters.get("query", "")
        tags = filters.get("tags", [])
        limit = filters.get("limit", 10)

        try:
            r = self._client.post("/search", json={
                "query": query,
                "agent_id": self._agent_id,
                "namespace": self._namespace,
                "limit": limit,
                "tags": tags,
            })
            if r.status_code == 200:
                results = r.json().get("results", [])
                return [
                    Document(
                        content=res["content"],
                        id=str(res["id"]),
                        meta={"tags": res.get("tags", []), "saved_at": res.get("saved_at", "")},
                        score=res.get("score", 0.0),
                    )
                    for res in results
                ]
        except Exception:
            pass
        return []

    def delete_documents(self, document_ids: list) -> None:
        """Delete is a no-op — stonemem preserves history via supersession."""
        pass

    def recall(self, query: str, limit: int = 5) -> str:
        """Recall formatted context for a query."""
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
