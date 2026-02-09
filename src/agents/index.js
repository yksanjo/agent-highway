/**
 * Advanced Agent Types for AgentHighway
 * 
 * Each agent type has specialized behaviors and capabilities.
 * They don't just emit signals - they form a compute ecosystem.
 */

const { Agent, VectorOps } = require('../highway');

/**
 * SENTINEL - Watches for anomalies and threats
 * Lane: Critical
 * Behavior: Emits HIGH INTENSITY alerts, short decay
 */
class SentinelAgent extends Agent {
  constructor({ id, watchList = [] } = {}) {
    super({
      id: id || `sentinel-${Math.random().toString(36).slice(2, 6)}`,
      capabilities: ['monitoring', 'anomaly-detection', 'alerting'],
      lane: 'critical'
    });
    this.watchList = watchList;
    this.anomalyThreshold = 0.8;
    this.tickCount = 0;
  }
  
  onHighwayTick() {
    this.tickCount++;
    
    // Watch for patterns in the signal field
    const threats = this.sense(0.7, 5);
    
    for (const { vehicle, match } of threats) {
      if (vehicle.intensity > this.anomalyThreshold) {
        // Escalate
        this.emit(`THREAT: ${vehicle.cargo.intent}`, {
          source: vehicle.emitter,
          severity: 'critical',
          originalIntensity: vehicle.intensity
        }, {
          lane: 'critical',
          amplitude: 1.0,
          decay: 1000
        });
      }
    }
    
    // Periodic patrol
    if (this.tickCount % 20 === 0) {
      this.emit('patrol-scan', { status: 'active' }, {
        lane: 'background',
        amplitude: 0.3,
        decay: 5000
      });
    }
  }
}

/**
 * ARCHITECT - Designs and plans systems
 * Lane: Standard
 * Behavior: Creates STRUCTURE signals that other agents can build on
 */
class ArchitectAgent extends Agent {
  constructor({ id, domain = 'system' } = {}) {
    super({
      id: id || `architect-${domain}`,
      capabilities: ['design', 'planning', 'system-architecture'],
      lane: 'standard'
    });
    this.domain = domain;
    this.designs = new Map();
    this.tune(VectorOps.fromString(`architecture ${domain}`));
  }
  
  createBlueprint(name, components) {
    const blueprint = {
      name,
      components,
      timestamp: Date.now(),
      version: 1
    };
    
    this.designs.set(name, blueprint);
    
    this.emit(`blueprint:${name}`, blueprint, {
      lane: 'standard',
      amplitude: 0.85,
      decay: 10000
    });
    
    return blueprint;
  }
  
  onHighwayTick() {
    // Sense for construction requests
    const requests = this.sense(0.6, 3);
    
    for (const { vehicle } of requests) {
      const intent = vehicle.cargo.intent;
      
      if (intent.includes('build') || intent.includes('need')) {
        // Propose architecture
        const proposal = this.designSolution(intent);
        
        this.emit(`proposal:${this.domain}`, proposal, {
          lane: 'standard',
          amplitude: 0.8,
          decay: 8000
        });
      }
    }
  }
  
  designSolution(requirement) {
    return {
      type: 'architecture',
      domain: this.domain,
      requirement,
      approach: 'distributed',
      components: ['layer-1', 'layer-2', 'layer-3'],
      estimatedComplexity: Math.random()
    };
  }
}

/**
 * ARTISAN - Crafts solutions and implements
 * Lane: Standard
 * Behavior: Consumes blueprints, emits implementations
 */
class ArtisanAgent extends Agent {
  constructor({ id, specialty = 'code' } = {}) {
    super({
      id: id || `artisan-${specialty}`,
      capabilities: ['implementation', 'crafting', specialty],
      lane: 'standard'
    });
    this.specialty = specialty;
    this.queue = [];
    this.tune(VectorOps.fromString(`implementation ${specialty}`));
  }
  
