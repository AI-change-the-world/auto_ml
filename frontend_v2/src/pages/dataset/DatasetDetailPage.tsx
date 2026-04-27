import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { message, Spin, Modal, Image, Progress } from 'antd';
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
} from '@ant-design/icons';
import { getDataset, getDatasetFiles, uploadDatasetFiles, previewFile, deleteDataset, deleteDatasetFile, batchDeleteDatasetFiles } from '../../api/dataset';
import type { Dataset, DatasetFile } from '../../types';
import { DataTypeLabels, DatasetScenarioType, getDatasetScenarioLabel, isLlmConversationDataset, isMllmConversationDataset } from '../../types';
import { useTranslation } from 'react-i18next';
import { isImageFileName } from '../../utils/file';

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

const DatasetDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation('dataset');
  const tc = useTranslation('common').t;
  const datasetId = Number(id);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [files, setFiles] = useState<DatasetFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [previewUrls, setPreviewUrls] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState('all');
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isDragOver, setIsDragOver] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [ds, filesRes] = await Promise.all([getDataset(datasetId), getDatasetFiles(datasetId)]);
      if (ds) setDataset(ds);
      if (filesRes) setFiles(filesRes.items);
    } catch { message.error(tc('msg.loadFailed')); }
    finally { setLoading(false); }
  }, [datasetId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // 加载图片预览
  useEffect(() => {
    files.forEach(async (f) => {
      if (previewUrls[f.file_name]) return;
      if (!isImageFileName(f.file_name)) return;
      try {
        const res = await previewFile(datasetId, f.file_name);
        if (res?.presigned_url) setPreviewUrls((prev) => ({ ...prev, [f.file_name]: res.presigned_url }));
      } catch { /* ignore */ }
    });
  }, [files, datasetId]);

  const handleUpload = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    setUploading(true);
    setUploadProgress(0);
    try {
      // 模拟进度
      const timer = setInterval(() => {
        setUploadProgress((p) => Math.min(p + 10, 90));
      }, 500);
      const uploadedCount = await uploadDatasetFiles(datasetId, Array.from(fileList));
      clearInterval(timer);
      setUploadProgress(100);
      message.success(t('uploadSuccess', { count: uploadedCount ?? fileList.length }));
      setSelectedIds(new Set());
      fetchData();
    } catch { message.error(tc('msg.uploadFailed')); }
    finally {
      setTimeout(() => { setUploading(false); setUploadProgress(0); }, 500);
    }
  };

  const handleDeleteDataset = () => {
    Modal.confirm({
      title: t('deleteTitle'), content: t('deleteIrreversible'),
      okButtonProps: { danger: true },
      onOk: async () => { await deleteDataset(datasetId); message.success(tc('msg.deleted')); navigate('/datasets'); },
    });
  };

  const handleDeleteFile = (e: React.MouseEvent, file: DatasetFile) => {
    e.stopPropagation();
    Modal.confirm({
      title: t('deleteFileTitle'),
      content: t('deleteFileConfirm'),
      okButtonProps: { danger: true },
      onOk: async () => {
        await deleteDatasetFile(datasetId, file.id);
        message.success(tc('msg.deleted'));
        setSelectedIds((prev) => { const next = new Set(prev); next.delete(file.id); return next; });
        fetchData();
      },
    });
  };

  const handleBatchDelete = () => {
    if (selectedIds.size === 0) return;
    Modal.confirm({
      title: t('batchDelete'),
      content: t('batchDeleteConfirm', { count: selectedIds.size }),
      okButtonProps: { danger: true },
      onOk: async () => {
        await batchDeleteDatasetFiles(datasetId, Array.from(selectedIds));
        message.success(tc('msg.deleted'));
        setSelectedIds(new Set());
        fetchData();
      },
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
      <button onClick={() => navigate('/datasets')} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: 14 }}>
        <ArrowLeftOutlined /> {tc('action.back')}
      </button>
      <div style={{ textAlign: 'center', marginTop: 80, color: '#ccc' }}>{t('notExist')}</div>
    </div>
  );

  const imageFiles = files.filter((f) => isImageFileName(f.file_name));
  const displayedFiles = activeTab === 'images' ? imageFiles : files;
  const isAerialDataset = dataset.scenario_type === DatasetScenarioType.AerialStitch;
  const isImageDataset = dataset.data_type === 0;
  const isLlmDataset = isLlmConversationDataset(dataset.data_type, dataset.scenario_type);
  const isMllmDataset = isMllmConversationDataset(dataset.data_type, dataset.scenario_type);
  const overlapRatio = dataset.scenario_config?.stitching?.default_overlap_ratio;

  const tabs = [
    { key: 'all', label: t('allFiles'), icon: <FileOutlined />, count: files.length },
    { key: 'images', label: t('images'), icon: <PictureOutlined />, count: imageFiles.length },
    { key: 'info', label: t('info'), icon: <TagOutlined /> },
  ];

  return (
    <div className="page-container">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        style={{ display: 'none' }}
        onChange={(e) => { handleUpload(e.target.files); e.target.value = ''; }}
      />

      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#999', marginBottom: 16 }}>
        <span style={{ cursor: 'pointer' }} onClick={() => navigate('/datasets')}>{t('title')}</span>
        <span>&gt;</span>
        <span style={{ color: '#111', fontWeight: 500 }}>{dataset.name}</span>
      </div>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', margin: 0 }}>{dataset.name}</h1>
            <span style={{ padding: '2px 10px', background: '#eef2ff', color: '#4f6ef7', fontSize: 12, borderRadius: 999 }}>
              {DataTypeLabels[dataset.data_type] ?? tc('status.unknown')}
            </span>
            {isImageDataset && (
              <span style={{ padding: '2px 10px', background: isAerialDataset ? '#ecfdf5' : '#f8fafc', color: isAerialDataset ? '#0f766e' : '#64748b', fontSize: 12, borderRadius: 999, display: 'flex', alignItems: 'center', gap: 4 }}>
                <ApartmentOutlined /> {getDatasetScenarioLabel(dataset.data_type, dataset.scenario_type)}
              </span>
            )}
            {!isImageDataset && dataset.scenario_type !== DatasetScenarioType.Normal && (
              <span style={{ padding: '2px 10px', background: '#f8fafc', color: '#64748b', fontSize: 12, borderRadius: 999, display: 'flex', alignItems: 'center', gap: 4 }}>
                <ApartmentOutlined /> {getDatasetScenarioLabel(dataset.data_type, dataset.scenario_type)}
              </span>
            )}
            <span style={{ padding: '2px 10px', background: '#f0fdf4', color: '#16a34a', fontSize: 12, borderRadius: 999, display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 5, height: 5, borderRadius: 999, background: '#16a34a' }} /> {tc('status.ready')}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 13, color: '#888' }}>
            <span><FileOutlined /> {t('filesCount', { count: files.length })}</span>
            <span>·</span>
            <span><PictureOutlined /> {t('imagesCount', { count: imageFiles.length })}</span>
            <span>·</span>
            <span><ClockCircleOutlined /> {t('updatedAt', { date: new Date(dataset.updated_at).toLocaleDateString() })}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => fileInputRef.current?.click()}
            style={{ padding: '8px 16px', background: '#4f6ef7', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
          ><CloudUploadOutlined /> {t('dropUpload')}</button>
          <button
            onClick={handleDeleteDataset}
            style={{ padding: '8px 10px', background: '#fff', color: '#999', border: '1px solid #eee', borderRadius: 8, cursor: 'pointer', fontSize: 14 }}
          ><DeleteOutlined /></button>
        </div>
      </div>

      {dataset.description && <p style={{ fontSize: 13, color: '#666', margin: '8px 0 0' }}>{dataset.description}</p>}

      {isAerialDataset && (
        <div style={{ marginTop: 16, padding: 16, borderRadius: 12, background: 'linear-gradient(135deg, #ecfeff, #f8fafc)', border: '1px solid #ccfbf1', color: '#334155' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 700, color: '#0f766e', marginBottom: 6 }}>
            <ApartmentOutlined /> {t('aerialScenarioTitle')}
          </div>
          <div style={{ fontSize: 13, lineHeight: 1.7 }}>{t('aerialDetailDesc')}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
            <span style={{ padding: '3px 8px', borderRadius: 999, background: '#fff', border: '1px solid #dbeafe', color: '#2563eb', fontSize: 12 }}>
              {t('aerialRulePrefix')}
            </span>
            <span style={{ padding: '3px 8px', borderRadius: 999, background: '#fff', border: '1px solid #dbeafe', color: '#2563eb', fontSize: 12 }}>
              {t('aerialRuleGrid')}
            </span>
            <span style={{ padding: '3px 8px', borderRadius: 999, background: '#fff', border: '1px solid #dbeafe', color: '#2563eb', fontSize: 12 }}>
              {t('aerialRuleSkipInvalid')}
            </span>
            {typeof overlapRatio === 'number' && (
              <span style={{ padding: '3px 8px', borderRadius: 999, background: '#fff', border: '1px solid #dbeafe', color: '#2563eb', fontSize: 12 }}>
                {t('aerialOverlap', { value: `${Math.round(overlapRatio * 100)}%` })}
              </span>
            )}
          </div>
        </div>
      )}

      {(isLlmDataset || isMllmDataset) && (
        <div style={{ marginTop: 16, padding: 16, borderRadius: 12, background: 'linear-gradient(135deg, #f8fafc, #eef2ff)', border: '1px solid #e2e8f0', color: '#334155' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#1e40af', marginBottom: 6 }}>
            {isLlmDataset ? 'LLM 对话数据集' : 'MLLM 对话数据集'}
          </div>
          <div style={{ fontSize: 13, lineHeight: 1.7 }}>
            标注工作台会以对话方式编辑，结果文件按 JSON 存储。
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #eee', marginTop: 20, marginBottom: 20 }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => { setActiveTab(tab.key); setSelectedIds(new Set()); }}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '10px 16px', fontSize: 13, fontWeight: 500, cursor: 'pointer',
              border: 'none', background: 'none',
              borderBottom: activeTab === tab.key ? '2px solid #4f6ef7' : '2px solid transparent',
              color: activeTab === tab.key ? '#4f6ef7' : '#888',
              marginBottom: -1,
            }}
          >
            {tab.icon} {tab.label}
            {'count' in tab && (
              <span style={{ marginLeft: 4, padding: '0 6px', background: '#f5f5f5', color: '#888', fontSize: 11, borderRadius: 999 }}>{tab.count}</span>
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
                <p style={{ fontSize: 12, color: '#888', margin: '4px 0 0' }}>{t('uploading')}</p>
              </div>
            ) : (
              <>
                <CloudUploadOutlined style={{ fontSize: 28, color: isDragOver ? '#4f6ef7' : '#ccc', marginBottom: 8 }} />
                <p style={{ fontSize: 13, color: '#888', margin: 0 }}>{t('dropUpload')}</p>
                <p style={{ fontSize: 11, color: '#bbb', margin: '4px 0 0' }}>{t('dropLimit')}</p>
              </>
            )}
          </div>

          {/* Batch actions */}
          {displayedFiles.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <button
                onClick={toggleSelectAll}
                style={{
                  display: 'flex', alignItems: 'center', gap: 4, padding: '4px 10px',
                  border: '1px solid #e5e5e5', borderRadius: 6, background: '#fff',
                  fontSize: 12, color: '#555', cursor: 'pointer',
                }}
              >
                {selectedIds.size === displayedFiles.length ? <CheckSquareOutlined style={{ color: '#4f6ef7' }} /> : <BorderOutlined />}
                {selectedIds.size === displayedFiles.length ? t('cancelSelect') : t('selectAll')}
              </button>
              {selectedIds.size > 0 && (
                <>
                  <span style={{ fontSize: 12, color: '#888' }}>{t('selected', { count: selectedIds.size })}</span>
                  <button
                    onClick={handleBatchDelete}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 4, padding: '4px 10px',
                      border: '1px solid #fecaca', borderRadius: 6, background: '#fef2f2',
                      fontSize: 12, color: '#dc2626', cursor: 'pointer',
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
              <div className="image-grid">
                {imageFiles.map((f) => (
                  <div key={f.id} style={{
                    position: 'relative', paddingBottom: '100%', background: '#f5f5f5',
                    borderRadius: 8, overflow: 'hidden',
                    outline: selectedIds.has(f.id) ? '2px solid #4f6ef7' : 'none',
                    outlineOffset: -2,
                  }}>
                    <div style={{ position: 'absolute', inset: 0 }} onClick={() => toggleSelect(f.id)}>
                      {previewUrls[f.file_name] ? (
                        <Image
                          src={previewUrls[f.file_name]}
                          alt={f.file_name}
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
                      onClick={(e) => { e.stopPropagation(); toggleSelect(f.id); }}
                      style={{
                        position: 'absolute', top: 6, left: 6, width: 20, height: 20,
                        borderRadius: 4, background: selectedIds.has(f.id) ? '#4f6ef7' : 'rgba(0,0,0,0.3)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        cursor: 'pointer', color: '#fff', fontSize: 12,
                      }}
                    >
                      {selectedIds.has(f.id) && '✓'}
                    </div>
                    {/* Delete btn */}
                    <div
                      onClick={(e) => handleDeleteFile(e, f)}
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
                      padding: '16px 6px 4px', color: '#fff', fontSize: 10,
                      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                    }}>
                      {f.file_name}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 60, color: '#ddd' }}>
                <InboxOutlined style={{ fontSize: 48, marginBottom: 12 }} />
                <p style={{ fontSize: 13 }}>{t('noImages')}</p>
              </div>
            )
          ) : (
            // 全部文件列表视图
            displayedFiles.length > 0 ? (
              <div style={{ border: '1px solid #eee', borderRadius: 10, overflow: 'hidden' }}>
                {/* Table header */}
                <div style={{
                  display: 'grid', gridTemplateColumns: '40px 1fr 160px 60px',
                  padding: '8px 16px', background: '#fafafa', borderBottom: '1px solid #eee',
                  fontSize: 12, fontWeight: 600, color: '#888',
                }}>
                  <div />
                  <div>{t('fileName')}</div>
                  <div>{t('uploadTime')}</div>
                  <div style={{ textAlign: 'center' }}>{t('actions')}</div>
                </div>
                {/* Table rows */}
                {displayedFiles.map((f) => (
                  <div
                    key={f.id}
                    style={{
                      display: 'grid', gridTemplateColumns: '40px 1fr 160px 60px',
                      padding: '10px 16px', borderBottom: '1px solid #f5f5f5',
                      alignItems: 'center', fontSize: 13,
                      background: selectedIds.has(f.id) ? '#f0f4ff' : '#fff',
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={(e) => { if (!selectedIds.has(f.id)) e.currentTarget.style.background = '#fafafa'; }}
                    onMouseLeave={(e) => { if (!selectedIds.has(f.id)) e.currentTarget.style.background = '#fff'; }}
                  >
                    {/* Checkbox */}
                    <div
                      onClick={() => toggleSelect(f.id)}
                      style={{
                        width: 18, height: 18, borderRadius: 4, cursor: 'pointer',
                        border: selectedIds.has(f.id) ? 'none' : '1px solid #d9d9d9',
                        background: selectedIds.has(f.id) ? '#4f6ef7' : '#fff',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: '#fff', fontSize: 11,
                      }}
                    >
                      {selectedIds.has(f.id) && '✓'}
                    </div>
                    {/* File name */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, overflow: 'hidden' }}>
                      <span style={{ fontSize: 16, flexShrink: 0 }}>{getFileIcon(f.file_name)}</span>
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#111' }}>
                        {f.file_name}
                      </span>
                    </div>
                    {/* Upload time */}
                    <div style={{ color: '#999', fontSize: 12 }}>
                      {new Date(f.created_at).toLocaleString()}
                    </div>
                    {/* Actions */}
                    <div style={{ display: 'flex', justifyContent: 'center', gap: 4 }}>
                      <button
                        onClick={(e) => handleDeleteFile(e, f)}
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
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 60, color: '#ddd' }}>
                <InboxOutlined style={{ fontSize: 48, marginBottom: 12 }} />
                <p style={{ fontSize: 13 }}>{t('noFiles')}</p>
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
              { label: tc('label.files'), value: t('fileCount', { count: files.length }) },
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
                <div style={{ fontSize: 12, color: '#999', marginBottom: 2 }}>{item.label}</div>
                <div style={{ fontSize: 14, color: '#111' }}>{item.value}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DatasetDetailPage;
