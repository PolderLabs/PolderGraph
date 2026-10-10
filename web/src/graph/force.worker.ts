/**
 * Graph layout worker.
 *
 * The simulation is d3-force, which is what powers Obsidian's graph view.
 *
 * Why this replaced ForceAtlas2
 * -----------------------------
 * ForceAtlas2 applies constant forces for as long as it is iterated and has no
 * notion of the system cooling down. In a browser that means the graph never
 * stops moving: it twitches, clicks land on the wrong node, and because nothing
 * ever loses to attraction the layout keeps contracting into clumps.
 *
 * d3-force solves this at the root. Every force is multiplied by a global
 * `alpha` that decays geometrically, so motion dies away on its own and the
 * simulation reaches a genuine rest state. `alphaDecay` and `alphaMin` are
 * explicit, documented parameters, so there is no movement threshold to tune and
 * no fighting between a settling test and the forces that are still running.
 *
 * The forces used:
 *
 * - `forceManyBody` — long-range repulsion, which is what spreads the graph out.
 * - `forceLink`     — springs along edges, which keeps related code together.
 * - `forceCollide`  — keeps node circles from overlapping.
 * - `forceCenter`   — recentres the layout; it translates the group rather than
 *   pulling each node inward, which is what preserves the spread.
 */

/** Tunables for the simulation. Values are in layout units, not pixels. */
export interface LayoutSettings {
  /** Repulsion between nodes. More negative spreads the graph further apart. */
  chargeStrength: number;
  /** Spring strength along edges. Higher pulls related nodes closer. */
  linkStrength: number;
  /** Preferred distance between connected nodes. */
  linkDistance: number;
  /** How hard the layout's centroid is pulled to the middle of the view. */
  centerStrength: number;
  /** Velocity retained per tick. Lower settles faster and moves less. */
  velocityDecay: number;
  /** Extra gap kept between node circles when resolving collisions. */
  collisionPadding: number;
}

export const DEFAULT_SETTINGS: LayoutSettings = {
  chargeStrength: -320,
  linkStrength: 0.7,
  linkDistance: 60,
  centerStrength: 1,
  velocityDecay: 0.55,
  collisionPadding: 4,
};

/** Fraction of remaining energy dissipated each tick; ~0.1 to settle. */
const ALPHA_DECAY = 0.035;
/** Below this the simulation is finished and the worker stops. */
const ALPHA_MIN = 0.005;
/** Energy restored when the topology changes under a settled layout. */
const ALPHA_ON_SYNC = 0.25;
/** Minimum wall-clock gap between ticks, so the worker never outruns the frames. */
const MIN_TICK_INTERVAL_MS = 16;

/** Node identity travels as a table; typed arrays are indexed into it. */
export interface LayoutStartMessage {
  type: 'start';
  ids: string[];
  /** Radius per node, indexed like `ids`. */
  radii: Float32Array;
  /** Current positions, two entries per node: x, y. */
  positions: Float32Array;
  /** Flat array of edge endpoints as indices into `ids`. */
  edges: Int32Array;
  settings: LayoutSettings;
}

export interface LayoutSyncMessage {
  type: 'sync';
  ids: string[];
  radii: Float32Array;
  positions: Float32Array;
  edges: Int32Array;
}

export interface LayoutStopMessage {
  type: 'stop';
}

export type LayoutRequest = LayoutStartMessage | LayoutSyncMessage | LayoutStopMessage;

export interface LayoutTick {
  type: 'tick';
  /** Two entries per node: x, y, in the same order as the ids sent at start. */
  positions: Float32Array;
  tick: number;
  alpha: number;
}

export interface LayoutSettled {
  type: 'settled';
}

export type LayoutResponse = LayoutTick | LayoutSettled;

const self = globalThis as unknown as DedicatedWorkerGlobalScope;

import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  type Simulation,
} from 'd3-force';

interface SimNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface SimLink {
  source: number;
  target: number;
}

let nodes: SimNode[] = [];
let radii: number[] = [];
let settings: LayoutSettings = { ...DEFAULT_SETTINGS };
let simulation: Simulation<SimNode, SimLink> | null = null;
let tickCount = 0;
let lastTickAt = 0;
let timer: ReturnType<typeof setTimeout> | null = null;

/** Seeds nodes on a golden-angle spiral, the standard no-overlap start. */
function seed(count: number): void {
  const radius = Math.max(60, Math.sqrt(count) * 30);
  for (let i = 0; i < count; i += 1) {
    const node = nodes[i];
    const angle = i * 2.399963229728653;
    node.x = Math.cos(angle) * radius * Math.sqrt((i + 0.5) / count);
    node.y = Math.sin(angle) * radius * Math.sqrt((i + 0.5) / count);
    node.vx = 0;
    node.vy = 0;
  }
}

