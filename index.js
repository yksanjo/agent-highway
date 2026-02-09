#!/usr/bin/env node
/**
 * AgentHighway - Main Entry
 * 
 * Usage:
 *   node index.js              # Run with scanner
 *   node index.js --headless   # Run without scanner
 */

const { Highway } = require('./src/highway');
const { Scanner } = require('./src/scanner');
const { createSwarm } = require('./src/swarm');

const args = process.argv.slice(2);
const headless = args.includes('--headless');

console.log('╔═══════════════════════════════════════════════════════╗');
console.log('║                                                       ║');
console.log('║           🛣️  AGENTHIGHWAY v1.0                       ║');
console.log('║                                                       ║');
console.log('║     A Nervous System for AI Swarms                   ║');
console.log('║                                                       ║');
console.log('║     NO LOGS • NO BACKEND • JUST SIGNALS              ║');
console.log('║                                                       ║');
console.log('╚═══════════════════════════════════════════════════════╝');
console.log();

// Create highway
const highway = new Highway({ tickRate: 100 });

// Create scanner (unless headless)
let scanner;
if (!headless) {
  scanner = new Scanner(highway);
}

// Create swarm
console.log('🐝 Initializing swarm...');
const agents = createSwarm(highway);
console.log(`   ${agents.length} agents registered`);
console.log();

// Start
highway.start();

if (scanner) {
  scanner.start();
}

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n');
  console.log('🛑 Shutting down...');
  
  if (scanner) scanner.stop();
  highway.stop();
  
  console.log('✅ Highway closed. No logs saved.');
  process.exit(0);
});

// If headless, just show stats periodically
if (headless) {
  setInterval(() => {
    const stats = highway.getStats();
    console.log(
      `[${stats.cycle}] ` +
      `Agents: ${stats.agents} | ` +
      `Signals: C${stats.vehicles.critical}/S${stats.vehicles.standard}/B${stats.vehicles.background} | ` +
      `HotZones: ${stats.hotZones.length}`
    );
  }, 1000);
}
