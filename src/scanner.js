/**
 * AgentHighway Scanner
 * Real-time visualization and diagnostics
 * 
 * NO LOGGING - Just live observation
 */

const readline = require('readline');

class Scanner {
  constructor(highway) {
    this.highway = highway;
    this.running = false;
    this.refreshRate = 100;
    this.history = []; // Circular buffer (last 100 frames)
    
    // Attach to highway
    highway.onTick = (stats) => this.onHighwayTick(stats);
  }
  
  onHighwayTick(stats) {
    this.history.push({
      time: Date.now(),
      ...stats
    });
    
    // Keep only last 100 frames (~10 seconds at 100ms)
    if (this.history.length > 100) {
      this.history.shift();
    }
  }
  
  /**
   * Generate ASCII heatmap of signal field
   */
  renderHeatmap() {
    const lanes = ['critical', 'standard', 'background'];
    const width = 40;
    const lines = [];
    
    lines.push('┌' + '─'.repeat(width + 2) + '┐');
    lines.push('│' + ' '.repeat((width - 12) / 2) + 'SIGNAL FIELD' + ' '.repeat((width - 12) / 2) + '│');
    lines.push('├' + '─'.repeat(width + 2) + '┤');
    
    for (const lane of lanes) {
      const vehicles = this.highway.lanes[lane].filter(v => v.alive);
      const intensity = vehicles.reduce((sum, v) => sum + v.intensity, 0);
      const barLength = Math.min(width, Math.floor(intensity * width / 5));
      
      const symbols = {
        critical: '⚡',
        standard: '🔥',
        background: '💨'
      };
      
      const bar = symbols[lane].repeat(barLength) + '░'.repeat(width - barLength);
      const count = vehicles.length.toString().padStart(3);
      
      lines.push(`│ ${lane.slice(0, 3).toUpperCase()} ${bar} ${count} │`);
    }
    
    lines.push('└' + '─'.repeat(width + 2) + '┘');
    return lines.join('\n');
  }
  
  /**
   * Render hot zones
   */
  renderHotZones() {
    const zones = this.highway.hotZones.slice(0, 5);
    const lines = [];
    
    lines.push('╔══════════════ HOT ZONES ══════════════╗');
    
    if (zones.length === 0) {
      lines.push('║  (no interference patterns detected)  ║');
    } else {
      for (let i = 0; i < 5; i++) {
        const zone = zones[i];
        if (zone) {
          const intensity = '█'.repeat(Math.floor(zone.intensity * 10));
          const match = Math.floor(zone.match * 100);
          lines.push(`║ 🔥 ${intensity.padEnd(10)} ${match}% │ +${zone.intensity.toFixed(1)} ║`);
        } else {
          lines.push(`║ ${' '.repeat(37)} ║`);
        }
      }
    }
    
    lines.push('╚═══════════════════════════════════════╝');
    return lines.join('\n');
  }
  
  /**
   * Render agent status
   */
  renderAgents() {
    const lines = [];
    const agents = Array.from(this.highway.agents.values());
    
    lines.push('┌────────────── AGENTS ─────────────────┐');
    
    for (const agent of agents.slice(0, 8)) {
      const signals = agent.sense(0.3, 1);
      const activity = signals.length > 0 ? '⚡' : '○';
      const name = agent.id.slice(0, 8).padEnd(8);
      const lane = agent.lane.slice(0, 4).padEnd(4);
      lines.push(`│ ${activity} ${name} │ ${lane} │ ${agent.capabilities[0] || 'none'} │`);
    }
    
    if (agents.length > 8) {
      lines.push(`│ ... and ${agents.length - 8} more agents      │`);
    }
    
    lines.push('└───────────────────────────────────────┘');
    return lines.join('\n');
  }
  
  /**
   * Render full dashboard
   */
  render() {
    const stats = this.highway.getStats();
    const lines = [];
    
    // Header
    lines.push('');
    lines.push('╔══════════════════════════════════════════════════════════╗');
    lines.push('║           🛣️  AGENTHIGHWAY SCANNER v1.0                   ║');
    lines.push('║              ─── NO LOGS • LIVE ONLY ───                 ║');
    lines.push('╠══════════════════════════════════════════════════════════╣');
    lines.push(`║  Cycle: ${stats.cycle.toString().padEnd(10)} │  Agents: ${stats.agents.toString().padEnd(10)} ║`);
    lines.push(`║  Critical: ${stats.vehicles.critical.toString().padEnd(6)} │  Standard: ${stats.vehicles.standard.toString().padEnd(6)} │  BG: ${stats.vehicles.background.toString().padEnd(4)} ║`);
    lines.push('╚══════════════════════════════════════════════════════════╝');
    lines.push('');
    
    // Main content
    lines.push(this.renderHeatmap());
    lines.push('');
    lines.push(this.renderHotZones());
    lines.push('');
    lines.push(this.renderAgents());
    lines.push('');
    
    // Footer
    lines.push('┌──────────────────────────────────────────────────────────┐');
    lines.push('│  [LIVE] Press Ctrl+C to exit  │  Refresh: 100ms         │');
    lines.push('└──────────────────────────────────────────────────────────┘');
    
    return lines.join('\n');
  }
  
  /**
   * Start live monitoring
   */
  start() {
    if (this.running) return;
    this.running = true;
    
    console.clear();
    console.log('🔭 Scanner initializing...');
    
    this.interval = setInterval(() => {
      readline.cursorTo(process.stdout, 0, 0);
      readline.clearScreenDown(process.stdout);
      console.log(this.render());
    }, this.refreshRate);
  }
  
  /**
   * Stop monitoring
   */
  stop() {
    this.running = false;
    if (this.interval) {
      clearInterval(this.interval);
    }
    console.log('\n🔭 Scanner OFF');
  }
  
  /**
   * Export current state (for external tools)
   */
  snapshot() {
    return {
      timestamp: Date.now(),
      stats: this.highway.getStats(),
      vehicles: {
        critical: this.highway.lanes.critical.filter(v => v.alive).length,
        standard: this.highway.lanes.standard.filter(v => v.alive).length,
        background: this.highway.lanes.background.filter(v => v.alive).length
      },
      hotZones: this.highway.hotZones.length,
      agents: Array.from(this.highway.agents.keys())
    };
  }
}

module.exports = { Scanner };
