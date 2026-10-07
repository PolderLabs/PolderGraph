# Dashboard controls

Run `poldergraph ui` to start. Default: `http://127.0.0.1:7432`.

## Layout

- **Header**: workspace name, search bar, status indicator, settings
- **Left panel**: filters, node/edge type toggles, community selector, force controls
- **Canvas**: the interactive graph, always the largest area
- **Right panel**: inspector for the selected entity
- **Bottom bar**: breadcrumb, search results, selected path

## Views

| View | Trigger | Description |
|------|---------|-------------|
| Global | Default | Aggregated repository graph with important nodes |
| Local | Double-click a node | N-hop neighbourhood around the selected entity |
| Search | Type in the search bar | Results plus their most informative connections |
| Path | Context menu → "Path from" | Emphasizes a path, dims unrelated nodes |

## Interaction

| Action | Input |
|--------|-------|
| Zoom | Scroll wheel |
| Pan | Click-drag on canvas |
| Select | Click a node |
| Focus (local graph) | Double-click a node |
| Drag node | Click-drag a node |
| Pin/unpin | Context menu or drag |
| Copy name | Right-click → copy |
| Back/forward | Browser back/forward or keyboard |
| Context menu | Right-click |
| Search focus | `/` key |
| Clear focus | `Escape` |

## Filters

All filters are instant client-side operations that change visibility without mutating the graph:
- Text query (nodes matching a search term)
- Node kind (function, class, method, etc.)
- Language (python, typescript, etc.)
- Community (structural or hybrid)
- Edge type (calls, imports, inherits, etc.)
- Provenance (extracted, resolved, semantic, etc.)
- Minimum semantic similarity slider
- Hide generated/external
- Show only tests/docs/source

## Visual encoding

- **Node colour**: configurable by kind or community (toggle in settings)
- **Node size**: importance/degree with bounded scale
- **Node border**: selected, changed, unresolved states
- **Edge colour**: structural edges stronger; semantic edges dashed and lighter
- **Edge colour by provenance**: extracted/resolved blue, inferred dashed, semantic green, ambiguous red
- **Legend**: always visible

## Community modes

Toggle between:
- **Structural communities**: implementation topology from deterministic relationships
- **Hybrid communities**: adds high-confidence semantic edges

The UI labels which mode is active because their meanings differ.

## Advanced force controls

Collapsible panel with:
- Gravity
- Scaling ratio
- Slow-down/speed
- Edge weight influence
- Strong gravity mode
- Prevent overlap
- Reset to default

## Settings

- Colour mode (kind / community)
- Dark/light theme toggle
- Clear saved node positions
- Force layout controls (advanced panel)

## Live updates

When `poldergraph watch` is active, the dashboard receives index-change events via SSE:
- Changed nodes get a temporary visual marker
- Deleted nodes disappear
- New nodes appear if current filters include them
- Layout does not reset on incremental updates