import type { EdgeType, NodeKind, Provenance } from '../api/types';

/**
 * Visual encoding for the graph.
 *
 * The palette is deliberately small and hue-grouped so the canvas reads as a
 * map rather than confetti: containers/structure in cool blues, code in warm
 * ambers, content and tests in greens/purples, unresolved work in red.
 */

export type ColorMode = 'kind' | 'community';

export interface Palette {
  node: Record<string, string>;
  /** Categorical ramp used when coloring by community. */
  communityRamp: string[];
  edge: Record<string, string>;
  background: string;
  surface: string;
  text: string;
  textMuted: string;
  accent: string;
  selected: string;
  changed: string;
  unresolved: string;
  path: string;
}

/** Semantic similarity edges must never read as a structural fact. */
export const SEMANTIC_EDGE_TYPE = 'semantically_related';

export const isSemanticEdge = (type: EdgeType): boolean =>
  type === SEMANTIC_EDGE_TYPE || type === 'semantic';

/** Unresolved / ambiguous work gets its own hue, never a structural color. */
export const UNRESOLVED_KINDS: Record<string, boolean> = {
  unknown_symbol: true,
};

export const UNRESOLVED_PROVENANCE: Record<string, boolean> = {
  ambiguous: true,
  inferred: true,
};

export const DARK: Palette = {
  node: {
    workspace: '#7c6cf5',
    repository: '#8f7cf7',
    directory: '#6f8fe8',
    file: '#5fa8e8',
    module: '#48c2d8',

    namespace: '#4fb9a7',
    package: '#43c9b0',
    class: '#e0b055',
    interface: '#e8c46a',
    trait: '#e3bd63',
    enum: '#d9a94f',
    type_alias: '#efd07d',

    function: '#f08a5d',
    method: '#f5a06c',
    constructor: '#e8825a',
    endpoint: '#ff8a6b',

    property: '#b7c26a',
    field: '#aeba5f',
    constant: '#c9d477',
    variable: '#adba66',

    test: '#9b7ff0',
    document: '#6fa8dc',
    section: '#5f9bd0',
    image: '#cf7fbf',
    audio_segment: '#c173c9',
    video_segment: '#b96cc4',

    unknown_symbol: '#ff6b6b',
  },
  communityRamp: [
    '#5b8ff9',
    '#61ddaa',
    '#f6bd16',
    '#7262fd',
    '#78d3f8',
    '#9661bc',
    '#f6903d',
    '#008685',
    '#f08bb4',
    '#e8684a',
    '#6dc8ec',
    '#269eb9',
    '#ff99c3',
    '#c2c8d5',
    '#b6e3f5',
    '#d3c6ea',
    '#ffd8b8',
    '#aad8d8',
    '#ff6b6b',
    '#b2df8a',
  ],
  edge: {
    default: 'rgba(148, 170, 200, 0.34)',
    structural: 'rgba(160, 186, 216, 0.46)',
    contains: 'rgba(126, 158, 214, 0.36)',
    defines: 'rgba(224, 176, 85, 0.46)',
    imports: 'rgba(95, 168, 232, 0.46)',
    exports: 'rgba(72, 194, 216, 0.46)',
    calls: 'rgba(240, 138, 93, 0.58)',
    constructs: 'rgba(232, 130, 90, 0.5)',
    inherits: 'rgba(215, 160, 90, 0.5)',
    implements: 'rgba(199, 176, 120, 0.5)',
    overrides: 'rgba(232, 196, 106, 0.5)',
    references: 'rgba(150, 170, 196, 0.4)',
    reads: 'rgba(183, 194, 106, 0.42)',
    writes: 'rgba(174, 186, 95, 0.42)',
    returns_type: 'rgba(239, 208, 125, 0.4)',
    accepts_type: 'rgba(239, 208, 125, 0.36)',
    decorates: 'rgba(143, 124, 247, 0.45)',
    routes_to: 'rgba(255, 138, 107, 0.45)',
    tests: 'rgba(155, 127, 240, 0.48)',
    documents: 'rgba(111, 168, 220, 0.44)',
    semantically_related: 'rgba(122, 216, 190, 0.34)',
    semantic: 'rgba(122, 216, 190, 0.34)',
  },
  background: '#0e1117',
  surface: '#151a23',
  text: '#e6edf5',
  textMuted: '#8b98a9',
  accent: '#6ea8fe',
  selected: '#ffd166',
  changed: '#4ade80',
  unresolved: '#ff6b6b',
  path: '#f472b6',
};

