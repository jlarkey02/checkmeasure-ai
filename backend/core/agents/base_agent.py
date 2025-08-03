import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
import logging

class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"
    COMPLETED = "completed"
    FAILED = "failed"

class MessageType(Enum):
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"
    COORDINATION = "coordination"

@dataclass
class AgentMessage:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: Optional[str] = None
    message_type: MessageType = MessageType.TASK_REQUEST
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None

@dataclass
class AgentCapability:
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    dependencies: List[str] = field(default_factory=list)

class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str, capabilities: List[AgentCapability]):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.event_bus = None
        self.current_task = None
        self.task_queue = asyncio.Queue()
        self.running = False
        
        # Performance metrics
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.average_processing_time = 0.0
        self.last_activity = datetime.now()
        
        # Register default message handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.message_handlers[MessageType.TASK_REQUEST] = self._handle_task_request
        self.message_handlers[MessageType.STATUS_UPDATE] = self._handle_status_update
        self.message_handlers[MessageType.ERROR_REPORT] = self._handle_error_report
    
    async def start(self):
        """Start the agent's main processing loop"""
        self.running = True
        self.logger.info(f"Agent {self.name} starting...")
        
        # Start the main processing loop
        await self._main_loop()
    
    async def stop(self):
        """Stop the agent gracefully"""
        self.running = False
        self.logger.info(f"Agent {self.name} stopping...")
    
    async def _main_loop(self):
        """Main processing loop for the agent"""
        while self.running:
            try:
                # Process queued tasks
                if not self.task_queue.empty():
                    task = await self.task_queue.get()
                    await self._process_task(task)
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await self._handle_error(e)
    
    async def receive_message(self, message: AgentMessage):
        """Receive and process an incoming message"""
        self.logger.debug(f"Received message: {message.message_type} from {message.sender_id}")
        
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(f"Error handling message: {e}")
                await self._send_error_response(message, e)
        else:
            self.logger.warning(f"No handler for message type: {message.message_type}")
    
    async def send_message(self, message: AgentMessage):
        """Send a message through the event bus"""
        if self.event_bus:
            await self.event_bus.publish(message)
        else:
            self.logger.warning("No event bus connected")
    
    async def _handle_task_request(self, message: AgentMessage):
        """Handle incoming task requests"""
        task_data = message.payload
        
        # Check if we can handle this task
        if not self._can_handle_task(task_data):
            await self._send_task_rejection(message, "Task not supported")
            return
        
        # Queue the task for processing
        await self.task_queue.put(message)
        
        # Send acknowledgment
        response = AgentMessage(
            sender_id=self.agent_id,
            recipient_id=message.sender_id,
            message_type=MessageType.TASK_RESPONSE,
            payload={"status": "accepted", "estimated_time": self._estimate_processing_time(task_data)},
            correlation_id=message.id
        )
        await self.send_message(response)
    
    async def _process_task(self, message: AgentMessage):
        """Process a task from the queue"""
        start_time = datetime.now()
        
        try:
            self.status = AgentStatus.WORKING
            self.current_task = message
            
            # Update status
            await self._broadcast_status_update()
            
            # Execute the task
            result = await self.execute_task(message.payload)
            
            # Send response
            response = AgentMessage(
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                message_type=MessageType.TASK_RESPONSE,
                payload={
                    "status": "completed", 
                    "result": result,
                    "task_id": message.payload.get("task_id")
                },
                correlation_id=message.id
            )
            await self.send_message(response)
            
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(processing_time, success=True)
            
            self.status = AgentStatus.COMPLETED
            self.current_task = None
            
        except Exception as e:
            self.logger.error(f"Task processing failed: {e}")
            await self._send_error_response(message, e)
            self._update_performance_metrics(0, success=False)
            self.status = AgentStatus.FAILED
        
        finally:
            await self._broadcast_status_update()
    
    @abstractmethod
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the main task logic - to be implemented by subclasses"""
        pass
    
    def _can_handle_task(self, task_data: Dict[str, Any]) -> bool:
        """Check if this agent can handle the given task"""
        task_type = task_data.get("type")
        return any(cap.name == task_type for cap in self.capabilities)
    
    def _estimate_processing_time(self, task_data: Dict[str, Any]) -> float:
        """Estimate processing time for a task"""
        if self.average_processing_time > 0:
            return self.average_processing_time
        return 30.0  # Default estimate in seconds
    
    def _update_performance_metrics(self, processing_time: float, success: bool):
        """Update performance metrics"""
        if success:
            self.tasks_completed += 1
            # Update rolling average
            total_tasks = self.tasks_completed + self.tasks_failed
            self.average_processing_time = (
                (self.average_processing_time * (total_tasks - 1) + processing_time) / total_tasks
            )
        else:
            self.tasks_failed += 1
        
        self.last_activity = datetime.now()
    
    async def _broadcast_status_update(self):
        """Broadcast current status to other agents"""
        status_message = AgentMessage(
            sender_id=self.agent_id,
            message_type=MessageType.STATUS_UPDATE,
            payload={
                "status": self.status.value,
                "current_task": self.current_task.id if self.current_task else None,
                "queue_size": self.task_queue.qsize(),
                "performance": {
                    "tasks_completed": self.tasks_completed,
                    "tasks_failed": self.tasks_failed,
                    "average_processing_time": self.average_processing_time,
                    "last_activity": self.last_activity.isoformat()
                }
            }
        )
        await self.send_message(status_message)
    
    async def _send_error_response(self, original_message: AgentMessage, error: Exception):
        """Send error response for a failed task"""
        response = AgentMessage(
            sender_id=self.agent_id,
            recipient_id=original_message.sender_id,
            message_type=MessageType.TASK_RESPONSE,
            payload={
                "status": "failed",
                "error": str(error),
                "error_type": type(error).__name__,
                "task_id": original_message.payload.get("task_id"),
                "original_task": original_message.payload
            },
            correlation_id=original_message.id
        )
        await self.send_message(response)
    
    async def _send_task_rejection(self, message: AgentMessage, reason: str):
        """Send task rejection response"""
        response = AgentMessage(
            sender_id=self.agent_id,
            recipient_id=message.sender_id,
            message_type=MessageType.TASK_RESPONSE,
            payload={"status": "rejected", "reason": reason},
            correlation_id=message.id
        )
        await self.send_message(response)
    
    async def _handle_status_update(self, message: AgentMessage):
        """Handle status updates from other agents"""
        pass  # Can be overridden by subclasses
    
    async def _handle_error_report(self, message: AgentMessage):
        """Handle error reports from other agents"""
        self.logger.warning(f"Error reported by {message.sender_id}: {message.payload}")
    
    async def _handle_error(self, error: Exception):
        """Handle internal errors"""
        self.status = AgentStatus.ERROR
        self.logger.error(f"Internal error: {error}")
        await self._broadcast_status_update()
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information and status"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "input_types": cap.input_types,
                    "output_types": cap.output_types,
                    "dependencies": cap.dependencies
                }
                for cap in self.capabilities
            ],
            "performance": {
                "tasks_completed": self.tasks_completed,
                "tasks_failed": self.tasks_failed,
                "average_processing_time": self.average_processing_time,
                "queue_size": self.task_queue.qsize(),
                "last_activity": self.last_activity.isoformat()
            }
        }