import type {
  AiPipelineBindingResponse,
  AiPipelineFieldSchema,
  AiPipelineModelResourceItem,
  AiPipelineResourceSlotSchema,
  AiPipelineTemplateDetail,
  AiPipelineTemplateFormSchema,
} from '../types';

type JsonObject = Record<string, unknown>;

const isObject = (value: unknown): value is JsonObject => (
  typeof value === 'object' && value !== null && !Array.isArray(value)
);

const normalizeFieldArray = (value: unknown): AiPipelineFieldSchema[] => {
  if (!Array.isArray(value)) return [];
  return value
    .filter(isObject)
    .map((item) => ({
      key: typeof item.key === 'string' ? item.key : '',
      label: typeof item.label === 'string' ? item.label : (typeof item.key === 'string' ? item.key : ''),
      value_type: typeof item.value_type === 'string' ? item.value_type : undefined,
      required: item.required === true,
      default_value: item.default_value,
      description: typeof item.description === 'string' ? item.description : undefined,
      widget: typeof item.widget === 'string' ? item.widget : undefined,
      widget_props: isObject(item.widget_props) ? item.widget_props : null,
      options: Array.isArray(item.options)
        ? item.options
          .filter(isObject)
          .map((option) => ({
            label: typeof option.label === 'string' ? option.label : String(option.value ?? ''),
            value: option.value as string | number | boolean,
          }))
        : undefined,
      multiline: item.multiline === true,
    }))
    .filter((item) => item.key);
};

const normalizeResourceSlots = (value: unknown): AiPipelineResourceSlotSchema[] => {
  if (Array.isArray(value)) {
    return normalizeFieldArray(value);
  }
  if (!isObject(value)) return [];
  return Object.entries(value).map(([key, rawValue]) => {
    const item = isObject(rawValue) ? rawValue : {};
    return {
      key,
      label: typeof item.label === 'string' ? item.label : key,
      value_type: typeof item.value_type === 'string' ? item.value_type : 'resource_ref',
      required: item.required === true,
      default_value: item.default_value,
      description: typeof item.description === 'string' ? item.description : undefined,
      widget: typeof item.widget === 'string' ? item.widget : 'resource-select',
      widget_props: isObject(item.widget_props) ? item.widget_props : null,
      options: undefined,
      multiline: false,
    };
  });
};

const mergeDefinitionFallback = (
  definition: JsonObject,
  formSchema: JsonObject,
): AiPipelineTemplateFormSchema => {
  const runtimeInputs = normalizeFieldArray(
    formSchema.runtime_inputs
    ?? formSchema.fields
    ?? definition.runtime_inputs
    ?? definition.runtime_input_schema,
  );
  const resourceSlots = normalizeResourceSlots(
    formSchema.resource_slots
    ?? definition.resource_slots,
  );
  return {
    runtime_inputs: runtimeInputs,
    resource_slots: resourceSlots,
  };
};

const buildLegacyFormSchema = (): AiPipelineTemplateFormSchema => ({
  runtime_inputs: [
    {
      key: 'prompt',
      label: 'Prompt',
      value_type: 'string',
      widget: 'textarea',
      multiline: true,
      required: false,
    },
    {
      key: 'score_threshold',
      label: '阈值',
      value_type: 'number',
      widget: 'number',
      default_value: 0.2,
      required: false,
    },
  ],
  resource_slots: [
    {
      key: 'detector_model',
      label: '检测模型资源',
      value_type: 'resource_ref',
      widget: 'resource-select',
      required: false,
    },
  ],
});

export const getTemplateFormSchema = (templateDetail: AiPipelineTemplateDetail | null): AiPipelineTemplateFormSchema => {
  if (!templateDetail) {
    return buildLegacyFormSchema();
  }

  const definition = isObject(templateDetail.definition_json) ? templateDetail.definition_json : {};
  const formSchema = isObject(templateDetail.form_schema_json) ? templateDetail.form_schema_json : {};
  const normalized = mergeDefinitionFallback(definition, formSchema);
  if ((normalized.runtime_inputs?.length ?? 0) === 0 && (normalized.resource_slots?.length ?? 0) === 0) {
    return buildLegacyFormSchema();
  }
  return normalized;
};

const normalizeResourceBindingValue = (value: unknown, fallbackKey: string): Record<string, unknown> | null => {
  if (isObject(value)) return value;
  if (typeof value === 'number' && Number.isFinite(value)) {
    return {
      model_id: value,
      resource_id: `model:${value}`,
      slot_key: fallbackKey,
    };
  }
  if (typeof value === 'string' && value.trim()) {
    return {
      resource_id: value.trim(),
      slot_key: fallbackKey,
    };
  }
  return null;
};

