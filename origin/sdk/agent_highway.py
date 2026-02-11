"""
Agent Highway Python SDK
Beacon-based monitoring for AI agents

Usage:
    from agent_highway import AgentBeacon, BeaconConfig
    
    config = BeaconConfig(endpoint="https://your-worker.workers.dev")
    
    async with AgentBeacon("my-agent", "worker", config=config) as beacon:
        await beacon.start_heartbeat()
        await beacon.task_start("task-001")
        # ... do work ...
        await beacon.task_complete("task-001")
"""

import asyncio
import json
import time
import base64
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, Callable
from contextlib import asynccontextmanager
import aiohttp
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey
)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


@dataclass
class BeaconConfig:
    """Configuration for AgentBeacon"""
    endpoint: str
    lane: str = "default"
    heartbeat_interval: float = 30.0  # seconds
    auto_heartbeat: bool = True
    timeout: float = 10.0
    
    def __post_init__(self):
        # Ensure endpoint doesn't have trailing slash
        self.endpoint = self.endpoint.rstrip('/')


@dataclass
class SignalLien:
    """A signal lien emitted by an agent"""
    agent_id: str
    agent_type: str
    timestamp: int
    event_type: str
    sequence: int
    signature: str
    public_key: str
    task_id: Optional[str] = None
    parent_agent_id: Optional[str] = None
    target_agent_id: Optional[str] = None
    payload_hash: Optional[str] = None
    lane: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}


