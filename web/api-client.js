/**
 * AgentHighway API Client
 * 
 * REST API for community extensions
 */

const API_BASE = 'http://localhost:9001';
const WS_BASE = 'ws://localhost:9000';

/**
 * AgentHighway API v1.0
 * 
 * This API allows external tools and community extensions
 * to interact with the vortex without disrupting the ephemeral flow.
 */
const API_DOCS = `
═══════════════════════════════════════════════════════════════
  AGENTHIGHWAY API v1.0
  NO LOGS • NO STORAGE • COMMUNITY EXTENSIONS WELCOME
═══════════════════════════════════════════════════════════════

// WEBSOCKET (Real-time Events)
───────────────────────────────────────────────────────────────
ws://localhost:9000

Events emitted:
  - 'topology'     : Vortex structure update
  - 'signal'       : New signal emitted
  - 'agent:join'   : Agent entered highway
  - 'agent:leave'  : Agent exited highway
  - 'interference' : Hot zone detected

Subscribe:
  ws.send(JSON.stringify({
    action: 'subscribe',
    events: ['signal', 'interference']
  }));


// REST API
───────────────────────────────────────────────────────────────

GET /api/v1/status
  → { online: true, cycle: 1234, agents: 10, signals: 45 }

GET /api/v1/topology
  → { seats: [...], agents: [...], rotation: 0.5 }

GET /api/v1/signals?lane=critical&limit=10
  → { signals: [...] }

GET /api/v1/agents
  → { agents: [...] }

GET /api/v1/agents/:id
  → { id, seat, capabilities, focus: [...] }

GET /api/v1/interference
  → { hotZones: [...] }


// AGENT CONTROL
───────────────────────────────────────────────────────────────

POST /api/v1/agents/spawn
  body: {
    type: 'sentinel',  // sentinel|architect|artisan|catalyst|phantom
    config: { ... }
  }
  → { agentId, seatId }

POST /api/v1/agents/:id/emit
  body: {
    intent: "cpu high",
    payload: { ... },
    lane: "critical",  // critical|standard|background
    amplitude: 0.9,
    decay: 2000
  }
  → { signalId }

POST /api/v1/agents/:id/move
  body: { seatId: "inner-3" }
  → { success: true }

DELETE /api/v1/agents/:id
  → { success: true }


// VORTEX CONTROL
───────────────────────────────────────────────────────────────

POST /api/v1/vortex/rotate
  body: { speed: 0.5 }
  → { success: true }

POST /api/v1/vortex/pause
  → { paused: true }

POST /api/v1/vortex/resume
  → { resumed: true }


// EXTENSIONS / PLUGINS
───────────────────────────────────────────────────────────────

POST /api/v1/extensions/register
  body: {
    name: "my-extension",
    webhook: "http://localhost:8080/events",
    events: ["signal", "agent:join"]
  }
  → { extensionId, apiKey }

DELETE /api/v1/extensions/:id
  → { success: true }


// SNAPSHOT (Current state only - NO HISTORY)
───────────────────────────────────────────────────────────────

GET /api/v1/snapshot
  → Full topology + signals + agents (one moment in time)

WebSocket alternative:
  ws.send(JSON.stringify({ action: 'snapshot' }));


═══════════════════════════════════════════════════════════════
`;

class HighwayAPI {
  constructor() {
    this.ws = null;
    this.connected = false;
    this.listeners = new Map();
  }
  
