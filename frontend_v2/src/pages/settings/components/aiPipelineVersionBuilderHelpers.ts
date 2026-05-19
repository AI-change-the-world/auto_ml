import type {
  AiPipelineCapabilityField,
  AiPipelineCapabilityItem,
  AiPipelineFieldSchema,
  AiPipelineResourceSlotSchema,
} from '../../../types';

export type StepFieldBindingMode = 'fixed' | 'runtime_input' | 'resource_slot';

type StepFieldBindingValue = string | number | boolean | string[] | null;

export type GraphNodeKind = 'input' | 'capability' | 'output';
export type GraphInputTarget = string;

export interface StepFieldBinding {
  mode?: StepFieldBindingMode;
  value?: StepFieldBindingValue;
  runtime_input_key?: string;
  runtime_input_label?: string;
  resource_slot_key?: string;
  resource_slot_label?: string;
}

export interface GraphNodePosition {
  x: number;
  y: number;
}

export interface CapabilityNodeInputBinding {
  sourceNodeId?: string;
  sourceHandle?: string;
  target: GraphInputTarget;
}

export interface VersionBuilderStepValue {
  id: string;
  name: string;
  capability: string;
  input_key?: string;
  output_key?: string;
  provider?: string;
  provider_role?: string;
  context_mapping?: Record<string, string>;
  field_bindings?: Record<string, StepFieldBinding>;
  position?: GraphNodePosition;
  input_bindings?: CapabilityNodeInputBinding[];
}

export interface VersionBuilderGraphNodeValue {
  id: string;
  kind: GraphNodeKind;
  position: GraphNodePosition;
  step_id?: string;
  source_step_id?: string;
  output_handle?: string;
}

export interface VersionBuilderGraphEdgeValue {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface VersionBuilderGraphValue {
  nodes: VersionBuilderGraphNodeValue[];
  edges: VersionBuilderGraphEdgeValue[];
}

export interface VersionBuilderFormValues {
  change_note?: string;
  scene_type?: string;
  steps?: VersionBuilderStepValue[];
  graph?: VersionBuilderGraphValue;
}

export interface DerivedVersionPayload {
  runtimeInputs: AiPipelineFieldSchema[];
  resourceSlots: Array<AiPipelineResourceSlotSchema & Record<string, unknown>>;
  steps: Array<Record<string, unknown>>;
}

export interface VersionBuilderValidationIssue {
  stepId?: string;
  message: string;
}

const GRAPH_INPUT_NODE_ID = 'graph_input';
const GRAPH_OUTPUT_NODE_ID = 'graph_output';
const DEFAULT_NODE_X = 220;
const DEFAULT_NODE_Y_GAP = 180;
const DEFAULT_OUTPUT_HANDLE = 'result';
const DEFAULT_PRIMARY_TARGET: GraphInputTarget = 'primary';

const normalizeStepFieldBindingValue = (value: unknown): StepFieldBindingValue | undefined => {
  if (value == null) return null;
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return value;
  }
  if (Array.isArray(value) && value.every((item) => typeof item === 'string')) {
    return value;
  }
  return undefined;
};

export const safeKey = (value: string) => value.trim().replace(/[^a-zA-Z0-9_]+/g, '_').replace(/^_+|_+$/g, '');

const inferRuntimeValueType = (field: AiPipelineCapabilityField) => {
  if (field.value_type) return field.value_type;
  if (field.widget === 'number') return 'number';
  if (field.widget === 'switch') return 'boolean';
  if (field.widget === 'multi-select') return 'string_array';
  return 'string';
};

export const defaultBindingMode = (field: AiPipelineCapabilityField): StepFieldBindingMode => (
  field.binding_kind === 'resource' ? 'resource_slot' : 'fixed'
);

