import React, { useEffect, useState, useCallback } from 'react';
import { message, Spin, Modal, Input, Select } from 'antd';
import { ToolOutlined, ReloadOutlined, PlusOutlined, ApiOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { listToolModels, createToolModel } from '../../api/tool';
import type { ToolModelResponse } from '../../types/tool';

const ToolPage: React.FC = () => {
  const [models, setModels] = useState<ToolModelResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<{ name: string; model_type: string; endpoint: string }>({
    name: '', model_type: '', endpoint: '',
  });

  const fetchModels = useCallback(async () => {
    setLoading(true);
    try {
      const r = await listToolModels(1, 20);
      if (r) { setModels(r.items); setTotal(r.total); }
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchModels(); }, [fetchModels]);

  const handleCreate = async () => {
    if (!form.name) { message.warning('请输入名称'); return; }
    setCreating(true);
    try {
      await createToolModel({
        name: form.name,
        model_type: form.model_type || undefined,
        endpoint: form.endpoint || undefined,
      });
      message.success('创建成功');
      setCreateOpen(false);
      setForm({ name: '', model_type: '', endpoint: '' });
      fetchModels();
    } catch { message.error('创建失败'); }
    finally { setCreating(false); }
  };

  const typeColors: Record<string, string> = {
    segmentation: '#8b5cf6',
    detection: '#4f6ef7',
    classification: '#16a34a',
    ocr: '#f59e0b',
  };

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111', display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
            <ToolOutlined /> 工具模型
          </h1>
          <p style={{ color: '#888', fontSize: 13, marginTop: 4 }}>管理分割、检测、OCR 等辅助工具模型</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={fetchModels} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 14px', border: '1px solid #e5e5e5', borderRadius: 8, fontSize: 13, background: '#fff', color: '#666', cursor: 'pointer' }}>
            <ReloadOutlined /> 刷新
          </button>
          <button onClick={() => setCreateOpen(true)} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '8px 16px', background: '#4f6ef7', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
            <PlusOutlined /> 添加模型
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
      ) : models.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 80, color: '#ccc' }}>
          <ToolOutlined style={{ fontSize: 48, marginBottom: 12 }} />
          <p>暂无工具模型</p>
          <p style={{ fontSize: 13 }}>添加分割、检测等工具模型用于辅助标注</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 12 }}>
          {models.map((m) => {
            const color = typeColors[m.model_type || ''] || '#4f6ef7';
            return (
              <div key={m.id} style={{
                background: '#fff', border: '1px solid #eee', borderRadius: 12, padding: '18px 20px',
                display: 'flex', flexDirection: 'column', gap: 8, transition: 'box-shadow 0.2s',
              }} onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 2px 12px rgba(0,0,0,0.05)'}
                 onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: 10, background: `${color}12`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', color,
                  }}>
                    <ApiOutlined />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 15, fontWeight: 600, color: '#111', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.name}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                      {m.model_type && (
                        <span style={{ padding: '1px 8px', fontSize: 11, borderRadius: 999, background: `${color}12`, color }}>
                          {m.model_type}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                {m.endpoint && (
                  <div style={{ fontSize: 12, color: '#999', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {m.endpoint}
                  </div>
                )}
                <div style={{ fontSize: 12, color: '#bbb', marginTop: 'auto' }}>
                  {dayjs(m.created_at).format('YYYY-MM-DD HH:mm')}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div style={{ marginTop: 16, fontSize: 13, color: '#bbb' }}>共 {total} 个工具模型</div>

      <Modal title="添加工具模型" open={createOpen} onOk={handleCreate} onCancel={() => setCreateOpen(false)} confirmLoading={creating} okText="创建" cancelText="取消">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 16 }}>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>名称</label>
            <Input placeholder="模型名称" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>模型类型</label>
            <Select style={{ width: '100%' }} placeholder="选择模型类型" value={form.model_type || undefined} onChange={(v) => setForm({ ...form, model_type: v })} allowClear
              options={[
                { label: '目标检测', value: 'detection' },
                { label: '图像分割', value: 'segmentation' },
                { label: '图像分类', value: 'classification' },
                { label: 'OCR', value: 'ocr' },
              ]} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: '#555', marginBottom: 4 }}>服务地址</label>
            <Input placeholder="http://localhost:8080" value={form.endpoint} onChange={(e) => setForm({ ...form, endpoint: e.target.value })} />
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default ToolPage;
