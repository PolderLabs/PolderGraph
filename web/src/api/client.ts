import type {
  AggregateMode,
  ApiEnvelope,
  ApiErr,
  ApiErrorBody,
  ApiOk,
  CommunitiesData,
  CommunityMode,
  Direction,
  EntityData,
  GraphPayload,
  ImpactData,
  MemoryEntry,
  MemoryListData,
  MemoryStatusData,
  PathData,
  SearchData,
  SourceData,
  StatusData,
  ViewPreferences,
} from './types';

/** Raised when the server returns the documented failure envelope. */
export class ApiError extends Error {
  readonly code: string;
  readonly remediation: string | null;
  readonly status: number;

  constructor(body: ApiErrorBody, status: number) {
    super(body.message || body.code || 'Request failed');
    this.name = 'ApiError';
    this.code = body.code || 'unknown_error';
    this.remediation = body.remediation ?? null;
    this.status = status;
  }
}

/** Raised when the request never produced a valid envelope (offline, 502, HTML, ...). */
export class TransportError extends Error {
  readonly status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = 'TransportError';
    this.status = status;
  }
}

/** Raised when an in-flight request was superseded by a newer one. */
export class AbortedRequestError extends Error {
  constructor() {
    super('aborted');
    this.name = 'AbortedError';
  }
}

export function isAbortError(error: unknown): boolean {
  if (error instanceof AbortedRequestError) return true;
  if (typeof DOMException !== 'undefined' && error instanceof DOMException) {
    return error.name === 'AbortError';
  }
  return error instanceof Error && error.name === 'AbortError';
}

/** Same-origin by design: the dashboard never talks to a remote host. */
const BASE = '/api';

interface RequestOptions {
  signal?: AbortSignal;
  method?: 'GET' | 'POST';
  body?: unknown;
}

function joinQuery(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === '') continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : '';
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { signal, method = 'GET', body } = options;

  const headers: Record<string, string> = { Accept: 'application/json' };
  let payload: string | undefined;
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      method,
      headers,
      ...(payload !== undefined ? { body: payload } : {}),
      ...(signal ? { signal } : {}),
      credentials: 'same-origin',
      // Same-origin only: never send repository content to a third party.
      mode: 'same-origin',
    });
  } catch (error) {
    if (signal?.aborted) throw new AbortedRequestError();
    throw new TransportError(
      error instanceof Error ? error.message : 'Network request to the PolderGraph API failed.',
    );
  }

  const text = await response.text();

  let envelope: ApiEnvelope<T> | null = null;
  if (text.length > 0) {
    try {
      envelope = JSON.parse(text) as ApiEnvelope<T>;
    } catch {
      throw new TransportError(
        `The PolderGraph API returned a non-JSON response (HTTP ${response.status}).`,
        response.status,
      );
    }
  }

  if (envelope && envelope.ok === true) {
    return (envelope as ApiOk<T>).data;
  }

  if (envelope && envelope.ok === false) {
    throw new ApiError(envelope.error, response.status);
  }

  throw new TransportError(
    `Unexpected response from the PolderGraph API (HTTP ${response.status}).`,
    response.status,
  );
}

function asErrorPayload(status: number): ApiErr {
  return {
    ok: false,
    api_version: 1,
    error: {
      code: status === 404 ? 'not_found' : 'http_error',
      message: `Request failed with HTTP ${status}.`,
      remediation: 'Check that `poldergraph ui` is still serving this workspace.',
    },
  };
}

/* -------------------------------------------------------------------------- */
/* Endpoint bindings                                                          */
/* -------------------------------------------------------------------------- */

