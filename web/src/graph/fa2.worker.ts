/**
 * ForceAtlas2 iteration worker.
 *
 * Runs the layout off the UI thread so a 1000-node graph never blocks a frame.
 *
 * The worker owns the simulation and drives itself: it iterates, posts a tick,
 * and schedules the next iteration. The main thread only ever *applies*
 * positions and can interrupt between iterations with `stop` (pause) or
 * `sync` (the topology changed and the matrices must be rebuilt).
 *
 * The previous design — one iteration per request/response round trip — looked
 * more symmetric, but the main thread coalesces ticks into animation frames, so
 * it could only ever apply the newest tick. Any tick arriving while a frame was
 * already scheduled had its "run the next iteration" continuation dropped,
 * which silently stopped the layout after a single step.
 *
 * Numerical behaviour is identical to the synchronous layout because
 * `graphology-layout-forceatlas2/iterate` is the same function.
 */

import iterate from 'graphology-layout-forceatlas2/iterate';
import type { ForceAtlas2Settings } from 'graphology-layout-forceatlas2';

/** Full matrices and settings: (re)start the simulation from scratch. */
export interface Fa2WorkerStartMessage {
  type: 'start';
  nodes: ArrayBuffer;
  edges: ArrayBuffer;
  settings: ForceAtlas2Settings;
}

/** New node positions for the same topology; the simulation continues. */
export interface Fa2WorkerSyncMessage {
  type: 'sync';
  nodes: ArrayBuffer;
}

export interface Fa2WorkerStopMessage {
  type: 'stop';
}

export type Fa2WorkerRequest =
  | Fa2WorkerStartMessage
  | Fa2WorkerSyncMessage
  | Fa2WorkerStopMessage;

export interface Fa2WorkerTick {
  type: 'tick';
  nodes: ArrayBuffer;
  iteration: number;
}

export interface Fa2WorkerStopped {
  type: 'stopped';
}

export type Fa2WorkerResponse = Fa2WorkerTick | Fa2WorkerStopped;

const self = globalThis as unknown as DedicatedWorkerGlobalScope;

/**
 * Minimum wall-clock gap between two iterations.
 *
 * Faster than this produces positions nobody can see: the main thread coalesces
 * ticks into animation frames, so extra iterations would only burn CPU on the
 * worker and queue frames it will throw away.
 */
const MIN_ITERATION_INTERVAL_MS = 16;

let nodeMatrix: Float32Array | null = null;
let edgeMatrix: Float32Array | null = null;
let settings: ForceAtlas2Settings | null = null;
let iteration = 0;
let running = false;
let lastIterationAt = 0;

function step(): void {
  if (!running || !nodeMatrix || !edgeMatrix || !settings) return;

  // A topological edit always takes effect on the next iteration.
  const now = Date.now();
  const elapsed = now - lastIterationAt;
  if (elapsed < MIN_ITERATION_INTERVAL_MS) {
    setTimeout(step, MIN_ITERATION_INTERVAL_MS - elapsed);
    return;
  }
  lastIterationAt = now;

  iterate(settings, nodeMatrix, edgeMatrix);
  iteration += 1;

  // The matrix is not transferred: the worker keeps running from it, so the
  // main thread receives a structured-clone copy instead of taking ownership.
  self.postMessage({
    type: 'tick',
    nodes: nodeMatrix.slice().buffer,
    iteration,
  } satisfies Fa2WorkerTick);

  // `setTimeout` rather than a direct call, so a `stop` or `sync` message is
  // always observed before the next iteration begins.
  setTimeout(step, 0);
}

self.onmessage = (event: MessageEvent<Fa2WorkerRequest>) => {
  const message = event.data;
  switch (message.type) {
    case 'start':
      nodeMatrix = new Float32Array(message.nodes);
      edgeMatrix = new Float32Array(message.edges);
      settings = message.settings;
      iteration = 0;
      running = true;
      lastIterationAt = 0;
      setTimeout(step, 0);
      break;
    case 'sync':
      // Positions computed on the main thread (a drag, a pin) win over the
      // worker's own copy; the topology the worker holds stays authoritative.
      if (nodeMatrix) nodeMatrix = new Float32Array(message.nodes);
      break;
    case 'stop':
      running = false;
      self.postMessage({ type: 'stopped' } satisfies Fa2WorkerStopped);
      break;
  }
};