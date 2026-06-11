"""
stonemem Memory Provider for Hermes agents.
MIT Licensed — Blink Authority, Inc.

Implements the full MemoryProvider lifecycle, routing all operations
to the stonemem REST API on localhost:3391.
"""

import os
import json
import threading
import subprocess
import httpx

try:
    from agent.memory_provider import MemoryProvider as _Base
except ImportError:
    _Base = object

STONEMEM_URL = os.getenv("STONEMEM_URL", "http://127.0.0.1:3391")
STONEMEM_AGENT_ID = os.getenv("STONEMEM_AGENT_ID")
STONEMEM_AUTO_START = os.getenv("STONEMEM_AUTO_START", "true").lower() == "true"


class StonememProvider(_Base):
    name = "stonemem"

    def __init__(self):
        self._client = httpx.Client(base_url=STONEMEM_URL, timeout=10.0)
        self._agent_id = STONEMEM_AGENT_ID
        self._session_id = None
        self._pending = []

    def is_available(self) -> bool:
        try:
            r = self._client.get("/health")
            return r.status_code == 200
        except Exception:
            if STONEMEM_AUTO_START:
                try:
                    subprocess.Popen(
                        ["stonemem", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    import time; time.sleep(1)
                    r = self._client.get("/health")
                    return r.status_code == 200
                except Exception:
                    return False
            return False

    def initialize(self, session_id: str, **kwargs) -> None:
        if not self._agent_id:
            self._agent_id = kwargs.get("profile_name", "default")
        self._session_id = session_id
        self._client.post("/agent/register", json={
            "agent_id": self._agent_id,
            "role": kwargs.get("role"),
            "session_id": session_id,
        })

    def system_prompt_block(self) -> str:
        return (
            "Stonemem institutional memory is active. "
            "Use stonemem_search to find past knowledge and "
            "stonemem_save to store important facts for future recall."
        )

    def prefetch(self, query: str) -> str:
        try:
            r = self._client.post("/recall", json={
                "query": query,
                "agent_id": self._agent_id,
                "namespace": "default",
                "limit": 5,
            })
            if r.status_code == 200:
                return r.json().get("context", "")
        except Exception:
            pass
        return ""

    def queue_prefetch(self, query: str) -> None:
        t = threading.Thread(target=self.prefetch, args=(query,), daemon=True)
        t.start()

    def sync_turn(self, user_msg: str, assistant_msg: str) -> None:
        def _save():
            content = f"User: {user_msg}\nAssistant: {assistant_msg}"
            try:
                self._client.post("/save", json={
                    "agent_id": self._agent_id,
                    "namespace": "default",
                    "content": content,
                    "tags": ["conversation"],
                })
            except Exception:
                pass
        t = threading.Thread(target=_save, daemon=True)
        t.start()

    def get_tool_schemas(self) -> list:
        return [
            {
                "name": "stonemem_search",
                "description": "Search institutional memory for past knowledge, preferences, and facts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "default": 5},
                        "tags": {"type": "array", "items": {"type": "string"}, "default": []},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "stonemem_save",
                "description": "Save an important fact, preference, or piece of knowledge for future recall.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "The knowledge to save"},
                        "tags": {"type": "array", "items": {"type": "string"}, "default": []},
                        "supersedes": {"type": "integer", "description": "Entry ID this supersedes", "default": None},
                    },
                    "required": ["content"],
                },
            },
        ]

    def handle_tool_call(self, name: str, args: dict) -> str:
        try:
            if name == "stonemem_search":
                r = self._client.post("/search", json={
                    "query": args["query"],
                    "agent_id": self._agent_id,
                    "namespace": "default",
                    "limit": args.get("limit", 5),
                    "tags": args.get("tags", []),
                })
                return json.dumps(r.json()) if r.status_code == 200 else f"Error: {r.status_code}"
            elif name == "stonemem_save":
                r = self._client.post("/save", json={
                    "agent_id": self._agent_id,
                    "namespace": "default",
                    "content": args["content"],
                    "tags": args.get("tags", []),
                    "supersedes": args.get("supersedes"),
                })
                return json.dumps(r.json()) if r.status_code == 200 else f"Error: {r.status_code}"
        except Exception as e:
            return f"Error: {e}"
        return f"Unknown tool: {name}"

    def on_session_end(self, messages: list) -> None:
        try:
            self._client.post("/agent/deregister", json={
                "agent_id": self._agent_id,
            })
        except Exception:
            pass

    def on_delegation(self, task: str, result: str) -> None:
        try:
            self._client.post("/save", json={
                "agent_id": self._agent_id,
                "namespace": "default",
                "content": f"Delegation task: {task}\nResult: {result}",
                "tags": ["delegation"],
            })
        except Exception:
            pass

    def on_memory_write(self, action: str, target: str, content: str) -> None:
        try:
            self._client.post("/save", json={
                "agent_id": self._agent_id,
                "namespace": "default",
                "content": f"[{action}] {target}: {content}",
                "tags": ["memory_write", action],
            })
        except Exception:
            pass

    def on_pre_compress(self, messages: list) -> str:
        facts = []
        for msg in messages[-10:]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "assistant" and len(content) > 50:
                facts.append(content[:500])
        if facts:
            combined = "\n---\n".join(facts)
            try:
                self._client.post("/save", json={
                    "agent_id": self._agent_id,
                    "namespace": "default",
                    "content": f"Pre-compression extraction:\n{combined}",
                    "tags": ["compression"],
                })
            except Exception:
                pass
            return f"Extracted {len(facts)} key facts before compression."
        return ""

    def get_config_schema(self) -> dict:
        return {
            "STONEMEM_URL": {
                "type": "string",
                "default": "http://127.0.0.1:3391",
                "description": "stonemem server URL",
            },
            "STONEMEM_AGENT_ID": {
                "type": "string",
                "default": None,
                "description": "Agent ID (auto-detected from profile name if unset)",
            },
            "STONEMEM_AUTO_START": {
                "type": "boolean",
                "default": True,
                "description": "Auto-start stonemem binary if not running",
            },
        }

    def shutdown(self) -> None:
        self.on_session_end([])
        self._client.close()
