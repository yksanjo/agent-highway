/**
 * WebSocket client for connecting to AgentHighway
 */

import WebSocket from 'ws';
import { Signal, SignalHandler, ConnectionHandler, ErrorHandler } from './types';

export class HighwayClient {
  private url: string;
  private ws: WebSocket | null = null;
  private connected = false;
  private handlers: Map<string, SignalHandler> = new Map();
  private onConnectHandler?: ConnectionHandler;
  private onDisconnectHandler?: ConnectionHandler;
  private onErrorHandler?: ErrorHandler;

  constructor(url: string = 'ws://localhost:9000') {
    this.url = url;
  }

  /**
   * Connect to the highway
   */
  async connect(): Promise<boolean> {
    return new Promise((resolve) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.on('open', () => {
          this.connected = true;
          console.log(`🔌 Connected to AgentHighway at ${this.url}`);
          this.onConnectHandler?.();
          resolve(true);
        });

        this.ws.on('message', (data) => {
          try {
            const message = JSON.parse(data.toString());
            this.handleMessage(message);
          } catch (e) {
            console.error('Failed to parse message:', e);
          }
        });

        this.ws.on('close', () => {
          this.connected = false;
          console.log('🔌 Disconnected from highway');
          this.onDisconnectHandler?.();
        });

        this.ws.on('error', (error) => {
          console.error('WebSocket error:', error);
          this.onErrorHandler?.(error);
          resolve(false);
        });
      } catch (error) {
        console.error('Connection failed:', error);
        resolve(false);
      }
    });
  }

  /**
   * Disconnect from highway
   */
  disconnect(): void {
    this.connected = false;
    this.ws?.close();
  }

  /**
   * Register event handler
   */
  on(event: string, handler: SignalHandler): void {
    this.handlers.set(event, handler);
  }

  onConnect(handler: ConnectionHandler): void {
    this.onConnectHandler = handler;
  }

  onDisconnect(handler: ConnectionHandler): void {
    this.onDisconnectHandler = handler;
  }

  onError(handler: ErrorHandler): void {
    this.onErrorHandler = handler;
  }

  /**
   * Register agent on highway
   */
  async registerAgent(agentConfig: {
    id: string;
    name: string;
    capabilities: string[];
    lane?: string;
  }): Promise<void> {
    this.send({
      action: 'register_agent',
      payload: agentConfig
    });
  }

  /**
   * Emit a signal
   */
  async emit(
    intent: string,
    options: {
      payload?: any;
      lane?: string;
      amplitude?: number;
      decay?: number;
    } = {}
  ): Promise<string> {
    const signalId = `sig-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

    this.send({
      action: 'emit',
      payload: {
        id: signalId,
        intent,
        ...options
      }
    });

    return signalId;
  }

  /**
   * Subscribe to events
   */
  async subscribe(events: string[]): Promise<void> {
    this.send({
      action: 'subscribe',
      events
    });
  }

  private handleMessage(message: any): void {
    const type = message.type;
    const handler = this.handlers.get(type);

    if (handler) {
      handler(message.payload);
    }
  }

  private send(data: any): void {
    if (this.ws && this.connected) {
      this.ws.send(JSON.stringify(data));
    }
  }
}
