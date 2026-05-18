import React from 'react';
import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  DeleteOutlined,
  HolderOutlined,
  PartitionOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import {
  Button,
  Empty,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Switch,
  Tag,
  message,
} from 'antd';
import type {
  AiPipelineCapabilityField,
  AiPipelineCapabilityItem,
} from '../../../types';
import {
  createStepFromCapability,
  defaultBindingMode,
  deriveVersionPayloadFromSteps as deriveVersionPayloadFromStepsHelper,
  safeKey,
  type StepFieldBindingMode,
  type VersionBuilderFormValues,
  type VersionBuilderStepValue,
} from './aiPipelineVersionBuilderHelpers';

interface AiPipelineVersionBuilderProps {
  form: ReturnType<typeof Form.useForm<VersionBuilderFormValues>>[0];
  capabilities: AiPipelineCapabilityItem[];
  capabilitiesLoading?: boolean;
}

const providerRoleOptions = [
  { label: 'multimodal', value: 'multimodal' },
  { label: 'image_edit', value: 'image_edit' },
];

const capabilityAccentMap: Record<string, { border: string; fill: string; text: string }> = {
  vision: { border: '#7c3aed', fill: '#f3e8ff', text: '#6d28d9' },
  llm: { border: '#2563eb', fill: '#dbeafe', text: '#1d4ed8' },
  control: { border: '#0f766e', fill: '#ccfbf1', text: '#0f766e' },
  transform: { border: '#ea580c', fill: '#ffedd5', text: '#c2410c' },
};

const getCapabilityAccent = (category?: string | null) => (
  capabilityAccentMap[category || ''] || { border: '#475569', fill: '#e2e8f0', text: '#334155' }
);

