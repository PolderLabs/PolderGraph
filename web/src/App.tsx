import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { api, isAbortError } from './api/client';
import { describeDegradation, describeError } from './util/errors';
import { EventsClient, type EventsStatus } from './api/events';
import type {
  CommunitiesData,
  EntityData,
  GraphEdge,
  GraphNode,
  ImpactData,
  PathData,
  SearchResult,
  StatusData,
} from './api/types';

import { GraphCanvas, type CanvasInteractionState } from './graph/GraphCanvas';
import { applyFilters, collectFacets, type FilterableEdge, type FilterableNode } from './graph/filters';
import { PALETTES, type ColorMode, type Palette } from './graph/palette';
import { collapseCommunities, type CommunityMode } from './graph/community';
import { buildPathHighlight, mergePathIntoGraph, type PathHighlight } from './graph/path';

import { Header } from './components/Header';
import { FilterPanel, ForcePanel } from './components/FilterPanel';
import { Inspector } from './components/Inspector';
import { Legend } from './components/Legend';
import { BreadcrumbBar, type BreadcrumbEntry, type ViewMode } from './components/BreadcrumbBar';
import { ContextMenu, type ContextAction } from './components/ContextMenu';
import { SettingsDialog } from './components/SettingsDialog';
import { SourceDialog } from './components/SourceDialog';
import { MemoryWorkspace } from './components/MemoryWorkspace';

import {
  DEFAULT_FILTERS,
  DEFAULT_FORCE,
  loadPreferences,
  savePreferences,
  type ForceSettingsState,
  type FiltersState,
  type ViewPreferencesState,
} from './state/preferences';

type ErrorState = { code: string; message: string; remediation: string | null } | null;

interface RawGraph {
  nodes: FilterableNode[];
  edges: FilterableEdge[];
  truncated: boolean;
}

const EMPTY_GRAPH: RawGraph = { nodes: [], edges: [], truncated: false };

const CHANGED_MARKER_MS = 8000;

/**
 * How long to coalesce SSE change events before reloading the global graph.
 *
 * A full reindex emits one event per entity batch; without a debounce the
 * dashboard would issue hundreds of identical `/graph/global` requests.
 */
const SSE_REFRESH_DEBOUNCE_MS = 1500;

