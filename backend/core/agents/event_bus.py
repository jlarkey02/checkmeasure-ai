import asyncio
import logging
from typing import Dict, Set, List, Callable, Optional, Any
from collections import defaultdict
from datetime import datetime
import json
from .base_agent import AgentMessage, MessageType

class EventBus:
    """
    Central message bus for inter-agent communication.
    Supports pub/sub patterns, direct messaging, and message persistence.
    """
    
    def __init__(self):
        self.subscribers: Dict[str, Set[Callable]] = defaultdict(set)
        self.direct_routes: Dict[str, Callable] = {}
        self.message_history: List[AgentMessage] = []
        self.logger = logging.getLogger("event_bus")
        self.running = False
        self.message_queue = asyncio.Queue()
        self.delivery_confirmations: Dict[str, bool] = {}
        
        # Performance metrics
        self.messages_sent = 0
        self.messages_failed = 0
        self.average_delivery_time = 0.0
        
    async def start(self):
        """Start the event bus processing loop"""
        self.running = True
        self.logger.info("Event bus starting...")
        
        # Start the message processing loop
        asyncio.create_task(self._process_messages())
    
    async def stop(self):
        """Stop the event bus gracefully"""
        self.running = False
        self.logger.info("Event bus stopping...")
    
    async def _process_messages(self):
        """Main message processing loop"""
        while self.running:
            try:
                # Process queued messages
                if not self.message_queue.empty():
                    message = await self.message_queue.get()
                    await self._deliver_message(message)
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)
                
            except Exception as e:
                self.logger.error(f"Error in message processing loop: {e}")
    
    async def publish(self, message: AgentMessage):
        """Publish a message to the bus"""
        try:
            # Add to message history
            self.message_history.append(message)
            
            # Add to processing queue
            await self.message_queue.put(message)
            
            self.logger.debug(f"Message queued: {message.id} from {message.sender_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
            self.messages_failed += 1
            raise
    
    async def _deliver_message(self, message: AgentMessage):
        """Deliver a message to its recipients"""
        start_time = datetime.now()
        
        try:
            if message.recipient_id:
                # Direct message to specific recipient
                await self._deliver_direct_message(message)
            else:
                # Broadcast message to all subscribers
                await self._broadcast_message(message)
            
            # Update performance metrics
            delivery_time = (datetime.now() - start_time).total_seconds()
            self._update_delivery_metrics(delivery_time, success=True)
            
            # Mark as delivered
            self.delivery_confirmations[message.id] = True
            
        except Exception as e:
            self.logger.error(f"Failed to deliver message {message.id}: {e}")
            self._update_delivery_metrics(0, success=False)
            self.delivery_confirmations[message.id] = False
            raise
    
    async def _deliver_direct_message(self, message: AgentMessage):
        """Deliver message to a specific recipient"""
        recipient_handler = self.direct_routes.get(message.recipient_id)
        
        if recipient_handler:
            try:
                await recipient_handler(message)
                self.logger.debug(f"Direct message delivered to {message.recipient_id}")
            except Exception as e:
                self.logger.error(f"Failed to deliver direct message to {message.recipient_id}: {e}")
                raise
        else:
            self.logger.warning(f"No route found for recipient: {message.recipient_id}")
            raise ValueError(f"Recipient {message.recipient_id} not found")
    
    async def _broadcast_message(self, message: AgentMessage):
        """Broadcast message to all subscribers of the message type"""
        message_type_key = message.message_type.value
        subscribers = self.subscribers.get(message_type_key, set())
        
        if not subscribers:
            self.logger.debug(f"No subscribers for message type: {message_type_key}")
            return
        
        # Deliver to all subscribers concurrently
        delivery_tasks = []
        for subscriber in subscribers:
            task = asyncio.create_task(self._safe_deliver_to_subscriber(subscriber, message))
            delivery_tasks.append(task)
        
        # Wait for all deliveries to complete
        results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
        
        # Log any delivery failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to deliver to subscriber: {result}")
    
    async def _safe_deliver_to_subscriber(self, subscriber: Callable, message: AgentMessage):
        """Safely deliver message to a subscriber with error handling"""
        try:
            await subscriber(message)
        except Exception as e:
            self.logger.error(f"Subscriber error: {e}")
            # Don't re-raise to prevent one bad subscriber from affecting others
    
    def subscribe(self, message_type: MessageType, handler: Callable):
        """Subscribe to messages of a specific type"""
        message_type_key = message_type.value
        self.subscribers[message_type_key].add(handler)
        self.logger.debug(f"Added subscriber for {message_type_key}")
    
    def unsubscribe(self, message_type: MessageType, handler: Callable):
        """Unsubscribe from messages of a specific type"""
        message_type_key = message_type.value
        self.subscribers[message_type_key].discard(handler)
        self.logger.debug(f"Removed subscriber for {message_type_key}")
    
    def register_agent(self, agent_id: str, message_handler: Callable):
        """Register an agent for direct messaging"""
        self.direct_routes[agent_id] = message_handler
        self.logger.info(f"Registered agent: {agent_id}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from direct messaging"""
        if agent_id in self.direct_routes:
            del self.direct_routes[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")
    
    def _update_delivery_metrics(self, delivery_time: float, success: bool):
        """Update delivery performance metrics"""
        if success:
            self.messages_sent += 1
            # Update rolling average
            total_messages = self.messages_sent + self.messages_failed
            self.average_delivery_time = (
                (self.average_delivery_time * (total_messages - 1) + delivery_time) / total_messages
            )
        else:
            self.messages_failed += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus performance metrics"""
        return {
            "messages_sent": self.messages_sent,
            "messages_failed": self.messages_failed,
            "average_delivery_time": self.average_delivery_time,
            "queue_size": self.message_queue.qsize(),
            "active_subscribers": sum(len(subs) for subs in self.subscribers.values()),
            "registered_agents": len(self.direct_routes),
            "message_history_size": len(self.message_history)
        }
    
    def get_message_history(self, limit: int = 100, filter_type: Optional[MessageType] = None) -> List[Dict]:
        """Get recent message history"""
        messages = self.message_history[-limit:]
        
        if filter_type:
            messages = [msg for msg in messages if msg.message_type == filter_type]
        
        return [
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "recipient_id": msg.recipient_id,
                "message_type": msg.message_type.value,
                "timestamp": msg.timestamp.isoformat(),
                "correlation_id": msg.correlation_id,
                "delivered": self.delivery_confirmations.get(msg.id, False)
            }
            for msg in messages
        ]
    
    async def send_direct_message(self, sender_id: str, recipient_id: str, 
                                message_type: MessageType, payload: Dict[str, Any],
                                correlation_id: Optional[str] = None) -> str:
        """Convenience method to send a direct message"""
        message = AgentMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload,
            correlation_id=correlation_id
        )
        
        await self.publish(message)
        return message.id
    
    async def broadcast_message(self, sender_id: str, message_type: MessageType, 
                              payload: Dict[str, Any]) -> str:
        """Convenience method to broadcast a message"""
        message = AgentMessage(
            sender_id=sender_id,
            message_type=message_type,
            payload=payload
        )
        
        await self.publish(message)
        return message.id
    
    def clear_history(self):
        """Clear message history (useful for testing)"""
        self.message_history.clear()
        self.delivery_confirmations.clear()
        self.logger.info("Message history cleared")
    
    def get_agent_status(self) -> Dict[str, bool]:
        """Get the online status of all registered agents"""
        return {agent_id: True for agent_id in self.direct_routes.keys()}
    
    async def ping_agent(self, agent_id: str) -> bool:
        """Ping an agent to check if it's responsive"""
        try:
            ping_message = AgentMessage(
                sender_id="event_bus",
                recipient_id=agent_id,
                message_type=MessageType.STATUS_UPDATE,
                payload={"type": "ping"}
            )
            
            await self.publish(ping_message)
            
            # Wait for response (simplified - in production you'd implement proper response handling)
            await asyncio.sleep(1)
            
            return self.delivery_confirmations.get(ping_message.id, False)
            
        except Exception as e:
            self.logger.error(f"Failed to ping agent {agent_id}: {e}")
            return False