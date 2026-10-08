/**
 * Sigma configured so its canvases can be read back.
 *
 * Sigma creates its WebGL contexts with `preserveDrawingBuffer: false`, the
 * default and the faster option: the drawing buffer is discarded once the frame
 * is composited. That makes the canvas unreadable from outside — `drawImage`
 * into a 2D context (the only correct way to read a composited WebGL canvas;
 * `readPixels` reads the cleared buffer) yields all zeros unless the read
 * happens inside the very frame that drew.
 *
 * Overriding the context factory in a subclass rather than patching
 * `Sigma.prototype` keeps the change local to this app and keeps the stock
 * behaviour available for anyone who wants it. The cost is one extra buffer
 * retention per frame.
 */

import Sigma from 'sigma';
import type { Attributes } from 'graphology-types';

export class MeasuredSigma<
  N extends Attributes = Attributes,
  E extends Attributes = Attributes,
  G extends Attributes = Attributes,
> extends Sigma<N, E, G> {
  override createWebGLContext(
    id: string,
    options: Parameters<Sigma<N, E, G>['createWebGLContext']>[1] = {},
  ): WebGLRenderingContext {
    return super.createWebGLContext(id, { ...options, preserveDrawingBuffer: true });
  }
}