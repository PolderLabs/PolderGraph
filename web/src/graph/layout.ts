import type Graph from 'graphology';
import type { ForceAtlas2Settings } from 'graphology-layout-forceatlas2';
import type { Fa2WorkerResponse } from './fa2.worker';

export const FA2_DEFAULTS: ForceAtlas2Settings = {
  linLogMode: false,
  outboundAttractionDistribution: false,
  adjustSizes: false,
  edgeWeightInfluence: 1,
  scalingRatio: 1,
  strongGravityMode: false,
  gravity: 1,
  slowDown: 1,
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

const PPN = 10;
const PPE = 3;

/** Attributes this app writes onto graph nodes; the rest is server-provided. */
export interface LayoutNodeAttributes extends Record<string, unknown> {
  x: number;
  y: number;
  size: number;
  fixed?: boolean;
  pgLayoutVersion?: number;
}

export interface LayoutControllerOptions {
  graph: Graph;
  settings?: Partial<ForceAtlas2Settings>;
  /** Invoked once per batch of applied positions. */
  onFrame: () => void;
  /** Invoked when the run state changes. */
  onRunningChange?: (running: boolean) => void;
  /** Fraction of nodes whose position is preserved across a full rebuild. */
  stablePositionRatio?: number;
}

/** Bumped whenever positions are rebuilt from scratch (view switch, reset). */
const LAYOUT_VERSION = 1;

/**
 * Supervises ForceAtlas2 running inside a Web Worker.
 *
 * The controller owns the node matrix so it can re-inject current positions
 * when the graph changes. That is what keeps the layout from exploding on
 * incremental SSE updates: incoming nodes are seeded near their neighbours and
 * existing nodes keep their coordinates instead of being re-seeded randomly.
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
  private pendingFrame = false;
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
    this.applySettings(patch);
    if (this.running) {
      // Settings are read on every iteration; no restart required.
      this.rebuildMatrices();
      this.postStep();
    }
  }

  resetLayout(): void {
    this.reseedAll();
    this.rebuildMatrices();
    this.postStep();
  }

  start(): void {
    if (this.destroyed || this.graph.order === 0) return;
    this.ensureWorker();
    if (this.nodeMatrix === null) {
      this.rebuildMatrices();
    }
    this.setRunning(true);
    this.postStep();
  }

  stop(): void {
    this.setRunning(false);
    this.worker?.postMessage({ type: 'stop' });
  }

  /** Re-reads the graph, keeping positions for nodes that already have them. */
  sync(): void {
    this.rebuildMatrices();
    if (this.running) this.postStep();
  }

  /**
   * Pins a node in place (drag) or releases it.
   *
   * The matrix stores `fixed` at offset 9, so pinning is applied directly
   * rather than waiting for a full rebuild.
   */
  setFixed(node: string, fixed: boolean): void {
    if (!this.graph.hasNode(node)) return;
    this.graph.setNodeAttribute(node, 'fixed', fixed);
    const matrixIndex = this.index[node];
    if (matrixIndex !== undefined && this.nodeMatrix) {
      this.nodeMatrix[matrixIndex + 9] = fixed ? 1 : 0;
    }
  }

  destroy(): void {
    this.destroyed = true;
    this.setRunning(false);
    this.worker?.terminate();
    this.worker = null;
    this.nodeMatrix = null;
    this.edgeMatrix = null;
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
      if (message.type === 'tick') {
        this.nodeMatrix = new Float32Array(message.nodes);
        this.iteration = message.iteration;
        this.flushPositions();
        if (this.running) this.postStep();
      }
    };
    worker.onerror = () => {
      // A worker crash must not leave the UI in a "running" lie.
      this.setRunning(false);
    };
    this.worker = worker;
    return worker;
  }

  /**
   * Applies the latest matrix back onto the graph, at most once per frame so a
   * fast worker cannot starve the render loop.
   */
  private flushPositions(): void {
    if (this.pendingFrame || !this.nodeMatrix) return;
    this.pendingFrame = true;
    const apply = () => {
      this.pendingFrame = false;
      if (this.destroyed) return;
      this.applyPositions();
      this.onFrame();
    };
    if (typeof requestAnimationFrame === 'function') {
      requestAnimationFrame(apply);
    } else {
      setTimeout(apply, 0);
    }
  }

  private applyPositions(): void {
    const matrix = this.nodeMatrix;
    if (!matrix) return;
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

  private postStep(): void {
    if (!this.nodeMatrix || !this.edgeMatrix || !this.worker) return;
    // Hand the buffers over; they are transferred and re-created each tick.
    this.worker.postMessage(
      { type: 'step', nodes: this.nodeMatrix.buffer },
      [this.nodeMatrix.buffer as ArrayBuffer],
    );
  }

  private reseedAll(): void {
    this.graph.forEachNode((node, attr) => {
      this.graph.setNodeAttribute(node, 'x', Math.random());
      this.graph.setNodeAttribute(node, 'y', Math.random());
      this.graph.setNodeAttribute(node, 'pgLayoutVersion', LAYOUT_VERSION);
      if (attr.fixed) this.graph.setNodeAttribute(node, 'fixed', false);
    });
  }

  /**
   * Seeds new nodes next to their neighbours so incremental additions do not
   * land in a random corner and yank the layout around.
   */
  private seedIncremental(): void {
    const pending: string[] = [];
    this.graph.forEachNode((node, attr) => {
      if (!Number.isFinite(attr.x) || !Number.isFinite(attr.y)) pending.push(node);
    });
    if (pending.length === 0) return;

    const fresh = new Set(pending);
    for (const node of pending) {
      let sx = 0;
      let sy = 0;
      let count = 0;
      this.graph.forEachNeighbor(node, (neighbor) => {
        const attr = this.graph.getNodeAttributes(neighbor);
        if (fresh.has(neighbor)) return;
        if (!Number.isFinite(attr.x) || !Number.isFinite(attr.y)) return;
        sx += attr.x;
        sy += attr.y;
        count += 1;
      });
      if (count > 0) {
        this.graph.setNodeAttribute(node, 'x', sx / count + (Math.random() - 0.5) * 0.02);
        this.graph.setNodeAttribute(node, 'y', sy / count + (Math.random() - 0.5) * 0.02);
      } else {
        this.graph.setNodeAttribute(node, 'x', Math.random());
        this.graph.setNodeAttribute(node, 'y', Math.random());
      }
      this.graph.setNodeAttribute(node, 'pgLayoutVersion', LAYOUT_VERSION);
    }
  }

  private rebuildMatrices(): void {
    const order = this.graph.order;
    const size = this.graph.size;

    // Preserve existing coordinates before anything is rebuilt.
    this.seedIncremental();

    const nodes = new Float32Array(order * PPN);
    const edges = new Float32Array(size * PPE);
    const index: Record<string, number> = {};

    let j = 0;
    this.graph.forEachNode((node, attr) => {
      index[node] = j;
      nodes[j] = Number.isFinite(attr.x) ? attr.x : Math.random();
      nodes[j + 1] = Number.isFinite(attr.y) ? attr.y : Math.random();
      nodes[j + 2] = 0; // dx
      nodes[j + 3] = 0; // dy
      nodes[j + 4] = 0; // old dx
      nodes[j + 5] = 0; // old dy
      nodes[j + 6] = 1; // mass
      nodes[j + 7] = 1; // convergence
      nodes[j + 8] = typeof attr.size === 'number' ? attr.size : 1;
      nodes[j + 9] = attr.fixed ? 1 : 0;
      j += PPN;
    });

    let e = 0;
    this.graph.forEachEdge((_edge, attrs, source, target) => {
      const si = index[source];
      const ti = index[target];
      if (si === undefined || ti === undefined) return;
      const weight = typeof attrs.weight === 'number' && Number.isFinite(attrs.weight)
        ? attrs.weight
        : 1;
      nodes[si + 6] += weight;
      nodes[ti + 6] += weight;
      edges[e] = si;
      edges[e + 1] = ti;
      edges[e + 2] = weight;
      e += PPE;
    });

    this.nodeMatrix = nodes;
    this.edgeMatrix = edges;
    this.index = index;
    this.order = this.graph.nodes();
  }

  /** Rebuild and hand the matrices to a fresh worker. */
  restart(): void {
    if (this.destroyed) return;
    this.rebuildMatrices();
    if (!this.running) return;
    this.ensureWorker();
    this.postStep();
  }

  get edgeWeightOf(): (edge: string) => number {
    return (edge: string) => {
      const attrs = this.graph.getEdgeAttributes(edge);
      return typeof attrs.weight === 'number' && Number.isFinite(attrs.weight) ? attrs.weight : 1;
    };
  }
}
