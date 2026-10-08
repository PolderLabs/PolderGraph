/**
 * Graph attributes this app owns, kept separate from the Sigma component so
 * both the renderer and the synchroniser share one definition.
 *
 * Sigma 3 draws a node as a filled disc; there is no per-node border or glow
 * primitive. A "ring" is therefore drawn as a second, larger, hollow disc
 * behind the node, which is why `pgRing*` exists alongside the fill color.
 */

/** Attributes stored on every graph node. */
export interface PgNodeAttributes {
  x: number;
  y: number;
  size: number;
  label: string;
  kind: string;
  /** Sigma 3 edge/node program selector. */
  type: string;
  color: string;
  /** Sigma 3 reads this when drawing the node label. */
  labelColor: string;
  /** Halo disc drawn behind the node: color, size and width in pixels. */
  pgRingColor: string;
  pgRingSize: number;
  /** Sigma 3 skips labels below this rendered size unless `forceLabel`. */
  labelRenderedSizeThreshold?: number;
  pgImportance: number;
  pgDegree: number;
  pgCommunity: string;
  /** 1 when the entity could not be resolved in the index. */
  pgUnresolved: number;
  /** 1 while the entity carries a "changed since Git base" marker. */
  pgChanged: number;
  pgPinned: number;
  /** Set by a drag; the layout controller treats it as a hard constraint. */
  fixed?: boolean;
}

/** Attributes stored on every graph edge. */
export interface PgEdgeAttributes {
  size: number;
  color: string;
  label: string;
  weight: number;
  /** Sigma 3 edge program selector: `line` (solid) or `dashed` (semantic). */
  type: string;
  edgeType: string;
  provenance: string;
  semantic: number;
  /** Endpoints, cached so Sigma reducers can test adjacency in O(1). */
  sourceId: string;
  targetId: string;
}