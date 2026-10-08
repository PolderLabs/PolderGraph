import type {
  CommunitySummary,
  EntityData,
  EntityEdge,
  EntityRef,
  ImpactData,
} from '../api/types';
import type { Palette } from '../graph/palette';
import { isSemanticEdge, nodeColorForKind } from '../graph/palette';

export interface InspectorProps {
  entity: EntityData | null;
  impact: ImpactData | null;
  loading: boolean;
  error: { code: string; message: string; remediation: string | null } | null;
  palette: Palette;
  onNavigate: (id: string) => void;
  onFocusLocal: (id: string) => void;
  onPathFrom: (id: string) => void;
  onPathTo: (id: string) => void;
  onImpact: (id: string) => void;
  onExplain: (id: string) => void;
  onCopy: (text: string, what: string) => void;
  onOpenSource: (path: string, line: number | null) => void;
  onClose: () => void;
}

/**
 * Detail panel for the selected entity.
 *
 * Relations are buttons, not links: navigating must replace the graph payload
 * without tearing down this panel, so the user's reading position survives.
 */
export function Inspector(props: InspectorProps): JSX.Element {
  const { entity, impact, loading, error, palette } = props;

  if (error) {
    return (
      <aside className="inspector" aria-label="Inspector">
        <div className="inspector__error">
          <h2 className="inspector__errorTitle">{error.code}</h2>
          <p>{error.message}</p>
          {error.remediation && <p className="inspector__remedy">{error.remediation}</p>}
        </div>
      </aside>
    );
  }

  if (!entity) {
    return (
      <aside className="inspector" aria-label="Inspector">
        <p className="inspector__empty">
          Select a node to inspect it. Double-click to open its local graph.
        </p>
      </aside>
    );
  }

  const record = entity.entity;
  const kindColor = nodeColorForKind(record.kind, palette);

  const inbound = groupRelations(entity.inbound ?? []);
  const outbound = groupRelations(entity.outbound ?? []);
  const semantic = (entity.semantic_neighbors ?? [])
    .slice()
    .sort((a, b) => b.similarity - a.similarity);
  const unresolved = entity.unresolved ?? [];

  return (
    <aside className="inspector" aria-label={`Inspector for ${record.qualified_name ?? record.name}`}>
      <header className="inspector__header">
        <span className="inspector__kind" style={{ color: kindColor, borderColor: kindColor }}>
          {record.kind}
        </span>
        <h2 className="inspector__title">{record.qualified_name ?? record.name}</h2>
        {record.path && (
          <p className="inspector__path">
            <button
              type="button"
              className="linkish"
              onClick={() => props.onOpenSource(record.path as string, record.start_line)}
              title="Open in editor"
            >
              {record.path}
              {record.start_line !== null ? `:${record.start_line}` : ''}
            </button>
            <button
              type="button"
              className="iconButton"
              onClick={() => props.onCopy(record.path as string, 'path')}
              title="Copy path"
            >
              copy
            </button>
          </p>
        )}
        {record.qualified_name && (
          <button
            type="button"
            className="iconButton"
            onClick={() => props.onCopy(record.qualified_name as string, 'qualified name')}
          >
            Copy qualified name
          </button>
        )}
        <button type="button" className="inspector__close" onClick={props.onClose} title="Close inspector">
          ×
        </button>
      </header>

      {loading && <p className="inspector__loading">Loading…</p>}

      {record.signature && (
        <section className="inspector__section">
          <h3>Signature</h3>
          <pre className="inspector__code">{record.signature}</pre>
        </section>
      )}

      {record.docstring && (
        <section className="inspector__section">
          <h3>Documentation</h3>
          {/* Server text is rendered as text nodes only, never as markup. */}
          <p className="inspector__doc">{record.docstring}</p>
        </section>
      )}

      {entity.excerpt && (
        <section className="inspector__section">
          <h3>Excerpt</h3>
          <pre className="inspector__code">{entity.excerpt}</pre>
        </section>
      )}

      <section className="inspector__section">
        <h3>Details</h3>
        <dl className="inspector__facts">
          <Fact label="Language" value={record.language} />
          <Fact
            label="Lines"
            value={
              record.start_line !== null && record.end_line !== null
                ? `${record.start_line}–${record.end_line}`
                : null
            }
          />
          <Fact label="Visibility" value={record.visibility} />
          <Fact label="Generated" value={record.is_generated ? 'yes' : 'no'} />
          <Fact label="External" value={record.is_external ? 'yes' : 'no'} />
          {entity.parent && (
            <div className="inspector__fact">
              <dt>Parent</dt>
              <dd>
                <RelationButton
                  entity={entity.parent}
                  palette={palette}
                  onClick={() => props.onNavigate(entity.parent!.id)}
                />
              </dd>
            </div>
          )}
          {entity.communities?.structural && (
            <Fact
              label="Community (structural)"
              value={formatCommunity(entity.communities.structural)}
            />
          )}
          {entity.communities?.hybrid && (
            <Fact label="Community (hybrid)" value={formatCommunity(entity.communities.hybrid)} />
          )}
        </dl>
      </section>

      {unresolved.length > 0 && (
        <section className="inspector__section">
          <h3>Unresolved references</h3>
          <p className="inspector__hint">
            The index could not bind these names to a definition; they are not facts.
          </p>
          <ul className="inspector__list">
            {unresolved.map((entry) => (
              <li key={entry.id} className="inspector__listItem">
                <RelationButton
                  entity={{ id: entry.id, label: entry.label, kind: entry.kind, path: entry.path }}
                  palette={palette}
                  onClick={() => props.onNavigate(entry.id)}
                />
              </li>
            ))}
          </ul>
        </section>
      )}

      <RelationGroup
        title="Inbound (uses / depends on)"
        relations={inbound}
        palette={palette}
        onNavigate={props.onNavigate}
      />
      <RelationGroup
        title="Outbound (used by / depends on)"
        relations={outbound}
        palette={palette}
        onNavigate={props.onNavigate}
      />

      {semantic.length > 0 && (
        <section className="inspector__section">
          <h3>
            Semantic neighbours
            <span className="inspector__badge inspector__badge--semantic">evidence, not fact</span>
          </h3>
          <ul className="inspector__list">
            {semantic.map((neighbour) => (
              <li key={neighbour.entity.id} className="inspector__listItem">
                <RelationButton
                  entity={neighbour.entity}
                  palette={palette}
                  onClick={() => props.onNavigate(neighbour.entity.id)}
                />
                <span className="inspector__similarity" title="cosine similarity">
                  {neighbour.similarity.toFixed(3)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {impact && (
        <section className="inspector__section">
          <h3>Impact</h3>
          <ImpactGroup label="Direct" entries={impact.direct} onNavigate={props.onNavigate} />
          <ImpactGroup label="Transitive" entries={impact.transitive} onNavigate={props.onNavigate} />
          <ImpactGroup label="Tests" entries={impact.tests} onNavigate={props.onNavigate} />
          <ImpactGroup label="Docs" entries={impact.docs} onNavigate={props.onNavigate} />
          <ImpactGroup
            label="Semantic only (no structural edge)"
            entries={impact.semantic_only}
            onNavigate={props.onNavigate}
          />
        </section>
      )}

      {entity.metrics && Object.keys(entity.metrics).length > 0 && (
        <section className="inspector__section">
          <h3>Metrics</h3>
          <dl className="inspector__facts">
            {Object.entries(entity.metrics).map(([key, value]) => (
              <div className="inspector__fact" key={key}>
                <dt>{key}</dt>
                <dd>{String(value)}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      <section className="inspector__section inspector__actions">
        <h3>Actions</h3>
        <div className="inspector__actionRow">
          <button type="button" onClick={() => props.onFocusLocal(record.id)}>
            Local graph
          </button>
          <button type="button" onClick={() => props.onPathFrom(record.id)}>
            Path from here
          </button>
          <button type="button" onClick={() => props.onPathTo(record.id)}>
            Path to here
          </button>
          <button type="button" onClick={() => props.onImpact(record.id)}>
            Impact
          </button>
          <button type="button" onClick={() => props.onExplain(record.id)}>
            Explain
          </button>
        </div>
      </section>
    </aside>
  );
}

function Fact({ label, value }: { label: string; value: string | number | boolean | null | undefined }) {
  if (value === null || value === undefined || value === '') return null;
  return (
    <div className="inspector__fact">
      <dt>{label}</dt>
      <dd>{String(value)}</dd>
    </div>
  );
}

/** Renders a community summary, falling back to its bare id. */
function formatCommunity(community: CommunitySummary | null | undefined): string {
  if (!community) return '—';
  const parts = [community.label, community.size].filter(
    (part) => part !== null && part !== undefined && part !== '',
  );
  return parts.length > 0 ? parts.join(' · ') : String(community.community_id ?? '—');
}

/** Groups relations by edge type so related facts read together. */
function groupRelations(
  relations: Array<EntityEdge & { entity: EntityRef }>,
): Map<string, Array<EntityEdge & { entity: EntityRef }>> {
  const grouped = new Map<string, Array<EntityEdge & { entity: EntityRef }>>();
  for (const relation of relations) {
    const bucket = grouped.get(relation.type);
    if (bucket) bucket.push(relation);
    else grouped.set(relation.type, [relation]);
  }
  return grouped;
}

interface RelationGroupProps {
  title: string;
  relations: Map<string, Array<EntityEdge & { entity: EntityRef }>>;
  palette: Palette;
  onNavigate: (id: string) => void;
}

function RelationGroup({ title, relations, palette, onNavigate }: RelationGroupProps): JSX.Element | null {
  if (relations.size === 0) return null;
  return (
    <section className="inspector__section">
      <h3>{title}</h3>
      {[...relations.entries()].map(([type, entries]) => (
        <div key={type} className="inspector__relationGroup">
          <h4 className="inspector__relationType">
            {type}
            <span className="inspector__count">{entries.length}</span>
          </h4>
          <ul className="inspector__list">
            {entries.map((entry) => (
              <li key={entry.id} className="inspector__listItem">
                <RelationButton entity={entry.entity} palette={palette} onClick={() => onNavigate(entry.entity.id)} />
                <ProvenanceTag edge={entry} palette={palette} />
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

interface RelationButtonProps {
  entity: EntityRef;
  palette: Palette;
  onClick: () => void;
}

/**
 * A single relation target. Clicking navigates in place — the graph payload is
 * replaced but this panel keeps rendering, so the trail stays readable.
 */
function RelationButton({ entity, palette, onClick }: RelationButtonProps): JSX.Element {
  const label = entity.label ?? entity.qualified_name ?? entity.id;
  const kind = entity.kind ?? 'module';
  const meta = entity.path ? `${entity.path}${entity.qualified_name ? ` · ${entity.qualified_name}` : ''}` : entity.qualified_name ?? '';
  return (
    <button
      type="button"
      className="relation"
      onClick={onClick}
      title={meta || label}
    >
      <span className="relation__dot" style={{ background: nodeColorForKind(kind, palette) }} />
      <span className="relation__text">
        <span className="relation__label">{label}</span>
        {entity.path && <span className="relation__path">{entity.path}</span>}
      </span>
    </button>
  );
}

function ProvenanceTag({ edge, palette }: { edge: EntityEdge; palette: Palette }): JSX.Element | null {
  if (isSemanticEdge(edge.type)) {
    return <span className="inspector__badge inspector__badge--semantic">semantic</span>;
  }
  if (edge.provenance === 'ambiguous' || edge.provenance === 'inferred') {
    return (
      <span className="inspector__badge inspector__badge--warn" style={{ color: palette.unresolved }}>
        {edge.provenance}
      </span>
    );
  }
  return null;
}

interface ImpactGroupProps {
  label: string;
  entries: Array<{ id?: string; label?: string; path?: string | null; qualified_name?: string | null }>;
  onNavigate: (id: string) => void;
}

function ImpactGroup({ label, entries, onNavigate }: ImpactGroupProps): JSX.Element | null {
  if (!entries || entries.length === 0) return null;
  return (
    <div className="inspector__relationGroup">
      <h4 className="inspector__relationType">
        {label}
        <span className="inspector__count">{entries.length}</span>
      </h4>
      <ul className="inspector__list">
        {entries.map((entry, position) => (
          <li key={entry.id ?? `${label}-${position}`} className="inspector__listItem">
            {entry.id ? (
              <button type="button" className="relation" onClick={() => onNavigate(entry.id as string)}>
                <span className="relation__text">
                  <span className="relation__label">{entry.label ?? entry.qualified_name ?? entry.id}</span>
                  {entry.path && <span className="relation__path">{entry.path}</span>}
                </span>
              </button>
            ) : (
              <span className="relation">
                <span className="relation__text">
                  <span className="relation__label">{entry.label ?? entry.qualified_name ?? '—'}</span>
                  {entry.path && <span className="relation__path">{entry.path}</span>}
                </span>
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
