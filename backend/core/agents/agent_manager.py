import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import traceback

from .base_agent import BaseAgent, AgentStatus, AgentMessage, MessageType
from .event_bus import EventBus

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNRESPONSIVE = "unresponsive"

class AgentManager:
    """
    Manages agent lifecycle, health monitoring, fault tolerance, and recovery.
    Provides centralized agent registry and monitoring capabilities.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = logging.getLogger("agent_manager")
        
        # Agent registry and tracking
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_health: Dict[str, HealthStatus] = {}
        self.agent_last_seen: Dict[str, datetime] = {}
        self.agent_tasks: Dict[str, List[str]] = {}  # Agent -> List of task IDs
        
        # Health monitoring configuration
        self.health_check_interval = 30.0  # seconds
        self.unresponsive_threshold = 120.0  # seconds
        self.degraded_threshold = 60.0  # seconds
        self.max_restart_attempts = 3
        self.restart_cooldown = 300.0  # seconds
        
        # Recovery tracking
        self.restart_attempts: Dict[str, int] = {}
        self.last_restart_time: Dict[str, datetime] = {}
        self.failed_agents: Dict[str, str] = {}  # Agent ID -> failure reason
        
        # Monitoring state
        self.running = False
        self.health_monitors: Dict[str, asyncio.Task] = {}
        
        # Performance metrics
        self.total_agents_registered = 0
        self.total_restarts = 0
        self.total_failures = 0
        
        # Subscribe to relevant events
        self.event_bus.subscribe(MessageType.STATUS_UPDATE, self._handle_agent_status)
        self.event_bus.subscribe(MessageType.ERROR_REPORT, self._handle_agent_error)
    
    async def start(self):
        """Start the agent manager"""
        self.running = True
        self.logger.info("Agent manager starting...")
        
        # Start health monitoring loop
        asyncio.create_task(self._health_monitoring_loop())
    
    async def stop(self):
        """Stop the agent manager and all agents"""
        self.running = False
        self.logger.info("Agent manager stopping...")
        
        # Stop all health monitors
        for monitor in self.health_monitors.values():
            monitor.cancel()
        
        # Stop all agents gracefully
        await self._stop_all_agents()
    
    async def register_agent(self, agent: BaseAgent, auto_start: bool = True) -> bool:
        """Register and optionally start an agent"""
        try:
            # Check if agent is already registered
            if agent.agent_id in self.agents:
                self.logger.warning(f"Agent {agent.agent_id} already registered")
                return False
            
            # Register the agent
            self.agents[agent.agent_id] = agent
            self.agent_health[agent.agent_id] = HealthStatus.HEALTHY
            self.agent_last_seen[agent.agent_id] = datetime.now()
            self.agent_tasks[agent.agent_id] = []
            self.restart_attempts[agent.agent_id] = 0
            
            # Connect agent to event bus
            agent.event_bus = self.event_bus
            self.event_bus.register_agent(agent.agent_id, agent.receive_message)
            
            self.total_agents_registered += 1
            self.logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
            
            # Start the agent if requested
            if auto_start:
                await self._start_agent(agent.agent_id)
            
            # Start health monitoring for this agent
            self._start_health_monitor(agent.agent_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent.agent_id}: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        try:
            if agent_id not in self.agents:
                self.logger.warning(f"Agent {agent_id} not found for unregistration")
                return False
            
            # Stop health monitoring
            if agent_id in self.health_monitors:
                self.health_monitors[agent_id].cancel()
                del self.health_monitors[agent_id]
            
            # Stop the agent
            await self._stop_agent(agent_id)
            
            # Remove from event bus
            self.event_bus.unregister_agent(agent_id)
            
            # Clean up tracking data
            del self.agents[agent_id]
            del self.agent_health[agent_id]
            del self.agent_last_seen[agent_id]
            del self.agent_tasks[agent_id]
            del self.restart_attempts[agent_id]
            
            if agent_id in self.last_restart_time:
                del self.last_restart_time[agent_id]
            if agent_id in self.failed_agents:
                del self.failed_agents[agent_id]
            
            self.logger.info(f"Unregistered agent: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    async def _start_agent(self, agent_id: str) -> bool:
        """Start a specific agent"""
        try:
            agent = self.agents.get(agent_id)
            if not agent:
                self.logger.error(f"Agent {agent_id} not found")
                return False
            
            # Start the agent in a separate task
            agent_task = asyncio.create_task(agent.start())
            self.logger.info(f"Started agent: {agent.name}")
            
            # Update health status
            self.agent_health[agent_id] = HealthStatus.HEALTHY
            self.agent_last_seen[agent_id] = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start agent {agent_id}: {e}")
            self.agent_health[agent_id] = HealthStatus.UNHEALTHY
            self.failed_agents[agent_id] = str(e)
            return False
    
    async def _stop_agent(self, agent_id: str) -> bool:
        """Stop a specific agent"""
        try:
            agent = self.agents.get(agent_id)
            if not agent:
                return False
            
            await agent.stop()
            self.logger.info(f"Stopped agent: {agent.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop agent {agent_id}: {e}")
            return False
    
    async def _stop_all_agents(self):
        """Stop all registered agents"""
        stop_tasks = []
        for agent_id in list(self.agents.keys()):
            task = asyncio.create_task(self._stop_agent(agent_id))
            stop_tasks.append(task)
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
    
    def _start_health_monitor(self, agent_id: str):
        """Start health monitoring for an agent"""
        monitor_task = asyncio.create_task(self._monitor_agent_health(agent_id))
        self.health_monitors[agent_id] = monitor_task
    
    async def _monitor_agent_health(self, agent_id: str):
        """Monitor the health of a specific agent"""
        while self.running and agent_id in self.agents:
            try:
                await self._check_agent_health(agent_id)
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error monitoring agent {agent_id}: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _check_agent_health(self, agent_id: str):
        """Check the health of a specific agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        now = datetime.now()
        last_seen = self.agent_last_seen.get(agent_id, now)
        time_since_last_seen = (now - last_seen).total_seconds()
        
        current_health = self.agent_health.get(agent_id, HealthStatus.HEALTHY)
        new_health = current_health
        
        # Determine health status based on responsiveness
        if time_since_last_seen > self.unresponsive_threshold:
            new_health = HealthStatus.UNRESPONSIVE
        elif time_since_last_seen > self.degraded_threshold:
            new_health = HealthStatus.DEGRADED
        elif agent.status == AgentStatus.ERROR:
            new_health = HealthStatus.UNHEALTHY
        else:
            new_health = HealthStatus.HEALTHY
        
        # Update health status if changed
        if new_health != current_health:
            self.agent_health[agent_id] = new_health
            self.logger.info(f"Agent {agent.name} health changed: {current_health.value} -> {new_health.value}")
            
            # Handle health state changes
            await self._handle_health_change(agent_id, new_health)
    
    async def _handle_health_change(self, agent_id: str, new_health: HealthStatus):
        """Handle agent health status changes"""
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        if new_health in [HealthStatus.UNRESPONSIVE, HealthStatus.UNHEALTHY]:
            # Attempt to restart the agent
            await self._attempt_agent_restart(agent_id)
        elif new_health == HealthStatus.DEGRADED:
            # Log warning but don't restart yet
            self.logger.warning(f"Agent {agent.name} is degraded")
    
    async def _attempt_agent_restart(self, agent_id: str):
        """Attempt to restart a failed agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        # Check restart cooldown
        if agent_id in self.last_restart_time:
            time_since_restart = (datetime.now() - self.last_restart_time[agent_id]).total_seconds()
            if time_since_restart < self.restart_cooldown:
                self.logger.info(f"Agent {agent.name} restart on cooldown")
                return
        
        # Check restart attempt limit
        attempts = self.restart_attempts.get(agent_id, 0)
        if attempts >= self.max_restart_attempts:
            self.logger.error(f"Agent {agent.name} exceeded max restart attempts")
            self.failed_agents[agent_id] = "Max restart attempts exceeded"
            return
        
        # Attempt restart
        self.logger.info(f"Attempting to restart agent {agent.name} (attempt {attempts + 1})")
        
        try:
            # Stop the agent first
            await self._stop_agent(agent_id)
            await asyncio.sleep(2)  # Brief pause
            
            # Start the agent
            success = await self._start_agent(agent_id)
            
            if success:
                self.restart_attempts[agent_id] = 0  # Reset attempts on successful restart
                self.last_restart_time[agent_id] = datetime.now()
                self.total_restarts += 1
                self.logger.info(f"Successfully restarted agent {agent.name}")
                
                # Remove from failed agents if it was there
                if agent_id in self.failed_agents:
                    del self.failed_agents[agent_id]
            else:
                self.restart_attempts[agent_id] = attempts + 1
                self.logger.error(f"Failed to restart agent {agent.name}")
        
        except Exception as e:
            self.restart_attempts[agent_id] = attempts + 1
            self.logger.error(f"Error during agent restart: {e}")
    
    async def _health_monitoring_loop(self):
        """Main health monitoring loop"""
        while self.running:
            try:
                # Perform system-wide health checks
                await self._system_health_check()
                await asyncio.sleep(self.health_check_interval * 2)  # Less frequent system checks
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
    
    async def _system_health_check(self):
        """Perform system-wide health checks"""
        # Check event bus health
        if not self.event_bus.running:
            self.logger.error("Event bus is not running")
        
        # Check for orphaned tasks
        await self._check_for_orphaned_tasks()
        
        # Log overall system health
        healthy_agents = sum(1 for h in self.agent_health.values() if h == HealthStatus.HEALTHY)
        total_agents = len(self.agents)
        
        if total_agents > 0:
            health_percentage = (healthy_agents / total_agents) * 100
            if health_percentage < 50:
                self.logger.warning(f"System health degraded: {health_percentage:.1f}% of agents healthy")
    
    async def _check_for_orphaned_tasks(self):
        """Check for tasks that may be orphaned due to agent failures"""
        # This would integrate with the ProjectOrchestrator to check for stuck tasks
        pass
    
    async def _handle_agent_status(self, message: AgentMessage):
        """Handle agent status updates"""
        agent_id = message.sender_id
        if agent_id in self.agent_last_seen:
            self.agent_last_seen[agent_id] = datetime.now()
        
        # Update task tracking
        payload = message.payload
        if "current_task" in payload and payload["current_task"]:
            task_id = payload["current_task"]
            if task_id not in self.agent_tasks.get(agent_id, []):
                self.agent_tasks[agent_id].append(task_id)
    
    async def _handle_agent_error(self, message: AgentMessage):
        """Handle agent error reports"""
        agent_id = message.sender_id
        error_info = message.payload
        
        self.logger.error(f"Error from agent {agent_id}: {error_info}")
        
        # Mark agent as unhealthy
        self.agent_health[agent_id] = HealthStatus.UNHEALTHY
        self.failed_agents[agent_id] = error_info.get("error", "Unknown error")
        self.total_failures += 1
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a specific agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        return {
            "agent_id": agent_id,
            "name": agent.name,
            "status": agent.status.value,
            "health": self.agent_health.get(agent_id, HealthStatus.UNHEALTHY).value,
            "last_seen": self.agent_last_seen.get(agent_id, datetime.now()).isoformat(),
            "restart_attempts": self.restart_attempts.get(agent_id, 0),
            "active_tasks": len(self.agent_tasks.get(agent_id, [])),
            "capabilities": [cap.name for cap in agent.capabilities],
            "performance": agent.get_info().get("performance", {}),
            "error": self.failed_agents.get(agent_id)
        }
    
    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Get status of all registered agents"""
        return [self.get_agent_status(agent_id) for agent_id in self.agents.keys()]
    
    def get_healthy_agents(self) -> List[str]:
        """Get list of healthy agent IDs"""
        return [
            agent_id for agent_id, health in self.agent_health.items()
            if health == HealthStatus.HEALTHY
        ]
    
    def get_failed_agents(self) -> Dict[str, str]:
        """Get dictionary of failed agents and their failure reasons"""
        return self.failed_agents.copy()
    
    def get_manager_metrics(self) -> Dict[str, Any]:
        """Get agent manager performance metrics"""
        health_distribution = {}
        for health in HealthStatus:
            health_distribution[health.value] = sum(
                1 for h in self.agent_health.values() if h == health
            )
        
        return {
            "total_agents_registered": self.total_agents_registered,
            "active_agents": len(self.agents),
            "total_restarts": self.total_restarts,
            "total_failures": self.total_failures,
            "health_distribution": health_distribution,
            "failed_agents_count": len(self.failed_agents),
            "system_uptime": (datetime.now() - datetime.now()).total_seconds() if self.running else 0
        }
    
    async def force_restart_agent(self, agent_id: str) -> bool:
        """Force restart of a specific agent (admin function)"""
        if agent_id not in self.agents:
            return False
        
        # Reset restart attempts for forced restart
        self.restart_attempts[agent_id] = 0
        
        await self._attempt_agent_restart(agent_id)
        return True
    
    async def get_agent_logs(self, agent_id: str, lines: int = 100) -> List[str]:
        """Get recent log entries for a specific agent"""
        # This would integrate with the logging system to retrieve agent-specific logs
        # For now, return a placeholder
        return [f"Log entry for agent {agent_id}"]