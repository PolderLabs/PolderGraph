import { useEffect, useState } from 'react';
import type { ColorMode, ThemeName } from '../graph/palette';
import type { CommunityMode } from '../graph/community';
import type { ViewPreferencesState } from '../state/preferences';

export interface SettingsDialogProps {
  open: boolean;
  preferences: ViewPreferencesState;
  onChange: (next: ViewPreferencesState) => void;
  onClose: () => void;
  onResetLayout: () => void;
  onClearPositions: () => void;
  editorCommand: string;
  onEditorCommandChange: (value: string) => void;
}

/** Global display and layout settings. */
export function SettingsDialog(props: SettingsDialogProps): JSX.Element | null {
  const { open, editorCommand, onClose } = props;
  const [draftEditor, setDraftEditor] = useState(editorCommand);

  useEffect(() => {
    if (open) setDraftEditor(editorCommand);
  }, [open, editorCommand]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  if (!props.open) return null;

  const update = (patch: Partial<ViewPreferencesState>) =>
    props.onChange({ ...props.preferences, ...patch });

  return (
    <div className="modalBackdrop" onMouseDown={(event) => {
      if (event.target === event.currentTarget) props.onClose();
    }}>
      <div className="modal" role="dialog" aria-modal="true" aria-label="Settings">
        <header className="modal__header">
          <h2>Settings</h2>
          <button type="button" className="modal__close" onClick={props.onClose} aria-label="Close settings">
            ×
          </button>
        </header>

        <section className="modal__section">
          <h3>Appearance</h3>
          <label className="field">
            <span className="field__label">Theme</span>
            <select
              className="field__input"
              value={props.preferences.theme}
              onChange={(event) => update({ theme: event.target.value as ThemeName })}
            >
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
          </label>

          <label className="field">
            <span className="field__label">Color nodes by</span>
            <select
              className="field__input"
              value={props.preferences.colorMode}
              onChange={(event) => update({ colorMode: event.target.value as ColorMode })}
            >
              <option value="kind">Node kind</option>
              <option value="community">Community</option>
            </select>
          </label>

          <ToggleRow
            label="Show labels"
            checked={props.preferences.showLabels}
            onChange={(value) => update({ showLabels: value })}
          />
          <ToggleRow
            label="Hide low-value edges until focus"
            checked={props.preferences.hideLowValueEdges}
            onChange={(value) => update({ hideLowValueEdges: value })}
          />
        </section>

        <section className="modal__section">
          <h3>Graph payload</h3>
          <label className="field">
            <span className="field__label">
              Global node limit <strong>{props.preferences.globalLimit}</strong>
            </span>
            <input
              type="range"
              min={200}
              max={20000}
              step={200}
              value={props.preferences.globalLimit}
              onChange={(event) => update({ globalLimit: Number(event.target.value) })}
            />
            <span className="field__hint">
              Large repositories are aggregated rather than fully rendered. Raise only if your machine can keep up.
            </span>
          </label>

          <label className="field">
            <span className="field__label">Aggregation</span>
            <select
              className="field__input"
              value={props.preferences.aggregate}
              onChange={(event) =>
                update({ aggregate: event.target.value as ViewPreferencesState['aggregate'] })
              }
            >
              <option value="none">None — individual entities</option>
              <option value="directory">Group by directory</option>
              <option value="community">Group by community</option>
            </select>
          </label>
        </section>

        <section className="modal__section">
          <h3>Communities</h3>
          <label className="field">
            <span className="field__label">Detection mode</span>
            <select
              className="field__input"
              value={props.preferences.communityMode}
              onChange={(event) => update({ communityMode: event.target.value as CommunityMode })}
            >
              <option value="structural">Structural — dependency reachability</option>
              <option value="hybrid">Hybrid — structure + embedding similarity</option>
            </select>
          </label>
          <ToggleRow
            label="Collapse communities to meta-nodes"
            checked={props.preferences.collapseCommunities}
            onChange={(value) => update({ collapseCommunities: value })}
          />
        </section>

        <section className="modal__section">
          <h3>Editor integration</h3>
          <label className="field">
            <span className="field__label">Open command</span>
            <input
              className="field__input"
              value={draftEditor}
              placeholder="code --goto {file}:{line}"
              onChange={(event) => setDraftEditor(event.target.value)}
              onBlur={() => props.onEditorCommandChange(draftEditor)}
            />
            <span className="field__hint">
              <code>{'{file}'}</code> and <code>{'{line}'}</code> are substituted with the indexed path.
              Paths come from the index only, never typed by hand.
            </span>
          </label>
        </section>

        <footer className="modal__footer">
          <button type="button" onClick={props.onClearPositions}>
            Clear saved positions
          </button>
          <button type="button" onClick={props.onResetLayout}>
            Reset layout
          </button>
          <button type="button" className="modal__primary" onClick={props.onClose}>
            Done
          </button>
        </footer>
      </div>
    </div>
  );
}

function ToggleRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}): JSX.Element {
  return (
    <label className="toggle">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}
