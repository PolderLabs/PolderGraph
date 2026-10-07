import type { EvidenceKind, SearchResult } from '../api/types';

export type ViewMode = 'global' | 'local' | 'search' | 'path';

export interface BreadcrumbEntry {
  id: string;
  label: string;
}

export interface BreadcrumbBarProps {
  view: ViewMode;
  truncated: boolean;
  communityMode: 'structural' | 'hybrid';
  pathDescription: string | null;
  results: SearchResult[];
  historyBack: BreadcrumbEntry[];
  historyForward: BreadcrumbEntry[];
  onNavigateHistory: (entry: BreadcrumbEntry, direction: 'back' | 'forward') => void;
  onClearPath: () => void;
  onSelectResult: (result: SearchResult) => void;
  onViewChange: (view: ViewMode) => void;
}

/**
 * Bottom bar: current view, result list, selection history and path status.
 * This is the only place search results are listed, keeping the canvas dominant.
 */
export function BreadcrumbBar(props: BreadcrumbBarProps): JSX.Element {
  const { results, view, truncated } = props;

  return (
    <footer className="breadcrumbs" aria-label="View status and results">
      <div className="breadcrumbs__nav">
        <button
          type="button"
          className="breadcrumbs__arrow"
          disabled={props.historyBack.length === 0}
          onClick={() => {
            const entry = props.historyBack[props.historyBack.length - 1];
            if (entry) props.onNavigateHistory(entry, 'back');
          }}
          title="Back (Alt+←)"
        >
          ←
        </button>
        <button
          type="button"
          className="breadcrumbs__arrow"
          disabled={props.historyForward.length === 0}
          onClick={() => {
            const entry = props.historyForward[props.historyForward.length - 1];
            if (entry) props.onNavigateHistory(entry, 'forward');
          }}
          title="Forward (Alt+→)"
        >
          →
        </button>
      </div>

      <div className="breadcrumbs__views" role="tablist" aria-label="Graph view">
        {(['global', 'local', 'search', 'path'] as ViewMode[]).map((mode) => (
          <button
            key={mode}
            type="button"
            role="tab"
            aria-selected={view === mode}
            className={view === mode ? 'chip chip--active' : 'chip'}
            onClick={() => props.onViewChange(mode)}
            disabled={(mode === 'local' || mode === 'path' || mode === 'search') && results.length === 0 && view !== mode}
          >
            {mode}
          </button>
        ))}
      </div>

      {props.pathDescription && (
        <div className="breadcrumbs__path">
          <span className="breadcrumbs__pathText">{props.pathDescription}</span>
          <button type="button" className="breadcrumbs__clear" onClick={props.onClearPath}>
            clear
          </button>
        </div>
      )}

      <div className="breadcrumbs__status">
        {view === 'global' && (
          <span className="breadcrumbs__meta">
            {truncated ? 'sampled — zoom or filter to explore further' : 'complete for this limit'}
          </span>
        )}
        {view === 'local' && <span className="breadcrumbs__meta">neighborhood view</span>}
        {view === 'path' && <span className="breadcrumbs__meta">path emphasised; unrelated nodes dimmed</span>}
        <span className="breadcrumbs__meta">communities: {props.communityMode}</span>
      </div>

      {results.length > 0 && (
        <ul className="results" aria-label="Search results">
          {results.map((result) => (
            <li key={result.id}>
              <button type="button" className="result" onClick={() => props.onSelectResult(result)}>
                <EvidenceBadge evidence={result.evidence} />
                <span className="result__label">{result.label}</span>
                <span className="result__kind">{result.kind}</span>
                {result.path && <span className="result__path">{result.path}</span>}
                <span className="result__score">{result.score.toFixed(2)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </footer>
  );
}

const EVIDENCE_LABELS: Record<EvidenceKind, string> = {
  exact: 'exact',
  lexical: 'lexical',
  semantic: 'semantic',
  'graph-expanded': 'graph',
};

const EVIDENCE_HINTS: Record<EvidenceKind, string> = {
  exact: 'Matched the symbol or path exactly',
  lexical: 'Matched textually (identifier, docstring or path fragment)',
  semantic: 'Matched by embedding similarity — evidence, not a structural fact',
  'graph-expanded': 'Reached through the graph from an initial match',
};

/**
 * Match-evidence badge.
 *
 * This is a first-class part of the product contract: structural truth and
 * semantic evidence must never look interchangeable, so every result states how
 * it was found.
 */
export function EvidenceBadge({ evidence }: { evidence: EvidenceKind }): JSX.Element {
  const label = EVIDENCE_LABELS[evidence] ?? evidence;
  return (
    <span className={`badge badge--${evidence}`} title={EVIDENCE_HINTS[evidence] ?? label}>
      {label}
    </span>
  );
}
