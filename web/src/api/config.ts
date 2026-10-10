import { request } from './client';

/**
 * Writable configuration, mirroring the server's section allowlist.
 *
 * The dashboard never edits configuration text directly: it edits these typed
 * sections and the server validates every key, so a stale field name fails
 * loudly instead of looking like it worked.
 */
export type ConfigSection =
  | 'index'
  | 'embedding'
  | 'semantic_edges'
  | 'graph'
  | 'retrieval'
  | 'privacy'
  | 'decisions';

export type SectionValues = Record<string, unknown>;
export type ConfigPayload = Record<ConfigSection, SectionValues>;

export interface ModelsStatus {
  backend: string;
  model: string;
  dimensions: number;
  device: string;
  allow_downloads: boolean;
  cache_dir: string;
  cached: boolean;
  vectors: number;
}

export interface ModelsDownloadResult {
  model: string;
  dimensions: number;
  cached: boolean;
}

export function fetchConfig(): Promise<ConfigPayload> {
  return request<ConfigPayload>('/config');
}

export function saveConfig(payload: Partial<ConfigPayload>): Promise<{ applied: string[] }> {
  // The shared client serialises the body; stringifying here would send a JSON
  // string inside JSON and the server would reject it as a non-object.
  return request<{ applied: string[] }>('/config', {
    method: 'PUT',
    body: payload,
  });
}

export function fetchModelsStatus(): Promise<ModelsStatus> {
  return request<ModelsStatus>('/models/status');
}

export function downloadModel(): Promise<ModelsDownloadResult> {
  return request<ModelsDownloadResult>('/models/download', { method: 'POST' });
}