import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

from .base_agent import BaseAgent, AgentCapability
from .event_bus import EventBus
from .agent_manager import AgentManager
from .project_orchestrator import ProjectOrchestrator

@dataclass
class AgentRegistration:
    agent_id: str
    name: str
    agent_type: str
    capabilities: List[AgentCapability]
    version: str
    registered_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class AgentRegistry:
    """
    Central registry for agent discovery, capability matching, and system coordination.
    Provides a unified interface for managing the multi-agent system.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("agent_registry")
        
        # Core components
        self.event_bus = EventBus()
        self.agent_manager = AgentManager(self.event_bus)
        self.project_orchestrator = ProjectOrchestrator(self.event_bus)
        
        # Registry data
        self.registrations: Dict[str, AgentRegistration] = {}
        self.capability_index: Dict[str, Set[str]] = {}  # Capability -> Set of agent IDs
        self.agent_type_index: Dict[str, Set[str]] = {}  # Agent type -> Set of agent IDs
        
        # System state
        self.running = False
        self.startup_complete = False
        
        # Factory for creating agents
        self.agent_factories: Dict[str, Callable[[], BaseAgent]] = {}
        
        # Performance metrics
        self.total_registrations = 0
        self.successful_matches = 0
        self.failed_matches = 0
    
    async def start(self):
        """Start the agent registry and all core components"""
        self.running = True
        self.logger.info("Agent registry starting...")
        
        try:
            # Start core components in order
            await self.event_bus.start()
            await self.agent_manager.start()
            await self.project_orchestrator.start()
            
            # Register orchestrator with agent manager
            self.project_orchestrator.agent_manager = self.agent_manager
            
            self.startup_complete = True
            self.logger.info("Agent registry startup complete")
            
        except Exception as e:
            self.logger.error(f"Failed to start agent registry: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the agent registry and all components"""
        self.running = False
        self.logger.info("Agent registry stopping...")
        
        try:
            # Stop components in reverse order
            await self.project_orchestrator.stop()
            await self.agent_manager.stop()
            await self.event_bus.stop()
            
            self.logger.info("Agent registry stopped")
            
        except Exception as e:
            self.logger.error(f"Error during registry shutdown: {e}")
    
    def register_agent_factory(self, agent_type: str, factory: Callable[[], BaseAgent]):
        """Register a factory function for creating agents of a specific type"""
        self.agent_factories[agent_type] = factory
        self.logger.info(f"Registered agent factory for type: {agent_type}")
    
    async def register_agent(self, agent: BaseAgent, agent_type: str = "generic", 
                           version: str = "1.0.0", metadata: Dict[str, Any] = None) -> bool:
        """Register an agent with the system"""
        try:
            # Create registration record
            registration = AgentRegistration(
                agent_id=agent.agent_id,
                name=agent.name,
                agent_type=agent_type,
                capabilities=agent.capabilities,
                version=version,
                metadata=metadata or {}
            )
            
            # Store registration
            self.registrations[agent.agent_id] = registration
            
            # Update indexes
            self._update_capability_index(agent.agent_id, agent.capabilities)
            self._update_agent_type_index(agent.agent_id, agent_type)
            
            # Register with agent manager
            success = await self.agent_manager.register_agent(agent)
            if not success:
                # Rollback registration
                await self.unregister_agent(agent.agent_id)
                return False
            
            # Register with project orchestrator
            self.project_orchestrator.register_agent(agent)
            
            self.total_registrations += 1
            self.logger.info(f"Successfully registered agent: {agent.name} ({agent_type})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent.agent_id}: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the system"""
        try:
            registration = self.registrations.get(agent_id)
            if not registration:
                self.logger.warning(f"Agent {agent_id} not found for unregistration")
                return False
            
            # Remove from indexes
            self._remove_from_capability_index(agent_id, registration.capabilities)
            self._remove_from_agent_type_index(agent_id, registration.agent_type)
            
            # Unregister from components
            await self.agent_manager.unregister_agent(agent_id)
            self.project_orchestrator.unregister_agent(agent_id)
            
            # Remove registration
            del self.registrations[agent_id]
            
            self.logger.info(f"Successfully unregistered agent: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    def _update_capability_index(self, agent_id: str, capabilities: List[AgentCapability]):
        """Update the capability index for an agent"""
        for capability in capabilities:
            if capability.name not in self.capability_index:
                self.capability_index[capability.name] = set()
            self.capability_index[capability.name].add(agent_id)
    
    def _remove_from_capability_index(self, agent_id: str, capabilities: List[AgentCapability]):
        """Remove an agent from the capability index"""
        for capability in capabilities:
            if capability.name in self.capability_index:
                self.capability_index[capability.name].discard(agent_id)
                if not self.capability_index[capability.name]:
                    del self.capability_index[capability.name]
    
    def _update_agent_type_index(self, agent_id: str, agent_type: str):
        """Update the agent type index"""
        if agent_type not in self.agent_type_index:
            self.agent_type_index[agent_type] = set()
        self.agent_type_index[agent_type].add(agent_id)
    
    def _remove_from_agent_type_index(self, agent_id: str, agent_type: str):
        """Remove an agent from the agent type index"""
        if agent_type in self.agent_type_index:
            self.agent_type_index[agent_type].discard(agent_id)
            if not self.agent_type_index[agent_type]:
                del self.agent_type_index[agent_type]
    
    def find_agents_by_capability(self, capability_name: str) -> List[str]:
        """Find all agents that have a specific capability"""
        return list(self.capability_index.get(capability_name, set()))
    
    def find_agents_by_type(self, agent_type: str) -> List[str]:
        """Find all agents of a specific type"""
        return list(self.agent_type_index.get(agent_type, set()))
    
    def find_agents_by_capabilities(self, required_capabilities: List[str]) -> List[str]:
        """Find agents that have all required capabilities"""
        if not required_capabilities:
            return list(self.registrations.keys())
        
        # Start with agents that have the first capability
        matching_agents = self.capability_index.get(required_capabilities[0], set()).copy()
        
        # Intersect with agents that have each additional capability
        for capability in required_capabilities[1:]:
            capability_agents = self.capability_index.get(capability, set())
            matching_agents &= capability_agents
        
        return list(matching_agents)
    
    def get_agent_capabilities(self, agent_id: str) -> List[AgentCapability]:
        """Get the capabilities of a specific agent"""
        registration = self.registrations.get(agent_id)
        return registration.capabilities if registration else []
    
    def get_available_capabilities(self) -> List[str]:
        """Get list of all available capabilities in the system"""
        return list(self.capability_index.keys())
    
    def get_agent_types(self) -> List[str]:
        """Get list of all agent types in the system"""
        return list(self.agent_type_index.keys())
    
    async def create_agent(self, agent_type: str, agent_id: str = None, 
                         name: str = None, config: Dict[str, Any] = None) -> Optional[BaseAgent]:
        """Create and register a new agent using a registered factory"""
        factory = self.agent_factories.get(agent_type)
        if not factory:
            self.logger.error(f"No factory registered for agent type: {agent_type}")
            return None
        
        try:
            # Create the agent
            agent = factory()
            
            # Override properties if provided
            if agent_id:
                agent.agent_id = agent_id
            if name:
                agent.name = name
            
            # Apply configuration if provided
            if config:
                for key, value in config.items():
                    if hasattr(agent, key):
                        setattr(agent, key, value)
            
            # Register the agent
            success = await self.register_agent(agent, agent_type)
            if success:
                return agent
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to create agent of type {agent_type}: {e}")
            return None
    
    async def create_project(self, name: str, description: str, 
                           tasks: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> str:
        """Create and start a new project"""
        project_id = await self.project_orchestrator.create_project(
            name, description, tasks, metadata
        )
        
        # Auto-start the project
        await self.project_orchestrator.start_project(project_id)
        
        return project_id
    
    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a project"""
        return self.project_orchestrator.get_project_status(project_id)
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an agent"""
        return self.agent_manager.get_agent_status(agent_id)
    
    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents"""
        return self.agent_manager.get_all_agents_status()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health information"""
        agent_statuses = self.get_all_agents_status()
        
        healthy_count = sum(1 for agent in agent_statuses if agent["health"] == "healthy")
        total_count = len(agent_statuses)
        
        return {
            "overall_health": "healthy" if healthy_count == total_count else "degraded" if healthy_count > 0 else "unhealthy",
            "total_agents": total_count,
            "healthy_agents": healthy_count,
            "unhealthy_agents": total_count - healthy_count,
            "available_capabilities": len(self.capability_index),
            "available_agent_types": len(self.agent_type_index),
            "event_bus_metrics": self.event_bus.get_metrics(),
            "agent_manager_metrics": self.agent_manager.get_manager_metrics(),
            "orchestrator_metrics": self.project_orchestrator.get_orchestrator_metrics()
        }
    
    def get_registry_info(self) -> Dict[str, Any]:
        """Get detailed registry information"""
        return {
            "total_registrations": self.total_registrations,
            "active_agents": len(self.registrations),
            "successful_matches": self.successful_matches,
            "failed_matches": self.failed_matches,
            "startup_complete": self.startup_complete,
            "running": self.running,
            "registered_types": list(self.agent_type_index.keys()),
            "available_capabilities": list(self.capability_index.keys()),
            "registered_factories": list(self.agent_factories.keys())
        }
    
    def get_agent_registration(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get registration information for a specific agent"""
        return self.registrations.get(agent_id)
    
    def list_registrations(self) -> List[Dict[str, Any]]:
        """List all agent registrations"""
        return [
            {
                "agent_id": reg.agent_id,
                "name": reg.name,
                "agent_type": reg.agent_type,
                "version": reg.version,
                "registered_at": reg.registered_at.isoformat(),
                "capabilities": [cap.name for cap in reg.capabilities],
                "metadata": reg.metadata
            }
            for reg in self.registrations.values()
        ]
    
    async def match_agents_for_task(self, task_requirements: Dict[str, Any]) -> List[str]:
        """Find the best agents to handle a specific task"""
        try:
            required_capabilities = task_requirements.get("capabilities", [])
            preferred_type = task_requirements.get("agent_type")
            
            # Find agents by capabilities
            capable_agents = self.find_agents_by_capabilities(required_capabilities)
            
            # Filter by type if specified
            if preferred_type:
                type_agents = self.find_agents_by_type(preferred_type)
                capable_agents = [agent_id for agent_id in capable_agents if agent_id in type_agents]
            
            # Filter by availability (healthy agents)
            healthy_agents = self.agent_manager.get_healthy_agents()
            available_agents = [agent_id for agent_id in capable_agents if agent_id in healthy_agents]
            
            if available_agents:
                self.successful_matches += 1
            else:
                self.failed_matches += 1
                self.logger.warning(f"No available agents found for task requirements: {task_requirements}")
            
            return available_agents
            
        except Exception as e:
            self.logger.error(f"Error matching agents for task: {e}")
            self.failed_matches += 1
            return []
    
    async def restart_agent(self, agent_id: str) -> bool:
        """Restart a specific agent"""
        return await self.agent_manager.force_restart_agent(agent_id)
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export system configuration for backup/restore"""
        return {
            "registrations": [
                {
                    "agent_id": reg.agent_id,
                    "name": reg.name,
                    "agent_type": reg.agent_type,
                    "version": reg.version,
                    "metadata": reg.metadata
                }
                for reg in self.registrations.values()
            ],
            "agent_factories": list(self.agent_factories.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    async def import_configuration(self, config: Dict[str, Any]) -> bool:
        """Import system configuration from backup"""
        try:
            registrations = config.get("registrations", [])
            
            for reg_data in registrations:
                agent_type = reg_data["agent_type"]
                if agent_type in self.agent_factories:
                    agent = await self.create_agent(
                        agent_type=agent_type,
                        agent_id=reg_data["agent_id"],
                        name=reg_data["name"],
                        config=reg_data.get("metadata", {})
                    )
                    if not agent:
                        self.logger.warning(f"Failed to restore agent: {reg_data['name']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False