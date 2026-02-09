"""
WebSocket client for connecting to AgentHighway
"""

import asyncio
import json
import websockets
from typing import Optional, Callable, Dict, Any, List


class HighwayClient:
    """
    Async client for connecting to AgentHighway vortex.
    
    Usage:
        client = HighwayClient("ws://localhost:9000")
        await client.connect()
        
        # Register agent
        await client.register_agent({
            "id": "my-agent",
            "capabilities": ["coding"]
        })
        
        # Emit signal
        await client.emit({
            "intent": "help needed",
            "lane": "standard"
        })
    """
    
    def __init__(self, url: str = "ws://localhost:9000"):
        self.url = url
        self.ws = None
        self.connected = False
        self.agent_id = None
        self.handlers = {}
        self._listen_task = None
        
    async def connect(self) -> bool:
        """Connect to the highway."""
        try:
            self.ws = await websockets.connect(self.url)
            self.connected = True
            self._listen_task = asyncio.create_task(self._listen())
            print(f"🔌 Connected to AgentHighway at {self.url}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from highway."""
        self.connected = False
        if self._listen_task:
            self._listen_task.cancel()
        if self.ws:
            await self.ws.close()
        print("🔌 Disconnected")
    
    async def _listen(self):
        """Listen for incoming messages."""
        try:
            async for message in self.ws:
                data = json.loads(message)
                await self._handle_message(data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.connected:
                print(f"⚠️  Listen error: {e}")
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming message."""
        msg_type = data.get("type")
        if msg_type in self.handlers:
            await self.handlers[msg_type](data.get("payload"))
    
    def on(self, event_type: str, handler: Callable):
        """Register event handler."""
        self.handlers[event_type] = handler
    
    async def register_agent(self, agent_config: Dict[str, Any]) -> bool:
        """Register an agent on the highway."""
        if not self.connected:
            raise ConnectionError("Not connected to highway")
        
        await self.ws.send(json.dumps({
            "action": "register_agent",
            "payload": agent_config
        }))
        
        self.agent_id = agent_config.get("id")
        return True
    
    async def emit(self, intent: str, payload: Any = None, 
                   lane: str = "standard", amplitude: float = 0.8,
                   decay: int = 2000) -> str:
        """Emit a signal onto the highway."""
        if not self.connected:
            raise ConnectionError("Not connected")
        
        signal = {
            "action": "emit",
            "payload": {
                "intent": intent,
                "payload": payload,
                "lane": lane,
                "amplitude": amplitude,
                "decay": decay
            }
        }
        
        await self.ws.send(json.dumps(signal))
        return f"sig-{asyncio.get_event_loop().time()}"
    
    async def subscribe(self, events: List[str]):
        """Subscribe to event types."""
        await self.ws.send(json.dumps({
            "action": "subscribe",
            "events": events
        }))


class SyncHighwayClient:
    """Synchronous wrapper for HighwayClient."""
    
    def __init__(self, url: str = "ws://localhost:9000"):
        self.url = url
        self._async_client = HighwayClient(url)
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
    
    def connect(self) -> bool:
        return self._loop.run_until_complete(self._async_client.connect())
    
    def disconnect(self):
        self._loop.run_until_complete(self._async_client.disconnect())
    
    def emit(self, intent: str, **kwargs) -> str:
        return self._loop.run_until_complete(
            self._async_client.emit(intent, **kwargs)
        )
    
    def on(self, event_type: str, handler: Callable):
        self._async_client.on(event_type, handler)
