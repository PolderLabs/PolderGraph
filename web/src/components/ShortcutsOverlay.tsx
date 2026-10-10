import { useEffect } from 'react';
import { IconClose } from './Icons';

/** Keyboard shortcuts, shown on demand so the canvas is not cluttered by hints. */
const SHORTCUTS: [string, string][] = [
  ['F', 'Fit the graph to the canvas'],
  ['Space', 'Pause or resume the layout'],
  ['R', 'Re-seed the layout'],
  ['L', 'Toggle labels'],
  ['K', 'Toggle the legend'],
  ['S', 'Open settings'],
  ['/', 'Focus search'],
  ['Esc', 'Clear the selection'],
  ['?', 'Show or hide this list'],
];

export function ShortcutsOverlay({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}): JSX.Element | null {
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div
      className="shortcuts"
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts"
      onClick={onClose}
    >
      <div className="shortcuts__panel" onClick={(event) => event.stopPropagation()}>
        <div className="settings__cardHead">
          <h2 className="shortcuts__title">Keyboard shortcuts</h2>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={onClose}
            aria-label="Close shortcuts"
          >
            <IconClose size={14} />
          </button>
        </div>
        <dl className="shortcuts__list">
          {SHORTCUTS.map(([key, description]) => (
            <div key={key} style={{ display: 'contents' }}>
              <dt>
                <kbd>{key}</kbd>
              </dt>
              <dd>{description}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}