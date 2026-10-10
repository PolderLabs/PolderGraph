import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Graph from 'graphology';
import { MeasuredSigma } from './MeasuredSigma';
import { EdgeRectangleProgram, NodeCircleProgram } from 'sigma/rendering';
import type { EdgeDisplayData, NodeDisplayData, SigmaNodeEventPayload } from 'sigma/types';

import type { FilterableEdge, FilterableNode } from './filters';
import {
  AGGREGATE_SIZE_SCALE,
  communityColor,
  DEFAULT_SIZE_SCALE,
  edgeColor,
  edgeSizeFor,
  nodeColorForKind,
  sizeForImportance,
} from './palette';
import type { ColorMode, Palette } from './palette';
import { LayoutController } from './layout';
import { buildAdjacency, syncGraph, TRANSPARENT } from './sync';
import type { PgEdgeAttributes, PgNodeAttributes } from './attributes';
import type { ForceSettingsState } from '../state/preferences';
import { desaturate } from '../util/color';
import { DashedEdgeProgram } from './edgeProgram';
import { NodeRingProgram } from './ringProgram';

/** Sigma instance typed with the attributes this app stores on each item. */
type PgSigma = MeasuredSigma<PgNodeAttributes, PgEdgeAttributes>;

/** Sigma hands reducers the graph's own attribute object plus display fields. */
type NodeDisplay = NodeDisplayData & PgNodeAttributes;
type EdgeDisplay = EdgeDisplayData & PgEdgeAttributes;

export interface CanvasInteractionState {
  selectedId: string | null;
  hoveredId: string | null;
  pinnedIds: Set<string>;
  changedIds: Set<string>;
  /** Node ids on the emphasised path; empty means "no path view". */
  pathNodeIds: Set<string>;
  pathEdgeIds: Set<string>;
}

export interface GraphCanvasProps {
  nodes: FilterableNode[];
  edges: FilterableEdge[];
  palette: Palette;
  colorMode: ColorMode;
  interaction: CanvasInteractionState;
  forceSettings: ForceSettingsState;
  layoutRunning: boolean;
  /**
   * Reports that the layout settled or started, so the UI can stop showing a
   * running layout and leave the canvas still.
   */
  onLayoutRunningChange?: (running: boolean) => void;
  showLabels: boolean;
  hideLowValueEdges: boolean;
  /** Bumping this refits the camera (view switch, reset). */
  fitToken: number;
  /** Bumping this re-seeds node positions and resumes the layout worker. */
  layoutResetToken: number;
  onSelect: (id: string | null) => void;
  onHover: (id: string | null) => void;
  onFocusNode: (id: string) => void;
  onContextMenu: (id: string | null, x: number, y: number) => void;
  onNodePinned: (id: string, pinned: boolean) => void;
  onLayoutFrame: () => void;
}

interface CanvasHandle {
  sigma: PgSigma;
  graph: Graph<PgNodeAttributes, PgEdgeAttributes>;
  controller: LayoutController;
  /** Undirected adjacency, rebuilt when the topology changes. */
  adjacency: Map<string, Set<string>>;
}

/**
 * WebGL graph canvas.
 *
 * Sigma, the graphology graph and the layout controller are created once and
 * mutated in place. Rebuilding the renderer on every data change would drop the
 * camera, the WebGL contexts and all node positions, which is exactly what
 * makes a live update feel like a page reload.
 *
 * Node size is in device pixels (`itemSizesReference: "screen"`), so a node
 * radius stays a readable number of pixels no matter how ForceAtlas2 rescales
 * the coordinate space while it settles.
 */