class AgentBeacon:
    """
    Beacon emitter for AI agents.
    
    Emits cryptographically-signed signal liens to the Agent Highway Origin.
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str = "worker",
        config: Optional[BeaconConfig] = None,
        private_key: Optional[Ed25519PrivateKey] = None
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or BeaconConfig(endpoint="http://localhost:8787")
        
        # Generate or use provided Ed25519 key pair
        if private_key is None:
            self._private_key = Ed25519PrivateKey.generate()
        else:
            self._private_key = private_key
            
        self._public_key = self._private_key.public_key()
        self._public_key_b64 = self._encode_public_key()
        
        # Sequence number for replay protection
        self._sequence = 0
        
        # State tracking
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._active = False
        self._current_task: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
    def _encode_public_key(self) -> str:
        """Encode public key to base64url"""
        raw = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return self._base64url_encode(raw)
    
    def _base64url_encode(self, data: bytes) -> str:
        """Base64url encode without padding"""
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')
    
    def _sign_message(self, message: str) -> str:
        """Sign a message with Ed25519"""
        signature = self._private_key.sign(message.encode('utf-8'))
        return self._base64url_encode(signature)
    
    def _create_lien(
        self,
        event_type: str,
        task_id: Optional[str] = None,
        parent_agent_id: Optional[str] = None,
        target_agent_id: Optional[str] = None,
        payload_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SignalLien:
        """Create a signed signal lien"""
        self._sequence += 1
        
        lien = SignalLien(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=int(time.time() * 1000),
            event_type=event_type,
            sequence=self._sequence,
            signature="",  # Will be filled after signing
            public_key=self._public_key_b64,
            task_id=task_id,
            parent_agent_id=parent_agent_id,
            target_agent_id=target_agent_id,
            payload_hash=payload_hash,
            lane=self.config.lane,
            metadata=metadata or {}
        )
        
        # Create canonical message and sign
        message_obj = {
            "agent_id": lien.agent_id,
            "agent_type": lien.agent_type,
            "timestamp": lien.timestamp,
            "event_type": lien.event_type,
            "task_id": lien.task_id,
            "parent_agent_id": lien.parent_agent_id,
            "target_agent_id": lien.target_agent_id,
            "payload_hash": lien.payload_hash,
            "sequence": lien.sequence,
            "lane": lien.lane,
            "metadata": lien.metadata
        }
        message = json.dumps(message_obj, separators=(',', ':'))
        lien.signature = self._sign_message(message)
        
        return lien
    
    async def _emit(self, lien: SignalLien) -> Dict[str, Any]:
        """Emit a lien to the beacon collector"""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        
        url = f"{self.config.endpoint}/beacon"
        
        async with self._session.post(
            url,
            json=lien.to_dict(),
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as resp:
            resp.raise_for_status()
            return await resp.json()
    
    async def emit(
        self,
        event_type: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SignalLien:
        """
        Emit a custom lien event.
        
        Args:
            event_type: Type of event (birth, heartbeat, task_start, etc.)
            task_id: Optional task ID
            metadata: Optional metadata dictionary
            
        Returns:
            The emitted SignalLien
        """
        lien = self._create_lien(
            event_type=event_type,
            task_id=task_id,
            metadata=metadata
        )
        await self._emit(lien)
        return lien
    
    async def birth(self, metadata: Optional[Dict[str, Any]] = None) -> SignalLien:
        """Emit a birth lien (agent instantiation)"""
        # Reset sequence for birth
        self._sequence = 0
        return await self.emit("birth", metadata=metadata)
    
    async def death(self, metadata: Optional[Dict[str, Any]] = None) -> SignalLien:
        """Emit a death lien (graceful shutdown)"""
        return await self.emit("death", metadata=metadata)
    
    async def heartbeat(self, metadata: Optional[Dict[str, Any]] = None) -> SignalLien:
        """Emit a heartbeat lien"""
        return await self.emit("heartbeat", metadata=metadata)
    
    async def task_start(
        self,
        task_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SignalLien:
        """Emit a task_start lien"""
        self._current_task = task_id
        return await self.emit("task_start", task_id=task_id, metadata=metadata)
    
    async def task_complete(
        self,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SignalLien:
        """Emit a task_complete lien"""
        task = task_id or self._current_task
        if task:
            self._current_task = None
        return await self.emit("task_complete", task_id=task, metadata=metadata)
    
    async def error(
        self,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SignalLien:
        """Emit an error lien"""
        meta = metadata or {}
        meta["error"] = error_message
        return await self.emit("error", metadata=meta)
    
    async def handoff(
        self,
        target_agent_id: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SignalLien:
        """Emit a handoff lien (delegation to another agent)"""
        lien = self._create_lien(
            event_type="handoff",
            target_agent_id=target_agent_id,
            task_id=task_id or self._current_task,
            metadata=metadata
        )
        await self._emit(lien)
        return lien
    
    async def start_heartbeat(self):
        """Start automatic heartbeat emission"""
        if not self.config.auto_heartbeat:
            return
            
        self._active = True
        
        async def heartbeat_loop():
            while self._active:
                try:
                    await self.heartbeat()
                except Exception as e:
                    print(f"Heartbeat error: {e}")
                await asyncio.sleep(self.config.heartbeat_interval)
        
        self._heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    async def stop_heartbeat(self):
        """Stop automatic heartbeat emission"""
        self._active = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.birth()
        await self.start_heartbeat()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop_heartbeat()
        
        if exc_type:
            await self.error(str(exc_val))
        else:
            await self.death()
        
        if self._session:
            await self._session.close()
    
    def get_public_key(self) -> str:
        """Get the base64url-encoded public key"""
        return self._public_key_b64
    
    def get_private_key_pem(self) -> str:
        """Export private key as PEM (for storage)"""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
    
    @classmethod
    def from_private_key_pem(
        cls,
        pem: str,
        agent_id: str,
        agent_type: str = "worker",
        config: Optional[BeaconConfig] = None
    ) -> "AgentBeacon":
        """Create AgentBeacon from a PEM-encoded private key"""
        private_key = serialization.load_pem_private_key(pem.encode('utf-8'), password=None)
        if not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError("Key must be an Ed25519 private key")
        return cls(agent_id, agent_type, config, private_key)


class BeaconMetrics:
    """Collect and report metrics about beacon emissions"""
    
    def __init__(self, beacon: AgentBeacon):
        self.beacon = beacon
        self.emissions: list = []
        self.errors: list = []
        
    def record_emission(self, lien: SignalLien, response_time_ms: float):
        """Record a successful emission"""
        self.emissions.append({
            "timestamp": time.time(),
            "event_type": lien.event_type,
            "response_time_ms": response_time_ms
        })
        
    def record_error(self, error: Exception):
        """Record an emission error"""
        self.errors.append({
            "timestamp": time.time(),
            "error": str(error)
        })
        
    def get_stats(self) -> Dict[str, Any]:
        """Get emission statistics"""
        if not self.emissions:
            return {"total_emissions": 0, "total_errors": len(self.errors)}
        
        recent = [e for e in self.emissions if time.time() - e["timestamp"] < 3600]
        avg_response = sum(e["response_time_ms"] for e in recent) / len(recent) if recent else 0
        
        return {
            "total_emissions": len(self.emissions),
            "total_errors": len(self.errors),
            "emissions_1h": len(recent),
            "avg_response_ms": round(avg_response, 2),
            "error_rate": len(self.errors) / (len(self.emissions) + len(self.errors))
        }


# Convenience function for quick usage
@asynccontextmanager
async def beacon(
    agent_id: str,
    agent_type: str = "worker",
    endpoint: str = "http://localhost:8787",
    lane: str = "default"
):
    """
    Quick context manager for emitting beacons.
    
    Usage:
        async with beacon("my-agent", endpoint="https://...") as b:
            await b.task_start("task-1")
            # ... do work ...
            await b.task_complete("task-1")
    """
    config = BeaconConfig(endpoint=endpoint, lane=lane)
    async with AgentBeacon(agent_id, agent_type, config) as b:
        yield b


if __name__ == "__main__":
    # Example usage
    async def main():
        config = BeaconConfig(
            endpoint="http://localhost:8787",
            lane="test"
        )
        
        async with AgentBeacon("demo-agent", "worker", config) as beacon:
            print(f"Agent public key: {beacon.get_public_key()}")
            
            # Start some work
            await beacon.task_start("task-001", {"input": "test data"})
            await asyncio.sleep(1)
            await beacon.task_complete("task-001", {"output": "result"})
            
            # Keep alive for a bit
            await asyncio.sleep(5)
    
    asyncio.run(main())
