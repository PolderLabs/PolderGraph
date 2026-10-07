import type { GraphEdge, GraphNode } from '../api/types';
import { isSemanticEdge } from './palette';

export type CommunityMode = 'structural' | 'hybrid';

export const COMMUNITY_META_PREFIX = 'pg:community:';

/** Meta-node id for a community in a given mode. */
export function communityMetaId(mode: CommunityMode, community: string): string {
  return `${COMMUNITY_META_PREFIX}${mode}:${community}`;
}

export function isCommunityMeta(id: string): boolean {
  return id.startsWith(COMMUNITY_META_PREFIX);
}

/**
 * Structural and hybrid communities are produced by different algorithms and
 * are not comparable, so the mode is carried on the node and shown in the UI.
 */
export const COMMUNITY_MODE_EXPLANATION: Record<CommunityMode, string> = {
  structural:
    'Structural communities: grouped by call/import/containment reachability. Membership means "these entities depend on each other structurally".',
  hybrid:
    'Hybrid communities: grouped by structure combined with embedding similarity. Membership may span modules that are structurally separate but semantically related.',
};

export interface CollapseResult {
  nodes: GraphNode[];
  edges: GraphEdge[];
  /** Meta-id -> member ids, for expanding on demand. */
  members: Record<string, string[]>;
}

function communityKey(node: GraphNode): string | null {
  if (node.community === null || node.community === undefined) return null;
  const key = String(node.community);
  return key === '' ? null : key;
}

/**
 * Collapses each community into a single meta-node.
 *
 * Intra-community edges disappear (their meaning is absorbed by the member
 * count) while inter-community edges are lifted onto the meta-nodes and their
 * weights summed, so the collapsed view keeps the real topology.
 */
export function collapseCommunities(
  nodes: GraphNode[],
  edges: GraphEdge[],
  mode: CommunityMode,
  communities: Record<string, string>,
): CollapseResult {
  const meta = new Map<string, GraphNode>();
  const members: Record<string, string[]> = {};
  const keptNodes: GraphNode[] = [];
  const nodeToMeta = new Map<string, string>();

  for (const node of nodes) {
    const key = communityKey(node);
    if (key === null) {
      keptNodes.push(node);
      continue;
    }
    const id = communityMetaId(mode, key);
    nodeToMeta.set(node.id, id);

    const label = communities[key] ?? `Community ${key}`;
    const existing = meta.get(id);
    if (existing) {
      existing.degree += 1;
      existing.importance += node.importance;
    } else {
      meta.set(id, {
        id,
        label,
        kind: 'directory',
        language: null,
        path: null,
        community: key,
        importance: node.importance,
        degree: 1,
        is_container: true,
      });
      members[id] = [];
    }
    members[id].push(node.id);
  }

  const lifted = new Map<string, GraphEdge>();
  const intraCount: Record<string, number> = {};

  for (const edge of edges) {
    const sourceMeta = nodeToMeta.get(edge.source);
    const targetMeta = nodeToMeta.get(edge.target);

    if (sourceMeta && targetMeta) {
      if (sourceMeta === targetMeta) {
        intraCount[sourceMeta] = (intraCount[sourceMeta] ?? 0) + 1;
      } else {
        liftEdge(lifted, sourceMeta, targetMeta, edge);
      }
      continue;
    }

    if (sourceMeta || targetMeta) {
      liftEdge(lifted, sourceMeta ?? edge.source, targetMeta ?? edge.target, edge);
      continue;
    }

    lifted.set(edge.id, edge);
  }

  const metaNodes = [...meta.values()].map((node) => {
    const metaId = communityMetaId(mode, String(node.community));
    return {
      ...node,
      label: `${node.label} (${members[metaId]?.length ?? 0})`,
      kind: 'community' as const,
    };
  });

  return {
    nodes: [...keptNodes, ...metaNodes],
    edges: [...lifted.values()],
    members,
  };
}

function liftEdge(
  target: Map<string, GraphEdge>,
  source: string,
  targetNode: string,
  edge: GraphEdge,
): void {
  const id = `${source}->${targetNode}`;
  const existing = target.get(id);
  if (!existing) {
    target.set(id, {
      ...edge,
      id,
      source,
      target: targetNode,
      confidence: edge.confidence,
    });
    return;
  }
  // Keep the strongest provenance as the representative of the merged bundle.
  const semantic = isSemanticEdge(edge.type);
  const existingSemantic = isSemanticEdge(existing.type);
  if (existingSemantic && !semantic) {
    target.set(id, { ...existing, type: edge.type, provenance: edge.provenance });
  }
}