const renderFixedValueInput = (field: AiPipelineCapabilityField) => {
  const placeholder = field.placeholder || field.description || `请输入${field.label}`;
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

const readStepFieldBindingMode = (
  allSteps: VersionBuilderStepValue[],
  stepIndex: number,
  fieldKey: string,
): StepFieldBindingMode | undefined => allSteps?.[stepIndex]?.field_bindings?.[fieldKey]?.mode;

const renderBindingSummary = (
  step: VersionBuilderStepValue,
  field: AiPipelineCapabilityField,
) => {
  const binding = step.field_bindings?.[field.key];
  const mode = binding?.mode || defaultBindingMode(field);

  if (mode === 'resource_slot') {
    return binding?.resource_slot_label || binding?.resource_slot_key || '资源槽位';
  }
  if (mode === 'runtime_input') {
    return binding?.runtime_input_label || binding?.runtime_input_key || '运行参数';
  }
  if (binding?.value === undefined || binding?.value === null || binding?.value === '') {
    return '固定值';
  }
  return Array.isArray(binding.value) ? binding.value.join(', ') : String(binding.value);
};

const moveStep = (
  steps: VersionBuilderStepValue[],
  fromIndex: number,
  toIndex: number,
) => {
  if (toIndex < 0 || toIndex >= steps.length || fromIndex === toIndex) {
    return steps;
  }
  const next = [...steps];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  return next;
};

const DRAG_CAPABILITY_KEY = 'application/x-automl-capability';

export const deriveVersionPayloadFromSteps = (
  steps: VersionBuilderStepValue[],
  capabilities: AiPipelineCapabilityItem[],
) => deriveVersionPayloadFromStepsHelper(steps, capabilities);

const AiPipelineVersionBuilder: React.FC<AiPipelineVersionBuilderProps> = ({
  form,
  capabilities,
}) => {
  const sceneType = Form.useWatch('scene_type', form) as string | undefined;
  const steps = (Form.useWatch('steps', form) as VersionBuilderStepValue[] | undefined) ?? [];
  const [selectedStepIndex, setSelectedStepIndex] = React.useState<number>(0);
  const [draggingCapability, setDraggingCapability] = React.useState<string | null>(null);
  const [canvasDragging, setCanvasDragging] = React.useState(false);

  const filteredCapabilities = React.useMemo(() => (
    capabilities.filter((item) => (
      item.scene_types.length === 0
      || !sceneType
      || item.scene_types.includes(sceneType)
    ))
  ), [capabilities, sceneType]);

  const capabilityMap = React.useMemo(() => (
    new Map(filteredCapabilities.map((item) => [item.name, item]))
  ), [filteredCapabilities]);

  const derivedPayload = React.useMemo(() => (
    deriveVersionPayloadFromSteps(steps, filteredCapabilities)
  ), [steps, filteredCapabilities]);

  const selectedStep = steps[selectedStepIndex];
  const selectedCapability = selectedStep?.capability
    ? capabilityMap.get(selectedStep.capability)
    : undefined;

  React.useEffect(() => {
    if (steps.length === 0) {
      setSelectedStepIndex(0);
      return;
    }
    if (selectedStepIndex > steps.length - 1) {
      setSelectedStepIndex(steps.length - 1);
    }
  }, [selectedStepIndex, steps.length]);

  const appendCapabilityStep = React.useCallback((capabilityName: string) => {
    const capability = capabilityMap.get(capabilityName);
    if (!capability) {
      message.warning('当前场景下找不到这个 Capability');
      return;
    }
    const nextSteps = [...steps, createStepFromCapability(capability)];
    form.setFieldValue('steps', nextSteps);
    setSelectedStepIndex(nextSteps.length - 1);
  }, [capabilityMap, form, steps]);

  const handleMoveStep = (fromIndex: number, toIndex: number) => {
    const nextSteps = moveStep(steps, fromIndex, toIndex);
    form.setFieldValue('steps', nextSteps);
    setSelectedStepIndex(toIndex);
  };

  const handleDeleteStep = (index: number) => {
    const nextSteps = steps.filter((_, currentIndex) => currentIndex !== index);
    form.setFieldValue('steps', nextSteps);
    if (nextSteps.length === 0) {
      setSelectedStepIndex(0);
      return;
    }
    setSelectedStepIndex(Math.max(0, index - 1));
  };

  const handleCapabilityDragStart = (
    event: React.DragEvent<HTMLButtonElement>,
    capabilityName: string,
  ) => {
    event.dataTransfer.setData(DRAG_CAPABILITY_KEY, capabilityName);
    event.dataTransfer.effectAllowed = 'copy';
    setDraggingCapability(capabilityName);
  };

  const handleCanvasDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const capabilityName = event.dataTransfer.getData(DRAG_CAPABILITY_KEY);
    setCanvasDragging(false);
    setDraggingCapability(null);
    if (!capabilityName) {
      return;
    }
    appendCapabilityStep(capabilityName);
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '260px minmax(0, 1fr) 360px', gap: 0, minHeight: 'calc(100vh - 140px)', background: '#f8fafc' }}>
      <div style={{ borderRight: '1px solid #e2e8f0', background: '#ffffff', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <div style={{ padding: '18px 18px 14px', borderBottom: '1px solid #e2e8f0' }}>
          <div className="card-title" style={{ marginBottom: 4 }}>Node Library</div>
          <div className="caption-text" style={{ color: '#64748b' }}>把左侧节点拖到画板中创建。</div>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filteredCapabilities.length === 0 ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前场景没有可用节点" />
          ) : (
            filteredCapabilities.map((capability) => {
              const accent = getCapabilityAccent(capability.category);
              const isDragging = draggingCapability === capability.name;
              return (
                <button
                  key={capability.name}
                  type="button"
                  draggable
                  onDragStart={(event) => handleCapabilityDragStart(event, capability.name)}
                  onDragEnd={() => {
                    setDraggingCapability(null);
                    setCanvasDragging(false);
                  }}
                  style={{
                    borderRadius: 14,
                    border: `1px solid ${isDragging ? accent.border : '#e2e8f0'}`,
                    background: isDragging ? accent.fill : '#ffffff',
                    padding: 14,
                    textAlign: 'left',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                    <div style={{ width: 34, height: 34, borderRadius: 10, background: accent.fill, color: accent.text, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <HolderOutlined />
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 700 }}>{capability.display_name}</div>
                      <div className="caption-text" style={{ color: '#64748b', marginTop: 4 }}>{capability.name}</div>
                      <div className="caption-text" style={{ color: '#94a3b8', marginTop: 6, lineHeight: 1.6 }}>
                        {capability.description || '拖到画板中创建节点'}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '18px 24px', borderBottom: '1px solid #e2e8f0', background: '#ffffff' }}>
          <div>
            <div className="card-title" style={{ marginBottom: 2 }}>Pipeline Canvas</div>
            <div className="caption-text" style={{ color: '#64748b' }}>从左侧拖拽节点到画板。点中节点后在右侧配置。</div>
          </div>
          <Space size={16}>
            <div className="caption-text" style={{ color: '#64748b' }}>节点 {derivedPayload.steps.length}</div>
            <div className="caption-text" style={{ color: '#64748b' }}>运行参数 {derivedPayload.runtimeInputs.length}</div>
            <div className="caption-text" style={{ color: '#64748b' }}>资源槽位 {derivedPayload.resourceSlots.length}</div>
          </Space>
        </div>

        <div
          onDragOver={(event) => {
            event.preventDefault();
            event.dataTransfer.dropEffect = 'copy';
            setCanvasDragging(true);
          }}
          onDragLeave={() => setCanvasDragging(false)}
          onDrop={handleCanvasDrop}
          style={{
            flex: 1,
            overflow: 'auto',
            padding: 24,
            backgroundColor: canvasDragging ? '#eef4ff' : '#f8fafc',
            backgroundImage: 'radial-gradient(#dbe4f0 1px, transparent 1px)',
            backgroundSize: '18px 18px',
            transition: 'background-color 0.15s ease',
          }}
        >
          {steps.length === 0 ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100%' }}>
              <div style={{ width: 420, borderRadius: 20, border: `1px dashed ${canvasDragging ? '#3b82f6' : '#cbd5e1'}`, background: '#ffffff', padding: 28, textAlign: 'center' }}>
                <div style={{ width: 56, height: 56, borderRadius: 18, background: '#e0e7ff', color: '#4338ca', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14 }}>
                  <PartitionOutlined />
                </div>
                <div className="card-title" style={{ marginBottom: 8 }}>拖拽节点到画板</div>
                <div className="caption-text" style={{ color: '#64748b', lineHeight: 1.7 }}>
                  左侧选择 Capability，拖到这里创建 Pipeline 节点。
                </div>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18, minHeight: '100%' }}>
              <div style={{ width: '100%', maxWidth: 1160, display: 'flex', justifyContent: 'center' }}>
                <div style={{ minWidth: 260, maxWidth: 320, borderRadius: 16, border: '1px solid #cbd5e1', background: '#ffffff', padding: 18, boxShadow: '0 10px 30px rgba(15,23,42,0.04)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 34, height: 34, borderRadius: 10, background: '#e0e7ff', color: '#4338ca', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <PartitionOutlined />
                    </div>
                    <div>
                      <div className="body-text-sm" style={{ fontWeight: 600, color: '#0f172a' }}>输入节点</div>
                      <div className="caption-text" style={{ color: '#64748b' }}>Pipeline 输入</div>
                    </div>
                  </div>
                  <div style={{ marginTop: 14, padding: '10px 12px', borderRadius: 10, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                    <div className="caption-text" style={{ color: '#64748b' }}>source</div>
                    <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 600 }}>input</div>
                  </div>
                </div>
              </div>

              {steps.map((step, index) => {
                const capability = capabilityMap.get(step.capability);
                const accent = getCapabilityAccent(capability?.category);
                const isSelected = selectedStepIndex === index;
                return (
                  <React.Fragment key={`${step.name}-${index}`}>
                    <div style={{ width: 2, height: 22, background: '#cbd5e1' }} />
                    <div style={{ width: '100%', maxWidth: 1160, display: 'flex', justifyContent: index % 2 === 0 ? 'flex-start' : 'flex-end' }}>
                      <button
                        type="button"
                        onClick={() => setSelectedStepIndex(index)}
                        style={{
                          width: 360,
                          borderRadius: 18,
                          border: `1px solid ${isSelected ? accent.border : '#cbd5e1'}`,
                          background: '#ffffff',
                          padding: 18,
                          textAlign: 'left',
                          boxShadow: isSelected ? '0 16px 36px rgba(37,99,235,0.12)' : '0 8px 28px rgba(15,23,42,0.05)',
                          outline: 'none',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
                            <div style={{ width: 40, height: 40, borderRadius: 12, background: accent.fill, color: accent.text, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                              <SettingOutlined />
                            </div>
                            <div style={{ minWidth: 0 }}>
                              <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 700 }}>
                                {capability?.display_name || step.capability}
                              </div>
                              <div className="caption-text" style={{ color: '#64748b', marginTop: 2 }}>
                                {step.name}
                              </div>
                            </div>
                          </div>
                          <Tag color="blue" style={{ marginInlineEnd: 0 }}>{capability?.category || 'capability'}</Tag>
                        </div>

                        <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                          <div style={{ padding: '10px 12px', borderRadius: 10, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                            <div className="caption-text" style={{ color: '#64748b' }}>输入</div>
                            <div className="body-text-sm" style={{ color: '#0f172a' }}>{step.input_key || 'input'}</div>
                          </div>
                          <div style={{ padding: '10px 12px', borderRadius: 10, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                            <div className="caption-text" style={{ color: '#64748b' }}>输出</div>
                            <div className="body-text-sm" style={{ color: '#0f172a' }}>{step.output_key || step.name}</div>
                          </div>
                        </div>

                        {capability?.parameter_fields?.length ? (
                          <div style={{ marginTop: 14, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            {capability.parameter_fields.slice(0, 3).map((field) => (
                              <Tag key={field.key} style={{ borderRadius: 999, paddingInline: 10 }}>
                                {field.label}: {renderBindingSummary(step, field)}
                              </Tag>
                            ))}
                          </div>
                        ) : null}
                      </button>
                    </div>
                  </React.Fragment>
                );
              })}

              <div style={{ width: 2, height: 22, background: '#cbd5e1' }} />
              <div style={{ width: '100%', maxWidth: 1160, display: 'flex', justifyContent: 'center' }}>
                <div style={{ minWidth: 260, maxWidth: 320, borderRadius: 16, border: '1px dashed #cbd5e1', background: '#ffffff', padding: 18 }}>
                  <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 600 }}>输出节点</div>
                  <div className="caption-text" style={{ color: '#64748b', marginTop: 6 }}>
                    {derivedPayload.steps.length > 0 ? '最终输出来自最后一个节点。' : '暂无节点输出。'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={{ width: 360, borderLeft: '1px solid #e2e8f0', background: '#ffffff', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
        <div style={{ padding: '18px 20px', borderBottom: '1px solid #e2e8f0' }}>
          <div className="card-title" style={{ marginBottom: 4 }}>Node Inspector</div>
          <div className="caption-text" style={{ color: '#64748b' }}>
            {selectedStep ? '点击左侧节点后在这里配置。' : '先在画板中选择一个节点。'}
          </div>
        </div>

        {!selectedStep || !selectedCapability ? (
          <div style={{ padding: 20 }}>
            <div style={{ marginBottom: 20, borderRadius: 12, border: '1px solid #e2e8f0', background: '#f8fafc', padding: 16 }}>
              <div className="caption-text" style={{ color: '#64748b', marginBottom: 8 }}>运行参数</div>
              <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 600 }}>{derivedPayload.runtimeInputs.length}</div>
            </div>
            <div style={{ marginBottom: 20, borderRadius: 12, border: '1px solid #e2e8f0', background: '#f8fafc', padding: 16 }}>
              <div className="caption-text" style={{ color: '#64748b', marginBottom: 8 }}>资源槽位</div>
              <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 600 }}>{derivedPayload.resourceSlots.length}</div>
            </div>
            <div style={{ marginBottom: 20, borderRadius: 12, border: '1px solid #e2e8f0', background: '#f8fafc', padding: 16 }}>
              <div className="caption-text" style={{ color: '#64748b', marginBottom: 8 }}>节点数</div>
              <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 600 }}>{derivedPayload.steps.length}</div>
            </div>
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="选择一个节点后开始配置" />
          </div>
        ) : (
          <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 20 }}>
              <div>
                <div className="body-text-sm" style={{ fontWeight: 700, color: '#0f172a' }}>
                  {selectedCapability.display_name}
                </div>
                <div className="caption-text" style={{ color: '#64748b', marginTop: 4 }}>
                  {selectedCapability.name}
                </div>
              </div>
              <Space size={4}>
                <Button
                  size="small"
                  icon={<ArrowUpOutlined />}
                  disabled={selectedStepIndex === 0}
                  onClick={() => handleMoveStep(selectedStepIndex, selectedStepIndex - 1)}
                />
                <Button
                  size="small"
                  icon={<ArrowDownOutlined />}
                  disabled={selectedStepIndex === steps.length - 1}
                  onClick={() => handleMoveStep(selectedStepIndex, selectedStepIndex + 1)}
                />
                <Button
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => handleDeleteStep(selectedStepIndex)}
                />
              </Space>
            </div>

            <div style={{ marginBottom: 20, borderRadius: 12, border: '1px solid #e2e8f0', background: '#f8fafc', padding: 14 }}>
              <div className="caption-text" style={{ color: '#64748b' }}>
                {selectedCapability.description || '当前节点没有额外描述。'}
              </div>
            </div>

            <Form.Item
              label="节点 Key"
              name={['steps', selectedStepIndex, 'name']}
              rules={[{ required: true, message: '请输入节点 key' }]}
            >
              <Input placeholder="如：draft_boxes" />
            </Form.Item>

            <Form.Item
              label="Capability"
              name={['steps', selectedStepIndex, 'capability']}
              rules={[{ required: true, message: '请选择 Capability' }]}
            >
              <Select
                options={filteredCapabilities.map((item) => ({
                  label: `${item.display_name} · ${item.name}`,
                  value: item.name,
                }))}
              />
            </Form.Item>

            <Form.Item
              label="输入来源"
              name={['steps', selectedStepIndex, 'input_key']}
              rules={[{ required: true, message: '请输入输入来源' }]}
            >
              <Input placeholder="如：input / overlay_result" />
            </Form.Item>

            <Form.Item label="输出 Key" name={['steps', selectedStepIndex, 'output_key']}>
              <Input placeholder="如：draft_annotations" />
            </Form.Item>

            <Form.Item label="Provider 名称" name={['steps', selectedStepIndex, 'provider']}>
              <Input placeholder="如：qwen_vl" />
            </Form.Item>

            <Form.Item label="Provider 角色" name={['steps', selectedStepIndex, 'provider_role']}>
              <Select allowClear options={providerRoleOptions} placeholder="仅作编排提示" />
            </Form.Item>

            {selectedCapability.context_mapping_targets.length > 0 ? (
              <div style={{ marginBottom: 20 }}>
                <div className="card-title" style={{ marginBottom: 12 }}>上下文映射</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {selectedCapability.context_mapping_targets.map((target) => (
                    <Form.Item
                      key={target.key}
                      label={target.label}
                      name={['steps', selectedStepIndex, 'context_mapping', target.key]}
                      extra={target.description || undefined}
                    >
                      <Input placeholder="如：overlay_result.overlay_image" />
                    </Form.Item>
                  ))}
                </div>
              </div>
            ) : null}

            {selectedCapability.parameter_fields.length > 0 ? (
              <div>
                <div className="card-title" style={{ marginBottom: 12 }}>参数绑定</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  {selectedCapability.parameter_fields.map((paramField) => {
                    const bindingPath = ['steps', selectedStepIndex, 'field_bindings', paramField.key] as (string | number)[];
                    const mode = readStepFieldBindingMode(steps, selectedStepIndex, paramField.key);
                    const effectiveMode = mode || defaultBindingMode(paramField);
                    const modeOptions = paramField.binding_kind === 'resource'
                      ? [{ label: '资源槽位', value: 'resource_slot' }]
                      : [
                        { label: '固定值', value: 'fixed' },
                        { label: '运行参数', value: 'runtime_input' },
                      ];

                    return (
                      <div key={paramField.key} style={{ borderRadius: 12, border: '1px solid #e2e8f0', padding: 14, background: '#ffffff' }}>
                        <div style={{ marginBottom: 12 }}>
                          <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 600 }}>{paramField.label}</div>
                          <div className="caption-text" style={{ color: '#64748b', marginTop: 4 }}>
                            {paramField.description || paramField.key}
                          </div>
                        </div>

                        <Form.Item label="绑定方式" name={[...bindingPath, 'mode']}>
                          <Select options={modeOptions} />
                        </Form.Item>

                        {effectiveMode === 'fixed' ? (
                          <Form.Item
                            label="固定值"
                            name={[...bindingPath, 'value']}
                            valuePropName={(paramField.widget === 'switch' || paramField.value_type === 'boolean') ? 'checked' : 'value'}
                          >
                            {renderFixedValueInput(paramField)}
                          </Form.Item>
                        ) : null}

                        {effectiveMode === 'runtime_input' ? (
                          <>
                            <Form.Item label="运行参数 Key" name={[...bindingPath, 'runtime_input_key']}>
                              <Input placeholder={`如：${safeKey(`${selectedStep.name || 'step'}_${paramField.key}`)}`} />
                            </Form.Item>
                            <Form.Item label="运行参数名称" name={[...bindingPath, 'runtime_input_label']}>
                              <Input placeholder={paramField.label} />
                            </Form.Item>
                          </>
                        ) : null}

                        {effectiveMode === 'resource_slot' ? (
                          <>
                            <Form.Item label="资源槽位 Key" name={[...bindingPath, 'resource_slot_key']}>
                              <Input placeholder={`如：${safeKey(`${selectedStep.name || 'step'}_${paramField.key}`)}`} />
                            </Form.Item>
                            <Form.Item label="资源槽位名称" name={[...bindingPath, 'resource_slot_label']}>
                              <Input placeholder={paramField.label} />
                            </Form.Item>
                          </>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
};

export default AiPipelineVersionBuilder;
