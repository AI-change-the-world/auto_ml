import React, { useEffect, useState } from 'react';
import { SettingOutlined, CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { Button, Form, Input, InputNumber, Switch, message } from 'antd';
import { useTranslation } from 'react-i18next';
import apiClient from '../../api/client';
import { getAssistantConfig, updateAssistantConfig } from '../../api/assistant';
import {
  getAnnotationDeleteConfirmEnabled,
  getDatasetDeleteConfirmEnabled,
  getDeployConfirmEnabled,
  getTaskDeleteConfirmEnabled,
  setAnnotationDeleteConfirmEnabled,
  setDatasetDeleteConfirmEnabled,
  setDeployConfirmEnabled,
  setTaskDeleteConfirmEnabled,
} from '../../utils/localSettings';
import type { AssistantConfigUpdateRequest } from '../../types';

type ModuleState = 'enabled' | 'unavailable' | 'disabled';

type HealthResponse = {
  status: string;
  service: string;
  version?: string;
  modules?: Partial<Record<'dataset_mgmt' | 'annotation_mgmt' | 'train_task' | 'model_deploy' | 'predict_service' | 'user_mgmt', ModuleState>>;
  dependencies?: Partial<Record<'model_trainer' | 'model_deploy' | 'ai_pipeline_runtime', {
    status: ModuleState;
    version?: string | null;
  }>>;
};

type AssistantFormValues = AssistantConfigUpdateRequest;

const getConfiguredApiBaseUrl = () => {
  const base = import.meta.env.VITE_API_BASE_URL || '/api';
  if (/^https?:\/\//i.test(base)) {
    return base.replace(/\/+$/, '');
  }
  return new URL(base, window.location.origin).toString().replace(/\/+$/, '');
};

const SettingsPage: React.FC = () => {
  const { t } = useTranslation('settings');
  const tc = useTranslation('common').t;
  const [assistantForm] = Form.useForm<AssistantFormValues>();
  const [backendVersion, setBackendVersion] = useState<string>('-');
  const [platformName, setPlatformName] = useState<string>('AutoML Studio');
  const [datasetDeleteConfirmEnabled, setDatasetDeleteConfirmEnabledState] = useState(true);
  const [annotationDeleteConfirmEnabled, setAnnotationDeleteConfirmEnabledState] = useState(true);
  const [taskDeleteConfirmEnabled, setTaskDeleteConfirmEnabledState] = useState(true);
  const [deployConfirmEnabled, setDeployConfirmEnabledState] = useState(true);
  const [moduleStatusMap, setModuleStatusMap] = useState<Record<string, ModuleState>>({
    dataset_mgmt: 'enabled',
    annotation_mgmt: 'enabled',
    train_task: 'enabled',
    model_deploy: 'enabled',
    predict_service: 'enabled',
    user_mgmt: 'disabled',
  });
  const [dependencyMap, setDependencyMap] = useState<NonNullable<HealthResponse['dependencies']>>({});
  const [assistantLoading, setAssistantLoading] = useState(true);
  const [assistantSaving, setAssistantSaving] = useState(false);
  const [assistantApiKeyConfigured, setAssistantApiKeyConfigured] = useState(false);

  const modules = [
    { key: 'dataset_mgmt', name: t('datasetMgmt') },
    { key: 'annotation_mgmt', name: t('annotationMgmt') },
    { key: 'train_task', name: t('trainTask') },
    { key: 'model_deploy', name: t('modelDeploy') },
    { key: 'user_mgmt', name: t('userMgmt') },
    { key: 'predict_service', name: t('predictService') },
  ];
  const dependencyRows = [
    { key: 'model_trainer', label: t('trainTask') },
    { key: 'model_deploy', label: t('modelDeploy') },
    { key: 'ai_pipeline_runtime', label: t('aiPipelineRuntime') },
  ] as const;
  const apiBaseUrl = getConfiguredApiBaseUrl();

  useEffect(() => {
    let active = true;
    setDatasetDeleteConfirmEnabledState(getDatasetDeleteConfirmEnabled());
    setAnnotationDeleteConfirmEnabledState(getAnnotationDeleteConfirmEnabled());
    setTaskDeleteConfirmEnabledState(getTaskDeleteConfirmEnabled());
    setDeployConfirmEnabledState(getDeployConfirmEnabled());

    const loadHealth = async () => {
      try {
        const response = await apiClient.get<HealthResponse>('/health');
        if (!active) return;
        setBackendVersion(response.data.version || '-');
        setPlatformName(response.data.service || 'AutoML Studio');
        if (response.data.modules) {
          setModuleStatusMap((prev) => ({
            ...prev,
            ...response.data.modules,
          }));
        }
        if (response.data.dependencies) {
          setDependencyMap((prev) => ({
            ...prev,
            ...response.data.dependencies,
          }));
        }
      } catch {
        if (!active) return;
        setBackendVersion('-');
        setPlatformName('AutoML Studio');
      }
    };

    void loadHealth();
    const loadAssistantConfig = async () => {
      try {
        const config = await getAssistantConfig();
        if (!active) return;
        setAssistantApiKeyConfigured(config?.api_key_configured === true);
        assistantForm.setFieldsValue({
          enabled: config?.enabled === true,
          base_url: config?.base_url || undefined,
          api_key: undefined,
          model: config?.model || undefined,
          timeout_seconds: config?.timeout_seconds ?? 60,
          temperature: config?.temperature ?? 0.2,
          max_tokens: config?.max_tokens ?? 2048,
          system_prompt: config?.system_prompt || undefined,
        });
      } catch {
        if (!active) return;
        message.error('加载智能助手配置失败');
      } finally {
        if (active) setAssistantLoading(false);
      }
    };
    void loadAssistantConfig();
    return () => {
      active = false;
    };
  }, [assistantForm]);

  const handleConfirmDeleteChange = (
    checked: boolean,
    setter: React.Dispatch<React.SetStateAction<boolean>>,
    persist: (enabled: boolean) => void,
    label: string,
  ) => {
    setter(checked);
    persist(checked);
    message.success(`${label}${checked ? '已开启确认' : '已关闭确认'}`);
  };

  const handleAssistantSave = async () => {
    try {
      const values = await assistantForm.validateFields();
      setAssistantSaving(true);
      const config = await updateAssistantConfig({
        ...values,
        base_url: values.base_url?.trim() || undefined,
        api_key: values.api_key?.trim() || undefined,
        model: values.model?.trim() || undefined,
        system_prompt: values.system_prompt?.trim() || undefined,
      });
      setAssistantApiKeyConfigured(config?.api_key_configured === true);
      assistantForm.setFieldValue('api_key', undefined);
      message.success('智能助手配置已保存');
    } catch (error) {
      if (error instanceof Error && error.message) {
        message.error(error.message);
      }
    } finally {
      setAssistantSaving(false);
    }
  };

  return (
    <div className="page-container" style={{ maxWidth: 700 }}>
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-title-icon">
            <SettingOutlined />
          </div>
          <div>
            <h1 className="page-title">{t('title')}</h1>
          </div>
        </div>
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24, marginBottom: 20 }}>
        <h3 className="card-title" style={{ marginBottom: 16 }}>{t('systemInfo')}</h3>
        {[
          { label: t('platformName'), value: platformName },
          { label: t('version'), value: backendVersion },
          { label: t('apiAddress'), value: apiBaseUrl, mono: true },
          { label: t('backendProxy'), value: apiBaseUrl, mono: true },
        ].map((item, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: i < 3 ? '1px solid #f8f8f8' : 'none' }}>
            <span className="body-text-sm" style={{ color: '#888' }}>{item.label}</span>
            <span className="body-text-sm" style={{ color: '#111', fontFamily: item.mono ? 'monospace' : 'inherit', background: item.mono ? '#f7f7f8' : 'none', padding: item.mono ? '2px 8px' : 0, borderRadius: 4 }}>{item.value}</span>
          </div>
          ))}
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24, marginBottom: 20 }}>
        <h3 className="card-title" style={{ marginBottom: 16 }}>{t('serviceVersions')}</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 10 }}>
          {dependencyRows.map((item) => {
            const detail = dependencyMap[item.key];
            const version = detail?.version || '-';
            const status = detail?.status || 'unavailable';
            const versionText = version === '-' ? '-' : `v${version}`;
            return (
              <div key={item.key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#fafafa', borderRadius: 8 }}>
                <span className="body-text-sm" style={{ color: '#555' }}>{item.label}</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className="body-text-sm" style={{ color: '#111', fontFamily: 'monospace' }}>{versionText}</span>
                  {status === 'enabled' ? (
                    <span className="caption-text" style={{ color: '#16a34a', display: 'flex', alignItems: 'center', gap: 4 }}>{tc('status.enabled')}</span>
                  ) : (
                    <span className="caption-text" style={{ color: '#dc2626', display: 'flex', alignItems: 'center', gap: 4 }}>{tc('status.notAvailable')}</span>
                  )}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24, marginBottom: 20 }}>
        <h3 className="card-title" style={{ marginBottom: 16 }}>删除确认</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 12, alignItems: 'center' }}>
          <span className="body-text-sm" style={{ color: '#555' }}>数据集删除需要确认</span>
          <Switch checked={datasetDeleteConfirmEnabled} onChange={(checked) => handleConfirmDeleteChange(checked, setDatasetDeleteConfirmEnabledState, setDatasetDeleteConfirmEnabled, '数据集删除')} />
          <span className="body-text-sm" style={{ color: '#555' }}>标注删除需要确认</span>
          <Switch checked={annotationDeleteConfirmEnabled} onChange={(checked) => handleConfirmDeleteChange(checked, setAnnotationDeleteConfirmEnabledState, setAnnotationDeleteConfirmEnabled, '标注删除')} />
          <span className="body-text-sm" style={{ color: '#555' }}>任务删除需要确认</span>
          <Switch checked={taskDeleteConfirmEnabled} onChange={(checked) => handleConfirmDeleteChange(checked, setTaskDeleteConfirmEnabledState, setTaskDeleteConfirmEnabled, '任务删除')} />
          <span className="body-text-sm" style={{ color: '#555' }}>部署下线需要确认</span>
          <Switch checked={deployConfirmEnabled} onChange={(checked) => handleConfirmDeleteChange(checked, setDeployConfirmEnabledState, setDeployConfirmEnabled, '部署下线')} />
        </div>
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 6, padding: 24, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, marginBottom: 16 }}>
          <div>
            <h3 className="card-title" style={{ marginBottom: 4 }}>智能助手</h3>
            <div className="body-text-sm" style={{ color: '#888' }}>API Key 仅在保存时提交，服务端加密保存且不会读取回显。</div>
          </div>
          <Button type="primary" loading={assistantSaving} disabled={assistantLoading} onClick={() => void handleAssistantSave()}>
            保存配置
          </Button>
        </div>
        <Form form={assistantForm} layout="vertical" disabled={assistantLoading}>
          <Form.Item label="启用智能助手" name="enabled" valuePropName="checked" style={{ marginBottom: 16 }}>
            <Switch />
          </Form.Item>
          <Form.Item label="Base URL" name="base_url">
            <Input placeholder="如：https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item label="API Key" name="api_key" extra={assistantApiKeyConfigured ? '密钥已配置，留空会保留当前值。' : '首次启用时需要填写。'}>
            <Input.Password autoComplete="new-password" placeholder={assistantApiKeyConfigured ? '留空保持当前密钥' : '请输入 API Key'} />
          </Form.Item>
          <Form.Item label="模型名称" name="model">
            <Input placeholder="如：gpt-4.1-mini、qwen-plus、deepseek-chat" />
          </Form.Item>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
            <Form.Item label="超时（秒）" name="timeout_seconds" rules={[{ required: true }]}>
              <InputNumber min={1} max={600} precision={0} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="Temperature" name="temperature" rules={[{ required: true }]}>
              <InputNumber min={0} max={5} step={0.1} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="最大输出 Token" name="max_tokens" rules={[{ required: true }]}>
              <InputNumber min={1} max={65536} precision={0} style={{ width: '100%' }} />
            </Form.Item>
          </div>
          <Form.Item label="系统提示词" name="system_prompt" style={{ marginBottom: 0 }}>
            <Input.TextArea rows={4} placeholder="留空时使用平台默认助手提示词" />
          </Form.Item>
        </Form>
      </div>

      <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24 }}>
        <h3 className="card-title" style={{ marginBottom: 16 }}>{t('modules')}</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {modules.map((m, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#fafafa', borderRadius: 8 }}>
              <span className="body-text-sm" style={{ color: '#555' }}>{m.name}</span>
              {moduleStatusMap[m.key] === 'enabled' ? (
                <span className="caption-text" style={{ color: '#16a34a', display: 'flex', alignItems: 'center', gap: 4 }}><CheckCircleOutlined /> {tc('status.enabled')}</span>
              ) : moduleStatusMap[m.key] === 'unavailable' ? (
                <span className="caption-text" style={{ color: '#dc2626', display: 'flex', alignItems: 'center', gap: 4 }}><CloseCircleOutlined /> {tc('status.notAvailable')}</span>
              ) : (
                <span className="caption-text" style={{ color: '#bbb', display: 'flex', alignItems: 'center', gap: 4 }}><ClockCircleOutlined /> {tc('status.pending')}</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