const buildDefaultFieldBindings = (capability: AiPipelineCapabilityItem, baseKey: string) => (
  Object.fromEntries(
    (capability.parameter_fields ?? []).map((field) => {
      const mode = defaultBindingMode(field);
      const fallbackLabel = field.label || field.key;
      return [
        field.key,
        {
          mode,
          value: mode === 'fixed' ? normalizeStepFieldBindingValue(field.default_value) : undefined,
          runtime_input_key: mode === 'runtime_input' ? safeKey(`${baseKey}_${field.key}`) : undefined,
          runtime_input_label: mode === 'runtime_input' ? fallbackLabel : undefined,
          resource_slot_key: mode === 'resource_slot' ? safeKey(`${baseKey}_${field.key}`) : undefined,
          resource_slot_label: mode === 'resource_slot' ? fallbackLabel : undefined,
        } satisfies StepFieldBinding,
      ];
    }),
  )
);

export const createStepFromCapability = (
  capability: AiPipelineCapabilityItem,
  options?: {
    id?: string;
    name?: string;
    output_key?: string;
    position?: GraphNodePosition;
    input_bindings?: CapabilityNodeInputBinding[];
  },
): VersionBuilderStepValue => {
  const baseKey = safeKey(options?.name || capability.name) || 'step';
  const id = options?.id || `step_${baseKey}`;
  return {
    id,
    name: options?.name || baseKey,
    capability: capability.name,
    input_key: 'input',
    output_key: options?.output_key || capability.recommended_output_key || baseKey,
    provider: undefined,
    provider_role: capability.provider_role || undefined,
    context_mapping: {},
    field_bindings: buildDefaultFieldBindings(capability, baseKey),
    position: options?.position,
    input_bindings: options?.input_bindings ?? [],
  };
};

const normalizeObject = (value: unknown): Record<string, unknown> => (
  typeof value === 'object' && value !== null && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {}
);

const findRuntimeInputSchema = (
  runtimeInputs: AiPipelineFieldSchema[],
  key: string,
) => runtimeInputs.find((item) => item.key === key);

const findResourceSlotSchema = (
  resourceSlots: Array<AiPipelineResourceSlotSchema & Record<string, unknown>>,
  key: string,
) => resourceSlots.find((item) => item.key === key);

const getStepNodeId = (stepId: string) => `node_${stepId}`;

const getStepResultHandle = (_step: VersionBuilderStepValue) => DEFAULT_OUTPUT_HANDLE;

const getDefaultNodePosition = (index: number): GraphNodePosition => ({
  x: DEFAULT_NODE_X + (index % 2) * 120,
  y: 120 + index * DEFAULT_NODE_Y_GAP,
});

const getOutputNodePosition = (steps: VersionBuilderStepValue[]): GraphNodePosition => ({
  x: DEFAULT_NODE_X + 320,
  y: 140 + Math.max(steps.length, 1) * DEFAULT_NODE_Y_GAP,
});