export function GraphCanvas(props: GraphCanvasProps): JSX.Element {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const handleRef = useRef<CanvasHandle | null>(null);
  const [ready, setReady] = useState(false);

  // Sigma callbacks and reducers are installed once; they read live props here.
  const propsRef = useRef(props);
  propsRef.current = props;

  /* ------------------------------------------------------------------ setup */

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const graph = new Graph<PgNodeAttributes, PgEdgeAttributes>({ multi: false, type: 'mixed' });
    const controller = new LayoutController({
      graph,
      onFrame: () => propsRef.current.onLayoutFrame(),
      onRunningChange: (running: boolean) => propsRef.current.onLayoutRunningChange?.(running),
    });

    const sigma = new MeasuredSigma<PgNodeAttributes, PgEdgeAttributes>(graph, container, {
      // The ring is a second node program: Sigma 3 has no per-node border, so
      // selected / changed / unresolved / pinned are drawn as a hollow disc.
      nodeProgramClasses: {
        circle: NodeCircleProgram<PgNodeAttributes, PgEdgeAttributes>,
        ringed: NodeRingProgram<PgNodeAttributes, PgEdgeAttributes>,
      },
      // A semantic edge is evidence, not a fact, and is drawn dashed. Sigma 3
      // exposes custom edge programs as a documented extension point.
      edgeProgramClasses: {
        line: EdgeRectangleProgram<PgNodeAttributes, PgEdgeAttributes>,
        dashed: DashedEdgeProgram<PgNodeAttributes, PgEdgeAttributes>,
      },
      defaultNodeType: 'circle',
      defaultEdgeType: 'line',
      // Pixel-sized items: a node radius stays a real number of pixels however
      // ForceAtlas2 rescales the coordinate space while it settles.
      itemSizesReference: 'screen',
      nodeReducer: (node, data) =>
        reduceNode(node, data as NodeDisplay, propsRef.current, handleRef.current),
      edgeReducer: (edge, data) => reduceEdge(edge, data as EdgeDisplay, propsRef.current),
      // Resize handling is ours; Sigma would otherwise fight the observer.
      allowInvalidContainer: true,
      // Edge labels are never drawn globally: at graph scale they are noise.
      renderEdgeLabels: false,
      renderLabels: true,
      labelDensity: 0.12,
      labelGridCellSize: 110,
      // Below this rendered diameter a label is unreadable clutter.
      labelRenderedSizeThreshold: 9,
      minEdgeThickness: 0.6,
      labelColor: { attribute: 'labelColor' },
      // ForceAtlas2 changes coordinate bounds while settling; keep all nodes
      // fitted so layout movement remains visible across desktop and mobile.
      autoRescale: true,
      stagePadding: 24,
      zIndex: true,
    }) as PgSigma;

    handleRef.current = { sigma, graph, controller, adjacency: new Map() };
    // Diagnostic handle for the node-coordinate measurement: a ref callback runs
    // before this effect, so the instance is published here.
    if (container) {
      (container as HTMLDivElement & { pgSigma?: PgSigma }).pgSigma = sigma;
    }
    setReady(true);

    const onResize = () => sigma.refresh();
    window.addEventListener('resize', onResize);

    return () => {
      window.removeEventListener('resize', onResize);
      controller.destroy();
      sigma.kill();
      handleRef.current = null;
      setReady(false);
    };
  }, []);

  /* ------------------------------------------------------------ graph payload */

  useEffect(() => {
    const handle = handleRef.current;
    if (!ready || !handle) return;

    const topologyChanged = syncGraph(handle.graph, props.nodes, props.edges);
    if (topologyChanged) handle.adjacency = buildAdjacency(handle.graph);
    handle.controller.sync();
    handle.sigma.refresh();
  }, [ready, props.nodes, props.edges]);

  /* -------------------------------------------------------- layout controls */

  useEffect(() => {
    const handle = handleRef.current;
    if (!ready || !handle) return;
    const force = props.forceSettings;
    handle.controller.setSettings({
      chargeStrength: force.chargeStrength,
      linkStrength: force.linkStrength,
      linkDistance: force.linkDistance,
      centerStrength: force.centerStrength,
      velocityDecay: force.velocityDecay,
      collisionPadding: force.collisionPadding,
    });
  }, [ready, props.forceSettings]);

  const wasLayoutRunning = useRef(false);
  useEffect(() => {
    const handle = handleRef.current;
    if (!ready || !handle) return;
    if (props.layoutRunning) {
      wasLayoutRunning.current = true;
      handle.controller.start();
    } else {
      handle.controller.stop();
      // Refit only on the transition into paused. A settled layout can finish
      // well inside or well outside the current viewport, and a viewer should
      // see the whole result instead of one corner of it.
      if (wasLayoutRunning.current) {
        wasLayoutRunning.current = false;
        handle.sigma.getCamera().animatedReset({ duration: 320 });
      }
    }
  }, [ready, props.layoutRunning]);

  /* ------------------------------------------------------ appearance refresh */

  useEffect(() => {
    const handle = handleRef.current;
    if (!ready || !handle) return;
    handle.sigma.setSetting('renderLabels', props.showLabels);
    handle.sigma.refresh();
  }, [ready, props.showLabels]);

  // Selection, hover, pin, change and path state all feed the reducers.
  useEffect(() => {
    handleRef.current?.sigma.refresh();
  }, [
    ready,
    props.interaction.selectedId,
    props.interaction.hoveredId,
    props.palette,
    props.colorMode,
    props.hideLowValueEdges,
    props.interaction.pinnedIds,
    props.interaction.changedIds,
    props.interaction.pathNodeIds,
    props.interaction.pathEdgeIds,
  ]);

  /* ---------------------------------------------------------------- camera */

  useEffect(() => {
    const handle = handleRef.current;
    if (!ready || !handle || props.fitToken === 0) return;
    handle.sigma.getCamera().animatedReset({ duration: 320 });
  }, [ready, props.fitToken]);

  useEffect(() => {
    const handle = handleRef.current;
    if (!ready || !handle || props.layoutResetToken === 0) return;
    handle.controller.resetLayout();
    handle.sigma.refresh();
  }, [ready, props.layoutResetToken]);

  /* ----------------------------------------------------------------- events */

  useEffect(() => {
    const handle = handleRef.current;
    if (!ready || !handle) return;
    const sigma = handle.sigma;

    const handleNodeClick = ({ node }: SigmaNodeEventPayload) => propsRef.current.onSelect(node);
    const handleDoubleClick = ({ node }: SigmaNodeEventPayload) => propsRef.current.onFocusNode(node);
    const handleEnter = ({ node }: SigmaNodeEventPayload) => propsRef.current.onHover(node);
    const handleLeave = () => propsRef.current.onHover(null);
    const handleStageClick = () => propsRef.current.onSelect(null);

    // Sigma normalises mouse and touch into `event`; `original` carries the
    // untouched browser event, which is what clientX/clientY come from.
    const openMenu = (node: string | null, coords: SigmaNodeEventPayload['event']) => {
      coords.preventSigmaDefault();
      const original = coords.original as MouseEvent;
      original.preventDefault();
      propsRef.current.onContextMenu(node, original.clientX, original.clientY);
    };
    const handleRightClickNode = (payload: SigmaNodeEventPayload) => openMenu(payload.node, payload.event);
    const handleRightClickStage = (payload: { event: SigmaNodeEventPayload['event'] }) =>
      openMenu(null, payload.event);

    // Sigma 3 has no drag events, so dragging is driven from the container:
    // press a node, follow the pointer, release. The layout is woken while the
    // pointer is down, so the rest of the graph rearranges around the node
    // instead of the node being pulled through a frozen picture.
    let dragging: string | null = null;
    let moved = false;
    let downAt = { x: 0, y: 0 };

    const toGraphPoint = (clientX: number, clientY: number) => {
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) return;
      return (
        handle.sigma.framedGraphToViewport({
          x: clientX - rect.left,
          y: clientY - rect.top,
        }) ?? null
      );
    };

    const applyDrag = (event: MouseEvent) => {
      if (!dragging) return;
      moved = true;
      const point = toGraphPoint(event.clientX, event.clientY);
      if (!point) return;
      handle.controller.dragTo(dragging, point.x, point.y);
      handle.sigma.refresh();
    };

    const finishDrag = (event: MouseEvent) => {
      if (!dragging) return;
      const node = dragging;
      // A press that never moved is a click, not a drag: pin it instead.
      const isClick =
        !moved && Math.hypot(event.clientX - downAt.x, event.clientY - downAt.y) < 4;
      dragging = null;
      moved = false;
      containerRef.current?.removeEventListener('mousemove', applyDrag);
      handle.controller.endDrag(node, isClick);
      if (isClick) propsRef.current.onNodePinned(node, true);
    };

    const handleDownNode = ({ node, event }: SigmaNodeEventPayload) => {
      dragging = node;
      moved = false;
      const original = event.original as MouseEvent;
      downAt = { x: original.clientX, y: original.clientY };
      handle.controller.beginDrag(node);
      containerRef.current?.addEventListener('mousemove', applyDrag);
      window.addEventListener('mouseup', finishDrag, { once: true });
    };

    const handleUpNode = ({ node }: SigmaNodeEventPayload) => {
      if (dragging === node) finishDrag({ clientX: downAt.x, clientY: downAt.y } as MouseEvent);
    };

    sigma.on('clickNode', handleNodeClick);
    sigma.on('doubleClickNode', handleDoubleClick);
    sigma.on('enterNode', handleEnter);
    sigma.on('leaveNode', handleLeave);
    sigma.on('clickStage', handleStageClick);
    sigma.on('rightClickNode', handleRightClickNode);
    sigma.on('rightClickStage', handleRightClickStage);
    sigma.on('downNode', handleDownNode);
    sigma.on('upNode', handleUpNode);

    return () => {
      sigma.off('clickNode', handleNodeClick);
      sigma.off('doubleClickNode', handleDoubleClick);
      sigma.off('enterNode', handleEnter);
      sigma.off('leaveNode', handleLeave);
      sigma.off('clickStage', handleStageClick);
      sigma.off('rightClickNode', handleRightClickNode);
      sigma.off('rightClickStage', handleRightClickStage);
      sigma.off('downNode', handleDownNode);
      sigma.off('upNode', handleUpNode);
    };
  }, [ready]);

  const style = useMemo(
    () => ({ background: props.palette.background }) as React.CSSProperties,
    [props.palette.background],
  );

  const ref = useCallback((element: HTMLDivElement | null) => {
    containerRef.current = element;
  }, []);

  return <div className="graph-canvas" style={style} ref={ref} data-testid="graph-canvas" />;
}

