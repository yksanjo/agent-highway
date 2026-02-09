"""
HighwayAgent - Base class for AI agents
"""

from typing import List, Dict, Any, Optional
from .client import HighwayClient, SyncHighwayClient


class HighwayAgent:
    """
    Base class for AI agents that connect to AgentHighway.
    
    Subclass this and override on_signal() to handle incoming signals.
    
    Example:
        class MyAgent(HighwayAgent):
            def on_signal(self, signal):
                if "help" in signal.intent:
                    self.emit("I can help!", lane="standard")
    """
    
    def __init__(self, 
                 name: str,
                 capabilities: List[str],
                 preferred_lane: str = "standard",
                 auto_connect: bool = True):
        self.name = name
        self.id = name.lower().replace(" ", "-")
        self.capabilities = capabilities
        self.preferred_lane = preferred_lane
        self.auto_connect = auto_connect
        
        self.client: Optional[SyncHighwayClient] = None
        self.connected = False
        self.received_signals = []
        
    def connect(self, highway_url: str = "ws://localhost:9000") -> bool:
        """Connect to the highway."""
        self.client = SyncHighwayClient(highway_url)
        
        if not self.client.connect():
            return False
        
        # Register with highway
        self.client.register_agent({
            "id": self.id,
            "name": self.name,
            "capabilities": self.capabilities,
            "lane": self.preferred_lane
        })
        
        # Setup signal handler
        self.client.on("signal", self._on_signal_received)
        
        self.connected = True
        print(f"🤖 Agent {self.name} connected to highway")
        return True
    
    def disconnect(self):
        """Disconnect from highway."""
        if self.client:
            self.client.disconnect()
        self.connected = False
    
    def emit(self, intent: str, payload: Any = None, 
             lane: Optional[str] = None, **kwargs) -> str:
        """Emit a signal onto the highway."""
        if not self.connected:
            raise RuntimeError("Agent not connected. Call connect() first.")
        
        lane = lane or self.preferred_lane
        return self.client.emit(intent, payload=payload, lane=lane, **kwargs)
    
    def _on_signal_received(self, signal_data: Dict):
        """Internal handler for incoming signals."""
        signal = Signal.from_dict(signal_data)
        self.received_signals.append(signal)
        self.on_signal(signal)
    
    def on_signal(self, signal: 'Signal'):
        """
        Override this method to handle incoming signals.
        
        Args:
            signal: The received signal with intent, payload, etc.
        """
        pass
    
    def sense(self, timeout: float = 1.0) -> List['Signal']:
        """
        Sense signals from the highway.
        
        Returns signals received in the last timeout seconds.
        """
        # In real impl: fetch from highway
        # For now: return cached signals
        signals = self.received_signals[:]
        self.received_signals = []
        return signals
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class Signal:
    """Represents a signal on the highway."""
    
    def __init__(self, 
                 intent: str,
                 emitter: str,
                 lane: str = "standard",
                 payload: Any = None,
                 intensity: float = 1.0):
        self.intent = intent
        self.emitter = emitter
        self.lane = lane
        self.payload = payload
        self.intensity = intensity
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Signal':
        return cls(
            intent=data.get("intent", ""),
            emitter=data.get("emitter", "unknown"),
            lane=data.get("lane", "standard"),
            payload=data.get("payload"),
            intensity=data.get("intensity", 1.0)
        )
    
    def __repr__(self):
        return f"Signal({self.emitter}: {self.intent[:30]}...)"
