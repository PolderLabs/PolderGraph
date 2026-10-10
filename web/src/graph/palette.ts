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
  /** Inferred / ambiguous edges: red, never a structural hue. */
  unresolvedEdge: string;
  background: string;
  surface: string;
  text: string;
  /** Text colour used on top of bright, filled shapes (dark in both themes). */
  labelOnLight: string;
  /** Text colour used on top of dark, filled shapes. */
  labelOnDark: string;
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
    workspace: '#8b5cf6',
    repository: '#a855f7',
    directory: '#4c8dff',
    file: '#38bdf8',
    module: '#22d3ee',

    namespace: '#2dd4bf',
    package: '#14b8a6',
    class: '#ffc93c',
    interface: '#fde047',
    trait: '#facc15',
    enum: '#fbbf24',
    type_alias: '#e3e048',

    function: '#ff5a3c',
    method: '#ff7a45',
    constructor: '#f04438',
    endpoint: '#ff8a5c',

    property: '#a3e635',
    field: '#84cc16',
    constant: '#bef264',
    variable: '#9ccc3c',

    test: '#c084fc',
    document: '#94a3b8',
    section: '#60a5fa',
    image: '#f472b6',
    audio_segment: '#e879f9',
    video_segment: '#d946ef',

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
    default: 'rgba(148, 170, 200, 0.55)',
    structural: 'rgba(176, 200, 228, 0.7)',
    contains: 'rgba(146, 178, 234, 0.6)',
    defines: 'rgba(230, 186, 100, 0.66)',
    imports: 'rgba(110, 182, 240, 0.66)',
    exports: 'rgba(88, 208, 228, 0.66)',
    calls: 'rgba(244, 152, 108, 0.72)',
    constructs: 'rgba(238, 142, 100, 0.66)',
    inherits: 'rgba(222, 170, 100, 0.62)',
    implements: 'rgba(206, 184, 130, 0.62)',
    overrides: 'rgba(236, 202, 116, 0.62)',
    references: 'rgba(166, 184, 208, 0.55)',
    reads: 'rgba(190, 200, 116, 0.58)',
    writes: 'rgba(182, 194, 105, 0.58)',
    returns_type: 'rgba(242, 214, 138, 0.55)',
    accepts_type: 'rgba(242, 214, 138, 0.5)',
    decorates: 'rgba(158, 142, 252, 0.62)',
    routes_to: 'rgba(255, 150, 120, 0.62)',
    tests: 'rgba(168, 144, 246, 0.64)',
    documents: 'rgba(126, 184, 232, 0.6)',
    semantically_related: 'rgba(140, 228, 202, 0.6)',
    semantic: 'rgba(140, 228, 202, 0.6)',
  },
  unresolvedEdge: 'rgba(255, 122, 122, 0.5)',
  background: '#08090c',
  surface: '#101318',
  text: '#e6edf5',
  labelOnLight: '#0b0e14',
  labelOnDark: '#f2f7ff',
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
    default: 'rgba(60, 80, 110, 0.5)',
    structural: 'rgba(50, 72, 104, 0.6)',
    contains: 'rgba(63, 111, 216, 0.55)',
    defines: 'rgba(184, 121, 26, 0.58)',
    imports: 'rgba(47, 134, 207, 0.58)',
    exports: 'rgba(29, 159, 184, 0.58)',
    calls: 'rgba(209, 89, 31, 0.66)',
    constructs: 'rgba(200, 88, 40, 0.6)',
    inherits: 'rgba(170, 120, 40, 0.58)',
    implements: 'rgba(160, 140, 80, 0.56)',
    overrides: 'rgba(194, 144, 31, 0.58)',
    references: 'rgba(80, 100, 130, 0.52)',
    reads: 'rgba(120, 135, 50, 0.54)',
    writes: 'rgba(110, 128, 44, 0.54)',
    returns_type: 'rgba(160, 130, 30, 0.52)',
    accepts_type: 'rgba(150, 125, 40, 0.48)',
    decorates: 'rgba(107, 82, 221, 0.58)',
    routes_to: 'rgba(224, 80, 58, 0.58)',
    tests: 'rgba(116, 66, 214, 0.6)',
    documents: 'rgba(63, 119, 173, 0.56)',
    semantically_related: 'rgba(30, 145, 120, 0.6)',
    semantic: 'rgba(30, 145, 120, 0.6)',
  },
  unresolvedEdge: 'rgba(220, 38, 38, 0.72)',
  background: '#f7f9fc',
  surface: '#ffffff',
  text: '#131820',
  labelOnLight: '#0b0e14',
  labelOnDark: '#f7f9fc',
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

