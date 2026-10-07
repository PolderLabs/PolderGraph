/**
 * Ambient types for `graphology-layout-forceatlas2/iterate`.
 *
 * The package ships typings for its main entrypoint and its worker supervisor
 * but not for the single-iteration function, which `src/graph/fa2.worker.ts`
 * uses to run ForceAtlas2 off the UI thread under its own pause/resume
 * protocol.
 */
declare module 'graphology-layout-forceatlas2/iterate' {
  import type { ForceAtlas2Settings } from 'graphology-layout-forceatlas2';

  /**
   * Applies exactly one ForceAtlas2 iteration.
   * Both matrices are mutated in place; positions live at stride 10.
   */
  export default function iterate(
    settings: ForceAtlas2Settings,
    nodeMatrix: Float32Array,
    edgeMatrix: Float32Array,
  ): void;
}