export default function App(): JSX.Element {
  /* ---------------------------------------------------------------- prefs */
  const [preferences, setPreferences] = useState<ViewPreferencesState>(() => loadPreferences());
  const [editorCommand, setEditorCommand] = useState('code --goto {file}:{line}');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [workspaceMode, setWorkspaceMode] = useState<'graph' | 'memory'>('graph');
  const [mobilePanel, setMobilePanel] = useState<'filters' | 'inspector' | null>(null);

  useEffect(() => {
    savePreferences(preferences);
  }, [preferences]);

  const palette: Palette = PALETTES[preferences.theme];
  const communityMode: CommunityMode = preferences.communityMode;

  /* --------------------------------------------------------------- status */
  const [status, setStatus] = useState<StatusData | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);

  /* ----------------------------------------------------------------- view */
  const [view, setView] = useState<ViewMode>('global');
  const [graph, setGraph] = useState<RawGraph>(EMPTY_GRAPH);
  const [graphError, setGraphError] = useState<ErrorState>(null);
  const [graphLoading, setGraphLoading] = useState(false);

  /* ------------------------------------------------------------ selection */
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(() => new Set());
  const [changedIds, setChangedIds] = useState<Set<string>>(() => new Set());

  const [history, setHistory] = useState<BreadcrumbEntry[]>([]);
  const [future, setFuture] = useState<BreadcrumbEntry[]>([]);

  /* -------------------------------------------------------------- inspect */
  const [entity, setEntity] = useState<EntityData | null>(null);
  const [impact, setImpact] = useState<ImpactData | null>(null);
  const [inspectorError, setInspectorError] = useState<ErrorState>(null);
  const [inspectorLoading, setInspectorLoading] = useState(false);

  /* --------------------------------------------------------------- search */
  const [searchValue, setSearchValue] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  /* ----------------------------------------------------------------- misc */
  const [communities, setCommunities] = useState<CommunitiesData | null>(null);
  const [pathData, setPathData] = useState<PathData | null>(null);
  const [pathEndpoints, setPathEndpoints] = useState<{ from: string; to: string } | null>(null);
  const [layoutRunning, setLayoutRunning] = useState(true);
  const [forceOpen, setForceOpen] = useState(false);
  const [fitToken, setFitToken] = useState(0);
  const [layoutResetToken, setLayoutResetToken] = useState(0);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId: string | null } | null>(null);
  const [sourceTarget, setSourceTarget] = useState<{ path: string; line: number | null } | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [eventsStatus, setEventsStatus] = useState<EventsStatus>('connecting');

  const searchRef = useRef<HTMLInputElement | null>(null);
  const graphAbort = useRef<AbortController | null>(null);
  const inspectorAbort = useRef<AbortController | null>(null);
  const searchAbort = useRef<AbortController | null>(null);
  const refreshTimer = useRef<number | null>(null);
  const liveView = useRef(view);
  const livePreferences = useRef(preferences);
  liveView.current = view;
  livePreferences.current = preferences;

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast((current) => (current === message ? null : current)), 2600);
  }, []);

  /* ---------------------------------------------------------------- status */
  useEffect(() => {
    const controller = new AbortController();
    api
      .status(controller.signal)
      .then((data) => {
        setStatus(data);
        setStatusError(null);
      })
      .catch((error: unknown) => {
        if (isAbortError(error)) return;
        setStatusError(describeError(error).message);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    api
      .communities(communityMode, controller.signal)
      .then(setCommunities)
      .catch(() => {
        // Community metadata is optional; the graph renders without it.
      });
    return () => controller.abort();
  }, [communityMode]);

  /* --------------------------------------------------- graph data loading */

  const loadGlobal = useCallback(
    async (limit: number, aggregate: ViewPreferencesState['aggregate']) => {
      graphAbort.current?.abort();
      const controller = new AbortController();
      graphAbort.current = controller;
      setGraphLoading(true);
      try {
        const payload = await api.globalGraph({ limit, aggregate }, controller.signal);
        setGraph({
          nodes: payload.nodes as FilterableNode[],
          edges: payload.edges as FilterableEdge[],
          truncated: payload.truncated,
        });
        setGraphError(null);
      } catch (error) {
        if (isAbortError(error)) return;
        setGraphError(describeError(error));
      } finally {
        if (!controller.signal.aborted) setGraphLoading(false);
      }
    },
    [],
  );

  const loadLocal = useCallback(async (focusId: string) => {
    graphAbort.current?.abort();
    const controller = new AbortController();
    graphAbort.current = controller;
    setGraphLoading(true);
    try {
      const payload = await api.neighborhood(
        focusId,
        {
          depth: preferences.local.depth,
          direction: preferences.local.direction,
          structuralOnly: preferences.local.structuralOnly,
          fanout: preferences.local.fanout,
        },
        controller.signal,
      );
      setGraph({
        nodes: payload.nodes as FilterableNode[],
        edges: payload.edges as FilterableEdge[],
        truncated: payload.truncated,
      });
      setGraphError(null);
    } catch (error) {
      if (isAbortError(error)) return;
      setGraphError(describeError(error));
    } finally {
      if (!controller.signal.aborted) setGraphLoading(false);
    }
  }, [preferences.local]);

  // Initial load and reload whenever the global payload shape changes.
  useEffect(() => {
    if (workspaceMode !== 'graph') return;
    void loadGlobal(preferences.globalLimit, preferences.aggregate);
    return () => graphAbort.current?.abort();
  }, [workspaceMode, loadGlobal, preferences.globalLimit, preferences.aggregate]);

  /* -------------------------------------------------------------- filtering */

  const filtered = useMemo(
    () => applyFilters(graph.nodes, graph.edges, preferences.filters),
    [graph, preferences.filters],
  );

  const facets = useMemo(
    () => collectFacets(graph.nodes, graph.edges),
    [graph],
  );

  const communityLabels = useMemo<Record<string, string>>(() => {
    const labels: Record<string, string> = {};
    for (const community of communities?.communities ?? []) {
      labels[String(community.community_id)] = community.label ?? `Community ${community.community_id}`;
    }
    return labels;
  }, [communities]);

  /** Applies community collapse after filtering, never before. */
  const collapsedGraph = useMemo(() => {
    if (!preferences.collapseCommunities) return { nodes: filtered.nodes, edges: filtered.edges };
    return collapseCommunities(
      filtered.nodes as GraphNode[],
      filtered.edges as GraphEdge[],
      communityMode,
      communityLabels,
    );
  }, [filtered, preferences.collapseCommunities, communityMode, communityLabels]);
  const displayNodes = collapsedGraph.nodes as FilterableNode[];
  const displayEdges = collapsedGraph.edges as FilterableEdge[];

  /* ------------------------------------------------------------------ path */

  const pathHighlight: PathHighlight | null = useMemo(() => {
    if (view !== 'path' || !pathData || !pathEndpoints) return null;
    return buildPathHighlight(pathData, pathEndpoints.from, pathEndpoints.to, displayEdges);
  }, [view, pathData, pathEndpoints, displayEdges]);

  /* ------------------------------------------------------------- inspector */

  const loadInspector = useCallback(async (id: string) => {
    inspectorAbort.current?.abort();
    const controller = new AbortController();
    inspectorAbort.current = controller;
    setInspectorLoading(true);
    try {
      const data = await api.entity(id, controller.signal);
      setEntity(data);
      setInspectorError(null);
    } catch (error) {
      if (isAbortError(error)) return;
      setEntity(null);
      setInspectorError(describeError(error));
    } finally {
      if (!controller.signal.aborted) setInspectorLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setEntity(null);
      setImpact(null);
      setInspectorError(null);
      return;
    }
    void loadInspector(selectedId);
  }, [selectedId, loadInspector]);

  const loadImpact = useCallback(async (id: string) => {
    try {
      setImpact(await api.impact(id, { maxDepth: 3 }));
    } catch {
      // Impact is supplementary; a failure must not clear the inspector.
    }
  }, []);

  /* --------------------------------------------------------- history + nav */

  const pushHistory = useCallback((id: string, label: string) => {
    setHistory((previous) => [...previous.slice(-49), { id, label }]);
    setFuture([]);
  }, []);

  const selectNode = useCallback(
    (id: string | null, options: { record?: boolean } = {}) => {
      setSelectedId(id);
      if (id && options.record !== false) {
        pushHistory(id, id);
      }
    },
    [pushHistory],
  );

  const focusLocalGraph = useCallback(
    (id: string) => {
      selectNode(id);
      setView('local');
      setPathData(null);
      setPathEndpoints(null);
      void loadLocal(id);
      setFitToken((token) => token + 1);
    },
    [loadLocal, selectNode],
  );

  const navigateHistory = useCallback(
    (entry: BreadcrumbEntry, direction: 'back' | 'forward') => {
      if (direction === 'back') {
        setHistory((previous) => {
          const next = previous.slice(0, -1);
          setFuture((forwardStack) => [...forwardStack, previous[previous.length - 1]]);
          return next;
        });
      } else {
        setFuture((previous) => {
          const next = previous.slice(0, -1);
          setHistory((backStack) => [...backStack, previous[previous.length - 1]]);
          return next;
        });
      }
      setSelectedId(entry.id);
      setEntity(null);
      void loadInspector(entry.id);
    },
    [loadInspector],
  );

  /* ---------------------------------------------------------------- search */

  const runSearch = useCallback(
    async (query: string) => {
      searchAbort.current?.abort();
      if (query.trim().length === 0) {
        setResults([]);
        setView('global');
        return;
      }
      const controller = new AbortController();
      searchAbort.current = controller;
      setSearching(true);
      try {
        const data = await api.search(
          {
            q: query.trim(),
            limit: 50,
            includeSemantic: true,
            includeStructuralContext: true,
          },
          controller.signal,
        );
        setResults(data.results);
        setView('search');

        // The server returns no graph context for a search, so the graph is not
        // replaced here. Selecting a result focuses that entity's local graph,
        // which is the only way to see *why* it matched.
        const best = data.results[0];
        if (best) {
          setSelectedId(best.id);
          setPinnedIds(new Set());
        }
        const degraded = [
          ...(Array.isArray(data.degraded) ? data.degraded : []),
          ...(Array.isArray(data.routing?.degraded) ? data.routing.degraded : []),
        ];
        if (degraded.length > 0) {
          // Surface the real reason and what to do about it, rather than a bare
          // flag that leaves the user guessing which channel went missing.
          showToast(`${describeDegradation(degraded[0])}`);
        }
      } catch (error) {
        if (isAbortError(error)) return;
        showToast(describeError(error).message);
      } finally {
        if (!controller.signal.aborted) setSearching(false);
      }
    },
    [showToast],
  );

  /* ------------------------------------------------------------------ path */

  const runPath = useCallback(
    async (from: string, to: string) => {
      graphAbort.current?.abort();
      const controller = new AbortController();
      graphAbort.current = controller;
      setGraphLoading(true);
      try {
        const data = await api.path({ from, to }, controller.signal);
        setPathData(data);
        setPathEndpoints({ from, to });
        setView('path');
        if (data.found) {
          const merged = mergePathIntoGraph(
            displayNodes,
            displayEdges,
            data,
          );
          setGraph({ nodes: merged.nodes, edges: merged.edges, truncated: graph.truncated });
        } else {
          showToast('No path found between those entities.');
        }
        setFitToken((token) => token + 1);
      } catch (error) {
        if (isAbortError(error)) return;
        setGraphError(describeError(error));
      } finally {
        if (!controller.signal.aborted) setGraphLoading(false);
      }
    },
    [displayNodes, displayEdges, graph.truncated, showToast],
  );

  /* ------------------------------------------------------------- live SSE */

  /**
   * Coalesces change events.
   *
   * A reindex emits one event per batch of entities, so a single scan can
   * produce hundreds of events in a second. Marking each node changed is cheap
   * and instant, but refetching per event would be a denial of service against
   * the server, so the refetch is debounced and only the *global* view is
   * reloaded. The local, path and search views keep the payload the user is
   * actually looking at.
   */
  useEffect(() => {
    const client = new EventsClient({
      onStatus: setEventsStatus,
      onChange: (change) => {
        const touched = change.ids.filter((id) => !id.startsWith('root:'));
        if (touched.length === 0) return;

        // Mark immediately so the change is visible before the refetch lands.
        setChangedIds((previous) => {
          const next = new Set(previous);
          for (const id of touched) next.add(id);
          return next;
        });
        window.setTimeout(() => {
          setChangedIds((previous) => {
            const next = new Set(previous);
            for (const id of touched) next.delete(id);
            return next;
          });
        }, CHANGED_MARKER_MS);

        if (liveView.current !== 'global') return;
        if (refreshTimer.current !== null) window.clearTimeout(refreshTimer.current);
        refreshTimer.current = window.setTimeout(() => {
          refreshTimer.current = null;
          void loadGlobal(livePreferences.current.globalLimit, livePreferences.current.aggregate);
        }, SSE_REFRESH_DEBOUNCE_MS);
      },
      onError: () => {
        // The client retries with backoff; the status pill reports the state.
      },
    });

    client.start();
    return () => {
      client.close();
      if (refreshTimer.current !== null) {
        window.clearTimeout(refreshTimer.current);
        refreshTimer.current = null;
      }
    };
  }, [loadGlobal]);

  /* -------------------------------------------------------------- keyboard */

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const typing =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement;

      if (event.key === '/' && !typing) {
        event.preventDefault();
        searchRef.current?.focus();
        return;
      }
      if (event.key === 'Escape') {
        setContextMenu(null);
        setSettingsOpen(false);
        if (typing) (target as HTMLInputElement).blur();
        else if (selectedId) selectNode(null);
        return;
      }
      if (event.altKey && event.key === 'ArrowLeft') {
        event.preventDefault();
        const entry = history[history.length - 1];
        if (entry) navigateHistory(entry, 'back');
        return;
      }
      if (event.altKey && event.key === 'ArrowRight') {
        event.preventDefault();
        const entry = future[future.length - 1];
        if (entry) navigateHistory(entry, 'forward');
        return;
      }
      if (typing) return;
      if (event.key === 'f') setFitToken((token) => token + 1);
      if (event.key === ' ') {
        event.preventDefault();
        setLayoutRunning((running) => !running);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [history, future, navigateHistory, selectedId, selectNode]);

  /* ------------------------------------------------------- context menu ops */

  const contextActions = useMemo<ContextAction[]>(() => {
    if (!contextMenu?.nodeId) {
      return [
        { id: 'fit', label: 'Fit graph', shortcut: 'F' },
        { id: 'reset-layout', label: 'Reset layout' },
        { id: 'collapse', label: preferences.collapseCommunities ? 'Expand communities' : 'Collapse communities' },
      ];
    }
    return [
      { id: 'local', label: 'Open local graph', shortcut: 'double-click' },
      { id: 'explain', label: 'Explain' },
      { id: 'related', label: 'Show related' },
      { id: 'path-from', label: 'Path from here…' },
      { id: 'path-to', label: 'Path to here…' },
      { id: 'impact', label: 'Show impact' },
      { id: 'pin', label: pinnedIds.has(contextMenu.nodeId) ? 'Unpin' : 'Pin' },
      { id: 'copy-id', label: 'Copy id' },
    ];
  }, [contextMenu, pinnedIds, preferences.collapseCommunities]);

  const runContextAction = useCallback(
    (actionId: string) => {
      const nodeId = contextMenu?.nodeId;
      setContextMenu(null);
      if (!nodeId) {
        if (actionId === 'fit') setFitToken((token) => token + 1);
        if (actionId === 'reset-layout') {
          setLayoutRunning(true);
          setLayoutResetToken((token) => token + 1);
          setFitToken((token) => token + 1);
        }
        if (actionId === 'collapse') {
          setPreferences((previous) => ({
            ...previous,
            collapseCommunities: !previous.collapseCommunities,
          }));
        }
        return;
      }
      switch (actionId) {
        case 'local':
          focusLocalGraph(nodeId);
          break;
        case 'explain':
          selectNode(nodeId);
          void loadInspector(nodeId);
          void loadImpact(nodeId);
          showToast(`Structural relations and evidence for ${nodeId.slice(0, 12)}…`);
          break;
        case 'related':
          focusLocalGraph(nodeId);
          break;
        case 'path-from': {
          const other = window.prompt('Path from this entity to which id?');
          if (other) void runPath(nodeId, other.trim());
          break;
        }
        case 'path-to': {
          const other = window.prompt('Path from which id to this entity?');
          if (other) void runPath(other.trim(), nodeId);
          break;
        }
        case 'impact':
          selectNode(nodeId);
          void loadImpact(nodeId);
          break;
        case 'pin':
          setPinnedIds((previous) => {
            const next = new Set(previous);
            if (next.has(nodeId)) next.delete(nodeId);
            else next.add(nodeId);
            return next;
          });
          break;
        case 'copy-id':
          void navigator.clipboard?.writeText(nodeId);
          showToast('Copied entity id.');
          break;
        default:
          break;
      }
    },
    [contextMenu, focusLocalGraph, selectNode, loadInspector, loadImpact, runPath, showToast],
  );

  /* -------------------------------------------------------------- assembly */

  const interaction: CanvasInteractionState = useMemo(
    () => ({
      selectedId,
      hoveredId,
      pinnedIds,
      changedIds,
      pathNodeIds: pathHighlight?.nodeIds ?? new Set(),
      pathEdgeIds: pathHighlight?.edgeIds ?? new Set(),
    }),
    [selectedId, hoveredId, pinnedIds, changedIds, pathHighlight],
  );

  const pathDescription = pathHighlight
    ? `${pathHighlight.hops} hops from ${pathHighlight.from.slice(0, 16)}… to ${pathHighlight.to.slice(0, 16)}…`
    : null;


  const updatePreferences = useCallback((next: ViewPreferencesState) => setPreferences(next), []);
  const resetLayout = useCallback(() => {
    setLayoutRunning(true);
    setLayoutResetToken((token) => token + 1);
    setFitToken((token) => token + 1);
  }, []);

  return (
    <div className="app" data-theme={preferences.theme}>
      <Header
        workspaceMode={workspaceMode}
        onWorkspaceModeChange={(mode) => setWorkspaceMode(mode)}
        status={status}
        statusError={statusError}
        eventsStatus={eventsStatus}
        theme={preferences.theme}
        palette={palette}
        searchValue={searchValue}
        searching={searching}
        onSearchChange={setSearchValue}
        onSearchSubmit={(value) => void runSearch(value)}
        onToggleTheme={() =>
          setPreferences((previous) => ({
            ...previous,
            theme: previous.theme === 'dark' ? 'light' : 'dark',
          }))
        }
        onToggleLegend={() =>
          setPreferences((previous) => ({ ...previous, showLegend: !previous.showLegend }))
        }
        onOpenSettings={() => setSettingsOpen(true)}
        onToggleFilters={() => setMobilePanel((panel) => panel === 'filters' ? null : 'filters')}
        onToggleInspector={() => setMobilePanel((panel) => panel === 'inspector' ? null : 'inspector')}
        ref={searchRef}
      />

      {workspaceMode === 'memory' ? (
        <MemoryWorkspace onNotify={showToast} />
      ) : <main className={`app__body${mobilePanel ? ` app__body--${mobilePanel}` : ''}`}>
        <div className="app__left" aria-label="Graph filters">
          <FilterPanel
            facets={facets}
            filters={preferences.filters}
            visibleCount={filtered.nodes.length}
            totalCount={graph.nodes.length}
            communityMode={communityMode}
            onChange={(filters: FiltersState) =>
              setPreferences((previous) => ({ ...previous, filters }))
            }
            onReset={() =>
              setPreferences((previous) => ({ ...previous, filters: DEFAULT_FILTERS }))
            }
          />
        </div>

        <section className="app__canvas" aria-label="Graph canvas">
          {graphError ? (
            <div className="canvasMessage canvasMessage--error" role="alert">
              <h2>{graphError.code}</h2>
              <p>{graphError.message}</p>
              {graphError.remediation && <p className="canvasMessage__remedy">{graphError.remediation}</p>}
              <button
                type="button"
                onClick={() => void loadGlobal(preferences.globalLimit, preferences.aggregate)}
              >
                Retry
              </button>
            </div>
          ) : (
            <GraphCanvas
              nodes={displayNodes}
              edges={displayEdges}
              palette={palette}
              colorMode={preferences.colorMode as ColorMode}
              interaction={interaction}
              forceSettings={preferences.force}
              layoutResetToken={layoutResetToken}
              layoutRunning={layoutRunning}
              onLayoutRunningChange={setLayoutRunning}
              showLabels={preferences.showLabels}
              hideLowValueEdges={preferences.hideLowValueEdges}
              fitToken={fitToken}
              onSelect={(id) => selectNode(id)}
              onHover={setHoveredId}
              onFocusNode={focusLocalGraph}
              onContextMenu={(id, x, y) => setContextMenu({ nodeId: id, x, y })}
              onNodePinned={(id, pinned) =>
                setPinnedIds((previous) => {
                  const next = new Set(previous);
                  if (pinned) next.add(id);
                  else next.delete(id);
                  return next;
                })
              }
              onLayoutFrame={() => undefined}
            />
          )}

          {graphLoading && <div className="canvasBadge">loading…</div>}

          <div className="canvasControls">
            <button type="button" onClick={() => setFitToken((token) => token + 1)} title="Fit (F)">
              fit
            </button>
            <button
              type="button"
              onClick={() => setLayoutRunning((running) => !running)}
              title="Pause/resume layout (Space)"
            >
              {layoutRunning ? 'pause' : 'resume'}
            </button>
            <button
              type="button"
              onClick={resetLayout}
              title="Re-seed positions"
            >
              reset layout
            </button>
          </div>

          {preferences.showLegend && (
            <Legend
              palette={palette}
              colorMode={preferences.colorMode}
              facets={facets}
              communityMode={communityMode}
              communityCount={
                preferences.colorMode === 'community'
                  ? facets.communities.length
                  : (status?.communities[communityMode] ?? 0)
              }
            />
          )}
        </section>

        <div className="app__right" aria-label="Selected entity details">
          <Inspector
            entity={entity}
            impact={impact}
            loading={inspectorLoading}
            error={inspectorError}
            palette={palette}
            onNavigate={(id) => selectNode(id)}
            onFocusLocal={focusLocalGraph}
            onPathFrom={(id) => {
              const other = window.prompt('Path from which id to this entity?');
              if (other) void runPath(other.trim(), id);
            }}
            onPathTo={(id) => {
              const other = window.prompt('Path from this entity to which id?');
              if (other) void runPath(id, other.trim());
            }}
            onImpact={(id) => void loadImpact(id)}
            onExplain={(id) => {
              selectNode(id);
              void loadImpact(id);
            }}
            onCopy={(text, what) => {
              void navigator.clipboard?.writeText(text);
              showToast(`Copied ${what}.`);
            }}
            onOpenSource={(path, line) => setSourceTarget({ path, line })}
            onClose={() => selectNode(null)}
          />
        </div>
      </main>}

      {workspaceMode === 'graph' && <BreadcrumbBar
        view={view}
        truncated={graph.truncated}
        communityMode={communityMode}
        pathDescription={pathDescription}
        results={results}
        historyBack={history}
        historyForward={future}
        onNavigateHistory={navigateHistory}
        onClearPath={() => {
          setPathData(null);
          setPathEndpoints(null);
          setView('global');
        }}
        onSelectResult={(result) => {
          selectNode(result.id);
          if (!graph.nodes.some((node) => node.id === result.id)) {
            focusLocalGraph(result.id);
          }
        }}
        onViewChange={(next) => {
          if (next === 'global') {
            setView('global');
            setPathData(null);
            setPathEndpoints(null);
            void loadGlobal(preferences.globalLimit, preferences.aggregate);
          } else if (next === 'local' && selectedId) {
            setView('local');
            void loadLocal(selectedId);
          } else if (next === 'search') {
            setView('search');
          }
        }}
      />}

      {workspaceMode === 'graph' && <div className="app__overlays">
        <ForcePanel
          settings={preferences.force}
          open={forceOpen}
          onToggleOpen={() => setForceOpen((open) => !open)}
          onChange={(force: ForceSettingsState) =>
            setPreferences((previous) => ({ ...previous, force }))
          }
          onReset={() =>
            setPreferences((previous) => ({ ...previous, force: DEFAULT_FORCE }))
          }
        />
      </div>}

      {workspaceMode === 'graph' && contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          nodeId={contextMenu.nodeId}
          actions={contextActions}
          onRun={runContextAction}
          onClose={() => setContextMenu(null)}
        />
      )}

      {workspaceMode === 'graph' && <SettingsDialog
        open={settingsOpen}
        preferences={preferences}
        onChange={updatePreferences}
        onClose={() => setSettingsOpen(false)}
        onResetLayout={resetLayout}
        onClearPositions={() => showToast('Saved node positions cleared.')}
        editorCommand={editorCommand}
        onEditorCommandChange={setEditorCommand}
      />}

      {workspaceMode === 'graph' && sourceTarget && (
        <SourceDialog
          path={sourceTarget.path}
          line={sourceTarget.line}
          editorCommand={editorCommand}
          onClose={() => setSourceTarget(null)}
        />
      )}

      {toast && <div className="toast" role="status">{toast}</div>}
    </div>
  );
}
