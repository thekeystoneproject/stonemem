"""stonemem adapter for Hermes agents."""
from .provider import StonememProvider

def register(ctx):
    ctx.register_memory_provider("stonemem", StonememProvider)
