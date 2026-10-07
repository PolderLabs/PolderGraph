import { useEffect, useMemo, useRef, useState } from 'react';
import Graph from 'graphology';
import Sigma from 'sigma';
import { createNodeBorderProgram } from '@sigma/node-border';
import type {
  EdgeDisplayData,
  MouseCoords,
  NodeDisplayData,
  SigmaEventPayload,
  SigmaNodeEventPayload,
} from 'sigma/types';
import type { EdgeProgramType } from 'sigma/rendering';

import type { FilterableEdge, FilterableNode } from './filters';
import {
  communityColor,
  edgeColor,
  edgeSizeFor,
  nodeColorForKind,
  sizeForImportance,
} from './palette';
import type { ColorMode, Palette } from './palette';
import { EdgeDashedProgram } from './dashedEdge';
import { ForceAtlas2Controller } from './layout';
import { buildAdjacency, syncGraph, TRANSPARENT } from './sync';
import type { PgEdgeAttributes, PgNodeAttributes } from './attributes';
import type { ForceSettingsState } from '../state/preferences';
import { desaturate } from '../util/color';

/** Program key for the dashed edge program used by semantic evidence. */
const SEMANTIC_PROGRAM = 'semantic';

/** Sigma instance typed with the attributes this app stores on each item. */
type PgSigma = Sigma<PgNodeAttributes, PgEdgeAttributes>;

/**
 * Sigma's display types do not declare custom attributes, but the node data it
 * hands to reducers is the graph's own attribute object. These aliases make
 * that explicit instead of casting at every use.
 */
type NodeDisplayDataWithAttrs = NodeDisplayData & PgNodeAttributes;
type EdgeDisplayDataWithAttrs = EdgeDisplayData & PgEdgeAttributes;

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
  showLabels: boolean;
  hideLowValueEdges: boolean;
  /** Bumping this refits the camera (view switch, reset). */
  fitToken: number;
  onSelect: (id: string | null) => void;
  onHover: (id: string | null) => void;
  onFocusNode: (id: string) => void;
  onContextMenu: (id: string | null, x: number, y: number) => void;
  onNodeMoved: (id: string) => void;
  onNodePinned: (id: string, pinned: boolean) => void;
  onLayoutFrame: () => void;
  onLayoutRunningChange: (running: boolean) => void;
}

interface CanvasHandle {
  sigma: PgSigma;
  graph: Graph<PgNodeAttributes, PgEdgeAttributes>;
  controller: ForceAtlas2Controller;
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
    const controller = new ForceAtlas2Controller({
      graph,
      onFrame: () => propsRef.current.onLayoutFrame(),
      onRunningChange: (running) => propsRef.current.onLayoutRunningChange(running),
    });

    const sigma: PgSigma = new Sigma<PgNodeAttributes, PgEdgeAttributes>(graph, container, {
      // Resize handling is ours; Sigma would otherwise fight the observer loop.
      allowInvalidContainer: true,
      // Edge labels are never drawn globally: at graph scale they are noise.
      renderEdgeLabels: false,
      renderLabels: true,
      labelFont: 'Inter, ui-sans-serif, system-ui, sans-serif',
      labelSize: 12,
      labelWeight: '500',
      labelColor: { attribute: 'labelColor' },
      labelDensity: 0.08,
      labelGridCellSize: 110,
      labelRenderedSizeThreshold: 6,
      minEdgeThickness: 0.5,
      autoCenter: false,
      autoRescale: false,
      stagePadding: 20,
      defaultNodeColor: '#7f8ea3',
      defaultEdgeColor: '#7f8ea3',
      nodeProgramClasses: { bordered: createNodeBorderProgram() },
      // Semantic edges get a real dashed program, not just a different colour.
      edgeProgramClasses: {
        semantic: EdgeDashedProgram as unknown as EdgeProgramType<
          PgNodeAttributes,
          PgEdgeAttributes
        >,
      },
      defaultNodeType: 'bordered',
      defaultEdgeType: 'line',
    });

    handleRef.current = { sigma, graph, controller, adjacency: new Map() };
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

  /* --------------------------------------------------------------- reducers */

  // Reducers are hot paths: they run for every visible item on every frame.
  // They are installed once and read live state through `propsRef`/`handle`.
  useEffect(() => {
    const handle = handleRef.current;
    if (!ready || !handle) return;

    handle.sigma.setSetting('nodeReducer', (node, data) =>
      reduceNode(node, data as NodeDisplayDataWithAttrs, propsRef.current, handle),
    );
    handle.sigma.setSetting('edgeReducer', (edge, data) =>
      reduceEdge(edge, data as EdgeDisplayDataWithAttrs, propsRef.current),
    );
    handle.sigma.refresh();
  }, [ready]);

  /* ------------------------------------------------------------ graph payload */

  useEffect(() => {
    const handle = handleRef.current;
    if (!ready || !handle) return;

    const topologyChanged = syncGraph(handle.graph, handle.controller, props.nodes, props.edges);
    if (topologyChanged) handle.adjacency = buildAdjacency(handle.graph);
    handle.sigma.refresh();
  }, [ready, props.nodes, props.edges]);

  /* -------------------------------------------------------- layout controls */

