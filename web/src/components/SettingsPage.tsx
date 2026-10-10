import { Fragment, useCallback, useEffect, useMemo, useState } from 'react';
import {
  downloadModel,
  fetchConfig,
  fetchModelsStatus,
  saveConfig,
  type ConfigPayload,
  type ConfigSection,
  type ModelsStatus,
} from '../api/config';
import { describeError } from '../util/errors';
import type { ViewPreferencesState } from '../state/preferences';
import { PALETTES, type ThemeName } from '../graph/palette';

/**
 * The workspace settings surface.
 *
 * Configuration is edited per section and saved explicitly, so a half-finished
 * edit never reaches the server and a rejected value is reported against the
 * field that caused it. Remote egress is deliberately not a plain checkbox: it
 * states what it would send and off is the default.
 */
export interface SettingsPageProps {
  open: boolean;
  onClose: () => void;
  onSaved?: () => void;
  /** View preferences stay local to the browser, unlike workspace config. */
  preferences: ViewPreferencesState;
  onPreferencesChange: (next: ViewPreferencesState) => void;
  onResetLayout?: () => void;
}

const VIEW_TAB = '__view__' as const;
type ActiveTab = ConfigSection | typeof VIEW_TAB;

type SaveState = { kind: 'idle' } | { kind: 'saving' } | { kind: 'saved' } | { kind: 'error'; message: string };

interface FieldSpec {
  key: string;
  label: string;
  hint: string;
  kind: 'toggle' | 'text' | 'number' | 'select';
  options?: string[];
  min?: number;
  max?: number;
  step?: number;
  /** Marks a setting that can send content off this machine. */
  egress?: boolean;
}

