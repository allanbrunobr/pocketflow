"""
A2A Flow for PocketFlow
"""

from typing import Dict, Any, Optional, List
import logging

from .. import Flow, AsyncFlow
from .nodes import SendTaskNode, GetTaskNode, CancelTaskNode, SubscribeTaskNode

# Configure logger
logger = logging.getLogger(__name__)

def create_a2a_flow(client, is_async=True):
    """
    Create an A2A flow.
    
    Args:
        client: A2A client to use for communication
        is_async: Whether to create an async flow
        
    Returns:
        A Flow object for A2A communication
    """
    # Create the nodes
    send_task = SendTaskNode()
    get_task = GetTaskNode()
    cancel_task = CancelTaskNode()
    subscribe_task = SubscribeTaskNode()
    
    # Set parameters
    send_task.set_params({"client": client})
    get_task.set_params({"client": client})
    cancel_task.set_params({"client": client})
    subscribe_task.set_params({"client": client})
    
    # Create the flow based on whether it's async or not
    if is_async:
        flow = AsyncFlow()
    else:
        flow = Flow()
    
    # Start with the send task node
    flow.start(send_task)
    
    # If there's an error, you might want to handle it differently
    send_task - "error" >> None
    
    # Allow manual transitions to other nodes if needed
    send_task - "get" >> get_task
    send_task - "cancel" >> cancel_task
    send_task - "subscribe" >> subscribe_task
    
    # Return the flow
    return flow