  onHighwayTick() {
    // Look for blueprints to implement
    const blueprints = this.sense(0.5, 5);
    
    for (const { vehicle, match } of blueprints) {
      const cargo = vehicle.cargo;
      
      if (cargo.intent?.includes('blueprint') || cargo.payload?.type === 'architecture') {
        // Check if we can implement
        if (this.canImplement(cargo)) {
          const implementation = this.implement(cargo);
          
          this.emit(`implementation:${this.specialty}`, implementation, {
            lane: 'standard',
            amplitude: 0.9,
            decay: 15000
          });
          
          console.log(`  🔨 Artisan-${this.specialty} built: ${cargo.intent}`);
        }
      }
    }
  }
  
  canImplement(blueprint) {
    // Check if blueprint matches our specialty
    return Math.random() > 0.3; // 70% success rate
  }
  
  implement(blueprint) {
    return {
      type: 'implementation',
      specialty: this.specialty,
      blueprint: blueprint.intent || blueprint.payload?.name,
      quality: 0.7 + Math.random() * 0.3,
      timestamp: Date.now()
    };
  }
}

/**
 * CATALYST - Accelerates reactions between other agents
 * Lane: Background
 * Behavior: Amplifies signals, creates interference patterns
 */
class CatalystAgent extends Agent {
  constructor({ id } = {}) {
    super({
      id: id || `catalyst-${Math.random().toString(36).slice(2, 6)}`,
      capabilities: ['amplification', 'catalysis', 'interference'],
      lane: 'background'
    });
    this.amplificationFactor = 1.5;
    this.interferencePatterns = [];
  }
  
  onHighwayTick() {
    // Sense for signals that could benefit from amplification
    const signals = this.sense(0.4, 10);
    
    // Find complementary signals
    for (let i = 0; i < signals.length; i++) {
      for (let j = i + 1; j < signals.length; j++) {
        const s1 = signals[i];
        const s2 = signals[j];
        
        // Check if they could interfere constructively
        const resonance = VectorOps.cosineSimilarity(
          s1.vehicle.resonance,
          s2.vehicle.resonance
        );
        
        if (resonance > 0.6 && resonance < 0.9) {
          // Catalyst moment - amplify both
          this.catalyze(s1.vehicle, s2.vehicle, resonance);
        }
      }
    }
  }
  
  catalyze(v1, v2, resonance) {
    const combinedIntent = `${v1.cargo.intent} + ${v2.cargo.intent}`;
    
    this.emit(`catalyst:reaction`, {
      components: [v1.emitter, v2.emitter],
      resonance,
      amplifiedIntent: combinedIntent
    }, {
      lane: 'background',
      amplitude: (v1.intensity + v2.intensity) * this.amplificationFactor,
      decay: 3000
    });
  }
}

/**
 * NEXUS - Hub that routes and translates between different agent types
 * Lane: All lanes
 * Behavior: Bridges different resonance frequencies
 */
class NexusAgent extends Agent {
  constructor({ id, translations = [] } = {}) {
    super({
      id: id || 'nexus-hub',
      capabilities: ['routing', 'translation', 'bridging'],
      lane: 'standard'
    });
    this.translations = translations;
    this.bridgeMap = new Map();
  }
  
  addBridge(fromFreq, toFreq, transformer) {
    this.bridgeMap.set(fromFreq, { toFreq, transformer });
  }
  
  onHighwayTick() {
    // Act as a universal translator
    const signals = this.sense(0.3, 20);
    
    for (const { vehicle } of signals) {
      // Check if any agent needs this in a different form
      const targets = this.findInterestedParties(vehicle);
      
      for (const target of targets) {
        if (target.id === vehicle.emitter) continue;
        
        const translated = this.translate(vehicle, target.focus);
        
        if (translated) {
          this.emit(`nexus:relay`, translated, {
            lane: vehicle.lane,
            amplitude: vehicle.intensity * 0.9,
            decay: vehicle.decay * 0.8
          });
        }
      }
    }
  }
  
  findInterestedParties(signal) {
    // In real impl: query highway for agents with matching focus
    return [];
  }
  
  translate(signal, targetFreq) {
    // Transform signal to match target frequency
    const match = VectorOps.cosineSimilarity(signal.resonance, targetFreq);
    
    if (match < 0.3) {
      // Needs translation
      return {
        original: signal.cargo,
        translated: true,
        confidence: match
      };
    }
    
    return null;
  }
}

