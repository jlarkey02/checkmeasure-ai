from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging

from core.agents.agent_registry import AgentRegistry
from core.agents.specialized.joist_calculation_agent import JoistCalculationAgent

router = APIRouter()
logger = logging.getLogger(__name__)

# Global agent registry instance
agent_registry: Optional[AgentRegistry] = None

class AgentSystemRequest(BaseModel):
    action: str  # "start", "stop", "restart"

class AgentTaskRequest(BaseModel):
    agent_type: str
    task_type: str
    parameters: Dict[str, Any]
    priority: Optional[int] = 2

class ProjectCreateRequest(BaseModel):
    name: str
    description: str
    tasks: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None

class AgentCreateRequest(BaseModel):
    agent_type: str
    agent_id: Optional[str] = None
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

async def get_registry() -> AgentRegistry:
    """Get or create the agent registry"""
    global agent_registry
    
    if agent_registry is None:
        agent_registry = AgentRegistry()
        
        # Register agent factories
        agent_registry.register_agent_factory("joist_calculation", lambda: JoistCalculationAgent())
        
        # Start the registry
        await agent_registry.start()
        logger.info("Agent registry initialized")
    
    return agent_registry

@router.post("/system/control")
async def control_agent_system(request: AgentSystemRequest):
    """Control the agent system (start/stop/restart)"""
    try:
        registry = await get_registry()
        
        if request.action == "start":
            if not registry.running:
                await registry.start()
                return {"status": "started", "message": "Agent system started successfully"}
            else:
                return {"status": "already_running", "message": "Agent system is already running"}
        
        elif request.action == "stop":
            if registry.running:
                await registry.stop()
                return {"status": "stopped", "message": "Agent system stopped successfully"}
            else:
                return {"status": "already_stopped", "message": "Agent system is already stopped"}
        
        elif request.action == "restart":
            await registry.stop()
            await asyncio.sleep(1)  # Brief pause
            await registry.start()
            return {"status": "restarted", "message": "Agent system restarted successfully"}
        
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")
    
    except Exception as e:
        logger.error(f"Error controlling agent system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/health")
async def get_system_health():
    """Get overall system health"""
    try:
        registry = await get_registry()
        health = registry.get_system_health()
        return health
    
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/info")
async def get_registry_info():
    """Get agent registry information"""
    try:
        registry = await get_registry()
        info = registry.get_registry_info()
        return info
    
    except Exception as e:
        logger.error(f"Error getting registry info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/create")
async def create_agent(request: AgentCreateRequest):
    """Create a new agent"""
    try:
        registry = await get_registry()
        
        agent = await registry.create_agent(
            agent_type=request.agent_type,
            agent_id=request.agent_id,
            name=request.name,
            config=request.config
        )
        
        if agent:
            return {
                "status": "created",
                "agent_id": agent.agent_id,
                "name": agent.name,
                "type": request.agent_type
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create agent")
    
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents")
async def list_agents():
    """List all registered agents"""
    try:
        registry = await get_registry()
        agents = registry.get_all_agents_status()
        return {"agents": agents}
    
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}")
async def get_agent_status(agent_id: str):
    """Get status of a specific agent"""
    try:
        registry = await get_registry()
        status = registry.get_agent_status(agent_id)
        
        if status:
            return status
        else:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_id}/restart")
async def restart_agent(agent_id: str):
    """Restart a specific agent"""
    try:
        registry = await get_registry()
        success = await registry.restart_agent(agent_id)
        
        if success:
            return {"status": "restarted", "agent_id": agent_id}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to restart agent {agent_id}")
    
    except Exception as e:
        logger.error(f"Error restarting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_id}")
async def unregister_agent(agent_id: str):
    """Unregister an agent"""
    try:
        registry = await get_registry()
        success = await registry.unregister_agent(agent_id)
        
        if success:
            return {"status": "unregistered", "agent_id": agent_id}
        else:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    except Exception as e:
        logger.error(f"Error unregistering agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects")
