import type { GraphEdge, GraphNode } from '../api/types';
import type { FiltersState } from '../state/preferences';
import { isSemanticEdge } from './palette';

/** Groups that "only X" toggles map onto. */
export const KIND_GROUPS = {
  tests: ['test'],
  docs: ['document', 'section'],
  media: ['image', 'audio_segment', 'video_segment'],
} as const;

const SOURCE_KINDS = new Set<string>([
  'file',
  'module',
  'class',
  'interface',
  'trait',
  'enum',
  'type_alias',
  'function',
  'method',
  'constructor',
  'property',
  'field',
  'constant',
  'variable',
  'endpoint',
]);

export interface FilterableNode extends GraphNode {
  is_generated?: boolean;
  is_external?: boolean;
  changed?: boolean;
}

export interface FilterableEdge extends GraphEdge {
  similarity?: number;
}

function anyActive(record: Record<string, boolean>): boolean {
  for (const key of Object.keys(record)) {
    if (record[key]) return true;
  }
  return false;
}

function matchesSelection(value: string | null, record: Record<string, boolean>): boolean {
  // An untouched facet never hides anything.
  if (!anyActive(record)) return true;
  if (!value) return false;
  return record[value] === true;
}

function textMatches(node: FilterableNode, needle: string): boolean {
  if (!needle) return true;
  const haystack = `${node.label} ${node.path ?? ''} ${node.kind} ${node.language ?? ''}`;
  return haystack.toLowerCase().includes(needle);
}

export function nodePassesFilters(node: FilterableNode, filters: FiltersState): boolean {
  if (filters.hideGenerated && node.is_generated === true) return false;
  if (filters.hideExternal && node.is_external === true) return false;

  if (filters.onlyTests && !(KIND_GROUPS.tests as readonly string[]).includes(node.kind)) return false;
  if (filters.onlyDocs && !(KIND_GROUPS.docs as readonly string[]).includes(node.kind)) return false;
  if (filters.onlyMedia && !(KIND_GROUPS.media as readonly string[]).includes(node.kind)) return false;
  if (filters.onlySource && !SOURCE_KINDS.has(node.kind)) return false;

  if (filters.changedSinceGitBase && node.changed !== true) return false;

  if (!matchesSelection(node.kind, filters.kinds)) return false;
  if (!matchesSelection(node.language, filters.languages)) return false;

  if (anyActive(filters.roots)) {
    const root = filters.roots;
    const path = node.path ?? '';
    const matched = Object.keys(root).some(
      (candidate) => root[candidate] && (path === candidate || path.startsWith(`${candidate}/`)),
    );
    if (!matched) return false;
  }

  if (anyActive(filters.communities)) {
    const community =
      node.community === null || node.community === undefined ? '' : String(node.community);
    if (filters.communities[community] !== true) return false;
  }

  return textMatches(node, filters.text.trim().toLowerCase());
}

export function edgePassesFilters(edge: FilterableEdge, filters: FiltersState): boolean {
  if (!matchesSelection(edge.type, filters.edgeTypes)) return false;
  if (!matchesSelection(edge.provenance, filters.provenance)) return false;

  // The similarity floor only constrains semantic evidence; structural truth is
  // never filtered by an embedding threshold.
  if (isSemanticEdge(edge.type)) {
    const similarity = edge.similarity ?? edge.confidence ?? 1;
    if (similarity < filters.minSimilarity) return false;
  }

  return true;
}

export interface VisibleGraph {
  nodes: FilterableNode[];
  edges: FilterableEdge[];
  /** Node ids retained by filters, used to drop dangling edges. */
  nodeIds: Set<string>;
}

export function applyFilters(
  nodes: FilterableNode[],
  edges: FilterableEdge[],
  filters: FiltersState,
): VisibleGraph {
  const visibleNodes = nodes.filter((node) => nodePassesFilters(node, filters));
  const nodeIds = new Set(visibleNodes.map((node) => node.id));

  // Edges survive only when both endpoints do: a filtered node may not dangle.
  const visibleEdges = edges.filter(
    (edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target) && edgePassesFilters(edge, filters),
  );

  return { nodes: visibleNodes, edges: visibleEdges, nodeIds };
}

export interface FacetOptions {
  kinds: string[];
  languages: string[];
  roots: string[];
  communities: string[];
  edgeTypes: string[];
  provenance: string[];
}

/** Facet values present in the current payload, sorted for a stable UI. */
export function collectFacets(nodes: FilterableNode[], edges: FilterableEdge[]): FacetOptions {
  const kinds = new Set<string>();
  const languages = new Set<string>();
  const roots = new Set<string>();
  const communities = new Set<string>();
  const edgeTypes = new Set<string>();
  const provenance = new Set<string>();

  for (const node of nodes) {
    kinds.add(node.kind);
    if (node.language) languages.add(node.language);
    if (node.path) {
      const root = node.path.split('/')[0];
      if (root) roots.add(root);
    }
    if (node.community !== null && node.community !== undefined) {
      communities.add(String(node.community));
    }
  }

  for (const edge of edges) {
    edgeTypes.add(edge.type);
    provenance.add(edge.provenance);
  }

  const alphabetical = (values: Set<string>): string[] =>
    [...values].sort((a, b) => a.localeCompare(b));

  // Community ids are numeric for both detection modes, so they read as a
  // sequence rather than as "10" before "2".
  const byCommunityId = [...communities].sort((a, b) => Number(a) - Number(b));

  return {
    kinds: alphabetical(kinds),
    languages: alphabetical(languages),
    roots: alphabetical(roots),
    communities: byCommunityId,
    edgeTypes: alphabetical(edgeTypes),
    provenance: alphabetical(provenance),
  };
}
