import type Graph from 'graphology';
import type { ForceAtlas2Settings } from 'graphology-layout-forceatlas2';
import type { Fa2WorkerResponse } from './fa2.worker';

export const FA2_DEFAULTS: ForceAtlas2Settings = {
  linLogMode: false,
  outboundAttractionDistribution: false,
  adjustSizes: false,
  edgeWeightInfluence: 1,
  scalingRatio: 10,
  strongGravityMode: true,
  // ForceAtlas2's repulsion grows with node count. At gravity 1 a 1000-node
  // graph keeps expanding without bound, so the camera rescales forever and
  // nodes drift outside the viewport. Strong gravity pulls the layout to a
  // stable radius quickly, which is what a viewer actually wants.
  gravity: 20,
  // SlowDown damps the speed ramp; without it the first iterations fling nodes
  // far apart before attraction can pull them back.
  slowDown: 4,
  barnesHutOptimize: true,
  barnesHutTheta: 0.5,
};

/**
 * Settings that make the layout stable enough for incremental live updates.
 *
 * Overlap prevention costs a full O(n^2) pass per iteration, which is only
 * affordable on a small graph, so it is opt-in and auto-disabled above
 * `PREVENT_OVERLAP_MAX_NODES`.
 */
export const PREVENT_OVERLAP_MAX_NODES = 4000;

/** Stride of one node row in the worker's node matrix. */
const NODE_STRIDE = 10;
/** Stride of one edge row in the worker's edge matrix. */
const EDGE_STRIDE = 3;
/** Offsets inside a node row, matching `graphology-layout-forceatlas2`. */
const OFFSET_MASS = 6;
const OFFSET_FIXED = 9;

/**
 * Radius of the initial golden-angle seed spiral.
 *
 * ForceAtlas2's repulsion falls off as 1/d, so a tight seed makes the first
 * iterations explosive. A wide seed means the layout contracts smoothly into
 * its final shape instead of jumping on the first frame.
 *
 * The value is paired with the default `scalingRatio` of 1: a graph seeded at
 * this radius settles near a few thousand units across, which Sigma normalises
 * to fill the canvas at its default zoom.
 */
const SEED_SPREAD = 12;

/** Attributes this app writes onto graph nodes; the rest is server-provided. */
export interface LayoutNodeAttributes extends Record<string, unknown> {
  x: number;
  y: number;
  fixed?: boolean;
}

export interface LayoutControllerOptions {
  graph: Graph;
  settings?: Partial<ForceAtlas2Settings>;
  /** Invoked once per batch of applied positions. */
  onFrame: () => void;
  /** Invoked when the run state changes. */
  onRunningChange?: (running: boolean) => void;
}

/**
 * Supervises ForceAtlas2 running inside a Web Worker.
 *
 * The controller owns the node matrix so it can re-inject current positions
 * whenever the graph changes. That is what keeps an incremental SSE update from
 * exploding the layout: incoming nodes are seeded next to their neighbours and
 * every existing node keeps its coordinate instead of being re-seeded.
 *
 * The worker protocol is deliberately one iteration per message rather than a
 * `setInterval` loop inside the worker, so pause/resume and topology changes
 * are always observed between steps.
 */
export class ForceAtlas2Controller {
  private readonly graph: Graph;
  private worker: Worker | null = null;
  private settings: ForceAtlas2Settings = { ...FA2_DEFAULTS };
  private nodeMatrix: Float32Array | null = null;
  private edgeMatrix: Float32Array | null = null;
  private index: Record<string, number> = {};
  private order: string[] = [];
  private running = false;
  private iteration = 0;
  private framePending = false;
  private latestTick: ArrayBuffer | null = null;
  private workerStarted = false;
  private seeded = false;
  private destroyed = false;
  private readonly onFrame: () => void;
  private readonly onRunningChange?: (running: boolean) => void;

  constructor(options: LayoutControllerOptions) {
    this.graph = options.graph;
    this.onFrame = options.onFrame;
    this.onRunningChange = options.onRunningChange;
    this.applySettings(options.settings ?? {});
  }

  get isRunning(): boolean {
    return this.running;
  }

  get currentSettings(): ForceAtlas2Settings {
    return { ...this.settings };
  }

  get currentIteration(): number {
    return this.iteration;
  }

  setSettings(patch: Partial<ForceAtlas2Settings>): void {
    const next = { ...this.settings, ...patch };
    const changed = (Object.keys(next) as Array<keyof ForceAtlas2Settings>).some(
      (key) => next[key] !== this.settings[key],
    );
    if (!changed) return;
    this.applySettings(patch);
    // Settings are applied inside the worker's own loop, so it is restarted
    // rather than rebuilt here: the worker holds the live matrices.
    this.restart();
  }

  /** Re-seeds, rebuilds and hands fresh matrices to the worker. */
  private restart(): void {
    if (this.destroyed) return;
    this.rebuildMatrices();
    this.workerStarted = false;
    if (this.running) this.postStep();
  }