  useEffect(() => {
    const handle = handleRef.current;
    if (!ready || !handle) return;
    const force = props.forceSettings;
    handle.controller.setSettings({
      gravity: force.gravity,
      scalingRatio: force.scalingRatio,
      slowDown: force.slowDown,
      edgeWeightInfluence: force.edgeWeightInfluence,
      strongGravityMode: force.strongGravityMode,
      adjustSizes: force.adjustSizes,
      linLogMode: force.linLogMode,
      outboundAttractionDistribution: force.outboundAttractionDistribution,
    });
  }, [
    ready,
    props.forceSettings,
  ]);

  useEffect(() => {
    const handle = handleRef.current;
    if (!ready || !handle) return;
    if (props.layoutRunning) {
      handle.controller.start();
    } else {
      handle.controller.stop();
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
    void handle.sigma.getCamera().animatedReset({ duration: 320 });
  }, [ready, props.fitToken]);

  /* ----------------------------------------------------------------- events */

  useEffect(() => {
    const handle = handleRef.current;
    if (!ready || !handle) return;
    const sigma = handle.sigma;
    let pressedNode: string | null = null;

    const handleNodeClick = ({ node }: SigmaNodeEventPayload) => propsRef.current.onSelect(node);
    const handleDoubleClick = ({ node }: SigmaNodeEventPayload) => propsRef.current.onFocusNode(node);
    const handleEnter = ({ node }: SigmaNodeEventPayload) => propsRef.current.onHover(node);
    const handleLeave = () => propsRef.current.onHover(null);
    const handleStageClick = () => propsRef.current.onSelect(null);

    // Sigma normalises mouse and touch into `MouseCoords`; `original` carries
    // the untouched browser event, which is what clientX/clientY come from.
    const openMenu = (node: string | null, coords: MouseCoords) => {
      coords.preventSigmaDefault();
      const original = coords.original as MouseEvent;
      original.preventDefault();
      propsRef.current.onContextMenu(node, original.clientX, original.clientY);
    };
    const handleRightClickNode = (payload: SigmaNodeEventPayload) => openMenu(payload.node, payload.event);
    const handleRightClickStage = (payload: SigmaEventPayload) => openMenu(null, payload.event);

    // Sigma has no dedicated drag event, so a drag is inferred from a node
    // press followed by a release on the same node.
    const handleDownNode = ({ node }: SigmaNodeEventPayload) => {
      pressedNode = node;
      propsRef.current.onNodePinned(node, true);
    };
    const handleUpNode = ({ node }: SigmaNodeEventPayload) => {
      if (pressedNode === node) propsRef.current.onNodeMoved(node);
      pressedNode = null;
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

  return <div className="graph-canvas" style={style} ref={containerRef} data-testid="graph-canvas" />;
}

/* -------------------------------------------------------------------------- */
/* Reducers: every dynamic styling decision lives here, so the graph attributes */
/* stay a faithful copy of what the server sent.                               */
/* -------------------------------------------------------------------------- */

function reduceNode(
  node: string,
  data: NodeDisplayDataWithAttrs,
  props: GraphCanvasProps,
  handle: CanvasHandle,
): Partial<NodeDisplayDataWithAttrs> {
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
  const focusNeighbours = focusId === null ? undefined : handle.adjacency.get(focusId);
  const nearFocus =
    focusId !== null && (node === focusId || focusNeighbours?.has(node) === true);

  let color = base;
  let labelColor = palette.text;

  if (interaction.pathNodeIds.size > 0) {
    color = onPath ? base : desaturate(base, 0.75);
  } else if (focusId !== null && !nearFocus) {
    color = desaturate(base, 0.62);
    labelColor = palette.textMuted;
  }
  if (hovered) color = palette.selected;

  const changed = interaction.changedIds.has(node) || data.pgChanged === 1;
  const pinned = interaction.pinnedIds.has(node) || data.pgPinned === 1;
  const unresolved = data.pgUnresolved === 1;

  // The ring is the only place these states are shown, so they never fight the
  // node's own colour for meaning.
  const borderColor = selected
    ? palette.selected
    : changed
      ? palette.changed
      : unresolved
        ? palette.unresolved
        : pinned
          ? palette.accent
          : TRANSPARENT;
  const borderSize = selected ? 0.42 : changed ? 0.3 : unresolved ? 0.24 : pinned ? 0.2 : 0;

  return {
    ...data,
    color,
    size: sizeForImportance(data.pgImportance, data.pgDegree, { min: 2.2, max: 18 }),
    labelColor,
    borderColor,
    borderSize,
    type: 'bordered',
    zIndex: selected ? 3 : hovered ? 2 : changed ? 1 : 0,
    forceLabel: selected || hovered,
    hidden: false,
  };
}

function reduceEdge(
  edge: string,
  data: EdgeDisplayDataWithAttrs,
  props: GraphCanvasProps,
): Partial<EdgeDisplayDataWithAttrs> {
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
    size: onPath ? 2.6 : edgeSizeFor(data.provenance, data.edgeType, data.weight),
    label: '',
    forceLabel: false,
    // Semantic evidence renders through the dashed program, so it can never be
    // mistaken for a resolved structural call at a glance.
    type: data.semantic === 1 ? SEMANTIC_PROGRAM : 'line',
    zIndex: onPath ? 2 : emphasise ? 1 : 0,
    // Low-value edges stay hidden until focus makes them meaningful.
    hidden: props.hideLowValueEdges && !emphasise && interaction.selectedId !== null,
  };
}
