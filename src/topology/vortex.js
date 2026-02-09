/**
 * Vortex Topology
 * 
 * Agents don't just communicate - they exist in a spatial compute vortex.
 * Signals flow through the topology, not just broadcast.
 * 
 * Visual metaphor:
 *                    ╭──────────╮
 *               ╭────┤  SEAT 1  ├────╮
 *          ╭────┤    ╰────┬─────╯    ├────╮
 *     ╭────┤    │         │          │    ├────╮
 *     │    │ SEAT 2 ◄─────┼─────────► SEAT 3 │    │
 *     │    ╰────┬─────────┼──────────┬────╯    │
 *     │         │    ╭────┴────╮     │         │
 *     │         └───►┤  CORE   ├◄────┘         │
 *     │              ╰────┬────╯                │
 *     │    ╭──────────────┼──────────────╮     │
 *     ╰────┤   SEAT 4 ◄───┴───► SEAT 5   ├────╯
 *          ╰──────────────┴──────────────╯
 * 
 * The vortex is a living topology where:
 * - Each SEAT is a position in compute space
 * - Distance affects signal propagation speed
 * - The CORE is the densest interference zone
 * - Signals spiral toward the center, then radiate outward
 */

const { VectorOps } = require('../highway');

/**
 * A Seat in the compute vortex
 */
class Seat {
  constructor({
    id,
    position,        // {x, y, z} in vortex space
    tier = 'edge',   // 'core', 'inner', 'outer', 'edge'
    capacity = 10,   // How many agents can occupy
    resonance = null // Preferred signal frequency
  }) {
    this.id = id;
    this.position = position;
    this.tier = tier;
    this.capacity = capacity;
    this.occupants = new Set();
    this.resonance = resonance || VectorOps.random();
    
    // Vortex dynamics
    this.rotationSpeed = this.calculateRotation();
    this.gravityWell = this.calculateGravity();
  }
  
  calculateRotation() {
    // Inner tiers rotate faster
    const speeds = { core: 0.5, inner: 0.3, outer: 0.15, edge: 0.05 };
    return speeds[this.tier] || 0.1;
  }
  
  calculateGravity() {
    // Closer to core = stronger gravity
    const distance = Math.sqrt(
      this.position.x ** 2 + 
      this.position.y ** 2 + 
      this.position.z ** 2
    );
    return 1 / (distance + 0.1);
  }
  
  occupy(agent) {
    if (this.occupants.size >= this.capacity) {
      return false;
    }
    this.occupants.add(agent.id);
    agent.seat = this;
    return true;
  }
  
  vacate(agent) {
    this.occupants.delete(agent.id);
    agent.seat = null;
  }
  
  /**
   * Calculate distance to another seat
   */
  distanceTo(other) {
    const dx = this.position.x - other.position.x;
    const dy = this.position.y - other.position.y;
    const dz = this.position.z - other.position.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }
  
  /**
   * Calculate signal propagation time to another seat
   */
  propagationTimeTo(other) {
    const distance = this.distanceTo(other);
    // Vortex effect: signals travel faster toward core
    const vortexBoost = 1 + this.gravityWell;
    return distance / vortexBoost;
  }
}

/**
 * The Vortex - Spatial compute topology
 */
class Vortex {
  constructor(config = {}) {
    this.seats = new Map();
    this.agents = new Map();
    this.rotation = 0;
    this.cycle = 0;
    
    // Vortex configuration
    this.tiers = config.tiers || {
      core: { radius: 10, seats: 3 },
      inner: { radius: 30, seats: 6 },
      outer: { radius: 60, seats: 12 },
      edge: { radius: 100, seats: 24 }
    };
    
    this.initializeTopology();
  }
  
  /**
   * Create the vortex structure
   */
  initializeTopology() {
    // Core - the densest compute zone
    for (let i = 0; i < this.tiers.core.seats; i++) {
      const angle = (i / this.tiers.core.seats) * Math.PI * 2;
      this.createSeat(`core-${i}`, {
        x: Math.cos(angle) * this.tiers.core.radius * 0.3,
        y: Math.sin(angle) * this.tiers.core.radius * 0.3,
        z: (Math.random() - 0.5) * 10
      }, 'core');
    }
    
    // Inner ring
    for (let i = 0; i < this.tiers.inner.seats; i++) {
      const angle = (i / this.tiers.inner.seats) * Math.PI * 2;
      this.createSeat(`inner-${i}`, {
        x: Math.cos(angle) * this.tiers.inner.radius,
        y: Math.sin(angle) * this.tiers.inner.radius,
        z: (Math.random() - 0.5) * 20
      }, 'inner');
    }
    
    // Outer ring
    for (let i = 0; i < this.tiers.outer.seats; i++) {
      const angle = (i / this.tiers.outer.seats) * Math.PI * 2;
      this.createSeat(`outer-${i}`, {
        x: Math.cos(angle) * this.tiers.outer.radius,
        y: Math.sin(angle) * this.tiers.outer.radius,
        z: (Math.random() - 0.5) * 40
      }, 'outer');
    }
    
    // Edge ring
    for (let i = 0; i < this.tiers.edge.seats; i++) {
      const angle = (i / this.tiers.edge.seats) * Math.PI * 2;
      this.createSeat(`edge-${i}`, {
        x: Math.cos(angle) * this.tiers.edge.radius,
        y: Math.sin(angle) * this.tiers.edge.radius,
        z: (Math.random() - 0.5) * 60
      }, 'edge');
    }
    
    console.log(`🌀 Vortex initialized: ${this.seats.size} seats`);
  }
  