/** Section definitions. Order is the order they are shown in. */
const SECTIONS: {
  id: ConfigSection;
  title: string;
  summary: string;
  fields: FieldSpec[];
}[] = [
  {
    id: 'embedding',
    title: 'Embeddings',
    summary: 'The model that turns code into vectors. Local by default.',
    fields: [
      {
        key: 'backend',
        label: 'Backend',
        hint: 'Native runs EmbeddingGemma on this machine. API backends send code to a remote service.',
        kind: 'select',
        options: ['native', 'ollama', 'api', 'none'],
        egress: true,
      },
      { key: 'model', label: 'Model', hint: 'Model identifier for the native backend.', kind: 'text' },
      {
        key: 'device',
        label: 'Device',
        hint: 'Where the model runs. "auto" picks the best available.',
        kind: 'select',
        options: ['auto', 'cpu', 'cuda'],
      },
      {
        key: 'revision',
        label: 'Revision',
        hint: 'Pin an exact model revision for reproducible vectors.',
        kind: 'text',
      },
      { key: 'normalize', label: 'Normalize vectors', hint: 'Required for cosine similarity.', kind: 'toggle' },
      {
        key: 'api_endpoint',
        label: 'API endpoint',
        hint: 'Only used by the API backend. Hosted embeddings send source code.',
        kind: 'text',
        egress: true,
      },
      {
        key: 'api_model',
        label: 'API model',
        hint: 'Embedding model name for the API backend.',
        kind: 'text',
        egress: true,
      },
    ],
  },
  {
    id: 'decisions',
    title: 'Decisions',
    summary: 'Typed decision models for routing and memory gates. Off by default.',
    fields: [
      {
        key: 'provider',
        label: 'Provider',
        hint: 'Disabled runs no decision model at all. Laya is local; hosted providers send context.',
        kind: 'select',
        options: ['disabled', 'laya', 'openai', 'typesafe'],
        egress: true,
      },
      { key: 'model', label: 'Model', hint: 'Decision model override.', kind: 'text' },
      {
        key: 'timeout',
        label: 'Timeout (seconds)',
        hint: 'Hard deadline for a decision, including loading a local model.',
        kind: 'number',
        min: 0.1,
        max: 120,
        step: 0.5,
      },
      {
        key: 'confidence_threshold',
        label: 'Confidence threshold',
        hint: 'Minimum confidence before a decision overrides the deterministic result.',
        kind: 'number',
        min: 0.5,
        max: 1,
        step: 0.05,
      },
      {
        key: 'max_state_tokens',
        label: 'Max state tokens',
        hint: 'Rejects oversized requests before a local model loads. 0 means unbounded.',
        kind: 'number',
        min: 0,
        step: 256,
      },
      {
        key: 'max_rss_mb',
        label: 'Memory cap (MB)',
        hint: 'Evicts the local decision worker above this resident size. Empty means no cap.',
        kind: 'number',
        min: 1,
        step: 64,
      },
    ],
  },
  {
    id: 'privacy',
    title: 'Privacy and egress',
    summary: 'What may leave this machine. Everything here defaults to off or local.',
    fields: [
      {
        key: 'allow_remote_embedding',
        label: 'Allow remote embeddings',
        hint: 'Sends source code to a hosted embedding provider. Off by default.',
        kind: 'toggle',
        egress: true,
      },
      {
        key: 'allow_remote_decisions',
        label: 'Allow remote decisions',
        hint: 'Sends query context to a hosted decision model. Off by default.',
        kind: 'toggle',
        egress: true,
      },
      {
        key: 'allow_model_downloads',
        label: 'Allow model downloads',
        hint: 'Turn off to forbid fetching model weights. Already-cached models keep working.',
        kind: 'toggle',
      },
      { key: 'telemetry', label: 'Telemetry', hint: 'No usage data is sent today.', kind: 'toggle' },
    ],
  },
  {
    id: 'index',
    title: 'Indexing',
    summary: 'What gets indexed and how large a file may be.',
    fields: [
      {
        key: 'dimensions',
        label: 'Vector dimensions',
        hint: 'Changing this invalidates existing vectors and needs a reindex.',
        kind: 'number',
        min: 128,
        max: 3072,
        step: 128,
      },
      { key: 'include_media', label: 'Include media', hint: 'Index images, audio and video.', kind: 'toggle' },
      { key: 'include_generated', label: 'Include generated files', hint: 'Usually noise.', kind: 'toggle' },
      { key: 'follow_symlinks', label: 'Follow symlinks', hint: 'Off avoids loops outside the workspace.', kind: 'toggle' },
      {
        key: 'max_file_bytes',
        label: 'Max file size (bytes)',
        hint: 'Files larger than this are skipped.',
        kind: 'number',
        min: 1024,
        step: 100000,
      },
      {
        key: 'watch_debounce_seconds',
        label: 'Watch debounce (s)',
        hint: 'How long the watcher waits for edits to settle.',
        kind: 'number',
        min: 0,
        step: 0.1,
      },
    ],
  },
  {
    id: 'retrieval',
    title: 'Retrieval',
    summary: 'How much evidence each query gathers.',
    fields: [
      {
        key: 'semantic_candidates',
        label: 'Semantic candidates',
        hint: 'Vector candidates per query.',
        kind: 'number',
        min: 0,
        step: 5,
      },
      {
        key: 'lexical_candidates',
        label: 'Lexical candidates',
        hint: 'Keyword candidates per query.',
        kind: 'number',
        min: 0,
        step: 5,
      },
      {
        key: 'graph_hops',
        label: 'Graph hops',
        hint: 'How far structural expansion travels.',
        kind: 'number',
        min: 0,
        max: 6,
        step: 1,
      },
      {
        key: 'default_context_tokens',
        label: 'Context budget (tokens)',
        hint: 'Default evidence budget for an agent context request.',
        kind: 'number',
        min: 500,
        step: 500,
      },
    ],
  },
  {
    id: 'semantic_edges',
    title: 'Semantic edges',
    summary: 'Similarity links shown in the graph. These are inferred, never proven.',
    fields: [
      { key: 'enabled', label: 'Show semantic edges', hint: 'Edges inferred from embedding similarity.', kind: 'toggle' },
      {
        key: 'top_k',
        label: 'Neighbours per node',
        hint: 'How many similarity neighbours each node gets.',
        kind: 'number',
        min: 1,
        step: 1,
      },
      {
        key: 'minimum_similarity',
        label: 'Minimum similarity',
        hint: 'Lower is denser. "auto" derives a threshold from the graph.',
        kind: 'text',
      },
    ],
  },
  {
    id: 'graph',
    title: 'Graph',
    summary: 'Community detection and centrality computation.',
    fields: [
      {
        key: 'community_algorithm',
        label: 'Community algorithm',
        hint: 'Used to group related code into clusters.',
        kind: 'select',
        options: ['leiden', 'louvain', 'label_propagation'],
      },
      {
        key: 'community_resolution',
        label: 'Community resolution',
        hint: 'Higher gives smaller, tighter communities.',
        kind: 'number',
        min: 0.1,
        max: 5,
        step: 0.1,
      },
      {
        key: 'compute_betweenness',
        label: 'Compute betweenness',
        hint: 'Slow on large graphs; off by default.',
        kind: 'toggle',
      },
    ],
  },
];

