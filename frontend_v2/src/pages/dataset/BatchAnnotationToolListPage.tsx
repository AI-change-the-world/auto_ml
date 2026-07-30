import React from 'react';
import { DeleteOutlined, EditOutlined, InfoCircleOutlined, PauseCircleOutlined, PlayCircleOutlined, SaveOutlined, SearchOutlined, UploadOutlined } from '@ant-design/icons';
import { Button, Card, Descriptions, Drawer, Empty, Input, Popconfirm, Select, Spin, Tag, Tooltip, Typography, message } from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { deleteBatchAnnotationScript, getBatchAnnotationScript, listBatchAnnotationScripts, updateBatchAnnotationScript } from '../../api/batchAnnotation';
import { DataTypeLabels, DataTypeOptions, type AiPipelineBatchScript } from '../../types';
import BatchAnnotationRunModal from './components/BatchAnnotationRunModal';
import BatchScriptEditorModal from './components/BatchScriptEditorModal';

const { Text } = Typography;

const annotationTypeLabels: Record<number, string> = {
  0: '检测', 1: '分类', 2: '分割', 3: '多模态对话', 4: '姿态', 5: '文本对话',
  6: 'DPO', 7: 'DPO 二选一', 8: 'DPO 多选一', 9: 'DPO 参考增强', 10: 'DPO 多轮',
};

interface EditableScriptDetail {
  name: string;
  description: string;
  readmeMarkdown: string;
}

function toEditableDetail(script: AiPipelineBatchScript): EditableScriptDetail {
  return {
    name: script.name,
    description: script.description ?? '',
    readmeMarkdown: script.readme_markdown ?? '',
  };
}