export const LIGHT: Palette = {
  ...DARK,
  node: {
    ...DARK.node,
    workspace: '#5b45d6',
    repository: '#6b52dd',
    directory: '#3f6fd8',
    file: '#2f86cf',
    module: '#1d9fb8',
    class: '#b8791a',
    interface: '#c2901f',
    function: '#d1591f',
    method: '#dd7327',
    endpoint: '#e0503a',
    test: '#7442d6',
    document: '#3f77ad',
    image: '#a83fa0',
    unknown_symbol: '#d92c2c',
  },
  edge: {
    default: 'rgba(60, 80, 110, 0.3)',
    structural: 'rgba(50, 72, 104, 0.42)',
    contains: 'rgba(63, 111, 216, 0.34)',
    defines: 'rgba(184, 121, 26, 0.42)',
    imports: 'rgba(47, 134, 207, 0.42)',
    exports: 'rgba(29, 159, 184, 0.42)',
    calls: 'rgba(209, 89, 31, 0.52)',
    constructs: 'rgba(200, 88, 40, 0.46)',
    inherits: 'rgba(170, 120, 40, 0.46)',
    implements: 'rgba(160, 140, 80, 0.44)',
    overrides: 'rgba(194, 144, 31, 0.46)',
    references: 'rgba(80, 100, 130, 0.36)',
    reads: 'rgba(120, 135, 50, 0.38)',
    writes: 'rgba(110, 128, 44, 0.38)',
    returns_type: 'rgba(160, 130, 30, 0.36)',
    accepts_type: 'rgba(150, 125, 40, 0.32)',
    decorates: 'rgba(107, 82, 221, 0.42)',
    routes_to: 'rgba(224, 80, 58, 0.42)',
    tests: 'rgba(116, 66, 214, 0.44)',
    documents: 'rgba(63, 119, 173, 0.4)',
    semantically_related: 'rgba(30, 145, 120, 0.36)',
    semantic: 'rgba(30, 145, 120, 0.36)',
  },
  background: '#f7f9fc',
  surface: '#ffffff',
  text: '#131820',
  textMuted: '#5a6676',
  accent: '#2563eb',
  selected: '#b45309',
  changed: '#15803d',
  unresolved: '#dc2626',
  path: '#db2777',
};

export const PALETTES = { dark: DARK, light: LIGHT } as const;
export type ThemeName = keyof typeof PALETTES;

/**
 * Stable hue for an arbitrary community id.
 *
 * Communities are integers whose meaning differs between structural and hybrid
 * detection, so the hue is derived from the id alone and is *not* comparable
 * across modes — the UI states the active mode instead.
 */
export function communityColor(community: number | string | null | undefined, ramp: string[]): string {
  if (community === null || community === undefined || community === '') {
    return ramp[ramp.length - 1];
  }
  const numeric =
    typeof community === 'number'
      ? community
      : Number.parseInt(community, 10);
  const hash = Number.isFinite(numeric)
    ? Math.abs(numeric)
    : Array.from(String(community)).reduce((acc, ch) => (acc * 31 + ch.charCodeAt(0)) % 100000, 7);
  return ramp[hash % ramp.length];
}

export function nodeColorForKind(kind: NodeKind, palette: Palette): string {
  return palette.node[kind] ?? palette.node.default ?? '#7f8ea3';
}

/** Edge colors: semantic is lighter and dashed, inferred/ambiguous desaturated. */
export function edgeColor(
  type: EdgeType,
  provenance: Provenance,
  palette: Palette,
): string {
  const base = palette.edge[type] ?? palette.edge.default;
  if (isSemanticEdge(type)) return base;
  if (UNRESOLVED_PROVENANCE[provenance]) return 'rgba(255, 122, 122, 0.36)';
  if (provenance === 'resolved' || provenance === 'extracted') return base;
  return base;
}

export interface SizeScale {
  min: number;
  max: number;
}

export const DEFAULT_SIZE_SCALE: SizeScale = { min: 2.4, max: 16 };

/**
 * Bounded sqrt scale over degree/importance.
 *
 * Squaring the input would make a handful of hubs the whole canvas; a square
 * root keeps a 100x degree range inside ~10x size range.
 */
export function sizeForImportance(importance: number, degree: number, scale: SizeScale): number {
  const signal = Math.max(0, Math.sqrt(Math.max(importance, 0) + Math.log1p(Math.max(degree, 0))));
  const upper = Math.sqrt(1 + Math.log1p(500));
  const normalized = Math.min(1, signal / upper);
  return scale.min + (scale.max - scale.min) * Math.pow(normalized, 0.7);
}

export function edgeSizeFor(
  provenance: Provenance,
  type: EdgeType,
  base = 1,
): number {
  if (isSemanticEdge(type)) return Math.max(0.6, base * 0.75);
  if (UNRESOLVED_PROVENANCE[provenance]) return Math.max(0.6, base * 0.8);
  if (provenance === 'extracted') return base * 1.35;
  if (provenance === 'resolved') return base * 1.2;
  return base;
}
