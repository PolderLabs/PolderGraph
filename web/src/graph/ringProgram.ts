/**
 * Node ring (halo) program for Sigma 3.
 *
 * Sigma 3 draws a node as one filled disc and offers no per-node border, glow or
 * ring primitive. The visual contract still needs selected / changed /
 * unresolved / pinned to be distinguishable at a glance without stealing the
 * node's own colour, so a ring is drawn as a second program: a slightly larger
 * disc with a hollow centre.
 *
 * The ring is not a separate graph node. Sigma calls `processVisibleItem` once
 * per node per program, so the ring's geometry stays locked to its node even
 * while the layout is moving, and a node with no ring state emits no geometry
 * at all.
 *
 * Sigma's own circle vertex shader already exposes everything the fragment
 * stage needs (`v_diffVector` is this vertex's offset from the node centre,
 * `v_radius` is the node's rendered radius), so only the fragment shader is
 * replaced. `processVisibleItem` widens the uploaded size by the stroke so the
 * enlarged triangle covers the ring.
 */

import { NodeCircleProgram } from 'sigma/rendering';
import type { NodeDisplayData } from 'sigma/types';
import type { Attributes } from 'graphology-types';

/** Attributes the ring program reads off each node. */
export interface RingNodeAttributes {
  /** Ring color; a fully transparent value means "draw nothing". */
  pgRingColor: string;
  /** Ring stroke width in the same units as node size; 0 means "no ring". */
  pgRingSize: number;
}

type RingData = NodeDisplayData & RingNodeAttributes;

/** Sentinel the reducer writes for "no ring". */
const TRANSPARENT_RING = 'rgba(0,0,0,0)';

const RING_FRAGMENT_SHADER = /* glsl */ `
precision mediump float;

varying vec4 v_color;
varying vec2 v_diffVector;
varying float v_radius;
varying float v_border;

void main() {
  #ifdef PICKING_MODE
    // The ring is decoration and must never be clickable, or a selected node
    // would swallow clicks aimed at a neighbour behind it.
    discard;
  #else
    // Distance from the node centre, in the node's own size units.
    float dist = length(v_diffVector);
    // The stroke is carried as a fraction of the radius by the vertex stage, so
    // a one-unit feather stays visually constant for large and small nodes.
    float stroke = max(v_radius * 0.28, v_border);
    float inner = max(v_radius - stroke, 0.0);
    float feather = max(v_radius * 0.08, 1.0);
    float coverage = smoothstep(v_radius, v_radius - feather, dist)
                    * smoothstep(inner, inner + feather, dist);
    if (coverage <= 0.0) discard;
    gl_FragColor = vec4(v_color.rgb, v_color.a * coverage);
  #endif
}
`;

/**
 * Ring program, registered as node type `ringed`.
 *
 * `NodeCircleProgram` is subclassed so the vertex layout, attribute bindings and
 * size-uniform handling stay in lockstep with the stock disc program; only the
 * fragment shader differs. The generics are propagated so the class stays
 * assignable to Sigma's `NodeProgramType` for this app's attribute types.
 */
export class NodeRingProgram<
  N extends Attributes = Attributes,
  E extends Attributes = Attributes,
  G extends Attributes = Attributes,
> extends NodeCircleProgram<N, E, G> {
  override getDefinition() {
    const definition = super.getDefinition();
    return { ...definition, FRAGMENT_SHADER_SOURCE: RING_FRAGMENT_SHADER };
  }

  override processVisibleItem(nodeIndex: number, startIndex: number, data: NodeDisplayData): void {
    const ring = data as RingData;
    if (!(ring.pgRingSize > 0) || ring.pgRingColor === TRANSPARENT_RING) {
      // Collapse all three vertices onto the origin: the triangle degenerates to
      // a point and rasterises to nothing.
      this.array.fill(0, startIndex, startIndex + this.STRIDE);
      return;
    }
    // Widen the geometry so the ring sits outside the node's own disc.
    super.processVisibleItem(nodeIndex, startIndex, {
      ...data,
      size: data.size + ring.pgRingSize,
    });
  }
}