  createSeat(id, position, tier) {
    const seat = new Seat({ id, position, tier });
    this.seats.set(id, seat);
    return seat;
  }
  
  /**
   * Place agent in the vortex
   */
  seatAgent(agent, preferredTier = null) {
    // Find best seat based on agent's needs
    const candidates = Array.from(this.seats.values())
      .filter(s => s.occupants.size < s.capacity)
      .filter(s => !preferredTier || s.tier === preferredTier)
      .sort((a, b) => {
        // Prioritize by resonance match
        const matchA = VectorOps.cosineSimilarity(agent.focus, a.resonance);
        const matchB = VectorOps.cosineSimilarity(agent.focus, b.resonance);
        return matchB - matchA;
      });
    
    if (candidates.length === 0) {
      console.log(`⚠️ No seats available for ${agent.id}`);
      return null;
    }
    
    const seat = candidates[0];
    seat.occupy(agent);
    this.agents.set(agent.id, agent);
    
    console.log(`💺 ${agent.id} seated at ${seat.id} (${seat.tier})`);
    return seat;
  }
  
  /**
   * Calculate signal path through vortex
   */
  calculateSignalPath(fromAgent, toAgent) {
    const fromSeat = fromAgent.seat;
    const toSeat = toAgent.seat;
    
    if (!fromSeat || !toSeat) {
      return null;
    }
    
    // Direct path
    const direct = {
      type: 'direct',
      distance: fromSeat.distanceTo(toSeat),
      time: fromSeat.propagationTimeTo(toSeat),
      hops: 1
    };
    
    // Vortex path (spiral toward core then out)
    const coreSeats = Array.from(this.seats.values()).filter(s => s.tier === 'core');
    const nearestCore = coreSeats.sort((a, b) => 
      fromSeat.distanceTo(a) - fromSeat.distanceTo(b)
    )[0];
    
    const vortexDistance = 
      fromSeat.distanceTo(nearestCore) + 
      nearestCore.distanceTo(toSeat);
    
    const vortexTime = 
      fromSeat.propagationTimeTo(nearestCore) + 
      nearestCore.propagationTimeTo(toSeat);
    
    const vortex = {
      type: 'vortex',
      distance: vortexDistance,
      time: vortexTime,
      hops: 2,
      via: nearestCore.id
    };
    
    // Return fastest path
    return direct.time < vortex.time ? direct : vortex;
  }
  
  /**
   * Get agents that can sense a signal
   */
  getSensingAgents(originAgent, resonance, radius = null) {
    const originSeat = originAgent.seat;
    if (!originSeat) return [];
    
    const results = [];
    
    for (const [agentId, agent] of this.agents) {
      if (agentId === originAgent.id) continue;
      
      const agentSeat = agent.seat;
      if (!agentSeat) continue;
      
      const distance = originSeat.distanceTo(agentSeat);
      
      // Check radius
      if (radius && distance > radius) continue;
      
      // Check resonance
      const match = VectorOps.cosineSimilarity(resonance, agent.focus);
      
      results.push({
        agent,
        distance,
        match,
        seat: agentSeat
      });
    }
    
    return results.sort((a, b) => b.match - a.match);
  }
  
  /**
   * Rotate the vortex (called each tick)
   */
  rotate() {
    this.cycle++;
    this.rotation += 0.01;
    
    // Update seat positions based on rotation
    for (const seat of this.seats.values()) {
      const speed = seat.rotationSpeed;
      const angle = this.rotation * speed;
      
      const r = Math.sqrt(seat.position.x ** 2 + seat.position.y ** 2);
      seat.position.x = Math.cos(angle) * r;
      seat.position.y = Math.sin(angle) * r;
    }
  }
  
  /**
   * Get topology snapshot (for visualization)
   */
  snapshot() {
    return {
      rotation: this.rotation,
      cycle: this.cycle,
      seats: Array.from(this.seats.values()).map(s => ({
        id: s.id,
        tier: s.tier,
        position: s.position,
        occupants: Array.from(s.occupants),
        capacity: s.capacity,
        gravity: s.gravityWell,
        rotation: s.rotationSpeed
      })),
      agents: Array.from(this.agents.values()).map(a => ({
        id: a.id,
        seat: a.seat?.id,
        capabilities: a.capabilities
      }))
    };
  }
}

module.exports = { Vortex, Seat };
