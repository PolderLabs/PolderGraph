import type Graph from 'graphology';
import { isSemanticEdge, UNRESOLVED_KINDS } from './palette';
import type { ForceAtlas2Controller } from './layout';
import type { PgEdgeAttributes, PgNodeAttributes } from './attributes';
import type { FilterableEdge, FilterableNode } from './filters';

/**
 * Reconciles the graphology graph with the incoming payload.
 *
 * Existing nodes keep their `x`/`y`, which is what makes SSE updates and view
 * switches non-destructive: the layout controller never re-seeds a node that
 * already has a position.
 *
 * @returns whether the topology changed, so adjacency can be rebuilt.
 */
export function syncGraph(
  graph: Graph<PgNodeAttributes, PgEdgeAttributes>,
  controller: ForceAtlas2Controller,
  nodes: FilterableNode[],
  edges: FilterableEdge[],
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
        pgCommunity: communityKey(node.community),
        pgUnresolved: UNRESOLVED_KINDS[node.kind] ? 1 : 0,
        pgChanged: node.changed === true ? 1 : 0,
      });
      continue;
    }

    graph.addNode(node.id, {
      x: Math.random(),
      y: Math.random(),
      size: 1,
      label: node.label,
      kind: node.kind,
      color: '#7f8ea3',
      labelColor: '#e6edf5',
      borderColor: TRANSPARENT,
      borderSize: 0,
      pgImportance: node.importance,
      pgDegree: node.degree,
      pgCommunity: communityKey(node.community),
      pgUnresolved: UNRESOLVED_KINDS[node.kind] ? 1 : 0,
      pgChanged: node.changed === true ? 1 : 0,
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

  // `dropNode` already removed every edge touching a removed node, so any edge
  // left dangling has been caught by the prune above.
  controller.sync();
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

/** Fully transparent border: an "empty" ring that costs no fragment work. */
export const TRANSPARENT = 'rgba(0,0,0,0)';

function communityKey(community: number | string | null | undefined): string {
  return community === null || community === undefined ? '' : String(community);
}