function build(): Simulation<SimNode, SimLink> {
  const links: SimLink[] = [];
  for (let i = 0; i + 1 < edgeIndices.length; i += 2) {
    links.push({ source: edgeIndices[i], target: edgeIndices[i + 1] });
  }
  return forceSimulation<SimNode, SimLink>(nodes)
    .force('charge', forceManyBody<SimNode>().strength(settings.chargeStrength).distanceMax(600))
    .force(
      'link',
      forceLink<SimNode, SimLink>(links)
        .id((_node: SimNode, index: number) => index)
        .distance(settings.linkDistance)
        // d3 distributes a node's pull across its degree; without that a hub
        // with hundreds of edges tears its neighbours apart.
        .strength(
          settings.linkStrength /
            Math.max(1, Math.min(20, countDegree(links, links.length))),
        ),
    )
    .force(
      'collide',
      forceCollide<SimNode>((_node: SimNode, index: number) => radii[index] + settings.collisionPadding).iterations(2),
    )
    .force('center', forceCenter(0, 0).strength(settings.centerStrength))
    .velocityDecay(settings.velocityDecay)
    .alphaDecay(ALPHA_DECAY)
    .stop();
}

let edgeIndices: Int32Array = new Int32Array(0);

function countDegree(links: SimLink[], _total: number): number {
  // A single representative degree: enough to stop hubs dominating without
  // pretending to model the real distribution.
  return Math.max(1, Math.round(links.length / Math.max(1, nodes.length)));
}

function tick(): void {
  timer = null;
  const now = Date.now();
  const elapsed = now - lastTickAt;
  if (elapsed < MIN_TICK_INTERVAL_MS) {
    timer = setTimeout(tick, MIN_TICK_INTERVAL_MS - elapsed);
    return;
  }
  lastTickAt = now;
  if (!simulation) return;

  simulation.tick();
  tickCount += 1;

  self.postMessage({
    type: 'tick',
    positions: pack(),
    tick: tickCount,
    alpha: simulation.alpha(),
  } satisfies LayoutTick);

  if (simulation.alpha() < ALPHA_MIN) {
    self.postMessage({ type: 'settled' } satisfies LayoutSettled);
    return;
  }
  // `setTimeout` rather than a direct call, so a `stop` or `sync` message is
  // always observed between ticks.
  timer = setTimeout(tick, 0);
}

/** Serialises current positions as x, y pairs. */
function pack(): Float32Array {
  const out = new Float32Array(nodes.length * 2);
  for (let i = 0; i < nodes.length; i += 1) {
    out[i * 2] = nodes[i].x;
    out[i * 2 + 1] = nodes[i].y;
  }
  return out;
}

/** Rebuilds simulation state from the main thread's id table and positions. */
function rebuild(nextIds: string[], nextRadii: Float32Array, positions: Float32Array, edges: Int32Array, reseed: boolean): void {
  const count = nextIds.length;
  radii = Array.from(nextRadii);
  edgeIndices = edges;
  const rebuilt: SimNode[] = [];
  for (let i = 0; i < count; i += 1) {
    const x = positions[i * 2];
    const y = positions[i * 2 + 1];
    rebuilt.push({
      x: Number.isFinite(x) ? x : 0,
      y: Number.isFinite(y) ? y : 0,
      vx: 0,
      vy: 0,
    });
  }
  nodes = rebuilt;
  if (reseed) seed(count);
  simulation = build();
}

self.onmessage = (event: MessageEvent<LayoutRequest>) => {
  const message = event.data;
  switch (message.type) {
    case 'start': {
      settings = { ...DEFAULT_SETTINGS, ...message.settings };
      rebuild(message.ids, message.radii, message.positions, message.edges, true);
      tickCount = 0;
      lastTickAt = 0;
      clearTimeout(timer ?? undefined);
      timer = setTimeout(tick, 0);
      break;
    }
    case 'sync': {
      // The topology changed. Rebuild around the current positions and give the
      // simulation a little energy so it absorbs the change, then settles again
      // instead of running forever.
      rebuild(message.ids, message.radii, message.positions, message.edges, false);
      simulation?.alpha(ALPHA_ON_SYNC).restart();
      tickCount = 0;
      lastTickAt = 0;
      clearTimeout(timer ?? undefined);
      timer = setTimeout(tick, 0);
      break;
    }
    case 'stop':
      clearTimeout(timer ?? undefined);
      timer = null;
      simulation?.stop();
      break;
  }
};