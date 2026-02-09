"""
Agent Beacon SDK

Core SDK for emitting signal liens to Agent Highway Origin.
"""

import asyncio
import hashlib
import json
import secrets
import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Callable, Dict, Optional, Union
import logging

import aiohttp

# Configure logging
logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of signal lien events."""
    BIRTH = "birth"
    HEARTBEAT = "heartbeat"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    DEATH = "death"
    HANDOFF = "handoff"
    ERROR = "error"


class BeaconError(Exception):
    """Base exception for beacon errors."""
    pass


class AuthenticationError(BeaconError):
    """Raised when beacon authentication fails."""
    pass


class NetworkError(BeaconError):
    """Raised when network communication fails."""
    pass


@dataclass
class SignalLien:
    """A signal lien (existence proof) emitted by an agent."""
    agent_id: str
    agent_type: str
    timestamp: int
    event_type: EventType
    sequence: int
    signature: str
    task_id: Optional[str] = None
    parent_agent_id: Optional[str] = None
    target_agent_id: Optional[str] = None
    payload_hash: Optional[str] = None
    public_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    lane: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class BeaconConfig:
    """Configuration for the beacon emitter."""
    endpoint: str = "https://agent-highway-origin.yksanjo.workers.dev"
    heartbeat_interval: int = 30  # seconds
    timeout: int = 5  # seconds for HTTP requests
    max_retries: int = 3
    retry_delay: float = 1.0
    auto_heartbeat: bool = True
    lane: str = "default"  # Protocol lane: a2a, mcp, custom


class AgentBeacon:
    """
    Main class for emitting signal liens (beacons) to Agent Highway Origin.
    
    This class provides async methods for agents to emit existence proofs
    that can be collected and visualized in the Origin dashboard.
    
    Example:
        >>> async with AgentBeacon("worker-1", "task_processor") as beacon:
        ...     await beacon.start_heartbeat()
        ...     await beacon.task_start("task-123")
        ...     # Do work...
        ...     await beacon.task_complete("task-123")
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: str = "agent",
        config: Optional[BeaconConfig] = None,
        private_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the beacon emitter.
        
        Args:
            agent_id: Unique identifier for this agent instance.
                     If not provided, a UUID will be generated.
            agent_type: Type/class of agent (e.g., "worker", "orchestrator")
            config: BeaconConfig instance with endpoint and timing settings
            private_key: Optional Ed25519 private key for signing
            metadata: Optional metadata to include in all liens
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.agent_type = agent_type
        self.config = config or BeaconConfig()
        self.metadata = metadata or {}
        
        # State
        self._sequence = 0
        self._session: Optional[aiohttp.ClientSession] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._shutdown = False
        self._birth_time = time.time()
        
        # Signing key (for future Ed25519 implementation)
        self._private_key = private_key or secrets.token_hex(32)
        self._public_key = hashlib.sha256(self._private_key.encode()).hexdigest()[:32]
        
        # Task tracking
        self._active_tasks: set = set()
        
        logger.debug(f"Beacon initialized for agent {self.agent_id} ({self.agent_type})")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        await self.birth()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - emits death beacon."""
        await self.shutdown()
    
    async def connect(self):
        """Initialize HTTP session."""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
    
    async def disconnect(self):
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def _generate_signature(self, lien: SignalLien) -> str:
        """
        Generate a signature for the lien.
        
        Note: Currently uses HMAC-SHA256 for MVP. In production,
        this should use Ed25519 signatures.
        """
        # Create message from lien fields (excluding signature)
        message_data = {
            "agent_id": lien.agent_id,
            "agent_type": lien.agent_type,
            "timestamp": lien.timestamp,
            "event_type": lien.event_type,
            "task_id": lien.task_id,
            "parent_agent_id": lien.parent_agent_id,
            "target_agent_id": lien.target_agent_id,
            "payload_hash": lien.payload_hash,
            "sequence": lien.sequence,
        }
        message = json.dumps(message_data, sort_keys=True)
        
        # Generate HMAC
        signature = hmac.new(
            self._private_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _hash_payload(self, payload: Optional[Dict[str, Any]]) -> Optional[str]:
        """Generate a hash of the payload for integrity verification."""
        if payload is None:
            return None
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()[:16]
    
    async def emit(
        self,
        event_type: Union[EventType, str],
        payload: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        parent_agent_id: Optional[str] = None,
        target_agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emit a signal lien (beacon) to the collector.
        
        Args:
            event_type: Type of event (birth, heartbeat, task_start, etc.)
            payload: Optional data payload to include
            task_id: Optional task identifier
            parent_agent_id: Optional parent agent (for lineage tracking)
            target_agent_id: Optional target agent (for handoffs)
            metadata: Additional metadata for this specific lien
            
        Returns:
            True if emitted successfully, False otherwise
            
        Note:
            This method is fire-and-forget. It will not block agent execution
            and failures are logged but not raised.
        """
        if self._shutdown:
            logger.warning("Cannot emit beacon: beacon is shutdown")
            return False
        
        if self._session is None:
            await self.connect()
        
        self._sequence += 1
        
        # Merge metadata
        merged_metadata = {**self.metadata}
        if metadata:
            merged_metadata.update(metadata)
        
        # Create lien
        lien = SignalLien(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=int(time.time() * 1000),
            event_type=event_type if isinstance(event_type, EventType) else EventType(event_type),
            sequence=self._sequence,
            signature="",  # Will be filled
            task_id=task_id,
            parent_agent_id=parent_agent_id,
            target_agent_id=target_agent_id,
            payload_hash=self._hash_payload(payload),
            public_key=self._public_key,
            metadata=merged_metadata if merged_metadata else None,
            lane=self.config.lane
        )
        
        # Sign
        lien.signature = self._generate_signature(lien)
        
        # Emit with retries
        for attempt in range(self.config.max_retries):
            try:
                async with self._session.post(
                    f"{self.config.endpoint}/beacon",
                    json=lien.to_dict(),
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 201:
                        logger.debug(f"Beacon emitted: {event_type} (seq: {self._sequence})")
                        return True
                    elif response.status == 401:
                        logger.error("Beacon authentication failed")
                        return False
                    else:
                        text = await response.text()
                        logger.warning(f"Beacon emit failed: {response.status} - {text}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Beacon timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"Beacon emit error (attempt {attempt + 1}): {e}")
            
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        logger.error(f"Failed to emit beacon after {self.config.max_retries} attempts")
        return False
    
    async def birth(self, metadata: Optional[Dict[str, Any]] = None):
        """
        Emit a birth beacon - signals that this agent has been instantiated.
        
        Args:
            metadata: Optional metadata about the agent's birth context
        """
        birth_metadata = {
            "birth_time": self._birth_time,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            **(metadata or {})
        }
        return await self.emit(EventType.BIRTH, metadata=birth_metadata)
    
    async def death(self, reason: str = "shutdown", payload: Optional[Dict] = None):
        """
        Emit a death beacon - signals that this agent is shutting down.
        
        Args:
            reason: Reason for death (shutdown, error, killed, etc.)
            payload: Additional data about the death
        """
        death_payload = {
            "reason": reason,
            "lifetime_seconds": time.time() - self._birth_time,
            **(payload or {})
        }
        return await self.emit(EventType.DEATH, payload=death_payload)
    
    async def heartbeat(self, metadata: Optional[Dict] = None):
        """
        Emit a single heartbeat beacon.
        
        Args:
            metadata: Optional status metadata (memory usage, queue depth, etc.)
        """
        hb_metadata = {
            "active_tasks": len(self._active_tasks),
            "uptime_seconds": time.time() - self._birth_time,
            **(metadata or {})
        }
        return await self.emit(EventType.HEARTBEAT, metadata=hb_metadata)
    
    async def start_heartbeat(self, interval: Optional[int] = None):
        """
        Start periodic heartbeat emission.
        
        Args:
            interval: Seconds between heartbeats (defaults to config value)
        """
        interval = interval or self.config.heartbeat_interval
        
        async def heartbeat_loop():
            while not self._shutdown:
                await self.heartbeat()
                await asyncio.sleep(interval)
        
        self._heartbeat_task = asyncio.create_task(heartbeat_loop())
        logger.info(f"Heartbeat started (interval: {interval}s)")
    
    async def stop_heartbeat(self):
        """Stop the periodic heartbeat."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            logger.info("Heartbeat stopped")
    
    async def task_start(self, task_id: str, payload: Optional[Dict] = None):
        """
        Emit a task_start beacon.
        
        Args:
            task_id: Unique identifier for the task
            payload: Optional task data
        """
        self._active_tasks.add(task_id)
        return await self.emit(EventType.TASK_START, task_id=task_id, payload=payload)
    
    async def task_complete(
        self, 
        task_id: str, 
        result: Optional[str] = "success",
        payload: Optional[Dict] = None
    ):
        """
        Emit a task_complete beacon.
        
        Args:
            task_id: Task identifier
            result: Task result (success, error, cancelled)
            payload: Optional result data
        """
        self._active_tasks.discard(task_id)
        complete_payload = {"result": result, **(payload or {})}
        return await self.emit(
            EventType.TASK_COMPLETE, 
            task_id=task_id, 
            payload=complete_payload
        )
    
    async def handoff(
        self, 
        target_agent_id: str, 
        context: Optional[Dict] = None,
        task_id: Optional[str] = None
    ):
        """
        Emit a handoff beacon - signals delegation to another agent.
        
        Args:
            target_agent_id: ID of the agent taking over
            context: Optional context to pass to target agent
            task_id: Optional task being handed off
        """
        return await self.emit(
            EventType.HANDOFF,
            target_agent_id=target_agent_id,
            task_id=task_id,
            payload=context
        )
    
    async def error(self, error: Exception, context: Optional[Dict] = None):
        """
        Emit an error beacon.
        
        Args:
            error: The exception that occurred
            context: Optional context about what was happening
        """
        error_payload = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            **(context or {})
        }
        return await self.emit(EventType.ERROR, payload=error_payload)
    
    async def shutdown(self, reason: str = "shutdown"):
        """
        Graceful shutdown - stops heartbeat and emits death beacon.
        
        Args:
            reason: Reason for shutdown
        """
        if self._shutdown:
            return
        
        self._shutdown = True
        
        await self.stop_heartbeat()
        await self.death(reason)
        await self.disconnect()
        
        logger.info(f"Beacon shutdown complete for {self.agent_id}")


# Import hmac here to avoid issues if not needed
import hmac
import sys
