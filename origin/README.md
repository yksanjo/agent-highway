# 🛣️ Agent Highway Origin

Beacon-based monitoring system for AI agents using Cloudflare Workers and Durable Objects.

## What's New ✨

- ✅ **Ed25519 Signature Verification** - Cryptographically signed liens
- ✅ **Horizontal Sharding** - Scales across 256+ Durable Objects
- ✅ **Built-in Dashboard** - Real-time HTML dashboard at root path
- ✅ **Python SDK** - Full-featured async SDK with Ed25519 signing
- ✅ **Comprehensive Tests** - Unit tests with Vitest

## Overview

Agent Highway Origin is a **signal lien** (existence proof) collection and visualization system that enables AI agents to emit cryptographically-signed, timestamped beacons at key lifecycle moments. This creates a distributed audit trail that becomes the substrate for agent activity visualization and cross-agent discovery.

## 🎯 Core Concept: The "Signal Lien"

A signal lien is an existence proof that an agent emits:

| Event | Description |
|-------|-------------|
| `birth` | Agent instantiation |
| `heartbeat` | Periodic "I'm alive" signal |
| `task_start` | Beginning of work unit |
| `task_complete` | Completion of work unit |
| `death` | Graceful shutdown |
| `handoff` | Delegation to another agent |
| `error` | Exception or failure |

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   Agent     │────▶│  Cloudflare Worker   │────▶│  Dashboard UI   │
│  (Python)   │     │  + Durable Objects   │     │   (Built-in)    │
└─────────────┘     └──────────────────────┘     └─────────────────┘
                           │                              │
                           ▼                              ▼
                    ┌──────────────┐              ┌──────────────┐
                    │  SQLite DO   │              │  Real-time   │
                    │  (Time-series│              │  Dashboard   │
                    │   storage)   │              │  WebSocket   │
                    └──────────────┘              └──────────────┘
```

### Sharding for Scale

The system uses intelligent sharding to distribute load across multiple Durable Objects:

- **Beacon writes** → Sharded by agent_id (256 shards via first 2 chars)
- **Global queries** → Routed to 'global' DO
- **Agent-specific queries** → Routed to appropriate shard

```typescript
// Example shard keys
"agent-abc123" → "shard_ab"
"worker-xyz789" → "shard_xy"
```

## 🚀 Quick Start

### 1. Deploy the Cloudflare Worker

```bash
cd agent-highway-origin
npm install
npm run deploy
```

### 2. Install Python SDK

```bash
cd agent-highway/sdk
pip install -r requirements.txt
```

### 3. Emit Your First Beacon

```python
import asyncio
from agent_highway import AgentBeacon, BeaconConfig

async def main():
    config = BeaconConfig(
        endpoint="https://your-worker.workers.dev",
        lane="production"
    )
    
    async with AgentBeacon("my-agent", "worker", config=config) as beacon:
        await beacon.start_heartbeat()
        
        await beacon.task_start("task-001", {"input": "data"})
        # ... do work ...
        await beacon.task_complete("task-001", {"output": "result"})

asyncio.run(main())
```

### 4. View the Dashboard

Open your worker URL in a browser:
- `https://your-worker.workers.dev/` - Live dashboard with real-time updates
- `https://your-worker.workers.dev/agents/live` - Live agent states (JSON)
- `https://your-worker.workers.dev/stats` - System statistics (JSON)

## 📡 API Endpoints

### POST /beacon
Emit a signal lien.

```json
{
  "agent_id": "agent-001",
  "agent_type": "worker",
  "timestamp": 1704067200000,
  "event_type": "task_start",
  "sequence": 5,
  "signature": "base64url_signature",
  "public_key": "base64url_public_key",
  "task_id": "task-001",
  "lane": "default",
  "metadata": {"region": "us-east"}
}
```

**Signature Verification:**
The signature is Ed25519 over a canonical JSON message:
```json
{
  "agent_id": "...",
  "agent_type": "...",
  "timestamp": 1704067200000,
  "event_type": "...",
  "sequence": 5,
  "lane": "...",
  "metadata": {...}
}
```

### GET /agents/live
Get current agent states.

```json
{
  "agents": [
    {
      "agent_id": "agent-001",
      "agent_type": "worker",
      "status": "active",
      "last_timestamp": 1704067200000,
      "lien_count": 42,
      "lane": "default"
    }
  ],
  "count": 1
}
```

### GET /beacon/stream
Query historical liens.

Query params:
- `since` - Unix timestamp (ms)
- `type` - Filter by agent type
- `event` - Filter by event type
- `lane` - Filter by lane
- `limit` - Max results (default: 100, max: 1000)

### WebSocket /beacon/ws
Real-time lien stream.

Connect via WebSocket to receive live lien updates:
```javascript
const ws = new WebSocket('wss://your-worker.workers.dev/beacon/ws');
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  // msg.type === 'lien' | 'snapshot'
  // msg.data = lien data
};
```