export const createDefaultGraphFromSteps = (
  steps: VersionBuilderStepValue[],
): VersionBuilderGraphValue => {
  const nodes: VersionBuilderGraphNodeValue[] = [
    {
      id: GRAPH_INPUT_NODE_ID,
      kind: 'input',
      position: { x: DEFAULT_NODE_X, y: 24 },
    },
  ];
  const edges: VersionBuilderGraphEdgeValue[] = [];
  const stepNodeIdById = new Map<string, string>();

  steps.forEach((step, index) => {
    const nodeId = getStepNodeId(step.id);
    stepNodeIdById.set(step.id, nodeId);
    nodes.push({
      id: nodeId,
      kind: 'capability',
      position: step.position || getDefaultNodePosition(index),
      step_id: step.id,
    });
  });

  nodes.push({
    id: GRAPH_OUTPUT_NODE_ID,
    kind: 'output',
    position: getOutputNodePosition(steps),
    source_step_id: steps[steps.length - 1]?.id,
    output_handle: steps[steps.length - 1] ? getStepResultHandle(steps[steps.length - 1]) : undefined,
  });

  steps.forEach((step, index) => {
    const targetNodeId = getStepNodeId(step.id);
    const bindings = step.input_bindings && step.input_bindings.length > 0
      ? step.input_bindings
      : [{
        sourceNodeId: index === 0 ? GRAPH_INPUT_NODE_ID : steps[index - 1]?.id,
        sourceHandle: index === 0 ? 'input' : getStepResultHandle(steps[index - 1]),
        target: DEFAULT_PRIMARY_TARGET,
      }];

    bindings.forEach((binding, bindingIndex) => {
      const sourceNodeId = binding.sourceNodeId === GRAPH_INPUT_NODE_ID
        ? GRAPH_INPUT_NODE_ID
        : binding.sourceNodeId
          ? stepNodeIdById.get(binding.sourceNodeId) || GRAPH_INPUT_NODE_ID
          : GRAPH_INPUT_NODE_ID;
      edges.push({
        id: `edge_${sourceNodeId}_${targetNodeId}_${binding.target}_${bindingIndex}`,
        source: sourceNodeId,
        target: targetNodeId,
        sourceHandle: binding.sourceHandle || (sourceNodeId === GRAPH_INPUT_NODE_ID ? 'input' : DEFAULT_OUTPUT_HANDLE),
        targetHandle: binding.target,
      });
    });
  });

  if (steps.length > 0) {
    const lastStep = steps[steps.length - 1];
    edges.push({
      id: `edge_${lastStep.id}_${GRAPH_OUTPUT_NODE_ID}`,
      source: getStepNodeId(lastStep.id),
      target: GRAPH_OUTPUT_NODE_ID,
      sourceHandle: getStepResultHandle(lastStep),
      targetHandle: 'result',
    });
  }

  return { nodes, edges };
};

const buildContextMappingFromBindings = (
  bindings: CapabilityNodeInputBinding[],
  stepById?: Map<string, VersionBuilderStepValue>,
): Record<string, string> => {
  const mapping: Record<string, string> = {};
  for (const binding of bindings) {
    if (!binding.sourceNodeId) {
      continue;
    }
    if (binding.target === DEFAULT_PRIMARY_TARGET) {
      continue;
    }
    if (binding.sourceNodeId === GRAPH_INPUT_NODE_ID) {
      mapping[binding.target] = `input.${binding.target}`;
      continue;
    }
    const sourceStep = stepById?.get(binding.sourceNodeId);
    const sourceKey = sourceStep?.output_key || sourceStep?.name || binding.sourceHandle;
    if (sourceKey) {
      mapping[binding.target] = `${sourceKey}.${binding.target}`;
    }
  }
  return mapping;
};

const buildInputKeyFromBindings = (
  bindings: CapabilityNodeInputBinding[],
  stepById: Map<string, VersionBuilderStepValue>,
): string => {
  const primaryBinding = bindings.find((item) => item.target === DEFAULT_PRIMARY_TARGET) || bindings[0];
  if (!primaryBinding || !primaryBinding.sourceNodeId || primaryBinding.sourceNodeId === GRAPH_INPUT_NODE_ID) {
    return 'input';
  }
  const sourceStep = stepById.get(primaryBinding.sourceNodeId);
  if (!sourceStep) {
    return 'input';
  }
  return sourceStep.output_key || sourceStep.name || 'input';
};

