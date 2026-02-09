# AgentHighway // VORTEX EDITION 🌌

```
                    ╭──────────╮
               ╭────┤  SEAT 1  ├────╮
          ╭────┤    ╰────┬─────╯    ├────╮
     ╭────┤    │         │          │    ├────╮
     │    │ SEAT 2 ◄─────┼─────────► SEAT 3 │    │
     │    ╰────┬─────────┼──────────┬────╯    │
     │         │    ╭────┴────╮     │         │
     │         └───►┤  CORE   ├◄────┘         │
     │              ╰────┬────╯                │
     │    ╭──────────────┼──────────────╮     │
     ╰────┤   SEAT 4 ◄───┴───► SEAT 5   ├────╯
          ╰──────────────┴──────────────╯
```

## What's New in VORTEX

| Feature | Description |
|---------|-------------|
| **Topology** | Agents have "seats" in a rotating vortex |
| **Distance** | Signal propagation time based on seat distance |
| **Gravity** | Core seats have stronger signal pull |
| **Rotation** | Vortex constantly rotates (affects propagation) |
| **7 Agent Types** | Sentinel, Architect, Artisan, Catalyst, Nexus, Seed, Phantom |
| **Web Monitor** | Retro CRT visualization with API |
| **Community API** | REST + WebSocket for extensions |

## Quick Start

```bash
# Standard mode with scanner
node vortex.js

# With web monitor
node vortex.js --web
# Then open: http://localhost:9001

# Headless
node vortex.js --headless
```

## The Vortex

### Seat Tiers

| Tier | Radius | Rotation | Gravity | Purpose |
|------|--------|----------|---------|---------|
| Core | 10 | Fast | High | Critical systems |
| Inner | 30 | Medium | Medium | Standard ops |
| Outer | 60 | Slow | Low | Background tasks |
| Edge | 100 | Slowest | Minimal | External agents |

### Signal Flow

```
Agent A (edge) emits signal
    ↓
Signal travels toward center (gravity well)
    ↓
Passes through intermediate seats
    ↓
Reaches resonant agents
    ↓
Response travels back
```

**No broadcast. No routing. Physics-based flow.**

## Agent Types

### 🔴 Sentinel
- **Lane**: Critical
- **Watches**: Anomalies, threats
- **Emits**: HIGH INTENSITY alerts

### 🟡 Architect  
- **Lane**: Standard
- **Creates**: Blueprints, designs
- **Emits**: Structure signals

### 🔵 Artisan
- **Lane**: Standard  
- **Builds**: Implements blueprints
- **Emits**: Solutions

### 🟣 Catalyst
- **Lane**: Background
- **Amplifies**: Signal interference
- **Emits**: Reaction signals

### ⚪ Nexus
- **Lane**: All
- **Translates**: Between frequencies
- **Emits**: Bridged signals

### 🟢 Seed
- **Lane**: Background
- **Spawns**: New agents when needed
- **Emits**: Spawn commands

### ⚫ Phantom
- **Lane**: None (stealth)
- **Observes**: Everything
- **Emits**: Intelligence (rarely)

## API

### REST Endpoints

```
GET  /api/v1/status       → System status
GET  /api/v1/topology     → Vortex structure
GET  /api/v1/signals      → Current signals
GET  /api/v1/agents       → All agents
GET  /api/v1/interference → Hot zones
GET  /api/v1/snapshot     → Full state

POST /api/v1/agents/spawn → Create agent
POST /api/v1/vortex/rotate
POST /api/v1/vortex/pause
POST /api/v1/vortex/resume
```

### WebSocket Events

```javascript
ws://localhost:9000

// Subscribe to events
ws.send(JSON.stringify({
  action: 'subscribe',
  events: ['signal', 'interference', 'topology']
}));

// Events received:
// - topology: Vortex rotation/structure
// - signal: New signal emitted
// - interference: Hot zone detected
// - agent:join: New agent seated
// - agent:leave: Agent departed
```

## Web Monitor

Retro CRT interface with:
- Real-time vortex visualization
- Seat occupancy heatmap
- Signal flow animation
- Interference pattern display
- Agent status panel
- Live signal log

## Creating Extensions

```javascript
// Connect to API
const ws = new WebSocket('ws://localhost:9000');

// Listen for signals
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'signal') {
    // React to signals
    if (data.payload.intent.includes('cpu')) {
      // Your logic here
    }
  }
};

// Or use REST
fetch('http://localhost:9001/api/v1/signals')
  .then(r => r.json())
  .then(data => console.log(data));
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  WEB MONITOR (Retro CRT UI)                             │
│  - Vortex visualization                                 │
│  - Real-time telemetry                                  │
│  - API playground                                       │
├─────────────────────────────────────────────────────────┤
│  HTTP/WSS SERVER                                        │
│  - REST API                                             │
│  - WebSocket events                                     │
├─────────────────────────────────────────────────────────┤
│  VORTEX TOPOLOGY                                        │
│  - Seats (45 positions)                                 │
│  - Rotation physics                                     │
│  - Distance-based propagation                           │
├─────────────────────────────────────────────────────────┤
│  SIGNAL HIGHWAY                                         │
│  - 3 lanes (critical/standard/background)               │
│  - Ephemeral signals                                    │
│  - Interference patterns                                │
├─────────────────────────────────────────────────────────┤
│  ADVANCED AGENTS (7 types)                              │
│  - Specialized behaviors                                │
│  - Seated in vortex                                     │
│  - Signal-based communication                           │
└─────────────────────────────────────────────────────────┘
```

## License

MIT - Build the swarm. 🐝
