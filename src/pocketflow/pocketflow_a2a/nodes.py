"""
A2A Nodes for PocketFlow
"""

from typing import Dict, Any, Optional, List
import logging
import json

from .. import Node

# Configure logger
logger = logging.getLogger(__name__)

class SendTaskNode(Node):
    """
    Node for sending a task to an A2A agent.
    """
    
    def prep(self, shared):
        """
        Prepare the task data.
        
        Args:
            shared: Shared data dictionary containing task parameters
            
        Returns:
            Task data ready for processing
        """
        # Get the client from params
        client = self.params.get("client")
        if not client:
            raise ValueError("A2A client not provided")
        
        # Extract data from shared store
        message = shared.get("message")
        accepted_output_modes = shared.get("accepted_output_modes", ["text"])
        history_length = shared.get("history_length")
        
        if not message:
            raise ValueError("Message not provided")
        
        # Return task data
        return {
            "client": client,
            "message": message,
            "accepted_output_modes": accepted_output_modes,
            "history_length": history_length
        }
    
    async def exec_async(self, task_data):
        """
        Send the task to the agent.
        
        Args:
            task_data: Task data to process
            
        Returns:
            Task response
        """
        client = task_data["client"]
        message = task_data["message"]
        accepted_output_modes = task_data["accepted_output_modes"]
        history_length = task_data["history_length"]
        
        # Send the task
        response = await client.send_task(
            message=message,
            accepted_output_modes=accepted_output_modes,
            history_length=history_length
        )
        
        return response
    
    async def post_async(self, shared, prep_res, exec_res):
        """
        Save the task response to the shared store.
        
        Args:
            shared: Shared data dictionary
            prep_res: Result from prep
            exec_res: Result from exec
            
        Returns:
            Action to take next
        """
        # Save the task response to the shared store
        shared["task_response"] = exec_res
        
        # Check if the task was successful
        if "error" in exec_res:
            shared["task_error"] = exec_res["error"]
            return "error"
        
        # Extract the task result
        if "result" in exec_res:
            shared["task_result"] = exec_res["result"]
            
            # Extract the final text from the artifacts if available
            if "artifacts" in exec_res["result"] and exec_res["result"]["artifacts"]:
                for artifact in exec_res["result"]["artifacts"]:
                    if "parts" in artifact:
                        for part in artifact["parts"]:
                            if part.get("type") == "text":
                                shared["task_text"] = part.get("text", "")
                                break
                        if "task_text" in shared:
                            break
        
        # Return the default action
        return "default"


class GetTaskNode(Node):
    """
    Node for getting a task from an A2A agent.
    """
    
    def prep(self, shared):
        """
        Prepare the task data.
        
        Args:
            shared: Shared data dictionary containing task parameters
            
        Returns:
            Task data ready for processing
        """
        # Get the client from params
        client = self.params.get("client")
        if not client:
            raise ValueError("A2A client not provided")
        
        # Extract data from shared store
        task_id = shared.get("task_id")
        
        if not task_id:
            raise ValueError("Task ID not provided")
        
        # Return task data
        return {
            "client": client,
            "task_id": task_id
        }
    
    async def exec_async(self, task_data):
        """
        Get the task from the agent.
        
        Args:
            task_data: Task data to process
            
        Returns:
            Task response
        """
        client = task_data["client"]
        task_id = task_data["task_id"]
        
        # Get the task
        response = await client.get_task(task_id)
        
        return response
    
    async def post_async(self, shared, prep_res, exec_res):
        """
        Save the task response to the shared store.
        
        Args:
            shared: Shared data dictionary
            prep_res: Result from prep
            exec_res: Result from exec
            
        Returns:
            Action to take next
        """
        # Save the task response to the shared store
        shared["task_response"] = exec_res
        
        # Check if the task was successful
        if "error" in exec_res:
            shared["task_error"] = exec_res["error"]
            return "error"
        
        # Extract the task result
        if "result" in exec_res:
            shared["task_result"] = exec_res["result"]
            
            # Extract the final text from the artifacts if available
            if "artifacts" in exec_res["result"] and exec_res["result"]["artifacts"]:
                for artifact in exec_res["result"]["artifacts"]:
                    if "parts" in artifact:
                        for part in artifact["parts"]:
                            if part.get("type") == "text":
                                shared["task_text"] = part.get("text", "")
                                break
                        if "task_text" in shared:
                            break
        
        # Return the default action
        return "default"


class CancelTaskNode(Node):
    """
    Node for canceling a task in an A2A agent.
    """
    
    def prep(self, shared):
        """
        Prepare the task data.
        
        Args:
            shared: Shared data dictionary containing task parameters
            
        Returns:
            Task data ready for processing
        """
        # Get the client from params
        client = self.params.get("client")
        if not client:
            raise ValueError("A2A client not provided")
        
        # Extract data from shared store
        task_id = shared.get("task_id")
        
        if not task_id:
            raise ValueError("Task ID not provided")
        
        # Return task data
        return {
            "client": client,
            "task_id": task_id
        }
    
    async def exec_async(self, task_data):
        """
        Cancel the task.
        
        Args:
            task_data: Task data to process
            
        Returns:
            Task response
        """
        client = task_data["client"]
        task_id = task_data["task_id"]
        
        # Cancel the task
        response = await client.cancel_task(task_id)
        
        return response
    
    async def post_async(self, shared, prep_res, exec_res):
        """
        Save the task response to the shared store.
        
        Args:
            shared: Shared data dictionary
            prep_res: Result from prep
            exec_res: Result from exec
            
        Returns:
            Action to take next
        """
        # Save the task response to the shared store
        shared["task_response"] = exec_res
        
        # Check if the task was successful
        if "error" in exec_res:
            shared["task_error"] = exec_res["error"]
            return "error"
        
        # Extract the task result
        if "result" in exec_res:
            shared["task_result"] = exec_res["result"]
        
        # Return the default action
        return "default"


class SubscribeTaskNode(Node):
    """
    Node for subscribing to a task in an A2A agent.
    """
    
    def prep(self, shared):
        """
        Prepare the task data.
        
        Args:
            shared: Shared data dictionary containing task parameters
            
        Returns:
            Task data ready for processing
        """
        # Get the client from params
        client = self.params.get("client")
        if not client:
            raise ValueError("A2A client not provided")
        
        # Extract data from shared store
        task_id = shared.get("task_id")
        
        if not task_id:
            raise ValueError("Task ID not provided")
        
        # Return task data
        return {
            "client": client,
            "task_id": task_id
        }
    
    async def exec_async(self, task_data):
        """
        Subscribe to the task.
        
        Args:
            task_data: Task data to process
            
        Returns:
            Task response
        """
        client = task_data["client"]
        task_id = task_data["task_id"]
        
        # Subscribe to the task
        updates = []
        async for update in client.subscribe_to_task(task_id):
            updates.append(update)
        
        return updates
    
    async def post_async(self, shared, prep_res, exec_res):
        """
        Save the task updates to the shared store.
        
        Args:
            shared: Shared data dictionary
            prep_res: Result from prep
            exec_res: Result from exec
            
        Returns:
            Action to take next
        """
        # Save the task updates to the shared store
        shared["task_updates"] = exec_res
        
        # Extract the final update if available
        if exec_res and len(exec_res) > 0:
            shared["final_update"] = exec_res[-1]
        
        # Return the default action
        return "default"