import { useEffect, useState } from 'react';
import { api, isAbortError } from '../api/client';
import { describeError } from '../util/errors';

export interface SourceDialogProps {
  path: string;
  line: number | null;
  editorCommand: string;
  onClose: () => void;
}

interface SourceState {
  content: string | null;
  startLine: number;
  endLine: number;
  error: { code: string; message: string; remediation: string | null } | null;
  loading: boolean;
}

/**
 * Source preview.
 *
 * The path always originates from an indexed entity, so the request goes to
 * `/api/source` — the client never fetches an arbitrary filesystem location and
 * never renders server text as markup.
 */
export function SourceDialog(props: SourceDialogProps): JSX.Element {
  const { path, line, editorCommand, onClose } = props;
  const [state, setState] = useState<SourceState>({
    content: null,
    startLine: 0,
    endLine: 0,
    error: null,
    loading: true,
  });

  useEffect(() => {
    const controller = new AbortController();
    setState((previous) => ({ ...previous, loading: true, error: null }));

    api.source({ path }, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        setState({
          content: data.content,
          startLine: data.start_line,
          endLine: data.end_line,
          error: null,
          loading: false,
        });
      })
      .catch((error: unknown) => {
        if (isAbortError(error)) return;
        setState({
          content: null,
          startLine: 0,
          endLine: 0,
          error: describeError(error),
          loading: false,
        });
      });

    return () => controller.abort();
  }, [path]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  const openInEditor = () => {
    const command = editorCommand
      .replaceAll('{file}', path)
      .replaceAll('{line}', String(line ?? 1));
    // Launches the user's configured local editor; no network egress.
    window.open(command, '_self');
  };

  const lines = state.content ? state.content.split('\n') : [];

  return (
    <div
      className="modalBackdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="modal modal--wide" role="dialog" aria-modal="true" aria-label={`Source of ${path}`}>
        <header className="modal__header">
          <h2 className="modal__path">{path}</h2>
          <button type="button" className="modal__close" onClick={onClose} aria-label="Close source">
            ×
          </button>
        </header>

        {state.loading && <p className="modal__hint">Loading source…</p>}

        {state.error && (
          <div className="canvasMessage canvasMessage--error">
            <h3>{state.error.code}</h3>
            <p>{state.error.message}</p>
            {state.error.remediation && <p className="canvasMessage__remedy">{state.error.remediation}</p>}
          </div>
        )}

        {state.content !== null && (
          <pre className="source">
            {lines.map((text, index) => {
              const lineNumber = state.startLine + index;
              const isTarget = line !== null && lineNumber === line;
              return (
                <span key={lineNumber} className={isTarget ? 'source__line source__line--hit' : 'source__line'}>
                  <span className="source__number">{lineNumber}</span>
                  <span className="source__text">{text}</span>
                </span>
              );
            })}
          </pre>
        )}

        <footer className="modal__footer">
          <button type="button" onClick={openInEditor}>
            Open in editor
          </button>
          <button type="button" className="modal__primary" onClick={onClose}>
            Close
          </button>
        </footer>
      </div>
    </div>
  );
}
