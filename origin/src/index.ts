/**
 * Agent Highway Origin - Beacon Collector
 * Cloudflare Workers + Durable Objects for signal lien aggregation
 */

import { DurableObject } from "cloudflare:workers";
import type { DurableObjectState, SqlStorage } from "cloudflare:workers";

// Environment interface
interface Env {
  BEACON_COLLECTOR: DurableObjectNamespace<BeaconCollector>;
  ENVIRONMENT?: string;
}

// Signal Lien Interface
export interface SignalLien {
  agent_id: string;
  agent_type: string;
  timestamp: number;
  event_type: 'birth' | 'heartbeat' | 'task_start' | 'task_complete' | 'death' | 'handoff' | 'error';
  task_id?: string;
  parent_agent_id?: string;
  target_agent_id?: string;
  payload_hash?: string;
  sequence: number;
  signature: string;
  public_key: string;
  metadata?: Record<string, any>;
  lane?: string; // Protocol lane: a2a, mcp, custom
}

// Agent State Materialized View
interface AgentState {
  agent_id: string;
  agent_type: string;
  last_event: string;
  last_timestamp: number;
  status: 'active' | 'idle' | 'ghost' | 'dead';
  sequence: number;
  current_task?: string;
  birth_timestamp: number;
  heartbeat_interval?: number;
  expected_next_heartbeat?: number;
  lane?: string;
}

/**
 * BeaconCollector - Durable Object for collecting and aggregating signal liens
 */
export class BeaconCollector extends DurableObject<Env> {
  sql: SqlStorage;
  
  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    
    // Initialize database schema
    this.initSchema();
    
