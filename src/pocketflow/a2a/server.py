"""
A2A Server Implementation for PocketFlow
"""

from typing import AsyncIterable, Any, Optional, Callable
import json
import logging
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from sse_starlette.sse import EventSourceResponse

# Configure a logger specific to the server
logger = logging.getLogger("A2AServer")

class A2AServer:
    """
    A2A Server implementation for PocketFlow.
    Handles A2A protocol requests and routes them to the appropriate task manager.
    """

    def __init__(
        self,
        get_task_manager: Callable,
        host: str = "0.0.0.0",
        port: int = 5000,
    ):
        """
        Initialize the A2A server.
        
        Args:
            get_task_manager: Function to get the task manager
            host: Host to bind the server to
            port: Port to bind the server to
        """
        self.host = host
        self.port = port
        self.get_task_manager = get_task_manager
        self.app = Starlette()
        
        # Set up routes
        self.app.add_route("/", self.handle_request, methods=["POST"])
        self.app.add_websocket_route("/ws", self.handle_websocket)
        self.app.add_route(
            "/.well-known/agent.json", self.get_agent_card, methods=["GET"]
        )
    
    async def get_agent_card(self, request: Request) -> JSONResponse:
        """
        Handle GET requests to /.well-known/agent.json.
        
        Args:
            request: The HTTP request
            
        Returns:
            JSON response with the agent card
        """
        logger.info("Serving Agent Card request")
        task_manager = self.get_task_manager()
        agent_card = getattr(task_manager, "agent_card", {
            "name": "PocketFlow A2A Agent",
            "description": "A generic A2A-compatible agent powered by PocketFlow"
        })
        return JSONResponse(agent_card)
    
    async def handle_request(self, request: Request) -> JSONResponse:
        """
        Handle POST requests to the root endpoint.
        
        Args:
            request: The HTTP request
            
        Returns:
            JSON response with the result
        """
        request_id = "unknown"
        
        try:
            # Parse request body
            content = await request.body()
            data = json.loads(content)
            request_id = data.get("id", "unknown")
            
            logger.info(f"Received request: {request_id}")
            
            # Get task manager
            task_manager = self.get_task_manager()
            
            # Process request based on method
            method = data.get("method")
            if method == "tasks/get":
                response = await task_manager.on_get_task(data)
            elif method == "tasks/send":
                response = await task_manager.on_send_task(data)
            elif method == "tasks/cancel":
                response = await task_manager.on_cancel_task(data)
            elif method == "tasks/subscribe":
                result = await task_manager.on_send_task_subscribe(data)
                if isinstance(result, AsyncIterable):
                    return EventSourceResponse(result)
                else:
                    response = result
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found"
                    }
                }
            
            logger.info(f"Sending response for request: {request_id}")
            return JSONResponse(response)
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            })
        
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": "Internal error"
                }
            })
    
    async def handle_websocket(self, websocket):
        """
        Handle WebSocket connections.
        
        Args:
            websocket: The WebSocket connection
        """
        await websocket.accept()
        try:
            # Get task manager
            task_manager = self.get_task_manager()
            
            # Process messages
            async for message in websocket.iter_text():
                try:
                    data = json.loads(message)
                    request_id = data.get("id", "unknown")
                    
                    logger.info(f"Received WebSocket message: {request_id}")
                    
                    # Process request based on method
                    method = data.get("method")
                    if method == "tasks/get":
                        response = await task_manager.on_get_task(data)
                    elif method == "tasks/send":
                        response = await task_manager.on_send_task(data)
                    elif method == "tasks/cancel":
                        response = await task_manager.on_cancel_task(data)
                    elif method == "tasks/subscribe":
                        # For subscriptions over WebSocket, we stream responses
                        result = await task_manager.on_send_task_subscribe(data)
                        if isinstance(result, AsyncIterable):
                            async for item in result:
                                await websocket.send_text(json.dumps(item))
                            continue
                        else:
                            response = result
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"Method '{method}' not found"
                            }
                        }
                    
                    # Send response
                    await websocket.send_text(json.dumps(response))
                
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }))
                
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}", exc_info=True)
                    await websocket.send_text(json.dumps({
                        "jsonrpc": "2.0",
                        "id": data.get("id", None),
                        "error": {
                            "code": -32603,
                            "message": "Internal error"
                        }
                    }))
        
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
        
        finally:
            await websocket.close()
    
    def run(self):
        """Run the server."""
        uvicorn.run(self.app, host=self.host, port=self.port)