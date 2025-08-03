import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

from .base_agent import BaseAgent, AgentMessage, MessageType, AgentStatus
from .event_bus import EventBus

class ProjectStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ProjectTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    task_type: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    assigned_agent: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: float = 0.0
    actual_duration: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None

@dataclass
class Project:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    tasks: List[ProjectTask] = field(default_factory=list)
    status: ProjectStatus = ProjectStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ProjectOrchestrator:
    """
    Coordinates multi-agent execution of complex construction calculation projects.
    Handles task scheduling, dependency management, load balancing, and fault tolerance.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = logging.getLogger("project_orchestrator")
        
        # Project and task management
        self.projects: Dict[str, Project] = {}
        self.active_tasks: Dict[str, ProjectTask] = {}
        self.agent_registry: Dict[str, BaseAgent] = {}
        self.agent_workloads: Dict[str, int] = {}
        
        # Scheduling and coordination
        self.task_queue = asyncio.PriorityQueue()
        self.running = False
        self.scheduling_interval = 1.0  # seconds
        
        # Performance metrics
        self.projects_completed = 0
        self.projects_failed = 0
        self.average_project_duration = 0.0
        self.total_tasks_executed = 0
        
        # Subscribe to agent status updates
        self.event_bus.subscribe(MessageType.STATUS_UPDATE, self._handle_agent_status)
        self.event_bus.subscribe(MessageType.TASK_RESPONSE, self._handle_task_response)
        self.event_bus.subscribe(MessageType.ERROR_REPORT, self._handle_error_report)
    
    async def start(self):
        """Start the orchestrator"""
        self.running = True
        self.logger.info("Project orchestrator starting...")
        
        # Register orchestrator with event bus for message routing
        self.event_bus.register_agent("orchestrator", self._handle_message)
        
        # Start the main coordination loop
        asyncio.create_task(self._coordination_loop())
    
    async def stop(self):
        """Stop the orchestrator gracefully"""
        self.running = False
        # Unregister from event bus
        self.event_bus.unregister_agent("orchestrator")
        self.logger.info("Project orchestrator stopping...")
    
    async def _handle_message(self, message: AgentMessage):
        """Handle incoming messages to the orchestrator"""
        self.logger.debug(f"Orchestrator received message: {message.message_type} from {message.sender_id}")
        
        try:
            if message.message_type == MessageType.TASK_RESPONSE:
                await self._handle_task_response(message)
            elif message.message_type == MessageType.STATUS_UPDATE:
                await self._handle_agent_status(message)
            elif message.message_type == MessageType.ERROR_REPORT:
                await self._handle_error_report(message)
            else:
                self.logger.warning(f"Unhandled message type: {message.message_type}")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _coordination_loop(self):
        """Main coordination loop for task scheduling and management"""
        while self.running:
            try:
                # Schedule ready tasks
                await self._schedule_ready_tasks()
                
                # Check for failed tasks that need retry
                await self._handle_failed_tasks()
                
                # Update project statuses
                await self._update_project_statuses()
                
                # Clean up completed projects
                await self._cleanup_completed_projects()
                
                await asyncio.sleep(self.scheduling_interval)
                
            except Exception as e:
                self.logger.error(f"Error in coordination loop: {e}")
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agent_registry[agent.agent_id] = agent
        self.agent_workloads[agent.agent_id] = 0
        agent.event_bus = self.event_bus
        
        self.logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agent_registry:
            del self.agent_registry[agent_id]
            del self.agent_workloads[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")
    
    async def create_project(self, name: str, description: str, 
                           tasks: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> str:
        """Create a new project with tasks"""
        project = Project(
            name=name,
            description=description,
            metadata=metadata or {}
        )
        
        # Create tasks
        for task_data in tasks:
            task = ProjectTask(
                name=task_data.get("name", ""),
                description=task_data.get("description", ""),
                task_type=task_data.get("type", ""),
                priority=TaskPriority(task_data.get("priority", 2)),
                dependencies=task_data.get("dependencies", []),
                required_capabilities=task_data.get("capabilities", []),
                input_data=task_data.get("input", {}),
                estimated_duration=task_data.get("estimated_duration", 30.0),
                max_retries=task_data.get("max_retries", 3)
            )
            project.tasks.append(task)
        
        self.projects[project.id] = project
        self.logger.info(f"Created project: {name} with {len(tasks)} tasks")
        
        return project.id
    
    async def start_project(self, project_id: str) -> bool:
        """Start execution of a project"""
        project = self.projects.get(project_id)
        if not project:
            self.logger.error(f"Project not found: {project_id}")
            return False
        
        if project.status != ProjectStatus.PENDING:
            self.logger.warning(f"Project {project_id} is not in pending status")
            return False
        
        project.status = ProjectStatus.IN_PROGRESS
        project.started_at = datetime.now()
        
        # Queue all ready tasks
        await self._queue_ready_tasks(project)
        
        self.logger.info(f"Started project: {project.name}")
        return True
    
    async def _queue_ready_tasks(self, project: Project):
        """Queue tasks that are ready to execute"""
        for task in project.tasks:
            if task.status == ProjectStatus.PENDING and self._are_dependencies_met(task, project):
                # Priority queue uses (priority, item) tuples - lower priority value = higher priority
                priority = -task.priority.value  # Negate for proper priority ordering
                await self.task_queue.put((priority, task))
                task.status = ProjectStatus.IN_PROGRESS
    
    def _are_dependencies_met(self, task: ProjectTask, project: Project) -> bool:
        """Check if all task dependencies are completed"""
        if not task.dependencies:
            return True
        
        dependency_tasks = {t.id: t for t in project.tasks}
        
        for dep_id in task.dependencies:
            dep_task = dependency_tasks.get(dep_id)
            if not dep_task or dep_task.status != ProjectStatus.COMPLETED:
                return False
        
        return True
    
    async def _schedule_ready_tasks(self):
        """Schedule ready tasks to available agents"""
        while not self.task_queue.empty():
            try:
                priority, task = await asyncio.wait_for(self.task_queue.get(), timeout=0.1)
                
                # Find best agent for this task
                agent_id = await self._find_best_agent(task)
                
                if agent_id:
                    await self._assign_task_to_agent(task, agent_id)
                else:
                    # No available agent, put task back in queue
                    await self.task_queue.put((priority, task))
                    break
                    
            except asyncio.TimeoutError:
                break
    
    async def _find_best_agent(self, task: ProjectTask) -> Optional[str]:
        """Find the best available agent for a task"""
        suitable_agents = []
        
        for agent_id, agent in self.agent_registry.items():
            # Check if agent has required capabilities
            agent_capabilities = {cap.name for cap in agent.capabilities}
            required_capabilities = set(task.required_capabilities)
            
            if not required_capabilities.issubset(agent_capabilities):
                continue
            
            # Check if agent is available
            if agent.status not in [AgentStatus.IDLE, AgentStatus.COMPLETED]:
                continue
            
            # Calculate suitability score
            workload = self.agent_workloads.get(agent_id, 0)
            score = -workload  # Prefer agents with lower workload
            
            # Bonus for exact capability match
            if agent_capabilities == required_capabilities:
                score += 10
            
            suitable_agents.append((score, agent_id))
        
        if suitable_agents:
            # Return agent with highest score
            suitable_agents.sort(reverse=True)
            return suitable_agents[0][1]
        
        return None
    
    async def _assign_task_to_agent(self, task: ProjectTask, agent_id: str):
        """Assign a task to a specific agent"""
        task.assigned_agent = agent_id
        task.started_at = datetime.now()
        self.active_tasks[task.id] = task
        self.agent_workloads[agent_id] += 1
        
        # Send task to agent
        message = AgentMessage(
            sender_id="orchestrator",
            recipient_id=agent_id,
            message_type=MessageType.TASK_REQUEST,
            payload={
                "task_id": task.id,
                "type": task.task_type,
                "name": task.name,
                "description": task.description,
                "input": task.input_data,
                "priority": task.priority.value
            }
        )
        
        await self.event_bus.publish(message)
        self.logger.info(f"Assigned task {task.name} to agent {agent_id}")
    
    async def _handle_task_response(self, message: AgentMessage):
        """Handle task completion responses from agents"""
        payload = message.payload
        task_id = payload.get("task_id")
        
        if not task_id or task_id not in self.active_tasks:
            return
        
        task = self.active_tasks[task_id]
        response_status = payload.get("status")
        
        if response_status == "completed":
            await self._handle_task_completion(task, payload.get("result", {}))
        elif response_status == "failed":
            await self._handle_task_failure(task, payload.get("error", "Unknown error"))
        elif response_status == "accepted":
            self.logger.info(f"Task {task.name} accepted by {message.sender_id}")
    
    async def _handle_task_completion(self, task: ProjectTask, result: Dict[str, Any]):
        """Handle successful task completion"""
        task.status = ProjectStatus.COMPLETED
        task.completed_at = datetime.now()
        task.output_data = result
        task.actual_duration = (task.completed_at - task.started_at).total_seconds()
        
        # Update agent workload
        if task.assigned_agent:
            self.agent_workloads[task.assigned_agent] -= 1
        
        # Remove from active tasks
        del self.active_tasks[task.id]
        
        self.total_tasks_executed += 1
        self.logger.info(f"Task completed: {task.name}")
        
        # Check if this enables new tasks
        await self._check_for_newly_ready_tasks(task)
    
    async def _handle_task_failure(self, task: ProjectTask, error: str):
        """Handle task failure with retry logic"""
        task.error_message = error
        task.retry_count += 1
        
        # Update agent workload
        if task.assigned_agent:
            self.agent_workloads[task.assigned_agent] -= 1
        
        if task.retry_count < task.max_retries:
            # Retry the task
            task.status = ProjectStatus.PENDING
            task.assigned_agent = None
            self.logger.warning(f"Task {task.name} failed, retrying ({task.retry_count}/{task.max_retries})")
            
            # Re-queue with lower priority
            priority = -(task.priority.value - 1)
            await self.task_queue.put((priority, task))
        else:
            # Mark as failed
            task.status = ProjectStatus.FAILED
            task.completed_at = datetime.now()
            self.logger.error(f"Task {task.name} failed after {task.max_retries} retries: {error}")
        
        # Remove from active tasks
        del self.active_tasks[task.id]
    
    async def _check_for_newly_ready_tasks(self, completed_task: ProjectTask):
        """Check if completing this task enables new tasks"""
        # Find the project this task belongs to
        project = None
        for proj in self.projects.values():
            if any(t.id == completed_task.id for t in proj.tasks):
                project = proj
                break
        
        if project:
            await self._queue_ready_tasks(project)
    
    async def _handle_failed_tasks(self):
        """Handle failed tasks that need retry"""
        # This is handled in _handle_task_failure
        pass
    
    async def _update_project_statuses(self):
        """Update project statuses based on task completion"""
        for project in self.projects.values():
            if project.status != ProjectStatus.IN_PROGRESS:
                continue
            
            all_tasks_done = True
            any_task_failed = False
            
            for task in project.tasks:
                if task.status in [ProjectStatus.PENDING, ProjectStatus.IN_PROGRESS]:
                    all_tasks_done = False
                elif task.status == ProjectStatus.FAILED:
                    any_task_failed = True
            
            if any_task_failed:
                project.status = ProjectStatus.FAILED
                project.completed_at = datetime.now()
                self.projects_failed += 1
                self.logger.error(f"Project failed: {project.name}")
            elif all_tasks_done:
                project.status = ProjectStatus.COMPLETED
                project.completed_at = datetime.now()
                duration = (project.completed_at - project.started_at).total_seconds()
                self._update_project_metrics(duration)
                self.logger.info(f"Project completed: {project.name}")
    
    async def _cleanup_completed_projects(self):
        """Clean up old completed projects"""
        # Keep projects for analysis, but could implement cleanup logic here
        pass
    
    def _update_project_metrics(self, duration: float):
        """Update project performance metrics"""
        self.projects_completed += 1
        total_projects = self.projects_completed + self.projects_failed
        self.average_project_duration = (
            (self.average_project_duration * (total_projects - 1) + duration) / total_projects
        )
    
    async def _handle_agent_status(self, message: AgentMessage):
        """Handle agent status updates"""
        agent_id = message.sender_id
        payload = message.payload
        
        # Update agent workload based on queue size
        queue_size = payload.get("queue_size", 0)
        self.agent_workloads[agent_id] = queue_size
    
    async def _handle_error_report(self, message: AgentMessage):
        """Handle error reports from agents"""
        self.logger.error(f"Error report from {message.sender_id}: {message.payload}")
    
    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a project"""
        project = self.projects.get(project_id)
        if not project:
            return None
        
        task_statuses = {}
        for task in project.tasks:
            task_statuses[task.id] = {
                "name": task.name,
                "status": task.status.value,
                "assigned_agent": task.assigned_agent,
                "progress": self._calculate_task_progress(task),
                "output_data": task.output_data if task.status == ProjectStatus.COMPLETED else None,
                "error_message": task.error_message if task.status == ProjectStatus.FAILED else None,
                "input_data": task.input_data,
                "task_type": task.task_type,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "actual_duration": task.actual_duration if task.completed_at else None
            }
        
        return {
            "id": project.id,
            "name": project.name,
            "status": project.status.value,
            "created_at": project.created_at.isoformat(),
            "started_at": project.started_at.isoformat() if project.started_at else None,
            "completed_at": project.completed_at.isoformat() if project.completed_at else None,
            "total_tasks": len(project.tasks),
            "completed_tasks": sum(1 for t in project.tasks if t.status == ProjectStatus.COMPLETED),
            "failed_tasks": sum(1 for t in project.tasks if t.status == ProjectStatus.FAILED),
            "task_details": task_statuses
        }
    
    def _calculate_task_progress(self, task: ProjectTask) -> float:
        """Calculate task progress percentage"""
        if task.status == ProjectStatus.COMPLETED:
            return 100.0
        elif task.status == ProjectStatus.FAILED:
            return 0.0
        elif task.status == ProjectStatus.IN_PROGRESS:
            if task.estimated_duration > 0 and task.started_at:
                elapsed = (datetime.now() - task.started_at).total_seconds()
                return min(90.0, (elapsed / task.estimated_duration) * 100)
            return 50.0
        else:
            return 0.0
    
    def get_orchestrator_metrics(self) -> Dict[str, Any]:
        """Get orchestrator performance metrics"""
        return {
            "projects_completed": self.projects_completed,
            "projects_failed": self.projects_failed,
            "average_project_duration": self.average_project_duration,
            "total_tasks_executed": self.total_tasks_executed,
            "active_projects": len([p for p in self.projects.values() if p.status == ProjectStatus.IN_PROGRESS]),
            "active_tasks": len(self.active_tasks),
            "registered_agents": len(self.agent_registry),
            "agent_workloads": self.agent_workloads.copy()
        }