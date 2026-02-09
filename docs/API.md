# AgentHighway API Reference

## Overview

AgentHighway provides both **WebSocket** (real-time) and **REST** (request/response) APIs.

Base URLs:
- WebSocket: `ws://localhost:9000`
- REST: `http://localhost:9001`

---

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:9000');

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### Actions

#### Register Agent
```json
{
  "action": "register_agent",
  "payload": {
    "id": "my-agent",
    "name": "My Agent",
    "capabilities": ["coding", "analysis"],
    "preferredLane": "standard"
  }
}
```

#### Emit Signal
```json
{
  "action": "emit",
  "payload": {
    "intent": "need help with auth",
    "payload": { "details": "..." },
    "lane": "critical",
    "amplitude": 0.9,
    "decay": 2000
  }
}
```

#### Subscribe to Events
```json
{
  "action": "subscribe",
  "events": ["signal", "interference", "topology"]
}
```

### Events

#### signal
Emitted when any agent emits a signal.
```json
{
  "type": "signal",
  "payload": {
    "id": "sig-abc123",
    "intent": "help needed",
    "emitter": "agent-1",
    "lane": "critical",
    "intensity": 0.85,
    "timestamp": 1770669123456
  }
}
```

#### interference
Emitted when hot zones (constructive interference) are detected.
```json
{
  "type": "interference",
  "payload": {
    "intensity": 1.8,
    "match": 0.92,
    "agents": ["agent-1", "agent-2"],
    "combinedIntent": "auth-security"
  }
}
```

#### topology
Periodic update of vortex structure.
```json
{
  "type": "topology",
  "payload": {
    "rotation": 0.5,
    "cycle": 1234,
    "seats": [...],
    "agents": [...]
  }
}
```

---

## REST API

### Status

```bash
GET /api/v1/status
```

Response:
```json
{
  "online": true,
  "cycle": 1234,
  "rotation": 0.5,
  "agents": 10,
  "signals": {
    "critical": 5,
    "standard": 12,
    "background": 23
  }
}
```

### Topology

```bash
GET /api/v1/topology
```

Response:
```json
{
  "rotation": 0.5,
  "cycle": 1234,
  "seats": [
    {
      "id": "core-0",
      "tier": "core",
      "position": {"x": 5, "y": 0, "z": 2},
      "occupants": ["sentinel-alpha"],
      "capacity": 3,
      "gravity": 0.95
    }
  ],
  "agents": [
    {
      "id": "sentinel-alpha",
      "seat": "core-0",
      "capabilities": ["monitoring"]
    }
  ]
}
```

### Signals

```bash
GET /api/v1/signals?lane=critical&limit=10
```

Parameters:
- `lane` (optional): Filter by lane (critical|standard|background)
- `limit` (optional): Max results (default 10)

Response:
```json
{
  "signals": [
    {
      "id": "sig-abc123",
      "emitter": "agent-1",
      "intent": "cpu high",
      "lane": "critical",
      "intensity": 0.92,
      "birthTime": 1770669123456,
      "decay": 2000
    }
  ]
}
```

### Agents

#### List Agents
```bash
GET /api/v1/agents
```

Response:
```json
{
  "agents": [
    {
      "id": "sentinel-alpha",
      "seat": "core-0",
      "capabilities": ["monitoring", "alerts"],
      "lane": "critical"
    }
  ]
}
```

#### Spawn Agent
```bash
POST /api/v1/agents/spawn
Content-Type: application/json

{
  "type": "sentinel",
  "config": {
    "capabilities": ["custom"]
  }
}
```

Response:
```json
{
  "success": true,
  "agentId": "sentinel-xyz789",
  "seatId": "core-1"
}
```

### Interference

```bash
GET /api/v1/interference
```

Response:
```json
{
  "hotZones": [
    {
      "intensity": 1.85,
      "match": 0.94,
      "agents": ["agent-1", "agent-2"]
    }
  ]
}
```

### Snapshot

```bash
GET /api/v1/snapshot
```

Returns complete current state (topology + signals + status).

### Vortex Control

#### Rotate
```bash
POST /api/v1/vortex/rotate
Content-Type: application/json

{
  "speed": 0.5
}
```

#### Pause
```bash
POST /api/v1/vortex/pause
```

#### Resume
```bash
POST /api/v1/vortex/resume
```

---

## Error Handling

All errors follow this format:

```json
{
  "error": "Description of what went wrong",
  "code": "ERROR_CODE",
  "timestamp": 1770669123456
}
```

Common codes:
- `NOT_CONNECTED`: WebSocket not established
- `AGENT_NOT_FOUND`: Agent ID doesn't exist
- `SEAT_FULL`: No capacity in requested tier
- `INVALID_LANE`: Lane must be critical|standard|background

---

## Rate Limits

- REST: 100 requests/minute
- WebSocket: 1000 signals/minute per agent
- Burst: 10 signals/second

---

## SDKs

See SDK documentation for language-specific implementations:
- [Python SDK](../sdks/python/README.md)
- [JavaScript SDK](../sdks/javascript/README.md)
