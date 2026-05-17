import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeftOutlined,
  PlusOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import {
  Button,
  Drawer,
  Form,
  Input,
  InputNumber,
  message,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tag,
  Typography,
} from 'antd';
import { getAnnotation } from '../../api/annotation';
import {
  createAiPipelineBinding,
  listAiPipelineBindings,
  listAiPipelineModelResources,
  listAiPipelineTemplates,
  updateAiPipelineBinding,
} from '../../api/aiPipeline';
import type {
  AiPipelineBindingCreateRequest,
  AiPipelineBindingResponse,
  AiPipelineModelResourceItem,
  AiPipelineTemplateListItem,
  AnnotationProject,
} from '../../types';

const { Text } = Typography;

interface BindingFormValues {
  name?: string;
  description?: string;
  template_id?: number;
  template_version?: number;
  is_default?: boolean;
  prompt?: string;
  score_threshold?: number;
  detector_model_id?: number;
}

const formatJsonPreview = (value: unknown) => {
  if (!value) return '-';
  if (typeof value === 'string') return value;
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
};

const parseBindingFormValues = (binding: AiPipelineBindingResponse): BindingFormValues => {
  const runtimeInputs = binding.runtime_input_defaults_json;
  const runtimePayload = (runtimeInputs && typeof runtimeInputs === 'object' && !Array.isArray(runtimeInputs))
    ? runtimeInputs as Record<string, unknown>
    : {};
  const resourceBindings = binding.resource_bindings_json;
  const resourcePayload = (resourceBindings && typeof resourceBindings === 'object' && !Array.isArray(resourceBindings))
    ? resourceBindings as Record<string, unknown>
    : {};
  const detectorModel = resourcePayload.detector_model;
  const detectorModelPayload = (detectorModel && typeof detectorModel === 'object' && !Array.isArray(detectorModel))
    ? detectorModel as Record<string, unknown>
    : {};
  const modelIdValue = detectorModelPayload.model_id;
  return {
    name: binding.name ?? undefined,
    description: binding.description ?? undefined,
    template_id: binding.template_id,
    template_version: binding.template_version,
    is_default: binding.is_default,
    prompt: typeof runtimePayload.prompt === 'string' ? runtimePayload.prompt : undefined,
    score_threshold: typeof runtimePayload.score_threshold === 'number' ? runtimePayload.score_threshold : undefined,
    detector_model_id: typeof modelIdValue === 'number' ? modelIdValue : undefined,
  };
};

const buildBindingPayload = (
  annotationId: number,
  values: BindingFormValues,
): AiPipelineBindingCreateRequest => {
  return {
    binding_type: 'annotation_project',
    binding_target_id: annotationId,
    template_id: values.template_id ?? 0,
    template_version: values.template_version ?? 1,
    name: values.name?.trim() || undefined,
    description: values.description?.trim() || undefined,
    is_default: Boolean(values.is_default),
    runtime_input_defaults_json: {
      ...(values.prompt?.trim() ? { prompt: values.prompt.trim() } : {}),
      ...(values.score_threshold !== undefined ? { score_threshold: values.score_threshold } : {}),
    },
    resource_bindings_json: values.detector_model_id
      ? {
        detector_model: {
          model_id: values.detector_model_id,
          resource_id: `model:${values.detector_model_id}`,
        },
      }
      : {},
  };
};

