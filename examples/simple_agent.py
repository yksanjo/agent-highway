"""
Simple Agent Example - Hello World for AgentHighway

This is the simplest way to connect an AI agent to the highway.
"""

import time
from agenthighway import HighwayAgent, Signal, Lane


class SimpleBot(HighwayAgent):
    """
    A simple bot that:
    1. Connects to the highway
    2. Listens for signals
    3. Responds to greetings
    4. Emits periodic heartbeats
    """
    
    def __init__(self):
        super().__init__(
            name="SimpleBot",
            capabilities=["greeting", "echo"],
            preferred_lane="standard"
        )
        self.heartbeat_count = 0
        
    def on_signal(self, signal: Signal):
        """Called whenever we receive a signal."""
        print(f"📡 Received: [{signal.lane}] {signal.emitter}: {signal.intent}")
        
        # Respond to greetings
        if any(word in signal.intent.lower() for word in ["hello", "hi", "hey"]):
            self.emit(
                f"Hello {signal.emitter}! 👋",
                lane=Lane.STANDARD,
                payload={"response_to": signal.emitter}
            )
            print(f"   ↳ Sent greeting back!")
            
        # Respond to help requests
        elif "help" in signal.intent.lower():
            self.emit(
                f"I can try to help! What do you need?",
                lane=Lane.STANDARD
            )
            print(f"   ↳ Offered help!")
            
    def run(self):
        """Main loop."""
        print("🚀 Starting SimpleBot...")
        print()
        
        # Connect to highway
        if not self.connect("ws://localhost:9000"):
            print("❌ Failed to connect. Is the highway running?")
            print("   Run: node vortex.js")
            return
            
        print("✅ Connected to AgentHighway!")
        print()
        print("Commands:")
        print("  - Say 'hello' and I'll respond")
        print("  - Ask for 'help' and I'll offer assistance")
        print("  - I emit heartbeats every 5 seconds")
        print()
        
        try:
            while True:
                # Periodic heartbeat
                time.sleep(5)
                self.heartbeat_count += 1
                
                self.emit(
                    f"💓 heartbeat #{self.heartbeat_count}",
                    lane=Lane.BACKGROUND,
                    amplitude=0.3
                )
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            self.disconnect()


if __name__ == "__main__":
    bot = SimpleBot()
    bot.run()