const topoSortSteps = (
  steps: VersionBuilderStepValue[],
): VersionBuilderStepValue[] => {
  const stepById = new Map(steps.map((step) => [step.id, step]));
  const incomingCount = new Map<string, number>();
  const outgoing = new Map<string, string[]>();

  steps.forEach((step) => {
    incomingCount.set(step.id, 0);
    outgoing.set(step.id, []);
  });

  steps.forEach((step) => {
    for (const binding of step.input_bindings ?? []) {
      if (!binding.sourceNodeId || binding.sourceNodeId === GRAPH_INPUT_NODE_ID) {
        continue;
      }
      if (!stepById.has(binding.sourceNodeId)) {
        continue;
      }
      incomingCount.set(step.id, (incomingCount.get(step.id) || 0) + 1);
      outgoing.get(binding.sourceNodeId)?.push(step.id);
    }
  });

  const queue = steps
    .filter((step) => (incomingCount.get(step.id) || 0) === 0)
    .sort((a, b) => {
      const aY = a.position?.y ?? 0;
      const bY = b.position?.y ?? 0;
      if (aY !== bY) return aY - bY;
      return (a.position?.x ?? 0) - (b.position?.x ?? 0);
    });

  const result: VersionBuilderStepValue[] = [];

  while (queue.length > 0) {
    const current = queue.shift()!;
    result.push(current);
    for (const nextId of outgoing.get(current.id) ?? []) {
      const nextCount = (incomingCount.get(nextId) || 0) - 1;
      incomingCount.set(nextId, nextCount);
      if (nextCount === 0) {
        const nextStep = stepById.get(nextId);
        if (nextStep) {
          queue.push(nextStep);
          queue.sort((a, b) => {
            const aY = a.position?.y ?? 0;
            const bY = b.position?.y ?? 0;
            if (aY !== bY) return aY - bY;
            return (a.position?.x ?? 0) - (b.position?.x ?? 0);
          });
        }
      }
    }
  }

  if (result.length !== steps.length) {
    throw new Error('节点连接存在环路，当前仅支持无环 Pipeline');
  }
  return result;
};

const getExecutableStepIdsFromGraph = (
  graph: VersionBuilderGraphValue,
): Set<string> => {
  const nodeById = new Map(graph.nodes.map((node) => [node.id, node]));
  const upstream = new Map<string, string[]>();
  graph.edges.forEach((edge) => {
    const items = upstream.get(edge.target) ?? [];
    items.push(edge.source);
    upstream.set(edge.target, items);
  });

  const result = new Set<string>();
  const visitedNodeIds = new Set<string>();
  const queue = [...(upstream.get(GRAPH_OUTPUT_NODE_ID) ?? [])];

  while (queue.length > 0) {
    const nodeId = queue.shift();
    if (!nodeId || visitedNodeIds.has(nodeId) || nodeId === GRAPH_INPUT_NODE_ID) {
      continue;
    }
    visitedNodeIds.add(nodeId);
    const node = nodeById.get(nodeId);
    if (node?.kind === 'capability' && node.step_id) {
      result.add(node.step_id);
    }
    queue.push(...(upstream.get(nodeId) ?? []));
  }

  return result;
};

export const validateVersionBuilderSteps = (
  steps: VersionBuilderStepValue[],
  graph?: VersionBuilderGraphValue,
): VersionBuilderValidationIssue[] => {
  const issues: VersionBuilderValidationIssue[] = [];
  const executableStepIds = graph
    ? getExecutableStepIdsFromGraph(graph)
    : new Set(steps.map((step) => step.id));

  steps.filter((step) => executableStepIds.has(step.id)).forEach((step) => {
    const primaryBinding = (step.input_bindings ?? []).find((binding) => binding.target === DEFAULT_PRIMARY_TARGET);
    if (!primaryBinding) {
      issues.push({
        stepId: step.id,
        message: `节点 ${step.name || step.capability} 缺少主输入连线`,
      });
    }
  });

  if (steps.length > 0 && graph) {
    const outputIncomingCount = graph.edges.filter((edge) => edge.target === GRAPH_OUTPUT_NODE_ID).length;
    if (outputIncomingCount === 0) {
      issues.push({ message: '输出节点缺少输入连线' });
    }
    if (outputIncomingCount > 1) {
      issues.push({ message: '输出节点只能连接一个上游节点' });
    }
  }

  return issues;
};