const BatchAnnotationToolListPage: React.FC = () => {
  const [loading, setLoading] = React.useState(true);
  const [scripts, setScripts] = React.useState<AiPipelineBatchScript[]>([]);
  const [dataType, setDataType] = React.useState<number | undefined>();
  const [keyword, setKeyword] = React.useState('');
  const [selectedScript, setSelectedScript] = React.useState<AiPipelineBatchScript | null>(null);
  const [loadingScriptKey, setLoadingScriptKey] = React.useState<string | null>(null);
  const [updatingScriptKey, setUpdatingScriptKey] = React.useState<string | null>(null);
  const [deletingScriptKey, setDeletingScriptKey] = React.useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = React.useState(false);
  const [detailOpen, setDetailOpen] = React.useState(false);
  const [detailLoading, setDetailLoading] = React.useState(false);
  const [detailSaving, setDetailSaving] = React.useState(false);
  const [detailEditing, setDetailEditing] = React.useState(false);
  const [detailScript, setDetailScript] = React.useState<AiPipelineBatchScript | null>(null);
  const [detailDraft, setDetailDraft] = React.useState<EditableScriptDetail>({ name: '', description: '', readmeMarkdown: '' });

  const loadScripts = React.useCallback(async () => {
    setLoading(true);
    try {
      setScripts(await listBatchAnnotationScripts(true));
    } catch {
      message.error('加载批量标注工具失败');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => { void loadScripts(); }, [loadScripts]);

  const handleConfigure = async (scriptKey: string) => {
    setLoadingScriptKey(scriptKey);
    try {
      const script = await getBatchAnnotationScript(scriptKey);
      if (!script) throw new Error('工具详情不存在');
      setSelectedScript(script);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '加载工具参数失败');
    } finally {
      setLoadingScriptKey(null);
    }
  };

  const handleEnabledChange = async (script: AiPipelineBatchScript) => {
    setUpdatingScriptKey(script.key);
    try {
      const updatedScript = await updateBatchAnnotationScript(script.key, { enabled: !script.enabled });
      if (!updatedScript) throw new Error('工具状态更新失败');
      setScripts((currentScripts) => currentScripts.map((item) => (
        item.key === updatedScript.key ? updatedScript : item
      )));
      message.success(script.enabled ? '工具已禁用' : '工具已启用');
    } catch (error) {
      message.error(error instanceof Error ? error.message : '更新工具状态失败');
    } finally {
      setUpdatingScriptKey(null);
    }
  };

  const handleOpenDetail = async (scriptKey: string) => {
    setDetailOpen(true);
    setDetailLoading(true);
    setDetailEditing(false);
    setDetailScript(null);
    try {
      const script = await getBatchAnnotationScript(scriptKey);
      if (!script) throw new Error('工具详情不存在');
      setDetailScript(script);
      setDetailDraft(toEditableDetail(script));
    } catch (error) {
      message.error(error instanceof Error ? error.message : '加载工具详情失败');
      setDetailOpen(false);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDeleteScript = async (script: AiPipelineBatchScript) => {
    setDeletingScriptKey(script.key);
    try {
      await deleteBatchAnnotationScript(script.key);
      setScripts((currentScripts) => currentScripts.filter((item) => item.key !== script.key));
      if (detailScript?.key === script.key) {
        setDetailOpen(false);
        setDetailScript(null);
      }
      message.success('脚本已删除');
    } catch (error) {
      message.error(error instanceof Error ? error.message : '删除脚本失败');
    } finally {
      setDeletingScriptKey(null);
    }
  };

  const handleSaveDetail = async () => {
    if (!detailScript) return;
    if (!detailDraft.name.trim()) {
      message.error('工具名称不能为空');
      return;
    }
    setDetailSaving(true);
    try {
      const updatedScript = await updateBatchAnnotationScript(detailScript.key, {
        name: detailDraft.name.trim(),
        description: detailDraft.description.trim() || null,
        readme_markdown: detailDraft.readmeMarkdown || null,
      });
      if (!updatedScript) throw new Error('保存工具详情失败');
      setDetailScript(updatedScript);
      setDetailDraft(toEditableDetail(updatedScript));
      setDetailEditing(false);
      setScripts((currentScripts) => currentScripts.map((item) => (
        item.key === updatedScript.key ? { ...item, ...updatedScript, readme_markdown: undefined } : item
      )));
      message.success('工具详情已保存');
    } catch (error) {
      message.error(error instanceof Error ? error.message : '保存工具详情失败');
    } finally {
      setDetailSaving(false);
    }
  };

  const visibleScripts = React.useMemo(() => scripts.filter((script) => (
    (dataType === undefined || script.supported_data_types.includes(dataType))
    && (!keyword.trim() || `${script.name} ${script.description ?? ''} ${script.key}`.toLowerCase().includes(keyword.trim().toLowerCase()))
  )), [dataType, keyword, scripts]);

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 className="page-title" style={{ margin: 0 }}>批量标注工具</h1>
          <Text type="secondary">选择工具后配置数据集与运行参数</Text>
        </div>
        <Button type="primary" icon={<UploadOutlined />} onClick={() => setUploadOpen(true)}>上传脚本包</Button>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 18 }}>
        <Select
          value={dataType}
          allowClear
          placeholder="全部数据类型"
          style={{ width: 200 }}
          onChange={setDataType}
          options={DataTypeOptions.map((item) => ({ label: item.label, value: item.value }))}
        />
        <Input
          prefix={<SearchOutlined />}
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
          placeholder="搜索工具"
          style={{ width: 280 }}
        />
      </div>

      {loading ? <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 120 }}><Spin /></div> : visibleScripts.length === 0 ? <Empty description="没有匹配的批量标注工具" /> : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', alignItems: 'stretch', gap: 14 }}>
          {visibleScripts.map((script) => (
            <Card
              key={script.key}
              size="small"
              styles={{ body: { minHeight: 220, display: 'flex', flexDirection: 'column', padding: 16 } }}
              style={{ height: '100%', borderRadius: 6, boxShadow: 'none', borderColor: '#e5e7eb' }}
            >
              <div style={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between', gap: 12 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{script.name}</div>
                  <Text type="secondary" style={{ fontSize: 12 }}>v{script.version} · {script.is_builtin ? '内置' : '脚本包'}</Text>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', flexShrink: 0, gap: 4 }}>
                  <div style={{ display: 'flex', gap: 4, whiteSpace: 'nowrap' }}>
                    <Tag color={script.enabled ? 'green' : 'default'}>{script.enabled ? '已启用' : '已禁用'}</Tag>
                    <Tag color={script.is_builtin ? 'default' : 'blue'}>{script.parameter_fields.length} 参数</Tag>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 2, height: 24 }}>
                    <Tooltip title="工具详情">
                      <Button
                        aria-label="工具详情"
                        type="text"
                        size="small"
                        icon={<InfoCircleOutlined />}
                        onClick={() => { void handleOpenDetail(script.key); }}
                      />
                    </Tooltip>
                    <Tooltip title={script.enabled ? '禁用工具' : '启用工具'}>
                      <Button
                        type="text"
                        size="small"
                        icon={script.enabled ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                        loading={updatingScriptKey === script.key}
                        onClick={() => { void handleEnabledChange(script); }}
                      />
                    </Tooltip>
                    {!script.is_builtin && (
                      <Popconfirm
                        title="删除上传脚本？"
                        description="删除后不可再创建新任务，已有任务记录不受影响。"
                        okText="删除"
                        cancelText="取消"
                        okButtonProps={{ danger: true }}
                        onConfirm={() => { void handleDeleteScript(script); }}
                      >
                        <Tooltip title="删除脚本">
                          <Button aria-label="删除脚本" type="text" size="small" danger icon={<DeleteOutlined />} loading={deletingScriptKey === script.key} />
                        </Tooltip>
                      </Popconfirm>
                    )}
                  </div>
                </div>
              </div>
              <Text type="secondary" style={{ display: 'block', height: 44, lineHeight: '22px', overflow: 'hidden', marginTop: 10 }}>{script.description || '暂无说明'}</Text>
              <div style={{ display: 'flex', flexWrap: 'wrap', alignContent: 'flex-start', gap: 4, height: 32, overflow: 'hidden', marginTop: 12 }}>
                {script.supported_data_types.map((type) => <Tag key={`data-${type}`}>{DataTypeLabels[type] ?? type}</Tag>)}
                {script.supported_annotation_types.map((type) => <Tag key={`annotation-${type}`} color="cyan">{annotationTypeLabels[type] ?? `类型 ${type}`}</Tag>)}
              </div>
              <div style={{ marginTop: 'auto', paddingTop: 14, borderTop: '1px solid #f0f0f0' }}>
                <Button
                  type="primary"
                  block
                  icon={<PlayCircleOutlined />}
                  disabled={!script.enabled}
                  loading={loadingScriptKey === script.key}
                  onClick={() => { void handleConfigure(script.key); }}
                >
                  配置并执行
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
      <BatchAnnotationRunModal open={selectedScript !== null} script={selectedScript} onClose={() => setSelectedScript(null)} />
      <BatchScriptEditorModal open={uploadOpen} onClose={() => setUploadOpen(false)} onSubmitted={() => { void loadScripts(); }} />
      <Drawer
        title={detailScript?.name || '工具详情'}
        open={detailOpen}
        width={720}
        onClose={() => { setDetailOpen(false); setDetailEditing(false); }}
        styles={{ body: { padding: 20 } }}
        extra={!detailScript?.is_builtin && !detailLoading && (detailEditing ? (
          <div style={{ display: 'flex', gap: 8 }}>
            <Button onClick={() => { if (detailScript) setDetailDraft(toEditableDetail(detailScript)); setDetailEditing(false); }}>取消</Button>
            <Button type="primary" icon={<SaveOutlined />} loading={detailSaving} onClick={() => { void handleSaveDetail(); }}>保存</Button>
          </div>
        ) : <Button icon={<EditOutlined />} onClick={() => setDetailEditing(true)}>编辑</Button>)}
      >
        {detailLoading ? <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 100 }}><Spin /></div> : detailScript && (detailEditing ? (
          <div style={{ display: 'grid', gap: 16 }}>
            <div>
              <Text strong>工具名称</Text>
              <Input value={detailDraft.name} maxLength={255} onChange={(event) => setDetailDraft((current) => ({ ...current, name: event.target.value }))} style={{ marginTop: 6 }} />
            </div>
            <div>
              <Text strong>简要说明</Text>
              <Input.TextArea value={detailDraft.description} maxLength={2000} autoSize={{ minRows: 3, maxRows: 8 }} onChange={(event) => setDetailDraft((current) => ({ ...current, description: event.target.value }))} style={{ marginTop: 6 }} />
            </div>
            <div>
              <Text strong>README.md</Text>
              <Input.TextArea value={detailDraft.readmeMarkdown} maxLength={512 * 1024} autoSize={{ minRows: 18, maxRows: 32 }} onChange={(event) => setDetailDraft((current) => ({ ...current, readmeMarkdown: event.target.value }))} style={{ marginTop: 6, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace' }} />
            </div>
          </div>
        ) : (
          <>
            <Text type="secondary">{detailScript.is_builtin ? '内置工具' : '上传脚本包'} · v{detailScript.version}</Text>
            <Descriptions size="small" column={1} style={{ margin: '16px 0 20px' }}>
              <Descriptions.Item label="脚本标识">{detailScript.key}</Descriptions.Item>
              <Descriptions.Item label="入口文件">{detailScript.entrypoint || '-'}</Descriptions.Item>
              <Descriptions.Item label="状态"><Tag color={detailScript.enabled ? 'green' : 'default'}>{detailScript.enabled ? '已启用' : '已禁用'}</Tag></Descriptions.Item>
              <Descriptions.Item label="支持数据">
                {detailScript.supported_data_types.map((type) => <Tag key={type}>{DataTypeLabels[type] ?? type}</Tag>)}
              </Descriptions.Item>
              <Descriptions.Item label="支持标注">
                {detailScript.supported_annotation_types.map((type) => <Tag key={type} color="cyan">{annotationTypeLabels[type] ?? `类型 ${type}`}</Tag>)}
              </Descriptions.Item>
            </Descriptions>
            {detailScript.description && <Text type="secondary" style={{ display: 'block', whiteSpace: 'pre-wrap', marginBottom: 20 }}>{detailScript.description}</Text>}
            <section style={{ borderTop: '1px solid #e5e7eb', paddingTop: 16 }}>
              <div style={{ fontWeight: 600, marginBottom: 12 }}>使用说明</div>
              {detailScript.readme_markdown ? (
                <div className="batch-script-readme">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{detailScript.readme_markdown}</ReactMarkdown>
                </div>
              ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="脚本包未提供 README.md" />}
            </section>
          </>
        ))}
      </Drawer>
    </div>
  );
};

export default BatchAnnotationToolListPage;