async def create_project(request: ProjectCreateRequest):
    """Create a new project"""
    try:
        registry = await get_registry()
        
        project_id = await registry.create_project(
            name=request.name,
            description=request.description,
            tasks=request.tasks,
            metadata=request.metadata
        )
        
        return {
            "status": "created",
            "project_id": project_id,
            "name": request.name
        }
    
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}")
async def get_project_status(project_id: str):
    """Get status of a specific project"""
    try:
        registry = await get_registry()
        status = registry.get_project_status(project_id)
        
        if status:
            return status
        else:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    except Exception as e:
        logger.error(f"Error getting project status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/results")
async def get_project_results(project_id: str):
    """Get calculation results for a completed project"""
    try:
        registry = await get_registry()
        status = registry.get_project_status(project_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # Extract results from completed tasks
        results = []
        for task_id, task_info in status["task_details"].items():
            if task_info["status"] == "completed" and task_info["output_data"]:
                results.append({
                    "task_id": task_id,
                    "task_name": task_info["name"],
                    "task_type": task_info["task_type"],
                    "input_data": task_info["input_data"],
                    "output_data": task_info["output_data"],
                    "completed_at": task_info["completed_at"],
                    "duration": task_info["actual_duration"]
                })
        
        return {
            "project_id": project_id,
            "project_name": status["name"],
            "project_status": status["status"],
            "total_tasks": status["total_tasks"],
            "completed_tasks": status["completed_tasks"],
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Error getting project results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/execute")
async def execute_task(request: AgentTaskRequest):
    """Execute a task using the multi-agent system"""
    try:
        registry = await get_registry()
        
        # Create a simple project with a single task
        tasks = [
            {
                "name": f"{request.task_type} Task",
                "description": "Single task execution",
                "type": request.task_type,
                "capabilities": [request.agent_type],
                "input": request.parameters,
                "priority": request.priority
            }
        ]
        
        project_id = await registry.create_project(
            name=f"Single Task - {request.task_type}",
            description="Single task execution via API",
            tasks=tasks
        )
        
        return {
            "status": "task_queued",
            "project_id": project_id,
            "task_type": request.task_type,
            "agent_type": request.agent_type
        }
    
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities")
async def get_available_capabilities():
    """Get list of available capabilities"""
    try:
        registry = await get_registry()
        capabilities = registry.get_available_capabilities()
        agent_types = registry.get_agent_types()
        
        return {
            "capabilities": capabilities,
            "agent_types": agent_types
        }
    
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demo/joist-calculation")
async def demo_joist_calculation():
    """Demo endpoint to test the joist calculation agent"""
    try:
        registry = await get_registry()
        
        # Create a joist calculation agent if none exists
        joist_agents = registry.find_agents_by_type("joist_calculation")
        if not joist_agents:
            agent = await registry.create_agent("joist_calculation")
            if not agent:
                raise HTTPException(status_code=500, detail="Failed to create joist calculation agent")
        
        # Create a demo calculation task
        demo_task = {
            "name": "Demo Joist Calculation",
            "description": "Demonstration of joist calculation with enhanced AI features",
            "type": "joist_calculation",
            "capabilities": ["joist_calculation"],
            "input": {
                "span_length": 4.2,
                "joist_spacing": 0.45,
                "building_level": "L1",
                "room_type": "living",
                "load_type": "residential"
            },
            "priority": 3
        }
        
        project_id = await registry.create_project(
            name="Demo Joist Calculation",
            description="Demonstration of multi-agent joist calculation",
            tasks=[demo_task]
        )
        
        return {
            "status": "demo_started",
            "project_id": project_id,
            "description": "Demo joist calculation task created and queued",
            "input_parameters": demo_task["input"],
            "check_status_url": f"/api/agents/projects/{project_id}"
        }
    
    except Exception as e:
        logger.error(f"Error running demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))