export const deriveVersionPayloadFromSteps = (
  rawSteps: VersionBuilderStepValue[],
  capabilities: AiPipelineCapabilityItem[],
  graph?: VersionBuilderGraphValue,
): DerivedVersionPayload => {
  const capabilityMap = new Map(capabilities.map((item) => [item.name, item]));
  const runtimeInputs = new Map<string, AiPipelineFieldSchema>();
  const resourceSlots = new Map<string, AiPipelineResourceSlotSchema & Record<string, unknown>>();
  const executableStepIds = graph
    ? getExecutableStepIdsFromGraph(graph)
    : new Set(rawSteps.map((step) => step.id));
  const orderedSteps = topoSortSteps(
    rawSteps
      .filter((step) => executableStepIds.has(step.id) && step.name && step.capability)
      .map((step) => ({
        ...step,
        input_bindings: (step.input_bindings ?? []).filter((binding) => (
          !binding.sourceNodeId
          || binding.sourceNodeId === GRAPH_INPUT_NODE_ID
          || executableStepIds.has(binding.sourceNodeId)
        )),
      })),
  );
  const stepById = new Map(orderedSteps.map((step) => [step.id, step]));

  const runtimeSteps = orderedSteps.map((step) => {
    const capability = capabilityMap.get(step.capability);
    const params: Record<string, unknown> = {};
    const fieldBindings = step.field_bindings ?? {};

    for (const field of capability?.parameter_fields ?? []) {
      const binding = fieldBindings[field.key] ?? {};
      const mode = binding.mode || defaultBindingMode(field);
      if (mode === 'fixed') {
        if (binding.value !== undefined && binding.value !== null && binding.value !== '') {
          params[field.key] = binding.value;
        }
        continue;
      }
      if (mode === 'runtime_input' && binding.runtime_input_key) {
        runtimeInputs.set(binding.runtime_input_key, {
          key: binding.runtime_input_key,
          label: binding.runtime_input_label || field.label,
          value_type: inferRuntimeValueType(field),
          required: field.required === true,
          default_value: field.default_value,
          description: field.description || undefined,
          widget: field.widget || undefined,
          options: field.options,
          multiline: field.widget === 'textarea',
        });
        params[field.key] = `{{runtime.${binding.runtime_input_key}}}`;
        continue;
      }
      if (mode === 'resource_slot' && binding.resource_slot_key) {
        resourceSlots.set(binding.resource_slot_key, {
          key: binding.resource_slot_key,
          label: binding.resource_slot_label || field.label,
          value_type: 'resource_ref',
          required: field.required === true,
          description: field.description || undefined,
          widget: 'resource-select',
          widget_props: {
            resource_type: field.resource_type,
            task_kind: field.task_kind,
            deployed_only: field.deployed_only !== false,
          },
          resource_type: field.resource_type || 'onnx_model',
          task_kind: field.task_kind,
          deployed_only: field.deployed_only !== false,
        });
        if (field.key === 'model_id') {
          params.resource_slot = binding.resource_slot_key;
        } else {
          params[field.key] = `{{resource.${binding.resource_slot_key}}}`;
        }
      }
    }

    const inputBindings = step.input_bindings ?? [];
    return {
      name: step.name,
      editor_id: step.id,
      capability: step.capability,
      input_key: buildInputKeyFromBindings(inputBindings, stepById),
      output_key: step.output_key || step.name,
      provider: step.provider || undefined,
      provider_role: step.provider_role || undefined,
      context_mapping: buildContextMappingFromBindings(inputBindings, stepById),
      params,
    };
  });

  return {
    runtimeInputs: Array.from(runtimeInputs.values()),
    resourceSlots: Array.from(resourceSlots.values()),
    steps: runtimeSteps,
  };
};

