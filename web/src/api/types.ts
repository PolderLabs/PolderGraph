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

/**
 * Node as returned by graph endpoints.
 *
 * Verified against the live server: the payload also carries
 * `qualified_name`, `start_line`, `end_line` and `is_generated`. An
 * `aggregate=community` payload replaces the entity fields with `size` and a
 * `members` id list, so both shapes are modelled here.
 */
export interface GraphNode {
  id: string;
  label: string;
  kind: NodeKind;
  language: string | null;
  path: string | null;
  qualified_name?: string | null;
  start_line?: number | null;
  end_line?: number | null;
  community: number | string | null;
  importance: number;
  degree: number;
  is_container: boolean;
  is_generated?: boolean;
  /** Present on server-side aggregate meta-nodes only. */
  size?: number;
  members?: string[];
  aggregate_mode?: AggregateMode;
}

/**
 * Edge as returned by graph endpoints.
 *
 * The server sends `source`/`target` *and* the legacy `source_id`/`target_id`
 * aliases; only the former are read. `resolver`, `source_location` and
 * `metadata` are additional and unused.
 */
export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  provenance: Provenance;
  confidence: number;
  source_id?: string;
  target_id?: string;
  resolver?: string | null;
  source_location?: { path: string | null; line: number | null; col: number | null } | null;
  metadata?: Record<string, unknown>;
}

/** Shared shape of global / neighborhood payloads. */
export interface GraphPayload {
  nodes: GraphNode[];
  edges: GraphEdge[];
  truncated: boolean;
  aggregate?: AggregateMode;
  /** Total entities behind a sampled payload (`/graph/global` only). */
  total_entities?: number;
  cache_key?: string;
}

export interface StatusRoot {
  root_id: string;
  path: string;
  name: string;
  is_primary: boolean;
  vcs_branch?: string;
  vcs_head?: string;
  updated_at?: number;
}

export interface StatusData {
  root?: string;
  roots: StatusRoot[];
  fresh: boolean;
  counts: Record<string, number>;
  model: string;
  dimensions: number;
  schema_version: number;
  languages: string[];
  communities: { structural: number; hybrid: number };
  capabilities?: string;
}

/** Neighbor entry in the inspector and in relation lists. */
export interface EntityRef {
  id: string;
  /** The server sends `name` on entity endpoints and `label` on relations. */
  label?: string;
  name?: string;
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

/** The `entity` object returned by `/api/entity/{id}`. */
export interface EntityRecord {
  id: string;
  root_id?: string;
  kind: NodeKind;
  name: string;
  qualified_name: string | null;
  path: string | null;
  language: string | null;
  parent_id: string | null;
  start_line: number | null;
  end_line: number | null;
  visibility: string | null;
  signature: string | null;
  docstring: string | null;
  content_hash?: string;
  semantic_hash?: string | null;
  is_generated: boolean;
  is_external: boolean;
}

/** Communities are returned keyed by detection mode. */
export interface EntityCommunities {
  structural?: CommunitySummary | null;
  hybrid?: CommunitySummary | null;
}

/**
 * `/api/entity/{id}` wraps the entity rather than flattening it, and adds
 * `excerpt`, `unresolved`, `communities` and `metrics` alongside the relations.
 */
export interface EntityData {
  entity: EntityRecord;
  parent: EntityRecord | null;
  inbound: InboundRelation[];
  outbound: OutboundRelation[];
  semantic_neighbors: SemanticNeighbor[];
  communities: EntityCommunities;
  metrics: EntityMetrics;
  excerpt: string | null;
  unresolved: Array<{ id: string; label?: string; kind?: NodeKind; path?: string | null }>;
}

/** Tests and docs referencing an entity. The server sends `name`, not `label`. */
export interface ImpactListEntry {
  id?: string;
  label?: string;
  name?: string;
  kind?: NodeKind;
  path?: string | null;
  qualified_name?: string | null;
  start_line?: number | null;
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
  truncated: boolean;
  entity: EntityRecord;
}

export interface SearchResult {
  id: string;
  label: string;
  name?: string;
  kind: NodeKind;
  path: string | null;
  qualified_name: string | null;
  language?: string | null;
  start_line?: number | null;
  end_line?: number | null;
  score: number;
  evidence: EvidenceKind;
  score_features: Record<string, number>;
}

/**
 * `/api/search` returns no graph context on the current server, even with
 * `include_graph_context`. Selecting a result focuses its local graph instead.
 */
export interface SearchRouting {
  intent?: string;
  degraded?: boolean;
  [key: string]: unknown;
}

export interface SearchData {
  query?: string;
  results: SearchResult[];
  truncated: boolean;
  intent?: string;
  routing?: SearchRouting;
  degraded?: boolean;
}

export interface MemoryEntry {
  id: string;
  scope: 'project' | 'user';
  project_root: string | null;
  kind: 'fact' | 'preference' | 'decision' | 'workflow' | 'reference';
  content: string;
  tags: string[];
  created_at: number;
  updated_at: number;
  score?: number;
  matched_terms?: string[];
  retrieval?: string;
}

export interface MemoryStatusData {
  store: string;
  current_project: string;
  user_memories: number;
  project_memories: number;
  total_memories: number;
  scope_note: string;
}

export interface MemoryListData {
  scope: string;
  results: MemoryEntry[];
}

export interface PathNode {
  id: string;
  label?: string;
  name?: string;
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
  reason?: string | null;
  hops: number;
  from?: EntityRecord;
  to?: EntityRecord;
  nodes: PathNode[];
  edges: PathEdge[];
}

export interface CommunitySummaryEntry {
  community_id: number | string;
  label: string | null;
  size: number;
  resolution?: number;
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

/**
 * SSE payload for `event: change`.
 *
 * Verified against the live server: the data is `{kind, ids}`. Kinds are
 * `reindex` (the indexing pipeline rewrote entities) and `graph` (graph
 * recomputation finished; carries no ids). There is no add/remove split — an
 * entity id in a `reindex` event may have been added, changed or deleted, so
 * the dashboard treats the ids as "touched" and re-validates the payload.
 */
export interface ChangeEvent {
  kind: 'reindex' | 'graph' | (string & {});
  ids: string[];
}

/** Free-form preference bag forwarded to `POST /api/view/preferences`. */
export type ViewPreferences = Record<string, unknown>;
