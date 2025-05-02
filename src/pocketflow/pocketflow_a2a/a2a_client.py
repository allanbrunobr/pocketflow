"""
A2A Agent Client Implementation for PocketFlow
"""

import json
import logging
import uuid
import asyncio
from typing import Dict, Any, Optional, List, AsyncIterable
import httpx

# Configure logger
logger = logging.getLogger(__name__)

class A2AClientError(Exception):
    """Base exception for A2A client errors."""
    pass

class A2AAgentClient:
    """
    A2A Agent Client for PocketFlow.
    Used to interact with A2A-compatible agent servers.
    """
    
    def __init__(self, agent_url: str, session_id: Optional[str] = None):
        """
        Initialize the A2A agent client.
        
        Args:
            agent_url: URL of the agent server
            session_id: Optional session ID to use
        """
        self.agent_url = agent_url
        self.session_id = session_id or str(uuid.uuid4().hex)
        self.client = httpx.AsyncClient()
    
    async def get_agent_card(self) -> Dict[str, Any]:
        """
        Get the agent card from the server.
        
        Returns:
            Agent card data
        """
        url = f"{self.agent_url}/.well-known/agent.json"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise A2AClientError(f"Failed to get agent card: {e.response.status_code} {e.response.reason_phrase}")
        except Exception as e:
            raise A2AClientError(f"Failed to get agent card: {str(e)}")
    
    async def send_task(
        self, 
        message: str, 
        accepted_output_modes: List[str] = ["text"],
        history_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send a task to the agent.
        
        Args:
            message: Message to send to the agent
            accepted_output_modes: Output modes to accept
            history_length: Number of history items to include
            
        Returns:
            Task data
        """
        task_id = str(uuid.uuid4().hex)
        request_id = str(uuid.uuid4().hex)
        
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tasks/send",
            "params": {
                "id": task_id,
                "sessionId": self.session_id,
                "message": {
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": message
                        }
                    ]
                },
                "acceptedOutputModes": accepted_output_modes
            }
        }
        
        if history_length is not None:
            payload["params"]["historyLength"] = history_length
        
        logger.info(f"Sending task: {task_id}")
        try:
            response = await self.client.post(
                self.agent_url,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise A2AClientError(f"Failed to send task: {e.response.status_code} {e.response.reason_phrase}")
        except Exception as e:
            raise A2AClientError(f"Failed to send task: {str(e)}")
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get a task from the agent.
        
        Args:
            task_id: ID of the task to get
            
        Returns:
            Task data
        """
        request_id = str(uuid.uuid4().hex)
        
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tasks/get",
            "params": {
                "id": task_id,
                "sessionId": self.session_id
            }
        }
        
        logger.info(f"Getting task: {task_id}")
        try:
            response = await self.client.post(
                self.agent_url,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise A2AClientError(f"Failed to get task: {e.response.status_code} {e.response.reason_phrase}")
        except Exception as e:
            raise A2AClientError(f"Failed to get task: {str(e)}")
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            Task data
        """
        request_id = str(uuid.uuid4().hex)
        
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tasks/cancel",
            "params": {
                "id": task_id,
                "sessionId": self.session_id
            }
        }
        
        logger.info(f"Canceling task: {task_id}")
        try:
            response = await self.client.post(
                self.agent_url,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise A2AClientError(f"Failed to cancel task: {e.response.status_code} {e.response.reason_phrase}")
        except Exception as e:
            raise A2AClientError(f"Failed to cancel task: {str(e)}")
    
    async def subscribe_to_task(self, task_id: str) -> AsyncIterable[Dict[str, Any]]:
        """
        Subscribe to task updates.
        
        Args:
            task_id: ID of the task to subscribe to
            
        Yields:
            Task updates
        """
        request_id = str(uuid.uuid4().hex)
        
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tasks/subscribe",
            "params": {
                "id": task_id,
                "sessionId": self.session_id
            }
        }
        
        logger.info(f"Subscribing to task: {task_id}")
        try:
            async with self.client.stream(
                "POST",
                self.agent_url,
                json=payload,
                headers={"Accept": "text/event-stream"}
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data = json.loads(line[5:].strip())
                        yield data
        except httpx.HTTPStatusError as e:
            raise A2AClientError(f"Failed to subscribe to task: {e.response.status_code} {e.response.reason_phrase}")
        except Exception as e:
            raise A2AClientError(f"Failed to subscribe to task: {str(e)}")
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()