/* -------------------------------------------------------------------------- */
/* Reducers: every dynamic styling decision lives here, so the graph attributes */
/* stay a faithful copy of what the server sent.                               */
/* -------------------------------------------------------------------------- */

function reduceNode(
  node: string,
  data: NodeDisplay,
  props: GraphCanvasProps,
  handle: CanvasHandle | null,
): Partial<NodeDisplay> {
  const { palette, interaction } = props;

  const base =
    props.colorMode === 'community'
      ? communityColor(data.pgCommunity, palette.communityRamp)
      : nodeColorForKind(data.kind, palette);

  const selected = node === interaction.selectedId;
  const hovered = node === interaction.hoveredId;
  const onPath = interaction.pathNodeIds.size === 0 || interaction.pathNodeIds.has(node);

  // Selecting or hovering an entity keeps its direct neighbourhood lit, so the
  // structure around it stays readable while the rest of the graph recedes.
  const focusId = interaction.selectedId ?? interaction.hoveredId;
  const focusNeighbours = focusId === null ? undefined : handle?.adjacency.get(focusId);
  const nearFocus = focusId !== null && (node === focusId || focusNeighbours?.has(node) === true);

  let color = base;
  let labelColor = palette.text;

  if (interaction.pathNodeIds.size > 0) {
    color = onPath ? base : desaturate(base, 0.75);
  } else if (focusId !== null && !nearFocus) {
    color = desaturate(base, 0.62);
    labelColor = palette.textMuted;
  }
  if (hovered) color = palette.selected;

  const changed = interaction.changedIds.has(node);
  const pinned = interaction.pinnedIds.has(node);
  const unresolved = data.pgUnresolved === 1;

  // The ring is the only place these states are shown, so they never fight the
  // node's own colour for meaning.
  const ringColor = selected
    ? palette.selected
    : changed
      ? palette.changed
      : unresolved
        ? palette.unresolved
        : pinned
          ? palette.accent
          : TRANSPARENT;
  const ringWidth = selected ? 3 : changed ? 2.2 : unresolved ? 2 : pinned ? 1.6 : 0;

  // A community meta-node stands for many entities, so it gets its own, larger
  // size band rather than the ordinary node scale.
  const scale = data.kind === 'community' ? AGGREGATE_SIZE_SCALE : DEFAULT_SIZE_SCALE;
  const size = sizeForImportance(data.pgImportance, data.pgDegree, scale);

  return {
    ...data,
    color,
    size,
    labelColor,
    // A node with ring state is drawn by the ring program, which widens the
    // geometry and hollows the centre; without ring state it is a plain disc.
    type: ringWidth > 0 ? 'ringed' : 'circle',
    zIndex: selected ? 3 : hovered ? 2 : changed ? 1 : 0,
    forceLabel: selected || hovered,
    hidden: false,
    pgRingColor: ringColor,
    pgRingSize: ringWidth,
  };
}

