/**
 * ForceAtlas2 iteration worker.
 *
 * Runs the layout off the UI thread. The typed-array protocol matches
 * `graphology-layout-forceatlas2`'s own worker: the supervisor owns the node
 * matrix and posts it back for one iteration at a time, which keeps the
 * layout responsive to pause/resume and lets the main thread decide how many
 * positions to apply per frame.
 *
 * Using the package's `iterate` function keeps numerical behaviour identical to
 * the synchronous layout while still running in a worker.
 */

import iterate from 'graphology-layout-forceatlas2/iterate';
import type { ForceAtlas2Settings } from 'graphology-layout-forceatlas2';

export interface Fa2WorkerStartMessage {
  type: 'start';
  nodes: ArrayBuffer;
  edges: ArrayBuffer;
  settings: ForceAtlas2Settings;
}

export interface Fa2WorkerStepMessage {
  type: 'step';
  nodes: ArrayBuffer;
}

export interface Fa2WorkerStopMessage {
  type: 'stop';
}

export type Fa2WorkerRequest = Fa2WorkerStartMessage | Fa2WorkerStepMessage | Fa2WorkerStopMessage;

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

let nodeMatrix: Float32Array | null = null;
let edgeMatrix: Float32Array | null = null;
let settings: ForceAtlas2Settings | null = null;
let iteration = 0;
let running = false;

/**
 * One ForceAtlas2 step. The package's iterate() is CommonJS, so it is reached
 * through the interop default that the bundler produces.
 */
function stepOnce(): void {
  if (!nodeMatrix || !edgeMatrix || !settings) return;
  iterate(settings, nodeMatrix, edgeMatrix);
  iteration += 1;
  const out = nodeMatrix;
  self.postMessage(
    { type: 'tick', nodes: out.buffer as ArrayBuffer, iteration } satisfies Fa2WorkerTick,
    [out.buffer as ArrayBuffer],
  );
}

function scheduleStep(): void {
  if (!running) return;
  // Yield back to the worker's message queue so `stop` is always observed.
  setTimeout(stepOnce, 0);
}

self.onmessage = (event: MessageEvent<Fa2WorkerRequest>) => {
  const message = event.data;
  switch (message.type) {
    case 'start': {
      nodeMatrix = new Float32Array(message.nodes);
      edgeMatrix = new Float32Array(message.edges);
      settings = message.settings;
      iteration = 0;
      running = true;
      scheduleStep();
      break;
    }
    case 'step': {
      if (!nodeMatrix || !edgeMatrix || !settings) return;
      // Reuse the matrix the main thread patched with new positions / pins.
      const incoming = new Float32Array(message.nodes);
      nodeMatrix = incoming;
      running = true;
      scheduleStep();
      break;
    }
    case 'stop': {
      running = false;
      break;
    }
  }
};