  resetLayout(): void {
    // Re-seed from scratch: drop the seeding guard and clear every position so
    // `seedPositions` lays out a fresh spiral instead of keeping the old one.
    this.seeded = false;
    this.graph.forEachNode((node) => {
      this.graph.setNodeAttribute(node, 'fixed', false);
      this.graph.setNodeAttribute(node, 'x', 0);
      this.graph.setNodeAttribute(node, 'y', 0);
    });
    this.rebuildMatrices();
    this.postStep();
  }

  start(): void {
    if (this.destroyed) return;
    // The run state is recorded even when the graph is still empty: Sigma is
    // mounted before the first payload arrives, and `sync` resumes from here
    // once nodes exist. Returning early *before* setting the flag left the
    // layout permanently paused with no visible cause.
    this.setRunning(true);
    if (this.graph.order === 0) return;
    this.ensureWorker();
    if (this.nodeMatrix === null) {
      this.rebuildMatrices();
    }
    this.postStep();
  }

  stop(): void {
    this.setRunning(false);
    this.worker?.postMessage({ type: 'stop' });
  }

  /**
   * Re-reads the graph after an incremental update.
   *
   * Positions already on the graph are re-injected into the worker, so a new
   * node arriving over SSE joins where it belongs instead of restarting the
   * whole simulation from scratch.
   */
  sync(): void {
    if (this.graph.order === 0) return;
    if (!this.running) return;
    this.ensureWorker();
    this.rebuildMatrices();
    this.postStep();
  }

  /** Pins a node in place (drag) or releases it. */
  setFixed(node: string, fixed: boolean): void {
    if (!this.graph.hasNode(node)) return;
    this.graph.setNodeAttribute(node, 'fixed', fixed);
    const matrixIndex = this.index[node];
    if (matrixIndex === undefined) return;
    // The worker's matrix is authoritative, so a drag is written there too.
    // Otherwise the next iteration would snap the node straight back.
    if (this.nodeMatrix) this.nodeMatrix[matrixIndex + OFFSET_FIXED] = fixed ? 1 : 0;
    this.postStep();
  }

  destroy(): void {
    this.destroyed = true;
    this.setRunning(false);
    this.worker?.terminate();
    this.worker = null;
    this.workerStarted = false;
    this.nodeMatrix = null;
    this.edgeMatrix = null;
    this.latestTick = null;
    this.index = {};
    this.order = [];
  }

  private applySettings(patch: Partial<ForceAtlas2Settings>): void {
    this.settings = { ...FA2_DEFAULTS, ...patch };
    if (!this.canPreventOverlap()) {
      this.settings.adjustSizes = false;
    }
  }

  /**
   * Overlap prevention is quadratic per iteration, so it is capped rather than
   * silently freezing the browser on a large graph.
   */
  private canPreventOverlap(): boolean {
    return this.settings.adjustSizes === true && this.graph.order <= PREVENT_OVERLAP_MAX_NODES;
  }

  private setRunning(running: boolean): void {
    if (this.running === running) return;
    this.running = running;
    this.onRunningChange?.(running);
  }

  private ensureWorker(): Worker {
    if (this.worker) return this.worker;
    const worker = new Worker(new URL('./fa2.worker.ts', import.meta.url), { type: 'module' });
    worker.onmessage = (event: MessageEvent<Fa2WorkerResponse>) => {
      const message = event.data;
      if (message.type !== 'tick') return;
      this.iteration = message.iteration;
      this.applyPositions(message.nodes);
      this.onFrame();
    };
    worker.onerror = () => {
      // A worker crash must not leave the UI in a "running" lie.
      this.setRunning(false);
    };
    this.worker = worker;
    return worker;
  }

  /**
   * Writes a tick's positions onto the graph, at most once per animation frame
   * so a fast worker cannot starve the render loop.
   *
   * The tick is queued rather than applied inline: several ticks may arrive
   * between two frames, and only the newest matters.
   */
  private applyPositions(buffer: ArrayBuffer): void {
    this.latestTick = buffer;
    if (this.framePending) return;
    this.framePending = true;
    requestAnimationFrame(() => {
      this.framePending = false;
      if (this.destroyed) return;
      const pending = this.latestTick;
      this.latestTick = null;
      if (pending) this.writePositions(new Float32Array(pending));
      this.onFrame();
    });
  }

  private writePositions(matrix: Float32Array): void {
    for (const node of this.order) {
      const i = this.index[node];
      if (i === undefined || !this.graph.hasNode(node)) continue;
      const x = matrix[i];
      const y = matrix[i + 1];
      // NaN guard: a zero-mass graph or bad weights must not poison the canvas.
      if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
      this.graph.setNodeAttribute(node, 'x', x);
      this.graph.setNodeAttribute(node, 'y', y);
    }
  }

