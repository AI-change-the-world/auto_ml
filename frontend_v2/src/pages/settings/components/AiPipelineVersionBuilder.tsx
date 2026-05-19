import React from 'react';
import {
  DeleteOutlined,
  HolderOutlined,
  PartitionOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import {
  addEdge,
  Background,
  ConnectionMode,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Connection,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
  type NodeProps,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Button,
  Collapse,
  Empty,
  Form,
  Input,
  InputNumber,
  Popover,
  Select,
  Space,
  Switch,
  Tag,
  Tooltip,
  message,
} from 'antd';
import type {
  AiPipelineCapabilityField,
  AiPipelineCapabilityItem,
} from '../../../types';
import {
  applyGraphToSteps,
  createStepFromCapability,
  defaultBindingMode,
  deriveGraphFromSteps,
  deriveVersionPayloadFromSteps as deriveVersionPayloadFromStepsHelper,
  getGraphInputNodeId,
  getGraphOutputNodeId,
  getGraphStepNodeId,
  safeKey,
  type GraphInputTarget,
  type VersionBuilderFormValues,
  type VersionBuilderGraphEdgeValue,
  type VersionBuilderGraphNodeValue,
  type VersionBuilderGraphValue,
  type VersionBuilderStepValue,
} from './aiPipelineVersionBuilderHelpers';

interface AiPipelineVersionBuilderProps {
  form: ReturnType<typeof Form.useForm<VersionBuilderFormValues>>[0];
  capabilities: AiPipelineCapabilityItem[];
  capabilitiesLoading?: boolean;
}

type BuilderNodeData = {
  label: string;
  subLabel?: string;
  category?: string;
  selected?: boolean;
  contextTargets?: Array<{ key: string; label: string }>;
};

type BuilderNode = Node<BuilderNodeData, 'pipelineInput' | 'pipelineCapability' | 'pipelineOutput'>;
type BuilderEdge = Edge<Record<string, never>>;

const DRAG_CAPABILITY_KEY = 'application/x-automl-capability';
const panelBorder = '#dbe3ef';
const canvasBackground = '#f9fafb';
const primaryTarget: GraphInputTarget = 'primary';

const providerRoleOptions = [
  { label: 'multimodal', value: 'multimodal' },
  { label: 'image_edit', value: 'image_edit' },
];

const capabilityAccentMap: Record<string, { border: string; fill: string; text: string; muted: string }> = {
  text: { border: '#0f766e', fill: '#ecfdf5', text: '#047857', muted: '#d1fae5' },
  vision: { border: '#2563eb', fill: '#eff6ff', text: '#1d4ed8', muted: '#dbeafe' },
  image: { border: '#2563eb', fill: '#eff6ff', text: '#1d4ed8', muted: '#dbeafe' },
  multimodal: { border: '#2563eb', fill: '#eff6ff', text: '#1d4ed8', muted: '#dbeafe' },
  annotation: { border: '#0f766e', fill: '#ecfeff', text: '#0f766e', muted: '#ccfbf1' },
  model: { border: '#7c3aed', fill: '#f5f3ff', text: '#6d28d9', muted: '#ede9fe' },
  workflow: { border: '#475569', fill: '#f8fafc', text: '#334155', muted: '#e2e8f0' },
};

const getCapabilityAccent = (category?: string | null) => (
  capabilityAccentMap[category || ''] || {
    border: '#475569',
    fill: '#f8fafc',
    text: '#334155',
    muted: '#e2e8f0',
  }
);

const readDraggedCapability = (event: React.DragEvent) => (
  event.dataTransfer.getData(DRAG_CAPABILITY_KEY) || event.dataTransfer.getData('text/plain')
);

const getCapabilityGroupKey = (capability: AiPipelineCapabilityItem) => {
  const category = (capability.category || capability.provider_role || 'workflow').toLowerCase();
  if (category.includes('text') || category.includes('llm')) return 'text';
  if (category.includes('vision') || category.includes('image')) return 'vision';
  if (category.includes('annotation')) return 'annotation';
  if (category.includes('model')) return 'model';
  if (category.includes('multi')) return 'multimodal';
  return 'workflow';
};

const getCapabilityGroupLabel = (category: string, t: (key: string, options?: Record<string, unknown>) => string) => {
  const normalized = category.toLowerCase();
  if (normalized === 'text') return t('pipelineBuilder.groups.text');
  if (normalized === 'vision') return t('pipelineBuilder.groups.vision');
  if (normalized === 'annotation') return t('pipelineBuilder.groups.annotation');
  if (normalized === 'model') return t('pipelineBuilder.groups.model');
  if (normalized === 'multimodal') return t('pipelineBuilder.groups.multimodal');
  return t('pipelineBuilder.groups.workflow');
};

const renderFixedValueInput = (
  field: AiPipelineCapabilityField,
  t: (key: string, options?: Record<string, unknown>) => string,
) => {
  const placeholder = field.placeholder || field.description || t('pipelineBuilder.enterField', { label: field.label });
  const widget = field.widget || field.value_type || 'text';
  if (widget === 'textarea') {
    return <Input.TextArea rows={3} placeholder={placeholder} />;
  }
  if (widget === 'number' || field.value_type === 'number') {
    return <InputNumber style={{ width: '100%' }} placeholder={placeholder} />;
  }
  if (widget === 'switch' || field.value_type === 'boolean') {
    return <Switch />;
  }
  if (widget === 'select') {
    return (
      <Select
        allowClear
        options={(field.options ?? []).map((item) => ({ label: item.label, value: item.value }))}
        placeholder={placeholder}
      />
    );
  }
  if (widget === 'multi-select' || field.value_type === 'string_array') {
    return <Select mode="tags" tokenSeparators={[',']} placeholder={placeholder} />;
  }
  return <Input placeholder={placeholder} />;
};

const NodeShell: React.FC<React.PropsWithChildren<{
  data: BuilderNodeData;
  tone?: 'input' | 'output' | 'capability';
}>> = ({ data, tone = 'capability', children }) => {
  const accent = getCapabilityAccent(data.category);
  const iconColor = tone === 'input' ? '#2563eb' : tone === 'output' ? '#475569' : accent.text;
  const iconBg = tone === 'input' ? '#eff6ff' : tone === 'output' ? '#f1f5f9' : accent.muted;
  return (
    <div
      style={{
        width: 220,
        borderRadius: 6,
        border: `1px solid ${data.selected ? accent.border : panelBorder}`,
        background: '#ffffff',
        boxShadow: data.selected ? '0 0 0 2px rgba(37, 99, 235, 0.10)' : 'none',
        overflow: 'visible',
      }}
    >
      <div className="pipeline-node-drag-handle" style={{ display: 'grid', gridTemplateColumns: '28px minmax(0, 1fr)', gap: 9, alignItems: 'center', padding: '9px 11px', cursor: 'grab' }}>
        <div style={{ width: 28, height: 28, borderRadius: 5, background: iconBg, color: iconColor, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {tone === 'input' ? <PartitionOutlined /> : <SettingOutlined />}
        </div>
        <div style={{ minWidth: 0 }}>
          <div className="body-text-sm" style={{ fontWeight: 700, color: '#0f172a', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {data.label}
          </div>
          {data.subLabel ? (
            <div className="caption-text" style={{ color: '#64748b', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {data.subLabel}
            </div>
          ) : null}
        </div>
      </div>
      {children}
    </div>
  );
};

const PipelineInputNode: React.FC<NodeProps<BuilderNode>> = ({ data }) => (
  <NodeShell data={data} tone="input">
    <Handle type="source" id="input" position={Position.Right} style={{ width: 14, height: 14, background: '#2563eb', border: '2px solid #ffffff', zIndex: 20 }} />
  </NodeShell>
);

const PipelineOutputNode: React.FC<NodeProps<BuilderNode>> = ({ data }) => (
  <NodeShell data={data} tone="output">
    <Handle type="target" id="result" position={Position.Left} style={{ width: 14, height: 14, background: '#475569', border: '2px solid #ffffff', zIndex: 20 }} />
  </NodeShell>
);

const PipelineCapabilityNode: React.FC<NodeProps<BuilderNode>> = ({ data }) => (
  <NodeShell data={data}>
    <div style={{ borderTop: `1px solid ${panelBorder}`, padding: '7px 11px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span className="caption-text" style={{ color: '#64748b' }}>input</span>
      <span className="caption-text" style={{ color: '#64748b' }}>result</span>
    </div>
    <Handle type="target" id="primary" position={Position.Left} style={{ top: 48, width: 14, height: 14, background: '#2563eb', border: '2px solid #ffffff', zIndex: 20 }} />
    {(data.contextTargets ?? []).map((target, index) => (
      <Handle
        key={target.key}
        type="target"
        id={target.key}
        position={Position.Left}
        style={{ top: 82 + index * 20, width: 14, height: 14, background: '#0f766e', border: '2px solid #ffffff', zIndex: 20 }}
      />
    ))}
    <Handle type="source" id="result" position={Position.Right} style={{ width: 14, height: 14, background: '#475569', border: '2px solid #ffffff', zIndex: 20 }} />
  </NodeShell>
);

const nodeTypes = {
  pipelineInput: PipelineInputNode,
  pipelineCapability: PipelineCapabilityNode,
  pipelineOutput: PipelineOutputNode,
};

const createGraphEdge = (connection: Connection): VersionBuilderGraphEdgeValue => {
  const sourceHandle = connection.sourceHandle || (connection.source === getGraphInputNodeId() ? 'input' : 'result');
  const targetHandle = connection.targetHandle || (connection.target === getGraphOutputNodeId() ? 'result' : primaryTarget);
  return {
    id: `edge_${connection.source}_${sourceHandle}_${connection.target}_${targetHandle}_${Date.now()}`,
    source: connection.source || '',
    target: connection.target || '',
    sourceHandle,
    targetHandle,
  };
};

const toFlowEdge = (edge: VersionBuilderGraphEdgeValue): BuilderEdge => ({
  ...edge,
  type: 'smoothstep',
  markerEnd: { type: MarkerType.ArrowClosed, color: '#64748b' },
  style: { stroke: '#64748b', strokeWidth: 1.5 },
  data: {},
});

const buildGraphFromFlow = (
  nodes: BuilderNode[],
  edges: BuilderEdge[],
): VersionBuilderGraphValue => ({
  nodes: nodes.map((node) => {
    const baseNode = {
      id: node.id,
      position: node.position,
    };
    if (node.type === 'pipelineInput') {
      return {
        ...baseNode,
        kind: 'input',
      } satisfies VersionBuilderGraphNodeValue;
    }
    if (node.type === 'pipelineOutput') {
      return {
        ...baseNode,
        kind: 'output',
      } satisfies VersionBuilderGraphNodeValue;
    }
    return {
      ...baseNode,
      kind: 'capability',
      step_id: node.id.replace(/^node_/, ''),
    } satisfies VersionBuilderGraphNodeValue;
  }),
  edges: edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    sourceHandle: edge.sourceHandle ?? undefined,
    targetHandle: edge.targetHandle ?? undefined,
  })),
});

const buildFlowNodes = (
  graph: VersionBuilderGraphValue,
  steps: VersionBuilderStepValue[],
  capabilityMap: Map<string, AiPipelineCapabilityItem>,
  selectedNodeId: string,
): BuilderNode[] => graph.nodes.map((node) => {
  if (node.kind === 'input') {
    return {
      id: node.id,
      type: 'pipelineInput',
      position: node.position,
      data: { label: 'Input', subLabel: 'runtime input', selected: node.id === selectedNodeId },
      dragHandle: '.pipeline-node-drag-handle',
      deletable: false,
    };
  }
  if (node.kind === 'output') {
    return {
      id: node.id,
      type: 'pipelineOutput',
      position: node.position,
      data: { label: 'Output', subLabel: 'pipeline result', selected: node.id === selectedNodeId },
      dragHandle: '.pipeline-node-drag-handle',
      deletable: false,
    };
  }
  const step = steps.find((item) => item.id === node.step_id);
  const capability = step ? capabilityMap.get(step.capability) : undefined;
  return {
    id: node.id,
    type: 'pipelineCapability',
    position: node.position,
    dragHandle: '.pipeline-node-drag-handle',
    data: {
      label: capability?.display_name || step?.capability || 'Capability',
      subLabel: step?.name,
      category: capability?.category,
      selected: node.id === selectedNodeId,
      contextTargets: (capability?.context_mapping_targets ?? []).map((target) => ({
        key: target.key,
        label: target.label,
      })),
    },
  };
});

const buildFlowEdges = (graph: VersionBuilderGraphValue): BuilderEdge[] => graph.edges.map(toFlowEdge);

const getFlowNodeKind = (node?: BuilderNode): VersionBuilderGraphNodeValue['kind'] | undefined => {
  if (!node) return undefined;
  if (node.type === 'pipelineInput') return 'input';
  if (node.type === 'pipelineOutput') return 'output';
  return 'capability';
};

const getStepIdFromFlowNodeId = (nodeId?: string | null) => (
  nodeId?.startsWith('node_') ? nodeId.replace(/^node_/, '') : undefined
);

const getCapabilityOutputType = (
  nodeId: string,
  steps: VersionBuilderStepValue[],
  capabilityMap: Map<string, AiPipelineCapabilityItem>,
) => {
  if (nodeId === getGraphInputNodeId()) return 'image';
  const stepId = getStepIdFromFlowNodeId(nodeId);
  const step = steps.find((item) => item.id === stepId);
  return step ? capabilityMap.get(step.capability)?.output_type || undefined : undefined;
};

const getCapabilityAcceptedTypes = (
  nodeId: string,
  targetHandle: string | null | undefined,
  steps: VersionBuilderStepValue[],
  capabilityMap: Map<string, AiPipelineCapabilityItem>,
) => {
  if (nodeId === getGraphOutputNodeId()) return undefined;
  const stepId = getStepIdFromFlowNodeId(nodeId);
  const step = steps.find((item) => item.id === stepId);
  const capability = step ? capabilityMap.get(step.capability) : undefined;
  if (!capability) return undefined;
  if (!targetHandle || targetHandle === primaryTarget) return capability.input_types;
  return capability.context_mapping_targets.find((target) => target.key === targetHandle)?.accepted_output_types;
};

const isTypeCompatible = (sourceType?: string, acceptedTypes?: string[]) => (
  Boolean(sourceType && acceptedTypes && acceptedTypes.length > 0 && acceptedTypes.includes(sourceType))
);

const buildUniqueStep = (
  capability: AiPipelineCapabilityItem,
  currentSteps: VersionBuilderStepValue[],
  position: { x: number; y: number },
) => {
  const baseName = safeKey(capability.name) || 'step';
  const usedNames = new Set(currentSteps.map((item) => item.name));
  const usedIds = new Set(currentSteps.map((item) => item.id));
  const usedOutputKeys = new Set(currentSteps.map((item) => item.output_key).filter(Boolean));
  let nextName = baseName;
  let suffix = 2;
  while (usedNames.has(nextName)) {
    nextName = `${baseName}_${suffix}`;
    suffix += 1;
  }
  const idBase = `step_${nextName}`;
  let nextId = idBase;
  while (usedIds.has(nextId)) {
    nextId = `step_${nextName}_${suffix}`;
    suffix += 1;
  }
  let outputKey = capability.recommended_output_key || nextName;
  if (usedOutputKeys.has(outputKey)) {
    outputKey = nextName;
  }
  return createStepFromCapability(capability, {
    id: nextId,
    name: nextName,
    output_key: outputKey,
    position,
  });
};

export const deriveVersionPayloadFromSteps = (
  steps: VersionBuilderStepValue[],
  capabilities: AiPipelineCapabilityItem[],
  graph?: VersionBuilderGraphValue,
) => deriveVersionPayloadFromStepsHelper(steps, capabilities, graph);

const AiPipelineVersionBuilderInner: React.FC<AiPipelineVersionBuilderProps> = ({
  form,
  capabilities,
  capabilitiesLoading,
}) => {
  const { t } = useTranslation('settings');
  const reactFlow = useReactFlow<BuilderNode, BuilderEdge>();
  const sceneType = Form.useWatch('scene_type', form) as string | undefined;
  const steps = (Form.useWatch('steps', form) as VersionBuilderStepValue[] | undefined) ?? [];
  const watchedGraph = Form.useWatch('graph', form) as VersionBuilderGraphValue | undefined;
  const fallbackGraph = React.useMemo(() => deriveGraphFromSteps(steps), [steps]);
  const graph = watchedGraph ?? fallbackGraph;
  const [selectedNodeId, setSelectedNodeId] = React.useState<string>(getGraphInputNodeId());
  const [flowNodes, setFlowNodes, onNodesChange] = useNodesState<BuilderNode>([]);
  const [flowEdges, setFlowEdges, onEdgesChange] = useEdgesState<BuilderEdge>([]);
  const draggingCapabilityNameRef = React.useRef<string | null>(null);
  const lastFlowSyncSignatureRef = React.useRef('');
  const lastDragOverLogRef = React.useRef(0);
  const lastDropAtRef = React.useRef(0);

  React.useEffect(() => {
    if (!watchedGraph) {
      form.setFieldValue('graph', fallbackGraph);
    }
  }, [fallbackGraph, form, watchedGraph]);

  React.useEffect(() => {
    if (!selectedNodeId || flowNodes.length === 0 || flowNodes.some((node) => node.id === selectedNodeId)) {
      return;
    }
    setSelectedNodeId(getGraphInputNodeId());
  }, [flowNodes, selectedNodeId]);

  const filteredCapabilities = React.useMemo(() => (
    capabilities.filter((item) => (
      item.scene_types.length === 0
      || !sceneType
      || item.scene_types.includes(sceneType)
    ))
  ), [capabilities, sceneType]);

  const capabilityGroups = React.useMemo(() => {
    const groups = new Map<string, AiPipelineCapabilityItem[]>();
    filteredCapabilities.forEach((capability) => {
      const groupKey = getCapabilityGroupKey(capability);
      groups.set(groupKey, [...(groups.get(groupKey) ?? []), capability]);
    });
    return Array.from(groups.entries()).sort(([leftKey], [rightKey]) => leftKey.localeCompare(rightKey));
  }, [filteredCapabilities]);

  const capabilityMap = React.useMemo(() => (
    new Map(capabilities.map((item) => [item.name, item]))
  ), [capabilities]);

  const commitGraph = React.useCallback((nextGraph: VersionBuilderGraphValue, nextSteps = steps) => {
    form.setFieldsValue({
      graph: nextGraph,
      steps: applyGraphToSteps(nextSteps, nextGraph),
    });
  }, [form, steps]);

  const selectNode = React.useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId);
    setFlowNodes((currentNodes) => currentNodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        selected: node.id === nodeId,
      },
    })));
  }, [setFlowNodes]);

  const selectedFlowNode = flowNodes.find((node) => node.id === selectedNodeId);
  const selectedNodeKind = getFlowNodeKind(selectedFlowNode);
  const selectedGraphNode = selectedFlowNode
    ? graph.nodes.find((node) => node.id === selectedNodeId)
    : undefined;
  const selectedStepId = selectedNodeKind === 'capability'
    ? getStepIdFromFlowNodeId(selectedNodeId)
    : undefined;
  const selectedStepIndex = steps.findIndex((step) => step.id === selectedStepId);
  const selectedStep = selectedStepIndex >= 0 ? steps[selectedStepIndex] : undefined;
  const selectedCapability = selectedStep ? capabilityMap.get(selectedStep.capability) : undefined;
  const outputInputEdge = graph.edges.find((edge) => edge.target === getGraphOutputNodeId());
  const outputSourceFlowNode = outputInputEdge
    ? flowNodes.find((node) => node.id === outputInputEdge.source)
    : undefined;
  const outputSourceStep = getFlowNodeKind(outputSourceFlowNode) === 'capability'
    ? steps.find((step) => step.id === getStepIdFromFlowNodeId(outputSourceFlowNode?.id))
    : undefined;
  const flowSyncSignature = React.useMemo(() => JSON.stringify({
    nodes: graph.nodes,
    edges: graph.edges,
    steps: steps.map((step) => ({
      id: step.id,
      name: step.name,
      capability: step.capability,
    })),
    capabilities: capabilities.map((capability) => ({
      name: capability.name,
      display_name: capability.display_name,
      category: capability.category,
    })),
  }), [capabilities, graph.edges, graph.nodes, steps]);

  React.useEffect(() => {
    if (lastFlowSyncSignatureRef.current === flowSyncSignature) {
      return;
    }
    lastFlowSyncSignatureRef.current = flowSyncSignature;
    setFlowNodes(buildFlowNodes(graph, steps, capabilityMap, selectedNodeId));
    setFlowEdges(buildFlowEdges(graph));
  }, [capabilityMap, flowSyncSignature, graph, selectedNodeId, setFlowEdges, setFlowNodes, steps]);

  const isValidConnection = React.useCallback((connection: BuilderEdge | Connection) => {
    if (!connection.source || !connection.target || connection.source === connection.target) {
      console.debug('[AiPipelineBuilder] invalid connection: missing or same node', connection);
      return false;
    }
    const sourceKind = getFlowNodeKind(flowNodes.find((node) => node.id === connection.source));
    const targetKind = getFlowNodeKind(flowNodes.find((node) => node.id === connection.target));
    if (!sourceKind || !targetKind || sourceKind === 'output' || targetKind === 'input') {
      console.debug('[AiPipelineBuilder] invalid connection: unsupported endpoint', {
        connection,
        sourceKind,
        targetKind,
      });
      return false;
    }
    if (targetKind === 'output' && sourceKind !== 'capability') {
      console.debug('[AiPipelineBuilder] invalid connection: output requires capability source', connection);
      return false;
    }
    if (targetKind === 'capability' && sourceKind === 'input' && connection.targetHandle && connection.targetHandle !== primaryTarget) {
      console.debug('[AiPipelineBuilder] invalid connection: input can only connect to primary', connection);
      return false;
    }
    const sourceType = getCapabilityOutputType(connection.source, steps, capabilityMap);
    const acceptedTypes = getCapabilityAcceptedTypes(connection.target, connection.targetHandle, steps, capabilityMap);
    if (!isTypeCompatible(sourceType, acceptedTypes)) {
      console.debug('[AiPipelineBuilder] invalid connection: type mismatch', {
        connection,
        sourceType,
        acceptedTypes,
      });
      message.warning(t('pipelineBuilder.incompatibleConnection'));
      return false;
    }
    return true;
  }, [capabilityMap, flowNodes, steps, t]);

  const handleConnect = React.useCallback((connection: Connection) => {
    console.debug('[AiPipelineBuilder] connect', connection);
    if (!isValidConnection(connection)) {
      message.warning(t('pipelineBuilder.unsupportedConnection'));
      return;
    }
    const nextEdge = createGraphEdge(connection);
    const nextFlowEdges = addEdge(toFlowEdge(nextEdge), flowEdges)
      .filter((edge) => !(edge.target === nextEdge.target && edge.targetHandle === nextEdge.targetHandle && edge.id !== nextEdge.id))
      .filter((edge) => !(nextEdge.target === getGraphOutputNodeId() && edge.target === getGraphOutputNodeId() && edge.id !== nextEdge.id));
    const nextGraph = buildGraphFromFlow(flowNodes, nextFlowEdges);
    setFlowEdges(nextFlowEdges);
    commitGraph(nextGraph);
  }, [commitGraph, flowEdges, flowNodes, isValidConnection, setFlowEdges, t]);

  const handleFlowNodesChange = React.useCallback((changes: NodeChange<BuilderNode>[]) => {
    onNodesChange(changes);
    const removedNodeIds = changes.filter((change) => change.type === 'remove').map((change) => change.id);
    if (removedNodeIds.length === 0) {
      return;
    }
    const removedStepIds = graph.nodes
      .filter((node) => removedNodeIds.includes(node.id) && node.kind === 'capability' && node.step_id)
      .map((node) => node.step_id!);
    const nextNodes = graph.nodes
      .filter((node) => !removedNodeIds.includes(node.id) || node.kind !== 'capability');
    const nextEdges = graph.edges.filter((edge) => !removedNodeIds.includes(edge.source) && !removedNodeIds.includes(edge.target));
    const nextSteps = removedStepIds.length > 0
      ? steps.filter((step) => !removedStepIds.includes(step.id))
      : steps;
    if (removedNodeIds.includes(selectedNodeId)) {
      setSelectedNodeId(getGraphInputNodeId());
    }
    commitGraph({ nodes: nextNodes, edges: nextEdges }, nextSteps);
  }, [commitGraph, graph.edges, graph.nodes, onNodesChange, selectedNodeId, steps]);

  const handleNodeDragStop = React.useCallback((_: React.MouseEvent, node: BuilderNode) => {
    console.debug('[AiPipelineBuilder] node drag stop', node.id, node.position);
    const nextGraph = {
      ...graph,
      nodes: graph.nodes.map((item) => (
        item.id === node.id ? { ...item, position: node.position } : item
      )),
    };
    commitGraph(nextGraph);
  }, [commitGraph, graph]);

  const handleFlowEdgesChange = React.useCallback((changes: EdgeChange<BuilderEdge>[]) => {
    onEdgesChange(changes);
    const removedEdgeIds = changes.filter((change) => change.type === 'remove').map((change) => change.id);
    if (removedEdgeIds.length === 0) {
      return;
    }
    commitGraph({
      ...graph,
      edges: graph.edges.filter((edge) => !removedEdgeIds.includes(edge.id)),
    });
  }, [commitGraph, graph, onEdgesChange]);

  const addCapabilityNodeAtPosition = React.useCallback((
    capability: AiPipelineCapabilityItem,
    position: { x: number; y: number },
  ) => {
    const nextStep = buildUniqueStep(capability, steps, position);
    const nextFlowNode: BuilderNode = {
      id: getGraphStepNodeId(nextStep.id),
      type: 'pipelineCapability',
      position,
      dragHandle: '.pipeline-node-drag-handle',
      data: {
        label: capability.display_name || capability.name,
        subLabel: nextStep.name,
        category: capability.category,
        selected: true,
        contextTargets: (capability.context_mapping_targets ?? []).map((target) => ({
          key: target.key,
          label: target.label,
        })),
      },
    };
    const nextFlowNodes = [
      ...flowNodes.map((node) => ({
        ...node,
        data: { ...node.data, selected: false },
      })),
      nextFlowNode,
    ];
    const nextGraph = buildGraphFromFlow(nextFlowNodes, flowEdges);
    const nextSteps = [...steps, nextStep];
    setSelectedNodeId(nextFlowNode.id);
    setFlowNodes(nextFlowNodes);
    commitGraph(nextGraph, nextSteps);
  }, [commitGraph, flowEdges, flowNodes, setFlowNodes, steps]);

  const handleDrop = React.useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const now = Date.now();
    if (now - lastDropAtRef.current < 100) {
      return;
    }
    lastDropAtRef.current = now;
    const capabilityName = readDraggedCapability(event) || draggingCapabilityNameRef.current;
    console.debug('[AiPipelineBuilder] drop', {
      capabilityName,
      dataTypes: Array.from(event.dataTransfer.types),
      dataTransferText: event.dataTransfer.getData('text/plain'),
      clientX: event.clientX,
      clientY: event.clientY,
      viewportInitialized: reactFlow.viewportInitialized,
    });
    const capability = filteredCapabilities.find((item) => item.name === capabilityName);
    if (!capability) {
      console.debug('[AiPipelineBuilder] drop ignored: capability not found', capabilityName);
      return;
    }
    const position = reactFlow.screenToFlowPosition({ x: event.clientX, y: event.clientY });
    addCapabilityNodeAtPosition(capability, position);
    draggingCapabilityNameRef.current = null;
  }, [addCapabilityNodeAtPosition, filteredCapabilities, reactFlow]);

  const handleCapabilityDragStart = (event: React.DragEvent<HTMLElement>, capabilityName: string) => {
    console.debug('[AiPipelineBuilder] drag start', capabilityName);
    draggingCapabilityNameRef.current = capabilityName;
    event.dataTransfer.setData(DRAG_CAPABILITY_KEY, capabilityName);
    event.dataTransfer.setData('text/plain', capabilityName);
    event.dataTransfer.effectAllowed = 'copy';
  };

  const handleDeleteSelectedStep = () => {
    if (!selectedStep) return;
    const nodeId = getGraphStepNodeId(selectedStep.id);
    const nextSteps = steps.filter((step) => step.id !== selectedStep.id);
    const nextGraph = {
      nodes: graph.nodes.filter((node) => node.id !== nodeId),
      edges: graph.edges.filter((edge) => edge.source !== nodeId && edge.target !== nodeId),
    };
    setSelectedNodeId(getGraphInputNodeId());
    setFlowNodes(buildFlowNodes(nextGraph, nextSteps, capabilityMap, getGraphInputNodeId()));
    setFlowEdges(buildFlowEdges(nextGraph));
    commitGraph(nextGraph, nextSteps);
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: selectedGraphNode ? '260px minmax(0, 1fr) 340px' : '260px minmax(0, 1fr)', height: 'calc(100vh - 124px)', minHeight: 560, background: canvasBackground }}>
      <div style={{ borderRight: `1px solid ${panelBorder}`, background: '#ffffff', minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '12px 14px', borderBottom: `1px solid ${panelBorder}` }}>
          <div className="card-title">{t('pipelineBuilder.nodeLibrary')}</div>
          <div className="caption-text" style={{ color: '#64748b', marginTop: 4 }}>
            {t('pipelineBuilder.availableNodes', { count: filteredCapabilities.length })}
          </div>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: 8 }}>
          {filteredCapabilities.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={capabilitiesLoading ? t('pipelineBuilder.loadingNodes') : t('pipelineBuilder.noNodes')}
            />
          ) : (
            <Collapse
              ghost
              size="small"
              defaultActiveKey={capabilityGroups.map(([groupKey]) => groupKey)}
              items={capabilityGroups.map(([groupKey, groupCapabilities]) => ({
                key: groupKey,
                label: (
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                    <span>{getCapabilityGroupLabel(groupKey, t)}</span>
                    <span className="caption-text" style={{ color: '#94a3b8' }}>{groupCapabilities.length}</span>
                  </div>
                ),
                children: (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {groupCapabilities.map((capability) => {
                      const accent = getCapabilityAccent(capability.category);
                      const detail = (
                        <div style={{ maxWidth: 280 }}>
                          <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 700 }}>{capability.display_name}</div>
                          <div className="caption-text" style={{ color: '#64748b', marginTop: 4 }}>{capability.name}</div>
                          {capability.description ? (
                            <div className="caption-text" style={{ color: '#475569', marginTop: 8, lineHeight: 1.6 }}>
                              {capability.description}
                            </div>
                          ) : null}
                          <div style={{ marginTop: 10, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            <Tag bordered={false}>{getCapabilityGroupLabel(capability.category, t)}</Tag>
                            {capability.requires_provider ? <Tag bordered={false}>{t('pipelineBuilder.requiresProvider')}</Tag> : null}
                          </div>
                        </div>
                      );
                      return (
                        <Popover key={capability.name} placement="right" content={detail} mouseEnterDelay={0.25}>
                          <div
                            role="button"
                            tabIndex={0}
                            draggable
                            onDragStart={(event) => handleCapabilityDragStart(event, capability.name)}
                            onDragEnd={() => {
                              console.debug('[AiPipelineBuilder] drag end', capability.name);
                              draggingCapabilityNameRef.current = null;
                            }}
                            style={{
                              display: 'grid',
                              gridTemplateColumns: '22px minmax(0, 1fr)',
                              gap: 8,
                              alignItems: 'center',
                              borderRadius: 4,
                              padding: '7px 8px',
                              color: '#0f172a',
                              cursor: 'grab',
                              userSelect: 'none',
                            }}
                          >
                            <span style={{ width: 18, height: 18, borderRadius: 4, background: accent.muted, color: accent.text, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
                              <HolderOutlined style={{ fontSize: 12 }} />
                            </span>
                            <span style={{ minWidth: 0 }}>
                              <span className="body-text-sm" style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {capability.display_name}
                              </span>
                              <span className="caption-text" style={{ display: 'block', color: '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {capability.name}
                              </span>
                            </span>
                          </div>
                        </Popover>
                      );
                    })}
                  </div>
                ),
              }))}
            />
          )}
        </div>
      </div>

      <div
        style={{ minWidth: 0, minHeight: 0, height: '100%' }}
        onDragEnter={(event) => {
          event.preventDefault();
          event.dataTransfer.dropEffect = 'copy';
        }}
        onDragOver={(event) => {
          event.preventDefault();
          event.dataTransfer.dropEffect = 'copy';
        }}
        onDrop={handleDrop}
      >
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          nodeTypes={nodeTypes}
          onConnect={handleConnect}
          onNodesChange={handleFlowNodesChange}
          onNodeDragStop={handleNodeDragStop}
          onEdgesChange={handleFlowEdgesChange}
          onDragEnter={(event) => {
            event.preventDefault();
            event.dataTransfer.dropEffect = 'copy';
          }}
          onDragOver={(event) => {
            event.preventDefault();
            event.dataTransfer.dropEffect = 'copy';
            const now = Date.now();
            if (now - lastDragOverLogRef.current > 800) {
              lastDragOverLogRef.current = now;
              console.debug('[AiPipelineBuilder] drag over', {
                draggingCapabilityName: draggingCapabilityNameRef.current,
                dataTypes: Array.from(event.dataTransfer.types),
                clientX: event.clientX,
                clientY: event.clientY,
              });
            }
          }}
          onDrop={handleDrop}
          onNodeClick={(_, node) => {
            selectNode(node.id);
          }}
          onPaneClick={() => selectNode('')}
          isValidConnection={isValidConnection}
          onConnectStart={(_, params) => {
            console.debug('[AiPipelineBuilder] connect start', params);
          }}
          onConnectEnd={(event) => {
            console.debug('[AiPipelineBuilder] connect end', event.type);
          }}
          connectionMode={ConnectionMode.Loose}
          nodesConnectable
          elementsSelectable
          connectOnClick={false}
          deleteKeyCode={['Backspace', 'Delete']}
          defaultViewport={{ x: 80, y: 40, zoom: 0.85 }}
          defaultEdgeOptions={{ type: 'smoothstep' }}
        >
          <Background gap={18} size={1} color="#dbe4f0" />
          <Controls position="bottom-right" />
        </ReactFlow>
      </div>

      {selectedGraphNode ? (
      <div style={{ borderLeft: `1px solid ${panelBorder}`, background: '#ffffff', minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '14px 16px', borderBottom: `1px solid ${panelBorder}` }}>
          <div className="card-title">{t('pipelineBuilder.nodeInspector')}</div>
          <div className="caption-text" style={{ color: '#64748b', marginTop: 4 }}>
            {selectedStep?.name || (selectedNodeKind === 'input' ? t('pipelineBuilder.input') : selectedNodeKind === 'output' ? t('pipelineBuilder.output') : t('pipelineBuilder.selectNode'))}
          </div>
        </div>
        {selectedNodeKind === 'input' ? (
          <div style={{ padding: 18 }}>
            <div style={{ border: `1px solid ${panelBorder}`, borderRadius: 6, padding: 14, background: '#f8fafc' }}>
              <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 700 }}>{t('pipelineBuilder.inputNode')}</div>
              <div className="caption-text" style={{ color: '#64748b', marginTop: 8, lineHeight: 1.6 }}>
                {t('pipelineBuilder.inputNodeDescription')}
              </div>
            </div>
          </div>
        ) : selectedNodeKind === 'output' ? (
          <div style={{ padding: 18 }}>
            <div style={{ border: `1px solid ${panelBorder}`, borderRadius: 6, padding: 14, background: '#f8fafc', marginBottom: 12 }}>
              <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 700 }}>{t('pipelineBuilder.outputNode')}</div>
              <div className="caption-text" style={{ color: '#64748b', marginTop: 8, lineHeight: 1.6 }}>
                {t('pipelineBuilder.outputNodeDescription')}
              </div>
            </div>
            <div style={{ border: `1px solid ${panelBorder}`, borderRadius: 6, padding: 14 }}>
              <div className="caption-text" style={{ color: '#64748b', marginBottom: 8 }}>{t('pipelineBuilder.currentSource')}</div>
              <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 600 }}>
                {outputSourceStep ? `${outputSourceStep.name} -> ${outputSourceStep.output_key || outputSourceStep.name}` : t('pipelineBuilder.notConnected')}
              </div>
            </div>
          </div>
        ) : !selectedStep || !selectedCapability ? (
          <div style={{ padding: 18 }}>
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={t('pipelineBuilder.selectNodeToConfigure')} />
          </div>
        ) : (
          <div style={{ flex: 1, overflow: 'auto', padding: 18 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start', marginBottom: 16 }}>
              <div style={{ minWidth: 0 }}>
                <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 700 }}>{selectedCapability.display_name}</div>
                <div className="caption-text" style={{ color: '#64748b', marginTop: 4 }}>{selectedCapability.name}</div>
              </div>
              <Tooltip title={t('pipelineBuilder.deleteNode')}>
                <Button size="small" danger icon={<DeleteOutlined />} onClick={handleDeleteSelectedStep} />
              </Tooltip>
            </div>

            <Form.Item label={t('pipelineBuilder.nodeKey')} name={['steps', selectedStepIndex, 'name']} rules={[{ required: true, message: t('pipelineBuilder.nodeKeyRequired') }]}>
              <Input placeholder={t('pipelineBuilder.nodeKeyPlaceholder')} />
            </Form.Item>
            <Form.Item label={t('pipelineBuilder.capability')} name={['steps', selectedStepIndex, 'capability']} rules={[{ required: true, message: t('pipelineBuilder.capabilityRequired') }]}>
              <Select
                options={filteredCapabilities.map((item) => ({
                  label: `${item.display_name} · ${item.name}`,
                  value: item.name,
                }))}
              />
            </Form.Item>
            <Form.Item label={t('pipelineBuilder.outputKey')} name={['steps', selectedStepIndex, 'output_key']}>
              <Input placeholder={t('pipelineBuilder.outputKeyPlaceholder')} />
            </Form.Item>
            <Form.Item label={t('pipelineBuilder.providerName')} name={['steps', selectedStepIndex, 'provider']}>
              <Input placeholder={t('pipelineBuilder.providerNamePlaceholder')} />
            </Form.Item>
            <Form.Item label={t('pipelineBuilder.providerRole')} name={['steps', selectedStepIndex, 'provider_role']}>
              <Select allowClear options={providerRoleOptions} placeholder={t('pipelineBuilder.providerRolePlaceholder')} />
            </Form.Item>

            {selectedStep.input_bindings?.length ? (
              <div style={{ marginBottom: 18 }}>
                <div className="card-title" style={{ marginBottom: 8 }}>{t('pipelineBuilder.inputEdges')}</div>
                <Space size={[6, 6]} wrap>
                  {selectedStep.input_bindings.map((binding) => (
                    <Tag key={`${binding.sourceNodeId}-${binding.target}`} bordered={false}>
                      {binding.target}: {binding.sourceNodeId === getGraphInputNodeId() ? 'Input' : binding.sourceNodeId}
                    </Tag>
                  ))}
                </Space>
              </div>
            ) : null}

            {selectedCapability.parameter_fields.length > 0 ? (
              <div>
                <div className="card-title" style={{ marginBottom: 12 }}>{t('pipelineBuilder.parameterBindings')}</div>
                {selectedCapability.parameter_fields.map((field) => {
                  const bindingPath = ['steps', selectedStepIndex, 'field_bindings', field.key] as (string | number)[];
                  const bindingMode = selectedStep.field_bindings?.[field.key]?.mode || defaultBindingMode(field);
                  const modeOptions = field.binding_kind === 'resource'
                    ? [{ label: t('pipelineBuilder.resourceSlot'), value: 'resource_slot' }]
                    : [
                      { label: t('pipelineBuilder.fixedValue'), value: 'fixed' },
                      { label: t('pipelineBuilder.runtimeInput'), value: 'runtime_input' },
                    ];
                  return (
                    <div key={field.key} style={{ border: `1px solid ${panelBorder}`, borderRadius: 6, padding: 12, marginBottom: 12 }}>
                      <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 600, marginBottom: 10 }}>{field.label}</div>
                      <Form.Item label={t('pipelineBuilder.bindingMode')} name={[...bindingPath, 'mode']}>
                        <Select options={modeOptions} />
                      </Form.Item>
                      {bindingMode === 'fixed' ? (
                        <Form.Item
                          label={t('pipelineBuilder.fixedValue')}
                          name={[...bindingPath, 'value']}
                          valuePropName={(field.widget === 'switch' || field.value_type === 'boolean') ? 'checked' : 'value'}
                        >
                          {renderFixedValueInput(field, t)}
                        </Form.Item>
                      ) : null}
                      {bindingMode === 'runtime_input' ? (
                        <>
                          <Form.Item label={t('pipelineBuilder.runtimeInputKey')} name={[...bindingPath, 'runtime_input_key']}>
                            <Input placeholder={safeKey(`${selectedStep.name}_${field.key}`)} />
                          </Form.Item>
                          <Form.Item label={t('pipelineBuilder.runtimeInputLabel')} name={[...bindingPath, 'runtime_input_label']}>
                            <Input placeholder={field.label} />
                          </Form.Item>
                        </>
                      ) : null}
                      {bindingMode === 'resource_slot' ? (
                        <>
                          <Form.Item label={t('pipelineBuilder.resourceSlotKey')} name={[...bindingPath, 'resource_slot_key']}>
                            <Input placeholder={safeKey(`${selectedStep.name}_${field.key}`)} />
                          </Form.Item>
                          <Form.Item label={t('pipelineBuilder.resourceSlotLabel')} name={[...bindingPath, 'resource_slot_label']}>
                            <Input placeholder={field.label} />
                          </Form.Item>
                        </>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            ) : null}
          </div>
        )}
      </div>
      ) : null}
    </div>
  );
};

const AiPipelineVersionBuilder: React.FC<AiPipelineVersionBuilderProps> = (props) => (
  <ReactFlowProvider>
    <AiPipelineVersionBuilderInner {...props} />
  </ReactFlowProvider>
);

export default AiPipelineVersionBuilder;