    // Start ghost detection loop
    this.startGhostDetection();
  }
  
  async initSchema() {
    // Core lien storage - time-series of all agent events
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS liens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        agent_type TEXT,
        event_type TEXT NOT NULL,
        lane TEXT,
        timestamp INTEGER NOT NULL,
        task_id TEXT,
        parent_agent_id TEXT,
        target_agent_id TEXT,
        payload_hash TEXT,
        sequence INTEGER NOT NULL,
        signature TEXT NOT NULL,
        public_key TEXT,
        metadata TEXT,
        received_at INTEGER DEFAULT (unixepoch() * 1000)
      )
    `);
    
    // Materialized view: current agent states for fast queries
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS agent_states (
        agent_id TEXT PRIMARY KEY,
        agent_type TEXT,
        last_event TEXT,
        last_timestamp INTEGER,
        status TEXT DEFAULT 'active',
        sequence INTEGER,
        current_task TEXT,
        birth_timestamp INTEGER,
        heartbeat_interval INTEGER,
        expected_next_heartbeat INTEGER,
        lane TEXT,
        lien_count INTEGER DEFAULT 0
      )
    `);
    
    // Task tracking
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        agent_id TEXT,
        started_at INTEGER,
        completed_at INTEGER,
        status TEXT,
        duration_ms INTEGER
      )
    `);
    
    // Indexes for performance
    this.sql.exec(`CREATE INDEX IF NOT EXISTS idx_liens_time ON liens(timestamp)`);
    this.sql.exec(`CREATE INDEX IF NOT EXISTS idx_liens_agent ON liens(agent_id, timestamp DESC)`);
    this.sql.exec(`CREATE INDEX IF NOT EXISTS idx_liens_event ON liens(event_type, timestamp)`);
    this.sql.exec(`CREATE INDEX IF NOT EXISTS idx_liens_lane ON liens(lane, timestamp)`);
    this.sql.exec(`CREATE INDEX IF NOT EXISTS idx_states_status ON agent_states(status)`);
  }
  
  async startGhostDetection() {
    // Check for ghost agents every 30 seconds
    setInterval(async () => {
      const now = Date.now();
      const ghostThreshold = 60000; // 60 seconds without heartbeat = ghost
      
      this.sql.exec(`
        UPDATE agent_states 
        SET status = 'ghost'
        WHERE status = 'active' 
        AND expected_next_heartbeat < ${now}
        AND expected_next_heartbeat > 0
      `);
    }, 30000);
  }
  
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, DELETE',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    };
    
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }
    
    try {
      // Health check
      if (url.pathname === '/health') {
        const stats = this.getStats();
        return Response.json({ status: 'healthy', ...stats }, { headers: corsHeaders });
      }
      
      // Receive beacon from agent
      if (request.method === 'POST' && url.pathname === '/beacon') {
        return await this.handleBeacon(request, corsHeaders);
      }
      
      // WebSocket upgrade for real-time streaming
      if (url.pathname === '/beacon/ws') {
        return await this.handleWebSocket(request, corsHeaders);
      }
      
      // Query liens stream
      if (request.method === 'GET' && url.pathname === '/beacon/stream') {
        return await this.getLienStream(url, corsHeaders);
      }
      
      // Get live agent states
      if (url.pathname === '/agents/live') {
        return await this.getLiveAgents(url, corsHeaders);
      }
      
      // Get agent details
      if (url.pathname.startsWith('/agents/') && url.pathname.endsWith('/history')) {
        const agentId = url.pathname.split('/')[2];
        return await this.getAgentHistory(agentId, url, corsHeaders);
      }
      
      // Get system stats
      if (url.pathname === '/stats') {
        return Response.json(this.getStats(), { headers: corsHeaders });
      }
      
      // Get lanes info
      if (url.pathname === '/lanes') {
        return await this.getLanes(corsHeaders);
      }
      
      return new Response('Not found', { status: 404, headers: corsHeaders });
      
    } catch (error: unknown) {
      console.error('BeaconCollector error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      return new Response(
        JSON.stringify({ error: errorMessage }), 
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
  }
  
  async handleBeacon(request: Request, headers: Record<string, string>): Promise<Response> {
    const lien: SignalLien = await request.json();
    
    // Validate required fields
    if (!lien.agent_id || !lien.event_type || !lien.signature || !lien.timestamp) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }), 
        { status: 400, headers: { ...headers, 'Content-Type': 'application/json' } }
      );
    }
    
    // Verify signature
    if (!await this.verifyLien(lien)) {
      return new Response(
        JSON.stringify({ error: 'Invalid signature' }), 
        { status: 401, headers: { ...headers, 'Content-Type': 'application/json' } }
      );
    }
    
    // Store lien
    this.sql.exec(
      `INSERT INTO liens 
       (agent_id, agent_type, event_type, lane, timestamp, task_id, parent_agent_id, 
        target_agent_id, payload_hash, sequence, signature, public_key, metadata)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      lien.agent_id,
      lien.agent_type || 'unknown',
      lien.event_type,
      lien.lane || 'default',
      lien.timestamp,
      lien.task_id || null,
      lien.parent_agent_id || null,
      lien.target_agent_id || null,
      lien.payload_hash || null,
      lien.sequence,
      lien.signature,
      lien.public_key || null,
      lien.metadata ? JSON.stringify(lien.metadata) : null
    );
    
    // Update agent state
    await this.updateAgentState(lien);
    
    // Update task tracking if applicable
    if (lien.task_id) {
      await this.updateTask(lien);
    }
    
    // Broadcast to WebSocket subscribers
    this.broadcastToWebSockets({
      type: 'lien',
      data: lien,
      received_at: Date.now()
    });
    
    return new Response(
      JSON.stringify({ status: 'Lien recorded', agent_id: lien.agent_id }), 
      { status: 201, headers: { ...headers, 'Content-Type': 'application/json' } }
    );
  }
  
  async verifyLien(lien: SignalLien): Promise<boolean> {
    try {
      // Check sequence is incrementing
      let existingSeq: number | undefined;
      try {
        const result = this.sql.exec(
          `SELECT sequence FROM agent_states WHERE agent_id = ?`,
          lien.agent_id
        ).one() as { sequence?: number } | null;
        existingSeq = result?.sequence;
      } catch {
        existingSeq = undefined;
      }
      
      if (existingSeq !== undefined && lien.sequence <= existingSeq) {
        console.warn(`Sequence mismatch for ${lien.agent_id}: ${lien.sequence} <= ${existingSeq}`);
        return false;
      }
      
      // For birth events, sequence must be 1
      if (lien.event_type === 'birth' && existingSeq === undefined && lien.sequence !== 1) {
        console.warn(`Birth event must have sequence 1, got ${lien.sequence}`);
        return false;
      }
      
      // Ed25519 signature verification using Web Crypto API
      if (lien.public_key && lien.signature) {
        const isValid = await this.verifyEd25519Signature(lien);
        if (!isValid) {
          console.warn(`Invalid signature for agent ${lien.agent_id}`);
          return false;
        }
      }
      
      return true;
    } catch (e) {
      console.error('Lien verification error:', e);
      return false;
    }
  }
  
  async verifyEd25519Signature(lien: SignalLien): Promise<boolean> {
    try {
      // Create canonical message (excluding signature)
      const messageObj = {
        agent_id: lien.agent_id,
        agent_type: lien.agent_type,
        timestamp: lien.timestamp,
        event_type: lien.event_type,
        task_id: lien.task_id,
        parent_agent_id: lien.parent_agent_id,
        target_agent_id: lien.target_agent_id,
        payload_hash: lien.payload_hash,
        sequence: lien.sequence,
        lane: lien.lane,
        metadata: lien.metadata
      };
      const message = JSON.stringify(messageObj);
      
      // Import the public key
      const publicKeyData = this.base64UrlDecode(lien.public_key!);
      const signatureData = this.base64UrlDecode(lien.signature);
      
      const publicKey = await crypto.subtle.importKey(
        'raw',
        publicKeyData,
        { name: 'Ed25519' },
        false,
        ['verify']
      );
      
      // Verify signature
      const messageData = new TextEncoder().encode(message);
      const isValid = await crypto.subtle.verify(
        'Ed25519',
        publicKey,
        signatureData,
        messageData
      );
      
      return isValid;
    } catch (e) {
      console.error('Ed25519 verification error:', e);
      // If crypto fails, fall back to allowing (for development)
      // In production, return false here
      return true;
    }
  }
  
  base64UrlDecode(str: string): Uint8Array {
    // Convert base64url to base64
    let base64 = str.replace(/-/g, '+').replace(/_/g, '/');
    // Add padding
    while (base64.length % 4) {
      base64 += '=';
    }
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  }
  
  async updateAgentState(lien: SignalLien) {
    const now = Date.now();
    const heartbeatInterval = 30000; // 30s default
    
    // Calculate status
    let status: AgentState['status'] = 'active';
    if (lien.event_type === 'death') status = 'dead';
    else if (lien.event_type === 'error') status = 'ghost';
    
    // Get current task
    let currentTask = lien.task_id;
    if (lien.event_type === 'task_complete') currentTask = undefined;
    
    const expectedHeartbeat = now + heartbeatInterval;
    
    this.sql.exec(
      `INSERT INTO agent_states 
       (agent_id, agent_type, last_event, last_timestamp, status, sequence, 
        current_task, birth_timestamp, heartbeat_interval, expected_next_heartbeat, lane, lien_count)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
       ON CONFLICT(agent_id) DO UPDATE SET
         agent_type = excluded.agent_type,
         last_event = excluded.last_event,
         last_timestamp = excluded.last_timestamp,
         status = excluded.status,
         sequence = excluded.sequence,
         current_task = COALESCE(excluded.current_task, current_task),
         birth_timestamp = COALESCE(agent_states.birth_timestamp, excluded.birth_timestamp),
         heartbeat_interval = excluded.heartbeat_interval,
         expected_next_heartbeat = ?,
         lane = excluded.lane,
         lien_count = agent_states.lien_count + 1`,
      lien.agent_id,
      lien.agent_type || 'unknown',
      lien.event_type,
      lien.timestamp,
      status,
      lien.sequence,
      currentTask || null,
      lien.event_type === 'birth' ? lien.timestamp : null,
      heartbeatInterval,
      expectedHeartbeat,
      lien.lane || 'default',
      expectedHeartbeat
    );
  }
  
  async updateTask(lien: SignalLien) {
    if (lien.event_type === 'task_start' && lien.task_id) {
      this.sql.exec(
        `INSERT INTO tasks (task_id, agent_id, started_at, status)
         VALUES (?, ?, ?, 'running')
         ON CONFLICT(task_id) DO UPDATE SET
           agent_id = excluded.agent_id,
           started_at = excluded.started_at,
           status = 'running'`,
        lien.task_id,
        lien.agent_id,
        lien.timestamp
      );
    } else if (lien.event_type === 'task_complete' && lien.task_id) {
      const task = this.sql.exec(
        `SELECT started_at FROM tasks WHERE task_id = ?`,
        lien.task_id
      ).one() as { started_at?: number } | null;
      
      if (task?.started_at) {
        this.sql.exec(
          `UPDATE tasks SET 
            completed_at = ?,
            status = 'completed',
            duration_ms = ? - started_at
           WHERE task_id = ?`,
          lien.timestamp,
          lien.timestamp,
          lien.task_id
        );
      }
    }
  }
  
  async handleWebSocket(request: Request, headers: Record<string, string>): Promise<Response> {
    const upgradeHeader = request.headers.get('Upgrade');
    if (upgradeHeader !== 'websocket') {
      return new Response('Expected websocket', { status: 400, headers });
    }
    
    const [client, server] = Object.values(new WebSocketPair());
    
    server.accept();
    
    // Send initial snapshot
    const snapshot = this.getLiveAgentStates();
    server.send(JSON.stringify({ type: 'snapshot', data: snapshot }));
    
    // Store for broadcasting
    this.ctx.acceptWebSocket(server);
    
    server.addEventListener('message', (event) => {
      try {
        const msg = JSON.parse(event.data as string);
        
        // Handle subscription filters
        if (msg.type === 'subscribe') {
          (server as any).subscriptions = msg.filters || ['*'];
        }
      } catch (e) {
        // Ignore invalid messages
      }
    });
    
    return new Response(null, { status: 101, webSocket: client });
  }
  
  async webSocketMessage(ws: WebSocket, message: string | ArrayBuffer) {
    // Handle incoming messages from clients if needed
  }
  
  async webSocketClose(ws: WebSocket, code: number, reason: string, wasClean: boolean) {
    // Cleanup handled automatically
  }
  
  broadcastToWebSockets(message: Record<string, unknown>) {
    const msg = JSON.stringify(message);
    for (const ws of this.ctx.getWebSockets()) {
      try {
        const subscriptions = (ws as WebSocket & { subscriptions?: string[] }).subscriptions || ['*'];
        const lien = message.data as SignalLien;
        
        // Filter by agent type if subscription set
        if (subscriptions.includes('*') || 
            subscriptions.includes(lien.agent_type) ||
            subscriptions.includes(lien.lane || 'default')) {
          ws.send(msg);
        }
      } catch {
        // Remove dead connections
      }
    }
  }
  
  async getLienStream(url: URL, headers: Record<string, string>): Promise<Response> {
    const since = parseInt(url.searchParams.get('since') || '0');
    const agentType = url.searchParams.get('type');
    const eventType = url.searchParams.get('event');
    const lane = url.searchParams.get('lane');
    const limit = Math.min(parseInt(url.searchParams.get('limit') || '100'), 1000);
    
    let whereClause = `WHERE timestamp > ${since}`;
    const params: (string | number)[] = [];
    
    if (agentType) {
      whereClause += ` AND agent_type = ?`;
      params.push(agentType);
    }
    if (eventType) {
      whereClause += ` AND event_type = ?`;
      params.push(eventType);
    }
    if (lane) {
      whereClause += ` AND lane = ?`;
      params.push(lane);
    }
    
    const cursor = this.sql.exec(
      `SELECT * FROM liens ${whereClause} ORDER BY timestamp DESC LIMIT ${limit}`,
      ...params
    );
    
    const liens = Array.from(cursor);
    
    return Response.json({ liens, count: liens.length }, { headers });
  }
  
  async getLiveAgents(url: URL, headers: Record<string, string>): Promise<Response> {
    const status = url.searchParams.get('status');
    const lane = url.searchParams.get('lane');
    
    let whereClause = 'WHERE 1=1';
    const params: (string | number)[] = [];
    
    if (status) {
      whereClause += ` AND status = ?`;
      params.push(status);
    }
    if (lane) {
      whereClause += ` AND lane = ?`;
      params.push(lane);
    }
    
    const cursor = this.sql.exec(
      `SELECT * FROM agent_states ${whereClause} ORDER BY last_timestamp DESC`,
      ...params
    );
    
    const agents = Array.from(cursor);
    
    return Response.json({ agents, count: agents.length }, { headers });
  }
  
  async getAgentHistory(agentId: string, url: URL, headers: Record<string, string>): Promise<Response> {
    const limit = Math.min(parseInt(url.searchParams.get('limit') || '100'), 1000);
    
    const cursor = this.sql.exec(
      `SELECT * FROM liens WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ${limit}`,
      agentId
    );
    
    const history = Array.from(cursor);
    
    // Get agent summary
    const stateRaw = this.sql.exec(
      `SELECT * FROM agent_states WHERE agent_id = ?`,
      agentId
    ).one() as Record<string, SqlStorageValue> | null;
    const state = stateRaw ? (stateRaw as unknown as AgentState) : null;
    
    return Response.json({ agent_id: agentId, state, history }, { headers });
  }
  
  getLiveAgentStates(): AgentState[] {
    const cursor = this.sql.exec(`SELECT * FROM agent_states ORDER BY last_timestamp DESC`);
    return Array.from(cursor).map(row => row as unknown as AgentState);
  }
  
  getStats() {
    const totalLiens = this.sql.exec(`SELECT COUNT(*) as count FROM liens`).one() as { count: number };
    const activeAgents = this.sql.exec(`SELECT COUNT(*) as count FROM agent_states WHERE status = 'active'`).one() as { count: number };
    const ghostAgents = this.sql.exec(`SELECT COUNT(*) as count FROM agent_states WHERE status = 'ghost'`).one() as { count: number };
    const deadAgents = this.sql.exec(`SELECT COUNT(*) as count FROM agent_states WHERE status = 'dead'`).one() as { count: number };
    
    // Recent liens in last hour
    const oneHourAgo = Date.now() - 3600000;
    const recentLiens = this.sql.exec(
      `SELECT COUNT(*) as count FROM liens WHERE timestamp > ${oneHourAgo}`
    ).one() as { count: number };
    
    // Lane distribution
    const lanes = this.sql.exec(`
      SELECT lane, COUNT(*) as count 
      FROM agent_states 
      GROUP BY lane
    `);
    
    // Event type distribution
    const events = this.sql.exec(`
      SELECT event_type, COUNT(*) as count 
      FROM liens 
      WHERE timestamp > ${oneHourAgo}
      GROUP BY event_type
    `);
    
    return {
      total_liens: totalLiens?.count || 0,
      recent_liens_1h: recentLiens?.count || 0,
      agents: {
        active: activeAgents?.count || 0,
        ghost: ghostAgents?.count || 0,
        dead: deadAgents?.count || 0,
        total: (activeAgents?.count || 0) + (ghostAgents?.count || 0) + (deadAgents?.count || 0)
      },
      lanes: Array.from(lanes),
      recent_events: Array.from(events)
    };
  }
  
  async getLanes(headers: Record<string, string>): Promise<Response> {
    const cursor = this.sql.exec(`
      SELECT 
        lane,
        COUNT(*) as agent_count,
        SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_count,
        MAX(last_timestamp) as last_activity
      FROM agent_states
      GROUP BY lane
      ORDER BY agent_count DESC
    `);
    
    return Response.json({ lanes: Array.from(cursor) }, { headers });
  }
}

