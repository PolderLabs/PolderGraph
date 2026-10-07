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
