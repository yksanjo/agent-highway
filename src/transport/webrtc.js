/**
 * WebRTC Transport for AgentHighway
 * 
 * Enables true P2P distributed networks.
 * No central server. Agents connect directly.
 */

const EventEmitter = require('events');

/**
 * WebRTC signaling channel (for initial connection)
 * Can be replaced with any signaling mechanism
 */
class SignalingChannel extends EventEmitter {
  constructor(nodeId) {
    super();
    this.nodeId = nodeId;
    this.peers = new Map();
  }
  
  broadcast(message) {
    // In real impl: use WebSocket, PubSub, or DHT
    this.emit('signal', message);
  }
  
  signal(peerId, message) {
    // Direct signal to peer
    this.emit('signal', { to: peerId, from: this.nodeId, data: message });
  }
}

/**
 * P2P Connection to another node
 */
class PeerConnection extends EventEmitter {
  constructor(localId, remoteId, isInitiator = false) {
    super();
    this.localId = localId;
    this.remoteId = remoteId;
    this.isInitiator = isInitiator;
    this.connected = false;
    this.latency = null;
    
    // Simulated WebRTC (replace with actual wrtc library)
    this.pc = null;
    this.channel = null;
    
    this.initialize();
  }
  
  initialize() {
    // In real implementation:
    // this.pc = new RTCPeerConnection({ iceServers: [...] });
    
    // Simulation for now
    setTimeout(() => {
      this.connected = true;
      this.latency = Math.random() * 20 + 5; // 5-25ms
      this.emit('connect');
    }, 100);
  }
  
  send(data) {
    if (!this.connected) return false;
    
    // In real impl: this.channel.send(JSON.stringify(data))
    this.emit('data', data);
    return true;
  }
  
  close() {
    this.connected = false;
    this.emit('close');
  }
}

/**
 * Distributed Highway Node
 * 
 * Each node is both a highway AND a peer in the network.
 */
class DistributedHighway extends EventEmitter {
  constructor({
    nodeId = null,
    signaling = null,
    maxPeers = 10
  } = {}) {
    super();
    
    this.nodeId = nodeId || this.generateId();
    this.signaling = signaling || new SignalingChannel(this.nodeId);
    this.maxPeers = maxPeers;
    
    // Local highway state
    this.localSignals = [];
    this.peers = new Map();
    this.neighbors = new Set();
    
    // Network topology
    this.networkMap = new Map(); // nodeId -> {latency, hops, lastSeen}
    
    // Gossip protocol
    this.gossipInterval = null;
    this.gossipPeriod = 500; // ms
    
    this.initialize();
  }
  
  generateId() {
    return Math.random().toString(36).substring(2, 10);
  }
  
  initialize() {
    // Listen for signals from signaling channel
    this.signaling.on('signal', (msg) => {
      this.handleSignal(msg);
    });
    
    console.log(`🌐 Node ${this.nodeId} initialized`);
  }
  
  /**
   * Connect to a peer
   */
  async connect(peerId) {
    if (this.peers.has(peerId)) {
      return this.peers.get(peerId);
    }
    
    console.log(`🔗 Connecting to ${peerId}...`);
    
    const conn = new PeerConnection(this.nodeId, peerId, true);
    
    conn.on('connect', () => {
      console.log(`✅ Connected to ${peerId} (${conn.latency.toFixed(1)}ms)`);
      this.peers.set(peerId, conn);
      this.neighbors.add(peerId);
      this.networkMap.set(peerId, { latency: conn.latency, hops: 1 });
      this.emit('peer:connect', { peerId, latency: conn.latency });
    });
    
    conn.on('data', (data) => {
      this.handlePeerData(peerId, data);
    });
    
    conn.on('close', () => {
      this.peers.delete(peerId);
      this.neighbors.delete(peerId);
      this.emit('peer:disconnect', { peerId });
    });
    
    return conn;
  }
  
  /**
   * Handle incoming signal
   */
  handleSignal(msg) {
    if (msg.to && msg.to !== this.nodeId) return;
    
    // Handle connection request
    if (msg.type === 'offer') {
      this.handleOffer(msg);
    }
  }
  