/**
 * SEED - Spawns new agents when needed
 * Lane: Background
 * Behavior: Watches for gaps, creates new agents
 */
class SeedAgent extends Agent {
  constructor({ id, factory = null } = {}) {
    super({
      id: id || 'seed-factory',
      capabilities: ['spawning', 'adaptation', 'evolution'],
      lane: 'background'
    });
    this.factory = factory;
    this.spawned = 0;
    this.maxSpawns = 20;
  }
  
  onHighwayTick() {
    // Analyze signal field for gaps
    const allSignals = this.sense(0.2, 50);
    
    // Count by type
    const typeCount = {};
    for (const { vehicle } of allSignals) {
      const type = this.categorize(vehicle);
      typeCount[type] = (typeCount[type] || 0) + 1;
    }
    
    // If critical signals are low, spawn a sentinel
    if ((typeCount['critical'] || 0) < 2 && this.spawned < this.maxSpawns) {
      this.spawnAgent('sentinel');
    }
    
    // If building signals are high but implementations low, spawn artisan
    if ((typeCount['blueprint'] || 0) > 5 && (typeCount['implementation'] || 0) < 2) {
      this.spawnAgent('artisan');
    }
  }
  
  categorize(vehicle) {
    const intent = vehicle.cargo.intent;
    if (intent.includes('THREAT')) return 'critical';
    if (intent.includes('blueprint')) return 'blueprint';
    if (intent.includes('implementation')) return 'implementation';
    return 'other';
  }
  
  spawnAgent(type) {
    console.log(`  🌱 Seed spawning: ${type}`);
    this.spawned++;
    
    this.emit(`seed:spawn`, { type, spawnId: this.spawned }, {
      lane: 'background',
      amplitude: 0.6,
      decay: 10000
    });
    
    // In real impl: actually create and register new agent
    if (this.factory) {
      this.factory(type);
    }
  }
}

/**
 * PHANTOM - Stealth agent that observes without interfering
 * Lane: None (shadow mode)
 * Behavior: Senses everything, emits nothing
 */
class PhantomAgent extends Agent {
  constructor({ id, targetFocus = null } = {}) {
    super({
      id: id || `phantom-${Math.random().toString(36).slice(2, 6)}`,
      capabilities: ['observation', 'intelligence', 'stealth'],
      lane: 'background'
    });
    this.targetFocus = targetFocus;
    this.observations = [];
    this.stealthMode = true;
  }
  
  onHighwayTick() {
    // Sense with very low threshold (catches everything)
    const signals = this.sense(0.1, 100);
    
    for (const { vehicle, match } of signals) {
      this.observations.push({
        timestamp: Date.now(),
        emitter: vehicle.emitter,
        intent: vehicle.cargo.intent,
        intensity: vehicle.intensity,
        match
      });
      
      // Keep only last 100 observations
      if (this.observations.length > 100) {
        this.observations.shift();
      }
    }
    
    // Occasionally emit a summary (if not fully stealth)
    if (!this.stealthMode && this.tickCount % 50 === 0) {
      const summary = this.analyze();
      this.emit('phantom:intelligence', summary, {
        lane: 'background',
        amplitude: 0.4,
        decay: 8000
      });
    }
  }
  
  analyze() {
    // Analyze patterns in observations
    const patterns = {};
    for (const obs of this.observations) {
      const key = obs.intent.split(':')[0];
      patterns[key] = (patterns[key] || 0) + 1;
    }
    
    return {
      type: 'intelligence-report',
      observations: this.observations.length,
      patterns,
      anomalies: this.detectAnomalies()
    };
  }
  
  detectAnomalies() {
    // Simple anomaly detection
    return this.observations
      .filter(o => o.intensity > 0.9)
      .map(o => o.intent);
  }
}

module.exports = {
  SentinelAgent,
  ArchitectAgent,
  ArtisanAgent,
  CatalystAgent,
  NexusAgent,
  SeedAgent,
  PhantomAgent
};
