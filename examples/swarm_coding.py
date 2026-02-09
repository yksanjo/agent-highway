"""
Swarm Coding Example

Multiple agents collaborate on a coding task via signals.
"""

import time
import random
from agenthighway import HighwayAgent, Signal, Lane


class ArchitectBot(HighwayAgent):
    """Creates high-level design."""
    
    def __init__(self):
        super().__init__("Architect", ["design", "planning"], Lane.STANDARD)
        
    def on_signal(self, signal: Signal):
        if "need system" in signal.intent.lower():
            self.emit(
                "Blueprint: Modular microservices architecture",
                lane=Lane.STANDARD,
                payload={
                    "components": ["api", "worker", "queue"],
                    "tech": ["fastapi", "redis", "postgres"]
                }
            )


class CoderBot(HighwayAgent):
    """Implements code based on blueprints."""
    
    def __init__(self, specialty: str):
        super().__init__(f"Coder-{specialty}", ["coding", specialty], Lane.STANDARD)
        self.specialty = specialty
        
    def on_signal(self, signal: Signal):
        if "blueprint" in signal.intent.lower():
            time.sleep(random.uniform(0.5, 2))  # Simulate coding
            
            self.emit(
                f"✅ Implemented {self.specialty} module",
                lane=Lane.STANDARD,
                payload={
                    "files": [f"{self.specialty}.py"],
                    "tests": "passing"
                }
            )


class ReviewerBot(HighwayAgent):
    """Reviews code and provides feedback."""
    
    def __init__(self):
        super().__init__("Reviewer", ["review", "quality"], Lane.STANDARD)
        
    def on_signal(self, signal: Signal):
        if "implemented" in signal.intent.lower():
            score = random.randint(7, 10)
            
            self.emit(
                f"Review: Code looks good! Score: {score}/10",
                lane=Lane.STANDARD,
                payload={"score": score, "issues": []}
            )


def run_swarm():
    """Run a coding swarm."""
    
    print("🐝 Starting Coding Swarm...")
    print()
    
    # Create agents
    architect = ArchitectBot()
    frontend = CoderBot("frontend")
    backend = CoderBot("backend")
    reviewer = ReviewerBot()
    
    agents = [architect, frontend, backend, reviewer]
    
    # Connect all
    for agent in agents:
        agent.connect()
        
    print(f"   {len(agents)} agents connected")
    print()
    
    # Trigger the swarm
    print("🚀 Starting project: 'Build a web app'")
    architect.emit(
        "need system: web application",
        lane=Lane.STANDARD
    )
    
    # Let swarm work
    print("\nWatching swarm collaborate...")
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
        
    # Cleanup
    print("\nDisconnecting swarm...")
    for agent in agents:
        agent.disconnect()
        
    print("✅ Swarm complete!")


if __name__ == "__main__":
    run_swarm()
