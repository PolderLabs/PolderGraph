import { forwardRef } from 'react';
import type { StatusData } from '../api/types';
import type { EventsStatus } from '../api/events';
import type { Palette, ThemeName } from '../graph/palette';
import {
  IconFilters,
  IconGraph,
  IconSearch,
  IconSettings,
  IconSun,
  IconHelp,
  IconKey,
  IconTheme,
} from './Icons';

export interface HeaderProps {
  workspaceMode: 'graph' | 'memory';
  onWorkspaceModeChange: (mode: 'graph' | 'memory') => void;
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
  onOpenShortcuts?: () => void;
  onToggleFilters: () => void;
  onToggleInspector: () => void;
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

      <nav className="header__workspaces" aria-label="Workspace">
        {(['graph', 'memory'] as const).map((mode) => <button key={mode} type="button" aria-current={props.workspaceMode === mode ? 'page' : undefined} className={props.workspaceMode === mode ? 'header__workspaceTab is-active' : 'header__workspaceTab'} onClick={() => props.onWorkspaceModeChange(mode)}>{mode === 'graph' ? 'Graph' : 'Memory'}</button>)}
      </nav>

      {props.workspaceMode === 'graph' && <form
        className="header__search"
        role="search"
        onSubmit={(event) => {
          event.preventDefault();
          props.onSearchSubmit(props.searchValue);
        }}
      >
        <span className="header__searchIcon" aria-hidden="true">
          <IconSearch size={13} />
        </span>
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
      </form>}

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
          className="header__iconButton header__mobileAction"
          onClick={props.onToggleFilters}
          title="Show filters"
          aria-label="Show filters"
        >
          <IconFilters />
        </button>
        <button
          type="button"
          className="header__iconButton header__mobileAction"
          onClick={props.onToggleInspector}
          title="Show selected entity"
          aria-label="Show selected entity"
        >
          <IconGraph />
        </button>
        <button
          type="button"
          className="header__iconButton"
          onClick={props.onToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
        >
          {theme === 'dark' ? <IconTheme /> : <IconSun />}
        </button>
        <button
          type="button"
          className="header__iconButton"
          onClick={props.onToggleLegend}
          title="Toggle legend (K)"
          aria-label="Toggle legend"
        >
          <IconKey size={15} />
        </button>
        <button
          type="button"
          className="header__iconButton"
          onClick={props.onOpenSettings}
          title="Settings (S)"
          aria-label="Settings"
        >
          <IconSettings />
        </button>
        {props.onOpenShortcuts && (
          <button
            type="button"
            className="header__iconButton"
            onClick={props.onOpenShortcuts}
            title="Keyboard shortcuts (?)"
            aria-label="Keyboard shortcuts"
          >
            <IconHelp size={15} />
          </button>
        )}
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
