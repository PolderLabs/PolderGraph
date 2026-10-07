/**
 * Wire types for the PolderGraph dashboard API.
 *
 * These mirror the server contract exactly (api_version 1). Every response uses
 * the `{ok, api_version, data}` envelope; errors use `{ok: false, error}`.
 */

export type ApiVersion = 1;

export interface ApiErrorBody {
  code: string;
  message: string;
  remediation?: string | null;
}

/** Successful envelope. */
export interface ApiOk<T> {
  ok: true;
  api_version: ApiVersion;
  data: T;
}

/** Failure envelope. */
export interface ApiErr {
  ok: false;
  api_version: ApiVersion;
  error: ApiErrorBody;
}

export type ApiEnvelope<T> = ApiOk<T> | ApiErr;

/** Node kinds mirror `docs/data-model.md`. Unknown values are tolerated. */
export const NODE_KINDS = [
  'workspace',
  'repository',
  'directory',
  'file',
  'module',
  'namespace',
  'package',
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
  'test',
  'document',
  'section',
  'image',
  'audio_segment',
  'video_segment',
  'unknown_symbol',
] as const;

export type NodeKind = (typeof NODE_KINDS)[number] | (string & {});

/** Provenance classes from the data model. */
export const PROVENANCE_VALUES = [
  'extracted',
  'resolved',
  'inferred',
  'ambiguous',
  'semantic',
  'manual',
] as const;

export type Provenance = (typeof PROVENANCE_VALUES)[number] | (string & {});

/** Structural edge types. `semantically_related` is the only semantic one. */
export const EDGE_TYPES = [
  'contains',
  'defines',
  'imports',
  'exports',
  'calls',
  'constructs',
  'inherits',
  'implements',
  'overrides',
  'references',
  'reads',
  'writes',
  'returns_type',
  'accepts_type',
  'decorates',
  'routes_to',
  'tests',
  'documents',
  'semantically_related',
] as const;

export type EdgeType = (typeof EDGE_TYPES)[number] | (string & {});

export type AggregateMode = 'none' | 'directory' | 'community';
export type CommunityMode = 'structural' | 'hybrid';
export type Direction = 'in' | 'out' | 'both';
export type EvidenceKind = 'exact' | 'lexical' | 'semantic' | 'graph-expanded';
export type LayoutRunState = 'running' | 'stopped';

/** Node as returned by graph endpoints. */
export interface GraphNode {
  id: string;
  label: string;
  kind: NodeKind;
  language: string | null;
  path: string | null;
  community: number | string | null;
  importance: number;
  degree: number;
  is_container: boolean;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  provenance: Provenance;
  confidence: number;
}

/** Shared shape of global / neighborhood / search-graph payloads. */
export interface GraphPayload {
  nodes: GraphNode[];
  edges: GraphEdge[];
  truncated: boolean;
  aggregate?: AggregateMode;
}

export interface StatusData {
  roots: Array<{
    root_id: string;
    path: string;
    name: string;
    is_primary: boolean;
  }>;
  fresh: boolean;
  counts: Record<string, number>;
  model: string;
  dimensions: number;
  schema_version: number;
  languages: string[];
  communities: { structural: number; hybrid: number };
}

/** Neighbor entry in the inspector. */
export interface EntityRef {
  id: string;
  label?: string;
  kind?: NodeKind;
  path?: string | null;
  qualified_name?: string | null;
  language?: string | null;
}

export interface EntityEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  provenance: Provenance;
  confidence: number;
}

export interface InboundRelation extends EntityEdge {
  entity: EntityRef;
}

export interface OutboundRelation extends EntityEdge {
  entity: EntityRef;
}

export interface SemanticNeighbor {
  entity: EntityRef;
  similarity: number;
}

export interface EntityMetrics {
  [key: string]: number | string | boolean | null;
}

export interface CommunitySummary {
  community_id?: number | string | null;
  label?: string | null;
  size?: number | null;
  mode?: CommunityMode | string;
}

export interface EntityData {
  id: string;
  kind: NodeKind;
  name: string;
  qualified_name: string | null;
  path: string | null;
  language: string | null;
  start_line: number | null;
  end_line: number | null;
  signature: string | null;
  docstring: string | null;
  visibility: string | null;
  is_generated: boolean;
  metrics: EntityMetrics;
  community: CommunitySummary | string | number | null;
  inbound: InboundRelation[];
  outbound: OutboundRelation[];
  semantic_neighbors: SemanticNeighbor[];
  parent: EntityRef | null;
}

/** Tests and docs referencing an entity. */
export interface ImpactListEntry {
  id?: string;
  label?: string;
  kind?: NodeKind;
  path?: string | null;
  qualified_name?: string | null;
  type?: EdgeType;
  similarity?: number | null;
  [key: string]: unknown;
}

export interface ImpactData {
  direct: ImpactListEntry[];
  transitive: ImpactListEntry[];
  tests: ImpactListEntry[];
  docs: ImpactListEntry[];
  semantic_only: ImpactListEntry[];
}

export interface SearchResult {
  id: string;
  label: string;
  kind: NodeKind;
  path: string | null;
  qualified_name: string | null;
  score: number;
  evidence: EvidenceKind;
  score_features: Record<string, number>;
}

export interface SearchData {
  results: SearchResult[];
  truncated: boolean;
}

export interface PathNode {
  id: string;
  label?: string;
  kind?: NodeKind;
  [key: string]: unknown;
}

export interface PathEdge {
  id?: string;
  source: string;
  target: string;
  type?: EdgeType;
  provenance?: Provenance;
  [key: string]: unknown;
}

export interface PathData {
  found: boolean;
  nodes: PathNode[];
  edges: PathEdge[];
  hops: number;
}

export interface CommunitySummaryEntry {
  community_id: number | string;
  label: string | null;
  size: number;
  top_entities: EntityRef[];
}

export interface CommunitiesData {
  mode: CommunityMode | string;
  communities: CommunitySummaryEntry[];
}

export interface SourceData {
  path: string;
  start_line: number;
  end_line: number;
  content: string;
}

/** SSE payload for `event: change`. */
export interface ChangeEvent {
  added: string[];
  removed: string[];
  changed: string[];
}

/** Free-form preference bag forwarded to `POST /api/view/preferences`. */
export type ViewPreferences = Record<string, unknown>;
