import type Graph from 'graphology';
import type {
  LayoutRequest,
  LayoutResponse,
  LayoutSettings,
} from './force.worker';
import { DEFAULT_SETTINGS } from './force.worker';

/**
 * Supervises the graph layout running inside a Web Worker.
 *
 * The controller owns the packed node buffer so it can push current positions
 * back whenever the graph changes. An incremental update therefore joins the
 * existing layout instead of restarting it.
 *
 * The worker decides when the layout is finished (its forces decay to zero);
 * this class just relays positions and reports the state change so the UI can
 * stop animating.
 */

/** Attributes this app writes onto graph nodes; the rest is server-provided. */
export interface LayoutNodeAttributes extends Record<string, unknown> {
  x: number;
  y: number;
  fixed?: boolean;
  size?: number;
}

/** Entries per node in the position buffer: x, y. */
const POSITION_STRIDE = 2;

export interface LayoutControllerOptions {
  graph: Graph;
  settings?: Partial<LayoutSettings>;
  /** Invoked once per batch of applied positions. */
  onFrame: () => void;
  /** Invoked when the run state changes, including when the layout settles. */
  onRunningChange?: (running: boolean) => void;
}

export class LayoutController {
  private readonly graph: Graph;
  private worker: Worker | null = null;
  private settings: LayoutSettings = { ...DEFAULT_SETTINGS };
  private order: string[] = [];
  private index: Record<string, number> = {};
  private running = false;
  private tickCount = 0;
  private alpha = 1;
  private framePending = false;
  private pending: Float32Array | null = null;
  private destroyed = false;
  private readonly onFrame: () => void;
  private readonly onRunningChange?: (running: boolean) => void;

  constructor(options: LayoutControllerOptions) {
    this.graph = options.graph;
    this.onFrame = options.onFrame;
    this.onRunningChange = options.onRunningChange;
    this.settings = { ...DEFAULT_SETTINGS, ...(options.settings ?? {}) };
  }

  get isRunning(): boolean {
    return this.running;
  }

  get currentSettings(): LayoutSettings {
    return { ...this.settings };
  }

  get currentTick(): number {
    return this.tickCount;
  }

  /** Simulation energy remaining; falls to zero as the layout settles. */
  get currentAlpha(): number {
    return this.alpha;
  }

  setSettings(patch: Partial<LayoutSettings>): void {
    const next = { ...this.settings, ...patch };
    const changed =
      next.chargeStrength !== this.settings.chargeStrength ||
      next.linkStrength !== this.settings.linkStrength ||
      next.linkDistance !== this.settings.linkDistance ||
      next.centerStrength !== this.settings.centerStrength ||
      next.velocityDecay !== this.settings.velocityDecay ||
      next.collisionPadding !== this.settings.collisionPadding;
    this.settings = next;
    if (changed && this.worker) {
      // Settings only take effect on a fresh run; restart so the viewer sees
      // the change rather than a layout computed with stale constants.
      this.restart();
    }
  }

  private setRunning(running: boolean): void {
    if (this.running === running) return;
    this.running = running;
    this.onRunningChange?.(running);
  }

  private ensureWorker(): Worker {
    if (this.worker) return this.worker;
    const worker = new Worker(new URL('./force.worker.ts', import.meta.url), { type: 'module' });
    worker.onmessage = (event: MessageEvent<LayoutResponse>) => {
      const message = event.data;
      if (message.type === 'settled') {
        // Forces have decayed to zero: the layout is at rest and the canvas
        // stops being redrawn, so the viewer can read and click it.
        this.setRunning(false);
        return;
      }
      this.tickCount = message.tick;
      this.alpha = message.alpha;
      this.applyPositions(message.positions);
    };
    worker.onerror = () => {
      this.setRunning(false);
    };
    this.worker = worker;
    return worker;
  }

  /**
   * Writes a tick's positions onto the graph, at most once per animation frame.
   *
   * Ticks are queued rather than applied inline: the worker can produce several
   * between two frames, and only the newest matters.
   */
  private applyPositions(buffer: Float32Array): void {
    this.pending = buffer;
    if (this.framePending) return;
    this.framePending = true;
    requestAnimationFrame(() => {
      this.framePending = false;
      if (this.destroyed) return;
      const positions = this.pending;
      this.pending = null;
      if (positions) this.writePositions(positions);
      this.onFrame();
    });
  }