/** A single readable line for any failure, never an undefined property. */
function describe(error: unknown): string {
  const described = describeError(error);
  const message = described?.message ?? 'Something went wrong.';
  return described?.remediation ? `${message} — ${described.remediation}` : message;
}

function coerce(field: FieldSpec, raw: unknown): unknown {
  if (field.kind === 'toggle') return Boolean(raw);
  if (field.kind === 'number') {
    if (raw === '' || raw === null || raw === undefined) return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : raw;
  }
  return raw;
}

export function SettingsPage({
  open,
  onClose,
  onSaved,
  preferences,
  onPreferencesChange,
  onResetLayout,
}: SettingsPageProps): JSX.Element | null {
  const [config, setConfig] = useState<ConfigPayload | null>(null);
  const [draft, setDraft] = useState<ConfigPayload | null>(null);
  const [models, setModels] = useState<ModelsStatus | null>(null);
  const [state, setState] = useState<SaveState>({ kind: 'idle' });
  const [downloading, setDownloading] = useState(false);
  const [activeSection, setActiveSection] = useState<ActiveTab>(VIEW_TAB);

  const load = useCallback(async () => {
    try {
      const [loaded, status] = await Promise.all([fetchConfig(), fetchModelsStatus()]);
      setConfig(loaded);
      setDraft(loaded);
      setModels(status);
    } catch (error) {
      setState({ kind: 'error', message: describe(error) });
    }
  }, []);

  useEffect(() => {
    if (open) void load();
  }, [open, load]);

  const dirty = useMemo(
    () => JSON.stringify(config ?? {}) !== JSON.stringify(draft ?? {}),
    [config, draft],
  );

  const setField = (section: ConfigSection, key: string, value: unknown) => {
    setDraft((previous) =>
      previous ? { ...previous, [section]: { ...previous[section], [key]: value } } : previous,
    );
    setState({ kind: 'idle' });
  };

  const save = async () => {
    if (!draft) return;
    setState({ kind: 'saving' });
    try {
      const changed: Partial<ConfigPayload> = {};
      for (const section of SECTIONS) {
        if (JSON.stringify(draft[section.id]) !== JSON.stringify(config?.[section.id])) {
          changed[section.id] = draft[section.id];
        }
      }
      if (Object.keys(changed).length === 0) {
        setState({ kind: 'saved' });
        return;
      }
      await saveConfig(changed);
      await load();
      setState({ kind: 'saved' });
      onSaved?.();
    } catch (error) {
      setState({ kind: 'error', message: describe(error) });
    }
  };

  const runDownload = async () => {
    setDownloading(true);
    try {
      await downloadModel();
      setModels(await fetchModelsStatus());
      setState({ kind: 'saved' });
    } catch (error) {
      setState({ kind: 'error', message: describe(error) });
    } finally {
      setDownloading(false);
    }
  };

  if (!open) return null;
  const section = SECTIONS.find((item) => item.id === activeSection);
  const values = section ? (draft?.[section.id] ?? {}) : {};

  const setPreference = <K extends keyof ViewPreferencesState>(
    key: K,
    value: ViewPreferencesState[K],
  ) => onPreferencesChange({ ...preferences, [key]: value });

  return (
    <div className="settings" role="dialog" aria-label="Settings" aria-modal="true">
      <header className="settings__head">
        <div>
          <h2 className="settings__title">Settings</h2>
          <p className="settings__subtitle">Workspace configuration for this repository.</p>
        </div>
        <div className="settings__actions">
          {state.kind === 'saved' && <span className="settings__saved" role="status">Saved</span>}
          {state.kind === 'error' && (
            <span className="settings__error" role="alert">
              {state.message}
            </span>
          )}
          <button type="button" className="btn btn--ghost" onClick={onClose}>
            Close
          </button>
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => void save()}
            disabled={!dirty || state.kind === 'saving'}
          >
            {state.kind === 'saving' ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      </header>

      <div className="settings__body">
        <nav className="settings__nav" aria-label="Settings sections">
          <button
            type="button"
            className={`settings__tab${activeSection === VIEW_TAB ? ' settings__tab--active' : ''}`}
            aria-current={activeSection === VIEW_TAB}
            onClick={() => setActiveSection(VIEW_TAB)}
          >
            <span className="settings__tabTitle">View and layout</span>
            <span className="settings__tabSummary">
              How the graph is drawn. Kept in this browser, not in workspace config.
            </span>
          </button>
          {SECTIONS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`settings__tab${activeSection === item.id ? ' settings__tab--active' : ''}`}
              aria-current={activeSection === item.id}
              onClick={() => setActiveSection(item.id)}
            >
              <span className="settings__tabTitle">{item.title}</span>
              <span className="settings__tabSummary">{item.summary}</span>
            </button>
          ))}
        </nav>

        <div className="settings__panel">
{activeSection === VIEW_TAB && (
            <section className="settings__card">
              <header className="settings__cardHead">
                <h3>View and layout</h3>
              </header>
              <div className="settings__field">
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={preferences.showLabels}
                    onChange={(event) => setPreference('showLabels', event.target.checked)}
                  />
                  <span className="switch__track" aria-hidden="true">
                    <span className="switch__thumb" />
                  </span>
                  <span className="switch__label">Show node labels</span>
                </label>
                <p className="field__hint">Off by default; labels appear on hover and selection.</p>
              </div>
              <div className="settings__field">
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={preferences.showLegend}
                    onChange={(event) => setPreference('showLegend', event.target.checked)}
                  />
                  <span className="switch__track" aria-hidden="true">
                    <span className="switch__thumb" />
                  </span>
                  <span className="switch__label">Show legend</span>
                </label>
                <p className="field__hint">A floating key. It covers part of the graph when open.</p>
              </div>
              <div className="settings__field">
                <label className="field" htmlFor="pref-theme">
                  <span className="field__label">Theme</span>
                  <select
                    id="pref-theme"
                    className="field__control"
                    value={preferences.theme}
                    onChange={(event) =>
                      setPreference('theme', event.target.value as ViewPreferencesState['theme'])
                    }
                  >
                    {(Object.keys(PALETTES) as ThemeName[]).map((theme) => (
                      <option key={theme} value={theme}>
                        {theme}
                      </option>
                    ))}
                  </select>
                </label>
                <p className="field__hint">Applies to the dashboard only.</p>
              </div>
              <div className="settings__field">
                <label className="field" htmlFor="pref-limit">
                  <span className="field__label">Global node limit</span>
                  <input
                    id="pref-limit"
                    className="field__control"
                    type="number"
                    min={50}
                    step={50}
                    value={preferences.globalLimit}
                    onChange={(event) => setPreference('globalLimit', Number(event.target.value))}
                  />
                </label>
                <p className="field__hint">
                  How many nodes the global view loads. Lower is faster and calmer.
                </p>
              </div>
              <div className="settings__field">
                <label className="field" htmlFor="pref-repulsion">
                  <span className="field__label">Repulsion</span>
                  <input
                    id="pref-repulsion"
                    className="field__control"
                    type="range"
                    min={-800}
                    max={-50}
                    step={10}
                    value={preferences.force.chargeStrength}
                    onChange={(event) =>
                      setPreference('force', {
                        ...preferences.force,
                        chargeStrength: Number(event.target.value),
                      })
                    }
                  />
                </label>
                <p className="field__hint">More negative pushes clusters further apart.</p>
              </div>
              <div className="settings__field">
                <label className="field" htmlFor="pref-settling">
                  <span className="field__label">Settling</span>
                  <input
                    id="pref-settling"
                    className="field__control"
                    type="range"
                    min={0.3}
                    max={0.95}
                    step={0.01}
                    value={preferences.force.velocityDecay}
                    onChange={(event) =>
                      setPreference('force', {
                        ...preferences.force,
                        velocityDecay: Number(event.target.value),
                      })
                    }
                  />
                </label>
                <p className="field__hint">Lower settles faster and moves less.</p>
              </div>
              {onResetLayout && (
                <div className="settings__row">
                  <button type="button" className="btn btn--ghost" onClick={onResetLayout}>
                    Reset layout
                  </button>
                  <span className="settings__note">Re-runs the layout from a fresh spread.</span>
                </div>
              )}
            </section>
          )}
          {section && (
            <Fragment key={section.id}>
          {section.id === 'embedding' && models && (
            <section className="settings__card">
              <header className="settings__cardHead">
                <h3>Local model</h3>
                <span className={`pill ${models.cached ? 'pill--ok' : 'pill--warn'}`}>
                  {models.cached ? 'Weights cached' : 'Weights not cached'}
                </span>
              </header>
              <dl className="settings__facts">
                <div>
                  <dt>Model</dt>
                  <dd>{models.model}</dd>
                </div>
                <div>
                  <dt>Dimensions</dt>
                  <dd>{models.dimensions}</dd>
                </div>
                <div>
                  <dt>Device</dt>
                  <dd>{models.device}</dd>
                </div>
                <div>
                  <dt>Vectors stored</dt>
                  <dd>{models.vectors}</dd>
                </div>
              </dl>
              <div className="settings__row">
                <button
                  type="button"
                  className="btn btn--primary"
                  onClick={() => void runDownload()}
                  disabled={downloading || !models.allow_downloads}
                  title={
                    models.allow_downloads
                      ? 'Fetch the model weights into the local cache'
                      : 'Enable "Allow model downloads" in Privacy first'
                  }
                >
                  {downloading ? 'Downloading…' : models.cached ? 'Re-download model' : 'Download model'}
                </button>
                {!models.allow_downloads && (
                  <span className="settings__note">
                    Downloads are switched off in Privacy and egress.
                  </span>
                )}
              </div>
            </section>
          )}

          <section className="settings__card">
            <header className="settings__cardHead">
              <h3>{section.title}</h3>
            </header>
            {section.fields.map((field) => {
              const raw = values[field.key];
              const id = `setting-${section.id}-${field.key}`;
              return (
                <div className="settings__field" key={field.key}>
                  {field.kind === 'toggle' ? (
                    <label className="switch" htmlFor={id}>
                      <input
                        id={id}
                        type="checkbox"
                        checked={Boolean(raw)}
                        onChange={(event) =>
                          setField(section.id, field.key, coerce(field, event.target.checked))
                        }
                      />
                      <span className="switch__track" aria-hidden="true">
                        <span className="switch__thumb" />
                      </span>
                      <span className="switch__label">
                        {field.label}
                        {field.egress && <span className="tag tag--warn">leaves this machine</span>}
                      </span>
                    </label>
                  ) : (
                    <label className="field" htmlFor={id}>
                      <span className="field__label">
                        {field.label}
                        {field.egress && <span className="tag tag--warn">leaves this machine</span>}
                      </span>
                      {field.kind === 'select' ? (
                        <select
                          id={id}
                          className="field__control"
                          value={String(raw ?? '')}
                          onChange={(event) => setField(section.id, field.key, coerce(field, event.target.value))}
                        >
                          {(field.options ?? []).map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          id={id}
                          className="field__control"
                          type={field.kind === 'number' ? 'number' : 'text'}
                          min={field.min}
                          max={field.max}
                          step={field.step}
                          value={raw === null || raw === undefined ? '' : String(raw)}
                          onChange={(event) => setField(section.id, field.key, coerce(field, event.target.value))}
                        />
                      )}
                    </label>
                  )}
                  <p className="field__hint">{field.hint}</p>
                </div>
              );
            })}
          </section>
            </Fragment>
          )}
        </div>
      </div>
    </div>
  );
}