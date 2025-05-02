from typing import Dict, Any, List, Optional, AsyncIterable, Union, Callable, Awaitable
import logging
import asyncio
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel

# Configure logger
logger = logging.getLogger(__name__)

class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"

class TextPart(BaseModel):
    text: str
    type: str = "text"

class Message(BaseModel):
    role: str
    parts: List[TextPart]

class TaskStatus(BaseModel):
    state: TaskState
    message: Optional[Message] = None

class Artifact(BaseModel):
    parts: List[TextPart]

class Task(BaseModel):
    id: str
    status: TaskStatus
    artifacts: List[Artifact] = []

class InMemoryTaskManager:
    """Base task manager that stores tasks in memory."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}

    async def upsert_task(self, task_params: Any) -> None:
        """
        Create or update a task.
        
        Args:
            task_params: Parameters for the task
        """
        task = Task(
            id=task_params.id,
            status=TaskStatus(state=TaskState.SUBMITTED),
            artifacts=[]
        )
        self.tasks[task_params.id] = task

    async def update_store(self, task_id: str, status: TaskStatus, artifacts: List[Artifact]) -> Task:
        """
        Update a task in the store.
        
        Args:
            task_id: ID of the task to update
            status: New status for the task
            artifacts: New artifacts for the task
            
        Returns:
            Updated task
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        task = self.tasks[task_id]
        task.status = status
        task.artifacts = artifacts
        return task

    def append_task_history(self, task: Task, history_length: Optional[int] = None) -> Task:
        """
        Append a task to the history.
        
        Args:
            task: Task to append
            history_length: Maximum history length
            
        Returns:
            Task with updated history
        """
        if history_length is not None and history_length > 0:
            task.artifacts = task.artifacts[-history_length:]
        return task

class JSONRPCResponse(BaseModel):
    id: str
    error: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None

class TaskSendParams(BaseModel):
    id: str
    message: Optional[Message] = None
    acceptedOutputModes: List[str] = []
    historyLength: Optional[int] = None

class SendTaskRequest(BaseModel):
    id: str
    params: TaskSendParams

class SendTaskResponse(BaseModel):
    id: str
    error: Optional[Dict[str, Any]] = None
    result: Optional[Task] = None

class SendTaskStreamingRequest(BaseModel):
    id: str
    params: TaskSendParams

class SendTaskStreamingResponse(BaseModel):
    id: str
    error: Optional[Dict[str, Any]] = None
    result: Optional[Task] = None

class UnsupportedOperationError(Exception):
    def __init__(self, message: str):
        self.message = message

class InternalError(Exception):
    def __init__(self, message: str):
        self.message = message

class InvalidParamsError(Exception):
    def __init__(self, message: str):
        self.message = message

def are_modalities_compatible(accepted_modes: List[str], supported_modes: List[str]) -> bool:
    """
    Check if the accepted modes are compatible with the supported modes.
    
    Args:
        accepted_modes: Modes accepted by the client
        supported_modes: Modes supported by the server
        
    Returns:
        True if compatible, False otherwise
    """
    return any(mode in supported_modes for mode in accepted_modes)

def new_incompatible_types_error(request_id: str) -> JSONRPCResponse:
    """
    Create a new incompatible types error response.
    
    Args:
        request_id: ID of the request
        
    Returns:
        Error response
    """
    return JSONRPCResponse(
        id=request_id,
        error={"code": -32602, "message": "Incompatible output modes"}
    )