const inferInputBindingsFromStep = (
  step: VersionBuilderStepValue,
  outputKeyToStepId: Map<string, string>,
): CapabilityNodeInputBinding[] => {
  const bindings: CapabilityNodeInputBinding[] = [];

  const normalizedInputKey = (step.input_key || 'input').trim();
  if (!normalizedInputKey || normalizedInputKey === 'input') {
    bindings.push({
      sourceNodeId: GRAPH_INPUT_NODE_ID,
      sourceHandle: 'input',
      target: DEFAULT_PRIMARY_TARGET,
    });
  } else {
    bindings.push({
      sourceNodeId: outputKeyToStepId.get(normalizedInputKey) || GRAPH_INPUT_NODE_ID,
      sourceHandle: DEFAULT_OUTPUT_HANDLE,
      target: DEFAULT_PRIMARY_TARGET,
    });
  }

  const contextMapping = step.context_mapping ?? {};
  Object.entries(contextMapping).forEach(([target, rawValue]) => {
    if (typeof rawValue !== 'string') {
      return;
    }
    const value = rawValue.trim();
    if (!value) {
      return;
    }
    const [outputKey] = value.split('.', 1);
    bindings.push({
      sourceNodeId: outputKeyToStepId.get(outputKey) || GRAPH_INPUT_NODE_ID,
      sourceHandle: DEFAULT_OUTPUT_HANDLE,
      target,
    });
  });

  return bindings;
};

export const parseVersionBuilderStepsFromTemplate = (
  definitionJson: unknown,
  formSchemaJson: unknown,
  capabilities: AiPipelineCapabilityItem[],
): VersionBuilderStepValue[] => {
  const definition = normalizeObject(definitionJson);
  const formSchema = normalizeObject(formSchemaJson);
  const rawSteps = Array.isArray(definition.steps) ? definition.steps : [];
  const runtimeInputs = Array.isArray(formSchema.runtime_inputs) ? formSchema.runtime_inputs as AiPipelineFieldSchema[] : [];
  const rawResourceSlots = formSchema.resource_slots;
  const resourceSlots = Array.isArray(rawResourceSlots)
    ? rawResourceSlots as Array<AiPipelineResourceSlotSchema & Record<string, unknown>>
    : Object.entries(normalizeObject(definition.resource_slots)).map(([key, value]) => ({
      key,
      ...normalizeObject(value),
    })) as Array<AiPipelineResourceSlotSchema & Record<string, unknown>>;
  const capabilityMap = new Map(capabilities.map((item) => [item.name, item]));
  const provisionalSteps: VersionBuilderStepValue[] = rawSteps
    .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null && !Array.isArray(item))
    .map((step, index) => {
      const capabilityName = typeof step.capability === 'string' ? step.capability : '';
      const capability = capabilityMap.get(capabilityName);
      const rawName = typeof step.name === 'string' ? step.name : `step_${index + 1}`;
      const rawEditorId = typeof step.editor_id === 'string' ? step.editor_id.trim() : '';
      const stepId = rawEditorId || `step_${safeKey(rawName) || index + 1}`;
      const outputKey = typeof step.output_key === 'string' ? step.output_key : '';
      const baseStep = capability ? createStepFromCapability(capability, {
        id: stepId,
        name: rawName,
        output_key: outputKey || undefined,
        position: getDefaultNodePosition(index),
      }) : {
        id: stepId,
        name: rawName,
        capability: capabilityName,
        input_key: 'input',
        output_key: outputKey,
        provider: undefined,
        provider_role: undefined,
        context_mapping: {},
        field_bindings: {},
        position: getDefaultNodePosition(index),
        input_bindings: [],
      };
      const params = normalizeObject(step.params);
      const fieldBindings = { ...(baseStep.field_bindings ?? {}) };

      for (const field of capability?.parameter_fields ?? []) {
        const rawValue = params[field.key];
        if (field.key === 'model_id' && typeof params.resource_slot === 'string' && params.resource_slot.trim()) {
          const slotKey = params.resource_slot.trim();
          const slotSchema = findResourceSlotSchema(resourceSlots, slotKey);
          fieldBindings[field.key] = {
            mode: 'resource_slot',
            resource_slot_key: slotKey,
            resource_slot_label: slotSchema?.label || field.label,
          };
          continue;
        }
        if (typeof rawValue === 'string' && rawValue.startsWith('{{runtime.') && rawValue.endsWith('}}')) {
          const runtimeKey = rawValue.slice('{{runtime.'.length, -2);
          const runtimeSchema = findRuntimeInputSchema(runtimeInputs, runtimeKey);
          fieldBindings[field.key] = {
            mode: 'runtime_input',
            runtime_input_key: runtimeKey,
            runtime_input_label: runtimeSchema?.label || field.label,
          };
          continue;
        }
        if (typeof rawValue === 'string' && rawValue.startsWith('{{resource.') && rawValue.endsWith('}}')) {
          const slotKey = rawValue.slice('{{resource.'.length, -2);
          const slotSchema = findResourceSlotSchema(resourceSlots, slotKey);
          fieldBindings[field.key] = {
            mode: 'resource_slot',
            resource_slot_key: slotKey,
            resource_slot_label: slotSchema?.label || field.label,
          };
          continue;
        }
        if (rawValue !== undefined) {
          const normalizedValue = normalizeStepFieldBindingValue(rawValue);
          if (normalizedValue === undefined) {
            continue;
          }
          fieldBindings[field.key] = {
            mode: 'fixed',
            value: normalizedValue,
          };
        }
      }

      return {
        ...baseStep,
        name: rawName,
        capability: capabilityName || baseStep.capability,
        input_key: typeof step.input_key === 'string' ? step.input_key : baseStep.input_key,
        output_key: outputKey || baseStep.output_key,
        provider: typeof step.provider === 'string' ? step.provider : baseStep.provider,
        provider_role: typeof step.provider_role === 'string' ? step.provider_role : baseStep.provider_role,
        context_mapping: normalizeObject(step.context_mapping) as Record<string, string>,
        field_bindings: fieldBindings,
      };
    })
    .filter((item) => item.capability && item.name);

  const outputKeyToStepId = new Map<string, string>();
  provisionalSteps.forEach((step) => {
    if (step.output_key) {
      outputKeyToStepId.set(step.output_key, step.id);
    } else {
      outputKeyToStepId.set(step.name, step.id);
    }
  });

  return provisionalSteps.map((step) => ({
    ...step,
    input_bindings: inferInputBindingsFromStep(step, outputKeyToStepId),
  }));
};

