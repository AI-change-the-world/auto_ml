export type RuntimeParameterValues = Record<string, unknown>;

export interface RuntimeParameterField {
  key: string;
  label: string;
  description?: string;
  type?: string;
  enum?: Array<string | number | boolean>;
  defaultValue?: unknown;
  minimum?: number;
  maximum?: number;
  exclusiveMinimum?: number;
  exclusiveMaximum?: number;
  required: boolean;
}

export type RuntimeParameterValidationError = 'required' | 'invalid' | 'invalidJson';

const isJsonObject = (value: unknown): value is RuntimeParameterValues => (
  typeof value === 'object' && value !== null && !Array.isArray(value)
);

const getFieldLabel = (key: string, definition: RuntimeParameterValues) => {
  if (typeof definition.title === 'string' && definition.title.trim()) return definition.title.trim();
  return key.replace(/[_-]+/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase());
};

export const getRuntimeParameterFields = (schema: Record<string, unknown>): RuntimeParameterField[] => {
  const properties = schema.properties;
  if (!isJsonObject(properties)) return [];
  const required = new Set(
    Array.isArray(schema.required)
      ? schema.required.filter((item): item is string => typeof item === 'string')
      : [],
  );

  return Object.entries(properties).flatMap(([key, rawDefinition]) => {
    if (!isJsonObject(rawDefinition)) return [];
    const definition = rawDefinition;
    return [{
      key,
      label: getFieldLabel(key, definition),
      description: typeof definition.description === 'string' ? definition.description : undefined,
      type: typeof definition.type === 'string' ? definition.type : undefined,
      enum: Array.isArray(definition.enum)
        ? definition.enum.filter((item): item is string | number | boolean => (
          typeof item === 'string' || typeof item === 'number' || typeof item === 'boolean'
        ))
        : undefined,
      defaultValue: definition.default,
      minimum: typeof definition.minimum === 'number' ? definition.minimum : undefined,
      maximum: typeof definition.maximum === 'number' ? definition.maximum : undefined,
      exclusiveMinimum: typeof definition.exclusiveMinimum === 'number' ? definition.exclusiveMinimum : undefined,
      exclusiveMaximum: typeof definition.exclusiveMaximum === 'number' ? definition.exclusiveMaximum : undefined,
      required: required.has(key),
    }];
  });
};

export const buildRuntimeParameterDefaults = (schema: Record<string, unknown>): RuntimeParameterValues => (
  getRuntimeParameterFields(schema).reduce<RuntimeParameterValues>((parameters, field) => {
    if (field.defaultValue !== undefined) parameters[field.key] = field.defaultValue;
    return parameters;
  }, {})
);

export const isStructuredRuntimeParameter = (field: RuntimeParameterField) => (
  field.type === 'array' || field.type === 'object'
);

const isEmptyValue = (value: unknown) => value === undefined || value === '';

export const normalizeRuntimeParameters = (
  schema: Record<string, unknown>,
  values: RuntimeParameterValues,
): { parameters?: RuntimeParameterValues; error?: { field: RuntimeParameterField; kind: RuntimeParameterValidationError } } => {
  const parameters: RuntimeParameterValues = {};

  for (const field of getRuntimeParameterFields(schema)) {
    const rawValue = values[field.key];
    if (isEmptyValue(rawValue)) {
      if (field.required) return { error: { field, kind: 'required' } };
      continue;
    }

    let value = rawValue;
    if (isStructuredRuntimeParameter(field) && typeof rawValue === 'string') {
      try {
        value = JSON.parse(rawValue);
      } catch {
        return { error: { field, kind: 'invalidJson' } };
      }
    }

    if (
      (field.type === 'number' || field.type === 'integer')
      && (typeof value !== 'number' || !Number.isFinite(value) || (field.type === 'integer' && !Number.isInteger(value)))
    ) {
      return { error: { field, kind: 'invalid' } };
    }
    if (field.type === 'boolean' && typeof value !== 'boolean') return { error: { field, kind: 'invalid' } };
    if (field.type === 'string' && typeof value !== 'string') return { error: { field, kind: 'invalid' } };
    if (field.type === 'array' && !Array.isArray(value)) return { error: { field, kind: 'invalid' } };
    if (field.type === 'object' && !isJsonObject(value)) return { error: { field, kind: 'invalid' } };
    if (field.minimum !== undefined && typeof value === 'number' && value < field.minimum) return { error: { field, kind: 'invalid' } };
    if (field.maximum !== undefined && typeof value === 'number' && value > field.maximum) return { error: { field, kind: 'invalid' } };
    if (field.exclusiveMinimum !== undefined && typeof value === 'number' && value <= field.exclusiveMinimum) return { error: { field, kind: 'invalid' } };
    if (field.exclusiveMaximum !== undefined && typeof value === 'number' && value >= field.exclusiveMaximum) return { error: { field, kind: 'invalid' } };
    if (field.enum && !field.enum.some((option) => Object.is(option, value))) return { error: { field, kind: 'invalid' } };
    parameters[field.key] = value;
  }

  return { parameters };
};