class A2ATaskManager(InMemoryTaskManager):
    """
    Base class for A2A task managers.
    
    This class provides a foundation for building A2A task managers,
    with methods for handling A2A requests.
    """
    
    SUPPORTED_CONTENT_TYPES = ["text", "application/json"]
    
    def __init__(self):
        """Initialize the task manager."""
        super().__init__()
        self.agent_card = {
            "name": "PocketFlow A2A Agent",
            "description": "An A2A-compatible agent powered by PocketFlow"
        }
    
    async def on_get_task(self, request: Any) -> Dict[str, Any]:
        """
        Handle a task get request.
        
        Args:
            request: The request
            
        Returns:
            The response
        """
        try:
            task_id = request.get("params", {}).get("id")
            if not task_id:
                return {
                    "id": request.get("id"),
                    "error": {"code": -32602, "message": "Missing task ID"}
                }
            
            if task_id not in self.tasks:
                return {
                    "id": request.get("id"),
                    "error": {"code": -32602, "message": f"Task {task_id} not found"}
                }
            
            task = self.tasks.get(task_id)
            return {
                "id": request.get("id"),
                "result": task
            }
        except Exception as e:
            logger.error(f"Error getting task: {e}")
            return {
                "id": request.get("id"),
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }
    
    async def on_cancel_task(self, request: Any) -> Dict[str, Any]:
        """
        Handle a task cancel request.
        
        Args:
            request: The request
            
        Returns:
            The response
        """
        try:
            task_id = request.get("params", {}).get("id")
            if not task_id:
                return {
                    "id": request.get("id"),
                    "error": {"code": -32602, "message": "Missing task ID"}
                }
            
            if task_id not in self.tasks:
                return {
                    "id": request.get("id"),
                    "error": {"code": -32602, "message": f"Task {task_id} not found"}
                }
            
            # Update task status to canceled
            task = await self.update_store(
                task_id,
                TaskStatus(state=TaskState.FAILED, message=Message(role="system", parts=[TextPart(text="Task canceled")])),
                self.tasks[task_id].artifacts
            )
            
            return {
                "id": request.get("id"),
                "result": task
            }
        except Exception as e:
            logger.error(f"Error canceling task: {e}")
            return {
                "id": request.get("id"),
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }
    
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle a task send request.
        
        Args:
            request: The request
            
        Returns:
            The response
        """
        logger.info(f"Received task send request: {request.params.id}")
        
        # Validate output modes
        if not are_modalities_compatible(
            request.params.acceptedOutputModes, self.SUPPORTED_CONTENT_TYPES
        ):
            logger.warning(
                "Unsupported output mode. Received %s, Support %s",
                request.params.acceptedOutputModes, self.SUPPORTED_CONTENT_TYPES
            )
            return SendTaskResponse(id=request.id, error=new_incompatible_types_error(request.id).error)
        
        # Upsert the task in the store (initial state: submitted)
        await self.upsert_task(request.params)
        
        # Update state to working before running
        await self.update_store(request.params.id, TaskStatus(state=TaskState.WORKING), [])
        
        try:
            # Extract the message text
            message_text = self._extract_message_text(request.params)
            
            if not message_text:
                fail_status = TaskStatus(
                    state=TaskState.FAILED, 
                    message=Message(role="agent", parts=[TextPart(text="No text found in message")])
                )
                await self.update_store(request.params.id, fail_status, [])
                return SendTaskResponse(id=request.id, error=InvalidParamsError(message="No text found in message"))
            
            # Handle the task
            success, result = await self.handle_task(message_text, request.params.id)
            
            if success:
                # Update the task in the store with final status and artifact
                final_task_status = TaskStatus(state=TaskState.COMPLETED)
                final_artifact = Artifact(parts=[TextPart(text=str(result))])
                
                final_task = await self.update_store(
                    request.params.id, final_task_status, [final_artifact]
                )
                
                # Prepare and return the A2A response
                task_result = self.append_task_history(final_task, request.params.historyLength)
                return SendTaskResponse(id=request.id, result=task_result)
            else:
                # Task failed
                fail_status = TaskStatus(
                    state=TaskState.FAILED, 
                    message=Message(role="agent", parts=[TextPart(text=str(result))])
                )
                await self.update_store(request.params.id, fail_status, [])
                return SendTaskResponse(id=request.id, error={"code": -32000, "message": str(result)})
        
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            fail_status = TaskStatus(
                state=TaskState.FAILED, 
                message=Message(role="agent", parts=[TextPart(text=f"Error processing task: {str(e)}")])
            )
            await self.update_store(request.params.id, fail_status, [])
            return SendTaskResponse(id=request.id, error=InternalError(message=f"Error processing task: {str(e)}"))
    
    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> Union[AsyncIterable[SendTaskStreamingResponse], JSONRPCResponse]:
        """
        Handle a task subscribe request.
        
        Args:
            request: The request
            
        Returns:
            The response
        """
        logger.warning(f"Streaming requested for task {request.params.id}, but not supported by default")
        # Return an error indicating streaming is not supported
        return JSONRPCResponse(
            id=request.id, 
            error={"code": -32601, "message": "Streaming not supported by this agent"}
        )
    
    def _extract_message_text(self, task_send_params: TaskSendParams) -> Optional[str]:
        """
        Extract the message text from the task parameters.
        
        Args:
            task_send_params: The task parameters
            
        Returns:
            The message text, or None if not found
        """
        if not task_send_params.message or not task_send_params.message.parts:
            logger.warning(f"No message parts found for task {task_send_params.id}")
            return None
        
        for part in task_send_params.message.parts:
            # Ensure part is treated as a dictionary if it came from JSON
            part_dict = part.dict() if hasattr(part, "dict") else part
            if part_dict.get("type") == "text" and "text" in part_dict:
                return part_dict["text"]
        
        logger.warning(f"No text part found in message for task {task_send_params.id}")
        return None
    
    async def handle_task(self, message_text: str, task_id: str) -> tuple[bool, Any]:
        """
        Handle a task. Override this method in subclasses.
        
        Args:
            message_text: The message text
            task_id: The task ID
            
        Returns:
            A tuple of (success, result)
        """
        # This method should be overridden in subclasses
        return True, f"Task {task_id} handled: {message_text}"