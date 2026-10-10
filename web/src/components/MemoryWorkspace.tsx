import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { api } from '../api/client';
import type { MemoryEntry, MemoryStatusData } from '../api/types';
import { describeError } from '../util/errors';

type ScopeFilter = 'all' | 'project' | 'user';
type MemoryKind = MemoryEntry['kind'];

const KINDS: MemoryKind[] = ['fact', 'preference', 'decision', 'workflow', 'reference'];

export function MemoryWorkspace({ onNotify }: { onNotify: (message: string) => void }): JSX.Element {
  const [scope, setScope] = useState<ScopeFilter>('all');
  const [status, setStatus] = useState<MemoryStatusData | null>(null);
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [query, setQuery] = useState('');
  const [semantic, setSemantic] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [content, setContent] = useState('');
  const [newScope, setNewScope] = useState<'project' | 'user'>('project');
  const [newKind, setNewKind] = useState<MemoryKind>('fact');
  const [tags, setTags] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [editKind, setEditKind] = useState<MemoryKind>('fact');
  const [editTags, setEditTags] = useState('');
  const [forgetId, setForgetId] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusData, listData] = await Promise.all([
        api.memoryStatus(),
        api.memoryList(scope),
      ]);
      setStatus(statusData);
      setMemories(listData.results);
    } catch (cause) {
      setError(describeError(cause).message);
    } finally {
      setLoading(false);
    }
  }, [scope]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const runSearch = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      await reload();
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await api.memorySearch({ q: trimmed, scope, semantic });
      setMemories(result.results);
    } catch (cause) {
      setError(describeError(cause).message);
    } finally {
      setLoading(false);
    }
  };

  const addMemory = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    if (!content.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api.memoryAdd({
        content,
        scope: newScope,
        kind: newKind,
        tags: parseTags(tags),
      });
      setContent('');
      setTags('');
      await reload();
      onNotify('Memory saved to the local store.');
    } catch (cause) {
      setError(describeError(cause).message);
    } finally {
      setBusy(false);
    }
  };

  const beginEdit = (memory: MemoryEntry): void => {
    setEditingId(memory.id);
    setEditContent(memory.content);
    setEditKind(memory.kind);
    setEditTags(memory.tags.join(', '));
  };

  const saveEdit = async (id: string): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      await api.memoryUpdate(id, {
        content: editContent,
        kind: editKind,
        tags: parseTags(editTags),
      });
      setEditingId(null);
      await reload();
      onNotify('Memory updated.');
    } catch (cause) {
      setError(describeError(cause).message);
    } finally {
      setBusy(false);
    }
  };

  const forget = async (memory: MemoryEntry): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      await api.memoryForget(memory.id);
      await reload();
      onNotify('Memory forgotten.');
    } catch (cause) {
      setError(describeError(cause).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="memory-workspace" aria-label="Shared agent memory">
      <header className="memory-hero">
        <div>
          <p className="eyebrow">POLDERGRAPH / MEMORY</p>
          <h1>Shared agent memory</h1>
          <p>Durable preferences and project knowledge available to OMP and Codex.</p>
        </div>
        <div className="memory-stats" aria-label="Memory totals">
          <MemoryStat label="Project" value={status?.project_memories ?? 0} />
          <MemoryStat label="Personal" value={status?.user_memories ?? 0} />
          <MemoryStat label="Total" value={status?.total_memories ?? 0} />
        </div>
      </header>

      <div className="memory-notice">
        <span className="memory-notice__icon" aria-hidden="true">⌂</span>
        <span><strong>Private and local.</strong> Memories stay in your OS user data folder and never enter the repository.</span>
      </div>

      {error && <div className="memory-error" role="alert">{error}</div>}

      <div className="memory-toolbar">
        <div className="scope-tabs" role="tablist" aria-label="Memory scope">
          {(['all', 'project', 'user'] as ScopeFilter[]).map((item) => (
            <button
              key={item}
              type="button"
              role="tab"
              aria-selected={scope === item}
              className={scope === item ? 'scope-tab scope-tab--active' : 'scope-tab'}
              onClick={() => { setQuery(''); setScope(item); }}
            >
              {item === 'all' ? 'All accessible' : item === 'user' ? 'Personal' : 'This project'}
            </button>
          ))}
        </div>
        <form className="memory-search" onSubmit={(event) => void runSearch(event)} role="search">
          <span aria-hidden="true">⌕</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Find a memory…"
            aria-label="Search memories"
          />
          <label className="memory-semantic" title="Use local EmbeddingGemma vectors for semantic matching">
            <input type="checkbox" aria-label="Use semantic memory search" checked={semantic} onChange={(event) => setSemantic(event.target.checked)} />
            Semantic
          </label>
          <button type="submit" className="button button--quiet">Search</button>
        </form>
      </div>

      <div className="memory-content">
        <form className="memory-compose" onSubmit={(event) => void addMemory(event)}>
          <div className="panel-title">
            <span className="panel-title__icon" aria-hidden="true">＋</span>
            <div><h2>Save a memory</h2><p>Keep only details useful in future work.</p></div>
          </div>
          <label className="field">
            <span className="field__label">Memory</span>
            <textarea
              value={content}
              aria-label="Memory content"
              onChange={(event) => setContent(event.target.value)}
              placeholder="e.g. This project uses pnpm and runs tests with pytest."
              rows={5}
              maxLength={32000}
              required
            />
          </label>
          <div className="memory-fields">
            <label className="field">
              <span className="field__label">Scope</span>
              <select value={newScope} aria-label="Memory scope" onChange={(event) => setNewScope(event.target.value as 'project' | 'user')}>
                <option value="project">This project</option>
                <option value="user">Personal, across projects</option>
              </select>
            </label>
            <label className="field">
              <span className="field__label">Type</span>
              <select value={newKind} aria-label="Memory type" onChange={(event) => setNewKind(event.target.value as MemoryKind)}>
                {KINDS.map((kind) => <option key={kind} value={kind}>{titleCase(kind)}</option>)}
              </select>
            </label>
          </div>
          <label className="field">
            <span className="field__label">Tags <span className="field__optional">optional</span></span>
            <input value={tags} aria-label="Tags, comma separated" onChange={(event) => setTags(event.target.value)} placeholder="tooling, workflow" />
          </label>
          <button type="submit" className="button button--primary" disabled={busy || !content.trim()}>
            {busy ? 'Saving…' : 'Save to memory'}
          </button>
          <p className="memory-compose__hint">Credentials and private keys are blocked. Avoid one-off task details.</p>
        </form>

        <section className="memory-list" aria-label="Saved memories">
          <div className="memory-list__header">
            <div><h2>{query.trim() ? 'Search results' : 'Saved memories'}</h2><p>{memories.length} shown · newest first</p></div>
            <button type="button" className="button button--quiet" onClick={() => void reload()} disabled={loading}>
              Refresh
            </button>
          </div>
          {loading ? (
            <div className="memory-empty"><span className="spinner" />Loading memories…</div>
          ) : memories.length === 0 ? (
            <div className="memory-empty">
              <span className="memory-empty__symbol" aria-hidden="true">◇</span>
              <strong>{query.trim() ? 'No matching memories' : 'A little context goes a long way'}</strong>
              <span>{query.trim() ? 'Try a broader search or another scope.' : 'Save a durable preference, project decision, or useful workflow.'}</span>
            </div>
          ) : (
            <ul className="memory-cards">
              {memories.map((memory) => (
                <li className="memory-card" key={memory.id}>
                  {editingId === memory.id ? (
                    <div className="memory-edit">
                      <textarea value={editContent} aria-label="Edited memory content" onChange={(event) => setEditContent(event.target.value)} rows={4} />
                      <div className="memory-fields">
                        <label className="field"><span className="field__label">Type</span>
                          <select value={editKind} aria-label="Edited memory type" onChange={(event) => setEditKind(event.target.value as MemoryKind)}>
                            {KINDS.map((kind) => <option key={kind} value={kind}>{titleCase(kind)}</option>)}
                          </select>
                        </label>
                        <label className="field"><span className="field__label">Tags</span>
                          <input value={editTags} aria-label="Edited tags, comma separated" onChange={(event) => setEditTags(event.target.value)} />
                        </label>
                      </div>
                      <div className="memory-card__actions">
                        <button type="button" className="button button--quiet" onClick={() => setEditingId(null)}>Cancel</button>
                        <button type="button" className="button button--primary" disabled={busy} onClick={() => void saveEdit(memory.id)}>Save changes</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="memory-card__topline">
                        <div className="memory-badges">
                          <span className={`memory-badge memory-badge--${memory.scope}`}>{memory.scope === 'user' ? 'Personal' : 'Project'}</span>
                          <span className="memory-badge">{titleCase(memory.kind)}</span>
                          {memory.retrieval && <span className="memory-badge memory-badge--score">{memory.retrieval} · {memory.score?.toFixed(2)}</span>}
                        </div>
                        <span className="memory-card__date" title={new Date(memory.updated_at * 1000).toLocaleString()}>
                          Updated {new Date(memory.updated_at * 1000).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="memory-card__content">{memory.content}</p>
                      {memory.tags.length > 0 && <div className="memory-tags">{memory.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>}
                      <div className="memory-card__bottom">
                        {memory.scope === 'project' && memory.project_root && <span className="memory-card__root" title={memory.project_root}>{memory.project_root}</span>}
                        <div className="memory-card__actions">
                          {forgetId === memory.id ? (
                            <><span className="memory-card__confirm">Remove permanently?</span><button type="button" className="button button--quiet" onClick={() => setForgetId(null)}>Cancel</button><button type="button" className="button button--danger" disabled={busy} onClick={() => void forget(memory)}>Confirm</button></>
                          ) : <><button type="button" className="button button--quiet" onClick={() => beginEdit(memory)}>Edit</button><button type="button" className="button button--danger" onClick={() => setForgetId(memory.id)}>Forget</button></>}
                        </div>
                      </div>
                    </>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
      <footer className="memory-footnote">
        <span>{status?.store ?? 'Local user-data store'}</span>
        <span>Agent context retrieves matching personal and project memories automatically.</span>
      </footer>
    </section>
  );
}

function MemoryStat({ label, value }: { label: string; value: number }): JSX.Element {
  return <div className="memory-stat"><span>{label}</span><strong>{value.toLocaleString()}</strong></div>;
}

function parseTags(value: string): string[] {
  return value.split(',').map((tag) => tag.trim()).filter(Boolean);
}

function titleCase(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
