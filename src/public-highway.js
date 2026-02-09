/**
 * Public Highway Server
 * 
 * Multi-tenant, rate-limited, auto-scaling highway for public use.
 * Anyone can connect without running their own server.
 */

const { Highway } = require('./highway');
const { Vortex } = require('./topology/vortex');
const { HighwayServer } = require('./server');

class PublicHighway {
  constructor(options = {}) {
    this.options = {
      maxAgents: options.maxAgents || 1000,
      maxAgentsPerIP: options.maxAgentsPerIP || 5,
      rateLimitWindow: options.rateLimitWindow || 60000, // 1 minute
      maxSignalsPerWindow: options.maxSignalsPerWindow || 100,
      enableRegistration: options.enableRegistration !== false,
      requireInvitation: options.requireInvitation || false,
      ...options
    };
    
    // Core systems
    this.highway = new Highway({ tickRate: 100 });
    this.vortex = new Vortex();
    this.server = null;
    
    // Multi-tenant tracking
    this.agentsByIP = new Map();
    this.rateLimits = new Map();
    this.bannedIPs = new Set();
    
    // Stats
    this.stats = {
      totalConnections: 0,
      activeAgents: 0,
      signalsEmitted: 0,
      startTime: Date.now()
    };
  }
  
  /**
   * Initialize and start the public highway
   */
  start() {
    console.log('╔═══════════════════════════════════════════════════════════════╗');
    console.log('║                                                               ║');
    console.log('║     🌐 PUBLIC AGENTHIGHWAY                                    ║');
    console.log('║                                                               ║');
    console.log('║     Multi-tenant • Rate-limited • Auto-scaling               ║');
    console.log('║                                                               ║');
    console.log('╚═══════════════════════════════════════════════════════════════╝');
    console.log();
    
    // Setup middleware
    this.setupRateLimiting();
    this.setupMultiTenancy();
    
    // Start core systems
    this.highway.start();
    
    // Start server with public config
    this.server = new HighwayServer(this.highway, this.vortex, {
      port: this.options.port || 9001,
      wsPort: this.options.wsPort || 9000,
      public: true
    });
    
    // Add public-specific middleware
    this.setupPublicMiddleware();
    
    this.server.start();
    
    // Start stats reporting
    this.startStatsReporting();
    
    console.log();
    console.log('🌐 Public highway is LIVE');
    console.log(`   WebSocket: ws://${this.getPublicHost()}:9000`);
    console.log(`   HTTP API: http://${this.getPublicHost()}:9001`);
    console.log(`   Web Monitor: http://${this.getPublicHost()}:9001`);
    console.log();
    console.log('   Anyone can connect. No approval needed.');
    console.log();
  }
  
  /**
   * Setup rate limiting per IP/agent
   */
  setupRateLimiting() {
    const checkRateLimit = (ip, agentId) => {
      // Check if IP is banned
      if (this.bannedIPs.has(ip)) {
        return { allowed: false, reason: 'IP banned' };
      }
      
      // Get or create rate limit tracker
      if (!this.rateLimits.has(ip)) {
        this.rateLimits.set(ip, {
          count: 0,
          windowStart: Date.now(),
          agents: new Set()
        });
      }
      
      const limit = this.rateLimits.get(ip);
      const now = Date.now();
      
      // Reset window if expired
      if (now - limit.windowStart > this.options.rateLimitWindow) {
        limit.count = 0;
        limit.windowStart = now;
      }
      
      // Check rate limit
      if (limit.count >= this.options.maxSignalsPerWindow) {
        return { 
          allowed: false, 
          reason: 'Rate limit exceeded',
          retryAfter: this.options.rateLimitWindow - (now - limit.windowStart)
        };
      }
      
      // Track agent
      if (agentId) {
        limit.agents.add(agentId);
      }
      
      limit.count++;
      return { allowed: true };
    };
    
    // Hook into highway emit
    const originalEmit = this.highway.emit.bind(this.highway);
    this.highway.emit = (config) => {
      const ip = config._meta?.ip || 'unknown';
      const agentId = config.emitter;
      
      const result = checkRateLimit(ip, agentId);
      if (!result.allowed) {
        console.log(`⚠️  Rate limit: ${ip} - ${result.reason}`);
        return null;
      }
      
      this.stats.signalsEmitted++;
      return originalEmit(config);
    };
  }
  
  /**
   * Setup multi-tenant agent tracking
   */
  setupMultiTenancy() {
    // Track agents by IP
    this.highway.onAgentConnect = (agent, ip) => {
      if (!this.agentsByIP.has(ip)) {
        this.agentsByIP.set(ip, new Set());
      }
      
      const agents = this.agentsByIP.get(ip);
      
      // Check per-IP limit
      if (agents.size >= this.options.maxAgentsPerIP) {
        console.log(`⚠️  Max agents reached for ${ip}`);
        return false;
      }
      
      agents.add(agent.id);
      this.stats.totalConnections++;
      this.stats.activeAgents++;
      
      return true;
    };
    
    this.highway.onAgentDisconnect = (agent, ip) => {
      const agents = this.agentsByIP.get(ip);
      if (agents) {
        agents.delete(agent.id);
        this.stats.activeAgents--;
      }
    };
  }
  
  /**
   * Setup public-specific middleware
   */
  setupPublicMiddleware() {
    // Add public endpoints
    this.server.app.get('/api/v1/public/stats', (req, res) => {
      res.json({
        ...this.stats,
        uptime: Date.now() - this.stats.startTime,
        uniqueIPs: this.agentsByIP.size,
        rateLimitedIPs: this.rateLimits.size
      });
    });
    
    // Health check for load balancers
    this.server.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        agents: this.stats.activeAgents,
        capacity: this.options.maxAgents,
        utilization: this.stats.activeAgents / this.options.maxAgents
      });
    });
  }
  
  /**
   * Get public host
   */
  getPublicHost() {
    return this.options.publicHost || 
           process.env.PUBLIC_HOST || 
           process.env.RAILWAY_STATIC_URL ||
           process.env.RENDER_EXTERNAL_HOSTNAME ||
           process.env.FLY_ALLOC_ID ? 'localhost' : 'localhost';
  }
  
  /**
   * Report stats periodically
   */
  startStatsReporting() {
    setInterval(() => {
      console.log(`\n📊 Public Highway Stats:`);
      console.log(`   Active Agents: ${this.stats.activeAgents}/${this.options.maxAgents}`);
      console.log(`   Unique IPs: ${this.agentsByIP.size}`);
      console.log(`   Total Signals: ${this.stats.signalsEmitted}`);
      console.log(`   Uptime: ${Math.floor((Date.now() - this.stats.startTime) / 1000)}s`);
    }, 60000);
  }
  
  /**
   * Ban an IP
   */
  banIP(ip, reason) {
    this.bannedIPs.add(ip);
    console.log(`🚫 Banned IP: ${ip} - ${reason}`);
  }
  
  /**
   * Unban an IP
   */
  unbanIP(ip) {
    this.bannedIPs.delete(ip);
    console.log(`✅ Unbanned IP: ${ip}`);
  }
}

module.exports = { PublicHighway };
