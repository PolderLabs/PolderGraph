import type { ColorMode, ThemeName } from '../graph/palette';

/**
 * Layout controls, named after the forces the simulation actually applies.
 *
 * These replaced the ForceAtlas2 knobs, which had no effect on the d3-force
 * model that now drives the graph.
 */
export interface ForceSettingsState {
  /** Repulsion between nodes. More negative spreads the graph further apart. */
  chargeStrength: number;
  /** Spring strength along edges. Higher pulls related code closer together. */
  linkStrength: number;
  /** Preferred distance between connected nodes. */
  linkDistance: number;
  /**
   * How hard the layout's centroid is pulled to the middle of the view. 1
   * fully recentres it each tick; 0 leaves it wherever it drifted.
   */
  centerStrength: number;
  /** Velocity kept per tick. Lower settles faster and moves less. */
  velocityDecay: number;
  /** Gap kept between node circles when overlaps are resolved. */
  collisionPadding: number;
}

export interface LocalViewState {
  depth: number;
  direction: 'in' | 'out' | 'both';
  structuralOnly: boolean;
  fanout: number;
}

export interface FiltersState {
  text: string;
  kinds: Record<string, boolean>;
  languages: Record<string, boolean>;
  roots: Record<string, boolean>;
  communities: Record<string, boolean>;
  edgeTypes: Record<string, boolean>;
  provenance: Record<string, boolean>;
  minSimilarity: number;
  hideGenerated: boolean;
  hideExternal: boolean;
  onlyTests: boolean;
  onlyDocs: boolean;
  onlySource: boolean;
  onlyMedia: boolean;
  changedSinceGitBase: boolean;
}

export interface ViewPreferencesState {
  theme: ThemeName;
  colorMode: ColorMode;
  showLegend: boolean;
  showLabels: boolean;
  hideLowValueEdges: boolean;
  communityMode: 'structural' | 'hybrid';
  collapseCommunities: boolean;
  globalLimit: number;
  aggregate: 'none' | 'directory' | 'community';
  force: ForceSettingsState;
  local: LocalViewState;
  filters: FiltersState;
}

export const DEFAULT_FORCE: ForceSettingsState = {
  chargeStrength: -260,
  linkStrength: 0.55,
  linkDistance: 46,
  centerStrength: 1,
  velocityDecay: 0.62,
  collisionPadding: 3,
};

export const DEFAULT_LOCAL: LocalViewState = {
  depth: 1,
  direction: 'both',
  structuralOnly: true,
  fanout: 24,
};

export const DEFAULT_FILTERS: FiltersState = {
  text: '',
  kinds: {},
  languages: {},
  roots: {},
  communities: {},
  edgeTypes: {},
  provenance: {},
  minSimilarity: 0.25,
  hideGenerated: true,
  hideExternal: false,
  onlyTests: false,
  onlyDocs: false,
  onlySource: false,
  onlyMedia: false,
  changedSinceGitBase: false,
};

export const DEFAULT_PREFERENCES: ViewPreferencesState = {
  theme: 'dark',
  colorMode: 'kind',
  showLegend: true,
  showLabels: true,
  hideLowValueEdges: true,
  communityMode: 'structural',
  collapseCommunities: false,
  globalLimit: 4000,
  aggregate: 'none',
  force: DEFAULT_FORCE,
  local: DEFAULT_LOCAL,
  filters: DEFAULT_FILTERS,
};

const STORAGE_KEY = 'poldergraph:view-preferences:v1';

function readStorage(): Partial<ViewPreferencesState> {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return {};
    return parsed as Partial<ViewPreferencesState>;
  } catch {
    // Private-mode or corrupted state must never block startup.
    return {};
  }
}

function writeStorage(value: ViewPreferencesState): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  } catch {
    // Storage unavailable (private browsing / quota): preferences stay in memory.
  }
}

/** Shallow-merges persisted state over the defaults, one level per section. */
export function loadPreferences(): ViewPreferencesState {
  const stored = readStorage();
  return {
    ...DEFAULT_PREFERENCES,
    ...stored,
    force: { ...DEFAULT_FORCE, ...(stored.force ?? {}) },
    local: { ...DEFAULT_LOCAL, ...(stored.local ?? {}) },
    filters: { ...DEFAULT_FILTERS, ...(stored.filters ?? {}) },
  };
}

export function savePreferences(preferences: ViewPreferencesState): void {
  writeStorage(preferences);
}

/** Node positions the user dragged, keyed by workspace view. */
const POSITION_KEY_PREFIX = 'poldergraph:positions:v1:';

export interface StoredPosition {
  x: number;
  y: number;
  fixed: boolean;
}

export function loadPositions(scope: string): Record<string, StoredPosition> {
  try {
    const raw = window.localStorage.getItem(POSITION_KEY_PREFIX + scope);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return {};
    return parsed as Record<string, StoredPosition>;
  } catch {
    return {};
  }
}

export function savePositions(scope: string, positions: Record<string, StoredPosition>): void {
  try {
    window.localStorage.setItem(POSITION_KEY_PREFIX + scope, JSON.stringify(positions));
  } catch {
    // Ignore: position persistence is a convenience, never a requirement.
  }
}