export const deriveGraphFromSteps = (
  steps: VersionBuilderStepValue[],
): VersionBuilderGraphValue => createDefaultGraphFromSteps(steps);

export const parseVersionBuilderGraphFromTemplate = (
  definitionJson: unknown,
  steps: VersionBuilderStepValue[],
): VersionBuilderGraphValue => {
  const fallbackGraph = deriveGraphFromSteps(steps);
  const definition = normalizeObject(definitionJson);
  const rawGraph = normalizeObject(definition.editor_graph);
  const rawNodes = Array.isArray(rawGraph.nodes) ? rawGraph.nodes : [];
  const rawEdges = Array.isArray(rawGraph.edges) ? rawGraph.edges : [];

  if (rawNodes.length === 0) {
    return fallbackGraph;
  }

  const stepIds = new Set(steps.map((step) => step.id));
  const fallbackNodeMap = new Map(fallbackGraph.nodes.map((node) => [node.id, node]));

  const parsedNodes: VersionBuilderGraphNodeValue[] = rawNodes
    .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null && !Array.isArray(item))
    .reduce<VersionBuilderGraphNodeValue[]>((result, item) => {
      const nodeId = typeof item.id === 'string' ? item.id : '';
      const fallbackNode = fallbackNodeMap.get(nodeId);
      if (!nodeId || !fallbackNode) {
        return result;
      }

      const kind = item.kind === 'input' || item.kind === 'capability' || item.kind === 'output'
        ? item.kind
        : fallbackNode.kind;
      const position = normalizeObject(item.position);
      const x = typeof position.x === 'number' ? position.x : fallbackNode.position.x;
      const y = typeof position.y === 'number' ? position.y : fallbackNode.position.y;
      const stepId = typeof item.step_id === 'string' && stepIds.has(item.step_id)
        ? item.step_id
        : fallbackNode.step_id;

      result.push({
        ...fallbackNode,
        kind,
        position: { x, y },
        step_id: stepId,
        source_step_id: typeof item.source_step_id === 'string' ? item.source_step_id : fallbackNode.source_step_id,
        output_handle: typeof item.output_handle === 'string' ? item.output_handle : fallbackNode.output_handle,
      });
      return result;
    }, []);

  const parsedNodeIds = new Set(parsedNodes.map((node) => node.id));
  const nodes = fallbackGraph.nodes.map((node) => (
    parsedNodes.find((candidate) => candidate.id === node.id) || node
  ));

  const edges: VersionBuilderGraphEdgeValue[] = rawEdges
    .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null && !Array.isArray(item))
    .reduce<VersionBuilderGraphEdgeValue[]>((result, item) => {
      const id = typeof item.id === 'string' ? item.id : '';
      const source = typeof item.source === 'string' ? item.source : '';
      const target = typeof item.target === 'string' ? item.target : '';
      if (!id || !source || !target) {
        return result;
      }
      if (!parsedNodeIds.has(source) || !parsedNodeIds.has(target)) {
        return result;
      }
      result.push({
        id,
        source,
        target,
        sourceHandle: typeof item.sourceHandle === 'string' ? item.sourceHandle : undefined,
        targetHandle: typeof item.targetHandle === 'string' ? item.targetHandle : undefined,
      });
      return result;
    }, []);

  return {
    nodes,
    edges,
  };
};

