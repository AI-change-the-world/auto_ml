import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { message, Spin, Modal, Image, Pagination, Progress } from 'antd';
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  PictureOutlined,
  InboxOutlined,
  ClockCircleOutlined,
  TagOutlined,
  ApartmentOutlined,
  CloudUploadOutlined,
  FileOutlined,
  FileZipOutlined,
  VideoCameraOutlined,
  AudioOutlined,
  FileTextOutlined,
  CheckSquareOutlined,
  BorderOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { getDataset, getDatasetSamples, uploadDatasetFiles, previewSample, deleteDataset, deleteDatasetSample } from '../../api/dataset';
import type { Dataset, SampleItem } from '../../types';
import {
  DataTypeLabels,
  DatasetScenarioType,
  getDatasetScenarioLabel,
  isAnyDpoDataset,
  isDpoBestOfNDataset,
  isDpoMultiTurnDataset,
  isDpoPairwiseDataset,
  isDpoReferenceChoiceDataset,
  isLlmConversationDataset,
  isMllmConversationDataset,
} from '../../types';
import { useTranslation } from 'react-i18next';
import { getDatasetDeleteConfirmEnabled } from '../../utils/localSettings';
import { emitDatasetsChanged } from '../../utils/projectEvents';
import { isImageFileName } from '../../utils/file';
import { getDatasetUploadRule, splitAcceptedFiles } from '../../utils/datasetUpload';

/** 获取文件图标 */
const getFileIcon = (fileName: string) => {
  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  if (['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'svg', 'ico'].includes(ext))
    return <PictureOutlined style={{ color: '#4f6ef7' }} />;
  if (['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'].includes(ext))
    return <VideoCameraOutlined style={{ color: '#f59e0b' }} />;
  if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'wma'].includes(ext))
    return <AudioOutlined style={{ color: '#8b5cf6' }} />;
  if (['zip', 'tar', 'gz', 'bz2', 'xz', 'rar', '7z', 'tgz'].includes(ext))
    return <FileZipOutlined style={{ color: '#ef4444' }} />;
  if (['txt', 'md', 'csv', 'json', 'xml', 'yaml', 'yml', 'log'].includes(ext))
    return <FileTextOutlined style={{ color: '#16a34a' }} />;
  return <FileOutlined style={{ color: '#999' }} />;
};

function getDpoScenarioGuide(dataset: Dataset) {
  if (isDpoPairwiseDataset(dataset.data_type, dataset.scenario_type)) {
    return {
      title: '二选一 JSONL 结构',
      requiredFields: ['item_key', 'prompt.messages', 'responses[2]'],
      notes: [
        'responses 必须恰好 2 条',
        '每条 response 需要唯一 response_id',
        '适合标准 A/B 偏好标注',
      ],
      example: '{"item_key":"case_001","prompt":{"messages":[{"role":"user","content":"..."}]},"responses":[{"response_id":"a","content":"..."},{"response_id":"b","content":"..."}]}',
    };
  }

  if (isDpoBestOfNDataset(dataset.data_type, dataset.scenario_type)) {
    return {
      title: '多选一 JSONL 结构',
      requiredFields: ['item_key', 'prompt.messages', 'responses[3~6]'],
      notes: [
        'responses 需要 3 到 6 条',
        '导出会按 winner_vs_all 展开',
        '适合多个候选回复中选最佳',
      ],
      example: '{"item_key":"case_002","task_type":"best_of_n","prompt":{"messages":[{"role":"user","content":"..."}]},"responses":[{"response_id":"a","content":"..."},{"response_id":"b","content":"..."},{"response_id":"c","content":"..."}]}',
    };
  }

  if (isDpoReferenceChoiceDataset(dataset.data_type, dataset.scenario_type)) {
    return {
      title: '参考增强 JSONL 结构',
      requiredFields: ['item_key', 'prompt.messages', 'responses[2~4]', 'reference'],
      notes: [
        '必须包含 reference 作为判断依据',
        '适合事实型或标准答案明确的任务',
        '可额外提供 rubric 指定判定重点',
      ],
      example: '{"item_key":"case_003","prompt":{"messages":[{"role":"user","content":"..."}]},"responses":[{"response_id":"a","content":"..."},{"response_id":"b","content":"..."}],"reference":{"content":"标准答案..."}}',
    };
  }

  if (isDpoMultiTurnDataset(dataset.data_type, dataset.scenario_type)) {
    return {
      title: '多轮对话 JSONL 结构',
      requiredFields: ['item_key', 'prompt.messages', 'responses[2~4]'],
      notes: [
        'prompt.messages 需要包含多轮上下文',
        '重点判断是否承接历史对话',
        '适合客服、助手、连续任务对话场景',
      ],
      example: '{"item_key":"case_004","prompt":{"messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."},{"role":"user","content":"..."}]},"responses":[{"response_id":"a","content":"..."},{"response_id":"b","content":"..."}]}',
    };
  }

  return {
    title: 'DPO JSONL 结构',
    requiredFields: ['item_key', 'prompt.messages', 'responses'],
    notes: [
      '旧 DPO 数据集兼容二选一和多选一',
      '建议后续新建时改用细分 DPO 子场景',
    ],
    example: '{"item_key":"case_legacy","prompt":{"messages":[{"role":"user","content":"..."}]},"responses":[{"response_id":"a","content":"..."},{"response_id":"b","content":"..."}]}',
  };
}

