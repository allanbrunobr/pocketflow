"""
A2A Server Agent Implementation for PocketFlow
"""

import logging
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel

from ..a2a import A2AServer
from .task_manager import A2ATaskManager

# Configure logger
logger = logging.getLogger(__name__)

class AgentCapabilities(BaseModel):
    """Agent capabilities model."""
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = False

class AgentAuthentication(BaseModel):
    """Agent authentication model."""
    type: str
    instructions: Optional[str] = None

class AgentSkill(BaseModel):
    """Agent skill model."""
    id: str
    name: str
    description: str
    tags: List[str] = []
    examples: List[str] = []
    inputModes: List[str] = ["text"]
    outputModes: List[str] = ["text"]

class AgentProvider(BaseModel):
    """Agent provider model."""
    id: str
    name: str
    url: Optional[str] = None
    logo: Optional[str] = None

class AgentCard(BaseModel):
    """Agent card model."""
    name: str
    description: str
    url: str
    version: str
    capabilities: AgentCapabilities
    skills: List[AgentSkill] = []
    provider: Optional[AgentProvider] = None
    authentication: Optional[AgentAuthentication] = None
    defaultInputModes: List[str] = ["text"]
    defaultOutputModes: List[str] = ["text"]

class A2AServerAgent:
    """
    A2A Server Agent implementation for PocketFlow.
    
    This class provides a simple way to create an A2A-compatible agent server
    using PocketFlow.
    """
    
    def __init__(
        self,
        task_manager_class: Type[A2ATaskManager],
        name: str,
        description: str,
        host: str = "localhost",
        port: int = 8000,
        version: str = "0.1.0",
        skills: Optional[List[Dict[str, Any]]] = None,
        streaming: bool = False,
    ):
        """
        Initialize the A2A server agent.
        
        Args:
            task_manager_class: The task manager class to use
            name: Name of the agent
            description: Description of the agent
            host: Host to bind the server to
            port: Port to bind the server to
            version: Version of the agent
            skills: List of skills for the agent
            streaming: Whether the agent supports streaming
        """
        self.task_manager_class = task_manager_class
        self.name = name
        self.description = description
        self.host = host
        self.port = port
        self.version = version
        self.streaming = streaming
        
        # Create the task manager
        self.task_manager = task_manager_class()
        
        # Set up the agent card
        capabilities = AgentCapabilities(
            streaming=streaming,
            pushNotifications=False,
            stateTransitionHistory=False
        )
        
        # Create skills
        agent_skills = []
        if skills:
            for skill_data in skills:
                agent_skills.append(AgentSkill(
                    id=skill_data.get("id", "default_skill"),
                    name=skill_data.get("name", "Default Skill"),
                    description=skill_data.get("description", ""),
                    tags=skill_data.get("tags", []),
                    examples=skill_data.get("examples", []),
                    inputModes=skill_data.get("inputModes", self.task_manager.SUPPORTED_CONTENT_TYPES),
                    outputModes=skill_data.get("outputModes", self.task_manager.SUPPORTED_CONTENT_TYPES)
                ))
        else:
            # Create a default skill
            agent_skills.append(AgentSkill(
                id="default_skill",
                name="Default Skill",
                description=f"Default skill for {name}",
                inputModes=self.task_manager.SUPPORTED_CONTENT_TYPES,
                outputModes=self.task_manager.SUPPORTED_CONTENT_TYPES
            ))
        
        self.agent_card = AgentCard(
            name=name,
            description=description,
            url=f"http://{host}:{port}/",
            version=version,
            capabilities=capabilities,
            skills=agent_skills,
            defaultInputModes=self.task_manager.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=self.task_manager.SUPPORTED_CONTENT_TYPES
        )
        
        # Set the agent card on the task manager
        self.task_manager.agent_card = self.agent_card.dict()
        
        # Create the A2A server
        self.server = A2AServer(
            get_task_manager=lambda: self.task_manager,
            host=host,
            port=port
        )
    
    def start(self):
        """Start the server."""
        logger.info(f"Starting {self.name} on http://{self.host}:{self.port}")
        self.server.run()