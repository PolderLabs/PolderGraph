import { useEffect, useMemo, useRef, useState } from 'react';
import Graph from 'graphology';
import Sigma from 'sigma';
import { layerDashed } from 'sigma/rendering';
import { numberProp } from 'sigma/primitives';
import type {
  EdgeDisplayData,
  MouseCoords,
  NodeDisplayData,
  SigmaEventPayload,
  SigmaNodeEventPayload,
} from 'sigma/types';

import type { FilterableEdge, FilterableNode } from './filters';
import {
  communityColor,
  edgeColor,
  edgeSizeFor,
  nodeColorForKind,
  sizeForImportance,
} from './palette';
import type { ColorMode, Palette } from './palette';
import { ForceAtlas2Controller } from './layout';
import { buildAdjacency, syncGraph, TRANSPARENT } from './sync';
import type { PgEdgeAttributes, PgNodeAttributes } from './attributes';
import type { ForceSettingsState } from '../state/preferences';
import { desaturate } from '../util/color';

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

    const primitives = {
      edges: {
        variables: {
          dashSize: numberProp(10000, { variable: true }),
          gapSize: numberProp(0, { variable: true }),
        },
        layers: [
          layerDashed({
            dashSize: { attribute: 'dashSize', default: 10000, mode: 'pixels' },
            gapSize: { attribute: 'gapSize', default: 0, mode: 'pixels' },
          }),
        ],
      },
    } as const;
    const sigma = new Sigma<
      PgNodeAttributes,
      PgEdgeAttributes,
      {},
      {},
      {},
      {},
      typeof primitives
    >(graph, container, {
      styles: {
        nodes: {
          labelColor: { attribute: 'labelColor' },
          backdropVisibility: 'visible',
          backdropColor: 'rgba(9, 13, 22, 0.9)',
          backdropPadding: 3,
          backdropCornerRadius: 4,
          backdropBorderColor: { attribute: 'ringColor' },
          backdropBorderWidth: { attribute: 'ringWidth' },
          backdropShadowColor: { attribute: 'glowColor' },
          backdropShadowBlur: { attribute: 'glowBlur' },
        },
        edges: {
          dashSize: { attribute: 'dashSize', defaultValue: 10000 },
          gapSize: { attribute: 'gapSize', defaultValue: 0 },
        },
      } as any,
      nodeReducer: (node, data, attrs) =>
        reduceNode(node, { ...data, ...attrs } as NodeDisplayDataWithAttrs, propsRef.current, handleRef.current),
      edgeReducer: (edge, data, attrs) =>
        reduceEdge(edge, { ...data, ...attrs } as EdgeDisplayDataWithAttrs, propsRef.current),
      settings: {
        // Resize handling is ours; Sigma would otherwise fight the observer loop.
        allowInvalidContainer: true,
        // Edge labels are never drawn globally: at graph scale they are noise.
        renderEdgeLabels: false,
        renderLabels: true,
        labelDensity: 0.08,
        labelGridCellSize: 110,
        labelRenderedSizeThreshold: 6,
        minEdgeThickness: 0.5,
        autoRescale: false,
        stagePadding: 20,
      },
    }) as PgSigma;

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
  handle: CanvasHandle | null,
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
  const focusNeighbours = focusId === null ? undefined : handle?.adjacency.get(focusId);
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
  const ringColor = selected
    ? palette.selected
    : changed
      ? palette.changed
      : unresolved
        ? palette.unresolved
        : pinned
          ? palette.accent
          : TRANSPARENT;
  const ringWidth = selected ? 1.5 : changed ? 1.1 : unresolved ? 1 : pinned ? 0.8 : 0;

  return {
    ...data,
    color,
    size: sizeForImportance(data.pgImportance, data.pgDegree, { min: 2.2, max: 18 }),
    labelColor,
    ringColor,
    ringWidth,
    glowColor: selected ? palette.selected : 'rgba(0,0,0,0)',
    glowBlur: selected ? 8 : 0,
    zIndex: selected ? 3 : hovered ? 2 : changed ? 1 : 0,
    labelVisibility: selected || hovered ? 'visible' : 'auto',
    visibility: 'visible',
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
    // Sigma's dashed primitive makes semantic evidence visually distinct.
    dashSize: data.semantic === 1 ? 7 : 10000,
    gapSize: data.semantic === 1 ? 5 : 0,
    zIndex: onPath ? 2 : emphasise ? 1 : 0,
    // Low-value edges stay hidden until focus makes them meaningful.
    visibility: props.hideLowValueEdges && !emphasise && interaction.selectedId !== null ? 'hidden' : 'visible',
  };
}