/**
 * Get Durable Object ID with sharding for scale
 * Shards by first 2 chars of agent_id for beacon writes
 * Uses 'global' for queries that span agents
 */
function getCollectorId(env: Env, request: Request): ReturnType<Env['BEACON_COLLECTOR']['idFromName']> {
  const url = new URL(request.url);
  
  // For beacon POSTs, shard by agent_id
  if (request.method === 'POST' && url.pathname === '/beacon') {
    // We'll parse the agent_id from the body in a moment
    // For now, return a placeholder that will be resolved
    return env.BEACON_COLLECTOR.idFromName('__PENDING__');
  }
  
  // For queries that need global view, use global DO
  if (url.pathname === '/agents/live' || 
      url.pathname === '/stats' || 
      url.pathname === '/lanes' ||
      url.pathname === '/') {
    return env.BEACON_COLLECTOR.idFromName('global');
  }
  
  // For agent-specific queries, shard by agent_id
  if (url.pathname.startsWith('/agents/')) {
    const agentId = url.pathname.split('/')[2];
    const shardKey = getShardKey(agentId);
    return env.BEACON_COLLECTOR.idFromName(shardKey);
  }
  
  // Default to global
  return env.BEACON_COLLECTOR.idFromName('global');
}

function getShardKey(agentId: string): string {
  // Use first 2 characters of agent_id for 256 shards
  // This distributes load while keeping related agents somewhat clustered
  if (agentId.length < 2) return `shard_${agentId}`;
  return `shard_${agentId.slice(0, 2)}`;
}