export const buildBindingFormInitialValues = (
  binding: AiPipelineBindingResponse | null,
  schema: AiPipelineTemplateFormSchema,
): Record<string, unknown> => {
  const initialValues: Record<string, unknown> = {};

  for (const field of schema.runtime_inputs ?? []) {
    if (field.default_value !== undefined) {
      initialValues.runtime = {
        ...(isObject(initialValues.runtime) ? initialValues.runtime : {}),
        [field.key]: field.default_value,
      };
    }
  }
  for (const field of schema.resource_slots ?? []) {
    if (field.default_value !== undefined) {
      initialValues.resource = {
        ...(isObject(initialValues.resource) ? initialValues.resource : {}),
        [field.key]: field.default_value,
      };
    }
  }

  if (!binding) {
    return initialValues;
  }

  initialValues.name = binding.name ?? undefined;
  initialValues.description = binding.description ?? undefined;
  initialValues.template_id = binding.template_id;
  initialValues.template_version = binding.template_version;
  initialValues.is_default = binding.is_default;

  const runtimeDefaults = isObject(binding.runtime_input_defaults_json)
    ? binding.runtime_input_defaults_json
    : {};
  Object.entries(runtimeDefaults).forEach(([key, value]) => {
    initialValues.runtime = {
      ...(isObject(initialValues.runtime) ? initialValues.runtime : {}),
      [key]: value,
    };
  });

  const resourceBindings = isObject(binding.resource_bindings_json)
    ? binding.resource_bindings_json
    : {};
  Object.entries(resourceBindings).forEach(([key, value]) => {
    const normalized = normalizeResourceBindingValue(value, key);
    initialValues.resource = {
      ...(isObject(initialValues.resource) ? initialValues.resource : {}),
      [key]: normalized?.resource_id ?? normalized?.model_id,
    };
  });

  return initialValues;
};

const readNestedPathValue = (
  values: Record<string, unknown>,
  groupKey: 'runtime' | 'resource',
  fieldKey: string,
): unknown => {
  const group = values[groupKey];
  if (!isObject(group)) return undefined;
  return group[fieldKey];
};

const normalizeResourcePayload = (
  slotKey: string,
  rawValue: unknown,
  modelResources: AiPipelineModelResourceItem[],
): Record<string, unknown> | null => {
  if (isObject(rawValue)) {
    const resourceId = typeof rawValue.resource_id === 'string' ? rawValue.resource_id : undefined;
    const modelId = typeof rawValue.model_id === 'number' ? rawValue.model_id : undefined;
    if (resourceId || modelId !== undefined) {
      return {
        ...rawValue,
        slot_key: slotKey,
        resource_id: resourceId ?? (modelId !== undefined ? `model:${modelId}` : undefined),
      };
    }
  }
  if (typeof rawValue === 'number' && Number.isFinite(rawValue)) {
    const matched = modelResources.find((item) => item.model_id === rawValue);
    return {
      slot_key: slotKey,
      model_id: rawValue,
      resource_id: matched?.resource_id || `model:${rawValue}`,
    };
  }
  if (typeof rawValue === 'string' && rawValue.trim()) {
    const matched = modelResources.find((item) => item.resource_id === rawValue.trim());
    return {
      slot_key: slotKey,
      resource_id: rawValue.trim(),
      ...(matched ? { model_id: matched.model_id } : {}),
    };
  }
  return null;
};

export const buildBindingPayloadFromForm = (
  annotationId: number,
  values: {
    template_id?: number;
    name?: string;
    description?: string;
    is_default?: boolean;
    runtime?: Record<string, unknown>;
    resource?: Record<string, unknown>;
  },
  schema: AiPipelineTemplateFormSchema,
  modelResources: AiPipelineModelResourceItem[],
) => {
  const runtimeInputDefaultsJson: Record<string, unknown> = {};
  const resourceBindingsJson: Record<string, unknown> = {};

  for (const field of schema.runtime_inputs ?? []) {
    const rawValue = readNestedPathValue(values, 'runtime', field.key);
    if (rawValue === undefined || rawValue === null || rawValue === '') continue;
    runtimeInputDefaultsJson[field.key] = rawValue;
  }

  for (const field of schema.resource_slots ?? []) {
    const normalized = normalizeResourcePayload(
      field.key,
      readNestedPathValue(values, 'resource', field.key),
      modelResources,
    );
    if (!normalized) continue;
    resourceBindingsJson[field.key] = normalized;
  }

  return {
    binding_type: 'annotation_project',
    binding_target_id: annotationId,
    template_id: Number(values.template_id ?? 0),
    name: typeof values.name === 'string' && values.name.trim() ? values.name.trim() : undefined,
    description: typeof values.description === 'string' && values.description.trim() ? values.description.trim() : undefined,
    is_default: values.is_default === true,
    runtime_input_defaults_json: runtimeInputDefaultsJson,
    resource_bindings_json: resourceBindingsJson,
  };
};
