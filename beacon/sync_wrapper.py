"""
Synchronous wrapper for the async beacon SDK.

For use in synchronous contexts where async/await is not available.
"""

import asyncio
import atexit
import threading
from typing import Optional, Dict, Any

from .beacon_sdk import AgentBeacon, BeaconConfig, EventType


class SyncBeacon:
    """
    Synchronous wrapper around AgentBeacon.
    
    This class provides synchronous methods for emitting beacons,
    suitable for use in synchronous codebases.
    
    Example:
        >>> beacon = SyncBeacon("my-agent", "worker")
        >>> beacon.start()
        >>> beacon.task_start("task-123")
        >>> # Do work...
        >>> beacon.task_complete("task-123")
        >>> beacon.shutdown()
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: str = "agent",
        config: Optional[BeaconConfig] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize synchronous beacon.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type/class of agent
            config: BeaconConfig instance
            metadata: Optional metadata
        """
        self._async_beacon = AgentBeacon(
            agent_id=agent_id,
            agent_type=agent_type,
            config=config,
            metadata=metadata
        )
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        
    def _ensure_loop(self):
        """Ensure event loop is running in background thread."""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
    
    def _run_loop(self):
        """Run the event loop in background thread."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
    
    def _run_async(self, coro):
        """Run an async coroutine synchronously."""
        self._ensure_loop()
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=10)  # 10 second timeout
    
    def start(self):
        """Initialize beacon and emit birth signal."""
        self._run_async(self._async_beacon.connect())
        self._run_async(self._async_beacon.birth())
        self._running = True
        
        # Register cleanup
        atexit.register(self.shutdown)
        
    def shutdown(self, reason: str = "shutdown"):
        """Shutdown beacon and emit death signal."""
        if not self._running:
            return
        
        self._run_async(self._async_beacon.shutdown(reason))
        self._running = False
        
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
    
    def emit(
        self,
        event_type: str,
        payload: Optional[Dict] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Emit a beacon synchronously.
        
        Args:
            event_type: Type of event
            payload: Optional payload data
            task_id: Optional task identifier
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        return self._run_async(self._async_beacon.emit(
            event_type=event_type,
            payload=payload,
            task_id=task_id,
            metadata=metadata
        ))
    
    def heartbeat(self, metadata: Optional[Dict] = None) -> bool:
        """Emit a heartbeat beacon."""
        return self._run_async(self._async_beacon.heartbeat(metadata))
    
    def task_start(self, task_id: str, payload: Optional[Dict] = None) -> bool:
        """Emit a task_start beacon."""
        return self._run_async(self._async_beacon.task_start(task_id, payload))
    
    def task_complete(
        self, 
        task_id: str, 
        result: str = "success",
        payload: Optional[Dict] = None
    ) -> bool:
        """Emit a task_complete beacon."""
        return self._run_async(self._async_beacon.task_complete(task_id, result, payload))
    
    def handoff(self, target_agent_id: str, context: Optional[Dict] = None) -> bool:
        """Emit a handoff beacon."""
        return self._run_async(self._async_beacon.handoff(target_agent_id, context))
    
    def error(self, error: Exception, context: Optional[Dict] = None) -> bool:
        """Emit an error beacon."""
        return self._run_async(self._async_beacon.error(error, context))
    
    def start_heartbeat(self, interval: int = 30):
        """Start periodic heartbeat."""
        self._run_async(self._async_beacon.start_heartbeat(interval))
    
    def stop_heartbeat(self):
        """Stop periodic heartbeat."""
        self._run_async(self._async_beacon.stop_heartbeat())
