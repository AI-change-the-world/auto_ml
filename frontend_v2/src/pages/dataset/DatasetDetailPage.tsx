import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { message, Spin, Modal, Image } from 'antd';
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  PictureOutlined,
  InboxOutlined,
  ClockCircleOutlined,
  TagOutlined,
  CloudUploadOutlined,
} from '@ant-design/icons';
import { getDataset, getDatasetFiles, uploadDatasetFiles, previewFile, deleteDataset } from '../../api/dataset';
import type { Dataset, DatasetFile } from '../../types';
import { DataTypeLabels } from '../../types';
import { useTranslation } from 'react-i18next';

const DatasetDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation('dataset');
  const tc = useTranslation('common').t;
  const datasetId = Number(id);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [files, setFiles] = useState<DatasetFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [previewUrls, setPreviewUrls] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState('images');

  const fetchData = useCallback(async () => {
    try {
      const [ds, filesRes] = await Promise.all([getDataset(datasetId), getDatasetFiles(datasetId)]);
      if (ds) setDataset(ds);
      if (filesRes) setFiles(filesRes.items);
    } catch { message.error(tc('msg.loadFailed')); }
    finally { setLoading(false); }
  }, [datasetId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  useEffect(() => {
    files.forEach(async (f) => {
      if (previewUrls[f.file_name]) return;
      const ext = f.file_name.split('.').pop()?.toLowerCase();
      if (!['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif'].includes(ext || '')) return;
      try {
        const res = await previewFile(datasetId, f.file_name);
        if (res?.presigned_url) setPreviewUrls((prev) => ({ ...prev, [f.file_name]: res.presigned_url }));
      } catch { /* ignore */ }
    });
  }, [files, datasetId]);

  const handleUpload = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    setUploading(true);
    try {
      await uploadDatasetFiles(datasetId, Array.from(fileList));
      message.success(t('uploadSuccess', { count: fileList.length }));
      fetchData();
    } catch { message.error(tc('msg.uploadFailed')); }
    finally { setUploading(false); }
  };

  const handleDelete = () => {
    Modal.confirm({
      title: t('deleteTitle'), content: t('deleteIrreversible'),
      okButtonProps: { danger: true },
      onOk: async () => { await deleteDataset(datasetId); message.success(tc('msg.deleted')); navigate('/datasets'); },
    });
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

  const tabs = [
    { key: 'images', label: t('images'), icon: <PictureOutlined /> },
    { key: 'info', label: t('info'), icon: <TagOutlined /> },
  ];

  const imageFiles = files.filter((f) => {
    const ext = f.file_name.split('.').pop()?.toLowerCase();
    return ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif'].includes(ext || '');
  });

  return (
    <div className="page-container">
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
            <span style={{ padding: '2px 10px', background: '#f0fdf4', color: '#16a34a', fontSize: 12, borderRadius: 999, display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 5, height: 5, borderRadius: 999, background: '#16a34a' }} /> {tc('status.ready')}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 13, color: '#888' }}>
            <span><PictureOutlined /> {t('filesCount', { count: files.length })}</span>
            <span>·</span>
            <span><TagOutlined /> {t('annotated', { count: files.length })}</span>
            <span>·</span>
            <span><ClockCircleOutlined /> {t('updatedAt', { date: new Date(dataset.updated_at).toLocaleDateString() })}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => navigate('/tasks')}
            style={{ padding: '8px 16px', background: '#4f6ef7', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer' }}
          >+ {t('newModel')}</button>
          <button
            onClick={handleDelete}
            style={{ padding: '8px 10px', background: '#fff', color: '#999', border: '1px solid #eee', borderRadius: 8, cursor: 'pointer', fontSize: 14 }}
          ><DeleteOutlined /></button>
        </div>
      </div>

      {dataset.description && <p style={{ fontSize: 13, color: '#666', margin: '8px 0 0' }}>{dataset.description}</p>}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #eee', marginTop: 20, marginBottom: 20 }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
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
            {tab.key === 'images' && (
              <span style={{ marginLeft: 4, padding: '0 6px', background: '#f5f5f5', color: '#888', fontSize: 11, borderRadius: 999 }}>{imageFiles.length}</span>
            )}
          </button>
        ))}
      </div>

      {activeTab === 'images' && (
        <>
          {/* Upload Zone */}
          <div
            style={{
              border: '2px dashed #e5e5e5', borderRadius: 12, padding: '32px 16px',
              textAlign: 'center', marginBottom: 20, cursor: 'pointer',
            }}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); handleUpload(e.dataTransfer.files); }}
            onClick={() => {
              const input = document.createElement('input');
              input.type = 'file'; input.multiple = true; input.accept = 'image/*,.zip,.tar';
              input.onchange = () => handleUpload(input.files);
              input.click();
            }}
          >
            {uploading ? <Spin tip={t('uploading')} /> : (
              <>
                <CloudUploadOutlined style={{ fontSize: 28, color: '#ccc', marginBottom: 8 }} />
                <p style={{ fontSize: 13, color: '#888', margin: 0 }}>{t('dropUpload')}</p>
                <p style={{ fontSize: 11, color: '#bbb', margin: '4px 0 0' }}>{t('dropLimit')}</p>
              </>
            )}
          </div>

          {imageFiles.length > 0 ? (
            <div className="image-grid">
              {imageFiles.map((f) => (
                <div key={f.id} style={{
                  position: 'relative', paddingBottom: '100%', background: '#f5f5f5',
                  borderRadius: 8, overflow: 'hidden',
                }}>
                  <div style={{ position: 'absolute', inset: 0 }}>
                    {previewUrls[f.file_name] ? (
                      <Image
                        src={previewUrls[f.file_name]}
                        alt={f.file_name}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        preview={{ mask: <span style={{ color: '#fff', fontSize: 12 }}>{t('preview')}</span> }}
                      />
                    ) : (
                      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ddd' }}>
                        <PictureOutlined style={{ fontSize: 32 }} />
                      </div>
                    )}
                  </div>
                  {/* Badge */}
                  <div style={{ position: 'absolute', top: 6, left: 6, background: 'rgba(0,0,0,0.5)', color: '#fff', fontSize: 11, padding: '1px 6px', borderRadius: 4, display: 'flex', alignItems: 'center', gap: 3 }}>
                    <TagOutlined style={{ fontSize: 10 }} /> 0
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 60, color: '#ddd' }}>
              <InboxOutlined style={{ fontSize: 48, marginBottom: 12 }} />
              <p style={{ fontSize: 13 }}>{t('noImages')}</p>
            </div>
          )}
        </>
      )}

      {activeTab === 'info' && (
        <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24 }}>
          <div className="info-grid-2">
            {[
              { label: tc('label.name'), value: dataset.name },
              { label: tc('label.type'), value: DataTypeLabels[dataset.data_type] ?? tc('status.unknown') },
              { label: tc('label.files'), value: t('fileCount', { count: files.length }) },
              { label: t('storageLocal'), value: dataset.storage_type === 0 ? t('storageLocal') : t('storageS3') },
              { label: tc('label.createdAt'), value: new Date(dataset.created_at).toLocaleString() },
              { label: tc('label.updatedAt'), value: new Date(dataset.updated_at).toLocaleString() },
              { label: t('path'), value: dataset.save_path || '-' },
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
