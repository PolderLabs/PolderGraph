# Dashboard graph layout

How the graph view arranges nodes, and why it behaves the way it does.

## The problem it had

Three symptoms, all reported from real use: the graph looked dense, it never
stopped moving, and everything collapsed into clumps with nodes drawn on top of
each other.

The root cause was structural, not cosmetic.

## Why ForceAtlas2 could not work here

ForceAtlas2 — the algorithm the dashboard used — applies **constant forces for
as long as it is iterated**. It has no notion of the system cooling down. In a
browser that means:

- The layout never stops, so the graph twitches and clicks land on the wrong node.
- Because nothing ever loses to attraction, the layout keeps contracting into
  clumps over time.
- There is no principled way to stop it. Any movement threshold fights the forces
  that are still running.

Two further bugs hid the real problem:

- `onRunningChange` was accepted by the layout controller but **never passed in**,
  so a finished run could never tell the UI it had finished.
- The overlap facility was dead code. `canPreventOverlap()` gated on
  `adjustSizes === true` while the shipped defaults set it to `false`, and
  `preventOverlap` was not set anywhere at all — the bundled
  `graphology-layout-forceatlas2` version does not support the option, so the
  guard could never enable it.

## What it uses now

[d3-force](https://d3js.org/d3-force), which is what powers Obsidian's graph
view. It fixes the root cause: **every force is multiplied by a global `alpha`
that decays geometrically**, so motion dies away on its own and the simulation
reaches a true rest state. `alphaDecay` and `alphaMin` are explicit parameters,
so there is no threshold to tune and nothing to fight.

| Force | Purpose |
|---|---|
| `forceManyBody` | Long-range repulsion, which spreads the graph out |
| `forceLink` | Springs along edges, which keeps related code together |
| `forceCollide` | Keeps node circles from overlapping |
| `forceCenter` | Recentres by translating the group, preserving the spread |

`forceCenter` translates the centroid rather than pulling each node inward. That
distinction matters: pulling nodes toward the origin competes with repulsion at
long range, where charge has already decayed to nothing, and collapses the
layout onto a line.

Edge springs are d3's progressive form, which distributes a node's pull across its
degree. Without it a hub with hundreds of edges tears its neighbours apart.

The settings exposed under **Force layout** are renamed after the forces that
actually run — repulsion, link strength, link distance, centering, settling,
node spacing. The ForceAtlas2 knobs had no effect on this model and are gone
rather than left as decoration.

## Verification

Checked in a real browser against a 1,000-node index:

- Two frames captured four seconds apart after settling are **byte-identical**,
  which is the objective test for jitter.
- The run settles in about **3 seconds**, after which the control reads "resume".
- Communities separate into readable clusters; nodes do not overlap.
- Selecting a node still opens the inspector with its actions
  (local graph, path from/to, impact, explain).
- No page errors; seven canvases render.

## Dragging

Nodes are draggable, and the rest of the graph rearranges around the one you
are holding. Sigma 3 has no drag events, so dragging is driven from the canvas
container: press a node, follow the pointer, release.

The important part is that a drag **wakes the simulation**. A settled layout has
no forces running, so without that the node would simply be pulled across a
frozen picture and nothing else would move. Dragging restores a small amount of
energy (`DRAG_ALPHA`) and pins the held node to the cursor; when the node is
released the layout decays back to rest on its own, so the graph never ends up
permanently animating after an interaction.

A press that never moves is treated as a click, not a drag, so selecting a node
still pins it rather than nudging the whole graph.

Verified in a browser: dragging a node opens its source in the inspector, the
surrounding clusters visibly re-settle around the new position, and two frames
captured four seconds after the drag are byte-identical.

## Degenerate layouts recover themselves

A layout collapsed into a line is still "settled" as far as alpha is concerned,
so it needs its own check. When the run finishes, the worker measures the
bounding box; if it is more than eight times wider than it is tall (or the
reverse), the graph is treated as a failure rather than a result and is laid out
again from the seed. One automatic rescue only, so a genuinely sparse graph is
left alone rather than being laid out forever.

This was added after a drag was seen leaving the graph as a single diagonal line
that never recovered on its own.

Dragging was also made non-destructive: the dragged node is moved through the
graph and the woken forces pull the neighbourhood around it, rather than being
pinned inside the worker. Pinning needs the node's index to stay in step with the
worker's own node list, and a single mismatch there corrupts the whole layout.

## Spacing

The shipped values favour a readable graph over a compact one: repulsion is
strong (`chargeStrength: -520`), edges prefer a longer rest length
(`linkDistance: 85`) and pull weakly (`linkStrength: 0.22`), and nodes keep a
visible gap (`collisionPadding: 9`). Communities separate into distinct groups
instead of one crowded mass.

## Also worth knowing

- Repulsion uses `distanceMax` to bound work, and the exact pass is skipped above
  a node count where it would stall the worker.
- Node identity travels to the worker as an id table with typed arrays indexed
  into it; a worker cannot receive strings inside a typed array.
- The camera refits once, on the transition into paused, because a settled
  layout can finish well inside or outside the viewport.