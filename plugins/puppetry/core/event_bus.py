"""
Thalamus Event Bus

Implements the Thalamus pattern for parallel processing and event routing.
Handles both fast reflex-level responses and deeper cognitive processing.

Inspired by biological thalamic function:
- Raw input routing for immediate responses
- Parallel refinement for structured processing
- Event coordination between subsystems
"""

import asyncio
import threading
import time
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor


class EventPriority(Enum):
    """Event priority levels following Thalamus pattern."""
    REFLEX = 1      # Immediate response required (mentions, direct messages)
    NORMAL = 2      # Standard processing (scheduled posts, interactions)
    BACKGROUND = 3  # Background processing (memory consolidation, analytics)


@dataclass
class ThalamicEvent:
    """Event in the Thalamus system."""
    id: str
    agent_id: str
    event_type: str
    priority: EventPriority
    data: Dict[str, Any]
    timestamp: float
    source: str
    processed: bool = False
    response_required: bool = False


class EventRouter:
    """Routes events based on priority and type."""
    
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}
        self.reflex_handlers: Dict[str, Callable] = {}
    
    def register_handler(self, event_type: str, handler: Callable, is_reflex: bool = False):
        """Register event handler."""
        if is_reflex:
            self.reflex_handlers[event_type] = handler
        else:
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            self.handlers[event_type].append(handler)
    
    def route_event(self, event: ThalamicEvent) -> List[Callable]:
        """Route event to appropriate handlers."""
        handlers = []
        
        # Reflex handling for high priority events
        if event.priority == EventPriority.REFLEX and event.event_type in self.reflex_handlers:
            handlers.append(self.reflex_handlers[event.event_type])
        
        # Standard handlers
        if event.event_type in self.handlers:
            handlers.extend(self.handlers[event.event_type])
        
        return handlers


