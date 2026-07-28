import React from 'react';
import { PlayCircleOutlined, SearchOutlined, UploadOutlined } from '@ant-design/icons';
import { Button, Card, Empty, Input, Select, Spin, Tag, Typography, message } from 'antd';
import { listBatchAnnotationScripts } from '../../api/batchAnnotation';
import { DataTypeLabels, DataTypeOptions, type AiPipelineBatchScript } from '../../types';
import BatchAnnotationRunModal from './components/BatchAnnotationRunModal';
import BatchScriptEditorModal from './components/BatchScriptEditorModal';

const { Text } = Typography;

const annotationTypeLabels: Record<number, string> = {
  0: '检测', 1: '分类', 2: '分割', 3: '多模态对话', 4: '姿态', 5: '文本对话',
  6: 'DPO', 7: 'DPO 二选一', 8: 'DPO 多选一', 9: 'DPO 参考增强', 10: 'DPO 多轮',
};

const BatchAnnotationToolListPage: React.FC = () => {
  const [loading, setLoading] = React.useState(true);
  const [scripts, setScripts] = React.useState<AiPipelineBatchScript[]>([]);
  const [dataType, setDataType] = React.useState<number | undefined>();
  const [keyword, setKeyword] = React.useState('');
  const [selectedScript, setSelectedScript] = React.useState<AiPipelineBatchScript | null>(null);
  const [uploadOpen, setUploadOpen] = React.useState(false);

  const loadScripts = React.useCallback(async () => {
    setLoading(true);
    try {
      setScripts(await listBatchAnnotationScripts());
    } catch {
      message.error('加载批量标注工具失败');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => { void loadScripts(); }, [loadScripts]);

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
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
          {visibleScripts.map((script) => (
            <Card
              key={script.key}
              size="small"
              styles={{ body: { minHeight: 184, display: 'flex', flexDirection: 'column', padding: 16 } }}
              style={{ borderRadius: 6, boxShadow: 'none', borderColor: '#e5e7eb' }}
            >
              <div style={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between', gap: 12 }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{script.name}</div>
                  <Text type="secondary" style={{ fontSize: 12 }}>v{script.version} · {script.is_builtin ? '内置' : '脚本包'}</Text>
                </div>
                <Tag color={script.is_builtin ? 'default' : 'blue'}>{script.parameter_fields.length} 参数</Tag>
              </div>
              <Text type="secondary" style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', marginTop: 10, minHeight: 40 }}>{script.description || '暂无说明'}</Text>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 12 }}>
                {script.supported_data_types.map((type) => <Tag key={`data-${type}`}>{DataTypeLabels[type] ?? type}</Tag>)}
                {script.supported_annotation_types.map((type) => <Tag key={`annotation-${type}`} color="cyan">{annotationTypeLabels[type] ?? `类型 ${type}`}</Tag>)}
              </div>
              <Button type="primary" icon={<PlayCircleOutlined />} style={{ marginTop: 'auto' }} onClick={() => setSelectedScript(script)}>配置并执行</Button>
            </Card>
          ))}
        </div>
      )}
      <BatchAnnotationRunModal open={selectedScript !== null} script={selectedScript} onClose={() => setSelectedScript(null)} />
      <BatchScriptEditorModal open={uploadOpen} onClose={() => setUploadOpen(false)} onSubmitted={() => { void loadScripts(); }} />
    </div>
  );
};

export default BatchAnnotationToolListPage;
