/**
 * Type definitions for AgentHighway SDK
 */

export enum Lane {
  CRITICAL = 'critical',
  STANDARD = 'standard',
  BACKGROUND = 'background'
}

export interface Signal {
  id?: string;
  intent: string;
  emitter: string;
  lane: Lane | string;
  payload?: any;
  amplitude?: number;
  decay?: number;
  timestamp?: number;
}

export interface AgentConfig {
  id?: string;
  name: string;
  capabilities: string[];
  preferredLane?: Lane | string;
  metadata?: Record<string, any>;
}

export interface EmitOptions {
  lane?: Lane | string;
  amplitude?: number;
  decay?: number;
  payload?: any;
}

export interface SenseOptions {
  threshold?: number;
  maxResults?: number;
  lanes?: (Lane | string)[];
}

export type SignalHandler = (signal: Signal) => void;
export type ConnectionHandler = () => void;
export type ErrorHandler = (error: Error) => void;