const AnnotationAiPipelinePage: React.FC = () => {
  const navigate = useNavigate();
  const { annotationId } = useParams<{ annotationId: string }>();
  const [form] = Form.useForm<BindingFormValues>();
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [project, setProject] = React.useState<AnnotationProject | null>(null);
  const [templates, setTemplates] = React.useState<AiPipelineTemplateListItem[]>([]);
  const [bindings, setBindings] = React.useState<AiPipelineBindingResponse[]>([]);
  const [modelResources, setModelResources] = React.useState<AiPipelineModelResourceItem[]>([]);
  const [editingBinding, setEditingBinding] = React.useState<AiPipelineBindingResponse | null>(null);

  const annotationNumericId = Number(annotationId);

  const loadData = React.useCallback(async () => {
    if (!annotationId || Number.isNaN(annotationNumericId)) return;
    setLoading(true);
    try {
      const [annotation, templatePage, bindingPage, models] = await Promise.all([
        getAnnotation(annotationNumericId),
        listAiPipelineTemplates({ page: 1, page_size: 100, scene_type: 'assist_annotation' }),
        listAiPipelineBindings({
          page: 1,
          page_size: 100,
          binding_type: 'annotation_project',
          binding_target_id: annotationNumericId,
        }),
        listAiPipelineModelResources(true),
      ]);
      setProject(annotation);
      setTemplates((templatePage?.items ?? []).filter((item) => item.status !== 'draft'));
      setBindings(bindingPage?.items ?? []);
      setModelResources(models);
    } catch (error) {
      console.error('failed to load annotation ai pipeline page', error);
      message.error('加载 AI Pipeline 配置失败');
    } finally {
      setLoading(false);
    }
  }, [annotationId, annotationNumericId]);

  React.useEffect(() => {
    void loadData();
  }, [loadData]);

  const openCreateDrawer = () => {
    setEditingBinding(null);
    form.setFieldsValue({
      template_version: 1,
      is_default: bindings.length === 0,
      score_threshold: 0.2,
    });
    setDrawerOpen(true);
  };

  const openEditDrawer = (binding: AiPipelineBindingResponse) => {
    setEditingBinding(binding);
    form.setFieldsValue(parseBindingFormValues(binding));
    setDrawerOpen(true);
  };

  const handleSubmit = async () => {
    if (!annotationId || Number.isNaN(annotationNumericId)) return;
    try {
      const values = await form.validateFields();
      const payload = buildBindingPayload(annotationNumericId, values);
      setSaving(true);
      if (editingBinding) {
        await updateAiPipelineBinding(editingBinding.id, {
          name: payload.name,
          description: payload.description,
          is_default: payload.is_default,
          runtime_input_defaults_json: payload.runtime_input_defaults_json,
          resource_bindings_json: payload.resource_bindings_json,
        });
        message.success('AI Pipeline binding 已更新');
      } else {
        await createAiPipelineBinding(payload);
        message.success('AI Pipeline binding 已创建');
      }
      setDrawerOpen(false);
      form.resetFields();
      await loadData();
    } catch (error) {
      if (error instanceof Error && error.message) {
        message.error(error.message);
      }
    } finally {
      setSaving(false);
    }
  };

  const templateOptions = templates.map((item) => ({
    label: item.name,
    value: item.id,
  }));

  const selectedTemplate = templates.find((item) => item.id === Form.useWatch('template_id', form));

  return (
    <div className="page-container" style={{ maxWidth: 1200 }}>
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-title-icon">
            <RobotOutlined />
          </div>
          <div>
            <h1 className="page-title">AI Pipeline 配置</h1>
            <p className="page-subtitle">{project ? project.name : '标注项目 AI 绑定与默认资源配置'}</p>
          </div>
        </div>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/annotations')}>
            返回
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDrawer}>
            新建 Binding
          </Button>
        </Space>
      </div>

      {loading ? (
        <div style={{ padding: 80, textAlign: 'center' }}>
          <Spin size="large" />
        </div>
      ) : (
        <>
          <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 8, padding: 16, marginBottom: 16 }}>
            <Space size={24}>
              <div>
                <div className="caption-text" style={{ color: '#888' }}>默认 Binding</div>
                <div className="body-text-sm" style={{ color: '#111' }}>
                  {bindings.find((item) => item.is_default)?.name
                    || bindings.find((item) => item.is_default)?.template_name
                    || '-'}
                </div>
              </div>
              <div>
                <div className="caption-text" style={{ color: '#888' }}>可用模板</div>
                <div className="body-text-sm" style={{ color: '#111' }}>{templates.length}</div>
              </div>
              <div>
                <div className="caption-text" style={{ color: '#888' }}>可用模型资源</div>
                <div className="body-text-sm" style={{ color: '#111' }}>{modelResources.length}</div>
              </div>
            </Space>
          </div>

          <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 8, padding: 8 }}>
            <Table<AiPipelineBindingResponse>
              rowKey="id"
              pagination={false}
              dataSource={bindings}
              locale={{ emptyText: '当前项目还没有 AI binding，先创建一个默认辅助配置。' }}
              columns={[
                {
                  title: '名称',
                  dataIndex: 'name',
                  key: 'name',
                  render: (_, record) => record.name || record.template_name || record.template_key || `Binding #${record.id}`,
                },
                {
                  title: '模板',
                  dataIndex: 'template_name',
                  key: 'template_name',
                  render: (_, record) => (
                    <Space size={8}>
                      <span>{record.template_name || record.template_key}</span>
                      <Tag>v{record.template_version}</Tag>
                    </Space>
                  ),
                },
                {
                  title: '资源',
                  key: 'resource_bindings_json',
                  render: (_, record) => (
                    <Text ellipsis style={{ maxWidth: 260 }} title={formatJsonPreview(record.resource_bindings_json)}>
                      {formatJsonPreview(record.resource_bindings_json)}
                    </Text>
                  ),
                },
                {
                  title: '运行参数',
                  key: 'runtime_input_defaults_json',
                  render: (_, record) => (
                    <Text ellipsis style={{ maxWidth: 260 }} title={formatJsonPreview(record.runtime_input_defaults_json)}>
                      {formatJsonPreview(record.runtime_input_defaults_json)}
                    </Text>
                  ),
                },
                {
                  title: '默认',
                  dataIndex: 'is_default',
                  key: 'is_default',
                  width: 90,
                  render: (value: boolean) => value ? <Tag color="blue">默认</Tag> : '-',
                },
                {
                  title: '操作',
                  key: 'actions',
                  width: 120,
                  render: (_, record) => (
                    <Button size="small" onClick={() => openEditDrawer(record)}>
                      编辑
                    </Button>
                  ),
                },
              ]}
            />
          </div>
        </>
      )}

      <Drawer
        title={editingBinding ? '编辑 Binding' : '新建 Binding'}
        width={520}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        destroyOnClose
        extra={(
          <Space>
            <Button onClick={() => setDrawerOpen(false)}>取消</Button>
            <Button type="primary" loading={saving} onClick={handleSubmit}>保存</Button>
          </Space>
        )}
      >
        <Form form={form} layout="vertical" initialValues={{ template_version: 1, score_threshold: 0.2 }}>
          <Form.Item
            label="Binding 名称"
            name="name"
          >
            <Input placeholder="如：默认检测辅助" />
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
          >
            <Input.TextArea rows={3} placeholder="可选描述" />
          </Form.Item>

          <Form.Item
            label="模板"
            name="template_id"
            rules={[{ required: true, message: '请选择模板' }]}
          >
            <Select placeholder="选择辅助标注模板" options={templateOptions} />
          </Form.Item>

          <Form.Item
            label="模板版本"
            name="template_version"
            rules={[{ required: true, message: '请输入模板版本' }]}
          >
            <InputNumber min={1} precision={0} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="检测模型资源"
            name="detector_model_id"
          >
            <Select
              allowClear
              placeholder="选择已部署模型"
              options={modelResources.map((item) => ({
                label: `${item.display_name}${item.deployment_device ? ` · ${item.deployment_device}` : ''}`,
                value: item.model_id,
              }))}
            />
          </Form.Item>

          <Form.Item
            label="Prompt"
            name="prompt"
          >
            <Input.TextArea rows={4} placeholder="可选，覆盖项目默认 prompt" />
          </Form.Item>

          <Form.Item
            label="阈值"
            name="score_threshold"
          >
            <InputNumber min={0} max={1} step={0.05} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="设为项目默认"
            name="is_default"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          {selectedTemplate && (
            <div style={{ padding: 12, border: '1px solid #eee', borderRadius: 8, background: '#fafafa' }}>
              <div className="caption-text" style={{ color: '#888', marginBottom: 6 }}>当前模板</div>
              <div className="body-text-sm" style={{ color: '#111', marginBottom: 4 }}>{selectedTemplate.name}</div>
              <div className="caption-text" style={{ color: '#666' }}>{selectedTemplate.description || '无描述'}</div>
            </div>
          )}
        </Form>
      </Drawer>
    </div>
  );
};

export default AnnotationAiPipelinePage;
