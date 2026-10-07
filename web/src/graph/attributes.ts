/**
 * Graph attributes this app owns, kept separate from the Sigma component so
 * both the renderer and the synchroniser share one definition.
 */

/** Attributes stored on every graph node. */
export interface PgNodeAttributes {
  x: number;
  y: number;
  size: number;
  label: string;
  kind: string;
  color: string;
  /** Read by Sigma's label drawing to colour the text per node. */
  labelColor: string;
  /** Read by the node-border WebGL program. */
  borderColor: string;
  borderSize: number;
  pgImportance: number;
  pgDegree: number;
  pgCommunity: string;
  pgUnresolved: number;
  pgChanged: number;
  pgPinned: number;
  fixed?: boolean;
}

/** Attributes stored on every graph edge. */
export interface PgEdgeAttributes {
  size: number;
  color: string;
  label: string;
  weight: number;
  edgeType: string;
  provenance: string;
  semantic: number;
  /** Endpoints, cached so Sigma reducers can test adjacency in O(1). */
  sourceId: string;
  targetId: string;
}
