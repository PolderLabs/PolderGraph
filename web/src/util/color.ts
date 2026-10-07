/**
 * Cheap desaturation used to dim items that are not part of the current focus.
 *
 * Runs for every visible node and edge on each frame, so it avoids colour-space
 * conversions: a single-pass RGB mix against the Rec. 601 luma is accurate
 * enough for a visual fade and costs a few arithmetic operations.
 */
export function desaturate(rgba: string, amount: number): string {
  const match = /rgba?\(([^)]+)\)/.exec(rgba);
  if (!match) return rgba;

  const parts = match[1].split(',').map((part) => Number.parseFloat(part.trim()));
  if (parts.length < 3 || parts.some((part) => !Number.isFinite(part))) return rgba;

  const [r, g, b] = parts;
  const alpha = parts.length > 3 ? parts[3] : 1;
  const grey = 0.3 * r + 0.59 * g + 0.11 * b;
  const mix = (channel: number): number => Math.round(channel + (grey - channel) * amount);

  return `rgba(${mix(r)}, ${mix(g)}, ${mix(b)}, ${alpha})`;
}