## 🐍 Python SDK Reference

### AgentBeacon

```python
from agent_highway import AgentBeacon, BeaconConfig, beacon

# Method 1: Context manager (recommended)
config = BeaconConfig(endpoint="https://...", lane="prod")
async with AgentBeacon("my-agent", "worker", config) as b:
    await b.task_start("task-1")
    # ... work ...
    await b.task_complete("task-1")

# Method 2: Quick context manager
async with beacon("my-agent", endpoint="https://...") as b:
    await b.emit("custom_event", metadata={"key": "value"})

# Method 3: Manual lifecycle
beacon = AgentBeacon("my-agent", "worker", config)
await beacon.birth()
await beacon.start_heartbeat()
await beacon.task_start("task-1")
# ... work ...
await beacon.task_complete("task-1")
await beacon.death()
```

### Key Methods

| Method | Description |
|--------|-------------|
| `birth()` | Emit birth lien (auto-called on context enter) |
| `death()` | Emit death lien (auto-called on context exit) |
| `heartbeat()` | Emit single heartbeat |
| `start_heartbeat()` | Start auto heartbeat every 30s |
| `stop_heartbeat()` | Stop auto heartbeat |
| `task_start(task_id, metadata)` | Mark task start |
| `task_complete(task_id, metadata)` | Mark task completion |
| `handoff(target_agent_id, task_id)` | Handoff to another agent |
| `error(message, metadata)` | Emit error event |
| `emit(event_type, ...)` | Emit custom event |

### Cryptographic Keys

The SDK automatically generates Ed25519 key pairs:

```python
# Auto-generated (default)
beacon = AgentBeacon("my-agent", "worker", config)

# From existing key
beacon = AgentBeacon.from_private_key_pem(pem_string, "my-agent", "worker", config)

# Export for persistence
private_key_pem = beacon.get_private_key_pem()
public_key = beacon.get_public_key()
```

## 🎨 Dashboard Features

The built-in dashboard (`/`) provides:

- **Live Stats Cards** - Active/ghost/dead agents, total liens
- **Agent Grid** - Visual overview with status indicators
- **Live Lien Stream** - Real-time feed via WebSocket
- **Lane Filtering** - Protocol-specific traffic analysis
- **Auto-refresh** - Stats update every 5 seconds

## 🛠️ Development

```bash
# Install dependencies
npm install

# Start local dev server
npm run dev

# Run tests
npm test

# Type check
npm run typecheck

# Deploy
npm run deploy
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch

# With coverage (add to vitest.config.ts)
```

## 📦 Project Structure

```
agent-highway-origin/
├── src/
│   ├── index.ts          # Main worker + Durable Object
│   ├── index.test.ts     # Unit tests
│   └── types.d.ts        # TypeScript definitions
├── sdk/
│   ├── agent_highway.py  # Python SDK
│   └── requirements.txt  # Python dependencies
├── scripts/
│   ├── deploy.sh         # Deployment script
│   └── dev.sh            # Local development
├── wrangler.toml         # Cloudflare config
├── package.json
├── tsconfig.json
└── vitest.config.ts      # Test configuration
```

## 🔐 Security

- **Ed25519 Signatures** - All liens are cryptographically signed
- **Signature Verification** - Server validates every lien
- **Sequence Numbers** - Prevents replay attacks
- **Key Persistence** - Export/import keys for agent identity

## 📊 Metrics & Observability

The system tracks:
- Agent birth/death events
- Task lifecycle (start/complete)
- Heartbeat health
- Lane-specific traffic
- Ghost agent detection (60s timeout)
- Response times

## 🌐 Integration Example

```python
import asyncio
from agent_highway import AgentBeacon, BeaconConfig

async def process_task(task_id: str, data: dict):
    config = BeaconConfig(
        endpoint="https://highway.example.com",
        lane="ml-pipeline"
    )
    
    async with AgentBeacon(f"worker-{task_id}", "ml-worker", config) as beacon:
        try:
            await beacon.task_start(task_id, {"input_size": len(data)})
            
            # Your actual work here
            result = await run_ml_model(data)
            
            await beacon.task_complete(task_id, {
                "output_size": len(result),
                "accuracy": result.accuracy
            })
            
        except Exception as e:
            await beacon.error(str(e), {"task_id": task_id})
            raise

asyncio.run(process_task("task-123", {"image": "..."}))
```

## 📈 Scaling Considerations

The system is designed to scale:

1. **Durable Object Sharding** - 256+ shards distribute load
2. **SQLite Limits** - Each DO has 1GB storage limit
3. **Rate Limits** - Cloudflare Workers limits apply
4. **WebSocket Limits** - 1000 concurrent connections per DO

For high-scale deployments:
- Increase shard count (modify `getShardKey`)
- Add data retention policies
- Consider DO eviction strategies

## 📄 License

MIT