  /**
   * Hands the current matrices to the worker.
   *
   * `start` is only ever sent once per worker lifetime: the worker drives itself
   * from there. Later changes go through `sync`, which carries new positions
   * only, so the simulation is never restarted mid-flight.
   */
  private postStep(): void {
    if (!this.nodeMatrix || !this.edgeMatrix || !this.worker) return;
    if (this.workerStarted) {
      this.worker.postMessage(
        { type: 'sync', nodes: this.nodeMatrix.slice().buffer as ArrayBuffer },
      );
    } else {
      this.workerStarted = true;
      this.worker.postMessage(
        {
          type: 'start',
          nodes: this.nodeMatrix.buffer as ArrayBuffer,
          edges: this.edgeMatrix.buffer as ArrayBuffer,
          settings: this.settings,
        },
        [this.nodeMatrix.buffer as ArrayBuffer, this.edgeMatrix.buffer as ArrayBuffer],
      );
    }
  }

  /**
   * Seeds any node that has no position yet.
   *
   * On the first pass every node is placed on a golden-angle spiral. That gives
   * a deterministic, reproducible initial state that already covers an area,
   * instead of the severe clumping a uniform random seed produces — clumped
   * seeds make the first repulsion steps enormous and the graph visibly jumps.
   *
   * On later passes only genuinely new nodes are placed, next to the centroid of
   * their already-positioned neighbours.
   */
  private seedPositions(): void {
    if (this.seeded) return;
    this.seeded = true;
    let index = 0;
    const total = Math.max(1, this.graph.order);
    this.graph.forEachNode((node) => {
      // radius ~ sqrt(i/n) * SPREAD: uniform area density, so no node starts on
      // top of another.
      const angle = index * 2.399963229728653;
      const radius = Math.sqrt(index / total) * SEED_SPREAD;
      this.graph.setNodeAttribute(node, 'x', Math.cos(angle) * radius);
      this.graph.setNodeAttribute(node, 'y', Math.sin(angle) * radius);
      index += 1;
    });
  }

  /** Seeds nodes added after the first pass next to their neighbours. */
  private seedIncremental(): void {
    const pending: string[] = [];
    this.graph.forEachNode((node, attributes) => {
      // A new node is added with no position at all, so a non-finite or
      // exactly-zero coordinate is the signal. Resetting the layout also zeroes
      // every node, but that path clears `seeded` first, so it takes the spiral.
      if (!Number.isFinite(attributes.x) || !Number.isFinite(attributes.y)) pending.push(node);
      else if (attributes.x === 0 && attributes.y === 0) pending.push(node);
    });
    if (pending.length === 0) return;

    const fresh = new Set(pending);
    for (const node of pending) {
      let sumX = 0;
      let sumY = 0;
      let count = 0;
      this.graph.forEachNeighbor(node, (neighbor) => {
        if (fresh.has(neighbor)) return;
        const attributes = this.graph.getNodeAttributes(neighbor);
        if (!Number.isFinite(attributes.x) || !Number.isFinite(attributes.y)) return;
        sumX += attributes.x;
        sumY += attributes.y;
        count += 1;
      });
      // Jitter is a fraction of the seed spread, so an isolated new node lands
      // in a plausible spot instead of exactly on the origin.
      const jitter = SEED_SPREAD * 0.02;
      const baseX = count > 0 ? sumX / count : (Math.random() - 0.5) * SEED_SPREAD;
      const baseY = count > 0 ? sumY / count : (Math.random() - 0.5) * SEED_SPREAD;
      this.graph.setNodeAttribute(node, 'x', baseX + (Math.random() - 0.5) * jitter);
      this.graph.setNodeAttribute(node, 'y', baseY + (Math.random() - 0.5) * jitter);
    }
  }

  private rebuildMatrices(): void {
    const order = this.graph.order;
    const size = this.graph.size;

    this.seedPositions();
    this.seedIncremental();

    const nodes = new Float32Array(order * NODE_STRIDE);
    const edges = new Float32Array(size * EDGE_STRIDE);
    const index: Record<string, number> = {};

    let j = 0;
    this.graph.forEachNode((node, attributes) => {
      index[node] = j;
      nodes[j] = Number.isFinite(attributes.x) ? attributes.x : 0;
      nodes[j + 1] = Number.isFinite(attributes.y) ? attributes.y : 0;
      nodes[j + 2] = 0; // dx
      nodes[j + 3] = 0; // dy
      nodes[j + 4] = 0; // old dx
      nodes[j + 5] = 0; // old dy
      nodes[j + 6] = 1; // mass
      nodes[j + 7] = 1; // convergence
      nodes[j + 8] = 1; // size
      nodes[j + 9] = attributes.fixed === true ? 1 : 0;
      j += NODE_STRIDE;
    });

    let e = 0;
    this.graph.forEachEdge((_edge, attributes, source, target) => {
      const sourceIndex = index[source];
      const targetIndex = index[target];
      if (sourceIndex === undefined || targetIndex === undefined) return;
      const weight =
        typeof attributes.weight === 'number' && Number.isFinite(attributes.weight)
          ? attributes.weight
          : 1;
      nodes[sourceIndex + OFFSET_MASS] += weight;
      nodes[targetIndex + OFFSET_MASS] += weight;
      edges[e] = sourceIndex;
      edges[e + 1] = targetIndex;
      edges[e + 2] = weight;
      e += EDGE_STRIDE;
    });

    this.nodeMatrix = nodes;
    this.edgeMatrix = edges;
    this.index = index;
    this.order = this.graph.nodes();
  }
}