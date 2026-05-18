import type {
  AiPipelineCapabilityField,
  AiPipelineCapabilityItem,
  AiPipelineFieldSchema,
  AiPipelineResourceSlotSchema,
} from '../../../types';

export type StepFieldBindingMode = 'fixed' | 'runtime_input' | 'resource_slot';

type StepFieldBindingValue = string | number | boolean | string[] | null;

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

export interface StepFieldBinding {
  mode?: StepFieldBindingMode;
  value?: StepFieldBindingValue;
  runtime_input_key?: string;
  runtime_input_label?: string;
  resource_slot_key?: string;
  resource_slot_label?: string;
}

export interface VersionBuilderStepValue {
  name: string;
  capability: string;
  input_key?: string;
  output_key?: string;
  provider?: string;
  provider_role?: string;
  context_mapping?: Record<string, string>;
  field_bindings?: Record<string, StepFieldBinding>;
}

export interface VersionBuilderFormValues {
  change_note?: string;
  scene_type?: string;
  steps?: VersionBuilderStepValue[];
}

export interface DerivedVersionPayload {
  runtimeInputs: AiPipelineFieldSchema[];
  resourceSlots: Array<AiPipelineResourceSlotSchema & Record<string, unknown>>;
  steps: Array<Record<string, unknown>>;
}

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

export const createStepFromCapability = (capability: AiPipelineCapabilityItem): VersionBuilderStepValue => {
  const baseKey = safeKey(capability.name) || 'step';
  const fieldBindings = Object.fromEntries(
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
  );

  return {
    name: baseKey,
    capability: capability.name,
    input_key: 'input',
    output_key: capability.recommended_output_key || baseKey,
    provider: undefined,
    provider_role: capability.provider_role || undefined,
    context_mapping: {},
    field_bindings: fieldBindings,
  };
};

export const deriveVersionPayloadFromSteps = (
  steps: VersionBuilderStepValue[],
  capabilities: AiPipelineCapabilityItem[],
): DerivedVersionPayload => {
  const capabilityMap = new Map(capabilities.map((item) => [item.name, item]));
  const runtimeInputs = new Map<string, AiPipelineFieldSchema>();
  const resourceSlots = new Map<string, AiPipelineResourceSlotSchema & Record<string, unknown>>();
  const runtimeSteps = steps
    .filter((step) => step.name && step.capability)
    .map((step) => {
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

      return {
        name: step.name,
        capability: step.capability,
        input_key: step.input_key || 'input',
        output_key: step.output_key || step.name,
        provider: step.provider || undefined,
        provider_role: step.provider_role || undefined,
        context_mapping: step.context_mapping || {},
        params,
      };
    });

  return {
    runtimeInputs: Array.from(runtimeInputs.values()),
    resourceSlots: Array.from(resourceSlots.values()),
    steps: runtimeSteps,
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

  return rawSteps
    .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null && !Array.isArray(item))
    .map((step, index) => {
      const capabilityName = typeof step.capability === 'string' ? step.capability : '';
      const capability = capabilityMap.get(capabilityName);
      const baseStep = capability ? createStepFromCapability(capability) : {
        name: typeof step.name === 'string' ? step.name : `step_${index + 1}`,
        capability: capabilityName,
        input_key: 'input',
        output_key: '',
        provider: undefined,
        provider_role: undefined,
        context_mapping: {},
        field_bindings: {},
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
        name: typeof step.name === 'string' ? step.name : baseStep.name,
        capability: capabilityName || baseStep.capability,
        input_key: typeof step.input_key === 'string' ? step.input_key : baseStep.input_key,
        output_key: typeof step.output_key === 'string' ? step.output_key : baseStep.output_key,
        provider: typeof step.provider === 'string' ? step.provider : baseStep.provider,
        provider_role: typeof step.provider_role === 'string' ? step.provider_role : baseStep.provider_role,
        context_mapping: normalizeObject(step.context_mapping) as Record<string, string>,
        field_bindings: fieldBindings,
      };
    })
    .filter((item) => item.capability && item.name);
};
