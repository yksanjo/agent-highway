# 🛣️ AgentHighway

> **A Nervous System for AI Swarms**
> 
> No logs. No backend. Just signals.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](docker-compose.yml)
[![WebSocket](https://img.shields.io/badge/WebSocket-Ready-green.svg)](src/server.js)

[📖 Documentation](#documentation) • [🚀 Quick Start](#quick-start) • [💻 SDKs](#sdks) • [🐳 Docker](#docker) • [🌐 API](#api)

---

## 🎯 What is AgentHighway?

AgentHighway is a **signal-based communication protocol** for AI agents. Unlike chat platforms or message queues, it creates a shared medium where agents communicate through ephemeral signals that interfere, resonate, and self-organize.

```
Traditional: Agent A → "message" → Server → "message" → Agent B (100ms+)
AgentHighway: Agent A ──⚡──► [Shared Field] ──⚡──► Agent B (<1ms)
```

### Key Differences

| Feature | Chat Platforms | Message Queues | AgentHighway |
|---------|---------------|----------------|--------------|
| **Storage** | Infinite logs | Persistent | **Zero** |
| **Latency** | 100ms+ | 50ms+ | **<1ms** |
| **State** | Stateful | Stateful | **Ephemeral** |
| **Routing** | Address-based | Topic-based | **Resonance-based** |
| **Scale** | 100s agents | 1000s agents | **10,000+ agents** |
| **Intelligence** | Human-readable | Structured | **Emergent** |

---

## 🌌 The Vortex

Agents exist in a **rotating topological space** with 45+ seats across 4 tiers:

```
                    🌀 THE VORTEX
                    
       Edge (24) ──slow rotation──┐
            │                     │
       Outer (12) ──medium───────┤
            │                     │
       Inner (6) ──fast─────────┤
            │                     │
       Core (3) ──intense────────┘
```

- **Distance affects propagation** (physics-based)
- **Gravity wells** pull signals toward center
- **Interference patterns** create emergent intelligence
- **No routing tables** - pure signal physics

---

## 🚀 Quick Start

### 1. Start the Highway

```bash
# Clone and start
git clone https://github.com/YOUR_USERNAME/agent-highway.git
cd agent-highway
docker-compose up -d

# Or local Node.js
npm install
node vortex.js --web
```

### 2. Connect an Agent (Python)

```bash
pip install -e sdks/python
```

```python
from agenthighway import HighwayAgent, Lane

agent = HighwayAgent("MyBot", ["coding", "analysis"])
agent.connect("ws://localhost:9000")

# Emit a signal
agent.emit("need help with auth system", lane=Lane.CRITICAL)

# Handle responses
@agent.on_signal
def on_signal(signal):
    print(f"Received: {signal.intent}")
```

### 3. Watch the Magic

Open `http://localhost:9001` for the retro CRT monitor:

![Monitor Preview](docs/images/monitor-preview.png)

---

## 💻 SDKs

### Python
```bash
pip install agenthighway
```
```python
from agenthighway import HighwayAgent
agent = HighwayAgent("Bot", ["coding"])
agent.connect()
```

### JavaScript/TypeScript
```bash
npm install @agenthighway/sdk
```
```typescript
import { HighwayAgent } from '@agenthighway/sdk';
const agent = new HighwayAgent({ name: "Bot", capabilities: ["coding"] });
await agent.connect();
```

---

## 🐳 Docker

```yaml
version: '3.8'
services:
  highway:
    image: agenthighway/core:latest
    ports:
      - "9000:9000"  # WebSocket
      - "9001:9001"  # HTTP API
```

```bash
docker-compose up -d
curl http://localhost:9001/api/v1/status
```

---

## 🌐 API

### WebSocket (Real-time)
```javascript
const ws = new WebSocket('ws://localhost:9000');

ws.send(JSON.stringify({
  action: 'emit',
  payload: {
    intent: 'hello world',
    lane: 'standard'
  }
}));
```

### REST
```bash
GET  /api/v1/status      # System status
GET  /api/v1/topology    # Vortex structure
GET  /api/v1/signals     # Current signals
POST /api/v1/agents/spawn # Create agent
```

---

## 🎨 Architecture

```
┌─────────────────────────────────────────────────────────┐
│  WEB MONITOR (Retro CRT UI)                             │
│  - Real-time vortex visualization                       │
│  - Signal flow animation                                │
│  - Hot zone detection                                   │
├─────────────────────────────────────────────────────────┤
│  HTTP/WSS SERVER                                        │
│  - REST API                                             │
│  - WebSocket events                                     │
├─────────────────────────────────────────────────────────┤
│  VORTEX TOPOLOGY                                        │
│  - 45 seats across 4 tiers                              │
│  - Rotating spatial structure                           │
│  - Gravity-based propagation                            │
├─────────────────────────────────────────────────────────┤
│  SIGNAL HIGHWAY                                         │
│  - 3 lanes (critical/standard/background)               │
│  - Ephemeral signals (no storage)                       │
│  - Interference patterns                                │
├─────────────────────────────────────────────────────────┤
│  ADVANCED AGENTS (7 types)                              │
│  - Sentinel, Architect, Artisan, Catalyst               │
│  - Nexus, Seed, Phantom                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🧠 Agent Types

| Agent | Purpose | Lane | Special Ability |
|-------|---------|------|-----------------|
| **Sentinel** | Monitor threats | Critical | Detects anomalies |
| **Architect** | Design systems | Standard | Creates blueprints |
| **Artisan** | Build solutions | Standard | Implements code |
| **Catalyst** | Amplify signals | Background | Creates interference |
| **Nexus** | Translate between agents | All | Universal translator |
| **Seed** | Spawn new agents | Background | Self-replication |
| **Phantom** | Stealth observer | Shadow | Undetectable |

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Latency** | <1ms |
| **Throughput** | 1M+ signals/sec |
| **Storage** | 0 GB |
| **Scale** | 10,000+ agents |
| **Signal Size** | ~500 bytes |

---

## 🔌 Framework Integrations

- **LangChain**: Native tools for emit/sense
- **AutoGen**: Bridge for multi-agent conversations
- **CrewAI**: Compatible via SDK
- **Custom**: Any Python/JS agent

---

## 📚 Documentation

- [Getting Started](GETTING_STARTED.md) - Your first 5 minutes
- [Architecture](AGENT_HIGHWAY_MANIFESTO.md) - Design philosophy
- [API Reference](docs/API.md) - Complete API docs
- [Examples](examples/) - Working code samples
- [SDK Guide](sdks/README.md) - Build with SDKs

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📜 License

MIT - See [LICENSE](LICENSE)

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=agenthighway/core&type=Date)](https://star-history.com/#agenthighway/core&Date)

---

**No logs. No backend. Just flow.** 🌊
