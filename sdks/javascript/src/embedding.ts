/**
 * Simple embedding/vector operations
 */

import * as crypto from 'crypto';

/**
 * Create a simple embedding vector from text
 * Uses hash-based approach for deterministic results
 */
export function embed(text: string, dimensions: number = 64): number[] {
  // Create hash
  const hash = crypto.createHash('sha256').update(text).digest();

  // Convert to vector
  const vec: number[] = [];
  for (let i = 0; i < dimensions; i++) {
    const idx = i % hash.length;
    const val = hash[idx] / 255; // Normalize to 0-1
    vec.push(val - 0.5); // Center around 0
  }

  // Normalize to unit vector
  const norm = Math.sqrt(vec.reduce((sum, v) => sum + v * v, 0));
  if (norm > 0) {
    return vec.map((v) => v / norm);
  }

  return vec;
}

/**
 * Calculate cosine similarity between two vectors
 */
export function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) return 0;

  let dot = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }

  if (normA === 0 || normB === 0) return 0;

  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

/**
 * Calculate resonance match
 */
export function resonanceMatch(focus: number[], signalResonance: number[]): number {
  return cosineSimilarity(focus, signalResonance);
}
