/**
 * AgentHighway - Core Engine
 * A signal highway for AI swarms
 * 
 * NO LOGS. NO STORAGE. JUST FLOW.
 */

const crypto = require('crypto');

/**
 * Simple ID generator
 */
function generateId() {
  return crypto.randomBytes(4).toString('hex');
}

/**
 * Vector operations for resonance matching
 */
class VectorOps {
  static cosineSimilarity(a, b) {
    if (a.length !== b.length) return 0;
    let dot = 0, normA = 0, normB = 0;
    for (let i = 0; i < a.length; i++) {
      dot += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }
    return dot / (Math.sqrt(normA) * Math.sqrt(normB) + 1e-8);
  }
  
  static random(dims = 64) {
    // Generate random unit vector (smaller for demo)
    const vec = Array(dims).fill(0).map(() => Math.random() - 0.5);
    const norm = Math.sqrt(vec.reduce((a, b) => a + b * b, 0));
    return vec.map(v => v / (norm + 1e-8));
  }
  
  static fromString(str, dims = 64) {
    // Simple hash-to-vector
    const hash = crypto.createHash('md5').update(str).digest('hex');
    const vec = [];
    for (let i = 0; i < dims; i++) {
      const byte = parseInt(hash.slice(i % 32 * 2, i % 32 * 2 + 2), 16);
      vec.push((byte / 255) - 0.5);
    }
    const norm = Math.sqrt(vec.reduce((a, b) => a + b * b, 0));
    return vec.map(v => v / (norm + 1e-8));
  }
}

/**
 * A Vehicle (signal) traveling on the highway
 */
class Vehicle {
  constructor({
    emitter,
    cargo,
    lane = 'standard',
    resonance,
    decay = 1000,
    velocity = 1,
    amplitude = 0.8
  }) {
    this.id = generateId();
    this.emitter = emitter;
    this.birthTime = Date.now();
    this.cargo = cargo;
    this.lane = lane;
    this.resonance = resonance;
    this.decay = decay;
    this.velocity = velocity;
    this.amplitude = amplitude;
    this.position = 0;
    this.interferenceCount = 0;
  }
  
  get intensity() {
    const age = Date.now() - this.birthTime;
    const halfLives = age / this.decay;
    return this.amplitude * Math.pow(0.5, halfLives);
  }
  
  get alive() {
    return this.intensity > 0.01;
  }
  
  move() {
    this.position += this.velocity;
  }
}

/**
 * The Highway - shared signal medium
 */
class Highway {
  constructor(options = {}) {
    this.lanes = {
      critical: [],
      standard: [],
      background: []
    };
    this.agents = new Map();
    this.cycle = 0;
    this.tickRate = options.tickRate || 10;
    this.running = false;
    this.onTick = null;
    this.hotZones = [];
  }
  
  register(agent) {
    this.agents.set(agent.id, agent);
    agent.highway = this;
    console.log(`🚗 Agent ${agent.id} entered highway`);
  }
  
  emit(vehicleConfig) {
    const vehicle = new Vehicle(vehicleConfig);
    this.lanes[vehicle.lane].push(vehicle);
    return vehicle.id;
  }
  
  sense({
    frequency,
    threshold = 0.6,
    lanes = ['critical', 'standard', 'background'],
    maxResults = 10
  }) {
    const results = [];
    
    for (const laneName of lanes) {
      for (const vehicle of this.lanes[laneName]) {
        if (!vehicle.alive) continue;
        
        const match = VectorOps.cosineSimilarity(frequency, vehicle.resonance);
        const weightedMatch = match * vehicle.intensity;
        
        if (weightedMatch > threshold) {
          results.push({ vehicle, match: weightedMatch, intensity: vehicle.intensity });
        }
      }
    }
    
    results.sort((a, b) => b.match - a.match);
    return results.slice(0, maxResults);
  }
  
  calculateInterference() {
    const allVehicles = [
      ...this.lanes.critical,
      ...this.lanes.standard,
      ...this.lanes.background
    ].filter(v => v.alive);
    
    this.hotZones = [];
    
    for (let i = 0; i < allVehicles.length; i++) {
      for (let j = i + 1; j < allVehicles.length; j++) {
        const v1 = allVehicles[i];
        const v2 = allVehicles[j];
        
        const resonance = VectorOps.cosineSimilarity(v1.resonance, v2.resonance);
        
        if (resonance > 0.75) {
          const combinedIntensity = v1.intensity + v2.intensity;
          this.hotZones.push({
            vehicles: [v1, v2],
            resonance: v1.resonance.map((v, i) => (v + v2.resonance[i]) / 2),
            intensity: combinedIntensity,
            match: resonance
          });
          
          v1.interferenceCount++;
          v2.interferenceCount++;
        }
      }
    }
    
    this.hotZones.sort((a, b) => b.intensity - a.intensity);
  }
  
  tick() {
    this.cycle++;
    
    for (const lane of Object.values(this.lanes)) {
      for (const vehicle of lane) {
        vehicle.move();
      }
    }
    
    this.calculateInterference();
    
    for (const laneName of Object.keys(this.lanes)) {
      this.lanes[laneName] = this.lanes[laneName].filter(v => v.alive);
    }
    
    for (const agent of this.agents.values()) {
      if (agent.onHighwayTick) {
        agent.onHighwayTick();
      }
    }
    
    if (this.onTick) {
      this.onTick(this.getStats());
    }
  }
  
  start() {
    if (this.running) return;
    this.running = true;
    console.log('🛣️  Highway OPEN');
    console.log(`   Tick rate: ${this.tickRate}ms`);
    
    this.interval = setInterval(() => this.tick(), this.tickRate);
  }
  
  stop() {
    this.running = false;
    if (this.interval) {
      clearInterval(this.interval);
    }
    console.log('🛑 Highway CLOSED');
  }
  
  getStats() {
    const critical = this.lanes.critical.filter(v => v.alive).length;
    const standard = this.lanes.standard.filter(v => v.alive).length;
    const background = this.lanes.background.filter(v => v.alive).length;
    
    return {
      cycle: this.cycle,
      agents: this.agents.size,
      vehicles: { critical, standard, background },
      totalVehicles: critical + standard + background,
      hotZones: this.hotZones.slice(0, 3).map(z => ({
        intensity: z.intensity.toFixed(2),
        match: z.match.toFixed(2)
      }))
    };
  }
}

/**
 * Base Agent class
 */
class Agent {
  constructor({ id, capabilities = [], lane = 'standard' } = {}) {
    this.id = id || generateId();
    this.capabilities = capabilities;
    this.lane = lane;
    this.focus = VectorOps.random();
    this.highway = null;
  }
  
  tune(frequency) {
    this.focus = frequency;
  }
  
  emit(intent, payload = null, options = {}) {
    if (!this.highway) {
      throw new Error('Agent not registered on highway');
    }
    
    let resonance;
    if (typeof intent === 'string') {
      resonance = VectorOps.fromString(intent);
    } else {
      resonance = this.focus;
    }
    
    return this.highway.emit({
      emitter: this.id,
      cargo: { intent, payload },
      lane: options.lane || this.lane,
      resonance,
      decay: options.decay || 2000,
      amplitude: options.amplitude || 0.8
    });
  }
  
  sense(threshold = 0.5, maxResults = 5) {
    if (!this.highway) return [];
    
    return this.highway.sense({
      frequency: this.focus,
      threshold,
      maxResults
    });
  }
  
  onHighwayTick() {
    // Override in subclasses
  }
}

module.exports = { Highway, Agent, Vehicle, VectorOps };
