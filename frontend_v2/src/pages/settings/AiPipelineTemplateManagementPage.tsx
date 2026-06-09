import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ApartmentOutlined,
  ArrowLeftOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import {
  Button,
  Drawer,
  Form,
  Input,
  message,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tag,
  Typography,
} from 'antd';
import {
  createAiPipelineTemplate,
  deleteAiPipelineTemplate,
  disableAiPipelineTemplate,
  listAiPipelineTemplates,
} from '../../api/aiPipeline';
import type {
  AiPipelineTemplateCreateRequest,
  AiPipelineTemplateListItem,
} from '../../types';

const { Text } = Typography;

interface TemplateFormValues {
  template_key: string;
  name: string;
  description?: string;
  scene_type: string;
  input_kind?: string;
  output_kind?: string;
  status?: string;
  is_builtin?: boolean;
}

const buildTemplateEditorUrl = (templateKey: string) => (
  `/ai-pipeline/editor/${encodeURIComponent(templateKey)}`
);

const sceneTypeOptions = [
  { label: 'assist_annotation', value: 'assist_annotation' },
  { label: 'video_annotation', value: 'video_annotation' },
  { label: 'general', value: 'general' },
];

const inputKindOptions = [
  { label: 'image', value: 'image' },
  { label: 'text', value: 'text' },
  { label: 'mixed', value: 'mixed' },
];

const outputKindOptions = [
  { label: 'annotations', value: 'annotations' },
  { label: 'overlay_image', value: 'overlay_image' },
  { label: 'preview_image', value: 'preview_image' },
  { label: 'text', value: 'text' },
];

const AiPipelineTemplateManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = React.useState(true);
  const [templates, setTemplates] = React.useState<AiPipelineTemplateListItem[]>([]);
  const [templateDrawerOpen, setTemplateDrawerOpen] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [actionLoading, setActionLoading] = React.useState(false);
  const [templateForm] = Form.useForm<TemplateFormValues>();

  const loadTemplates = React.useCallback(async () => {
    setLoading(true);
    try {
      const page = await listAiPipelineTemplates({ page: 1, page_size: 200 });
      setTemplates(page?.items ?? []);
    } catch (error) {
      console.error('failed to load ai pipeline templates', error);
      message.error('加载 AI Pipeline 模板失败');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadTemplates();
  }, [loadTemplates]);

  const openTemplateEditorPage = React.useCallback((templateKey: string) => {
    const openedWindow = window.open(buildTemplateEditorUrl(templateKey), '_blank', 'noopener');
    if (!openedWindow) {
      message.warning('浏览器拦截了新页面，请允许弹窗后重试。');
    }
  }, []);

  const openTemplateDrawer = () => {
    templateForm.setFieldsValue({
      scene_type: 'assist_annotation',
      input_kind: 'image',
      output_kind: 'annotations',
      status: 'active',
      is_builtin: false,
    });
    setTemplateDrawerOpen(true);
  };

  const openVersionBuilder = (templateKey: string) => {
    openTemplateEditorPage(templateKey);
  };

  const handleCreateTemplate = async () => {
    try {
      const values = await templateForm.validateFields();
      const payload: AiPipelineTemplateCreateRequest = {
        template_key: values.template_key.trim(),
        name: values.name.trim(),
        description: values.description?.trim(),
        scene_type: values.scene_type,
        input_kind: values.input_kind || undefined,
        output_kind: values.output_kind || undefined,
        status: values.status || 'active',
        is_builtin: Boolean(values.is_builtin),
      };
      setSaving(true);
      const created = await createAiPipelineTemplate(payload);
      message.success('模板已创建');
      setTemplateDrawerOpen(false);
      templateForm.resetFields();
      await loadTemplates();
      openTemplateEditorPage(created.template_key);
    } catch (error) {
      if (error instanceof Error && error.message) {
        message.error(error.message);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDisableTemplate = async (templateKey: string) => {
    try {
      setActionLoading(true);
      await disableAiPipelineTemplate(templateKey);
      await loadTemplates();
      message.success('模板已禁用');
    } catch (error) {
      if (error instanceof Error && error.message) {
        message.error(error.message);
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteTemplate = async (templateKey: string) => {
    try {
      setActionLoading(true);
      await deleteAiPipelineTemplate(templateKey);
      await loadTemplates();
      message.success('模板已删除');
    } catch (error) {
      if (error instanceof Error && error.message) {
        message.error(error.message);
      }
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-title-icon">
            <ApartmentOutlined />
          </div>
          <div>
            <h1 className="page-title">AI Pipeline 模板管理</h1>
            <p className="page-subtitle">统一维护平台 Pipeline 定义。项目页面只负责绑定与覆盖配置。</p>
          </div>
        </div>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/settings')}>
            返回设置
          </Button>
          <Button onClick={() => navigate('/ai-pipeline/providers')}>
            Provider 资源
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openTemplateDrawer}>
            新建模板
          </Button>
        </Space>
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 8, padding: 8 }}>
        {loading ? (
          <div style={{ padding: 80, textAlign: 'center' }}>
            <Spin size="large" />
          </div>
        ) : (
          <Table<AiPipelineTemplateListItem>
            rowKey="template_key"
            pagination={false}
            dataSource={templates}
            locale={{ emptyText: '暂无模板' }}
            columns={[
              {
                title: '模板',
                key: 'name',
                render: (_, record) => (
                  <div>
                    <div className="body-text-sm" style={{ color: '#111' }}>{record.name}</div>
                    <div className="caption-text" style={{ color: '#888' }}>{record.template_key}</div>
                  </div>
                ),
              },
              {
                title: '场景',
                dataIndex: 'scene_type',
                key: 'scene_type',
                width: 180,
              },
              {
                title: '输入 / 输出',
                key: 'io',
                width: 220,
                render: (_, record) => (
                  <Space size={6} wrap>
                    <Tag>{record.input_kind || '-'}</Tag>
                    <Text type="secondary">→</Text>
                    <Tag>{record.output_kind || '-'}</Tag>
                  </Space>
                ),
              },
              {
                title: '状态',
                dataIndex: 'status',
                key: 'status',
                width: 120,
                render: (value: string) => (
                  <Tag color={value === 'disabled' ? 'default' : 'blue'}>{value}</Tag>
                ),
              },
              {
                title: '定义',
                key: 'definition',
                width: 120,
                render: (_, record) => (
                  <span className="caption-text" style={{ color: '#666' }}>
                    {record.latest_version > 0 ? '已配置' : '未配置'}
                  </span>
                ),
              },
              {
                title: '操作',
                key: 'actions',
                width: 280,
                render: (_, record) => (
                  <Space size={8}>
                    <Button
                      size="small"
                      type="primary"
                      onClick={() => openVersionBuilder(record.template_key)}
                    >
                      修改
                    </Button>
                    <Button
                      size="small"
                      disabled={record.status === 'disabled'}
                      loading={actionLoading}
                      onClick={() => void handleDisableTemplate(record.template_key)}
                    >
                      禁用
                    </Button>
                    <Button
                      size="small"
                      danger
                      loading={actionLoading}
                      onClick={() => void handleDeleteTemplate(record.template_key)}
                    >
                      删除
                    </Button>
                  </Space>
                ),
              },
            ]}
          />
        )}
      </div>

      <Drawer
        title="新建模板"
        width={520}
        open={templateDrawerOpen}
        onClose={() => setTemplateDrawerOpen(false)}
        destroyOnClose
        extra={(
          <Space>
            <Button onClick={() => setTemplateDrawerOpen(false)}>取消</Button>
            <Button type="primary" loading={saving} onClick={() => void handleCreateTemplate()}>保存</Button>
          </Space>
        )}
      >
        <Form form={templateForm} layout="vertical">
          <Form.Item label="模板 Key" name="template_key" rules={[{ required: true, message: '请输入模板 key' }]}>
            <Input placeholder="如：assist_bbox_default" />
          </Form.Item>
          <Form.Item label="模板名称" name="name" rules={[{ required: true, message: '请输入模板名称' }]}>
            <Input placeholder="如：默认检测辅助模板" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item label="场景" name="scene_type" rules={[{ required: true, message: '请选择场景' }]}>
            <Select options={sceneTypeOptions} />
          </Form.Item>
          <Form.Item label="输入类型" name="input_kind" rules={[{ required: true, message: '请选择输入类型' }]}>
            <Select options={inputKindOptions} placeholder="请选择输入类型" />
          </Form.Item>
          <Form.Item label="输出类型" name="output_kind" rules={[{ required: true, message: '请选择输出类型' }]}>
            <Select options={outputKindOptions} placeholder="请选择输出类型" />
          </Form.Item>
          <Form.Item label="状态" name="status">
            <Select
              options={[
                { label: 'active', value: 'active' },
                { label: 'disabled', value: 'disabled' },
              ]}
            />
          </Form.Item>
          <Form.Item label="内置模板" name="is_builtin" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
};

export default AiPipelineTemplateManagementPage;
