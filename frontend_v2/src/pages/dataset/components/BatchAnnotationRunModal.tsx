import React from 'react';
import { PlayCircleOutlined } from '@ant-design/icons';
import { Alert, Button, Divider, Form, Input, InputNumber, Modal, Select, Spin, Switch, Tag, Typography, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { listAnnotations } from '../../../api/annotation';
import { createBatchAnnotationRun } from '../../../api/batchAnnotation';
import { listDatasets } from '../../../api/dataset';
import { emitBatchAnnotationRunsChanged } from '../../../utils/projectEvents';
import {
  DataTypeLabels,
  DataTypeOptions,
  type AiPipelineBatchScript,
  type AnnotationProject,
  type Dataset,
} from '../../../types';

const { Text } = Typography;

interface BatchFormValues {
  annotation_id?: number;
  selection_mode: 'all' | 'unannotated';
  overwrite_policy: 'skip_existing' | 'overwrite_draft' | 'overwrite_all';
  batch_size: number;
  script_params: Record<string, string | number | boolean | undefined>;
}

interface BatchAnnotationRunModalProps {
  open: boolean;
  script: AiPipelineBatchScript | null;
  onClose: () => void;
}

const scriptDefaults = (script: AiPipelineBatchScript): BatchFormValues['script_params'] => Object.fromEntries(
  script.parameter_fields
    .filter((field) => field.default_value !== undefined)
    .map((field) => [field.key, field.default_value]),
);

const BatchAnnotationRunModal: React.FC<BatchAnnotationRunModalProps> = ({ open, script, onClose }) => {
  const navigate = useNavigate();
  const [form] = Form.useForm<BatchFormValues>();
  const [loadingDatasets, setLoadingDatasets] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [dataType, setDataType] = React.useState<number | undefined>();
  const [datasets, setDatasets] = React.useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = React.useState<number | undefined>();
  const [annotations, setAnnotations] = React.useState<AnnotationProject[]>([]);

  const selectedAnnotationId = Form.useWatch('annotation_id', form);
  const selectedDataset = datasets.find((dataset) => dataset.id === selectedDatasetId);
  const selectedAnnotation = annotations.find((annotation) => annotation.id === selectedAnnotationId);
  const compatibleAnnotations = annotations.filter((annotation) => (
    script?.supported_annotation_types.includes(annotation.annotation_type)
  ));

  React.useEffect(() => {
    if (!open || !script) return;
    form.resetFields();
    form.setFieldsValue({
      selection_mode: 'unannotated',
      overwrite_policy: 'skip_existing',
      batch_size: 20,
      script_params: scriptDefaults(script),
    });
    setDataType(script.supported_data_types[0]);
    setSelectedDatasetId(undefined);
    setDatasets([]);
    setAnnotations([]);
  }, [form, open, script]);

  React.useEffect(() => {
    if (!open || dataType === undefined) return;
    let canceled = false;
    const loadDatasets = async () => {
      setLoadingDatasets(true);
      try {
        const firstPage = await listDatasets(1, 100, undefined, dataType);
        const remainingPages = await Promise.all(
          Array.from({ length: Math.max((firstPage?.pages ?? 1) - 1, 0) }, (_, index) => listDatasets(index + 2, 100, undefined, dataType)),
        );
        if (!canceled) setDatasets([...(firstPage?.items ?? []), ...remainingPages.flatMap((page) => page?.items ?? [])]);
      } catch {
        if (!canceled) message.error('加载数据集失败');
      } finally {
        if (!canceled) setLoadingDatasets(false);
      }
    };
    void loadDatasets();
    return () => { canceled = true; };
  }, [dataType, open]);

  React.useEffect(() => {
    if (!open || !selectedDatasetId) {
      setAnnotations([]);
      form.setFieldValue('annotation_id', undefined);
      return;
    }
    let canceled = false;
    const loadAnnotations = async () => {
      try {
        const firstPage = await listAnnotations(1, 100, undefined, selectedDatasetId);
        const remainingPages = await Promise.all(
          Array.from({ length: Math.max((firstPage?.pages ?? 1) - 1, 0) }, (_, index) => listAnnotations(index + 2, 100, undefined, selectedDatasetId)),
        );
        if (!canceled) setAnnotations([...(firstPage?.items ?? []), ...remainingPages.flatMap((page) => page?.items ?? [])]);
      } catch {
        if (!canceled) message.error('加载标注项目失败');
      }
    };
    void loadAnnotations();
    return () => { canceled = true; };
  }, [form, open, selectedDatasetId]);

  const handleDataTypeChange = (nextDataType: number) => {
    setDataType(nextDataType);
    setSelectedDatasetId(undefined);
    setAnnotations([]);
    form.setFieldValue('annotation_id', undefined);
  };

  const handleStart = async (values: BatchFormValues) => {
    if (!script || !selectedDatasetId || !values.annotation_id) return;
    setSubmitting(true);
    try {
      const run = await createBatchAnnotationRun({
        dataset_id: selectedDatasetId,
        annotation_id: values.annotation_id,
        script_key: script.key,
        selection_mode: values.selection_mode,
        overwrite_policy: values.overwrite_policy,
        script_params: values.script_params ?? {},
        batch_size: values.batch_size,
        parallelism: 1,
      });
      if (!run) throw new Error('任务创建失败');
      emitBatchAnnotationRunsChanged();
      onClose();
      message.success('批量标注任务已创建');
      navigate(`/batch-annotation/runs/${run.run_id}`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '创建批量标注任务失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      open={open}
      title={script ? <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span>{script.name}</span><Tag>v{script.version}</Tag></div> : '配置并执行'}
      width={760}
      destroyOnClose
      footer={null}
      onCancel={() => { if (!submitting) onClose(); }}
      styles={{ body: { maxHeight: 'calc(100vh - 180px)', overflowY: 'auto', paddingTop: 12 } }}
    >
      {!script ? <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}><Spin /></div> : (
        <Form<BatchFormValues> form={form} layout="vertical" onFinish={handleStart}>
          <Text type="secondary" style={{ display: 'block', marginBottom: 18 }}>{script.description || '按脚本包声明的参数创建一次批量标注任务'}</Text>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0 16px' }}>
            <Form.Item label="数据类型">
              <Select
                value={dataType}
                onChange={handleDataTypeChange}
                options={DataTypeOptions
                  .filter((item) => script.supported_data_types.includes(item.value))
                  .map((item) => ({ label: item.label, value: item.value }))}
              />
            </Form.Item>
            <Form.Item label="数据集" required>
              <Select
                value={selectedDatasetId}
                loading={loadingDatasets}
                placeholder="选择数据集"
                onChange={setSelectedDatasetId}
                options={datasets.map((dataset) => ({ label: `${dataset.name} (${dataset.count})`, value: dataset.id }))}
              />
            </Form.Item>
          </div>
          {selectedDataset ? <Text type="secondary" style={{ display: 'block', marginTop: -14, marginBottom: 16 }}>{DataTypeLabels[selectedDataset.data_type]} · {selectedDataset.count} 个样本</Text> : null}
          <Form.Item name="annotation_id" label="写入标注项目" rules={[{ required: true, message: '请选择标注项目' }]}>
            <Select
              disabled={!selectedDatasetId}
              placeholder={selectedDatasetId ? '选择标注项目' : '请先选择数据集'}
              options={compatibleAnnotations.map((item) => ({ label: `${item.name} · 类型 ${item.annotation_type}`, value: item.id }))}
            />
          </Form.Item>
          {selectedDatasetId && compatibleAnnotations.length === 0 ? <Alert style={{ marginBottom: 16 }} type="warning" showIcon message="当前数据集没有该工具兼容的标注项目" /> : null}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '0 16px' }}>
            <Form.Item name="selection_mode" label="执行范围">
              <Select options={[{ label: '仅未标注样本', value: 'unannotated' }, { label: '全部样本', value: 'all' }]} />
            </Form.Item>
            <Form.Item name="overwrite_policy" label="已有标注处理">
              <Select options={[{ label: '跳过已有结果', value: 'skip_existing' }, { label: '仅覆盖草稿', value: 'overwrite_draft' }, { label: '覆盖全部', value: 'overwrite_all' }]} />
            </Form.Item>
            <Form.Item name="batch_size" label="单批样本数">
              <InputNumber min={1} max={100} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          {script.parameter_fields.length > 0 ? <Divider style={{ margin: '6px 0 18px' }}>脚本参数</Divider> : null}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0 16px' }}>
            {script.parameter_fields.map((field) => (
              <Form.Item
                key={field.key}
                name={['script_params', field.key]}
                label={field.label}
                extra={field.description}
                valuePropName={field.value_type === 'boolean' ? 'checked' : 'value'}
                rules={field.required ? [{ required: true, message: `请填写${field.label}` }] : undefined}
              >
                {field.value_type === 'number' ? <InputNumber style={{ width: '100%' }} />
                  : field.value_type === 'boolean' ? <Switch />
                    : field.value_type === 'select' ? <Select options={(field.options ?? []).map((option) => ({ label: String(option), value: option }))} />
                      : field.value_type === 'secret' ? <Input.Password autoComplete="new-password" />
                        : <Input />}
              </Form.Item>
            ))}
          </div>

          <Divider style={{ margin: '8px 0 16px' }} />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
            <Button onClick={onClose} disabled={submitting}>取消</Button>
            <Button type="primary" htmlType="submit" icon={<PlayCircleOutlined />} loading={submitting} disabled={!selectedDatasetId || !selectedAnnotation}>创建并执行</Button>
          </div>
        </Form>
      )}
    </Modal>
  );
};

export default BatchAnnotationRunModal;
