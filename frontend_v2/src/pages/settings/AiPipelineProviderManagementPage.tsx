import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ApartmentOutlined,
  ArrowLeftOutlined,
  DeleteOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import {
  Button,
  Collapse,
  Drawer,
  Form,
  Input,
  InputNumber,
  Popconfirm,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tag,
  message,
} from 'antd';
import {
  createAiPipelineProviderResource,
  deleteAiPipelineProviderResource,
  listAiPipelineProviderResourceItems,
  updateAiPipelineProviderResource,
} from '../../api/aiPipeline';
import type {
  AiPipelineProviderResourceUpdateRequest,
  AiPipelineProviderResourceCreateRequest,
  AiPipelineProviderResourceItem,
} from '../../types';

interface ProviderFormValues {
  resource_id: string;
  provider_name: string;
  display_name: string;
  description?: string;
  kind: string;
  role: string;
  base_url?: string;
  api_key?: string;
  model?: string;
  timeout_seconds?: number;
  temperature?: number;
  max_tokens?: number;
  extra_headers_text?: string;
  extra_json_text?: string;
  enabled?: boolean;
}

const stringifyJson = (value: unknown) => {
  if (!value) return '';
  if (typeof value === 'string') return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return '';
  }
};

const parseJsonInput = (value?: string) => {
  const text = value?.trim();
  if (!text) return undefined;
  return JSON.parse(text);
};

const providerKindOptions = [
  { label: 'openai_compatible', value: 'openai_compatible' },
  { label: 'dashscope_multimodal', value: 'dashscope_multimodal' },
  // { label: 'mock', value: 'mock' },
];

const providerRoleOptions = [
  { label: 'multimodal', value: 'multimodal' },
  { label: 'image_edit', value: 'image_edit' },
  { label: 'text', value: 'text' },
];

const AiPipelineProviderManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm<ProviderFormValues>();
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [items, setItems] = React.useState<AiPipelineProviderResourceItem[]>([]);
  const [editingItem, setEditingItem] = React.useState<AiPipelineProviderResourceItem | null>(null);

  const loadItems = React.useCallback(async () => {
    setLoading(true);
    try {
      const result = await listAiPipelineProviderResourceItems(false);
      setItems(result);
    } catch (error) {
      console.error('failed to load ai pipeline provider resources', error);
      message.error('加载 Provider 资源失败');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadItems();
  }, [loadItems]);

  const openCreateDrawer = () => {
    setEditingItem(null);
    form.resetFields();
    form.setFieldsValue({
      kind: 'openai_compatible',
      role: 'multimodal',
      timeout_seconds: 60,
      temperature: 0,
      max_tokens: 1024,
      enabled: true,
    });
    setDrawerOpen(true);
  };

  const openEditDrawer = (item: AiPipelineProviderResourceItem) => {
    setEditingItem(item);
    form.setFieldsValue({
      resource_id: item.resource_id,
      provider_name: item.provider_name,
      display_name: item.display_name,
      description: item.description || undefined,
      kind: item.kind || 'openai_compatible',
      role: item.role,
      base_url: item.base_url || undefined,
      api_key: undefined,
      model: item.model || undefined,
      timeout_seconds: item.timeout_seconds ?? 60,
      temperature: item.temperature ?? 0,
      max_tokens: item.max_tokens ?? 1024,
      extra_headers_text: stringifyJson(item.extra_headers_json),
      extra_json_text: stringifyJson(item.extra_json),
      enabled: item.enabled !== false,
    });
    setDrawerOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const providerName = values.provider_name.trim();
      const payload: AiPipelineProviderResourceCreateRequest = {
        resource_id: values.resource_id?.trim() || `provider:${providerName}`,
        provider_name: providerName,
        display_name: values.display_name.trim(),
        description: values.description?.trim() || undefined,
        kind: values.kind,
        role: values.role,
        base_url: values.base_url?.trim() || undefined,
        api_key: values.api_key?.trim() || undefined,
        model: values.model?.trim() || undefined,
        timeout_seconds: values.timeout_seconds ?? 60,
        temperature: values.temperature ?? 0,
        max_tokens: values.max_tokens ?? 1024,
        extra_headers_json: parseJsonInput(values.extra_headers_text),
        extra_json: parseJsonInput(values.extra_json_text),
        enabled: values.enabled !== false,
      };
      setSaving(true);
      if (editingItem?.id) {
        const updatePayload: AiPipelineProviderResourceUpdateRequest = {
          display_name: payload.display_name,
          description: payload.description,
          kind: payload.kind,
          role: payload.role,
          base_url: payload.base_url,
          api_key: payload.api_key,
          model: payload.model,
          timeout_seconds: payload.timeout_seconds,
          temperature: payload.temperature,
          max_tokens: payload.max_tokens,
          extra_headers_json: payload.extra_headers_json,
          extra_json: payload.extra_json,
          enabled: payload.enabled,
        };
        await updateAiPipelineProviderResource(editingItem.id, updatePayload);
        message.success('Provider 资源已更新');
      } else {
        await createAiPipelineProviderResource(payload);
        message.success('Provider 资源已创建');
      }
      setDrawerOpen(false);
      form.resetFields();
      await loadItems();
    } catch (error) {
      if (error instanceof SyntaxError) {
        message.error('额外 JSON 配置格式不正确');
        return;
      }
      if (error instanceof Error && error.message) {
        message.error(error.message);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (item: AiPipelineProviderResourceItem) => {
    if (!item.id) return;
    try {
      await deleteAiPipelineProviderResource(item.id);
      message.success('Provider 资源已删除');
      await loadItems();
    } catch (error) {
      if (error instanceof Error && error.message) {
        message.error(error.message);
      }
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
            <h1 className="page-title">AI Provider 资源</h1>
            <p className="page-subtitle">统一维护平台可复用的模型服务 Provider，Binding 只选择资源，不直接填写配置。</p>
          </div>
        </div>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/ai-pipeline')}>
            返回模板管理
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateDrawer}>
            新建 Provider
          </Button>
        </Space>
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 8, padding: 8 }}>
        {loading ? (
          <div style={{ padding: 80, textAlign: 'center' }}>
            <Spin size="large" />
          </div>
        ) : (
          <Table<AiPipelineProviderResourceItem>
            rowKey={(item) => String(item.id ?? item.resource_id)}
            pagination={false}
            dataSource={items}
            locale={{ emptyText: '暂无 Provider 资源' }}
            columns={[
              {
                title: '资源',
                key: 'resource',
                render: (_, record) => (
                  <div>
                    <div className="body-text-sm" style={{ color: '#111' }}>{record.display_name}</div>
                    <div className="caption-text" style={{ color: '#888' }}>{record.resource_id}</div>
                  </div>
                ),
              },
              {
                title: 'Provider Name',
                dataIndex: 'provider_name',
                key: 'provider_name',
                width: 180,
              },
              {
                title: '密钥',
                dataIndex: 'api_key_configured',
                key: 'api_key_configured',
                width: 100,
                render: (value: boolean) => (
                  <Tag color={value ? 'blue' : 'default'}>{value ? '已配置' : '未配置'}</Tag>
                ),
              },
              {
                title: '角色 / 类型',
                key: 'role_kind',
                width: 220,
                render: (_, record) => (
                  <Space size={6} wrap>
                    <Tag>{record.role}</Tag>
                    <Tag bordered={false}>{record.kind || '-'}</Tag>
                  </Space>
                ),
              },
              {
                title: '模型',
                dataIndex: 'model',
                key: 'model',
                width: 180,
                render: (value: string | null | undefined) => value || '-',
              },
              {
                title: '状态',
                dataIndex: 'enabled',
                key: 'enabled',
                width: 100,
                render: (value: boolean | undefined) => (
                  <Tag color={value === false ? 'default' : 'blue'}>{value === false ? 'disabled' : 'enabled'}</Tag>
                ),
              },
              {
                title: '操作',
                key: 'actions',
                width: 180,
                render: (_, record) => (
                  <Space size={8}>
                    <Button size="small" onClick={() => openEditDrawer(record)}>
                      编辑
                    </Button>
                    <Popconfirm
                      title="确认删除当前 Provider 资源？"
                      okText="删除"
                      cancelText="取消"
                      okButtonProps={{ danger: true }}
                      onConfirm={() => void handleDelete(record)}
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
        )}
      </div>

      <Drawer
        title={editingItem ? '编辑 Provider 资源' : '新建 Provider 资源'}
        width={560}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        destroyOnClose
        extra={(
          <Space>
            <Button onClick={() => setDrawerOpen(false)}>取消</Button>
            <Button type="primary" loading={saving} onClick={() => void handleSubmit()}>
              保存
            </Button>
          </Space>
        )}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="Provider Name" name="provider_name" rules={[{ required: true, message: '请输入 provider name' }]}>
            <Input disabled={Boolean(editingItem)} placeholder="如：qwen_vl_prod" />
          </Form.Item>
          <Form.Item label="展示名称" name="display_name" rules={[{ required: true, message: '请输入展示名称' }]}>
            <Input placeholder="如：Qwen VL 生产环境" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item label="Provider 类型" name="kind" rules={[{ required: true, message: '请选择 Provider 类型' }]}>
            <Select options={providerKindOptions} />
          </Form.Item>
          <Form.Item label="角色" name="role" rules={[{ required: true, message: '请选择角色' }]}>
            <Select options={providerRoleOptions} />
          </Form.Item>
          <Form.Item label="Base URL" name="base_url">
            <Input placeholder="如：https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item label="API Key" name="api_key">
            <Input.Password placeholder={editingItem ? '留空表示保持当前 API Key' : '请输入 API Key'} />
          </Form.Item>
          <Form.Item label="模型名" name="model">
            <Input placeholder="如：gpt-4.1-mini" />
          </Form.Item>
          <Form.Item label="启用" name="enabled" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Collapse
            ghost
            items={[{
              key: 'advanced',
              label: '高级配置',
              children: (
                <>
                  <Form.Item label="资源 ID" name="resource_id">
                    <Input
                      disabled={Boolean(editingItem)}
                      placeholder={editingItem ? '资源 ID 不可编辑' : '留空自动生成，例如：provider:qwen_vl_prod'}
                    />
                  </Form.Item>
                  <Form.Item label="Timeout (s)" name="timeout_seconds">
                    <InputNumber style={{ width: '100%' }} min={1} max={600} />
                  </Form.Item>
                  <Form.Item label="Temperature" name="temperature">
                    <InputNumber style={{ width: '100%' }} min={0} max={5} step={0.1} />
                  </Form.Item>
                  <Form.Item label="Max Tokens" name="max_tokens">
                    <InputNumber style={{ width: '100%' }} min={1} max={65536} />
                  </Form.Item>
                  <Form.Item label="Extra Headers JSON" name="extra_headers_text">
                    <Input.TextArea rows={4} placeholder='如：{"Authorization":"Bearer xxx"}' />
                  </Form.Item>
                  <Form.Item label="Extra Config JSON" name="extra_json_text">
                    <Input.TextArea rows={4} placeholder='如：{"response_format":"b64_json"}' />
                  </Form.Item>
                </>
              ),
            }]}
          />
        </Form>
      </Drawer>
    </div>
  );
};

export default AiPipelineProviderManagementPage;
