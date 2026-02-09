#!/usr/bin/env node
/**
 * AgentHighway VORTEX Edition
 * 
 * Full system with:
 * - Topological vortex
 * - Advanced agents
 * - Distributed transport
 * - Retro web visualization
 * - Community API
 */

const { Highway, VectorOps } = require('./src/highway');
const { Vortex } = require('./src/topology/vortex');
const { Scanner } = require('./src/scanner');
const { HighwayServer } = require('./src/server');
const {
  SentinelAgent,
  ArchitectAgent,
  ArtisanAgent,
  CatalystAgent,
  NexusAgent,
  SeedAgent,
  PhantomAgent
} = require('./src/agents');

// Parse args
const args = process.argv.slice(2);
const webMode = args.includes('--web');
const headless = args.includes('--headless');

console.log('╔═══════════════════════════════════════════════════════════════╗');
console.log('║                                                               ║');
console.log('║     🌌 AGENTHIGHWAY // VORTEX EDITION v2.0                    ║');
console.log('║                                                               ║');
console.log('║     Topological Compute Swarm                                 ║');
console.log('║                                                               ║');
console.log('║     NO LOGS • NO BACKEND • SEATED AGENTS • SIGNAL FLOw        ║');
console.log('║                                                               ║');
console.log('╚═══════════════════════════════════════════════════════════════╝');
console.log();

// Create systems
const highway = new Highway({ tickRate: 100 });
const vortex = new Vortex();

// Connect highway to vortex
// When agents emit, their signals flow through vortex topology
const originalEmit = highway.emit.bind(highway);
highway.emit = function(vehicleConfig) {
  // In vortex mode, add topology info
  const agent = highway.agents.get(vehicleConfig.emitter);
  if (agent && agent.seat) {
    // Propagation time affects signal velocity
    vehicleConfig.velocity = agent.seat.gravityWell * 2;
  }
  return originalEmit(vehicleConfig);
};

// Scanner
let scanner;
if (!headless) {
  scanner = new Scanner(highway);
}

// Create advanced swarm
console.log('🐝 Initializing VORTEX SWARM...');
const agents = [];

// Core infrastructure
const monitor = new SentinelAgent({ id: 'sentinel-alpha', watchList: ['cpu', 'memory', 'auth'] });
agents.push(monitor);

const architect = new ArchitectAgent({ domain: 'distributed-systems' });
agents.push(architect);

const nexus = new NexusAgent({ id: 'nexus-hub-1' });
agents.push(nexus);

// Artisans
agents.push(new ArtisanAgent({ specialty: 'code' }));
agents.push(new ArtisanAgent({ specialty: 'database' }));
agents.push(new ArtisanAgent({ specialty: 'security' }));

// Researchers
agents.push(new SeedAgent({ factory: (type) => console.log(`  🌱 Factory would spawn: ${type}`) }));
agents.push(new CatalystAgent());
agents.push(new PhantomAgent({ targetFocus: VectorOps.fromString('anomaly') }));

// Seat agents in vortex
console.log();
console.log('💺 Seating agents in vortex...');
for (const agent of agents) {
  // Determine tier based on capabilities
  let preferredTier = 'outer';
  if (agent.capabilities.includes('monitoring')) preferredTier = 'core';
  else if (agent.capabilities.includes('implementation')) preferredTier = 'inner';
  else if (agent.capabilities.includes('catalysis')) preferredTier = 'inner';
  
  const seat = vortex.seatAgent(agent, preferredTier);
  
  // Register on highway
  if (seat) {
    highway.register(agent);
  }
}

console.log();
console.log(`   ${agents.length} agents seated across ${vortex.seats.size} seats`);
console.log(`   Tiers: Core=${vortex.tiers.core.seats}, Inner=${vortex.tiers.inner.seats}, Outer=${vortex.tiers.outer.seats}, Edge=${vortex.tiers.edge.seats}`);

// Start systems
highway.start();

if (scanner) {
  scanner.start();
}

// Web server
let server;
if (webMode) {
  server = new HighwayServer(highway, vortex, { port: 9001, wsPort: 9000 });
  server.start();
  console.log();
  console.log('🌐 Web Monitor: http://localhost:9001');
}

// Vortex rotation
const vortexInterval = setInterval(() => {
  vortex.rotate();
}, 100);

// Stats logging (if headless)
if (headless) {
  setInterval(() => {
    const stats = highway.getStats();
    const vortexStats = vortex.snapshot();
    console.log(
      `[${stats.cycle.toString().padStart(4)}] ` +
      `Seated:${vortexStats.agents.length.toString().padStart(2)} | ` +
      `⚡${stats.vehicles.critical.toString().padStart(2)} ` +
      `🔥${stats.vehicles.standard.toString().padStart(2)} ` +
      `💨${stats.vehicles.background.toString().padStart(2)} | ` +
      `🌀${(vortexStats.rotation % 360).toFixed(1)}° | ` +
      `🔥${stats.hotZones.length} zones`
    );
  }, 1000);
}

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n');
  console.log('🛑 Shutting down VORTEX...');
  
  clearInterval(vortexInterval);
  
  if (scanner) scanner.stop();
  if (server) server.stop();
  highway.stop();
  
  console.log('✅ Vortex collapsed. No traces remain.');
  process.exit(0);
});

// Help text
console.log();
console.log('Commands:');
console.log('  --web       Start with web monitor');
console.log('  --headless  Run without scanner UI');
console.log();
