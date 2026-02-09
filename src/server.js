/**
 * AgentHighway Web Server
 * 
 * Provides:
 * - WebSocket for real-time events
 * - REST API for community extensions
 * - Serves the web visualization
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { WebSocketServer } = require('ws');

class HighwayServer {
  constructor(highway, vortex, options = {}) {
    this.highway = highway;
    this.vortex = vortex;
    this.port = options.port || 9001;
    this.wsPort = options.wsPort || 9000;
    
    this.clients = new Set();
    this.extensions = new Map();
    
    this.initHTTPServer();
    this.initWSServer();
  }
  
  initHTTPServer() {
    this.server = http.createServer((req, res) => {
      // CORS
      res.setHeader('Access-Control-Allow-Origin', '*');
      res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
      
      if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
      }
      
      // Route
      const url = new URL(req.url, `http://localhost:${this.port}`);
      
      if (url.pathname.startsWith('/api/')) {
        this.handleAPI(req, res, url);
      } else {
        this.handleStatic(req, res, url);
      }
    });
  }
  
  initWSServer() {
    this.wss = new WebSocketServer({ port: this.wsPort });
    
    this.wss.on('connection', (ws) => {
      console.log('🔌 WebSocket client connected');
      this.clients.add(ws);
      
      // Send initial topology
      this.sendToClient(ws, {
        type: 'topology',
        payload: this.vortex.snapshot()
      });
      
      ws.on('message', (data) => {
        try {
          const cmd = JSON.parse(data);
          this.handleWSCommand(ws, cmd);
        } catch (e) {
          ws.send(JSON.stringify({ error: 'Invalid JSON' }));
        }
      });
      
      ws.on('close', () => {
        this.clients.delete(ws);
      });
    });
    
    // Broadcast updates
    setInterval(() => this.broadcastTopology(), 100);
    setInterval(() => this.broadcastSignals(), 50);
  }
  
  handleAPI(req, res, url) {
    const path = url.pathname;
    const method = req.method;
    
    // API Routing
    const routes = {
      'GET /api/v1/status': () => this.getStatus(),
      'GET /api/v1/topology': () => this.vortex.snapshot(),
      'GET /api/v1/signals': () => this.getSignals(url.searchParams),
      'GET /api/v1/agents': () => this.getAgents(),
      'GET /api/v1/interference': () => this.getInterference(),
      'GET /api/v1/snapshot': () => this.getSnapshot(),
      
      'POST /api/v1/agents/spawn': () => this.parseBody(req).then(body => this.spawnAgent(body)),
      'POST /api/v1/vortex/rotate': () => this.parseBody(req).then(body => this.rotateVortex(body)),
      'POST /api/v1/vortex/pause': () => this.pauseVortex(),
      'POST /api/v1/vortex/resume': () => this.resumeVortex(),
    };
    
    const routeKey = `${method} ${path.replace(/\/\d+/g, '')}`; // Remove IDs for matching
    const handler = routes[`${method} ${path}`] || routes[routeKey];
    
    if (handler) {
      Promise.resolve(handler())
        .then(result => {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify(result));
        })
        .catch(err => {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: err.message }));
        });
    } else {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Not found' }));
    }
  }
  
  handleStatic(req, res, url) {
    let filePath = url.pathname === '/' ? '/index.html' : url.pathname;
    filePath = path.join(__dirname, '../web', filePath);
    
    const ext = path.extname(filePath);
    const mimeTypes = {
      '.html': 'text/html',
      '.js': 'application/javascript',
      '.css': 'text/css',
      '.json': 'application/json',
      '.png': 'image/png',
      '.jpg': 'image/jpeg'
    };
    
    fs.readFile(filePath, (err, data) => {
      if (err) {
        res.writeHead(404);
        res.end('Not found');
        return;
      }
      
      res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'text/plain' });
      res.end(data);
    });
  }
  
  handleWSCommand(ws, cmd) {
    switch (cmd.action) {
      case 'subscribe':
        // Client subscribes to events
        ws.subscriptions = cmd.events || [];
        break;
      case 'rotate':
        // Rotate vortex
        break;
      case 'pause':
        // Pause
        break;
      case 'snapshot':
        this.sendToClient(ws, {
          type: 'snapshot',
          payload: this.getSnapshot()
        });
        break;
    }
  }
  
  // API Handlers
  getStatus() {
    const stats = this.highway.getStats();
    return {
      online: true,
      cycle: this.vortex.cycle,
      rotation: this.vortex.rotation,
      agents: stats.agents,
      signals: stats.totalVehicles,
      seats: this.vortex.seats.size,
      peers: 0 // Would track in distributed mode
    };
  }
  
  getSignals(params) {
    const lane = params.get('lane');
    const limit = parseInt(params.get('limit')) || 10;
    
    let signals = [
      ...this.highway.lanes.critical,
      ...this.highway.lanes.standard,
      ...this.highway.lanes.background
    ].filter(v => v.alive);
    
    if (lane) {
      signals = this.highway.lanes[lane] || [];
    }
    
    return {
      signals: signals.slice(0, limit).map(v => ({
        id: v.id,
        emitter: v.emitter,
        lane: v.lane,
        intent: v.cargo.intent,
        intensity: v.intensity,
        birthTime: v.birthTime,
        decay: v.decay
      }))
    };
  }
  
  getAgents() {
    return {
      agents: Array.from(this.vortex.agents.values()).map(a => ({
        id: a.id,
        seat: a.seat?.id,
        capabilities: a.capabilities,
        lane: a.lane
      }))
    };
  }
  
  getInterference() {
    return {
      hotZones: this.highway.hotZones.slice(0, 10).map(z => ({
        intensity: z.intensity,
        match: z.match,
        vehicles: z.vehicles.map(v => v.emitter)
      }))
    };
  }
  
  getSnapshot() {
    return {
      timestamp: Date.now(),
      topology: this.vortex.snapshot(),
      signals: this.getSignals(new URLSearchParams()),
      status: this.getStatus()
    };
  }
  
  spawnAgent(body) {
    // Would integrate with agent factory
    return { success: true, agentId: `agent-${Date.now()}`, seatId: 'tbd' };
  }
  
  rotateVortex(body) {
    this.vortex.rotation += body.speed || 0.1;
    return { success: true, rotation: this.vortex.rotation };
  }
  
  pauseVortex() {
    return { paused: true };
  }
  
  resumeVortex() {
    return { resumed: true };
  }
  
  // Helpers
  parseBody(req) {
    return new Promise((resolve, reject) => {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try {
          resolve(body ? JSON.parse(body) : {});
        } catch (e) {
          reject(e);
        }
      });
    });
  }
  
  sendToClient(ws, data) {
    if (ws.readyState === 1) { // OPEN
      ws.send(JSON.stringify(data));
    }
  }
  
  broadcast(data) {
    const json = JSON.stringify(data);
    for (const client of this.clients) {
      if (client.readyState === 1) {
        client.send(json);
      }
    }
  }
  
  broadcastTopology() {
    this.broadcast({
      type: 'topology',
      payload: this.vortex.snapshot()
    });
  }
  
  broadcastSignals() {
    const signals = [
      ...this.highway.lanes.critical,
      ...this.highway.lanes.standard,
      ...this.highway.lanes.background
    ].filter(v => v.alive);
    
    this.broadcast({
      type: 'signals',
      payload: signals
    });
  }
  
  // Start
  start() {
    this.server.listen(this.port, () => {
      console.log(`🌐 HTTP Server: http://localhost:${this.port}`);
      console.log(`📡 WebSocket: ws://localhost:${this.wsPort}`);
    });
  }
  
  stop() {
    this.server.close();
    this.wss.close();
  }
}

module.exports = { HighwayServer };
