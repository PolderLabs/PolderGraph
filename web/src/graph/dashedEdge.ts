import { EdgeProgram } from 'sigma/rendering';
import type { ProgramInfo } from 'sigma/rendering';
import type { EdgeDisplayData, NodeDisplayData, RenderParams } from 'sigma/types';
import { floatColor } from 'sigma/utils';

const UNIFORMS = ['u_matrix'] as const;

/**
 * Fragment shader that discards fragments to produce a dash pattern.
 *
 * Sigma's stock edge programs have no dash support, and semantic edges must
 * never be mistaken for structural facts, so semantic evidence gets its own
 * dashed line program rather than a slightly different color.
 */
const FRAGMENT_SHADER_SOURCE = /* glsl */ `
precision mediump float;

varying vec4 v_color;
varying float v_lineLength;

void main(void) {
  if (v_lineLength > 0.0 && fract(v_lineLength / 12.0) > 0.55) {
    discard;
  }
  gl_FragColor = v_color;
}
`;

const VERTEX_SHADER_SOURCE = /* glsl */ `
attribute vec4 a_id;
attribute vec4 a_color;
attribute vec2 a_position;
attribute float a_lineLength;

uniform mat3 u_matrix;

varying vec4 v_color;
varying float v_lineLength;

const float bias = 255.0 / 254.0;

void main() {
  gl_Position = vec4(
    (u_matrix * vec3(a_position, 1)).xy,
    0,
    1
  );

  #ifdef PICKING_MODE
  v_color = a_id;
  #else
  v_color = a_color;
  #endif

  v_color.a *= bias;
  v_lineLength = a_lineLength;
}
`;

/**
 * A dashed straight-line edge program used for semantic relationships.
 *
 * Picking mode keeps the same geometry as the stock program so hit-testing
 * behaves identically; only the rendered pixels are dashed.
 */
export class EdgeDashedProgram extends EdgeProgram<(typeof UNIFORMS)[number]> {
  getDefinition() {
    return {
      VERTICES: 2,
      VERTEX_SHADER_SOURCE,
      FRAGMENT_SHADER_SOURCE,
      METHOD: 1, // gl.LINES
      UNIFORMS,
      ATTRIBUTES: [
        { name: 'a_position', size: 2, type: 5126 as const },
        { name: 'a_color', size: 4, type: 5121 as const, normalized: true },
        { name: 'a_id', size: 4, type: 5121 as const, normalized: true },
        { name: 'a_lineLength', size: 1, type: 5126 as const },
      ],
    };
  }

  override processVisibleItem(
    edgeIndex: number,
    startIndex: number,
    sourceData: NodeDisplayData,
    targetData: NodeDisplayData,
    data: EdgeDisplayData,
  ): void {
    const array = this.array;
    const x1 = sourceData.x;
    const y1 = sourceData.y;
    const x2 = targetData.x;
    const y2 = targetData.y;
    const color = floatColor(data.color);
    const length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);

    array[startIndex++] = x1;
    array[startIndex++] = y1;
    array[startIndex++] = color;
    array[startIndex++] = edgeIndex;
    array[startIndex++] = length;

    array[startIndex++] = x2;
    array[startIndex++] = y2;
    array[startIndex++] = color;
    array[startIndex++] = edgeIndex;
    array[startIndex++] = length;
  }

  override setUniforms(params: RenderParams, { gl, uniformLocations }: ProgramInfo): void {
    gl.uniformMatrix3fv(uniformLocations.u_matrix, false, params.matrix);
  }
}