const DatasetDetailPage: React.FC = () => {
  const SAMPLE_PAGE_SIZE = 100;
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation('dataset');
  const tc = useTranslation('common').t;
  const datasetId = Number(id);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [samples, setSamples] = useState<SampleItem[]>([]);
  const [sampleTotal, setSampleTotal] = useState(0);
  const [samplePage, setSamplePage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [previewUrls, setPreviewUrls] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState('all');
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isDragOver, setIsDragOver] = useState(false);
  const previewObserverRef = useRef<IntersectionObserver | null>(null);
  const previewRequestedRef = useRef<Set<number>>(new Set());

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const itemType = activeTab === 'images' ? 'image' : undefined;
      const [ds, filesRes] = await Promise.all([
        getDataset(datasetId),
        getDatasetSamples(datasetId, samplePage, SAMPLE_PAGE_SIZE, itemType),
      ]);
      if (ds) setDataset(ds);
      if (filesRes) {
        setSamples(filesRes.items);
        setSampleTotal(filesRes.total);
      }
    } catch { message.error(tc('msg.loadFailed')); }
    finally { setLoading(false); }
  }, [activeTab, datasetId, samplePage, tc]);

  useEffect(() => { fetchData(); }, [fetchData]);

  useEffect(() => {
    setSelectedIds(new Set());
    previewObserverRef.current?.disconnect();
  }, [activeTab, samplePage]);

  useEffect(() => () => {
    previewObserverRef.current?.disconnect();
  }, []);

  const observePreviewTarget = useCallback((node: HTMLDivElement | null, sampleId: number, fileName: string) => {
    if (!node || previewUrls[fileName] || previewRequestedRef.current.has(sampleId)) {
      return;
    }

    if (!previewObserverRef.current) {
      previewObserverRef.current = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) {
            return;
          }

          const target = entry.target as HTMLDivElement;
          const observedSampleId = Number(target.dataset.sampleId);
          const observedFileName = target.dataset.fileName;
          if (!observedSampleId || !observedFileName || previewRequestedRef.current.has(observedSampleId)) {
            previewObserverRef.current?.unobserve(target);
            return;
          }

          previewRequestedRef.current.add(observedSampleId);
          previewObserverRef.current?.unobserve(target);
          previewSample(datasetId, observedSampleId)
            .then((res) => {
              if (res?.presigned_url) {
                setPreviewUrls((prev) => ({ ...prev, [observedFileName]: res.presigned_url }));
              }
            })
            .catch(() => { });
        });
      }, {
        rootMargin: '200px 0px',
        threshold: 0.1,
      });
    }

    node.dataset.sampleId = String(sampleId);
    node.dataset.fileName = fileName;
    previewObserverRef.current.observe(node);
  }, [datasetId, previewUrls]);

  const handleUpload = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0 || !dataset) return;
    const files = Array.from(fileList);
    const { accepted, rejected, rule } = splitAcceptedFiles(dataset, files);
    if (rejected.length > 0) {
      message.warning(t('uploadTypeInvalid', { types: rule.description || '-' }));
    }
    if (accepted.length === 0) return;
    setUploading(true);
    setUploadProgress(0);
    try {
      // 模拟进度
      const timer = setInterval(() => {
        setUploadProgress((p) => Math.min(p + 10, 90));
      }, 500);
      const uploadedCount = await uploadDatasetFiles(datasetId, accepted);
      clearInterval(timer);
      setUploadProgress(100);
      message.success(t('uploadSuccess', { count: uploadedCount ?? accepted.length }));
      setSamplePage(1);
      setSelectedIds(new Set());
      fetchData();
    } catch { message.error(tc('msg.uploadFailed')); }
    finally {
      setTimeout(() => { setUploading(false); setUploadProgress(0); }, 500);
    }
  };

  const handleDeleteDataset = () => {
    const onDelete = async () => {
      await deleteDataset(datasetId);
      message.success(tc('msg.deleted'));
      emitDatasetsChanged();
      navigate('/datasets');
    };
    if (!getDatasetDeleteConfirmEnabled()) {
      void onDelete();
      return;
    }
    Modal.confirm({
      title: t('deleteTitle'), content: t('deleteIrreversible'),
      okButtonProps: { danger: true },
      onOk: onDelete,
    });
  };

  const handleDeleteSample = (e: React.MouseEvent, sample: SampleItem) => {
    e.stopPropagation();
    const onDelete = async () => {
      await deleteDatasetSample(datasetId, sample.id);
      message.success(tc('msg.deleted'));
      setSelectedIds((prev) => { const next = new Set(prev); next.delete(sample.id); return next; });
      if (samples.length === 1 && samplePage > 1) {
        setSamplePage((prev) => Math.max(prev - 1, 1));
        return;
      }
      fetchData();
    };
    if (!getDatasetDeleteConfirmEnabled()) {
      void onDelete();
      return;
    }
    Modal.confirm({
      title: t('deleteFileTitle'),
      content: t('deleteFileConfirm'),
      okButtonProps: { danger: true },
      onOk: onDelete,
    });
  };

  const handleBatchDelete = () => {
    if (selectedIds.size === 0) return;
    const onDelete = async () => {
      await Promise.all(Array.from(selectedIds).map((sampleId) => deleteDatasetSample(datasetId, sampleId)));
      message.success(tc('msg.deleted'));
      setSelectedIds(new Set());
      if (selectedIds.size >= samples.length && samplePage > 1) {
        setSamplePage((prev) => Math.max(prev - 1, 1));
        return;
      }
      fetchData();
    };
    if (!getDatasetDeleteConfirmEnabled()) {
      void onDelete();
      return;
    }
    Modal.confirm({
      title: t('batchDelete'),
      content: t('batchDeleteConfirm', { count: selectedIds.size }),
      okButtonProps: { danger: true },
      onOk: onDelete,
    });
  };

  const toggleSelect = (fileId: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(fileId)) next.delete(fileId); else next.add(fileId);
      return next;
    });
  };

  const toggleSelectAll = () => {
    const displayed = displayedFiles;
    if (selectedIds.size === displayed.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(displayed.map((f) => f.id)));
    }
  };

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}><Spin size="large" /></div>;
  if (!dataset) return (
    <div style={{ padding: 24 }}>
      <button className="button-text" onClick={() => navigate('/datasets')} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', color: '#666', cursor: 'pointer' }}>
        <ArrowLeftOutlined /> {tc('action.back')}
      </button>
      <div style={{ textAlign: 'center', marginTop: 80, color: '#ccc' }}>{t('notExist')}</div>
    </div>
  );

  const getSampleFileName = (sample: SampleItem) => sample.asset?.file_name || sample.item_key;
  const imageFiles = samples.filter((sample) => isImageFileName(getSampleFileName(sample)));
  const displayedFiles = activeTab === 'images' ? imageFiles : samples;
  const isAerialDataset = dataset.scenario_type === DatasetScenarioType.AerialStitch;
  const isImageDataset = dataset.data_type === 0;
  const isLlmDataset = isLlmConversationDataset(dataset.data_type, dataset.scenario_type);
  const isMllmDataset = isMllmConversationDataset(dataset.data_type, dataset.scenario_type);
  const isDpoDataset = isAnyDpoDataset(dataset.data_type, dataset.scenario_type);
  const overlapRatio = dataset.scenario_config?.stitching?.default_overlap_ratio;
  const uploadRule = getDatasetUploadRule(dataset);
  const dpoGuide = isDpoDataset ? getDpoScenarioGuide(dataset) : null;
  const totalFileCount = activeTab === 'images' ? sampleTotal : dataset.count;
  const totalImageCount = isImageDataset ? dataset.count : activeTab === 'images' ? sampleTotal : imageFiles.length;

  const tabs = [
    { key: 'all', label: t('allFiles'), icon: <FileOutlined />, count: dataset.count },
    { key: 'images', label: t('images'), icon: <PictureOutlined />, count: totalImageCount },
    { key: 'info', label: t('info'), icon: <TagOutlined /> },
  ];

  return (
    <div className="page-container">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={uploadRule.accept}
        style={{ display: 'none' }}
        onChange={(e) => { handleUpload(e.target.files); e.target.value = ''; }}
      />

      {/* Breadcrumb */}
      <div className="body-text-sm" style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#999', marginBottom: 16 }}>
        <span className="body-text-sm" style={{ cursor: 'pointer' }} onClick={() => navigate('/datasets')}>{t('title')}</span>
        <span>&gt;</span>
        <span className="body-text-sm" style={{ color: '#111', fontWeight: 500 }}>{dataset.name}</span>
      </div>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <h1 className="page-title" style={{ color: '#111', margin: 0 }}>{dataset.name}</h1>
            <span className="tag-text" style={{ padding: '2px 10px', background: '#eef2ff', color: '#4f6ef7', borderRadius: 999 }}>
              {DataTypeLabels[dataset.data_type] ?? tc('status.unknown')}
            </span>
            {isImageDataset && (
              <span className="tag-text" style={{ padding: '2px 10px', background: isAerialDataset ? '#ecfdf5' : '#f8fafc', color: isAerialDataset ? '#0f766e' : '#64748b', borderRadius: 999, display: 'flex', alignItems: 'center', gap: 4 }}>
                <ApartmentOutlined /> {getDatasetScenarioLabel(dataset.data_type, dataset.scenario_type)}
              </span>
            )}
            {!isImageDataset && dataset.scenario_type !== DatasetScenarioType.Normal && (
              <span className="tag-text" style={{ padding: '2px 10px', background: '#f8fafc', color: '#64748b', borderRadius: 999, display: 'flex', alignItems: 'center', gap: 4 }}>
                <ApartmentOutlined /> {getDatasetScenarioLabel(dataset.data_type, dataset.scenario_type)}
              </span>
            )}
            <span className="tag-text" style={{ padding: '2px 10px', background: '#f0fdf4', color: '#16a34a', borderRadius: 999, display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 5, height: 5, borderRadius: 999, background: '#16a34a' }} /> {tc('status.ready')}
            </span>
          </div>
          <div className="body-text-sm" style={{ display: 'flex', alignItems: 'center', gap: 12, color: '#888' }}>
            <span><FileOutlined /> {t('filesCount', { count: totalFileCount })}</span>
            <span>·</span>
            <span><PictureOutlined /> {t('imagesCount', { count: totalImageCount })}</span>
            <span>·</span>
            <span><ClockCircleOutlined /> {t('updatedAt', { date: new Date(dataset.updated_at).toLocaleDateString() })}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className="button-text"
            onClick={() => navigate(`/datasets/${datasetId}/batch-annotation`)}
            style={{ padding: '8px 14px', background: '#fff', color: '#4f6ef7', border: '1px solid #c7d2fe', borderRadius: 6, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
          ><RobotOutlined /> 批量标注</button>
          <button
            className="button-text"
            onClick={() => fileInputRef.current?.click()}
            style={{ padding: '8px 16px', background: '#4f6ef7', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
          ><CloudUploadOutlined /> {t('dropUpload')}</button>
          <button
            onClick={handleDeleteDataset}
            style={{ padding: '8px 10px', background: '#fff', color: '#999', border: '1px solid #eee', borderRadius: 8, cursor: 'pointer', fontSize: 14 }}
          ><DeleteOutlined /></button>
        </div>
      </div>

      {dataset.description && <p className="body-text-sm" style={{ color: '#666', margin: '8px 0 0' }}>{dataset.description}</p>}

      {isAerialDataset && (
        <div style={{ marginTop: 16, padding: 16, borderRadius: 12, background: 'linear-gradient(135deg, #ecfeff, #f8fafc)', border: '1px solid #ccfbf1', color: '#334155' }}>
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#0f766e', marginBottom: 6 }}>
            <ApartmentOutlined /> {t('aerialScenarioTitle')}
          </div>
          <div className="body-text-sm">{t('aerialDetailDesc')}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
            <span className="tag-text" style={{ padding: '3px 8px', borderRadius: 999, background: '#fff', border: '1px solid #dbeafe', color: '#2563eb' }}>
              {t('aerialRulePrefix')}
            </span>
            <span className="tag-text" style={{ padding: '3px 8px', borderRadius: 999, background: '#fff', border: '1px solid #dbeafe', color: '#2563eb' }}>
              {t('aerialRuleGrid')}
            </span>
            <span className="tag-text" style={{ padding: '3px 8px', borderRadius: 999, background: '#fff', border: '1px solid #dbeafe', color: '#2563eb' }}>
              {t('aerialRuleSkipInvalid')}
            </span>
            {typeof overlapRatio === 'number' && (
              <span className="tag-text" style={{ padding: '3px 8px', borderRadius: 999, background: '#fff', border: '1px solid #dbeafe', color: '#2563eb' }}>
                {t('aerialOverlap', { value: `${Math.round(overlapRatio * 100)}%` })}
              </span>
            )}
          </div>
        </div>
      )}

      {(isLlmDataset || isMllmDataset) && (
        <div style={{ marginTop: 16, padding: 16, borderRadius: 12, background: 'linear-gradient(135deg, #f8fafc, #eef2ff)', border: '1px solid #e2e8f0', color: '#334155' }}>
          <div className="card-title" style={{ color: '#1e40af', marginBottom: 6 }}>
            {isLlmDataset ? 'LLM 对话数据集' : 'MLLM 对话数据集'}
          </div>
          <div className="body-text-sm">
            标注工作台会以对话方式编辑，结果文件按 JSON 存储。
          </div>
        </div>
      )}

      {isDpoDataset && (
        <div style={{ marginTop: 16, padding: 16, borderRadius: 12, background: 'linear-gradient(135deg, #fffdf4, #fff7ed)', border: '1px solid #fde68a', color: '#713f12' }}>
          <div className="card-title" style={{ marginBottom: 6 }}>
            {getDatasetScenarioLabel(dataset.data_type, dataset.scenario_type)}
          </div>
          <div className="body-text-sm">
            上传 `.jsonl` 文件后，系统会按当前 DPO 子场景导入结构化偏好样本，生成 `preference` 类型样本。
          </div>
          {dpoGuide && (
            <div style={{ marginTop: 12, padding: 12, borderRadius: 8, background: '#fff', border: '1px solid #fed7aa', color: '#7c2d12' }}>
              <div className="body-text-sm" style={{ fontWeight: 700, marginBottom: 8 }}>{dpoGuide.title}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
                {dpoGuide.requiredFields.map((field) => (
                  <span key={field} className="tag-text" style={{ padding: '2px 8px', borderRadius: 999, background: '#fff7ed', border: '1px solid #fdba74' }}>
                    {field}
                  </span>
                ))}
              </div>
              <div className="caption-text" style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 8 }}>
                {dpoGuide.notes.map((note) => (
                  <div key={note}>{note}</div>
                ))}
              </div>
              <div className="caption-text" style={{ color: '#9a3412', marginBottom: 4 }}>一行示例</div>
              <pre className="code-text" style={{ margin: 0, padding: 10, borderRadius: 6, background: '#fff7ed', border: '1px solid #fed7aa', color: '#7c2d12', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {dpoGuide.example}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #eee', marginTop: 20, marginBottom: 20 }}>
        {tabs.map((tab) => (
          <button
            className="button-text"
            key={tab.key}
            onClick={() => { setActiveTab(tab.key); setSamplePage(1); setSelectedIds(new Set()); }}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '10px 16px', cursor: 'pointer',
              border: 'none', background: 'none',
              borderBottom: activeTab === tab.key ? '2px solid #4f6ef7' : '2px solid transparent',
              color: activeTab === tab.key ? '#4f6ef7' : '#888',
              marginBottom: -1,
            }}
          >
            {tab.icon} {tab.label}
            {'count' in tab && (
              <span className="tag-text" style={{ marginLeft: 4, padding: '0 6px', background: '#f5f5f5', color: '#888', borderRadius: 999 }}>{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {(activeTab === 'all' || activeTab === 'images') && (
        <>
          {/* Upload Zone */}
          <div
            style={{
              border: isDragOver ? '2px dashed #4f6ef7' : '2px dashed #e5e5e5',
              borderRadius: 12, padding: '32px 16px',
              textAlign: 'center', marginBottom: 20, cursor: 'pointer',
              background: isDragOver ? '#f0f4ff' : 'transparent',
              transition: 'all 0.2s',
            }}
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setIsDragOver(false); handleUpload(e.dataTransfer.files); }}
            onClick={() => fileInputRef.current?.click()}
          >
            {uploading ? (
              <div style={{ maxWidth: 300, margin: '0 auto' }}>
                <Spin style={{ marginBottom: 8 }} />
                <Progress percent={uploadProgress} size="small" status="active" />
                <p className="caption-text" style={{ color: '#888', margin: '4px 0 0' }}>{t('uploading')}</p>
              </div>
            ) : (
              <>
                <CloudUploadOutlined style={{ fontSize: 28, color: isDragOver ? '#4f6ef7' : '#ccc', marginBottom: 8 }} />
                <p className="body-text-sm" style={{ color: '#888', margin: 0 }}>{t('dropUpload')}</p>
                <p className="tag-text" style={{ color: '#bbb', margin: '4px 0 0' }}>
                  {uploadRule.description || (isDpoDataset ? '.jsonl' : t('dropLimit'))}
                </p>
              </>
            )}
          </div>

          {/* Batch actions */}
          {displayedFiles.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <button
                className="button-text"
                onClick={toggleSelectAll}
                style={{
                  display: 'flex', alignItems: 'center', gap: 4, padding: '4px 10px',
                  border: '1px solid #e5e5e5', borderRadius: 6, background: '#fff',
                  color: '#555', cursor: 'pointer',
                }}
              >
                {selectedIds.size === displayedFiles.length ? <CheckSquareOutlined style={{ color: '#4f6ef7' }} /> : <BorderOutlined />}
                {selectedIds.size === displayedFiles.length ? t('cancelSelect') : t('selectAll')}
              </button>
              {selectedIds.size > 0 && (
                <>
                  <span className="caption-text" style={{ color: '#888' }}>{t('selected', { count: selectedIds.size })}</span>
                  <button
                    className="button-text"
                    onClick={handleBatchDelete}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 4, padding: '4px 10px',
                      border: '1px solid #fecaca', borderRadius: 6, background: '#fef2f2',
                      color: '#dc2626', cursor: 'pointer',
                    }}
                  >
                    <DeleteOutlined /> {t('batchDelete')}
                  </button>
                </>
              )}
            </div>
          )}

          {/* File grid/list */}
          {activeTab === 'images' ? (
            // 图片网格视图
            imageFiles.length > 0 ? (
              <>
                <div className="image-grid">
                {imageFiles.map((sample) => {
                  const fileName = getSampleFileName(sample);
                  return (
                  <div key={sample.id} style={{
                    position: 'relative', paddingBottom: '100%', background: '#f5f5f5',
                    borderRadius: 8, overflow: 'hidden',
                    outline: selectedIds.has(sample.id) ? '2px solid #4f6ef7' : 'none',
                    outlineOffset: -2,
                  }}>
                    <div
                      ref={(node) => observePreviewTarget(node, sample.id, fileName)}
                      style={{ position: 'absolute', inset: 0 }}
                      onClick={() => toggleSelect(sample.id)}
                    >
                      {previewUrls[fileName] ? (
                        <Image
                          src={previewUrls[fileName]}
                          alt={fileName}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          preview={{ mask: <span style={{ color: '#fff', fontSize: 12 }}>{t('preview')}</span> }}
                          onClick={(e) => e.stopPropagation()}
                        />
                      ) : (
                        <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ddd' }}>
                          <PictureOutlined style={{ fontSize: 32 }} />
                        </div>
                      )}
                    </div>
                    {/* Select checkbox */}
                    <div
                      onClick={(e) => { e.stopPropagation(); toggleSelect(sample.id); }}
                      style={{
                        position: 'absolute', top: 6, left: 6, width: 20, height: 20,
                        borderRadius: 4, background: selectedIds.has(sample.id) ? '#4f6ef7' : 'rgba(0,0,0,0.3)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        cursor: 'pointer', color: '#fff', fontSize: 12,
                      }}
                    >
                      {selectedIds.has(sample.id) && '✓'}
                    </div>
                    {/* Delete btn */}
                    <div
                      onClick={(e) => handleDeleteSample(e, sample)}
                      style={{
                        position: 'absolute', top: 6, right: 6, width: 20, height: 20,
                        borderRadius: 4, background: 'rgba(0,0,0,0.3)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        cursor: 'pointer', color: '#fff', fontSize: 11,
                        opacity: 0, transition: 'opacity 0.2s',
                      }}
                      className="file-delete-btn"
                      onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.opacity = '1'; (e.currentTarget as HTMLDivElement).style.background = 'rgba(220,38,38,0.8)'; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.opacity = '0'; (e.currentTarget as HTMLDivElement).style.background = 'rgba(0,0,0,0.3)'; }}
                    >
                      <DeleteOutlined />
                    </div>
                    {/* File name */}
                    <div style={{
                      position: 'absolute', bottom: 0, left: 0, right: 0,
                      background: 'linear-gradient(transparent, rgba(0,0,0,0.6))',
                      padding: '16px 6px 4px', color: '#fff',
                      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                    }} className="meta-text">
                      {fileName}
                    </div>
                  </div>
                );
                })}
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', marginTop: 20 }}>
                  <Pagination
                    current={samplePage}
                    pageSize={SAMPLE_PAGE_SIZE}
                    total={sampleTotal}
                    onChange={setSamplePage}
                    showSizeChanger={false}
                    showTotal={(totalValue) => t('totalFiles', { count: totalValue })}
                  />
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: 60, color: '#ddd' }}>
                <InboxOutlined style={{ fontSize: 48, marginBottom: 12 }} />
                <p className="body-text-sm">{t('noImages')}</p>
              </div>
            )
          ) : (
            // 全部文件列表视图
            displayedFiles.length > 0 ? (
              <>
                <div style={{ border: '1px solid #eee', borderRadius: 10, overflow: 'hidden' }}>
                  {/* Table header */}
                  <div style={{
                    display: 'grid', gridTemplateColumns: '40px 1fr 160px 60px',
                    padding: '8px 16px', background: '#fafafa', borderBottom: '1px solid #eee',
                    fontWeight: 600, color: '#888',
                  }} className="caption-text">
                    <div />
                    <div>{t('fileName')}</div>
                    <div>{t('uploadTime')}</div>
                    <div style={{ textAlign: 'center' }}>{t('actions')}</div>
                  </div>
                  {/* Table rows */}
                  {displayedFiles.map((sample) => {
                    const fileName = getSampleFileName(sample);
                    return (
                    <div
                      key={sample.id}
                      style={{
                        display: 'grid', gridTemplateColumns: '40px 1fr 160px 60px',
                        padding: '10px 16px', borderBottom: '1px solid #f5f5f5',
                        alignItems: 'center',
                        background: selectedIds.has(sample.id) ? '#f0f4ff' : '#fff',
                        transition: 'background 0.15s',
                      }} className="body-text-sm"
                      onMouseEnter={(e) => { if (!selectedIds.has(sample.id)) e.currentTarget.style.background = '#fafafa'; }}
                      onMouseLeave={(e) => { if (!selectedIds.has(sample.id)) e.currentTarget.style.background = '#fff'; }}
                    >
                      {/* Checkbox */}
                      <div
                        onClick={() => toggleSelect(sample.id)}
                        style={{
                          width: 18, height: 18, borderRadius: 4, cursor: 'pointer',
                          border: selectedIds.has(sample.id) ? 'none' : '1px solid #d9d9d9',
                          background: selectedIds.has(sample.id) ? '#4f6ef7' : '#fff',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          color: '#fff', fontSize: 11,
                        }}
                      >
                        {selectedIds.has(sample.id) && '✓'}
                      </div>
                      {/* File name */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, overflow: 'hidden' }}>
                        <span style={{ fontSize: 16, flexShrink: 0 }}>{getFileIcon(fileName)}</span>
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#111' }}>
                          {fileName}
                        </span>
                      </div>
                      {/* Upload time */}
                      <div className="caption-text" style={{ color: '#999' }}>
                        {new Date(sample.created_at).toLocaleString()}
                      </div>
                      {/* Actions */}
                      <div style={{ display: 'flex', justifyContent: 'center', gap: 4 }}>
                        <button
                          onClick={(e) => handleDeleteSample(e, sample)}
                          style={{
                            padding: '2px 6px', border: 'none', background: 'none',
                            color: '#999', cursor: 'pointer', fontSize: 13, borderRadius: 4,
                          }}
                          onMouseEnter={(e) => { e.currentTarget.style.color = '#dc2626'; }}
                          onMouseLeave={(e) => { e.currentTarget.style.color = '#999'; }}
                        >
                          <DeleteOutlined />
                        </button>
                      </div>
                    </div>
                  );
                  })}
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', marginTop: 20 }}>
                  <Pagination
                    current={samplePage}
                    pageSize={SAMPLE_PAGE_SIZE}
                    total={sampleTotal}
                    onChange={setSamplePage}
                    showSizeChanger={false}
                    showTotal={(totalValue) => t('totalFiles', { count: totalValue })}
                  />
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: 60, color: '#ddd' }}>
                <InboxOutlined style={{ fontSize: 48, marginBottom: 12 }} />
                <p className="body-text-sm">{t('noFiles')}</p>
              </div>
            )
          )}
        </>
      )}

      {activeTab === 'info' && (
        <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24 }}>
          <div className="info-grid-2">
            {[
              { label: tc('label.name'), value: dataset.name },
              { label: tc('label.type'), value: DataTypeLabels[dataset.data_type] ?? tc('status.unknown') },
              { label: t('scenarioType'), value: getDatasetScenarioLabel(dataset.data_type, dataset.scenario_type) },
              { label: tc('label.files'), value: t('fileCount', { count: dataset.count }) },
              { label: t('storageLocal'), value: dataset.storage_type === 0 ? t('storageLocal') : t('storageS3') },
              { label: tc('label.createdAt'), value: new Date(dataset.created_at).toLocaleString() },
              { label: tc('label.updatedAt'), value: new Date(dataset.updated_at).toLocaleString() },
              { label: t('path'), value: dataset.save_path || '-' },
              ...(isAerialDataset ? [
                { label: t('aerialNamingPattern'), value: dataset.scenario_config?.grouping?.pattern_hint || '-' },
                { label: t('aerialSequenceOrder'), value: dataset.scenario_config?.grouping?.sequence_order || '-' },
              ] : []),
              { label: tc('label.description'), value: dataset.description || '-' },
            ].map((item, i) => (
              <div key={i}>
                <div className="info-label" style={{ marginBottom: 2 }}>{item.label}</div>
                <div className="info-value">{item.value}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DatasetDetailPage;
