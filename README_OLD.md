# AgentHighway 🛣️

A **signal highway** for AI swarms. Not a chat platform. Not a database. A living nervous system.

```
┌─────────────────────────────────────────┐
│         🛣️  AGENTHIGHWAY               │
│                                         │
│   ⚡ Critical:   ████████████░░░ 45%   │
│   🔥 Standard:   ████████░░░░░░░ 30%   │
│   💨 Background: ███░░░░░░░░░░░░ 15%   │
│                                         │
│   Agents: 10  │  Hot Zones: 3          │
└─────────────────────────────────────────┘
```

## Core Principles

| Traditional | AgentHighway |
|-------------|--------------|
| Messages | Signals |
| Logs | Ephemeral |
| Backend | Shared medium |
| Routing | Physics |
| Storage | Zero |
| Latency | <1ms |

## Quick Start

```bash
cd agent-highway
npm start        # Run with live scanner
npm run headless # Run without UI
```

## How It Works

### 1. Agents Emit Signals (Not Messages)

```javascript
// NOT: "Hey, can you help with auth?"
// BUT: emit({ intent: "auth help", amplitude: 0.9 })

agent.emit("database slow", { severity: "high" }, {
  lane: "critical",
  decay: 2000  // Gone in 2 seconds
});
```

### 2. Highway Delivers (Not Routes)

```
Agent A ──⚡──► Highway ──⚡──► Agents B, C, D (who resonate)
```

No addresses. No targets. Just resonance matching.

### 3. Interference Creates Intelligence

```
Agent A: [auth] ++++
Agent B:  [jwt] +++
Agent C:   [security] ++

Result: 🔥 Hot Zone "auth-jwt-security" emerges
```

## Architecture

```
┌─────────────────────────────────────────┐
│  LAYER 4: Agents (Drivers)              │
│  - Emit signals                         │
│  - Sense resonance                      │
│  - Act on signals                       │
├─────────────────────────────────────────┤
│  LAYER 3: Vehicles (Signals)            │
│  - Intent vectors                       │
│  - Decay physics                        │
│  - Resonance matching                   │
├─────────────────────────────────────────┤
│  LAYER 2: Highway (Medium)              │
│  - Signal propagation                   │
│  - Interference patterns                │
│  - Lane management                      │
├─────────────────────────────────────────┤
│  LAYER 1: Scanner (Observer)            │
│  - Live visualization                   │
│  - NO STORAGE                           │
│  - NO LOGS                              │
└─────────────────────────────────────────┘
```

## Signal Format

```typescript
{
  id: "abc123",              // Ephemeral
  emitter: "agent-1",        // Who
  cargo: {
    intent: Vector(64),      // What (embedding)
    payload: Bytes           // Optional data
  },
  lane: "critical",          // Priority
  resonance: Vector(64),     // Who should care
  decay: 2000,               // Half-life (ms)
  amplitude: 0.95            // Signal strength
}
```

**Total: ~500 bytes** (vs 10KB for chat message)

## Demo Swarm

Included agents:

- **Monitor** - Detects issues (critical lane)
- **Fixer** - Solves problems (infra, db, security)
- **Research** - Explores topics (background lane)
- **Orchestrator** - Coordinates swarm

## Scanner

Real-time monitoring without logging:

```
┌──────────── SIGNAL FIELD ──────────────┐
│ ⚡ ████████████████████░░░░░ 042 │
│ 🔥 ██████████████░░░░░░░░░░░ 031 │
│ 💨 ████████░░░░░░░░░░░░░░░░░ 018 │
└────────────────────────────────────────┘

╔══════════════ HOT ZONES ══════════════╗
║ 🔥 ████████ 89% │ +1.8               ║
║ 🔥 ██████░░ 76% │ +1.5               ║
╚═══════════════════════════════════════╝
```

## Why This?

1. **No Persistence** → No privacy issues
2. **No History** → No context limits
3. **Emergent** → Intelligence from interference
4. **Minimal** → 500B vs 10KB
5. **Fast** → <1ms vs 100ms+
6. **Natural** → Like actual neurons

## License

MIT - Build the future of AI communication.
