/**
 * Dashed edge program for Sigma 3.
 *
 * Sigma 3 ships `EdgeLineProgram` (constant-thickness GL lines) and
 * `EdgeRectangleProgram` (tapered rectangles). Neither can express "this edge
 * is semantic evidence, not a structural fact", which the visual contract
 * requires. This subclasses the rectangle program — so thickness, hover
 * highlighting, clamping and picking all keep working — and swaps only the
 * fragment shader for one that discards fragments in a screen-space dash
 * pattern.
 *
 * Anchoring the dash to `gl_FragCoord` rather than to the edge's own length
 * keeps the pattern visually constant under pan and zoom, which is what makes a
 * dashed edge read as annotation rather than as one more solid edge.
 */

import { EdgeRectangleProgram } from 'sigma/rendering';
import type { Attributes } from 'graphology-types';

/** Dash pattern in device pixels: 9 on, 7 off. */
const DASH_LENGTH = 9.0;
const GAP_LENGTH = 7.0;

const DASHED_FRAGMENT_SHADER = /* glsl */ `
precision mediump float;

varying vec4 v_color;

const float DASH_LENGTH = ${DASH_LENGTH.toFixed(1)};
const float PERIOD = ${(DASH_LENGTH + GAP_LENGTH).toFixed(1)};

void main() {
  #ifdef PICKING_MODE
    // Picking stays solid. A dashed hit area would leave semantic edges
    // unpickable inside every gap, which is worse than a slightly larger
    // click target.
    gl_FragColor = v_color;
  #else
    float phase = mod(gl_FragCoord.x + gl_FragCoord.y, PERIOD);
    if (phase > DASH_LENGTH) discard;
    gl_FragColor = v_color;
  #endif
}
`;

/**
 * Dashed variant of Sigma's `EdgeRectangleProgram`.
 *
 * Registered as edge type `dashed` so an edge's `type` attribute selects
 * between a solid and a dashed draw without any branching in the reducer. The
 * generics are propagated so the class stays assignable to Sigma's
 * `EdgeProgramType` for this app's attribute types.
 */
export class DashedEdgeProgram<
  N extends Attributes = Attributes,
  E extends Attributes = Attributes,
  G extends Attributes = Attributes,
> extends EdgeRectangleProgram<N, E, G> {
  override getDefinition() {
    const definition = super.getDefinition();
    return { ...definition, FRAGMENT_SHADER_SOURCE: DASHED_FRAGMENT_SHADER };
  }
}