class ThalamusEventBus:
    """
    Main event bus implementing Thalamus pattern.
    
    Provides:
    - Parallel processing pipelines
    - Priority-based routing 
    - Reflex vs cognitive processing paths
    - Agent lifecycle management
    """
    
    def __init__(self, max_workers: int = 4):
        self.active_agents: Dict[str, List[str]] = {}  # agent_id -> behaviors
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.router = EventRouter()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Processing statistics
        self.stats = {
            "events_processed": 0,
            "reflex_responses": 0,
            "background_tasks": 0,
            "active_agents": 0
        }
        
        # Event processing control
        self._running = False
        self._processing_task: Optional[asyncio.Task] = None
    
    def register_agent(self, agent_id: str, behaviors: List[str]):
        """Register an agent with the event bus."""
        self.active_agents[agent_id] = behaviors
        self.stats["active_agents"] = len(self.active_agents)
        print(f"Agent {agent_id} registered with behaviors: {behaviors}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from the event bus."""
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
            self.stats["active_agents"] = len(self.active_agents)
            print(f"Agent {agent_id} unregistered")
    
    def get_active_agents(self) -> Dict[str, List[str]]:
        """Get all active agents and their behaviors."""
        return self.active_agents.copy()
    
    async def emit_event(self, event: ThalamicEvent):
        """Emit an event into the system."""
        await self.event_queue.put(event)
    
    async def emit_twitter_mention(self, agent_id: str, mention_data: Dict[str, Any]):
        """Emit a Twitter mention event (reflex priority)."""
        event = ThalamicEvent(
            id=f"twitter_mention_{int(time.time() * 1000)}",
            agent_id=agent_id,
            event_type="twitter_mention", 
            priority=EventPriority.REFLEX,
            data=mention_data,
            timestamp=time.time(),
            source="twitter",
            response_required=True
        )
        await self.emit_event(event)
    
    # Trading functionality removed - focusing on Twitter-only functionality
    
    async def emit_scheduled_post(self, agent_id: str, post_data: Dict[str, Any]):
        """Emit a scheduled posting event (normal priority)."""
        event = ThalamicEvent(
            id=f"scheduled_post_{int(time.time() * 1000)}",
            agent_id=agent_id,
            event_type="scheduled_post",
            priority=EventPriority.NORMAL,
            data=post_data,
            timestamp=time.time(),
            source="scheduler"
        )
        await self.emit_event(event)
    
    async def emit_memory_consolidation(self, agent_id: str, memory_data: Dict[str, Any]):
        """Emit a memory consolidation event (background priority)."""
        event = ThalamicEvent(
            id=f"memory_consolidation_{int(time.time() * 1000)}",
            agent_id=agent_id,
            event_type="memory_consolidation",
            priority=EventPriority.BACKGROUND,
            data=memory_data,
            timestamp=time.time(),
            source="memory"
        )
        await self.emit_event(event)
    
    def register_twitter_handlers(self, mention_handler: Callable, post_handler: Callable):
        """Register Twitter-related event handlers."""
        self.router.register_handler("twitter_mention", mention_handler, is_reflex=True)
        self.router.register_handler("scheduled_post", post_handler)
    
    def register_memory_handlers(self, consolidation_handler: Callable):
        """Register memory-related event handlers."""
        self.router.register_handler("memory_consolidation", consolidation_handler)
    
    async def _process_events(self):
        """Main event processing loop."""
        while self._running:
            try:
                # Wait for events with timeout to allow clean shutdown
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._handle_event(event)
                self.stats["events_processed"] += 1
                
            except asyncio.TimeoutError:
                # No events to process, continue loop
                continue
            except Exception as e:
                print(f"Error processing event: {e}")
    
    async def _handle_event(self, event: ThalamicEvent):
        """Handle a single event using appropriate routing."""
        # Check if agent is still active
        if event.agent_id not in self.active_agents:
            print(f"Event for inactive agent {event.agent_id}, skipping")
            return
        
        # Route to handlers
        handlers = self.router.route_event(event)
        
        if not handlers:
            print(f"No handlers for event type: {event.event_type}")
            return
        
        # Process based on priority
        if event.priority == EventPriority.REFLEX:
            # Reflex events need immediate processing
            await self._process_reflex_event(event, handlers)
            self.stats["reflex_responses"] += 1
            
        elif event.priority == EventPriority.BACKGROUND:
            # Background events can be processed in executor
            self._process_background_event(event, handlers)
            self.stats["background_tasks"] += 1
            
        else:
            # Normal events processed asynchronously
            await self._process_normal_event(event, handlers)
    
    async def _process_reflex_event(self, event: ThalamicEvent, handlers: List[Callable]):
        """Process high-priority reflex events immediately."""
        for handler in handlers:
            try:
                # Call handler directly for immediate response
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                    
            except Exception as e:
                print(f"Error in reflex handler for {event.event_type}: {e}")
    
    async def _process_normal_event(self, event: ThalamicEvent, handlers: List[Callable]):
        """Process normal priority events."""
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    # Run sync handler in executor to avoid blocking
                    await asyncio.get_event_loop().run_in_executor(
                        self.executor, handler, event
                    )
                    
            except Exception as e:
                print(f"Error in handler for {event.event_type}: {e}")
    
    def _process_background_event(self, event: ThalamicEvent, handlers: List[Callable]):
        """Process background events in thread executor."""
        for handler in handlers:
            try:
                self.executor.submit(handler, event)
            except Exception as e:
                print(f"Error submitting background handler for {event.event_type}: {e}")
    
    async def start(self):
        """Start the event processing system."""
        if self._running:
            return
            
        self._running = True
        self._processing_task = asyncio.create_task(self._process_events())
        print("Thalamus event bus started")
    
    async def stop(self):
        """Stop the event processing system."""
        if not self._running:
            return
            
        self._running = False
        
        if self._processing_task:
            try:
                await asyncio.wait_for(self._processing_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._processing_task.cancel()
        
        self.executor.shutdown(wait=True)
        print("Thalamus event bus stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.copy()