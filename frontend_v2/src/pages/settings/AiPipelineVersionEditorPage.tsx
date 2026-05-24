import React from 'react';
import { Navigate, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeftOutlined, CloseOutlined, SaveOutlined } from '@ant-design/icons';
import {
  Button,
  Form,
  Input,
  Space,
  Spin,
  Typography,
  message,
} from 'antd';
import {
  getAiPipelineTemplateDetail,
  listAiPipelineCapabilities,
  updateAiPipelineTemplate,
} from '../../api/aiPipeline';
import type {
  AiPipelineCapabilityItem,
  AiPipelineTemplateDetail,
  AiPipelineTemplateDraftSaveRequest,
} from '../../types';
import AiPipelineVersionBuilder, {
  deriveVersionPayloadFromSteps,
} from './components/AiPipelineVersionBuilder';
import {
  parseVersionBuilderInputSchema,
  parseVersionBuilderGraphFromTemplate,
  parseVersionBuilderStepsFromTemplate,
  validateVersionBuilderSteps,
  type VersionBuilderFormValues,
} from './components/aiPipelineVersionBuilderHelpers';

const { Text } = Typography;

const buildVersionPayloadJson = (
  template: AiPipelineTemplateDetail,
  values: VersionBuilderFormValues,
  capabilities: AiPipelineCapabilityItem[],
) => {
  const derived = deriveVersionPayloadFromSteps(values.steps ?? [], capabilities, values.graph);
  const resourceSlots = Object.fromEntries(derived.resourceSlots.map((item) => [
    String(item.key),
    {
      label: item.label,
      required: item.required === true,
      default_value: item.default_value,
      widget: 'resource-select',
      widget_props: (item as Record<string, unknown>).widget_props ?? {
        resource_type: (item as Record<string, unknown>).resource_type,
        task_kind: (item as Record<string, unknown>).task_kind,
        deployed_only: (item as Record<string, unknown>).deployed_only !== false,
      },
    },
  ]));

  return {
    definition_json: {
      name: template.template_key,
      display_name: template.name,
      description: template.description,
      pipeline_type: template.scene_type || 'generic',
      enabled: true,
      template_key: template.template_key,
      scene_type: template.scene_type,
      editor_graph: values.graph,
      input_schema: values.input_schema ?? { kind: template.input_kind || 'image' },
      output_schema: { kind: template.output_kind || 'annotation_bbox' },
      runtime_inputs: derived.runtimeInputs,
      resource_slots: resourceSlots,
      steps: derived.steps,
    },
    form_schema_json: {
      runtime_inputs: derived.runtimeInputs,
      resource_slots: derived.resourceSlots.map((item) => ({
        key: item.key,
        label: item.label,
        required: item.required === true,
        default_value: item.default_value,
        widget: 'resource-select',
        value_type: 'resource_ref',
        widget_props: (item as Record<string, unknown>).widget_props ?? {
          resource_type: (item as Record<string, unknown>).resource_type,
          task_kind: (item as Record<string, unknown>).task_kind,
          deployed_only: (item as Record<string, unknown>).deployed_only !== false,
        },
      })),
    },
  };
};

