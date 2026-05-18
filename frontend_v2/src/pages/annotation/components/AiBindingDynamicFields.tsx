import React from 'react';
import { Form, Input, InputNumber, Select, Switch } from 'antd';
import type {
  AiPipelineFieldSchema,
  AiPipelineModelResourceItem,
  AiPipelineResourceSlotSchema,
} from '../../../types';

interface AiBindingDynamicFieldsProps {
  runtimeFields: AiPipelineFieldSchema[];
  resourceFields: AiPipelineResourceSlotSchema[];
  modelResources: AiPipelineModelResourceItem[];
}

const toSelectOptions = (options?: Array<{ label: string; value: string | number | boolean }>) => (
  options?.map((item) => ({
    label: item.label,
    value: item.value,
  })) ?? []
);

const buildResourceOptions = (
  field: AiPipelineResourceSlotSchema,
  modelResources: AiPipelineModelResourceItem[],
) => {
  const widgetProps = field.widget_props ?? {};
  const taskKind = typeof widgetProps.task_kind === 'string' ? widgetProps.task_kind : undefined;
  const runtimeTemplate = typeof widgetProps.runtime_template === 'string' ? widgetProps.runtime_template : undefined;
  const deployedOnly = widgetProps.deployed_only !== false;

  return modelResources
    .filter((item) => {
      if (deployedOnly && !item.is_deployed) return false;
      if (taskKind && item.model_type && item.model_type !== taskKind && item.model_type !== 'detection') return false;
      if (runtimeTemplate && item.runtime_template && item.runtime_template !== runtimeTemplate) return false;
      return true;
    })
    .map((item) => ({
      label: `${item.display_name}${item.deployment_device ? ` · ${item.deployment_device}` : ''}`,
      value: item.resource_id,
    }));
};

const renderRuntimeField = (field: AiPipelineFieldSchema) => {
  const widget = field.widget || field.value_type || 'text';
  const commonProps = {
    placeholder: field.description || `请输入${field.label}`,
  };

  if (widget === 'textarea' || field.multiline) {
    return <Input.TextArea rows={4} {...commonProps} />;
  }
  if (widget === 'number' || field.value_type === 'number') {
    return <InputNumber style={{ width: '100%' }} {...commonProps} />;
  }
  if (widget === 'switch' || field.value_type === 'boolean') {
    return <Switch />;
  }
  if (widget === 'select') {
    return <Select options={toSelectOptions(field.options)} {...commonProps} />;
  }
  if (widget === 'multi-select' || field.value_type === 'string_array') {
    return <Select mode="tags" tokenSeparators={[',']} options={toSelectOptions(field.options)} {...commonProps} />;
  }
  return <Input {...commonProps} />;
};

const renderResourceField = (
  field: AiPipelineResourceSlotSchema,
  modelResources: AiPipelineModelResourceItem[],
) => {
  const widget = field.widget || 'resource-select';
  if (widget === 'select') {
    return <Select options={toSelectOptions(field.options)} placeholder={field.description || `请选择${field.label}`} />;
  }
  return (
    <Select
      allowClear
      showSearch
      optionFilterProp="label"
      placeholder={field.description || `请选择${field.label}`}
      options={buildResourceOptions(field, modelResources)}
    />
  );
};

const AiBindingDynamicFields: React.FC<AiBindingDynamicFieldsProps> = ({
  runtimeFields,
  resourceFields,
  modelResources,
}) => {
  return (
    <>
      {runtimeFields.length > 0 ? (
        <div style={{ marginBottom: 20 }}>
          <div className="caption-text" style={{ color: '#888', marginBottom: 12 }}>运行参数</div>
          {runtimeFields.map((field) => (
            <Form.Item
              key={field.key}
              label={field.label}
              name={['runtime', field.key]}
              rules={field.required ? [{ required: true, message: `请输入${field.label}` }] : undefined}
              valuePropName={(field.widget === 'switch' || field.value_type === 'boolean') ? 'checked' : 'value'}
              extra={field.description}
            >
              {renderRuntimeField(field)}
            </Form.Item>
          ))}
        </div>
      ) : null}

      {resourceFields.length > 0 ? (
        <div>
          <div className="caption-text" style={{ color: '#888', marginBottom: 12 }}>资源槽位</div>
          {resourceFields.map((field) => (
            <Form.Item
              key={field.key}
              label={field.label}
              name={['resource', field.key]}
              rules={field.required ? [{ required: true, message: `请选择${field.label}` }] : undefined}
              extra={field.description}
            >
              {renderResourceField(field, modelResources)}
            </Form.Item>
          ))}
        </div>
      ) : null}
    </>
  );
};

export default AiBindingDynamicFields;
