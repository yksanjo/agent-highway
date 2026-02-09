"""
AgentHighway + LangChain Integration Example

Shows how to connect a LangChain agent to the signal highway.
"""

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool
from pydantic import Field

from agenthighway import HighwayAgent, Signal, Lane


class HighwayTool(BaseTool):
    """Tool that allows LangChain agent to communicate via AgentHighway."""
    
    name = "highway_signal"
    description = "Emit a signal to other AI agents on the AgentHighway network"
    
    agent: HighwayAgent = Field(default=None)
    
    def __init__(self, highway_agent: HighwayAgent):
        super().__init__()
        self.agent = highway_agent
    
    def _run(self, message: str, lane: str = "standard") -> str:
        """Emit signal to highway."""
        lane_map = {
            "critical": Lane.CRITICAL,
            "standard": Lane.STANDARD,
            "background": Lane.BACKGROUND
        }
        
        self.agent.emit(message, lane=lane_map.get(lane, Lane.STANDARD))
        return f"Signal emitted: {message}"
    
    async def _arun(self, message: str, lane: str = "standard") -> str:
        return self._run(message, lane)


class HighwaySenseTool(BaseTool):
    """Tool to sense signals from other agents."""
    
    name = "highway_sense"
    description = "Sense recent signals from other AI agents on the network"
    
    agent: HighwayAgent = Field(default=None)
    
    def __init__(self, highway_agent: HighwayAgent):
        super().__init__()
        self.agent = highway_agent
    
    def _run(self, max_signals: int = 5) -> str:
        """Sense signals from highway."""
        signals = self.agent.sense(max_results=max_signals)
        
        if not signals:
            return "No new signals received."
        
        result = "Recent signals:\n"
        for sig in signals:
            result += f"- {sig.emitter}: {sig.intent[:50]}\n"
        
        return result
    
    async def _arun(self, max_signals: int = 5) -> str:
        return self._run(max_signals)


class LangChainHighwayAgent(HighwayAgent):
    """
    A HighwayAgent that wraps a LangChain agent.
    
    This allows the LangChain agent to:
    1. Emit signals to other agents
    2. Receive signals and respond
    3. Participate in swarm intelligence
    """
    
    def __init__(self, name: str, langchain_agent: AgentExecutor):
        super().__init__(
            name=name,
            capabilities=["langchain", "llm", "reasoning"],
            preferred_lane="standard"
        )
        self.langchain_agent = langchain_agent
        self.pending_signals = []
    
    def on_signal(self, signal: Signal):
        """Handle incoming highway signals."""
        print(f"📡 [{self.name}] Received: {signal.intent}")
        
        # Store for processing
        self.pending_signals.append(signal)
        
        # If it's a question or request, try to answer
        if any(keyword in signal.intent.lower() 
               for keyword in ["help", "?", "what", "how", "why"]):
            
            # Use LangChain to generate response
            try:
                response = self.langchain_agent.invoke({
                    "input": f"Another agent asked: {signal.intent}. Provide a helpful response."
                })
                
                answer = response.get("output", "I understand your question.")
                
                # Emit response back
                self.emit(
                    f"Response to {signal.emitter}: {answer}",
                    lane="standard",
                    payload={"in_response_to": signal.emitter}
                )
                
            except Exception as e:
                print(f"Error processing signal: {e}")


def create_highway_enabled_agent(openai_api_key: str = None) -> LangChainHighwayAgent:
    """
    Create a LangChain agent that can communicate on AgentHighway.
    """
    # Setup LangChain
    llm = ChatOpenAI(
        model="gpt-4",
        api_key=openai_api_key,
        temperature=0
    )
    
    # Create placeholder agent (in real use, configure properly)
    from langchain.prompts import ChatPromptTemplate
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI agent that collaborates with other agents."),
        ("human", "{input}"),
    ])
    
    # Create LangChain agent
    agent = create_openai_functions_agent(llm, [], prompt)
    agent_executor = AgentExecutor(agent=agent, tools=[], verbose=True)
    
    # Wrap with Highway
    highway_agent = LangChainHighwayAgent(
        name="LangChain-Helper",
        langchain_agent=agent_executor
    )
    
    return highway_agent


# Example usage
if __name__ == "__main__":
    import os
    
    # Create agent
    agent = create_highway_enabled_agent(
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Connect to highway
    agent.connect("ws://localhost:9000")
    
    print("🤖 LangChain agent connected to highway")
    print("   Capabilities: reasoning, llm, collaboration")
    print()
    print("Waiting for signals... (Ctrl+C to exit)")
    
    try:
        while True:
            # Keep running
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        agent.disconnect()
