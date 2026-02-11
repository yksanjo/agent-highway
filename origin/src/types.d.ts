/**
 * Type definitions for Agent Highway Origin
 */

declare module "cloudflare:workers" {
  export class DurableObject<T = unknown> {
    constructor(ctx: DurableObjectState, env: T);
    fetch(request: Request): Promise<Response>;
  }
  
  export interface DurableObjectState {
    storage: {
      sql: SqlStorage;
    };
    acceptWebSocket(ws: WebSocket): void;
    getWebSockets(): WebSocket[];
    waitUntil(promise: Promise<unknown>): void;
  }
  
  export interface SqlStorage {
    exec(sql: string, ...params: (string | number | null)[]): SqlCursor;
  }
  
  export interface SqlCursor {
    one(): unknown | null;
    [Symbol.iterator](): Iterator<unknown>;
  }
}

export interface Env {
  BEACON_COLLECTOR: DurableObjectNamespace<BeaconCollector>;
  ENVIRONMENT?: string;
  HEARTBEAT_TIMEOUT_MS?: string;
}

export interface SignalLien {
  agent_id: string;
  agent_type: string;
  timestamp: number;
  event_type: 'birth' | 'heartbeat' | 'task_start' | 'task_complete' | 'death' | 'handoff' | 'error';
  task_id?: string;
  parent_agent_id?: string;
  target_agent_id?: string;
  payload_hash?: string;
  sequence: number;
  signature: string;
  public_key: string;
  metadata?: Record<string, unknown>;
  lane?: string;
}

export interface AgentState {
  agent_id: string;
  agent_type: string;
  last_event: string;
  last_timestamp: number;
  status: 'active' | 'idle' | 'ghost' | 'dead';
  sequence: number;
  current_task?: string;
  birth_timestamp: number;
  heartbeat_interval?: number;
  expected_next_heartbeat?: number;
  lane?: string;
  lien_count: number;
}

export interface BeaconStats {
  total_liens: number;
  recent_liens_1h: number;
  agents: {
    active: number;
    ghost: number;
    dead: number;
    total: number;
  };
  lanes: Array<{
    lane: string;
    agent_count: number;
    active_count: number;
    last_activity: number;
  }>;
  recent_events: Array<{
    event_type: string;
    count: number;
  }>;
}
