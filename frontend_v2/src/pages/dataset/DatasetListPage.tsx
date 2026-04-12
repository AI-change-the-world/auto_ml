import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { message, Spin, Modal, Input } from 'antd';
import {
  PlusOutlined,
  DatabaseOutlined,
  SearchOutlined,
  PictureOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { listDatasets, createDataset, deleteDataset } from '../../api/dataset';
import type { Dataset, DatasetCreate } from '../../types';
import { DataTypeLabels } from '../../types';

const DatasetListPage: React.FC = () => {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [keyword, setKeyword] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState<DatasetCreate>({ name: '', data_type: 0 });

  const fetchDatasets = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listDatasets(1, 50, keyword || undefined);
      if (res) { setDatasets(res.items); setTotal(res.total); }
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  }, [keyword]);

  useEffect(() => { fetchDatasets(); }, [fetchDatasets]);

  const handleCreate = async () => {
    if (!formData.name.trim()) { message.warning('请输入名称'); return; }
    setCreating(true);
    try {
      const res = await createDataset(formData);
      message.success('创建成功');
      setCreateOpen(false);
      setFormData({ name: '', data_type: 0 });
      fetchDatasets();
      if (res) navigate(`/datasets/${res.id}`);
    } catch { message.error('创建失败'); }
    finally { setCreating(false); }
  };

  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    Modal.confirm({
      title: '删除数据集', content: '确定删除？',
      okButtonProps: { danger: true },
      onOk: async () => { await deleteDataset(id); message.success('已删除'); fetchDatasets(); },
    });
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
            <DatabaseOutlined /> 数据集
          </h1>
          <p style={{ color: '#888', fontSize: 13, marginTop: 4 }}>管理图片、视频和数据集</p>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 500,
            background: '#4f6ef7', color: '#fff', border: 'none', cursor: 'pointer',
          }}
        >
          <PlusOutlined /> 新建数据集
        </button>
      </div>

      {/* Search */}
      <div style={{ marginBottom: 20, position: 'relative', maxWidth: 360 }}>
        <SearchOutlined style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#bbb', fontSize: 13 }} />
        <input
          style={{
            width: '100%', padding: '8px 12px 8px 34px', border: '1px solid #e5e5e5',
            borderRadius: 8, fontSize: 13, outline: 'none', background: '#fff',
          }}
          placeholder="搜索数据集..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
        />
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
      ) : datasets.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 80, color: '#ccc' }}>
          <DatabaseOutlined style={{ fontSize: 48, marginBottom: 12 }} />
          <p style={{ fontSize: 14 }}>暂无数据集</p>
        </div>
      ) : (
        <div className="card-grid">
          {datasets.map((ds) => (
            <div
              key={ds.id}
              onClick={() => navigate(`/datasets/${ds.id}`)}
              style={{
                background: '#fff', border: '1px solid #eee', borderRadius: 12,
                overflow: 'hidden', cursor: 'pointer', transition: 'box-shadow 0.2s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.06)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; }}
            >
              <div style={{
                height: 120, background: 'linear-gradient(135deg, #e0e7ff, #c7d2fe)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative',
              }}>
                <PictureOutlined style={{ fontSize: 36, color: '#a5b4fc' }} />
                <button
                  onClick={(e) => handleDelete(e, ds.id)}
                  style={{
                    position: 'absolute', top: 8, right: 8, width: 28, height: 28,
                    borderRadius: 6, background: 'rgba(255,255,255,0.8)', border: 'none',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#999', fontSize: 13, opacity: 0, transition: 'opacity 0.2s',
                  }}
                  className="card-delete-btn"
                >
                  <DeleteOutlined />
                </button>
              </div>
              <div style={{ padding: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 600, color: '#111', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ds.name}</span>
                  <span style={{ fontSize: 11, padding: '1px 8px', background: '#eef2ff', color: '#4f6ef7', borderRadius: 999, flexShrink: 0 }}>
                    {DataTypeLabels[ds.data_type] ?? '未知'}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 12, color: '#999' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><PictureOutlined /> {ds.count} 文件</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}><ClockCircleOutlined /> {new Date(ds.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 16, fontSize: 13, color: '#bbb' }}>共 {total} 个数据集</div>

      <Modal title="新建数据集" open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); setFormData({ name: '', data_type: 0 }); }} confirmLoading={creating} okText="创建" cancelText="取消">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>名称</label>
            <Input placeholder="输入数据集名称" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>数据类型</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {Object.entries(DataTypeLabels).map(([k, v]) => (
                <button
                  key={k}
                  onClick={() => setFormData({ ...formData, data_type: Number(k) })}
                  style={{
                    padding: '5px 14px', fontSize: 13, borderRadius: 8, cursor: 'pointer',
                    border: formData.data_type === Number(k) ? '1px solid #4f6ef7' : '1px solid #e5e5e5',
                    background: formData.data_type === Number(k) ? '#eef2ff' : '#fff',
                    color: formData.data_type === Number(k) ? '#4f6ef7' : '#666',
                  }}
                >{v}</button>
              ))}
            </div>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>描述</label>
            <Input.TextArea rows={3} placeholder="可选描述" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default DatasetListPage;
