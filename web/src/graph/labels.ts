/**
 * Node label drawing.
 *
 * Sigma's default label renderer paints text directly onto whatever is behind
 * it. On the graph that means a label can land on the dark canvas, on a bright
 * node, or on the highlight ring drawn around a selected node - and a single
 * fixed text colour cannot be readable against all three. Measured on the
 * highlight colours, light text reached only 1.22:1 against the selection ring.
 *
 * Rather than switching text colour per state and hoping, every label is drawn
 * on a small backing plate in the canvas colour first. The text then always has
 * the same background to contrast against, whichever node happens to be under
 * it, so a single readable text colour is enough.
 */

import type { NodeLabelDrawingFunction } from 'sigma/rendering';
import type { Attributes } from 'graphology-types';
import type { PgEdgeAttributes, PgNodeAttributes } from './attributes';
import type { Palette } from './palette';

/**
 * Palette used by the label renderer.
 *
 * Sigma captures the drawing function once, so the current theme is published
 * here for it to read at draw time rather than captured in a closure.
 */
let currentPalette: Palette | null = null;

export function setLabelPalette(palette: Palette): void {
  currentPalette = palette;
}

/** Corner radius of the label plate, in pixels. */
const PLATE_RADIUS = 3;
/** Gap between the node edge and the plate, in pixels. */
const PLATE_GAP = 3;

export const drawReadableNodeLabel: NodeLabelDrawingFunction<
  PgNodeAttributes,
  PgEdgeAttributes,
  Attributes
> = (
  context,
  data,
  settings,
) => {
  const label = data.label;
  if (!label) return;

  const palette = currentPalette;
  const fontSize = Number(settings.labelSize) || 12;
  const font = `${settings.labelWeight ?? '500'} ${fontSize}px ${settings.labelFont ?? 'sans-serif'}`;

  context.save();
  context.font = font;
  context.textBaseline = 'middle';
  context.textAlign = 'left';

  const radius = Number(data.size) || 1;
  const textX = data.x + radius + PLATE_GAP;
  const textY = data.y;

  // The plate is drawn in the canvas colour, so the text contrast ratio is the
  // same wherever the label happens to sit.
  const plateHeight = fontSize + 4;
  const plateTop = textY - plateHeight / 2;
  const plateWidth = context.measureText(label).width + 8;

  context.fillStyle = palette?.background ?? '#0e1117';
  context.globalAlpha = 0.88;
  context.beginPath();
  context.roundRect(textX - 4, plateTop, plateWidth, plateHeight, PLATE_RADIUS);
  context.fill();

  context.globalAlpha = 1;
  context.fillStyle = data.labelColor ?? palette?.text ?? '#e6edf5';
  context.fillText(label, textX, textY);
  context.restore();
};