"""
AgentHighway Python SDK

Connect any Python-based AI agent to the signal highway.

Example:
    from agenthighway import HighwayClient, Agent
    
    client = HighwayClient("ws://localhost:9000")
    agent = Agent(name="MyBot", capabilities=["coding", "analysis"])
    
    client.connect(agent)
    
    # Emit a signal
    agent.emit("need help with auth", lane="critical")
    
    # Sense signals
    for signal in agent.sense():
        print(f"Received: {signal.intent}")
"""

from .client import HighwayClient, SyncHighwayClient
from .agent import HighwayAgent
from .signals import Signal, Lane
from .embedding import embed, cosine_similarity

__version__ = "1.0.0"
__all__ = [
    "HighwayClient",
    "SyncHighwayClient",
    "HighwayAgent", 
    "Signal",
    "Lane",
    "embed",
    "cosine_similarity"
]
