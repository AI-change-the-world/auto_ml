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

const DatasetDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
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
    } catch { message.error('加载失败'); }
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
      message.success(`上传 ${fileList.length} 个文件成功`);
      fetchData();
    } catch { message.error('上传失败'); }
    finally { setUploading(false); }
  };

  const handleDelete = () => {
    Modal.confirm({
      title: '删除数据集', content: '确定要删除此数据集吗？此操作不可恢复。',
      okButtonProps: { danger: true },
      onOk: async () => { await deleteDataset(datasetId); message.success('删除成功'); navigate('/datasets'); },
    });
  };

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}><Spin size="large" /></div>;
  if (!dataset) return (
    <div style={{ padding: 24 }}>
      <button onClick={() => navigate('/datasets')} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: 14 }}>
        <ArrowLeftOutlined /> 返回
      </button>
      <div style={{ textAlign: 'center', marginTop: 80, color: '#ccc' }}>数据集不存在</div>
    </div>
  );

  const tabs = [
    { key: 'images', label: '图片', icon: <PictureOutlined /> },
    { key: 'info', label: '信息', icon: <TagOutlined /> },
  ];

  const imageFiles = files.filter((f) => {
    const ext = f.file_name.split('.').pop()?.toLowerCase();
    return ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif'].includes(ext || '');
  });

  return (
    <div className="page-container">
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#999', marginBottom: 16 }}>
        <span style={{ cursor: 'pointer' }} onClick={() => navigate('/datasets')}>数据集</span>
        <span>&gt;</span>
        <span style={{ color: '#111', fontWeight: 500 }}>{dataset.name}</span>
      </div>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', margin: 0 }}>{dataset.name}</h1>
            <span style={{ padding: '2px 10px', background: '#eef2ff', color: '#4f6ef7', fontSize: 12, borderRadius: 999 }}>
              {DataTypeLabels[dataset.data_type] ?? '未知'}
            </span>
            <span style={{ padding: '2px 10px', background: '#f0fdf4', color: '#16a34a', fontSize: 12, borderRadius: 999, display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 5, height: 5, borderRadius: 999, background: '#16a34a' }} /> 就绪
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 13, color: '#888' }}>
            <span><PictureOutlined /> {files.length} 张图片</span>
            <span>·</span>
            <span><TagOutlined /> {files.length} 已标注</span>
            <span>·</span>
            <span><ClockCircleOutlined /> 更新于 {new Date(dataset.updated_at).toLocaleDateString()}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => navigate('/tasks')}
            style={{ padding: '8px 16px', background: '#4f6ef7', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer' }}
          >+ 新建模型</button>
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
            {uploading ? <Spin tip="上传中..." /> : (
              <>
                <CloudUploadOutlined style={{ fontSize: 28, color: '#ccc', marginBottom: 8 }} />
                <p style={{ fontSize: 13, color: '#888', margin: 0 }}>拖放图片、视频或数据集</p>
                <p style={{ fontSize: 11, color: '#bbb', margin: '4px 0 0' }}>图片 &lt;50 MB · 数据集 &lt;10 GB — ZIP, TAR</p>
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
                        preview={{ mask: <span style={{ color: '#fff', fontSize: 12 }}>预览</span> }}
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
              <p style={{ fontSize: 13 }}>暂无图片，请上传</p>
            </div>
          )}
        </>
      )}

      {activeTab === 'info' && (
        <div style={{ background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: 24 }}>
          <div className="info-grid-2">
            {[
              { label: '名称', value: dataset.name },
              { label: '类型', value: DataTypeLabels[dataset.data_type] ?? '未知' },
              { label: '文件数', value: `${files.length} 个` },
              { label: '存储', value: dataset.storage_type === 0 ? '本地' : 'S3' },
              { label: '创建', value: new Date(dataset.created_at).toLocaleString() },
              { label: '更新', value: new Date(dataset.updated_at).toLocaleString() },
              { label: '路径', value: dataset.save_path || '-' },
              { label: '描述', value: dataset.description || '-' },
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
