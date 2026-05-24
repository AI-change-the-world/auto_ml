import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  PlusOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import {
  Button,
  Drawer,
  Form,
  Input,
  Popconfirm,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { getAnnotation } from '../../api/annotation';
import {
  createAiPipelineBinding,
  deleteAiPipelineBinding,
  getAiPipelineTemplateDetail,
  listAiPipelineBindings,
  listAiPipelineModelResources,
  listAiPipelineProviderResources,
  listAiPipelineTemplates,
  updateAiPipelineBinding,
} from '../../api/aiPipeline';
import type {
  AiPipelineBindingResponse,
  AiPipelineProviderResourceOption,
  AiPipelineTemplateDetail,
  AiPipelineTemplateListItem,
  AnnotationProject,
} from '../../types';
import AiBindingDynamicFields from './components/AiBindingDynamicFields';
import {
  buildBindingFormInitialValues,
  buildBindingPayloadFromForm,
  getTemplateFormSchema,
} from '../../utils/aiPipelineSchema';

const { Text } = Typography;

const formatJsonPreview = (value: unknown) => {
  if (!value) return '-';
  if (typeof value === 'string') return value;
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
};

interface BindingFormState {
  name?: string;
  description?: string;
  template_id?: number;
  is_default?: boolean;
  runtime?: Record<string, unknown>;
  resource?: Record<string, unknown>;
}

const AnnotationAiBindingPage: React.FC = () => {
  const navigate = useNavigate();
  const { annotationId } = useParams<{ annotationId: string }>();
  const [form] = Form.useForm<BindingFormState>();
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [project, setProject] = React.useState<AnnotationProject | null>(null);
  const [templates, setTemplates] = React.useState<AiPipelineTemplateListItem[]>([]);
  const [bindings, setBindings] = React.useState<AiPipelineBindingResponse[]>([]);
  const [modelResources, setModelResources] = React.useState<ReturnType<typeof listAiPipelineModelResources> extends Promise<infer T> ? T : never>([]);
  const [providerResources, setProviderResources] = React.useState<AiPipelineProviderResourceOption[]>([]);
  const [editingBinding, setEditingBinding] = React.useState<AiPipelineBindingResponse | null>(null);
  const [selectedTemplateDetail, setSelectedTemplateDetail] = React.useState<AiPipelineTemplateDetail | null>(null);
  const [templateLoading, setTemplateLoading] = React.useState(false);
  const annotationNumericId = Number(annotationId);

  const loadData = React.useCallback(async () => {
    if (!annotationId || Number.isNaN(annotationNumericId)) return;
    setLoading(true);
    try {
      const [annotation, templatePage, bindingPage, models, providers] = await Promise.all([
        getAnnotation(annotationNumericId),
        listAiPipelineTemplates({ page: 1, page_size: 100, scene_type: 'assist_annotation' }),
        listAiPipelineBindings({
          page: 1,
          page_size: 100,
          binding_type: 'annotation_project',
          binding_target_id: annotationNumericId,
        }),
        listAiPipelineModelResources(true),
        listAiPipelineProviderResources(),
      ]);
      setProject(annotation);
      setTemplates((templatePage?.items ?? []).filter((item) => item.status !== 'disabled'));
      setBindings(bindingPage?.items ?? []);
      setModelResources(models);
      setProviderResources(providers);
    } catch (error) {
      console.error('failed to load annotation ai binding page', error);
      message.error('加载项目 AI Binding 配置失败');
    } finally {
      setLoading(false);
    }
  }, [annotationId, annotationNumericId]);

  React.useEffect(() => {
    void loadData();
  }, [loadData]);

  const loadTemplateDetail = React.useCallback(async (
    templateKey: string,
  ) => {
    setTemplateLoading(true);
    try {
      const detail = await getAiPipelineTemplateDetail(templateKey);
      setSelectedTemplateDetail(detail);
      return detail;
    } catch (error) {
      console.error('failed to load ai pipeline template detail', error);
      message.error('加载模板 schema 失败');
      return null;
    } finally {
      setTemplateLoading(false);
    }
  }, []);

  const openCreateDrawer = async () => {
    setEditingBinding(null);
    setSelectedTemplateDetail(null);
    form.resetFields();
    form.setFieldsValue({
      is_default: bindings.length === 0,
    });
    setDrawerOpen(true);
  };

  const openEditDrawer = async (binding: AiPipelineBindingResponse) => {
    setEditingBinding(binding);
    setDrawerOpen(true);
    const templateKey = templates.find((item) => item.id === binding.template_id)?.template_key ?? binding.template_key;
    if (!templateKey) {
      message.warning('当前绑定缺少模板标识，无法加载 schema');
      setSelectedTemplateDetail(null);
      form.setFieldsValue({
        ...buildBindingFormInitialValues(binding, getTemplateFormSchema(null)),
      });
      return;
    }
    const detail = await loadTemplateDetail(templateKey);
    form.setFieldsValue(buildBindingFormInitialValues(binding, getTemplateFormSchema(detail)));
  };

  const handleTemplateChange = async (templateId: number) => {
    const selectedTemplate = templates.find((item) => item.id === templateId);
    if (!selectedTemplate) {
      setSelectedTemplateDetail(null);
      return;
    }
    const detail = await loadTemplateDetail(selectedTemplate.template_key);
    const currentValues = form.getFieldsValue(true);
    const nextInitialValues = buildBindingFormInitialValues(editingBinding, getTemplateFormSchema(detail));
    form.setFieldsValue({
      ...currentValues,
      template_id: templateId,
      runtime: nextInitialValues.runtime,
      resource: nextInitialValues.resource,
    });
  };

  const handleSubmit = async () => {
    if (!annotationId || Number.isNaN(annotationNumericId)) return;
    try {
      const values = await form.validateFields();
      const payload = buildBindingPayloadFromForm(
        annotationNumericId,
        values,
        getTemplateFormSchema(selectedTemplateDetail),
        modelResources,
        providerResources,
      );
      setSaving(true);
      if (editingBinding) {
        await updateAiPipelineBinding(editingBinding.id, {
          template_id: payload.template_id,
          name: payload.name,
          description: payload.description,
          is_default: payload.is_default,
          runtime_input_defaults_json: payload.runtime_input_defaults_json,
          resource_bindings_json: payload.resource_bindings_json,
        });
        message.success('项目 AI Binding 已更新');
      } else {
        await createAiPipelineBinding(payload);
        message.success('项目 AI Binding 已创建');
      }
      setDrawerOpen(false);
      setSelectedTemplateDetail(null);
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

  const handleDeleteBinding = async (binding: AiPipelineBindingResponse) => {
    try {
      await deleteAiPipelineBinding(binding.id);
      message.success('项目 AI Binding 已删除');
      if (editingBinding?.id === binding.id) {
        setDrawerOpen(false);
        setEditingBinding(null);
        setSelectedTemplateDetail(null);
        form.resetFields();
      }
      await loadData();
    } catch (error) {
      console.error('failed to delete binding', error);
      message.error('删除项目 AI Binding 失败');
    }
  };

  const templateOptions = templates.map((item) => ({
    label: item.name,
    value: item.id,
  }));

  const selectedSchema = getTemplateFormSchema(selectedTemplateDetail);

  return (
    <div className="page-container" style={{ maxWidth: 1200 }}>
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-title-icon">
            <RobotOutlined />
          </div>
          <div>
            <h1 className="page-title">项目 AI Binding 配置</h1>
            <p className="page-subtitle">{project ? project.name : '标注项目默认模板、资源与运行参数绑定'}</p>
          </div>
        </div>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/annotations')}>
            返回
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => void openCreateDrawer()}>
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
                <div className="caption-text" style={{ color: '#888' }}>可选模板</div>
                <div className="body-text-sm" style={{ color: '#111' }}>{templates.length}</div>
              </div>
              <div>
                <div className="caption-text" style={{ color: '#888' }}>可选模型资源</div>
                <div className="body-text-sm" style={{ color: '#111' }}>{modelResources.length}</div>
              </div>
              <div>
                <div className="caption-text" style={{ color: '#888' }}>可选 Provider 资源</div>
                <div className="body-text-sm" style={{ color: '#111' }}>{providerResources.length}</div>
              </div>
              <div>
                <div className="caption-text" style={{ color: '#888' }}>模板定义入口</div>
                <Button type="link" style={{ padding: 0 }} onClick={() => navigate('/ai-pipeline')}>
                  前往平台模板管理
                </Button>
              </div>
              <div>
                <div className="caption-text" style={{ color: '#888' }}>Provider 资源入口</div>
                <Button type="link" style={{ padding: 0 }} onClick={() => navigate('/ai-pipeline/providers')}>
                  前往 Provider 资源管理
                </Button>
              </div>
            </Space>
          </div>

          <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 8, padding: 8 }}>
            <Table<AiPipelineBindingResponse>
              rowKey="id"
              pagination={false}
              dataSource={bindings}
              locale={{ emptyText: '当前项目还没有 AI Binding，请先创建一个项目默认绑定。' }}
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
                  render: (_, record) => record.template_name || record.template_key,
                },
                {
                  title: '资源绑定',
                  key: 'resource_bindings_json',
                  render: (_, record) => (
                    <Text ellipsis style={{ maxWidth: 260 }} title={formatJsonPreview(record.resource_bindings_json)}>
                      {formatJsonPreview(record.resource_bindings_json)}
                    </Text>
                  ),
                },
                {
                  title: '运行默认值',
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
                  width: 180,
                  render: (_, record) => (
                    <Space size={8}>
                      <Button size="small" onClick={() => void openEditDrawer(record)}>
                        编辑
                      </Button>
                      <Popconfirm
                        title="确认删除当前 Binding？"
                        okText="删除"
                        cancelText="取消"
                        okButtonProps={{ danger: true }}
                        onConfirm={() => void handleDeleteBinding(record)}
                      >
                        <Button size="small" danger icon={<DeleteOutlined />}>
                          删除
                        </Button>
                      </Popconfirm>
                    </Space>
                  ),
                },
              ]}
            />
          </div>
        </>
      )}

      <Drawer
        title={editingBinding ? '编辑项目 Binding' : '新建项目 Binding'}
        width={560}
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedTemplateDetail(null);
        }}
        destroyOnClose
        extra={(
          <Space>
            <Button onClick={() => setDrawerOpen(false)}>取消</Button>
            <Button type="primary" loading={saving} onClick={() => void handleSubmit()}>保存</Button>
          </Space>
        )}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="Binding 名称" name="name">
            <Input placeholder="如：默认检测辅助" />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <Input.TextArea rows={3} placeholder="可选描述" />
          </Form.Item>

          <Form.Item
            label="模板"
            name="template_id"
            rules={[{ required: true, message: '请选择模板' }]}
          >
            <Select
              placeholder="选择辅助标注模板"
              options={templateOptions}
              onChange={(value) => void handleTemplateChange(value)}
            />
          </Form.Item>

          <Form.Item label="设为项目默认" name="is_default" valuePropName="checked">
            <Switch />
          </Form.Item>

          {templateLoading ? (
            <div style={{ padding: '20px 0', textAlign: 'center' }}>
              <Spin />
            </div>
          ) : (
            <AiBindingDynamicFields
              runtimeFields={selectedSchema.runtime_inputs ?? []}
              resourceFields={selectedSchema.resource_slots ?? []}
              modelResources={modelResources}
              providerResources={providerResources}
            />
          )}

          {selectedTemplateDetail ? (
            <div style={{ padding: 12, border: '1px solid #eee', borderRadius: 8, background: '#fafafa', marginTop: 16 }}>
              <div className="caption-text" style={{ color: '#888', marginBottom: 6 }}>当前模板</div>
              <div className="body-text-sm" style={{ color: '#111', marginBottom: 4 }}>
                {selectedTemplateDetail.name}
              </div>
              <div className="caption-text" style={{ color: '#666' }}>{selectedTemplateDetail.description || '无描述'}</div>
            </div>
          ) : null}
        </Form>
      </Drawer>
    </div>
  );
};

export default AnnotationAiBindingPage;
