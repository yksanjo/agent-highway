/**
 * Vortex Visualizer
 * Retro CRT-style visualization of the agent topology
 */

class VortexVisualizer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.agents = [];
    this.signals = [];
    this.seats = [];
    this.rotation = 0;
    this.cycle = 0;
    
    this.resize();
    window.addEventListener('resize', () => this.resize());
    
    // Visual params
    this.colors = {
      phosphor: '#33ff00',
      phosphorDim: 'rgba(51, 255, 0, 0.3)',
      amber: '#ffb000',
      cyan: '#00ffff',
      red: '#ff3333',
      grid: 'rgba(51, 255, 0, 0.1)'
    };
    
    this.centerX = this.canvas.width / 2;
    this.centerY = this.canvas.height / 2;
    this.scale = Math.min(this.centerX, this.centerY) / 120;
  }
  
  resize() {
    this.canvas.width = this.canvas.offsetWidth;
    this.canvas.height = this.canvas.offsetHeight;
    this.centerX = this.canvas.width / 2;
    this.centerY = this.canvas.height / 2;
    this.scale = Math.min(this.centerX, this.centerY) / 120;
  }
  
  /**
   * Update topology data
   */
  updateTopology(data) {
    this.seats = data.seats || [];
    this.agents = data.agents || [];
    this.rotation = data.rotation || 0;
    this.cycle = data.cycle || 0;
  }
  
  /**
   * Update signal data
   */
  updateSignals(signals) {
    this.signals = signals || [];
  }
  
  /**
   * Main render loop
   */
  render() {
    this.ctx.fillStyle = '#0a0a0a';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    
    this.drawGrid();
    this.drawVortexRings();
    this.drawSeats();
    this.drawSignals();
    this.drawAgents();
    this.drawInterference();
    
    // CRT scanline effect
    this.drawScanlines();
  }
  
  drawGrid() {
    this.ctx.strokeStyle = this.colors.grid;
    this.ctx.lineWidth = 1;
    
    const gridSize = 40 * this.scale;
    
    // Radial grid
    for (let r = 20; r <= 120; r += 20) {
      this.ctx.beginPath();
      this.ctx.arc(this.centerX, this.centerY, r * this.scale, 0, Math.PI * 2);
      this.ctx.stroke();
    }
    
    // Angular grid
    for (let a = 0; a < 12; a++) {
      const angle = (a / 12) * Math.PI * 2 + this.rotation * 0.1;
      this.ctx.beginPath();
      this.ctx.moveTo(this.centerX, this.centerY);
      this.ctx.lineTo(
        this.centerX + Math.cos(angle) * 120 * this.scale,
        this.centerY + Math.sin(angle) * 120 * this.scale
      );
      this.ctx.stroke();
    }
  }
  
  drawVortexRings() {
    const rings = [
      { r: 20, color: this.colors.red, label: 'CORE' },
      { r: 50, color: this.colors.amber, label: 'INNER' },
      { r: 80, color: this.colors.phosphor, label: 'OUTER' },
      { r: 110, color: this.colors.cyan, label: 'EDGE' }
    ];
    
    for (const ring of rings) {
      this.ctx.strokeStyle = ring.color;
      this.ctx.lineWidth = 2;
      this.ctx.setLineDash([5, 5]);
      
      this.ctx.beginPath();
      this.ctx.arc(this.centerX, this.centerY, ring.r * this.scale, 0, Math.PI * 2);
      this.ctx.stroke();
      this.ctx.setLineDash([]);
      
      // Ring label
      this.ctx.fillStyle = ring.color;
      this.ctx.font = '10px Courier New';
      this.ctx.fillText(
        ring.label,
        this.centerX + ring.r * this.scale + 10,
        this.centerY - 5
      );
    }
  }
  
  drawSeats() {
    for (const seat of this.seats) {
      const x = this.centerX + seat.position.x * this.scale;
      const y = this.centerY + seat.position.y * this.scale;
      
      // Seat glow based on occupancy
      const occupancy = seat.occupants?.length || 0;
      const maxCap = seat.capacity || 1;
      const intensity = occupancy / maxCap;
      
      // Seat base
      this.ctx.fillStyle = `rgba(51, 255, 0, ${0.2 + intensity * 0.5})`;
      this.ctx.fillRect(x - 8, y - 8, 16, 16);
      
      // Seat border
      this.ctx.strokeStyle = this.colors.phosphor;
      this.ctx.lineWidth = 1;
      this.ctx.strokeRect(x - 8, y - 8, 16, 16);
      
      // Gravity indicator
      const gravity = seat.gravity || 0.1;
      this.ctx.fillStyle = this.colors.amber;
      this.ctx.fillRect(x - 6, y + 10, 12 * gravity, 2);
      
      // Occupant count
      if (occupancy > 0) {
        this.ctx.fillStyle = this.colors.phosphor;
        this.ctx.font = '9px Courier New';
        this.ctx.fillText(occupancy.toString(), x - 3, y - 10);
      }
    }
  }
  
  drawAgents() {
    for (const agent of this.agents) {
      // Find agent's seat position
      const seat = this.seats.find(s => s.id === agent.seat);
      if (!seat) continue;
      
      const x = this.centerX + seat.position.x * this.scale;
      const y = this.centerY + seat.position.y * this.scale;
      
      // Agent pulse
      const pulse = Math.sin(Date.now() / 200) * 0.5 + 0.5;
      const size = 6 + pulse * 4;
      
      // Agent glow
      const gradient = this.ctx.createRadialGradient(x, y, 0, x, y, size * 2);
      gradient.addColorStop(0, `rgba(51, 255, 0, ${0.8 * pulse})`);
      gradient.addColorStop(1, 'rgba(51, 255, 0, 0)');
      
      this.ctx.fillStyle = gradient;
      this.ctx.beginPath();
      this.ctx.arc(x, y, size * 2, 0, Math.PI * 2);
      this.ctx.fill();
      
      // Agent core
      this.ctx.fillStyle = this.colors.phosphor;
      this.ctx.beginPath();
      this.ctx.arc(x, y, 4, 0, Math.PI * 2);
      this.ctx.fill();
      
      // Agent ID (abbreviated)
      this.ctx.fillStyle = this.colors.phosphor;
      this.ctx.font = '8px Courier New';
      this.ctx.fillText(agent.id.slice(0, 6), x + 10, y + 3);
    }
  }
  
  drawSignals() {
    for (const signal of this.signals) {
      // Find emitter position
      const emitterAgent = this.agents.find(a => a.id === signal.emitter);
      if (!emitterAgent) continue;
      
      const seat = this.seats.find(s => s.id === emitterAgent.seat);
      if (!seat) continue;
      
      const x = this.centerX + seat.position.x * this.scale;
      const y = this.centerY + seat.position.y * this.scale;
      
      // Signal ripple
      const age = (Date.now() - signal.birthTime) / signal.decay;
      const radius = age * 50 * this.scale;
      const alpha = 1 - age;
      
      // Lane color
      const colors = {
        critical: this.colors.red,
        standard: this.colors.amber,
        background: this.colors.cyan
      };
      
      this.ctx.strokeStyle = colors[signal.lane] || this.colors.phosphor;
      this.ctx.lineWidth = 2;
      this.ctx.globalAlpha = Math.max(0, alpha);
      
      this.ctx.beginPath();
      this.ctx.arc(x, y, radius, 0, Math.PI * 2);
      this.ctx.stroke();
      
      this.ctx.globalAlpha = 1;
    }
  }
  
  drawInterference() {
    // Draw hot zones as glowing areas
    const hotZones = this.signals.filter(s => s.interferenceCount > 0);
    
    for (const zone of hotZones) {
      const seat = this.seats.find(s => s.occupants?.includes(zone.emitter));
      if (!seat) continue;
      
      const x = this.centerX + seat.position.x * this.scale;
      const y = this.centerY + seat.position.y * this.scale;
      
      const intensity = Math.min(zone.interferenceCount / 5, 1);
      
      const gradient = this.ctx.createRadialGradient(x, y, 0, x, y, 30 * this.scale);
      gradient.addColorStop(0, `rgba(255, 176, 0, ${intensity * 0.5})`);
      gradient.addColorStop(1, 'rgba(255, 176, 0, 0)');
      
      this.ctx.fillStyle = gradient;
      this.ctx.beginPath();
      this.ctx.arc(x, y, 30 * this.scale, 0, Math.PI * 2);
      this.ctx.fill();
    }
  }
  
  drawScanlines() {
    // Subtle scanline overlay
    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
    for (let y = 0; y < this.canvas.height; y += 4) {
      this.ctx.fillRect(0, y, this.canvas.width, 1);
    }
  }
  
  /**
   * Get seat at position (for click interactions)
   */
  getSeatAt(x, y) {
    for (const seat of this.seats) {
      const sx = this.centerX + seat.position.x * this.scale;
      const sy = this.centerY + seat.position.y * this.scale;
      const dist = Math.sqrt((x - sx) ** 2 + (y - sy) ** 2);
      
      if (dist < 15) {
        return seat;
      }
    }
    return null;
  }
}

// Export for use
if (typeof module !== 'undefined') {
  module.exports = { VortexVisualizer };
}