const AiPipelineVersionEditorPage: React.FC = () => {
  const navigate = useNavigate();
  const params = useParams<{ templateKey?: string }>();
  const [searchParams] = useSearchParams();
  const [form] = Form.useForm<VersionBuilderFormValues>();
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [templateDetail, setTemplateDetail] = React.useState<AiPipelineTemplateDetail | null>(null);
  const [capabilities, setCapabilities] = React.useState<AiPipelineCapabilityItem[]>([]);
  const routeTemplateKey = params.templateKey?.trim() || '';
  const queryTemplateKey = searchParams.get('template_key')?.trim() || '';
  const templateKey = routeTemplateKey || queryTemplateKey;

  if (!routeTemplateKey && queryTemplateKey) {
    return <Navigate to={`/ai-pipeline/editor/${encodeURIComponent(queryTemplateKey)}`} replace />;
  }

  React.useEffect(() => {
    const load = async () => {
      if (!templateKey) {
        setTemplateDetail(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const [detail, capabilityItems] = await Promise.all([
          getAiPipelineTemplateDetail(templateKey),
          listAiPipelineCapabilities(),
        ]);
        const scopedCapabilities = capabilityItems.filter((item) => (
          item.scene_types.length === 0 || item.scene_types.includes(detail.scene_type)
        ));
        const parsedSteps = parseVersionBuilderStepsFromTemplate(
          detail.definition_json,
          detail.form_schema_json,
          scopedCapabilities,
        );
        setTemplateDetail(detail);
        setCapabilities(capabilityItems);
        form.setFieldsValue({
          change_note: detail.change_note || '',
          scene_type: detail.scene_type,
          input_schema: parseVersionBuilderInputSchema(detail.definition_json, detail.input_kind),
          steps: parsedSteps,
          graph: parseVersionBuilderGraphFromTemplate(detail.definition_json, parsedSteps),
        });
      } catch (error) {
        console.error('failed to load version editor page', error);
        message.error('加载 Pipeline 编排页失败');
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [form, templateKey]);

  const closeEditorPage = React.useCallback(() => {
    if (window.opener && !window.opener.closed) {
      window.close();
      return;
    }
    navigate('/ai-pipeline');
  }, [navigate]);

  const handleSubmit = async () => {
    if (!templateDetail || !templateKey) return;
    try {
      await form.validateFields();
      const values = form.getFieldsValue(true) as VersionBuilderFormValues;
      const validationIssues = validateVersionBuilderSteps(values.steps ?? [], values.graph);
      if (validationIssues.length > 0) {
        message.error(validationIssues[0].message);
        return;
      }
      const { definition_json, form_schema_json } = buildVersionPayloadJson(
        templateDetail,
        values,
        capabilities.filter((item) => item.scene_types.length === 0 || item.scene_types.includes(templateDetail.scene_type)),
      );
      const payload: AiPipelineTemplateDraftSaveRequest = {
        change_note: values.change_note?.trim(),
        definition_json,
        form_schema_json,
      };
      setSaving(true);
      const savedTemplate = await updateAiPipelineTemplate(templateKey, payload);
      setTemplateDetail(savedTemplate);
      message.success('Pipeline 已保存');
    } catch (error) {
      if (error instanceof Error && error.message) {
        message.error(error.message);
      }
    } finally {
      setSaving(false);
    }
  };

  if (!loading && !templateDetail) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8fafc' }}>
        <Text type="secondary">模板不存在或加载失败</Text>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#f8fafc' }}>
      <Form form={form} layout="vertical" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        {loading || !templateDetail ? (
          <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8fafc' }}>
            <Spin size="large" />
          </div>
        ) : (
          <>
            <div style={{ height: 72, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', borderBottom: '1px solid #e2e8f0', background: '#ffffff' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}>
                <div style={{ width: 40, height: 40, borderRadius: 12, border: '1px solid #dbe3ef', background: '#f8fafc', color: '#475569', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <SaveOutlined />
                </div>
                <div>
                  <div className="page-title" style={{ fontSize: 22, lineHeight: '30px' }}>{templateDetail.name}</div>
                  <div className="page-subtitle" style={{ marginTop: 2 }}>
                    {templateDetail.template_key} · {templateDetail.scene_type}
                  </div>
                </div>
              </div>
              <Space>
                <Form.Item name="change_note" style={{ marginBottom: 0 }}>
                  <Input
                    style={{ width: 300 }}
                    placeholder="变更说明，如：新增视觉检测节点"
                  />
                </Form.Item>
                <Button icon={<CloseOutlined />} onClick={closeEditorPage}>
                  关闭
                </Button>
                <Button type="primary" loading={saving} onClick={() => void handleSubmit()}>
                  保存
                </Button>
              </Space>
            </div>
            <div style={{ height: 52, display: 'flex', alignItems: 'center', gap: 18, padding: '0 24px', borderBottom: '1px solid #e2e8f0', background: '#ffffff' }}>
              <div className="caption-text" style={{ color: '#64748b' }}>输入</div>
              <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 600 }}>{templateDetail.input_kind || '-'}</div>
              <div className="caption-text" style={{ color: '#64748b' }}>输出</div>
              <div className="body-text-sm" style={{ color: '#0f172a', fontWeight: 600 }}>{templateDetail.output_kind || '-'}</div>
              <Button type="link" icon={<ArrowLeftOutlined />} onClick={() => navigate('/ai-pipeline')} style={{ padding: 0, marginLeft: 'auto' }}>
                返回模板列表
              </Button>
            </div>

            <AiPipelineVersionBuilder
              form={form}
              capabilities={capabilities}
              capabilitiesLoading={false}
            />
          </>
        )}
      </Form>
    </div>
  );
};

export default AiPipelineVersionEditorPage;
