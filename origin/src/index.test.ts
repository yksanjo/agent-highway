/**
 * Tests for Agent Highway Origin
 * Run with: npm test
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { BeaconCollector, SignalLien } from './index';
import type { Env } from './types';

// Mock Cloudflare Workers environment
const createMockEnv = (): Env => ({
  BEACON_COLLECTOR: {
    idFromName: vi.fn((name: string) => ({ id: name })) as unknown as DurableObjectNamespace<BeaconCollector>['idFromName'],
    get: vi.fn() as unknown as DurableObjectNamespace<BeaconCollector>['get'],
    newUniqueId: vi.fn() as unknown as DurableObjectNamespace<BeaconCollector>['newUniqueId'],
    idFromString: vi.fn() as unknown as DurableObjectNamespace<BeaconCollector>['idFromString'],
    getByName: vi.fn() as unknown as DurableObjectNamespace<BeaconCollector>['getByName'],
    jurisdiction: vi.fn() as unknown as DurableObjectNamespace<BeaconCollector>['jurisdiction']
  }
});

const createMockState = () => ({
  storage: {
    sql: {
      exec: vi.fn()
    }
  },
  acceptWebSocket: vi.fn(),
  getWebSockets: vi.fn(() => [])
});

describe('BeaconCollector', () => {
  let collector: BeaconCollector;
  let mockState: any;
  let mockEnv: any;

  beforeEach(() => {
    mockState = createMockState();
    mockEnv = createMockEnv();
    
    // Setup default SQL responses
    mockState.storage.sql.exec.mockImplementation((sql: string, ...params: any[]) => {
      // Return empty results by default
      return {
        one: () => null,
        [Symbol.iterator]: function* () { yield* []; }
      };
    });
    
    collector = new BeaconCollector(mockState, mockEnv);
  });

  describe('Schema Initialization', () => {
    it('should create liens table', () => {
      const calls = mockState.storage.sql.exec.mock.calls;
      const createLiensCall = calls.find((call: any) => 
        call[0].includes('CREATE TABLE IF NOT EXISTS liens')
      );
      expect(createLiensCall).toBeDefined();
    });

    it('should create agent_states table', () => {
      const calls = mockState.storage.sql.exec.mock.calls;
      const createStatesCall = calls.find((call: any) => 
        call[0].includes('CREATE TABLE IF NOT EXISTS agent_states')
      );
      expect(createStatesCall).toBeDefined();
    });

    it('should create tasks table', () => {
      const calls = mockState.storage.sql.exec.mock.calls;
      const createTasksCall = calls.find((call: any) => 
        call[0].includes('CREATE TABLE IF NOT EXISTS tasks')
      );
      expect(createTasksCall).toBeDefined();
    });

    it('should create indexes', () => {
      const calls = mockState.storage.sql.exec.mock.calls;
      const indexCalls = calls.filter((call: any) => 
        call[0].includes('CREATE INDEX')
      );
      expect(indexCalls.length).toBeGreaterThanOrEqual(5);
    });
  });

  describe('Lien Verification', () => {
    it('should reject liens with missing required fields', async () => {
      const invalidLien = {
        agent_id: '',
        event_type: 'birth',
        signature: 'test',
        timestamp: Date.now(),
        sequence: 1
      };

      const request = new Request('http://localhost/beacon', {
        method: 'POST',
        body: JSON.stringify(invalidLien)
      });

      const response = await collector.handleBeacon(request, {});
      expect(response.status).toBe(400);
    });

    it('should accept valid birth lien', async () => {
      const validLien: SignalLien = {
        agent_id: 'test-agent',
        agent_type: 'worker',
        timestamp: Date.now(),
        event_type: 'birth',
        sequence: 1,
        signature: 'test-sig',
        public_key: 'test-key',
        lane: 'default'
      };

      const request = new Request('http://localhost/beacon', {
        method: 'POST',
        body: JSON.stringify(validLien)
      });

      // Mock no existing agent
      mockState.storage.sql.exec.mockImplementation((sql: string, ...params: any[]) => {
        if (sql.includes('SELECT sequence FROM agent_states')) {
          throw new Error('Not found');
        }
        return { one: () => null, [Symbol.iterator]: function* () { yield* []; } };
      });

      const response = await collector.handleBeacon(request, {});
      expect(response.status).toBe(201);
    });

    it('should reject out-of-sequence liens', async () => {
      const lien: SignalLien = {
        agent_id: 'test-agent',
        agent_type: 'worker',
        timestamp: Date.now(),
        event_type: 'heartbeat',
        sequence: 1, // Should be 2
        signature: 'test-sig',
        public_key: 'test-key'
      };

      // Mock existing agent with sequence 2
      mockState.storage.sql.exec.mockImplementation((sql: string, ...params: any[]) => {
        if (sql.includes('SELECT sequence FROM agent_states')) {
          return { one: () => ({ sequence: 2 }) };
        }
        return { one: () => null, [Symbol.iterator]: function* () { yield* []; } };
      });

      const isValid = await collector.verifyLien(lien);
      expect(isValid).toBe(false);
    });

    it('should reject birth events with sequence != 1', async () => {
      const lien: SignalLien = {
        agent_id: 'new-agent',
        agent_type: 'worker',
        timestamp: Date.now(),
        event_type: 'birth',
        sequence: 5, // Should be 1
        signature: 'test-sig',
        public_key: 'test-key'
      };

      // Mock no existing agent
      mockState.storage.sql.exec.mockImplementation((sql: string, ...params: any[]) => {
        if (sql.includes('SELECT sequence FROM agent_states')) {
          throw new Error('Not found');
        }
        return { one: () => null, [Symbol.iterator]: function* () { yield* []; } };
      });

      const isValid = await collector.verifyLien(lien);
      expect(isValid).toBe(false);
    });
  });

  describe('Agent State Updates', () => {
    it('should update agent state on birth', async () => {
      const lien: SignalLien = {
        agent_id: 'test-agent',
        agent_type: 'worker',
        timestamp: Date.now(),
        event_type: 'birth',
        sequence: 1,
        signature: 'test-sig',
        public_key: 'test-key'
      };

      await collector.updateAgentState(lien);

      const calls = mockState.storage.sql.exec.mock.calls;
      const updateCall = calls.find((call: any) => 
        call[0].includes('INSERT INTO agent_states') && 
        call[1] === 'test-agent'
      );
      expect(updateCall).toBeDefined();
    });

    it('should mark agent as dead on death event', async () => {
      const lien: SignalLien = {
        agent_id: 'test-agent',
        agent_type: 'worker',
        timestamp: Date.now(),
        event_type: 'death',
        sequence: 10,
        signature: 'test-sig',
        public_key: 'test-key'
      };

      await collector.updateAgentState(lien);

      const calls = mockState.storage.sql.exec.mock.calls;
      const updateCall = calls.find((call: any) => 
        call[0].includes('INSERT INTO agent_states')
      );
      expect(updateCall).toBeDefined();
      expect(updateCall[5]).toBe('dead'); // status parameter
    });
  });

  describe('Task Tracking', () => {
    it('should create task on task_start', async () => {
      const lien: SignalLien = {
        agent_id: 'test-agent',
        agent_type: 'worker',
        timestamp: Date.now(),
        event_type: 'task_start',
        sequence: 5,
        signature: 'test-sig',
        public_key: 'test-key',
        task_id: 'task-001'
      };

      await collector.updateTask(lien);

      const calls = mockState.storage.sql.exec.mock.calls;
      const taskCall = calls.find((call: any) => 
        call[0].includes('INSERT INTO tasks')
      );
      expect(taskCall).toBeDefined();
      expect(taskCall[1]).toBe('task-001');
    });

    it('should complete task on task_complete', async () => {
      const lien: SignalLien = {
        agent_id: 'test-agent',
        agent_type: 'worker',
        timestamp: Date.now() + 5000,
        event_type: 'task_complete',
        sequence: 6,
        signature: 'test-sig',
        public_key: 'test-key',
        task_id: 'task-001'
      };

      // Mock existing task
      mockState.storage.sql.exec.mockImplementation((sql: string, ...params: any[]) => {
        if (sql.includes('SELECT started_at FROM tasks')) {
          return { one: () => ({ started_at: Date.now() }) };
        }
        return { one: () => null, [Symbol.iterator]: function* () { yield* []; } };
      });

      await collector.updateTask(lien);

      const calls = mockState.storage.sql.exec.mock.calls;
      const updateCall = calls.find((call: any) => 
        call[0].includes('UPDATE tasks SET')
      );
      expect(updateCall).toBeDefined();
    });
  });

  describe('Stats', () => {
    it('should return stats structure', () => {
      mockState.storage.sql.exec.mockImplementation((sql: string) => {
        if (sql.includes('COUNT(*)')) {
          return { one: () => ({ count: 5 }) };
        }
        return { one: () => null, [Symbol.iterator]: function* () { yield* []; } };
      });

      const stats = collector.getStats();
      
      expect(stats).toHaveProperty('total_liens');
      expect(stats).toHaveProperty('recent_liens_1h');
      expect(stats).toHaveProperty('agents');
      expect(stats.agents).toHaveProperty('active');
      expect(stats.agents).toHaveProperty('ghost');
      expect(stats.agents).toHaveProperty('dead');
      expect(stats.agents).toHaveProperty('total');
    });
  });

  describe('WebSocket', () => {
    it('should handle WebSocket upgrade', async () => {
      const request = new Request('http://localhost/beacon/ws', {
        headers: { 'Upgrade': 'websocket' }
      });

      // Mock WebSocketPair
      const mockServer = {
        accept: vi.fn(),
        send: vi.fn(),
        addEventListener: vi.fn()
      };
      const mockClient = {};
      
      (global as unknown as { WebSocketPair: typeof WebSocketPair }).WebSocketPair = vi.fn(() => ({
        0: mockClient as WebSocket,
        1: mockServer as unknown as WebSocket
      }));

      const response = await collector.handleWebSocket(request, {});
      
      expect(response.status).toBe(101);
      expect(mockServer.accept).toHaveBeenCalled();
      expect(mockState.acceptWebSocket).toHaveBeenCalledWith(mockServer);
    });
  });

  describe('API Endpoints', () => {
    it('should handle health check', async () => {
      const request = new Request('http://localhost/health');
      
      mockState.storage.sql.exec.mockImplementation((sql: string) => {
        if (sql.includes('COUNT(*)')) {
          return { one: () => ({ count: 0 }) };
        }
        return { one: () => null, [Symbol.iterator]: function* () { yield* []; } };
      });

      const response = await collector.fetch(request);
      const data = await response.json() as { status: string };
      
      expect(data.status).toBe('healthy');
    });

    it('should return 404 for unknown paths', async () => {
      const request = new Request('http://localhost/unknown');
      const response = await collector.fetch(request);
      
      expect(response.status).toBe(404);
    });

    it('should handle CORS preflight', async () => {
      const request = new Request('http://localhost/beacon', {
        method: 'OPTIONS'
      });
      
      const response = await collector.fetch(request);
      
      expect(response.status).toBe(200);
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });
  });
});

describe('Worker Router', () => {
  it('should serve dashboard at root', async () => {
    const { default: worker } = await import('./index');
    
    const request = new Request('http://localhost/');
    const env = createMockEnv();
    const ctx = {} as ExecutionContext;
    
    const response = await worker.fetch(request, env, ctx);
    
    expect(response.headers.get('Content-Type')).toBe('text/html');
  });
});