  /**
   * Connect to WebSocket
   */
  connect() {
    try {
      this.ws = new WebSocket(WS_BASE);
      
      this.ws.onopen = () => {
        this.connected = true;
        this.updateConnectionStatus(true);
        console.log('🔗 Connected to AgentHighway');
      };
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      };
      
      this.ws.onclose = () => {
        this.connected = false;
        this.updateConnectionStatus(false);
        // Auto-reconnect
        setTimeout(() => this.connect(), 3000);
      };
      
      this.ws.onerror = (err) => {
        console.error('WebSocket error:', err);
      };
    } catch (e) {
      console.error('Failed to connect:', e);
    }
  }
  
  /**
   * Handle incoming messages
   */
  handleMessage(data) {
    // Emit to registered listeners
    const handlers = this.listeners.get(data.type) || [];
    for (const handler of handlers) {
      handler(data);
    }
    
    // Also emit specific events
    switch (data.type) {
      case 'topology':
        if (window.vortexVis) {
          window.vortexVis.updateTopology(data.payload);
        }
        break;
      case 'signal':
        this.logSignal(data.payload);
        break;
      case 'interference':
        this.logInterference(data.payload);
        break;
    }
  }
  
  /**
   * Subscribe to events
   */
  on(eventType, handler) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(handler);
  }
  
  /**
   * REST API Methods
   */
  async getStatus() {
    return this.fetch('/api/v1/status');
  }
  
  async getTopology() {
    return this.fetch('/api/v1/topology');
  }
  
  async getSignals(lane = null, limit = 10) {
    const query = new URLSearchParams();
    if (lane) query.set('lane', lane);
    query.set('limit', limit);
    return this.fetch(`/api/v1/signals?${query}`);
  }
  
  async spawnAgent(type, config = {}) {
    return this.fetch('/api/v1/agents/spawn', {
      method: 'POST',
      body: JSON.stringify({ type, config })
    });
  }
  
  async emitSignal(agentId, intent, options = {}) {
    return this.fetch(`/api/v1/agents/${agentId}/emit`, {
      method: 'POST',
      body: JSON.stringify({ intent, ...options })
    });
  }
  
  async fetch(path, options = {}) {
    const url = `${API_BASE}${path}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });
    return response.json();
  }
  
  /**
   * UI Control Methods
   */
  rotateVortex() {
    this.sendCommand({ action: 'rotate', speed: 0.5 });
  }
  
  pause() {
    this.sendCommand({ action: 'pause' });
    const btn = document.getElementById('pause-btn');
    if (btn) {
      btn.textContent = 'RESUME_SIM';
      btn.onclick = () => this.resume();
    }
  }
  
  resume() {
    this.sendCommand({ action: 'resume' });
    const btn = document.getElementById('pause-btn');
    if (btn) {
      btn.textContent = 'PAUSE_SIM';
      btn.onclick = () => this.pause();
    }
  }
  
  reset() {
    if (confirm('RESET_FIELD? This clears all signals.')) {
      this.sendCommand({ action: 'reset' });
    }
  }
  
  spawn(type) {
    this.spawnAgent(type);
    this.log(`Spawned ${type}`, 'info');
  }
  
  sendCommand(cmd) {
    if (this.ws && this.connected) {
      this.ws.send(JSON.stringify(cmd));
    }
  }
  
  /**
   * UI Helpers
   */
  updateConnectionStatus(connected) {
    const indicator = document.getElementById('conn-status');
    const text = document.getElementById('conn-text');
    
    if (indicator) {
      indicator.className = 'indicator ' + (connected ? 'online' : 'crit');
    }
    if (text) {
      text.textContent = connected ? 'ONLINE' : 'OFFLINE';
    }
  }
  
  logSignal(signal) {
    const lane = signal.lane || 'standard';
    const prefix = lane === 'critical' ? '⚡' : lane === 'standard' ? '●' : '○';
    const className = lane === 'critical' ? 'log-crit' : lane === 'standard' ? 'log-warn' : 'log-info';
    
    this.log(`${prefix} ${signal.emitter?.slice(0, 8)}: ${signal.cargo?.intent?.slice(0, 30)}`, className);
  }
  
  logInterference(zone) {
    this.log(`🔥 INTERFERENCE: ${zone.intensity.toFixed(2)}`, 'warn');
  }
  
  log(message, className = '') {
    const container = document.getElementById('log-container');
    if (!container) return;
    
    const entry = document.createElement('div');
    entry.className = 'log-entry ' + className;
    
    const time = new Date().toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
    
    entry.innerHTML = `<span class="log-time">[${time}]</span> ${message}`;
    container.insertBefore(entry, container.firstChild);
    
    // Keep only last 50 entries
    while (container.children.length > 50) {
      container.removeChild(container.lastChild);
    }
  }
  
  /**
   * Show/Hide API docs
   */
  showDocs() {
    const modal = document.getElementById('api-modal');
    const docs = document.getElementById('api-docs');
    if (modal && docs) {
      docs.textContent = API_DOCS;
      modal.classList.add('active');
    }
  }
  
  hideDocs() {
    const modal = document.getElementById('api-modal');
    if (modal) {
      modal.classList.remove('active');
    }
  }
  
  /**
   * Export snapshot
   */
  async exportSnapshot() {
    const data = await this.getTopology();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `highway-snapshot-${Date.now()}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
    this.log('📸 Snapshot exported', 'info');
  }
}

// Create global API instance
const api = new HighwayAPI();
