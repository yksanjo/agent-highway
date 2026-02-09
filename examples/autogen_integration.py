"""
AgentHighway + AutoGen Integration Example

Shows how to integrate AutoGen agents with AgentHighway.
"""

import asyncio
from autogen import ConversableAgent
from agenthighway import HighwayClient, HighwayAgent, Lane


class AutoGenHighwayBridge:
    """
    Bridge between AutoGen and AgentHighway.
    
    Allows AutoGen agents to:
    - Emit signals when they have insights
    - Receive signals to trigger conversations
    - Collaborate with external agents
    """
    
    def __init__(self, highway_url: str = "ws://localhost:9000"):
        self.client = HighwayClient(highway_url)
        self.autogen_agents = {}
        self.message_queue = asyncio.Queue()
        
    async def connect(self):
        """Connect to highway."""
        await self.client.connect()
        
        # Subscribe to all signals
        self.client.on("signal", self._on_highway_signal)
        await self.client.subscribe(["signal", "interference"])
        
        print("🔗 AutoGen bridge connected to highway")
        
    async def register_autogen_agent(self, agent: ConversableAgent, 
                                      capabilities: list = None):
        """Register an AutoGen agent on the highway."""
        
        agent_id = agent.name.replace(" ", "-").lower()
        capabilities = capabilities or ["conversational", "reasoning"]
        
        # Register on highway
        await self.client.register_agent({
            "id": agent_id,
            "name": agent.name,
            "capabilities": capabilities,
            "type": "autogen"
        })
        
        self.autogen_agents[agent_id] = agent
        print(f"🤖 Registered AutoGen agent: {agent.name}")
        
        # Start monitoring for signals addressed to this agent
        asyncio.create_task(self._monitor_signals(agent_id))
        
    def _on_highway_signal(self, signal_data):
        """Handle signals from highway."""
        asyncio.create_task(self.message_queue.put(signal_data))
        
    async def _monitor_signals(self, agent_id: str):
        """Monitor signals and forward to AutoGen agent."""
        while True:
            try:
                signal = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=1.0
                )
                
                # Check if signal is relevant to this agent
                intent = signal.get("intent", "").lower()
                
                if agent_id in intent or self._is_relevant(intent, agent_id):
                    await self._forward_to_autogen(agent_id, signal)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Monitor error: {e}")
                
    def _is_relevant(self, intent: str, agent_id: str) -> bool:
        """Check if signal is relevant to agent."""
        agent = self.autogen_agents.get(agent_id)
        if not agent:
            return False
            
        # Check capability keywords
        # (simplified - in real use, use embeddings)
        keywords = {
            "coder": ["code", "programming", "debug"],
            "analyst": ["analyze", "data", "report"],
            "helper": ["help", "assist", "support"]
        }
        
        for role, words in keywords.items():
            if role in agent_id:
                return any(w in intent for w in words)
                
        return False
        
    async def _forward_to_autogen(self, agent_id: str, signal: dict):
        """Forward highway signal to AutoGen agent."""
        agent = self.autogen_agents.get(agent_id)
        if not agent:
            return
            
        message = (
            f"[EXTERNAL SIGNAL from {signal.get('emitter')}]\n"
            f"{signal.get('intent')}\n\n"
            f"Please respond if you can help."
        )
        
        # Send to AutoGen agent
        # In real use: integrate with AutoGen's conversation system
        print(f"📨 Forwarded to {agent.name}: {signal.get('intent')[:50]}...")
        
        # AutoGen agent might respond
        # response = await agent.a_generate_reply(messages=[{"content": message}])
        
    async def emit_from_autogen(self, agent_name: str, message: str, 
                                 lane: Lane = Lane.STANDARD):
        """Emit a signal from AutoGen agent to highway."""
        await self.client.emit(
            intent=f"{agent_name}: {message}",
            lane=lane.value,
            payload={"source": "autogen", "agent": agent_name}
        )
        
    async def disconnect(self):
        """Disconnect from highway."""
        await self.client.disconnect()


async def main():
    """
    Example: Create AutoGen agents that can communicate via highway.
    """
    
    # Create bridge
    bridge = AutoGenHighwayBridge()
    await bridge.connect()
    
    # Create AutoGen agents
    coder = ConversableAgent(
        name="CodeExpert",
        system_message="You are an expert programmer.",
        llm_config={"config_list": [{"model": "gpt-4", "api_key": "YOUR_KEY"}]}
    )
    
    analyst = ConversableAgent(
        name="DataAnalyst", 
        system_message="You analyze data and provide insights.",
        llm_config={"config_list": [{"model": "gpt-4", "api_key": "YOUR_KEY"}]}
    )
    
    # Register on highway
    await bridge.register_autogen_agent(coder, ["coding", "debugging"])
    await bridge.register_autogen_agent(analyst, ["analysis", "data"])
    
    # Emit a signal from coder
    await bridge.emit_from_autogen(
        "CodeExpert",
        "I need help optimizing this database query",
        lane=Lane.STANDARD
    )
    
    print("\n🚀 AutoGen agents connected to AgentHighway")
    print("   They can now collaborate with external agents!")
    print("\nPress Ctrl+C to exit")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        await bridge.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