/**
 * Edge colors.
 *
 * Three evidence classes, three visually distinct treatments: a resolved
 * structural fact uses the edge type's own hue; semantic similarity uses the
 * teal semantic hue (drawn dashed by the edge reducer); and an inferred or
 * ambiguous edge uses the unresolved red, never a structural hue, so a
 * guess can never be misread as a fact.
 */
export function edgeColor(
  type: EdgeType,
  provenance: Provenance,
  palette: Palette,
): string {
  if (isSemanticEdge(type)) return palette.edge.semantic ?? palette.edge.default;
  if (UNRESOLVED_PROVENANCE[provenance]) return palette.unresolvedEdge;
  return palette.edge[type] ?? palette.edge.default;
}

export interface SizeScale {
  min: number;
  max: number;
}

/**
 * Node radii in **device pixels**.
 *
 * Sigma 3's `itemSizesReference: "screen"` setting makes `size` a pixel
 * diameter, so these bounds are directly comparable to the canvas and cannot
 * collapse to sub-pixel discs when the graph is normalised into [0,1]. A
 * radius of 4..14 px keeps a 1000-node graph legible and clickable.
 */
export const DEFAULT_SIZE_SCALE: SizeScale = { min: 1.6, max: 11 };

/** Larger bound used for community meta-nodes, which represent many entities. */
export const AGGREGATE_SIZE_SCALE: SizeScale = { min: 9, max: 26 };

/**
 * Bounded scale over degree/importance.
 *
 * The signal is the square root of importance plus the log of degree: a linear
 * importance is heavily right-skewed (PageRank), so without the root a handful
 * of hubs would swallow the whole size range. The result is clamped into
 * `[0,1]` and mapped onto pixel radii, so a 1000x degree range stays inside a
 * 3.5x size range.
 */
export function sizeForImportance(importance: number, degree: number, scale: SizeScale): number {
  const signal = Math.max(
    0,
    Math.sqrt(Math.max(importance, 0) * 10 + Math.log1p(Math.max(degree, 0)) / 2),
  );
  const upper = Math.sqrt(1 + Math.log1p(500) / 2);
  const normalized = Math.min(1, signal / upper);
  return scale.min + (scale.max - scale.min) * normalized ** 0.7;
}

/**
 * Edge thickness in **device pixels**.
 *
 * A structural fact drawn from source reads stronger than evidence drawn from
 * embeddings, which reads stronger than a guess: three distinct bands, all
 * above the renderer-wide `minEdgeThickness` floor so nothing disappears
 * entirely when zoomed out.
 */
export function edgeSizeFor(provenance: Provenance, type: EdgeType): number {
  if (isSemanticEdge(type)) return 1.2;
  if (UNRESOLVED_PROVENANCE[provenance]) return 1.1;
  if (provenance === 'extracted') return 2.2;
  if (provenance === 'resolved') return 1.8;
  return 1.5;
}

/**
 * Relative luminance of a hex colour, per WCAG 2.x.
 *
 * Used to decide which of the two text colours is readable on a node, rather
 * than assuming every label sits on the dark canvas.
 */
function luminance(hex: string): number {
  const value = hex.replace('#', '');
  const full = value.length === 3 ? value.split('').map((c) => c + c).join('') : value;
  const channels = [0, 2, 4].map((offset) => {
    const raw = parseInt(full.slice(offset, offset + 2), 16) / 255;
    return raw <= 0.03928 ? raw / 12.92 : ((raw + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

/** WCAG contrast ratio between two hex colours. */
export function contrastRatio(foreground: string, background: string): number {
  const a = luminance(foreground);
  const b = luminance(background);
  const lighter = Math.max(a, b);
  const darker = Math.min(a, b);
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Picks the text colour that is actually readable on `background`.
 *
 * A node's label can land on the node itself, on its selection ring, or on the
 * canvas. A single fixed label colour assumed the canvas and became unreadable
 * on the bright highlight colours - 1.22:1 for the light text on the selection
 * ring, against the 4.5:1 that body text needs. Both candidates are now
 * measured and the readable one wins, which keeps highlighted, pinned and
 * hovered labels legible in either theme.
 */
export function readableTextOn(background: string, palette: Palette): string {
  const onLight = palette.labelOnLight;
  const onDark = palette.labelOnDark;
  return contrastRatio(onLight, background) >= contrastRatio(onDark, background)
    ? onLight
    : onDark;
}