export const api = {
  status(signal?: AbortSignal): Promise<StatusData> {
    return request<StatusData>('/status', { ...(signal ? { signal } : {}) });
  },

  globalGraph(
    params: { limit?: number; aggregate?: AggregateMode } = {},
    signal?: AbortSignal,
  ): Promise<GraphPayload> {
    const qs = joinQuery({
      limit: params.limit,
      aggregate: params.aggregate ?? 'none',
    });
    return request<GraphPayload>(`/graph/global${qs}`, { ...(signal ? { signal } : {}) });
  },

  neighborhood(
    id: string,
    params: {
      depth?: number;
      direction?: Direction;
      structuralOnly?: boolean;
      fanout?: number;
      kinds?: string[];
      edgeTypes?: string[];
    } = {},
    signal?: AbortSignal,
  ): Promise<GraphPayload> {
    const qs = joinQuery({
      depth: params.depth,
      direction: params.direction ?? 'both',
      structural_only: params.structuralOnly ?? false,
      fanout: params.fanout,
      kinds: params.kinds?.length ? params.kinds.join(',') : undefined,
      edge_types: params.edgeTypes?.length ? params.edgeTypes.join(',') : undefined,
    });
    return request<GraphPayload>(
      `/graph/neighborhood/${encodeURIComponent(id)}${qs}`,
      { ...(signal ? { signal } : {}) },
    );
  },

  entity(id: string, signal?: AbortSignal): Promise<EntityData> {
    return request<EntityData>(`/entity/${encodeURIComponent(id)}`, {
      ...(signal ? { signal } : {}),
    });
  },

  search(
    params: {
      q: string;
      limit?: number;
      kinds?: string[];
      languages?: string[];
      paths?: string[];
      includeSemantic?: boolean;
      includeStructuralContext?: boolean;
      includeGraphContext?: boolean;
      graphContextLimit?: number;
      graphFanout?: number;
    },
    signal?: AbortSignal,
  ): Promise<SearchData> {
    const qs = joinQuery({
      q: params.q,
      limit: params.limit,
      kinds: params.kinds?.length ? params.kinds.join(',') : undefined,
      languages: params.languages?.length ? params.languages.join(',') : undefined,
      paths: params.paths?.length ? params.paths.join(',') : undefined,
      include_semantic: params.includeSemantic ?? true,
      include_structural_context: params.includeStructuralContext ?? true,
      include_graph_context: params.includeGraphContext ?? false,
      graph_context_limit: params.graphContextLimit,
      graph_fanout: params.graphFanout,
    });
    return request<SearchData>(`/search${qs}`, { ...(signal ? { signal } : {}) });
  },

  path(
    params: {
      from: string;
      to: string;
      structuralOnly?: boolean;
      includeSemantic?: boolean;
    },
    signal?: AbortSignal,
  ): Promise<PathData> {
    const qs = joinQuery({
      from: params.from,
      to: params.to,
      structural_only: params.structuralOnly ?? true,
      include_semantic: params.includeSemantic ?? false,
    });
    return request<PathData>(`/path${qs}`, { ...(signal ? { signal } : {}) });
  },

  impact(
    id: string,
    params: { maxDepth?: number; edgeTypes?: string[] } = {},
    signal?: AbortSignal,
  ): Promise<ImpactData> {
    const qs = joinQuery({
      max_depth: params.maxDepth,
      edge_types: params.edgeTypes?.length ? params.edgeTypes.join(',') : undefined,
    });
    return request<ImpactData>(`/impact/${encodeURIComponent(id)}${qs}`, {
      ...(signal ? { signal } : {}),
    });
  },

  communities(mode: CommunityMode, signal?: AbortSignal): Promise<CommunitiesData> {
    return request<CommunitiesData>(`/communities${joinQuery({ mode })}`, {
      ...(signal ? { signal } : {}),
    });
  },

  memoryStatus(signal?: AbortSignal): Promise<MemoryStatusData> {
    return request<MemoryStatusData>('/memory/status', { ...(signal ? { signal } : {}) });
  },

  memoryList(scope: string, signal?: AbortSignal): Promise<MemoryListData> {
    const qs = joinQuery({ scope, limit: 100 });
    return request<MemoryListData>(`/memory${qs}`, { ...(signal ? { signal } : {}) });
  },

  memorySearch(
    params: { q: string; scope: string; semantic: boolean },
    signal?: AbortSignal,
  ): Promise<MemoryListData & { query: string }> {
    const qs = joinQuery({ q: params.q, scope: params.scope, limit: 100, semantic: params.semantic });
    return request<MemoryListData & { query: string }>(`/memory/search${qs}`, {
      ...(signal ? { signal } : {}),
    });
  },

  memoryAdd(
    entry: { content: string; scope: 'project' | 'user'; kind: MemoryEntry['kind']; tags: string[] },
  ): Promise<MemoryEntry> {
    return request<MemoryEntry>('/memory', { method: 'POST', body: entry });
  },

  memoryUpdate(
    id: string,
    entry: { content: string; kind: MemoryEntry['kind']; tags: string[] },
  ): Promise<MemoryEntry> {
    return request<MemoryEntry>(`/memory/${encodeURIComponent(id)}/update`, {
      method: 'POST',
      body: entry,
    });
  },

  memoryForget(id: string): Promise<MemoryEntry> {
    return request<MemoryEntry>(`/memory/${encodeURIComponent(id)}/forget`, { method: 'POST' });
  },

  savePreferences(preferences: ViewPreferences, signal?: AbortSignal): Promise<ViewPreferences> {
    return request<ViewPreferences>('/view/preferences', {
      method: 'POST',
      body: preferences,
      ...(signal ? { signal } : {}),
    });
  },

  source(
    params: { path: string; startLine?: number; endLine?: number },
    signal?: AbortSignal,
  ): Promise<SourceData> {
    const qs = joinQuery({
      path: params.path,
      start_line: params.startLine,
      end_line: params.endLine,
    });
    return request<SourceData>(`/source${qs}`, { ...(signal ? { signal } : {}) });
  },
};

export type Api = typeof api;
export { asErrorPayload };
