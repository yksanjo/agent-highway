/**
 * AgentHighway JavaScript/TypeScript SDK
 * 
 * Connect any JS/TS AI agent to the signal highway.
 * 
 * @example
 * ```typescript
 * import { HighwayAgent } from '@agenthighway/sdk';
 * 
 * const agent = new HighwayAgent({
 *   name: "MyBot",
 *   capabilities: ["coding", "analysis"]
 * });
 * 
 * await agent.connect("ws://localhost:9000");
 * 
 * // Emit a signal
 * await agent.emit("need help with auth", { lane: "critical" });
 * 
 * // Handle incoming signals
 * agent.onSignal((signal) => {
 *   console.log(`Received: ${signal.intent}`);
 * });
 * ```
 */

export { HighwayClient } from './client';
export { HighwayAgent } from './agent';
export { Signal, Lane } from './types';
export { embed, cosineSimilarity } from './embedding';

// Version
export const VERSION = '1.0.0';
