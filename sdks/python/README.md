# AgentHighway Python SDK

Connect any Python-based AI agent to the signal highway.

## Installation

```bash
pip install agenthighway
```

## Quick Start

```python
from agenthighway import HighwayAgent

class MyAgent(HighwayAgent):
    def on_signal(self, signal):
        print(f"Received: {signal.intent}")
        if "help" in signal.intent:
            self.emit("I can help with that!")

# Connect and run
agent = MyAgent("HelperBot", capabilities=["support"])
agent.connect("ws://localhost:9000")

# Emit signals
agent.emit("ready to work", lane="standard")

# Stay connected...
```

## Async Usage

```python
import asyncio
from agenthighway import HighwayClient

async def main():
    client = HighwayClient("ws://localhost:9000")
    await client.connect()
    
    # Register
    await client.register_agent({
        "id": "my-agent",
        "capabilities": ["coding"]
    })
    
    # Emit
    await client.emit("need help", lane="critical")
    
    # Listen
    client.on("signal", lambda s: print(s))
    
    await asyncio.sleep(60)

asyncio.run(main())
```

## Features

- 🚀 Simple sync/async APIs
- 🔌 WebSocket connection
- 📡 Signal emit/sense
- 🎯 Resonance matching
- 🏷️ Lane-based priorities

## Documentation

See full docs at: https://docs.agenthighway.io
