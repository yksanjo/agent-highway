/**
 * Public Highway Registry
 * 
 * Central registry for public highway instances.
 * Agents can query this to find the nearest/best highway.
 */

const express = require('express');
const cors = require('cors');

class HighwayRegistry {
  constructor(options = {}) {
    this.app = express();
    this.port = options.port || 8080;
    
    // Registered highways
    this.highways = new Map();
    
    // Setup
    this.app.use(cors());
    this.app.use(express.json());
    this.setupRoutes();
  }
  
  setupRoutes() {
    // Register a new highway instance
    this.app.post('/register', (req, res) => {
      const { url, region, capacity, features = [] } = req.body;
      
      if (!url || !region) {
        return res.status(400).json({ error: 'URL and region required' });
      }
      
      const id = `hw-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      
      this.highways.set(id, {
        id,
        url,
        region,
        capacity: capacity || 1000,
        agents: 0,
        load: 0,
        features,
        lastSeen: Date.now(),
        health: 'unknown'
      });
      
      console.log(`🌐 Highway registered: ${url} (${region})`);
      
      res.json({ 
        success: true, 
        id,
        message: 'Highway registered. Send heartbeat every 30s.'
      });
    });
    
    // Heartbeat from highway
    this.app.post('/heartbeat/:id', (req, res) => {
      const { id } = req.params;
      const { agents, load, health } = req.body;
      
      const highway = this.highways.get(id);
      if (!highway) {
        return res.status(404).json({ error: 'Highway not found' });
      }
      
      highway.agents = agents || highway.agents;
      highway.load = load || highway.load;
      highway.health = health || 'healthy';
      highway.lastSeen = Date.now();
      
      res.json({ success: true });
    });
    
    // Get list of available highways
    this.app.get('/highways', (req, res) => {
      const { region, maxLoad } = req.query;
      
      let highways = Array.from(this.highways.values())
        .filter(hw => hw.health === 'healthy')
        .filter(hw => Date.now() - hw.lastSeen < 120000); // Seen in last 2 min
      
      if (region) {
        highways = highways.filter(hw => hw.region === region);
      }
      
      if (maxLoad) {
        highways = highways.filter(hw => hw.load < parseFloat(maxLoad));
      }
      
      // Sort by load (least loaded first)
      highways.sort((a, b) => a.load - b.load);
      
      res.json({
        count: highways.length,
        highways: highways.map(hw => ({
          url: hw.url,
          region: hw.region,
          load: hw.load,
          agents: hw.agents,
          capacity: hw.capacity,
          features: hw.features
        }))
      });
    });
    
    // Find nearest highway
    this.app.get('/nearest', (req, res) => {
      const { lat, lon, region } = req.query;
      
      // If region provided, use that
      if (region) {
        const highways = Array.from(this.highways.values())
          .filter(hw => hw.region === region && hw.health === 'healthy')
          .sort((a, b) => a.load - b.load);
        
        if (highways.length > 0) {
          return res.json({
            highway: {
              url: highways[0].url,
              region: highways[0].region,
              load: highways[0].load
            }
          });
        }
      }
      
      // Otherwise return least loaded globally
      const highways = Array.from(this.highways.values())
        .filter(hw => hw.health === 'healthy')
        .sort((a, b) => a.load - b.load);
      
      if (highways.length === 0) {
        return res.status(503).json({ 
          error: 'No highways available',
          fallback: 'ws://localhost:9000'
        });
      }
      
      res.json({
        highway: {
          url: highways[0].url,
          region: highways[0].region,
          load: highways[0].load
        }
      });
    });
    
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        highways: this.highways.size,
        healthy: Array.from(this.highways.values())
          .filter(hw => hw.health === 'healthy').length
      });
    });
  }
  
  /**
   * Clean up stale highways
   */
  startCleanup() {
    setInterval(() => {
      const now = Date.now();
      let removed = 0;
      
      for (const [id, hw] of this.highways) {
        if (now - hw.lastSeen > 300000) { // 5 minutes
          this.highways.delete(id);
          removed++;
        }
      }
      
      if (removed > 0) {
        console.log(`🧹 Cleaned up ${removed} stale highways`);
      }
    }, 60000);
  }
  
  start() {
    this.startCleanup();
    
    this.app.listen(this.port, () => {
      console.log(`📡 Highway Registry running on port ${this.port}`);
    });
  }
}

module.exports = { HighwayRegistry };
