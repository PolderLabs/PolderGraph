import { ApiError, TransportError } from '../api/client';

export interface UiError {
  code: string;
  message: string;
  remediation: string | null;
}

/**
 * Normalises every failure shape into a renderable error state.
 *
 * The dashboard must never crash on a bad response, so any thrown value —
 * API envelope error, network failure, or an unexpected throw — is turned into
 * something the UI can display with an actionable hint.
 */
export function describeError(error: unknown): UiError {
  if (error instanceof ApiError) {
    return { code: error.code, message: error.message, remediation: error.remediation };
  }
  if (error instanceof TransportError) {
    return {
      code: 'api_unreachable',
      message: error.message,
      remediation: 'Make sure the PolderGraph server is running, then retry.',
    };
  }
  return {
    code: 'unexpected_error',
    message: error instanceof Error ? error.message : String(error),
    remediation: null,
  };
}

/**
 * Turn a raw retrieval-degradation reason into an actionable message.
 *
 * The server reports the cause ("semantic backend unavailable: ...") but not
 * what to do about it, so the dashboard adds the fix for the failures a user can
 * actually resolve.
 */
export function describeDegradation(reason: string): string {
  const text = reason.trim();
  if (/sentence-transformers is not installed/i.test(text)) {
    return 'Semantic recall is unavailable because the embedding library is not installed. Run `uv pip install "poldergraph[semantic]"`, then reindex with `poldergraph update`. Structural and lexical results are unaffected.';
  }
  if (/semantic backend unavailable/i.test(text)) {
    return 'Semantic recall was skipped. Structural, lexical and exact results are unaffected. Check `poldergraph status` for the configured embedding backend.';
  }
  if (/readonly database|database is locked|disk i\/o/i.test(text)) {
    return 'The index database could not be written. Another process may hold it; stop any running daemon with `poldergraph daemon stop` and retry.';
  }
  if (/vector search failed/i.test(text)) {
    return 'Vector search failed, so only structural and lexical evidence was used. Run `poldergraph doctor` to check index integrity.';
  }
  return `Retrieval ran in degraded mode: ${text}`;
}