  private writePositions(buffer: Float32Array): void {
    const ids = this.order;
    const limit = Math.min(ids.length, Math.floor(buffer.length / POSITION_STRIDE));
    for (let i = 0; i < limit; i += 1) {
      const id = ids[i];
      if (!this.graph.hasNode(id)) continue;
      const x = buffer[i * POSITION_STRIDE];
      const y = buffer[i * POSITION_STRIDE + 1];
      // NaN guard: a degenerate graph must not poison the canvas.
      if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
      this.graph.setNodeAttribute(id, 'x', x);
      this.graph.setNodeAttribute(id, 'y', y);
    }
  }

  /**
   * Snapshots the graph as an id table plus typed arrays indexed by it.
   *
   * The id table is what keeps positions attached to the right node: a worker
   * cannot receive strings inside a typed array, so identity travels separately.
   */
  private snapshot(): {
    ids: string[];
    radii: Float32Array;
    positions: Float32Array;
    edges: Int32Array;
  } {
    this.order = [];
    this.index = {};
    const radii: number[] = [];
    const positions: number[] = [];
    this.graph.forEachNode((node, attributes) => {
      this.index[node] = this.order.length;
      this.order.push(node);
      const size = Number(attributes.size ?? 5);
      radii.push(Number.isFinite(size) && size > 0 ? size : 5);
      positions.push(Number(attributes.x ?? 0), Number(attributes.y ?? 0));
    });
    return {
      ids: this.order,
      radii: new Float32Array(radii),
      positions: new Float32Array(positions),
      edges: this.packEdges(),
    };
  }

  private packEdges(): Int32Array {
    const pairs: number[] = [];
    this.graph.forEachEdge((_edge, attrs, source, target) => {
      const sourceIndex = this.index[source];
      const targetIndex = this.index[target];
      if (sourceIndex === undefined || targetIndex === undefined) return;
      const weight = Number((attrs as { weight?: number }).weight ?? 1);
      // A handful of edges carry several times the default weight; repeating
      // them by their rounded weight reproduces that influence.
      const repeats = Math.max(1, Math.min(4, Math.round(weight)));
      for (let i = 0; i < repeats; i += 1) pairs.push(sourceIndex, targetIndex);
    });
    return new Int32Array(pairs);
  }

  private post(message: LayoutRequest): void {
    this.ensureWorker().postMessage(message);
  }

  /** Starts (or restarts) the simulation from the graph's current state. */
  start(): void {
    if (this.destroyed) return;
    if (this.graph.order === 0) return;
    this.setRunning(true);
    this.tickCount = 0;
    this.alpha = 1;
    const snapshot = this.snapshot();
    this.worker?.terminate();
    this.worker = null;
    this.post({ type: 'start', ...snapshot, settings: this.settings });
  }

  stop(): void {
    this.setRunning(false);
    this.post({ type: 'stop' });
  }

  private restart(): void {
    this.start();
  }

  /** Re-runs the layout from a fresh seeded spread. */
  resetLayout(): void {
    this.graph.forEachNode((node) => {
      this.graph.setNodeAttribute(node, 'fixed', false);
      this.graph.setNodeAttribute(node, 'x', 0);
      this.graph.setNodeAttribute(node, 'y', 0);
    });
    this.start();
  }

  /**
   * Re-reads the graph after an incremental update.
   *
   * New nodes and edges join the existing layout, which the worker absorbs and
   * then settles again, rather than the whole graph being re-laid out.
   */
  sync(): void {
    if (this.graph.order === 0) return;
    // The first payload usually arrives after mount, when there were no nodes to
    // start a run for. Creating the worker here is what gets the layout going.
    if (!this.worker) {
      this.start();
      return;
    }
    const snapshot = this.snapshot();
    this.post({ type: 'sync', ...snapshot });
  }

  /** Pins a node in place (drag) or releases it. */
  setFixed(node: string, fixed: boolean): void {
    if (!this.graph.hasNode(node)) return;
    this.graph.setNodeAttribute(node, 'fixed', fixed);
  }

  /** Moves a dragged node, writing straight to the graph. */
  setPosition(node: string, x: number, y: number): void {
    if (!this.graph.hasNode(node)) return;
    this.graph.setNodeAttribute(node, 'x', x);
    this.graph.setNodeAttribute(node, 'y', y);
  }

  destroy(): void {
    this.destroyed = true;
    this.worker?.terminate();
    this.worker = null;
  }
}