function reduceEdge(
  edge: string,
  data: EdgeDisplay,
  props: GraphCanvasProps,
): Partial<EdgeDisplay> {
  const { palette, interaction } = props;

  const onPath = interaction.pathEdgeIds.has(edge);
  const touchingFocus =
    interaction.selectedId !== null &&
    (data.sourceId === interaction.selectedId || data.targetId === interaction.selectedId);
  const touchingHover =
    interaction.hoveredId !== null &&
    (data.sourceId === interaction.hoveredId || data.targetId === interaction.hoveredId);

  let color = edgeColor(data.edgeType, data.provenance, palette);

  if (interaction.pathEdgeIds.size > 0) {
    color = onPath ? palette.path : desaturate(color, 0.8);
  } else if (interaction.selectedId !== null && !touchingFocus) {
    color = desaturate(color, 0.6);
  } else if (interaction.hoveredId !== null && !touchingHover && !touchingFocus) {
    color = desaturate(color, 0.5);
  }

  const emphasise = onPath || touchingFocus || touchingHover;

  return {
    ...data,
    color,
    size: onPath ? 3 : edgeSizeFor(data.provenance, data.edgeType),
    label: '',
    // The dashed program is what makes semantic evidence visually distinct.
    type: data.semantic === 1 ? 'dashed' : 'line',
    zIndex: onPath ? 2 : emphasise ? 1 : 0,
    // Low-value edges stay hidden until focus makes them meaningful.
    hidden: props.hideLowValueEdges && !emphasise && interaction.selectedId !== null,
  };
}