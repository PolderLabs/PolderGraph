/**
 * Reconciles the graphology graph with the incoming payload.
 *
 * Two invariants matter here and both exist for the same reason: a live update
 * must never reset or explode the layout.
 *
 *  1. A node that already exists keeps its `x`/`y`. Only a genuinely new node
 *     is seeded, and it is seeded next to its neighbours rather than randomly,
 *     so an SSE update lands locally instead of teleporting half the graph.
 *  2. The layout worker re-injects the current positions whenever topology
 *     changes, so the worker never restarts from its own stale copy.
 *
 * The Sigma instance is created once and mutated in place; rebuilding it would
 * drop the camera, the WebGL contexts and every position.
 */

import type Graph from 'graphology';
import type { PgEdgeAttributes, PgNodeAttributes } from './attributes';
import type { FilterableEdge, FilterableNode } from './filters';
import {
  AGGREGATE_SIZE_SCALE,
  communityColor,
  DEFAULT_SIZE_SCALE,
  isSemanticEdge,
  nodeColorForKind,
  sizeForImportance,
  UNRESOLVED_KINDS,
} from './palette';
import type { Palette } from './palette';


/** Edge program key used for a solid structural line. */
const SOLID_EDGE_TYPE = 'line';

/**
 * Edge program key used for a dashed semantic line.
 *
 * Registered in `GraphCanvas` as `dashed`; the string is duplicated here so
 * `sync.ts` has no import-time dependency on the Sigma renderer module.
 */
const DASHED_EDGE_TYPE = 'dashed';

/** Fully transparent: an "empty" state marker that costs no fragment work. */
export const TRANSPARENT = 'rgba(0,0,0,0)';

/**
 * @returns whether the topology changed, so adjacency must be rebuilt.
 */
/**
 * Appearance for a node the moment it enters the graph.
 *
 * The real values come from the display reducer, but that runs on a later
 * refresh; using a representative size and colour here means a newly loaded
 * graph is immediately visible and clickable.
 */
function initialAppearance(
  node: FilterableNode,
  palette: Palette,
  colorMode: 'kind' | 'community',
): { initialSize: number; initialColor: string } {
  const scale = node.kind === 'community' ? AGGREGATE_SIZE_SCALE : DEFAULT_SIZE_SCALE;
  return {
    initialSize: sizeForImportance(node.importance ?? 0, node.degree ?? 0, scale),
    // The real colour, not a placeholder. A placeholder grey meant every node
    // rendered as an undifferentiated dot until the reducer ran a moment later,
    // which looked like a visible switch from hollow to solid on load.
    initialColor:
      colorMode === 'community'
        ? communityColor(node.community === null || node.community === undefined
            ? ''
            : String(node.community), palette.communityRamp)
        : nodeColorForKind(node.kind ?? 'file', palette),
  };
}

export function syncGraph(
  graph: Graph<PgNodeAttributes, PgEdgeAttributes>,
  nodes: FilterableNode[],
  edges: FilterableEdge[],
  palette: Palette,
  colorMode: 'kind' | 'community' = 'kind',
): boolean {
  const present = new Set<string>();
  let topologyChanged = false;

  for (const node of nodes) {
    present.add(node.id);

    if (graph.hasNode(node.id)) {
      // Position, pin state and live markers are preserved across updates.
      graph.mergeNodeAttributes(node.id, {
        label: node.label,
        kind: node.kind,
        pgImportance: node.importance,
        pgDegree: node.degree,
        pgCommunity: node.community === null || node.community === undefined
          ? ''
          : String(node.community),
        pgUnresolved: UNRESOLVED_KINDS[node.kind] === true ? 1 : 0,
      });
      continue;
    }

    // A new node starts with the size and colour its display reducer would
    // give it. Starting at size 1 in a placeholder grey makes every node render
    // as an unclickable dot until the next refresh, which is what a freshly
    // loaded graph showed.
    const { initialSize, initialColor } = initialAppearance(node, palette, colorMode);
    graph.addNode(node.id, {
      x: 0,
      y: 0,
      size: initialSize,
      label: node.label,
      kind: node.kind,
      type: 'circle',
      color: initialColor,
      labelColor: '#e6edf5',
      pgRingColor: TRANSPARENT,
      pgRingSize: 0,
      pgImportance: node.importance,
      pgDegree: node.degree,
      pgCommunity: node.community === null || node.community === undefined
        ? ''
        : String(node.community),
      pgUnresolved: UNRESOLVED_KINDS[node.kind] === true ? 1 : 0,
      pgChanged: 0,
      pgPinned: 0,
    });
    topologyChanged = true;
  }

  for (const node of graph.nodes()) {
    if (!present.has(node)) {
      graph.dropNode(node);
      topologyChanged = true;
    }
  }

  const seenEdges = new Set<string>();

  for (const edge of edges) {
    // An edge whose endpoint was filtered out must not exist in the graph.
    if (!graph.hasNode(edge.source) || !graph.hasNode(edge.target)) continue;

    const attributes: PgEdgeAttributes = {
      size: 1,
      color: '#7f8ea3',
      label: '',
      weight: Number.isFinite(edge.confidence) ? edge.confidence : 1,
      type: isSemanticEdge(edge.type) ? DASHED_EDGE_TYPE : SOLID_EDGE_TYPE,
      edgeType: edge.type,
      provenance: edge.provenance,
      semantic: isSemanticEdge(edge.type) ? 1 : 0,
      sourceId: edge.source,
      targetId: edge.target,
    };

    if (graph.hasEdge(edge.id)) {
      graph.replaceEdgeAttributes(edge.id, attributes);
      seenEdges.add(edge.id);
      continue;
    }

    const existing = graph.edge(edge.source, edge.target);
    if (existing !== undefined) {
      // The graph is single: parallel edges collapse onto the first one. A
      // multigraph would multiply the WebGL buffers on wide fan-out hubs.
      // `existing` is the surviving key, so the alias must not be pruned.
      graph.replaceEdgeAttributes(existing, attributes);
      seenEdges.add(existing);
      continue;
    }

    graph.addEdgeWithKey(edge.id, edge.source, edge.target, attributes);
    seenEdges.add(edge.id);
    topologyChanged = true;
  }

  for (const edge of graph.edges()) {
    if (!seenEdges.has(edge)) {
      graph.dropEdge(edge);
      topologyChanged = true;
    }
  }

  return topologyChanged;
}

/** Undirected adjacency, rebuilt only when the topology actually changed. */
export function buildAdjacency(
  graph: Graph<PgNodeAttributes, PgEdgeAttributes>,
): Map<string, Set<string>> {
  const adjacency = new Map<string, Set<string>>();
  graph.forEachNode((node) => adjacency.set(node, new Set()));
  graph.forEachEdge((_edge, _attributes, source, target) => {
    adjacency.get(source)?.add(target);
    adjacency.get(target)?.add(source);
  });
  return adjacency;
}