import type { PathData, PathEdge } from '../api/types';
import type { FilterableEdge, FilterableNode } from './filters';

export interface PathHighlight {
  nodeIds: Set<string>;
  edgeIds: Set<string>;
  hops: number;
  from: string;
  to: string;
}

export const EMPTY_PATH: PathHighlight | null = null;

/**
 * Folds a server path result into the sets the renderers test against.
 *
 * The path edges are matched against the graph payload by endpoint pair
 * because the path endpoint may report its own edge ids, which do not have to
 * coincide with the ids used by the graph payload.
 */
export function buildPathHighlight(
  path: PathData,
  from: string,
  to: string,
  edges: FilterableEdge[],
): PathHighlight {
  const nodeIds = new Set<string>([from, to]);
  for (const node of path.nodes) nodeIds.add(node.id);

  const serverEdgeIds = new Set<string>();
  for (const edge of path.edges) {
    if (typeof edge.id === 'string') serverEdgeIds.add(edge.id);
  }

  const edgeIds = new Set<string>(serverEdgeIds);

  // Also light up any graph-payload edge that connects consecutive path nodes.
  const ordered = orderPathNodes(path, from, to);
  for (let i = 0; i + 1 < ordered.length; i += 1) {
    const a = ordered[i];
    const b = ordered[i + 1];
    for (const edge of edges) {
      const matches =
        (edge.source === a && edge.target === b) || (edge.source === b && edge.target === a);
      if (matches) edgeIds.add(edge.id);
    }
  }

  return { nodeIds, edgeIds, hops: path.hops, from, to };
}

/**
 * Reconstructs the traversal order of the returned path so consecutive hops
 * can be matched. Falls back to document order when the server omits a usable
 * ordering.
 */
function orderPathNodes(path: PathData, from: string, to: string): string[] {
  const ids = path.nodes.map((node) => node.id);
  const starts = ids.indexOf(from);
  const ends = ids.indexOf(to);
  if (starts === -1 || ends === -1 || starts === ends) return ids;

  // The edge list is the authoritative ordering when present.
  const edgeOrder = path.edges as PathEdge[];
  if (edgeOrder.length > 0) {
    const ordered: string[] = [from];
    let cursor = from;
    const guard = ids.length + 1;
    for (let step = 0; step < guard; step += 1) {
      const next = edgeOrder.find(
        (edge) => edge.source === cursor || edge.target === cursor,
      );
      if (!next) break;
      cursor = next.source === cursor ? next.target : next.source;
      if (ordered.includes(cursor)) break;
      ordered.push(cursor);
    }
    if (ordered.includes(to)) return ordered;
  }

  return [...ids.slice(starts, ends + 1), ...ids.slice(0, starts), ...ids.slice(ends + 1)];
}

/** Pads a path result into the current payload so the graph keeps its context. */
export function mergePathIntoGraph(
  baseNodes: FilterableNode[],
  baseEdges: FilterableEdge[],
  path: PathData,
): { nodes: FilterableNode[]; edges: FilterableEdge[] } {
  const knownNodes = new Set(baseNodes.map((node) => node.id));
  const knownEdges = new Set(baseEdges.map((edge) => edge.id));

  const extraNodes = path.nodes.filter((node) => !knownNodes.has(node.id));
  const extraEdges: FilterableEdge[] = [];

  for (const edge of path.edges) {
    if (typeof edge.id === 'string' && knownEdges.has(edge.id)) continue;
    extraEdges.push({
      id: edge.id ?? `${edge.source}->${edge.target}`,
      source: edge.source,
      target: edge.target,
      type: edge.type ?? 'references',
      provenance: edge.provenance ?? 'inferred',
      confidence: 1,
    });
  }

  return {
    nodes: [...baseNodes, ...extraNodes.map((node) => ({
      id: node.id,
      label: node.label ?? node.id,
      kind: node.kind ?? 'module',
      language: null,
      path: null,
      community: null,
      importance: 0.5,
      degree: 0,
      is_container: false,
    }))],
    edges: [...baseEdges, ...extraEdges],
  };
}