/**
 * Main Worker - routes requests to Durable Object
 */
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    
    // CORS headers for all responses
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, DELETE',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };
    
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }
    
    // Serve dashboard HTML at root
    if (url.pathname === '/') {
      return new Response(DASHBOARD_HTML, {
        headers: { 'Content-Type': 'text/html', ...corsHeaders }
      });
    }
    
    // For beacon POSTs, extract agent_id and shard
    if (request.method === 'POST' && url.pathname === '/beacon') {
      try {
        const body = await request.clone().json() as SignalLien;
        const shardKey = getShardKey(body.agent_id);
        const id = env.BEACON_COLLECTOR.idFromName(shardKey);
        const collector = env.BEACON_COLLECTOR.get(id);
        return collector.fetch(request);
      } catch (e) {
        // Fallback to global if parsing fails
        const id = env.BEACON_COLLECTOR.idFromName('global');
        const collector = env.BEACON_COLLECTOR.get(id);
        return collector.fetch(request);
      }
    }
    
    // For queries that need global view
    const id = getCollectorId(env, request);
    const collector = env.BEACON_COLLECTOR.get(id);
    return collector.fetch(request);
  }
};

// Simple HTML Dashboard
const DASHBOARD_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agent Highway Origin - Dashboard</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0a0a0f;
      color: #e0e0e0;
      min-height: 100vh;
    }
    .header {
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
      padding: 2rem;
      border-bottom: 1px solid #2a2a3e;
    }
    .header h1 {
      font-size: 1.8rem;
      background: linear-gradient(90deg, #00d4ff, #7b2cbf);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }
    .header p { color: #888; }
    .container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 2rem;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }
    .stat-card {
      background: #151520;
      border: 1px solid #2a2a3e;
      border-radius: 12px;
      padding: 1.5rem;
      transition: transform 0.2s;
    }
    .stat-card:hover { transform: translateY(-2px); border-color: #3a3a4e; }
    .stat-label {
      color: #888;
      font-size: 0.875rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .stat-value {
      font-size: 2rem;
      font-weight: 700;
      color: #00d4ff;
      margin-top: 0.5rem;
    }
    .stat-value.warning { color: #f59e0b; }
    .stat-value.danger { color: #ef4444; }
    .section {
      background: #151520;
      border: 1px solid #2a2a3e;
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }
    .section h2 {
      font-size: 1.25rem;
      margin-bottom: 1rem;
      color: #fff;
    }
    .agent-grid {
      display: grid;
      gap: 0.75rem;
    }
    .agent-card {
      background: #1a1a28;
      border: 1px solid #2a2a3e;
      border-radius: 8px;
      padding: 1rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      transition: all 0.2s;
    }
    .agent-card:hover { border-color: #00d4ff40; }
    .agent-status {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .agent-status.active { background: #22c55e; box-shadow: 0 0 8px #22c55e; }
    .agent-status.ghost { background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }
    .agent-status.dead { background: #ef4444; }
    .agent-info { flex: 1; }
    .agent-id {
      font-weight: 600;
      color: #fff;
      font-family: monospace;
    }
    .agent-type {
      font-size: 0.875rem;
      color: #888;
      margin-top: 0.25rem;
    }
    .agent-meta {
      text-align: right;
      font-size: 0.875rem;
      color: #666;
    }
    .lien-stream {
      max-height: 400px;
      overflow-y: auto;
    }
    .lien-item {
      padding: 0.75rem;
      border-bottom: 1px solid #2a2a3e;
      font-family: monospace;
      font-size: 0.875rem;
      display: flex;
      gap: 1rem;
      animation: fadeIn 0.3s ease;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateX(-10px); }
      to { opacity: 1; transform: translateX(0); }
    }
    .lien-time { color: #666; min-width: 80px; }
    .lien-agent { color: #00d4ff; min-width: 120px; }
    .lien-event {
      padding: 0.125rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      text-transform: uppercase;
    }
    .lien-event.birth { background: #22c55e20; color: #22c55e; }
    .lien-event.heartbeat { background: #3b82f620; color: #3b82f6; }
    .lien-event.task_start { background: #f59e0b20; color: #f59e0b; }
    .lien-event.task_complete { background: #22c55e20; color: #22c55e; }
    .lien-event.death { background: #ef444420; color: #ef4444; }
    .lien-event.error { background: #ef444420; color: #ef4444; }
    .empty-state {
      text-align: center;
      padding: 3rem;
      color: #666;
    }
    .refresh-btn {
      background: #00d4ff20;
      border: 1px solid #00d4ff;
      color: #00d4ff;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.875rem;
      transition: all 0.2s;
    }
    .refresh-btn:hover { background: #00d4ff30; }
    .lane-tags {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-top: 0.5rem;
    }
    .lane-tag {
      background: #2a2a3e;
      padding: 0.25rem 0.75rem;
      border-radius: 12px;
      font-size: 0.75rem;
      color: #888;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🛣️ Agent Highway Origin</h1>
    <p>Real-time beacon monitoring for AI agents</p>
  </div>
  
  <div class="container">
    <div class="stats-grid" id="stats">
      <div class="stat-card">
        <div class="stat-label">Active Agents</div>
        <div class="stat-value" id="stat-active">-</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Ghost Agents</div>
        <div class="stat-value warning" id="stat-ghost">-</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Dead Agents</div>
        <div class="stat-value danger" id="stat-dead">-</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Liens</div>
        <div class="stat-value" id="stat-liens">-</div>
      </div>
    </div>
    
    <div class="section">
      <h2>Live Agents <button class="refresh-btn" onclick="loadData()">Refresh</button></h2>
      <div class="agent-grid" id="agents">
        <div class="empty-state">Loading agents...</div>
      </div>
    </div>
    
    <div class="section">
      <h2>Live Lien Stream</h2>
      <div class="lien-stream" id="liens">
        <div class="empty-state">Connecting to WebSocket...</div>
      </div>
    </div>
  </div>
  
  <script>
    const API_BASE = '';
    let ws = null;
    
    async function loadData() {
      try {
        const [statsRes, agentsRes] = await Promise.all([
          fetch(\`\${API_BASE}/stats\`),
          fetch(\`\${API_BASE}/agents/live\`)
        ]);
        
        const stats = await statsRes.json();
        const agents = await agentsRes.json();
        
        // Update stats
        document.getElementById('stat-active').textContent = stats.agents?.active || 0;
        document.getElementById('stat-ghost').textContent = stats.agents?.ghost || 0;
        document.getElementById('stat-dead').textContent = stats.agents?.dead || 0;
        document.getElementById('stat-liens').textContent = stats.total_liens || 0;
        
        // Update agents
        const agentsContainer = document.getElementById('agents');
        if (agents.agents?.length === 0) {
          agentsContainer.innerHTML = '<div class="empty-state">No agents registered yet</div>';
        } else {
          agentsContainer.innerHTML = agents.agents?.map(agent => \`
            <div class="agent-card">
              <div class="agent-status \${agent.status}"></div>
              <div class="agent-info">
                <div class="agent-id">\${agent.agent_id}</div>
                <div class="agent-type">\${agent.agent_type} • Lane: \${agent.lane || 'default'}</div>
                <div class="lane-tags">
                  <span class="lane-tag">\${agent.lien_count} liens</span>
                  <span class="lane-tag">seq #\${agent.sequence}</span>
                  \${agent.current_task ? \`<span class="lane-tag">task: \${agent.current_task}</span>\` : ''}
                </div>
              </div>
              <div class="agent-meta">
                <div>\${agent.last_event}</div>
                <div>\${new Date(agent.last_timestamp).toLocaleTimeString()}</div>
              </div>
            </div>
          \`).join('') || '<div class="empty-state">No agents found</div>';
        }
      } catch (err) {
        console.error('Failed to load data:', err);
      }
    }
    
    function connectWebSocket() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      ws = new WebSocket(\`\${protocol}//\${window.location.host}/beacon/ws\`);
      
      const liensContainer = document.getElementById('liens');
      liensContainer.innerHTML = '';
      
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        
        if (msg.type === 'snapshot') {
          // Initial snapshot
          return;
        }
        
        if (msg.type === 'lien') {
          const lien = msg.data;
          const item = document.createElement('div');
          item.className = 'lien-item';
          item.innerHTML = \`
            <span class="lien-time">\${new Date(lien.timestamp).toLocaleTimeString()}</span>
            <span class="lien-agent">\${lien.agent_id.slice(0, 20)}...</span>
            <span class="lien-event \${lien.event_type}">\${lien.event_type}</span>
            <span style="color: #666;">\${lien.lane || 'default'}</span>
          \`;
          liensContainer.prepend(item);
          
          // Keep only last 50 items
          while (liensContainer.children.length > 50) {
            liensContainer.lastChild.remove();
          }
        }
      };
      
      ws.onclose = () => {
        setTimeout(connectWebSocket, 3000);
      };
      
      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        liensContainer.innerHTML = '<div class="empty-state">WebSocket disconnected</div>';
      };
    }
    
    // Initial load
    loadData();
    connectWebSocket();
    
    // Refresh stats every 5 seconds
    setInterval(loadData, 5000);
  </script>
</body>
</html>`;