  /**
   * Handle data from peer
   */
  handlePeerData(peerId, data) {
    // Flood prevention - check if we've seen this signal
    const signalId = data.id || JSON.stringify(data).slice(0, 16);
    
    if (this.seenSignals?.has(signalId)) {
      return; // Already processed
    }
    
    (this.seenSignals = this.seenSignals || new Set()).add(signalId);
    
    // Process based on type
    switch (data.type) {
      case 'signal':
        this.receiveSignal(data.payload);
        break;
      case 'gossip':
        this.handleGossip(peerId, data.payload);
        break;
      case 'topology':
        this.updateTopology(peerId, data.payload);
        break;
      default:
        this.emit('data', { from: peerId, data });
    }
    
    // Forward to other peers (gossip/flood)
    this.forwardToPeers(data, peerId);
  }
  
  /**
   * Emit a signal to the distributed network
   */
  emitSignal(signal) {
    const envelope = {
      type: 'signal',
      id: this.generateId(),
      origin: this.nodeId,
      timestamp: Date.now(),
      ttl: 10, // Time-to-live (hops)
      payload: signal
    };
    
    // Add to local signals
    this.localSignals.push(envelope);
    
    // Broadcast to all peers
    this.broadcastToPeers(envelope);
    
    // Emit locally
    this.emit('signal', signal);
    
    return envelope.id;
  }
  
  /**
   * Receive signal from network
   */
  receiveSignal(signal) {
    this.emit('signal:received', signal);
  }
  
  /**
   * Broadcast to all connected peers
   */
  broadcastToPeers(data, excludePeer = null) {
    for (const [peerId, conn] of this.peers) {
      if (peerId === excludePeer) continue;
      if (!conn.connected) continue;
      
      conn.send(data);
    }
  }
  
  /**
   * Forward to subset of peers (gossip protocol)
   */
  forwardToPeers(data, fromPeer) {
    if (data.ttl <= 0) return;
    
    data.ttl--;
    
    // Select random subset of peers (not the sender)
    const candidates = Array.from(this.peers.keys())
      .filter(id => id !== fromPeer);
    
    if (candidates.length === 0) return;
    
    // Gossip to 2 random peers (or all if less than 3)
    const gossipCount = Math.min(2, candidates.length);
    const selected = candidates
      .sort(() => Math.random() - 0.5)
      .slice(0, gossipCount);
    
    for (const peerId of selected) {
      const conn = this.peers.get(peerId);
      if (conn?.connected) {
        conn.send(data);
      }
    }
  }
  
  /**
   * Handle gossip message
   */
  handleGossip(fromPeer, gossip) {
    // Merge network maps
    for (const [nodeId, info] of Object.entries(gossip.network || {})) {
      if (nodeId === this.nodeId) continue;
      
      const current = this.networkMap.get(nodeId);
      const newHops = info.hops + 1;
      
      if (!current || newHops < current.hops) {
        this.networkMap.set(nodeId, {
          latency: info.latency + this.peers.get(fromPeer)?.latency || 0,
          hops: newHops,
          via: fromPeer,
          lastSeen: Date.now()
        });
      }
    }
  }
  
  /**
   * Start gossip protocol
   */
  startGossip() {
    this.gossipInterval = setInterval(() => {
      this.broadcastToPeers({
        type: 'gossip',
        payload: {
          nodeId: this.nodeId,
          network: Object.fromEntries(this.networkMap),
          timestamp: Date.now()
        }
      });
    }, this.gossipPeriod);
    
    console.log('📢 Gossip protocol started');
  }
  
  /**
   * Stop gossip
   */
  stopGossip() {
    if (this.gossipInterval) {
      clearInterval(this.gossipInterval);
    }
  }
  
  /**
   * Get network stats
   */
  getNetworkStats() {
    return {
      nodeId: this.nodeId,
      peers: this.peers.size,
      neighbors: Array.from(this.neighbors),
      networkSize: this.networkMap.size + 1, // +1 for self
      knownNodes: Array.from(this.networkMap.entries()).map(([id, info]) => ({
        id,
        hops: info.hops,
        latency: Math.round(info.latency)
      }))
    };
  }
  
  /**
   * Start the node
   */
  start() {
    this.startGossip();
    console.log(`🚀 Node ${this.nodeId} ONLINE`);
    this.emit('ready');
  }
  
  /**
   * Stop the node
   */
  stop() {
    this.stopGossip();
    for (const conn of this.peers.values()) {
      conn.close();
    }
    console.log(`🛑 Node ${this.nodeId} OFFLINE`);
  }
}

module.exports = { DistributedHighway, PeerConnection, SignalingChannel };
