"""
PocketFlow A2A Integration
-------------------------

This module provides integration between PocketFlow and the A2A protocol,
enabling PocketFlow flows to be exposed as A2A-compatible agents.
"""

from .task_manager import A2ATaskManager
from .a2a_client import A2AAgentClient
from .a2a_server import A2AServerAgent
from .nodes import (
    SendTaskNode,
    GetTaskNode,
    SubscribeTaskNode,
    CancelTaskNode
)
from .flow import create_a2a_flow

__all__ = [
    "A2ATaskManager",
    "A2AAgentClient",
    "A2AServerAgent",
    "SendTaskNode",
    "GetTaskNode",
    "SubscribeTaskNode",
    "CancelTaskNode",
    "create_a2a_flow"
]