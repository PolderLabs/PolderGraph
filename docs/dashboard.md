# Dashboard: Obsidian-style interactive graph explorer

The dashboard is intentionally simple and graph-first. It should feel closer to Obsidian's graph view than to a BI dashboard.

Run:

```bash
poldergraph ui
```

Default bind: `127.0.0.1` only. Open the browser automatically unless `--no-open`.

## Primary layout

```text
+-----------------------------------------------------------------------+
| PolderGraph | workspace | Search...                 status | settings  |
+------------------+-------------------------------------+---------------+
| filters/explorer |                                     | inspector     |
|                  |            graph canvas             |               |
| node types       |                                     | selected node |
| edge types       |       o----o                        | source        |
| communities      |     /   \    \                    | relations     |
| roots/paths      |    o     o----o                     | semantic      |
|                  |     \  /                           | community     |
| semantic slider  |       o                             | actions       |
| depth/fanout     |                                     |               |
+------------------+-------------------------------------+---------------+
| search result / breadcrumb / selected path                             |
+-----------------------------------------------------------------------+
```

The canvas dominates available space.

## Graph technology

Use Graphology as client graph representation and Sigma.js as the WebGL renderer. Use a ForceAtlas2 worker for force-directed layout so layout does not block the UI thread.

Do not require server-side layout for ordinary browsing.

Persist manual node positions per local workspace/view where practical.

## Views

### Global graph

Shows a sampled/aggregated repository graph. Large repositories must not send every node/edge to the browser immediately.

Server supplies:
- important nodes
- communities
- directory/module aggregates
- bounded structural connections

The user can progressively expand.

### Local graph

Equivalent to Obsidian's local graph concept: selected entity at center plus N-hop neighborhood.

Controls:
- depth 1..N
- incoming/outgoing/both
- structural-only / semantic
- edge types
- node kinds
- fan-out cap

### Search graph

Searching replaces or overlays the graph with search results plus their most informative connections.

### Path view

Visually emphasizes one or more paths between selected nodes and dims unrelated nodes.

## Interaction

Required:
- zoom/pan
- click select
- double-click focus/local graph
- drag node
- box/lasso selection if renderer support is clean
- hover neighbor highlighting
- keyboard search focus
- escape clears focus/modal
- back/forward selection history
- fit graph
- reset layout
- pause/resume layout
- pin/unpin node
- copy qualified name/path
- open source location in configurable editor
- context menu: explain, related, path from, path to, impact

## Visual encoding

Avoid arbitrary rainbow noise.

Node encodings:
- color: configurable by node kind OR community
- size: graph importance/degree with bounded scale
- border/ring: selected, changed, unresolved state
- icon/shape only if it remains legible at graph scale

Edge encodings:
- structural edges visually stronger
- semantic edges visually distinct and lighter/dashed where renderer permits
- inferred/ambiguous edges visually distinguishable from extracted/resolved
- hover/selection increases emphasis

Always include a legend.

## Filters

Graph filters inspired by Obsidian should be instant client-side when possible:
- text query
- node kind
- language
- path/root
- community
- edge type
- provenance
- minimum semantic similarity
- hide generated/external
- only tests/docs/source/media
- changed since current Git base where available

A filter changes visibility; it does not mutate the persisted graph.

## Force controls

Expose advanced layout controls in a collapsible panel:
- gravity
- scaling ratio
- slow-down/speed
- edge weight influence
- strong gravity mode
- prevent overlap if supported without unacceptable cost

Provide a reset-to-default button.

Most users should never need to touch these.

## Search

Top search supports:
- symbols
- file paths
- free natural language

Search results display a badge identifying match evidence:
- exact
- lexical
- semantic
- graph-expanded

Selecting a result focuses the graph and inspector.

## Inspector

For selected entity show:
- kind + qualified name
- file and lines
- signature
- docstring/excerpt
- parent/module/community
- structural inbound/outbound relationships grouped by type
- semantic neighbors with similarity values
- tests/docs relationships
- provenance/confidence
- graph metrics
- actions

Click a relation to navigate without closing the inspector.

## Community experience

Community mode can collapse each community to a meta-node. Expanding a community reveals its members.

Show both:
- Structural communities
- Hybrid communities

The UI must label which mode is active because their meaning differs.

## Performance strategy

For large graphs:
- initial graph response is capped
- aggregate by directory/module/community
- server-side neighborhood queries
- progressive expansion
- WebGL rendering
- ForceAtlas2 in web worker
- do not render edge labels globally
- hide low-value edges until zoom/focus
- abort stale API requests when the user changes focus quickly

Target smooth interaction on tens of thousands of visible elements; very large underlying graphs must rely on aggregation rather than attempting to render everything.

## Live updates

When `poldergraph watch` is active, dashboard receives index-change events by WebSocket/SSE.

Update behavior:
- changed nodes get a temporary visual marker
- deleted nodes disappear
- newly discovered nodes may appear if current filters include them
- layout should not completely explode/reset on every incremental update

## API surface used by dashboard

At minimum:
- `GET /api/status`
- `GET /api/graph/global`
- `GET /api/graph/neighborhood/{id}`
- `GET /api/entity/{id}`
- `GET /api/search?q=`
- `GET /api/path?from=&to=`
- `GET /api/communities`
- `GET /api/impact/{id}`
- `POST /api/view/preferences`
- `GET /api/events` or WebSocket equivalent

All responses use stable IDs and explicit provenance.

## Security

Default host is loopback. Binding to non-loopback requires an explicit flag and warning.

The dashboard API must not expose arbitrary filesystem reads. Source endpoints may return content only for indexed paths inside configured roots.

Never interpolate graph labels into HTML unsafely.
