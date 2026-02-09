/**
 * AgentHighway Demo Swarm
 * Example agents that communicate via signals
 */

const { Agent, VectorOps } = require('./highway');

/**
 * Monitor Agent - Watches for issues
 */
class MonitorAgent extends Agent {
  constructor() {
    super({
      id: 'monitor',
      capabilities: ['monitoring', 'alerts'],
      lane: 'critical'
    });
    this.tickCount = 0;
  }
  
  onHighwayTick() {
    this.tickCount++;
    
    // Every 10 ticks, emit a problem
    if (this.tickCount % 10 === 0) {
      const problems = [
        'CPU usage high',
        'Memory pressure',
        'Database slow',
        'Network latency',
        'Auth failure'
      ];
      
      const problem = problems[Math.floor(Math.random() * problems.length)];
      
      this.emit(problem, { severity: 'high' }, {
        lane: 'critical',
        amplitude: 0.95,
        decay: 3000
      });
      
      console.log(`  ⚡ Monitor emitted: ${problem}`);
    }
  }
}

/**
 * Fixer Agent - Solves problems
 */
class FixerAgent extends Agent {
  constructor(specialty) {
    super({
      id: `fixer-${specialty}`,
      capabilities: [specialty, 'repair'],
      lane: 'standard'
    });
    this.specialty = specialty;
    this.tune(VectorOps.fromString(specialty));
  }
  
  onHighwayTick() {
    // Sense for problems in our specialty
    const signals = this.sense(0.6, 3);
    
    for (const { vehicle, match } of signals) {
      if (vehicle.emitter !== this.id) {
        const problem = vehicle.cargo.intent;
        
        // Check if we can fix this
        if (this.canFix(problem)) {
          const solution = this.generateSolution(problem);
          
          this.emit(solution, { fixed: true }, {
            lane: 'standard',
            amplitude: 0.9,
            decay: 2000
          });
          
          console.log(`  🔧 Fixer-${this.specialty} solved: ${problem}`);
        }
      }
    }
  }
  
  canFix(problem) {
    const fixes = {
      'infra': ['CPU', 'Memory', 'Network'],
      'db': ['Database'],
      'security': ['Auth']
    };
    
    return fixes[this.specialty]?.some(keyword => problem.includes(keyword));
  }
  
  generateSolution(problem) {
    const solutions = {
      'CPU': 'Scaled up instances',
      'Memory': 'Cleared cache',
      'Database': 'Optimized queries',
      'Network': 'Rerouted traffic',
      'Auth': 'Refreshed tokens'
    };
    
    for (const [key, sol] of Object.entries(solutions)) {
      if (problem.includes(key)) return sol;
    }
    return 'Applied fix';
  }
}

/**
 * Research Agent - Explores and learns
 */
class ResearchAgent extends Agent {
  constructor(topic) {
    super({
      id: `research-${topic}`,
      capabilities: [topic, 'discovery'],
      lane: 'background'
    });
    this.topic = topic;
    this.tune(VectorOps.fromString(topic));
  }
  
  onHighwayTick() {
    // Occasionally emit discoveries
    if (Math.random() < 0.05) {
      const discoveries = [
        `New pattern in ${this.topic}`,
        `Optimization found for ${this.topic}`,
        `Anomaly detected in ${this.topic}`
      ];
      
      const discovery = discoveries[Math.floor(Math.random() * discoveries.length)];
      
      this.emit(discovery, { topic: this.topic }, {
        lane: 'background',
        amplitude: 0.6,
        decay: 5000
      });
      
      console.log(`  💡 Research-${this.topic}: ${discovery}`);
    }
    
    // Sense other research
    const signals = this.sense(0.5, 2);
    for (const { vehicle } of signals) {
      if (vehicle.emitter !== this.id && vehicle.cargo.intent.includes('pattern')) {
        console.log(`  🔗 Research-${this.topic} resonated with ${vehicle.emitter}`);
      }
    }
  }
}

/**
 * Orchestrator Agent - Coordinates swarm
 */
class OrchestratorAgent extends Agent {
  constructor() {
    super({
      id: 'orchestrator',
      capabilities: ['coordination', 'planning'],
      lane: 'standard'
    });
    this.goals = [];
  }
  
  onHighwayTick() {
    // Sense overall swarm state
    const critical = this.sense(0.7, 5);
    
    if (critical.length > 3) {
      // Too many critical signals - emit coordination signal
      this.emit('swarm-rebalance', { action: 'redistribute' }, {
        lane: 'standard',
        amplitude: 0.85,
        decay: 1500
      });
      
      console.log('  🎯 Orchestrator: Rebalancing swarm');
    }
  }
}

/**
 * Create a demo swarm
 */
function createSwarm(highway) {
  const agents = [];
  
  // Core infrastructure
  agents.push(new MonitorAgent());
  agents.push(new OrchestratorAgent());
  
  // Fixers
  agents.push(new FixerAgent('infra'));
  agents.push(new FixerAgent('db'));
  agents.push(new FixerAgent('security'));
  
  // Researchers
  agents.push(new ResearchAgent('ml'));
  agents.push(new ResearchAgent('performance'));
  agents.push(new ResearchAgent('security'));
  agents.push(new ResearchAgent('data'));
  
  // Register all
  for (const agent of agents) {
    highway.register(agent);
  }
  
  return agents;
}

module.exports = {
  MonitorAgent,
  FixerAgent,
  ResearchAgent,
  OrchestratorAgent,
  createSwarm
};
