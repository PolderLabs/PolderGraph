import { forwardRef } from 'react';
import type { StatusData } from '../api/types';
import type { EventsStatus } from '../api/events';
import type { Palette, ThemeName } from '../graph/palette';

export interface HeaderProps {
  status: StatusData | null;
  statusError: string | null;
  eventsStatus: EventsStatus;
  theme: ThemeName;
  palette: Palette;
  searchValue: string;
  searching: boolean;
  onSearchChange: (value: string) => void;
  onSearchSubmit: (value: string) => void;
  onToggleTheme: () => void;
  onToggleLegend: () => void;
  onOpenSettings: () => void;
}

/** Top bar: workspace identity, search, index status and global controls. */
export const Header = forwardRef<HTMLInputElement, HeaderProps>(function Header(props, searchRef) {
  const { status, statusError, eventsStatus, theme, palette } = props;

  const roots = status?.roots ?? [];
  const rootPaths = roots.map((root) => root.path);
  const workspace = rootPaths.length > 0 ? rootPaths.join(', ') : 'workspace';

  return (
    <header className="header" style={{ color: palette.text }}>
      <div className="header__brand">
        <span className="header__logo" aria-hidden="true" />
        <span className="header__title">PolderGraph</span>
      </div>

      <div className="header__workspace" title={rootPaths.join('\n')}>
        <span className="header__workspaceLabel">workspace</span>
        <span className="header__workspaceName">{workspace}</span>
      </div>

      <form
        className="header__search"
        role="search"
        onSubmit={(event) => {
          event.preventDefault();
          props.onSearchSubmit(props.searchValue);
        }}
      >
        <input
          ref={searchRef}
          type="search"
          className="header__searchInput"
          placeholder="Search symbols, paths, or ask a question…"
          value={props.searchValue}
          onChange={(event) => props.onSearchChange(event.target.value)}
          aria-label="Search symbols, file paths, or natural language"
          autoComplete="off"
          spellCheck={false}
        />
        {props.searching && <span className="header__spinner" aria-label="Searching" />}
      </form>

      <div className="header__status">
        <StatusPill
          label={statusError ? 'API offline' : status ? (status.fresh ? 'index fresh' : 'index stale') : 'connecting'}
          tone={statusError ? 'error' : status ? (status.fresh ? 'ok' : 'warn') : 'muted'}
          title={statusError ?? describeStatus(status)}
        />
        <StatusPill
          label={eventsLabel(eventsStatus)}
          tone={eventsStatus === 'open' ? 'ok' : eventsStatus === 'connecting' ? 'warn' : 'muted'}
          title="Live index updates over SSE"
        />
        <button
          type="button"
          className="header__iconButton"
          onClick={props.onToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
        >
          {theme === 'dark' ? '☾' : '☀'}
        </button>
        <button
          type="button"
          className="header__iconButton"
          onClick={props.onToggleLegend}
          title="Toggle legend"
          aria-label="Toggle legend"
          aria-pressed={props.searching ? undefined : undefined}
        >
          key
        </button>
        <button type="button" className="header__iconButton" onClick={props.onOpenSettings} title="Settings">
          ⚙
        </button>
      </div>
    </header>
  );
});

interface StatusPillProps {
  label: string;
  tone: 'ok' | 'warn' | 'error' | 'muted';
  title?: string;
}

function StatusPill({ label, tone, title }: StatusPillProps): JSX.Element {
  return (
    <span className={`pill pill--${tone}`} title={title}>
      <span className="pill__dot" aria-hidden="true" />
      {label}
    </span>
  );
}

function eventsLabel(status: EventsStatus): string {
  if (status === 'open') return 'live';
  if (status === 'connecting') return 'connecting';
  return 'offline';
}

function describeStatus(status: StatusData | null): string {
  if (!status) return 'Waiting for the PolderGraph API';
  const counts = Object.entries(status.counts)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n');
  return [
    `model: ${status.model} (${status.dimensions}d)`,
    `schema: v${status.schema_version}`,
    `languages: ${status.languages.join(', ') || 'none'}`,
    `communities: ${status.communities.structural} structural / ${status.communities.hybrid} hybrid`,
    counts,
  ]
    .filter(Boolean)
    .join('\n');
}