export const applyGraphToSteps = (
  steps: VersionBuilderStepValue[],
  graph: VersionBuilderGraphValue,
): VersionBuilderStepValue[] => {
  const nodeMap = new Map(graph.nodes.map((node) => [node.id, node]));
  const stepNodeByStepId = new Map<string, VersionBuilderGraphNodeValue>();
  graph.nodes.forEach((node) => {
    if (node.kind === 'capability' && node.step_id) {
      stepNodeByStepId.set(node.step_id, node);
    }
  });

  const stepIdByNodeId = new Map<string, string>();
  stepNodeByStepId.forEach((node, stepId) => {
    stepIdByNodeId.set(node.id, stepId);
  });

  const stepById = new Map(steps.map((step) => [step.id, step]));

  return steps.map((step) => {
    const stepNode = stepNodeByStepId.get(step.id);
    const inputBindings = graph.edges
      .filter((edge) => edge.target === stepNode?.id)
      .map((edge) => {
        const sourceNode = nodeMap.get(edge.source);
        const sourceStepId = sourceNode?.kind === 'capability'
          ? stepIdByNodeId.get(sourceNode.id)
          : sourceNode?.id;
        return {
          sourceNodeId: sourceStepId,
          sourceHandle: edge.sourceHandle,
          target: (edge.targetHandle as GraphInputTarget | undefined) || DEFAULT_PRIMARY_TARGET,
        } satisfies CapabilityNodeInputBinding;
      });

    return {
      ...step,
      position: stepNode?.position || step.position,
      input_bindings: inputBindings,
      input_key: buildInputKeyFromBindings(inputBindings, stepById),
      context_mapping: buildContextMappingFromBindings(inputBindings, stepById),
      output_key: step.output_key || step.name,
    };
  });
};

export const getGraphInputNodeId = () => GRAPH_INPUT_NODE_ID;
export const getGraphOutputNodeId = () => GRAPH_OUTPUT_NODE_ID;
export const getGraphStepNodeId = getStepNodeId;
export const getGraphOutputHandle = getStepResultHandle;
