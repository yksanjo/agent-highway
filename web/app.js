/**
 * AgentHighway Web Monitor
 * Main application entry
 */

// Initialize
let vortexVis;
let animationId;

function init() {
  console.log('🛣️ AgentHighway Monitor initializing...');
  
  // Create visualizer
  vortexVis = new VortexVisualizer('vortex-canvas');
  window.vortexVis = vortexVis;
  
  // Connect API
  api.connect();
  
  // Setup event listeners
  api.on('topology', (data) => {
    updateStats(data.payload);
  });
  
  api.on('signal', (data) => {
    updateSignalStats(data.payload);
  });
  
  // Canvas interactions
  setupCanvasInteractions();
  
  // Start render loop
  render();
  
  // Periodic updates
  setInterval(updateMetrics, 1000);
  
  console.log('✅ Monitor ready');
}

function updateStats(topology) {
  // Update counters
  const agentCount = topology.agents?.length || 0;
  const seatCount = topology.seats?.length || 0;
  
  document.getElementById('node-count').textContent = agentCount;
  document.getElementById('cycle-count').textContent = topology.cycle || 0;
  
  // Update rotation display
  const rotationDeg = Math.round((topology.rotation || 0) * 180 / Math.PI);
  document.getElementById('rotation').textContent = `${rotationDeg}°`;
}

function updateSignalStats(signals) {
  // Calculate signal rate (simplified)
  const rate = signals.length || 0;
  document.getElementById('signal-rate').textContent = `${rate}/s`;
}

function updateMetrics() {
  // These would come from API
  const mockData = {
    critical: Math.floor(Math.random() * 10),
    standard: Math.floor(Math.random() * 20),
    background: Math.floor(Math.random() * 30),
    hotZones: Math.floor(Math.random() * 5)
  };
  
  document.getElementById('metric-crit').textContent = mockData.critical;
  document.getElementById('metric-std').textContent = mockData.standard;
  document.getElementById('metric-bg').textContent = mockData.background;
  document.getElementById('metric-hot').textContent = mockData.hotZones;
}

function setupCanvasInteractions() {
  const canvas = document.getElementById('vortex-canvas');
  
  canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const seat = vortexVis.getSeatAt(x, y);
    if (seat) {
      api.log(`Selected seat: ${seat.id} (${seat.tier})`, 'info');
      // Could show seat details here
    }
  });
  
  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const seat = vortexVis.getSeatAt(x, y);
    canvas.style.cursor = seat ? 'pointer' : 'default';
  });
}

function render() {
  vortexVis.render();
  animationId = requestAnimationFrame(render);
}

// Handle window unload
window.addEventListener('beforeunload', () => {
  if (animationId) {
    cancelAnimationFrame(animationId);
  }
});

// Start
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
