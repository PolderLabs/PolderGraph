import type { ChangeEvent } from './types';

export type EventsStatus = 'connecting' | 'open' | 'closed';

export interface EventsClientOptions {
  /** Called for each parsed `event: change` payload. */
  onChange: (change: ChangeEvent) => void;
  /** Called when the connection state transitions. */
  onStatus?: (status: EventsStatus) => void;
  /** Called on transport errors; the client keeps retrying regardless. */
  onError?: (error: Error) => void;
  /** Base delay before reconnecting. Doubles up to `maxBackoffMs`. */
  baseBackoffMs?: number;
  maxBackoffMs?: number;
}

interface Block {
  event: string;
  data: string;
}

/**
 * Parses a raw SSE text buffer into complete event blocks.
 * Exported for reuse by tests and future transports.
 */
export function parseSseBlocks(buffer: string): { blocks: Block[]; rest: string } {
  const normalized = buffer.replace(/\r\n/g, '\n');
  const parts = normalized.split('\n\n');
  const rest = parts.pop() ?? '';
  const blocks: Block[] = [];

  for (const part of parts) {
    if (!part.trim()) continue;
    let event = 'message';
    const dataLines: string[] = [];
    for (const line of part.split('\n')) {
      if (line.startsWith(':')) continue; // comment / keep-alive
      if (line.startsWith('event:')) {
        event = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).replace(/^ /, ''));
      }
    }
    if (dataLines.length === 0) continue;
    blocks.push({ event, data: dataLines.join('\n') });
  }

  return { blocks, rest };
}

function toChangeEvent(raw: string): ChangeEvent | null {
  try {
    const parsed = JSON.parse(raw) as Partial<ChangeEvent>;
    const ids = Array.isArray(parsed.ids)
      ? parsed.ids.filter((value): value is string => typeof value === 'string')
      : [];
    const kind = typeof parsed.kind === 'string' ? parsed.kind : 'unknown';
    return { kind, ids };
  } catch {
    return null;
  }
}

/**
 * Server-Sent Events client for `GET /api/events`.
 *
 * `EventSource` reconnects on its own but loses buffered payloads across a
 * dropped connection, so the stream is driven manually with
 * `Last-Event-ID` support and exponential backoff. Idle periods are expected:
 * a quiet server simply sends nothing.
 */
export class EventsClient {
  private source: EventSource | null = null;
  private timer: number | null = null;
  private closed = false;
  private attempt = 0;
  private readonly options: {
    onChange: (change: ChangeEvent) => void;
    onStatus: (status: EventsStatus) => void;
    onError: (error: Error) => void;
    baseBackoffMs: number;
    maxBackoffMs: number;
  };

  constructor(options: EventsClientOptions) {
    this.options = {
      onChange: options.onChange,
      onStatus: options.onStatus ?? (() => undefined),
      onError: options.onError ?? (() => undefined),
      baseBackoffMs: options.baseBackoffMs ?? 1000,
      maxBackoffMs: options.maxBackoffMs ?? 15000,
    };
  }

  start(): void {
    if (this.closed) return;
    this.attempt = 0;
    this.open();
  }

  close(): void {
    this.closed = true;
    if (this.timer !== null) {
      window.clearTimeout(this.timer);
      this.timer = null;
    }
    this.source?.close();
    this.source = null;
    this.options.onStatus?.('closed');
  }

  private open(): void {
    if (this.closed) return;

    this.options.onStatus?.('connecting');

    // `withCredentials` stays false: same-origin, no cookies, no remote hosts.
    const source = new EventSource('/api/events', { withCredentials: false });
    this.source = source;

    // The browser manages `Last-Event-ID` on reconnect; nothing to set here.
    source.addEventListener('change', (event) => {
      const change = toChangeEvent((event as MessageEvent<string>).data);
      if (change) this.options.onChange(change);
    });

    source.onopen = () => {
      this.attempt = 0;
      this.options.onStatus?.('open');
    };

    source.onerror = () => {
      source.close();
      this.source = null;
      this.options.onError?.(new Error('Live update stream disconnected.'));
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect(): void {
    if (this.closed || this.timer !== null) return;
    const delay = Math.min(
      this.options.maxBackoffMs,
      this.options.baseBackoffMs * 2 ** this.attempt,
    );
    this.attempt += 1;
    this.timer = window.setTimeout(() => {
      this.timer = null;
      this.open();
    }, delay);
  }
}
