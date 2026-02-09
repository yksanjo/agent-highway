/**
 * HighwayAgent - Base class for AI agents
 */

import { HighwayClient } from './client';
import { Signal, AgentConfig, EmitOptions, SenseOptions, Lane } from './types';

export class HighwayAgent {
  private config: AgentConfig;
  private client: HighwayClient;
  private connected = false;
  private signalQueue: Signal[] = [];
  private signalHandler?: (signal: Signal) => void;

  constructor(config: AgentConfig) {
    this.config = {
      preferredLane: Lane.STANDARD,
      ...config
    };

    this.config.id = config.id || config.name.toLowerCase().replace(/\s+/g, '-');
    this.client = new HighwayClient();
  }

  /**
   * Connect to the highway
   */
  async connect(url?: string): Promise<boolean> {
    if (url) {
      this.client = new HighwayClient(url);
    }

    const success = await this.client.connect();
    if (!success) return false;

    // Register agent
    await this.client.registerAgent({
      id: this.config.id!,
      name: this.config.name,
      capabilities: this.config.capabilities,
      lane: this.config.preferredLane
    });

    // Setup signal handler
    this.client.on('signal', (payload) => {
      const signal = payload as Signal;
      this.signalQueue.push(signal);
      this.signalHandler?.(signal);
    });

    this.connected = true;
    console.log(`🤖 Agent ${this.config.name} connected`);
    return true;
  }

  /**
   * Disconnect from highway
   */
  disconnect(): void {
    this.client.disconnect();
    this.connected = false;
  }

  /**
   * Emit a signal
   */
  async emit(intent: string, options: EmitOptions = {}): Promise<string> {
    if (!this.connected) {
      throw new Error('Agent not connected. Call connect() first.');
    }

    return this.client.emit(intent, {
      lane: options.lane || this.config.preferredLane,
      ...options
    });
  }

  /**
   * Register signal handler
   */
  onSignal(handler: (signal: Signal) => void): void {
    this.signalHandler = handler;
  }

  /**
   * Sense signals from queue
   */
  sense(options: SenseOptions = {}): Signal[] {
    const threshold = options.threshold || 0;
    const maxResults = options.maxResults || 10;

    // Get and clear queue
    const signals = this.signalQueue.splice(0, maxResults);
    return signals;
  }

  /**
   * Get agent ID
   */
  get id(): string {
    return this.config.id!;
  }

  /**
   * Get agent name
   */
  get name(): string {
    return this.config.name;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connected;
  }
}
